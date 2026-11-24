"""supertrend · strategie S1–S4 (PREREG §4): tabella 10/3, tetto di rischio, mappa dei parametri, placebo P1 e P2, storia corta."""
from __future__ import annotations
import sys
from multiprocessing import Pool
import numpy as np, pandas as pd
import st_lib as L, st_engine as E

OUT = L.HERE
ALL = E.STRATS + E.EXTRA


def table(B, T, cap=False, names=ALL, tag=""):
    rows = []
    for s in names:
        if s not in T:
            continue
        for p, m in E.evaluate(B, T[s], cap).items():
            rows.append(dict(strat=s, cap=cap, periodo=p, tag=tag, **m))
    return pd.DataFrame(rows)


def judge(t: pd.DataFrame, bhs: dict) -> pd.DataFrame:
    """Criteri dei tre periodi (senza placebo)."""
    rows = []
    for s, g in t.groupby("strat", sort=False):
        g = g.set_index("periodo"); c = {}
        for p in L.PERIODS:
            m = g.loc[p]
            c[p] = dict(pos=m["cagr"] > 0, bh=m["S"] > bhs[p]["S"], dd=m["dd"] >= -0.35, no2=m["fin_no2"] > 10000)
        rows.append(dict(strat=s, **{f"{p}_{k}": v for p, d in c.items() for k, v in d.items()},
                         periodi_ok=sum(all(d.values()) for d in c.values()), tutti=all(all(d.values()) for d in c.values())))
    return pd.DataFrame(rows)


def _p2(seed):
    rng = np.random.default_rng(seed)
    a = E.permute(A0, E.START, L.CUT, rng)
    B = E.base_btc(a); T = E.targets(E.directions(B))
    i0, i1 = E.span(B); out = {}
    for s in E.STRATS:
        Eq, days, Tr = E.run(B, T[s], i0, i1)
        out[s] = E.metrics(Eq, days, Tr, B["idx"], E.START, L.CUT)["S"]
    out["bh"] = E.bh(B, E.START, L.CUT)["S"]
    return out


if __name__ == "__main__":
    A0 = L.load_4h(L.CUT)
    B = E.base_btc(A0); D = E.directions(B); T = E.targets(D)
    bhs = {p: E.bh(B, a, b) for p, (a, b) in E.PER_ALL.items()}
    pd.DataFrame(bhs).T.to_csv(OUT / "buyhold.csv")
    t = pd.concat([table(B, T), table(B, T, cap=True)])
    t.to_csv(OUT / "risultati.csv", index=False)
    j = judge(t[~t["cap"] & t["strat"].isin(E.STRATS)], bhs); jc = judge(t[t["cap"] & t["strat"].isin(E.STRATS)], bhs)
    j.to_csv(OUT / "criteri.csv", index=False); jc.to_csv(OUT / "criteri_tetto.csv", index=False)

    # storia corta (solo Binance dal 17/08/2017): sensibilità del 2018–20
    Bs = E.base_btc(A0, long_hist=False); Ts = E.targets(E.directions(Bs))
    ts = table(Bs, Ts, names=E.STRATS, tag="storia corta"); ts.to_csv(OUT / "storia_corta.csv", index=False)

    # mappa dei parametri (descrizione)
    rows = []
    for n in L.ATRS:
        for k in L.FACTORS:
            Tg = E.targets(E.directions(B, n, k))
            x = table(B, Tg, names=E.STRATS); x["atr"], x["factor"] = n, k
            jj = judge(x, bhs).set_index("strat")
            x["tutti"] = x["strat"].map(jj["tutti"]); x["periodi_ok"] = x["strat"].map(jj["periodi_ok"])
            rows.append(x)
    g = pd.concat(rows); g.to_csv(OUT / "mappa.csv", index=False)

    # P1: posizioni traslate circolarmente (1.000) sull'intero 2018–26
    i0, i1 = E.span(B); nbar = i1 - i0; lo = 30 * 6
    rng = np.random.default_rng(20261123); p1 = []
    for s in E.STRATS:
        real = t[(t["strat"] == s) & ~t["cap"] & (t["periodo"] == "2018-26")]["S"].iloc[0]
        seg = T[s][i0 - 1:i1 - 1]; v = []
        for _ in range(1000):
            tg = T[s].copy(); tg[i0 - 1:i1 - 1] = np.roll(seg, int(rng.integers(lo, nbar - lo)))
            Eq, days, Tr = E.run(B, tg, i0, i1)
            v.append(E.metrics(Eq, days, Tr, B["idx"], E.START, L.CUT)["S"])
        v = np.array(v)
        p1.append(dict(strat=s, S_reale=real, plac_mediana=np.median(v), plac_95=np.quantile(v, 0.95), p=float((v >= real).mean())))
        print(p1[-1], flush=True)
    pd.DataFrame(p1).to_csv(OUT / "placebo_p1.csv", index=False)

    # P2: prezzi rimescolati a blocchi di 20 giorni (300 serie), indicatore ricalcolato
    with Pool(4) as pool:
        r = pd.DataFrame(pool.map(_p2, range(300)))
    r.to_csv(OUT / "placebo_p2_serie.csv", index=False)
    p2 = []
    for s in E.STRATS:
        real = t[(t["strat"] == s) & ~t["cap"] & (t["periodo"] == "2018-26")]["S"].iloc[0]
        p2.append(dict(strat=s, S_reale=real, plac_mediana=r[s].median(), plac_95=r[s].quantile(0.95), p=float((r[s] >= real).mean()),
                       quota_sopra_bh_plac=float((r[s] > r["bh"]).mean())))
    pd.DataFrame(p2).to_csv(OUT / "placebo_p2.csv", index=False)

    # stampa
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    with open(OUT / "risultati.txt", "w") as fh:
        def P(*a):
            print(*a); print(*a, file=fh)
        P("BUY & HOLD"); P(pd.DataFrame(bhs).T.round(3).to_string())
        for cap in (False, True):
            P("\nSTRATEGIE 10/3" + (" · tetto di rischio 25%" if cap else " · 1x pieno"))
            x = t[t["cap"] == cap]
            for col, f in (("fin", 0), ("dd", 3), ("S", 2), ("n", 0), ("wr", 2), ("fin_no2", 0)):
                P(col); P(x.pivot(index="strat", columns="periodo", values=col).loc[[s for s in ALL if s in T]].round(f).to_string())
        P("\nCRITERI (1x)"); P(j.to_string()); P("\nCRITERI (tetto)"); P(jc[["strat", "periodi_ok", "tutti"]].to_string())
        P("\nSTORIA CORTA 2018-20"); P(ts[ts["periodo"] == "2018-20"][["strat", "fin", "dd", "S", "n"]].round(3).to_string())
        P("\nMAPPA S 2018-26 (righe ATR, colonne fattore) e combinazioni che passano i tre periodi")
        for s in E.STRATS:
            x = g[(g["strat"] == s) & (g["periodo"] == "2018-26")]
            P(s, "| passano", int(x["tutti"].sum()), "su 16 | S b&h", round(bhs["2018-26"]["S"], 2))
            P(x.pivot(index="atr", columns="factor", values="S").round(2).to_string())
            P(x.pivot(index="atr", columns="factor", values="fin").round(0).to_string())
        P("\nPLACEBO P1"); P(pd.DataFrame(p1).round(3).to_string()); P("\nPLACEBO P2"); P(pd.DataFrame(p2).round(3).to_string())
