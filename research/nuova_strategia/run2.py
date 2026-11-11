import pandas as pd, ns
f = ns.load(); V = ns.variants(f); A = ns.atr_w(f); rows = []
for name, (t, s) in V.items():
    for k in (None, 2, 2.5, 3, 4):
        a = ns.met(ns.sim(f, t, s, "2014-01-01", "2020-12-31", trail_k=k, atr=A)); rows.append(dict(variante=name, k=k or 0, **a))
d = pd.DataFrame(rows); d.to_csv("scelta_trailing_2014_2020.csv", index=False)
print(d.pivot(index="variante", columns="k", values="mar").to_string()); print(d.pivot(index="variante", columns="k", values="dd_%").to_string())
print(d.pivot(index="variante", columns="k", values="finale").to_string()); print(d.pivot(index="variante", columns="k", values="trade").to_string())
