import pandas as pd, ns
f = ns.load(); print("dati", f.index[0].date(), "→", f.index[-1].date(), "volume mancante:", int(f["volume"].isna().sum()))
V = ns.variants(f); rows = []
for name, (t, s) in V.items():
    a = ns.met(ns.sim(f, t, s, "2014-01-01", "2020-12-31")); rows.append(dict(variante=name, **a))
rows.append(dict(variante="Buy & hold", **ns.met(ns.bh(f, "2014-01-01", "2020-12-31"))))
d = pd.DataFrame(rows); d.to_csv("scelta_2014_2020.csv", index=False); print(d.to_string(index=False))
