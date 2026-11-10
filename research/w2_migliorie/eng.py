"""W2 + MACD · motore di ricerca delle migliorie (copia di radar.weekly.simulate con opzioni; a opzioni spente = baseline).
Non modifica radar/. Uso: from eng import *"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "short_w2"))
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402
from radar import weekly as W  # noqa: E402

DOW = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
TBILL = {2017: 0.009, 2018: 0.019, 2019: 0.021, 2020: 0.004, 2021: 0.0005, 2022: 0.020, 2023: 0.050, 2024: 0.050,
         2025: 0.042, 2026: 0.037}   # T-bill 3 mesi, medie annue approssimate (ipotesi dichiarata nel PREREG)

BASE = dict(anchor="SUN", sma=40, ema_t=20, ema_x=21, atr=14, stop=2.5, trail=2.5, f1=True,
            idle=None,            # None | float (tasso annuo) | "tbill"
            ema_n=1, ema_buf=0.0, ema_daily=False,       # M2
            reentry_n=0, cooldown=0,                     # M3
            run_r=None, run_k=None,                      # M4: dopo +run_r R il trailing diventa run_k ATRw
            lev_fn=None,                                 # M5: funzione (wk, data segnale) -> leva del long
            short_noflow=False,                          # M6 (D1)
            r2=None,                                     # M7: X ATRw sotto il massimo a 52 settimane nei trend vecchi
            ratchet=False,                               # M9
            lev=1.0)


def load_repo() -> pd.DataFrame:
    f = build_features(load_all())
    return f[f["close"].notna()]


def load_long(repo: pd.DataFrame) -> pd.DataFrame:
    import short_lab
    return short_lab.load_long(repo)


def weekly_bars(f: pd.DataFrame, p: dict) -> pd.DataFrame:
    rule = f"W-{p['anchor']}"
    w = f[["open", "high", "low", "close"]].resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    w["flow"] = f["pf14z"].resample(rule).last()
    w["fund7"] = f["funding"].fillna(0).rolling(7).mean().resample(rule).last()
    c = w["close"]
    w["sma"] = c.rolling(p["sma"]).mean()
    w["ema20"] = c.ewm(span=p["ema_t"], adjust=False).mean()
    w["ema21"] = c.ewm(span=p["ema_x"], adjust=False).mean()
    tr = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
    w["atr"] = tr.ewm(alpha=1 / p["atr"], adjust=False).mean()
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    above = (c > w["sma"]).astype(int)
    w["trend_age"] = above.groupby((above == 0).cumsum()).cumsum()
    m = c.ewm(span=8, adjust=False).mean() - c.ewm(span=21, adjust=False).mean()
    w["macd"], w["macd_sig"] = m, m.ewm(span=5, adjust=False).mean()
    f1 = (w["trend_age"] < W.OLD_TREND) | ((w["macd"] > w["macd_sig"]) & (w["macd"] > 0))
    if not p["f1"]:
        f1 = pd.Series(True, w.index)
    ok = pd.Series(True, w.index)
    if p["r2"] is not None:   # nuovo test del top in un trend vecchio
        top = c.rolling(52).max()
        ok = ~((w["trend_age"] >= W.OLD_TREND) & (c < top) & (c >= top - p["r2"] * w["atr"]))
    w["long_nf"] = (up & (c > w["ema21"]) & f1 & ok).fillna(False)          # senza flusso (M3a)
    w["long"] = (w["long_nf"] & (w["flow"] > 0)).fillna(False)
    sh = dn & (c < w["ema21"])
    w["short"] = (sh if p["short_noflow"] else sh & (w["flow"] < 0)).fillna(False)
    w["dist_long"] = ((w["fund7"] > W.FUND_HOT) & (w["flow"] < 0)).fillna(False)
    w["dist_short"] = ((w["fund7"] < W.FUND_COLD) & (w["flow"] > 0)).fillna(False)
    # uscita EMA21: n chiusure consecutive oltre la EMA21 di più di buf ATRw
    bl = (c < w["ema21"] - p["ema_buf"] * w["atr"]).astype(int)
    bs = (c > w["ema21"] + p["ema_buf"] * w["atr"]).astype(int)
    w["x_long"] = bl.rolling(p["ema_n"]).sum() >= p["ema_n"]
    w["x_short"] = bs.rolling(p["ema_n"]).sum() >= p["ema_n"]
    w["pos"] = np.arange(len(w))
    return w[w.index <= f.index[-1]]


def simulate(f: pd.DataFrame, start: str = "2021-01-01", end: str | None = None, capital: float = 10000.0, **kw) -> dict:
    p = dict(BASE, **kw)
    f = f[f["close"].notna()]
    if end:
        f = f[f.index <= pd.Timestamp(end)]
    w = weekly_bars(f, p)
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    e21d = w["ema21"].reindex(idx, method="ffill").to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    dow = DOW[p["anchor"]]
    SLIP, STOP_K, TRAIL_K = W.SLIP, p["stop"], p["trail"]
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)
    last_ema_exit = -999      # posizione (settimana) dell'ultima decisione di uscita EMA21
    last_ema_side = 0
    idle_gain = 0.0

    def close_all(px, i, reason):
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
                close_all(O[i] * (1 - SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                if side > 0:
                    lt = p["lev"] * (p["lev_fn"](wk, pend[3]) if p["lev_fn"] else 1.0)
                else:
                    lt = p["lev"] * min(1.0, W.R_SHORT / (2.5 * wk["atr"] / wk["close"]))
                fs = min(lt, 1.0) / lt if side > 0 else 0.0
                frate, fperp = fs * W.FEE_SPOT + (1 - fs) * W.FEE_PERP, 1 - fs
                px = O[i] * (1 + SLIP * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=round(px, 2), sig_close=float(wk["close"]), atr=float(wk["atr"]), expo=round(lt, 3),
                          eq0=cash + abs(q) * px * frate, stop0=float(wk["close"] - side * STOP_K * wk["atr"]),
                          best=O[i], curatr=float(wk["atr"]), k=TRAIL_K, rstop=None,
                          age=int(wk["trend_age"]), macd_up=bool(wk["macd"] > wk["macd_sig"]))
            pend = None
        if side:
            if p["run_r"] is not None and (tr["best"] - tr["entry_px"]) * side >= p["run_r"] * 2.5 * tr["atr"]:
                tr["k"] = p["run_k"]
            tl = tr["best"] - side * tr["k"] * tr["curatr"]
            stop = max(tr["stop0"], tl) if side > 0 else min(tr["stop0"], tl)
            if p["ratchet"]:
                if tr["rstop"] is not None:
                    stop = max(stop, tr["rstop"]) if side > 0 else min(stop, tr["rstop"])
                tr["rstop"] = stop
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        elif p["idle"] is not None:   # giorno senza posizione: la liquidità rende
            r = TBILL.get(day.year, 0.035) if p["idle"] == "tbill" else p["idle"]
            g = cash * r / 365.0
            cash += g
            idle_gain += g
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        is_week = day.dayofweek == dow and day in w.index
        if is_week:
            wk = w.loc[day]
            d = None
            if side:
                tr["curatr"] = float(wk["atr"])
                if wk["x_long"] if side > 0 else wk["x_short"]:
                    d = ("exit", "ema")
                    last_ema_exit, last_ema_side = int(wk["pos"]), side
                elif wk["dist_long"] if side > 0 else wk["dist_short"]:
                    d = ("exit", "dist")
            else:
                since = int(wk["pos"]) - last_ema_exit
                blocked = p["cooldown"] and since <= p["cooldown"]
                fast = p["reentry_n"] and last_ema_side > 0 and 0 < since <= p["reentry_n"] and wk["long_nf"]
                if not blocked:
                    if wk["long"] or fast:
                        d = ("enter", 1)
                    elif wk["short"]:
                        d = ("enter", -1)
            pend = d + (wk, day) if d else None
        elif side and p["ema_daily"] and pend is None:
            if (C[i] < e21d[i]) if side > 0 else (C[i] > e21d[i]):
                pend = ("exit", "ema_d", None, day)
    if side:   # posizione aperta: chiusa all'ultima chiusura (con commissione), come nelle metriche del tool
        i = len(idx) - 1
        t = dict(tr, exit=None, exit_px=float(C[i]), reason="open", move=(C[i] / tr["entry_px"] - 1) * side,
                 pnl=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1)
        trades.append(t)
    e = pd.Series(eq[t0:], idx[t0:]) * capital
    return {"trades": trades, "equity": e, "weekly": w, "idle_gain": idle_gain * capital, "p": p}


def metrics(r: dict) -> dict:
    e = r["equity"] / 10000.0
    pn = np.array([t["pnl"] for t in r["trades"]])
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    tot = float(e.iloc[-1] - 1)
    dd = float((e / e.cummax() - 1).min())
    cagr = (1 + tot) ** (1 / yrs) - 1 if tot > -1 else -1.0
    best = float(pn.max()) if len(pn) else 0.0
    return dict(final=float(e.iloc[-1] * 10000), ret=tot * 100, dd=dd * 100, n=len(pn),
                wr=float((pn > 0).mean() * 100) if len(pn) else float("nan"), cagr=cagr * 100,
                mar=cagr / abs(dd) if dd < 0 else float("nan"), best=best * 100,
                final_wo=float(e.iloc[-1] * 10000 / (1 + best)), worst=float(pn.min() * 100) if len(pn) else 0.0)


def bh(f: pd.DataFrame, start: str = "2021-01-01", end: str | None = None) -> dict:
    f = f[f["close"].notna()]
    if end:
        f = f[f.index <= pd.Timestamp(end)]
    f = f[f.index >= pd.Timestamp(start)]
    px = f["open"].iloc[0] * (1 + W.SLIP)
    e = f["close"] / px * (1 - W.FEE_SPOT)
    e.iloc[-1] *= (1 - W.FEE_SPOT)
    return metrics({"equity": e * 10000, "trades": [dict(pnl=float(e.iloc[-1] - 1))]})


def tkey(t: dict) -> tuple:
    return (t["side"], t["entry"], t["exit"])


def changed(base: dict, var: dict) -> tuple[int, int]:
    """(trade della baseline senza gemello identico nella variante, trade nuovi della variante)."""
    a, b = {tkey(t) for t in base["trades"]}, {tkey(t) for t in var["trades"]}
    return len(a - b), len(b - a)


def equal_dd_base(f: pd.DataFrame, dd_target: float, start="2021-01-01", end=None) -> tuple[float, float]:
    """Baseline con leva uniforme x tale che il max DD giornaliero = dd_target (in %). Ritorna (x, capitale finale)."""
    lo, hi = 0.2, 4.0
    for _ in range(30):
        x = (lo + hi) / 2
        m = metrics(simulate(f, start=start, end=end, lev=x))
        if abs(m["dd"]) < abs(dd_target):
            lo = x
        else:
            hi = x
    return x, m["final"]
