"""zeiierman3 · W3.2 (copia di radar.weekly.simulate, non modificato) con le varianti W1/W2 del PREREG.
W1: long aggiuntivo da flat su segnale R2 (tz risale sopra −90), uscita tz > −20 o all'apertura in cui W3.2 entra.
W2: con W3.2 aperto, metà della quantità all'apertura dopo il primo tz > −20 (long) / tz < −90 (short), una volta per trade.
Opzioni per il placebo: w1_plan {i_in: i_out}; w2_days set di indici-segnale (al posto dell'attraversamento)."""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from z3_lib import ROOT
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402

assert W.R_LONG == W.R_SHORT == 0.25 and W.STOP_K == W.TRAIL_K == 2.5


def frames():
    rd = lambda n: pd.read_csv(ROOT / "research" / "p2_nuovi" / "data" / n, index_col=0, parse_dates=True)  # noqa: E731
    return rd("f_repo.csv.gz"), rd("f_long.csv.gz")


def simulate(f, start, end, var=None, tz=None, w1_plan=None, w2_days=None, capital=10000.0):
    f = f[f["close"].notna() & (f.index <= end)]
    w = W.weekly_bars(f); idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    x = tz.reindex(idx).to_numpy(float) if tz is not None else np.full(len(idx), np.nan)
    xp = np.r_[np.nan, x[:-1]]
    up20 = (x > -20) & (xp <= -20); dn90 = (x < -90) & (xp >= -90); r2 = (x > -90) & (xp <= -90)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)
    x_qty, x_pend_in, x_pend_out, x_tr, x_trades = 0.0, False, False, None, []
    half_pend = False

    def close_all(px, i, reason):
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        tr.update(exit=str(idx[i].date()), reason=reason, pnl=cash / tr["eq0"] - 1); trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    def x_close(i, why):
        nonlocal cash, x_qty, x_tr
        px = O[i] * (1 - W.SLIP)
        cash += x_qty * px * (1 - W.FEE_SPOT)
        x_tr.update(exit=str(idx[i].date()), reason=why, pnl=cash / x_tr["eq0"] - 1); x_trades.append(x_tr)
        x_qty, x_tr = 0.0, None

    for i in range(t0, len(idx)):
        day = idx[i]
        if x_qty and (x_pend_out or (pend is not None and pend[0] == "enter")):
            x_close(i, "tz>-20" if x_pend_out else "W3.2 entra")
        x_pend_out = False
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = W.exposure(side, wk["close"], wk["atr"])
                fs = min(lt, 1.0) / lt if side > 0 else 0.0
                frate, fperp = fs * W.FEE_SPOT + (1 - fs) * W.FEE_PERP, 1 - fs
                px = O[i] * (1 + W.SLIP * side); q = side * lt * cash / px
                qty, cost = q, q * px; cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side=side, eq0=cash + abs(q) * px * frate,
                          stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]), best=O[i], curatr=float(wk["atr"]), half=None)
                tr["stop"] = tr["stop0"]
            pend = None
        elif x_pend_in and not side and not x_qty:
            px = O[i] * (1 + W.SLIP); x_tr = dict(entry=str(day.date()), eq0=cash)
            if w1_plan is not None:
                x_tr["out"] = w1_plan[i]
            x_qty = cash * (1 - W.FEE_SPOT) / px; cash = 0.0
        x_pend_in = False
        if half_pend and side:
            px = O[i] * (1 - W.SLIP * side); q, cst = qty * 0.5, cost * 0.5
            cash += q * px - cst - abs(q) * px * frate; qty, cost = qty - q, cost - cst
            tr["half"] = str(day.date())
        half_pend = False
        if side:
            tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl); tr["stop"] = stop
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                close_all((min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side), i,
                          "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0) + x_qty * C[i]
        # segnali delle varianti alla chiusura
        if var == "W2" and side and tr["half"] is None and not half_pend:
            trig = (i in w2_days) if w2_days is not None else (up20[i] if side > 0 else dn90[i])
            if trig:
                half_pend = True; tr["half"] = "pend"
        if var == "W1":
            if x_qty and (w1_plan is None and x[i] > -20 or w1_plan is not None and i + 1 >= x_tr["out"]):
                x_pend_out = True
            elif not x_qty and not side:
                if (w1_plan is None and r2[i]) or (w1_plan is not None and (i + 1) in w1_plan):
                    x_pend_in = True
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            pend = d + (wk, day) if d else None
        if x_pend_in and pend is not None:
            x_pend_in = False
    if x_qty:
        cash += x_qty * C[-1] * (1 - W.SLIP) * (1 - W.FEE_SPOT); x_tr.update(exit="fine", pnl=cash / x_tr["eq0"] - 1)
        x_trades.append(x_tr); x_qty = 0.0
        eq[-1] = cash + (qty * C[-1] - cost if side else 0.0)
    e = pd.Series(eq[t0:], idx[t0:]) * capital
    pn = np.array([t["pnl"] for t in trades] + ([float(eq[-1] / tr["eq0"] - 1)] if side else []))
    return dict(equity=e, trades=trades, open=tr, x_trades=x_trades, n=len(pn), pn=pn)


def met(r):
    e = r["equity"]; fin = float(e.iloc[-1])
    yrs = (e.index[-1] - e.index[0]).days / 365.25 + 1 / 365.25
    dd = float((e / e.cummax() - 1).min()); cagr = (fin / 10000) ** (1 / yrs) - 1
    pn = r["pn"]
    return dict(finale=round(fin), rend=round((fin / 1e4 - 1) * 100, 1), cagr=round(cagr * 100, 1), dd=round(dd * 100, 1),
                cagr_dd=round(cagr / abs(dd), 2), mar=round((fin / 1e4 - 1) / abs(dd), 2), trade=r["n"] + len(r["x_trades"]),
                wr=round(float((np.r_[pn, [t["pnl"] for t in r["x_trades"]]] > 0).mean() * 100)) if r["n"] else np.nan)
