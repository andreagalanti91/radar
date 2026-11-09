"""Famiglia D · uscite e leva su A1 (Ichimoku TK cross 4h). Vedi PREREG.md.
python3 run_d.py is | oos | lev | placebo | neigh   (risultati in csv nella cartella)"""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "A_trend"))
from engine import load_all, backtest, metrics, placebo, Exits, Sizing, Costs  # noqa
from strategies_a import ichi  # noqa

START, CUT, OI_START = "2021-01-01", "2024-01-01", "2021-12-01"
SZ_REF = Sizing(mode="risk", risk_pct=0.01, leverage=2, allocation="equal", max_exposure=3)
bars = load_all("4h")
SIG = {"tk": 9, "kj": 26}


def oiz(b, w=180):
    oi = b["oi"].replace(0, np.nan)
    ch = oi / oi.shift(6) - 1
    return (ch - ch.rolling(w, min_periods=w // 2).mean()) / ch.rolling(w, min_periods=w // 2).std()


def signals(tk=9, kj=26, oi_filter=False):
    out = {}
    for a, b in bars.items():
        s = ichi(b, tk=tk, kj=kj, sb=52)
        if oi_filter:
            s.loc[~(oiz(b) > 1.0).to_numpy(), "side"] = 0
        out[a] = s
    return out


def mk(pol, p):
    base = dict(reverse_exit=False, reverse_entry=False)
    if pol == "E1":
        return Exits(stop_atr=p["stop"], tp=[(p["tp1"], .5), (p["tp2"], .5)], tp_unit="R", be_after_tp1=True, time_bars=p["tb"], **base)
    if pol == "E2":
        return Exits(stop_atr=p["stop"], tp=[(p["tp1"], 1.0)], tp_unit="R", time_bars=p["tb"], **base)
    if pol == "E3":
        return Exits(stop_atr=p["stop"], tp=[(p["tp1"], .5), (p["tp2"], .5)], tp_unit="pct", be_after_tp1=True, time_bars=p["tb"], **base)
    if pol == "E4":
        return Exits(stop_atr=p["stop"], tp=[(p["tp1"], .5)], tp_unit="R", be_after_tp1=True, trail_atr=p["trail"],
                     trail_after_tp1=True, time_bars=p["tb"], **base)
    if pol == "E5":
        return Exits(stop_atr=p["stop"], tp=[(p["tp1"], .33), (p["tp2"], .33), (p["tp3"], .34)], tp_unit="R", be_after_tp1=True,
                     time_bars=p["tb"], **base)
    if pol == "E6":
        return Exits(stop_atr=p["stop"], tp=[(p["tp1"], 1.0)], tp_unit="R", time_bars=p["tb"], **base)
    if pol == "E7":
        return Exits(stop_atr=p["stop"], trail_atr=p["trail"], time_bars=p["tb"], **base)
    raise KeyError(pol)


POL = {"E1": {"stop": 1.5, "tp1": 1.5, "tp2": 3.0, "tb": 12}, "E2": {"stop": 2.0, "tp1": 3.0, "tb": 48},
       "E3": {"stop": 2.0, "tp1": .05, "tp2": .10, "tb": 72}, "E4": {"stop": 2.0, "tp1": 2.0, "trail": 3.0, "tb": 120},
       "E5": {"stop": 2.0, "tp1": 1.0, "tp2": 2.0, "tp3": 4.0, "tb": 72}, "E6": {"stop": 2.0, "tp1": 2.0, "tb": 72},
       "E7": {"stop": 2.0, "trail": 3.0, "tb": 180}}
NAMES = {"E1": "E1 REF 1,5ATR ½@1,5R BE ½@3R 12b", "E2": "E2 L78 2ATR tutto@3R 48b", "E3": "E3 costante +5%/+10% BE 72b",
         "E4": "E4 ½@2R BE + trailing 3ATR", "E5": "E5 ⅓@1R ⅓@2R ⅓@4R BE", "E6": "E6 tutto@2R 72b",
         "E7": "E7 chandelier 3ATR", "E8": "E8 scelta + OI in espansione", "E3*": "E3* costante scelta in campione"}


def run(pol, p, start, end=None, sz=SZ_REF, sig=None, oi=False):
    sig = sig or signals(oi_filter=oi)
    return backtest(bars, sig, mk(pol, p), sz, Costs(), start, end)


def row(res, extra=None):
    m = metrics(res); t = res.trades
    r = {k: m.get(k) for k in ("final", "ret_pct", "max_dd", "mar", "trades", "trades_per_month", "win_rate", "pf", "exp_R", "liquidations")}
    if len(t):
        g = t.groupby("asset")["pnl"].sum()
        r["assets_pos"] = int((g > 0).sum()); r["wo_best"] = round(float(t.pnl.sum() - t.pnl.max()), 0)
        r["lev_max"] = round(float(t.lev.max()), 2)
        r["stop_pct_max"] = round(float(((t.entry - t.stop0).abs() / t.entry).max() * 100), 1)
    r.update(extra or {})
    return r


def save(df, name):
    df.to_csv(os.path.join(HERE, name), index=False); print(df.to_string(index=False), flush=True)


def stage_is():
    S, S_oi = signals(), signals(oi_filter=True)
    rows = []
    for pol, p in POL.items():
        rows.append(row(run(pol, p, START, CUT, sig=S), {"pol": pol}))
    df = pd.DataFrame(rows)
    adm = df[(df.pf >= 1.1) & (df.exp_R > 0) & df.trades_per_month.between(2, 12) & (df.max_dd >= -25)]
    sel = None
    if len(adm):
        top = adm.exp_R.max(); sel = adm[adm.exp_R >= top - 0.02].sort_values("mar", ascending=False).pol.iloc[0]
    best = sel or df.sort_values("exp_R", ascending=False).pol.iloc[0]
    # E8 vs its base on the same window (from 2021-12)
    r8 = row(run(best, POL[best], OI_START, CUT, sig=S_oi), {"pol": "E8"})
    rb = row(run(best, POL[best], OI_START, CUT, sig=S), {"pol": f"{best} da 2021-12"})
    df = pd.concat([df, pd.DataFrame([r8, rb])], ignore_index=True)
    # constant grid (E3 neighbours, IS only)
    g = []
    for t1 in (3, 4, 5, 6, 8):
        for t2 in (6, 8, 10, 12, 15, 20):
            if t2 >= 1.5 * t1:
                p = dict(POL["E3"], tp1=t1 / 100, tp2=t2 / 100)
                g.append(row(run("E3", p, START, CUT, sig=S), {"tp1": t1, "tp2": t2}))
    g = pd.DataFrame(g)
    top = g.exp_R.max(); cst = g[g.exp_R >= top - 0.02].sort_values("mar", ascending=False).iloc[0]
    save(df, "is_results.csv"); save(g, "const_grid_is.csv")
    ch = {"admitted": adm.pol.tolist(), "selected": sel, "base_for_E8": best,
          "const": {"tp1": float(cst.tp1) / 100, "tp2": float(cst.tp2) / 100}}
    json.dump(ch, open(os.path.join(HERE, "choice.json"), "w"), indent=1); print(ch)


def all_pols():
    ch = json.load(open(os.path.join(HERE, "choice.json")))
    b = ch["base_for_E8"]
    P = {k: (k, v, False) for k, v in POL.items()}
    P["E8"] = (b, POL[b], True)
    P["E3*"] = ("E3", dict(POL["E3"], tp1=ch["const"]["tp1"], tp2=ch["const"]["tp2"]), False)
    return P, ch


def stage_oos():
    P, ch = all_pols(); rows = []
    S, S_oi = signals(), signals(oi_filter=True)
    for k, (pol, p, oi) in P.items():
        s = S_oi if oi else S
        st = OI_START if oi else START
        r = {"pol": k}
        for lab, (a, e) in {"IS": (st, CUT), "OOS": (CUT, None), "ALL": (st, None)}.items():
            r.update({f"{lab}_{kk}": v for kk, v in row(run(pol, p, a, e, sig=s)).items()})
        rows.append(r)
    save(pd.DataFrame(rows), "oos_results.csv")
    # yearly for the ALL run
    yr = []
    for k, (pol, p, oi) in P.items():
        res = run(pol, p, OI_START if oi else START, sig=S_oi if oi else S)
        d = res.daily; y = d.groupby(d.index.year).last(); prev = y.shift().fillna(res.capital)
        yr.append({"pol": k, **{int(i): round((y[i] / prev[i] - 1) * 100, 1) for i in y.index}})
        res.trades.to_csv(os.path.join(HERE, f"trades_{k.replace('*', 'x')}.csv"), index=False)
    save(pd.DataFrame(yr), "yearly.csv")


def stage_placebo():
    P, ch = all_pols(); S, S_oi = signals(), signals(oi_filter=True)
    n = int(os.environ.get("NPL", 500)); rows = []
    for k, (pol, p, oi) in P.items():
        for lab, (a, e, nn) in {"OOS": (CUT, None, n), "IS": (OI_START if oi else START, CUT, n // 2)}.items():
            res = run(pol, p, a, e, sig=S_oi if oi else S)
            pl = placebo(res, bars, mk(pol, p), SZ_REF, Costs(), n=nn, seed=0)
            R = pl["runs"]
            rows.append({"pol": k, "per": lab, "pct_expR": pl["pctl"]["exp_R"], "pct_ret": pl["pctl"]["ret_pct"],
                         "pl_med_expR": round(R.exp_R.median(), 3), "pl_med_ret": round(R.ret_pct.median(), 1),
                         "pl_med_pf": round(R.pf.median(), 2), "pl_share_pos": round((R.ret_pct > 0).mean() * 100, 0),
                         "pl_trades_med": R.trades.median(), "real_trades": len(res.trades)})
            print(rows[-1], flush=True)
    save(pd.DataFrame(rows), "placebo.csv")


def stage_neigh():
    P, ch = all_pols(); rows = []
    for k, (pol, p, oi) in P.items():
        sets = []
        for kk, v in p.items():
            for f in (.8, 1.2):
                q = dict(p); q[kk] = int(round(v * f)) if kk == "tb" else round(v * f, 4); sets.append((f"{kk}x{f}", q, SIG))
        for kk in ("tk", "kj"):
            for f in (.8, 1.2):
                sg = dict(SIG); sg[kk] = int(round(SIG[kk] * f)); sets.append((f"{kk}x{f}", p, sg))
        vals = []
        for lab, q, sg in sets:
            s = signals(sg["tk"], sg["kj"], oi_filter=oi)
            m = metrics(run(pol, q, CUT, sig=s)); vals.append(m["exp_R"])
            rows.append({"pol": k, "nb": lab, "exp_R": m["exp_R"], "pf": m["pf"], "ret_pct": m["ret_pct"], "max_dd": m["max_dd"]})
        print(k, "median", np.median(vals), flush=True)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(HERE, "neighbours.csv"), index=False)
    print(df.groupby("pol").agg(med_expR=("exp_R", "median"), share_pf1=("pf", lambda x: (x > 1).mean())).to_string())


def stage_lev():
    P, ch = all_pols(); S, S_oi = signals(), signals(oi_filter=True)
    keys = ["E1", "E3", "E3*", ch["selected"] or ch["base_for_E8"]]
    rows = []
    for k in dict.fromkeys(keys):
        pol, p, oi = P[k]
        grid = [(f"rischio {r:g}% max {L}x", Sizing(mode="risk", risk_pct=r / 100, leverage=L, allocation="shared", max_exposure=L))
                for r in (0.5, 1, 1.5) for L in (2, 3, 5)]
        grid += [(f"leva piena {L}x (nozionale {L}x capitale)", Sizing(mode="fixed", leverage=L, allocation="equal", max_exposure=L))
                 for L in (2, 3, 5)]
        for lab, sz in grid:
            r = {"pol": k, "sizing": lab}
            for per, (a, e) in {"ALL": (START, None), "IS": (START, CUT), "OOS": (CUT, None)}.items():
                rr = row(run(pol, p, a, e, sz=sz, sig=S))
                r.update({f"{per}_{kk}": rr.get(kk) for kk in ("final", "ret_pct", "max_dd", "mar", "pf", "exp_R", "liquidations", "lev_max", "stop_pct_max")})
            rows.append(r)
            print(r["pol"], lab, r["ALL_final"], r["ALL_max_dd"], r["ALL_liquidations"], flush=True)
    save(pd.DataFrame(rows), "leverage.csv")


if __name__ == "__main__":
    {"is": stage_is, "oos": stage_oos, "placebo": stage_placebo, "neigh": stage_neigh, "lev": stage_lev}[sys.argv[1]]()
