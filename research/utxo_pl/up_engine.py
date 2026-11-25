"""UTXO P/L (sostituto MVRV) · motore di ricerca (25/11/2026). Non modifica radar/.

Copia di radar.weekly.simulate (stesse costanti, stesse barre settimanali importate da radar.weekly) con DUE sole aggiunte:
- `end`: taglio dei dati (come research/tp_rientro/tp_engine.py);
- `rule` con le maschere giornaliere `cap` (capitolazione) ed `eup` (euforia), lette alla chiusura del giorno t:
    H1: short aperto e cap[t] -> uscita all'apertura di t+1 (motivo "zona");
    H2: alla domenica t la decisione "entra short" si annulla se cap[t];
    H3: long aperto e eup[t] -> uscita all'apertura di t+1.
    "H1+H2" (combinazione, solo informativa): chiude lo short al primo giorno di zona e non lo riapre finché la domenica è zona.
  Con rule=None il motore è identico a radar.weekly.simulate (verificato in up_run.py: stessi trade e stesso finale).
Il resto di W3.2 non cambia: dopo un'uscita "zona" la strategia è flat e può rientrare alla domenica successiva se il segnale
c'è ancora (la regola richiude lo short al primo giorno di zona successivo all'ingresso).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402

HERE = Path(__file__).resolve().parent


def load_mvrv() -> pd.Series:
    d = pd.read_csv(HERE / "mvrv.csv", parse_dates=["date"])
    return d.set_index("date")["mvrv"]


def zones(m: pd.Series, win: int = 1460, q: float = 0.10) -> pd.DataFrame:
    """Zone fissate nel PREREG. (b): soglia = quantile dei `win` giorni PRECEDENTI (esclude il giorno stesso: solo passato)."""
    lo = m.rolling(win, min_periods=win).quantile(q).shift(1)
    hi = m.rolling(win, min_periods=win).quantile(1 - q).shift(1)
    return pd.DataFrame({"mvrv": m, "cap_a": m < 1.0, "eup_a": m > 3.0, "cap_b": m <= lo, "eup_b": m >= hi,
                         "lo_b": lo, "hi_b": hi})


def simulate(f: pd.DataFrame, start: str = W.START, end: str | None = None, capital: float = 10000.0,
             rule: str | None = None, cap: pd.Series | None = None, eup: pd.Series | None = None,
             w: pd.DataFrame | None = None) -> dict:
    f = f[f["close"].notna()]
    if end:
        f = f[f.index <= end]
    if w is None:
        w = W.weekly_bars(f)
    else:
        w = w[w.index <= f.index[-1]]
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    CAP = (cap.reindex(idx).fillna(False).to_numpy(bool) if cap is not None else np.zeros(len(idx), bool))
    EUP = (eup.reindex(idx).fillna(False).to_numpy(bool) if eup is not None else np.zeros(len(idx), bool))
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)
    blocked = []
    R = set((rule or "").split("+"))

    def close_all(px: float, i: int, reason: str) -> None:
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1,
                  move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = W.exposure(side, wk["close"], wk["atr"], 1.0)
                fs = min(lt, 1.0) / lt if side > 0 else 0.0
                frate, fperp = fs * W.FEE_SPOT + (1 - fs) * W.FEE_PERP, 1 - fs
                px = O[i] * (1 + W.SLIP * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=round(px, 2), sig_close=float(wk["close"]), atr=float(wk["atr"]), expo=round(lt, 3),
                          market="spot" if side > 0 else "perp", eq0=cash + abs(q) * px * frate,
                          stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
                tr["stop"] = tr["stop0"]
            pend = None
        if side:
            tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            if "H2" in R and d == ("enter", -1) and CAP[i]:
                blocked.append(str(day.date()))
                d = None
            pend = d + (wk, day) if d else None
        # regola giornaliera: lettura alla chiusura di t, uscita all'apertura di t+1 (prevale sulla decisione domenicale,
        # che in posizione può essere solo un'uscita allo stesso prezzo)
        if side and (("H1" in R and side < 0 and CAP[i]) or ("H3" in R and side > 0 and EUP[i])):
            pend = ("exit", "zona", None, day)
    out = {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "open": None, "pending": None,
           "blocked": blocked}
    if side:
        i = len(idx) - 1
        tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
        trail = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
        out["open"] = dict(tr, trail=float(trail), last=float(C[i]), move=(C[i] / tr["entry_px"] - 1) * side,
                           pnl=(eq[i] / tr["eq0"] - 1), pnl_close=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1)
    if pend is not None:
        out["pending"] = {"kind": pend[0], "arg": pend[1], "date": str(pend[3].date())}
    return out


def h4(f: pd.DataFrame, cap: pd.Series, eup: pd.Series, start: str, end: str | None = None, hold: int = 365) -> dict:
    """H4 descrittiva: long 1x spot all'apertura dopo il primo giorno di capitolazione (da flat), uscita all'apertura dopo il
    primo giorno di euforia o dopo `hold` giorni. Costi spot + slippage come W3.2."""
    f = f[f["close"].notna()]
    if end:
        f = f[f.index <= end]
    idx = f.index
    O, C = f["open"].to_numpy(float), f["close"].to_numpy(float)
    CAP = cap.reindex(idx).fillna(False).to_numpy(bool)
    EUP = eup.reindex(idx).fillna(False).to_numpy(bool)
    t0 = idx.searchsorted(pd.Timestamp(start))
    e, pos, trades, eq = 1.0, None, [], np.full(len(idx), np.nan)
    pend = None
    for i in range(t0, len(idx)):
        if pend == "in" and pos is None:
            px = O[i] * (1 + W.SLIP)
            pos = dict(entry=str(idx[i].date()), entry_px=px, i0=i, e0=e * (1 - W.FEE_SPOT))
        elif pend == "out" and pos is not None:
            px = O[i] * (1 - W.SLIP)
            e = pos["e0"] * px / pos["entry_px"] * (1 - W.FEE_SPOT)
            trades.append(dict(pos, exit=str(idx[i].date()), exit_px=px, pnl=e / (pos["e0"] / (1 - W.FEE_SPOT)) - 1))
            pos = None
        pend = None
        eq[i] = pos["e0"] * C[i] / pos["entry_px"] if pos else e
        if pos is None and CAP[i]:
            pend = "in"
        elif pos is not None and (EUP[i] or i - pos["i0"] >= hold):
            pend = "out"
    opn = None
    if pos:
        opn = dict(pos, last=C[-1], pnl=eq[len(idx) - 1] * (1 - W.FEE_SPOT) / (pos["e0"] / (1 - W.FEE_SPOT)) - 1)
    return {"trades": trades, "open": opn, "equity": pd.Series(eq[t0:], idx[t0:]) * 10000}
