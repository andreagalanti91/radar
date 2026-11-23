"""ema_sma · W3.2 (radar.weekly, non modificato) per periodo e varianti K1–K3 (PREREG §6): copia di radar.weekly.simulate con
filtro d'ingresso (stato della regola a favore alla domenica) e uscita giornaliera (stato contro alla chiusura → apertura dopo)."""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
import es_lib as L
sys.path.insert(0, str(L.ROOT))
from radar import weekly as W  # noqa: E402

assert W.R_LONG == W.R_SHORT == 0.25 and W.STOP_K == 2.5


def frames():
    rd = lambda n: pd.read_csv(L.ROOT / "research" / "p2_nuovi" / "data" / n, index_col=0, parse_dates=True)  # noqa: E731
    return rd("f_repo.csv.gz"), rd("f_long.csv.gz")


def simulate(f, start, end, state=None, gate=False, xexit=False, capital=10000.0):
    f = f[f["close"].notna() & (f.index <= end)]
    w = W.weekly_bars(f); idx = f.index
    O, H, Lo, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    ST = state.reindex(idx).fillna(0).to_numpy() if state is not None else np.zeros(len(idx))
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)

    def close_all(px, i, reason):
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        tr.update(exit=str(idx[i].date()), reason=reason, pnl=cash / tr["eq0"] - 1); trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = W.exposure(side, wk["close"], wk["atr"])
                frate, fperp = (W.FEE_SPOT, 0.0) if side > 0 else (W.FEE_PERP, 1.0)
                px = O[i] * (1 + W.SLIP * side); q = side * lt * cash / px
                qty, cost = q, q * px; cash -= abs(q) * px * frate
                tr = dict(entry=str(day.date()), side=side, eq0=cash + abs(q) * px * frate, stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]),
                          best=O[i], curatr=float(wk["atr"]))
                tr["stop"] = tr["stop0"]
            pend = None
        if side:
            tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl); tr["stop"] = stop
            if (side > 0 and Lo[i] <= stop) or (side < 0 and H[i] >= stop):
                close_all((min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side), i, "stop")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if xexit and side and ST[i] == -side:
            pend = ("exit", "regola")
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            if d and d[0] == "enter" and gate and ST[i] != d[1]:
                d = None
            if d:
                pend = d + (wk, day)
    e = pd.Series(eq[t0:], idx[t0:])
    pn = np.array([t["pnl"] for t in trades] + ([e.iloc[-1] / tr["eq0"] - 1] if side else []))
    yrs = ((pd.Timestamp(end) - pd.Timestamp(start)).days + 1) / 365.25
    fin = float(e.iloc[-1]); dd = float((e / e.cummax() - 1).min()); cagr = fin ** (1 / yrs) - 1
    return dict(fin=fin * capital, cagr=cagr, dd=dd, S=cagr / abs(dd) if dd < 0 else np.nan, n=len(pn), wr=float((pn > 0).mean()) if len(pn) else np.nan)


def table(states: dict) -> pd.DataFrame:
    """W3.2 e varianti K per i tre periodi (ogni periodo da 10.000 $) e sull'intero 2021–26."""
    f, fl = frames(); rows = []
    per = dict(L.PERIODS); per["intero 2021-26"] = ("2021-01-01", L.CUT)
    var = {"W3.2": dict()}
    for k, (stt, g, x) in states.items():
        var[k] = dict(state=stt, gate=g, xexit=x)
    for name, kw in var.items():
        for p, (a, b) in per.items():
            rows.append(dict(var=name, periodo=p, **simulate(fl if a < "2021" else f, a, b, **kw)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    t = table({})
    print(t.round(3).to_string())
