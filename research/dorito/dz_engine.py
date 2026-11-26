"""Motori dello studio dorito (PREREG commit 5c92dc0).
- standalone(): S1–S4 (segnale alla chiusura del giorno t, esecuzione all'apertura di t+1).
- w32(): copia di radar.weekly.simulate (non modificato) con le varianti W1–W4.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from radar import weekly as W  # noqa: E402
from dorito_lib import daily, resample, resample_year, lele  # noqa: E402

assert W.R_LONG == W.R_SHORT == 0.25 and W.STOP_K == W.TRAIL_K == 2.5
FEE_SPOT, FEE_PERP, SLIP = 0.001, 0.0005, 0.001
assert W.FEE_SPOT == FEE_SPOT and W.FEE_PERP == FEE_PERP and W.SLIP == SLIP


def daily_signal(d, tf, bars=10, length=40, elif_=True):
    """Serie giornaliera (indice di d): +1 nero / −1 rosso nel giorno di CHIUSURA della barra, 0 altrove."""
    b = resample_year(d, tf)
    s = lele(b, bars, length, elif_)
    out = pd.Series(0, index=d.index)
    for t, v in s[s != 0].items():
        end = t + pd.Timedelta(days=int(b.loc[t, "n"]) - 1) if tf > 1 else t
        out.loc[end] = v
    return out


def funding_series(idx, path="data/funding.csv"):
    f = pd.read_csv(os.path.join(ROOT, path), parse_dates=["date"]).set_index("date")["funding"]
    return f.reindex(idx).fillna(0.0)


# ---------------------------------------------------------------- strategie a sé
def standalone(O, C, FU, sig, mode, t0, t1, collect=True):
    """mode 'long': nero → long spot, rosso → flat. mode 'ls': nero → long spot, rosso → short perp (inversione).
    Indici t0..t1 inclusi (giorni del periodo). Parte flat; posizione chiusa all'ultima chiusura (al netto dell'uscita)."""
    cash, qty, cost, side, rate = 1.0, 0.0, 0.0, 0, 0.0
    pend = 0  # posizione desiderata dal segnale di ieri (None = nessun cambio)
    pend_set = False
    trades = []
    eq = np.empty(t1 - t0 + 1) if collect else None
    eq0 = 1.0
    for i in range(t0, t1 + 1):
        if pend_set:
            if side and pend != side:
                px = O[i] * (1 - SLIP * side)
                cash += qty * px - cost - abs(qty) * px * rate
                trades.append(cash / eq0 - 1)
                qty, cost, side = 0.0, 0.0, 0
            if pend and not side:
                side = pend
                rate = FEE_SPOT if side > 0 else FEE_PERP
                px = O[i] * (1 + SLIP * side)
                eq0 = cash
                qty = side * cash / px
                cost = qty * px
                cash -= abs(qty) * px * rate
            pend_set = False
        if side < 0:
            cash -= qty * C[i] * FU[i]
        val = cash + (qty * C[i] - cost if side else 0.0)
        if val <= 0:  # capitale azzerato (short 1x senza stop): liquidazione, fine dell'attività
            trades.append(-1.0)
            if collect:
                eq[i - t0:] = 0.0
            return 0.0, trades, eq
        if collect:
            eq[i - t0] = val
        s = sig[i]
        if s and i < t1:
            tgt = 1 if s > 0 else (-1 if mode == "ls" else 0)
            if tgt != side:
                pend, pend_set = tgt, True
    if side:
        px = C[t1]
        cash += qty * px - cost - abs(qty) * px * rate
        trades.append(cash / eq0 - 1)
        if collect:
            eq[-1] = cash
    return cash, trades, eq


def buyhold(O, C, t0, t1):
    px = O[t0] * (1 + SLIP)
    q = (1 - FEE_SPOT) / px
    eq = q * C[t0:t1 + 1]
    eq[-1] = q * C[t1] * (1 - FEE_SPOT)
    return eq


def metr(eq, days, trades=None, cap=10000.0):
    e = np.asarray(eq, float) * cap   # eq in frazioni del capitale iniziale (1,0 = 10.000 $)
    fin = float(e[-1])
    yrs = days / 365.25
    dd = float((e / np.maximum.accumulate(np.r_[cap, e])[1:] - 1).min())
    cagr = (fin / cap) ** (1 / yrs) - 1 if fin > 0 else -1.0
    out = dict(finale=round(fin), rend=round((fin / cap - 1) * 100, 1), cagr=round(cagr * 100, 1), dd=round(dd * 100, 1),
               s=round(cagr / abs(dd), 2) if dd < 0 else np.nan, mar=round((fin / cap - 1) / abs(dd), 2) if dd < 0 else np.nan)
    if trades is not None:
        tr = np.array(trades)
        out.update(trade=len(tr), wr=round(float((tr > 0).mean() * 100)) if len(tr) else np.nan,
                   senza2=round(cap * float(np.prod(1 + np.sort(tr)[:-2]))) if len(tr) else np.nan)
    return out


# ---------------------------------------------------------------- W3.2 con varianti
class W32:
    """Prepara f (f_long o f_repo) una volta; run() simula W3.2 fra start ed end con eventuale variante."""

    def __init__(self, f, end):
        f = f[f["close"].notna() & (f.index <= pd.Timestamp(end))]
        self.f = f
        self.idx = f.index
        self.w = W.weekly_bars(f)
        self.O, self.H, self.L, self.C = (f[k].to_numpy(float).tolist() for k in ("open", "high", "low", "close"))
        self.FU = f["funding"].fillna(0).to_numpy(float).tolist()
        self.wk = {d: self.w.loc[d] for d in self.w.index}
        self.sun = [d.dayofweek == 6 and d in self.wk for d in self.idx]

    def run(self, start, var=None, tri=None, window=30):
        """var: None (W3.2), 'exit' (W1/W2: uscita al triangolo contrario dopo l'ingresso), 'filter' (W3/W4).
        tri: array allineato a self.idx (+1 nero, −1 rosso nel giorno di chiusura della barra)."""
        idx, O, H, L, C, FU = self.idx, self.O, self.H, self.L, self.C, self.FU
        n = len(idx)
        t0 = int(idx.searchsorted(pd.Timestamp(start)))
        tri = np.zeros(n, int) if tri is None else np.asarray(tri, int)
        if var == "filter":
            cb = np.cumsum(tri > 0)
            cr = np.cumsum(tri < 0)
            def recent(i, s):  # triangolo contrario a s nei `window` giorni fino a i incluso
                c = cr if s > 0 else cb
                return c[i] - (c[i - window] if i - window >= 0 else 0) > 0
        cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
        frate, fperp = FEE_PERP, 1.0
        trades, eq = [], np.full(n, np.nan)

        def close_all(px, i, reason):
            nonlocal cash, qty, cost, side, tr
            cash += qty * px - cost - abs(qty) * px * frate
            tr.update(exit=str(idx[i].date()), reason=reason, pnl=cash / tr["eq0"] - 1)
            trades.append(tr)
            tr, qty, cost, side = None, 0.0, 0.0, 0

        for i in range(t0, n):
            day = idx[i]
            if pend is not None:
                if pend[0] == "exit" and side:
                    close_all(O[i] * (1 - SLIP * side), i, pend[1])
                elif pend[0] == "enter" and not side:
                    side, wk = pend[1], pend[2]
                    lt = W.exposure(side, wk["close"], wk["atr"])
                    fs = min(lt, 1.0) / lt if side > 0 else 0.0
                    frate, fperp = fs * FEE_SPOT + (1 - fs) * FEE_PERP, 1 - fs
                    px = O[i] * (1 + SLIP * side)
                    q = side * lt * cash / px
                    qty, cost = q, q * px
                    cash -= abs(q) * px * frate
                    tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                              entry_i=i, expo=round(lt, 3), eq0=cash + abs(q) * px * frate,
                              stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
                    tr["stop"] = tr["stop0"]
                pend = None
            if side:
                tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
                stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
                tr["stop"] = stop
                if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                    px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - SLIP * side)
                    close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
                else:
                    cash -= fperp * qty * C[i] * FU[i]
                    tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
            eq[i] = cash + (qty * C[i] - cost if side else 0.0)
            if self.sun[i]:
                wk = self.wk[day]
                if side:
                    tr["curatr"] = float(wk["atr"])
                d = W._decide(wk, side)
                if d and var == "filter" and d[0] == "enter" and recent(i, d[1]):
                    d = None
                pend = d + (wk, day) if d else None
            if var == "exit" and side and tri[i] == -side and i >= tr["entry_i"] and (pend is None or pend[0] != "exit"):
                pend = ("exit", "dorito", None, day)
        out_tr = list(trades)
        if side:
            pnl_close = (eq[n - 1] - abs(qty) * C[n - 1] * frate) / tr["eq0"] - 1
            out_tr.append(dict(tr, exit="aperta", reason="open", pnl=pnl_close))
            eq[n - 1] = eq[n - 1] - abs(qty) * C[n - 1] * frate  # chiusura all'ultima chiusura con commissione
        e = pd.Series(eq[t0:], idx[t0:])
        return dict(equity=e, trades=out_tr)


def w_metr(r, cap=10000.0):
    e = r["equity"].to_numpy()
    days = (r["equity"].index[-1] - r["equity"].index[0]).days + 1
    m = metr(e, days, [t["pnl"] for t in r["trades"]], cap)
    return m
