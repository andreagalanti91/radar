"""supertrend · W3.2 (radar.weekly, non modificato) e varianti K1–K4 (PREREG §5). Copia di radar.weekly.simulate con:
K1 = niente cricchetto + uscita al cambio 1W contro; K2 = uscita al cambio 1D contro; K3 = filtro d'ingresso 1D concorde
(attesa fino a sabato, poi nuova decisione); K4 = uscita al cambio 4h contro, eseguita all'apertura 4h successiva."""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
import st_lib as L
sys.path.insert(0, str(L.ROOT))
from radar import weekly as W  # noqa: E402

assert W.R_LONG == W.R_SHORT == 0.25 and W.STOP_K == W.TRAIL_K == 2.5


def frames():
    rd = lambda n: pd.read_csv(L.ROOT / "research" / "p2_nuovi" / "data" / n, index_col=0, parse_dates=True)  # noqa: E731
    return rd("f_repo.csv.gz"), rd("f_long.csv.gz")


def flip_events(d: pd.Series) -> pd.Series:
    """Da direzione Pine (−1 rialzo, +1 ribasso) a eventi: +1 = cambio al rialzo (a favore dei long), −1 = al ribasso, 0 = nessuno."""
    fav = -d
    e = (fav != fav.shift()).astype(int) * fav
    e.iloc[:11] = 0
    return e


def st_inputs(daily: pd.DataFrame, a4: pd.DataFrame | None = None) -> dict:
    """Eventi e stato del Supertrend 10/3 su 1D, 1W (e 4h se ci sono le candele)."""
    w = L.weekly_from(daily)
    dd = pd.Series(L.supertrend(daily["high"].to_numpy(), daily["low"].to_numpy(), daily["close"].to_numpy())[1], daily.index)
    dw = pd.Series(L.supertrend(w["high"].to_numpy(), w["low"].to_numpy(), w["close"].to_numpy())[1], w.index)
    out = dict(FD=flip_events(dd), SD=-dd, FW=flip_events(dw))
    if a4 is not None:
        d4 = pd.Series(L.supertrend(a4["high"].to_numpy(), a4["low"].to_numpy(), a4["close"].to_numpy())[1], a4.index)
        out["F4"] = flip_events(d4); out["a4"] = a4
    return out


def simulate(f, start, end, var=None, X=None, capital=10000.0, detail=False):
    f = f[f["close"].notna() & (f.index <= end)]
    w = W.weekly_bars(f); idx = f.index
    O, H, Lo, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    z = np.zeros(len(idx))
    FD = X["FD"].reindex(idx).fillna(0).to_numpy() if var == "K2" else z
    SD = X["SD"].reindex(idx).fillna(0).to_numpy() if var == "K3" else z
    FW = X["FW"].reindex(idx).fillna(0).to_numpy() if var == "K1" else z
    if var == "K4":
        a4 = X["a4"]; F4 = X["F4"].to_numpy(); O4, L4, H4 = (a4[k].to_numpy(float) for k in ("open", "low", "high"))
        dn = a4.index.normalize(); first = pd.Series(np.arange(len(dn)), dn).groupby(level=0).agg(["first", "last"])
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr, waiting = 1.0, 0.0, 0.0, 0, None, None, None
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
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side=side, eq0=cash + abs(q) * px * frate,
                          stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
                tr["stop"] = tr["stop0"]
            pend = None
        kexit = None
        if side:
            if var != "K1":                                   # K1: lo stop iniziale resta fisso (niente cricchetto)
                tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
                tr["stop"] = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            stop = tr["stop"]
            x4 = None
            if var == "K4" and day in first.index:
                j0, j1 = first.loc[day, "first"], first.loc[day, "last"]
                hit = np.flatnonzero(F4[j0:j1 + 1] == -side)
                if len(hit):
                    k = j0 + hit[0]
                    if k < j1:                                # esecuzione all'apertura 4h successiva, nello stesso giorno
                        touched = (L4[j0:k + 1].min() <= stop) if side > 0 else (H4[j0:k + 1].max() >= stop)
                        x4 = None if touched else O4[k + 1]
                    else:
                        kexit = ("exit", "st4h")              # ultimo 4h del giorno: apertura del giorno dopo
            if x4 is not None:
                close_all(x4 * (1 - W.SLIP * side), i, "st4h")
            elif (side > 0 and Lo[i] <= stop) or (side < 0 and H[i] >= stop):
                close_all((min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side), i, "stop")
                kexit = None
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if side and var == "K2" and FD[i] == -side:
            kexit = ("exit", "st1d")
        if not side:
            kexit = None
        sunday = day.dayofweek == 6 and day in w.index
        if var == "K3" and waiting is not None and not side and not sunday:
            sd, wk0, d0 = waiting
            s0 = wk0["close"] - sd * W.STOP_K * wk0["atr"]
            if (sd > 0 and C[i] < s0) or (sd < 0 and C[i] > s0):
                waiting = None
            elif SD[i] == sd:
                pend = ("enter", sd, wk0, d0); waiting = None
        if sunday:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            if var == "K1" and side and d is None and FW[i] == -side:
                d = ("exit", "st1w")
            if var == "K3" and d and d[0] == "enter":
                expired = waiting is not None and waiting[0] == d[1]
                waiting = None
                if not expired and SD[i] != d[1]:
                    waiting = (d[1], wk, day); d = None
            elif var == "K3":
                waiting = None
            pend = d + (wk, day) if d else None
        if kexit is not None and pend is None:
            pend = kexit
    e = pd.Series(eq[t0:], idx[t0:])
    if side:
        trades = trades + [dict(tr, exit=None, reason="open", pnl=e.iloc[-1] / tr["eq0"] - 1)]
    pn = np.array([t["pnl"] for t in trades])
    yrs = ((pd.Timestamp(end) - pd.Timestamp(start)).days + 1) / 365.25
    fin = float(e.iloc[-1]); dd = float((e / e.cummax() - 1).min()); cagr = fin ** (1 / yrs) - 1
    out = dict(fin=fin * capital, cagr=cagr, dd=dd, S=cagr / abs(dd) if dd < 0 else np.nan, n=len(pn), wr=float((pn > 0).mean()) if len(pn) else np.nan,
               worst=float(pn.min()) if len(pn) else np.nan)
    if detail:
        out["trades"] = trades; out["equity"] = e
    return out


