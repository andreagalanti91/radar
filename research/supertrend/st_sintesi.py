"""supertrend · sintesi per il README: zona stabile di 10/3 nella mappa, accordo del Supertrend con gli ingressi di W3.2."""
import numpy as np, pandas as pd
import st_lib as L, st_engine as E, st_w32 as K

g = pd.read_csv(L.HERE / "mappa.csv"); bh = pd.read_csv(L.HERE / "buyhold.csv", index_col=0)
rows = []
for s in E.STRATS:
    x = g[(g["strat"] == s) & (g["periodo"] == "2018-26")].pivot(index="atr", columns="factor", values="S")
    i, j = list(x.index).index(10), list(x.columns).index(3.0)
    nb = [x.iloc[a, b] for a in range(i - 1, i + 2) for b in range(j - 1, j + 2) if (a, b) != (i, j) and 0 <= a < 4 and 0 <= b < 4]
    v = x.iloc[i, j]; sb = bh.loc["2018-26", "S"]
    same = sum((n > sb) == (v > sb) for n in nb)
    al = g[(g["strat"] == s) & (g["periodo"] == "2018-26")]
    rows.append(dict(strat=s, S_10_3=v, vicini=len(nb), stesso_segno=same, min_vicini=min(nb), max_vicini=max(nb), mediana_griglia=float(np.median(x.to_numpy())),
                     rango_su_16=int((x.to_numpy() > v).sum()) + 1, stabile=bool(same >= 6 and min(nb) <= v <= max(nb)), passano_su_16=int(al["tutti"].sum()),
                     sopra_bh_su_16=int((x.to_numpy() > sb).sum())))
Z = pd.DataFrame(rows); Z.to_csv(L.HERE / "mappa_sintesi.csv", index=False)
pd.set_option("display.width", 250); print(Z.round(2).to_string())
# quote di combinazioni per periodo: positive e sopra il buy & hold
for p in L.PERIODS:
    x = g[g["periodo"] == p]; sb = bh.loc[p, "S"]
    print(p, x.assign(ok=(x["cagr"] > 0) & (x["S"] > sb) & (x["dd"] >= -0.35)).groupby("strat", sort=False)["ok"].sum().to_dict())
# accordo del Supertrend con gli ingressi di W3.2 (descrizione)
a4 = L.load_4h(L.CUT); d = L.daily_from(a4); X = K.st_inputs(d, a4); w = L.weekly_from(d)
dw = -pd.Series(L.supertrend(w["high"].to_numpy(), w["low"].to_numpy(), w["close"].to_numpy())[1], w.index)
d4 = -pd.Series(L.supertrend(a4["high"].to_numpy(), a4["low"].to_numpy(), a4["close"].to_numpy())[1], a4.index + pd.Timedelta(hours=4))
t = pd.read_csv(L.HERE / "w32_k_trade.csv"); t = t[(t["var"] == "W3.2") & t["periodo"].isin(["2018-20", "2021-26"])]
t["st1w"] = [dw.loc[s] == sd for s, sd in zip(pd.to_datetime(t["signal"]), t["side"])]
t["st1d"] = [X["SD"].loc[s] == sd for s, sd in zip(pd.to_datetime(t["signal"]), t["side"])]
t["st4h"] = [d4.loc[s + pd.Timedelta(days=1)] == sd for s, sd in zip(pd.to_datetime(t["signal"]), t["side"])]
t.to_csv(L.HERE / "accordo_w32.csv", index=False)
print(t.round(3).to_string())
print(t.groupby("periodo")[["st1w", "st1d", "st4h"]].agg(["sum", "count"]))
for c in ("st1w", "st1d", "st4h"):
    print(c, "pnl medio concorde", t[t[c]]["pnl"].mean().round(3), "discorde", t[~t[c]]["pnl"].mean().round(3), "n", int(t[c].sum()), int((~t[c]).sum()))
