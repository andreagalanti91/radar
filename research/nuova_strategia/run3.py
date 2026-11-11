import itertools, json, numpy as np, pandas as pd, ns
f = ns.load(); S, E = "2021-01-01", None
def n6(rule="W-SUN", n_vw=26, n_vb=13, out=0.8, k=4, rcap=0.25, start=S, end=E, anchor=6):
    w = ns.bars(f, rule); vb = ns.vol_balance(w, n_vb); st, vw = ns.st_vwap(w, n_vw, vb, out)
    return ns.sim(f, ns.to_daily(f, st), ns.to_daily(f, vw), start, end, rcap=rcap, anchor=anchor, trail_k=k, atr=ns.atr_w(f, rule))
out = {}
# 1) giudizio: tutte le varianti con k=4 (trasparenza) + scelta
V = ns.variants(f); A = ns.atr_w(f); rows = []
for name, (t, s) in V.items():
    r = ns.sim(f, t, s, S, trail_k=4, atr=A); m = ns.met(r)
    h1 = ns.met(ns.sim(f, t, s, S, "2023-12-31", trail_k=4, atr=A)); h2 = ns.met(ns.sim(f, t, s, "2024-01-01", trail_k=4, atr=A))
    rows.append(dict(variante=name + " · trail 4", **m, r2123=h1["rend_%"], r24=h2["rend_%"], dd24=h2["dd_%"]))
b = ns.met(ns.bh(f, S)); rows.append(dict(variante="Buy & hold", **b, r2123=ns.met(ns.bh(f, S, "2023-12-31"))["rend_%"], r24=ns.met(ns.bh(f, "2024-01-01"))["rend_%"]))
d = pd.DataFrame(rows); d.to_csv("giudizio_2021.csv", index=False); print(d.to_string(index=False))
base = n6(); mb = ns.met(base); pd.DataFrame(base["trades"]).to_csv("trades_N6.csv", index=False); base["equity"].round(0).to_csv("equity_N6.csv")
print("\nTRADE N6:"); print(pd.DataFrame(base["trades"])[["entry", "entry_px", "exit", "exit_px", "pnl"]].round(3).to_string(index=False))
# 2) vicini
nb = []
for n_vw, n_vb, o, k, rc in itertools.product((20, 26, 32), (10, 13, 16), (0.7, 0.8, 0.9), (3, 4, 5), (0.25,)):
    nb.append(dict(n_vw=n_vw, n_vb=n_vb, out=o, k=k, **ns.met(n6(n_vw=n_vw, n_vb=n_vb, out=o, k=k))))
nb = pd.DataFrame(nb); nb.to_csv("vicini.csv", index=False)
print("\nVICINI (81): finale mediana", int(nb.finale.median()), "min", nb.finale.min(), "max", nb.finale.max(), "| DD mediano", nb["dd_%"].median(), "peggiore", nb["dd_%"].min(), "| quota sopra B&H", round((nb.finale > b["finale"]).mean() * 100), "% | posizione della scelta (percentile)", round((nb.finale < mb["finale"]).mean() * 100))
for col in ("n_vw", "n_vb", "out", "k"): print(" ", col, nb.groupby(col).finale.median().round(0).to_dict())
print("  tetto rischio:", {rc: ns.met(n6(rcap=rc))["finale"] for rc in (None, 0.20, 0.25, 0.30)}, "DD:", {rc: ns.met(n6(rcap=rc))["dd_%"] for rc in (None, 0.20, 0.25, 0.30)})
# 3) giorno di chiusura
dd = []
for i, dname in enumerate(ns.DAYS): dd.append(dict(giorno=dname, **ns.met(n6(rule="W-" + dname, anchor=i))))
dd = pd.DataFrame(dd); dd.to_csv("giorni.csv", index=False); print("\nGIORNI DI CHIUSURA:"); print(dd[["giorno", "finale", "dd_%", "mar", "trade", "wr_%"]].to_string(index=False))
# 4) senza il trade migliore, anni, 2014-20 ricontrollo
t = pd.DataFrame(base["trades"]); best = t.pnl.max(); print("\nsenza il migliore: finale ≈", int(mb["finale"] / (1 + best)), "| migliore", round(best * 100, 1), "%")
e = base["equity"]; print("per anno:", {y: round((g.iloc[-1] / g.iloc[0] - 1) * 100, 1) for y, g in e.groupby(e.index.year)})
print("in posizione % dei giorni:", round(100 * (e.diff().abs() > 1e-9).mean()))
print("2014-20 (scelta):", ns.met(n6(start="2014-01-01", end="2020-12-31")), "\n2018:", ns.met(n6(start="2018-01-01", end="2018-12-31")))
