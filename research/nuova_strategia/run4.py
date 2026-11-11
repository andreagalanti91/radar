import pandas as pd, ns
f = ns.load(); V = ns.variants(f); A = ns.atr_w(f); rows = []
for name, (t, s) in V.items():
    for k in (None, 2, 2.5, 3, 4):
        a = ns.met(ns.sim(f, t, s, "2014-01-01", "2020-12-31", trail_k=k, atr=A)); b = ns.met(ns.sim(f, t, s, "2021-01-01", trail_k=k, atr=A))
        rows.append(dict(variante=name.split()[0], k=k or 0, mar_1420=a["mar"], dd_1420=a["dd_%"], fin_21=b["finale"], dd_21=b["dd_%"], mar_21=b["mar"], tr_21=b["trade"], wr_21=b["wr_%"]))
d = pd.DataFrame(rows); d.to_csv("esplorativo_griglia.csv", index=False)
print(d.sort_values("fin_21", ascending=False).head(8).to_string(index=False))
print("sopra buy&hold (25.159) nel 2021→:", int((d.fin_21 > 25159).sum()), "su", len(d), "| DD 2021→ migliore:", d.dd_21.max(), "| correlazione di rango MAR 2014-20 vs 2021→:", round(d.mar_1420.corr(d.mar_21, method="spearman"), 2))