PERK = {**L.PERIODS, "2021-26": ("2021-01-01", L.CUT)}

if __name__ == "__main__":
    f, fl = frames()
    a4 = L.load_4h(L.CUT); daily = L.daily_from(a4)
    X = st_inputs(daily, a4)
    # 1) la copia riproduce l'originale
    o = W.simulate(f, start="2021-01-01"); m = W.metrics(o)
    mine = simulate(f, "2021-01-01", L.CUT, detail=True)
    print("radar.weekly:", round(float(o["equity"].iloc[-1]), 2), m["max_dd_pct"], m["n"], m["win_rate"], "| copia:", round(mine["fin"], 2), round(mine["dd"] * 100, 1), mine["n"], round(mine["wr"] * 100, 1))
    assert abs(float(o["equity"].iloc[-1]) - mine["fin"]) < 0.01 and len(o["trades"]) + (1 if o["open"] else 0) == mine["n"]
    # 2) tabella
    rows, tl = [], []
    for v in (None, "K1", "K2", "K3", "K4"):
        for p, (a, b) in PERK.items():
            r = simulate(fl if a < "2021" else f, a, b, v, X, detail=True)
            for t in r.pop("trades"):
                tl.append(dict(var=v or "W3.2", periodo=p, signal=t["signal"], entry=t["entry"], exit=t["exit"], side=t["side"], reason=t["reason"], pnl=t["pnl"]))
            r.pop("equity")
            rows.append(dict(var=v or "W3.2", periodo=p, **r))
    R = pd.DataFrame(rows); TL = pd.DataFrame(tl)
    R.to_csv(L.HERE / "w32_k.csv", index=False); TL.to_csv(L.HERE / "w32_k_trade.csv", index=False)
    # 3) criteri
    base = R[R["var"] == "W3.2"].set_index("periodo"); crit = []
    for v in ("K1", "K2", "K3", "K4"):
        g = R[R["var"] == v].set_index("periodo")
        c = dict(var=v, s2123=g.loc["2021-23", "S"] > base.loc["2021-23", "S"], s2426=g.loc["2024-26", "S"] > base.loc["2024-26", "S"],
                 s1820=g.loc["2018-20", "S"] >= base.loc["2018-20", "S"], dd=g.loc["2021-26", "dd"] >= -0.30, wr=g.loc["2021-26", "wr"] >= 0.70)
        c["migliora_senza_placebo"] = all(v_ for k_, v_ in c.items() if k_ != "var"); crit.append(c)
    CR = pd.DataFrame(crit)
    # 4) placebo: eventi (o stato) traslati circolarmente, 500 volte; capitale 2021–26
    rng = np.random.default_rng(20261123); pl = []
    for v, key in (("K1", "FW"), ("K2", "FD"), ("K3", "SD"), ("K4", "F4")):
        real = R[(R["var"] == v) & (R["periodo"] == "2021-26")]["fin"].iloc[0]; s = X[key]; sims = []
        for _ in range(500):
            Xp = dict(X); Xp[key] = pd.Series(np.roll(s.to_numpy(), int(rng.integers(len(s) // 20, len(s) - len(s) // 20))), s.index)
            sims.append(simulate(f, "2021-01-01", L.CUT, v, Xp)["fin"])
        sims = np.array(sims)
        pl.append(dict(var=v, reale=real, plac_mediana=np.median(sims), plac_5=np.quantile(sims, 0.05), plac_95=np.quantile(sims, 0.95), p=float((sims >= real).mean())))
        print(pl[-1], flush=True)
    PL = pd.DataFrame(pl); PL.to_csv(L.HERE / "w32_k_placebo.csv", index=False)
    CR = CR.merge(PL[["var", "p"]], on="var"); CR["migliora"] = CR["migliora_senza_placebo"] & (CR["p"] <= 0.0125)
    CR.to_csv(L.HERE / "w32_k_criteri.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    with open(L.HERE / "w32_k.txt", "w") as fh:
        for title, x in (("W3.2 E VARIANTI K", R.round(3)), ("CRITERI", CR), ("PLACEBO", PL.round(3)),
                         ("TRADE 2021-26", TL[TL["periodo"] == "2021-26"].round(4))):
            s_ = f"\n{title}\n{x.to_string()}"; print(s_); print(s_, file=fh)
