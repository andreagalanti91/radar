import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "../w2_migliorie"); from eng import *
import numpy as np, pandas as pd
f = load_repo(); fl = load_long(f)
def z(s, n=180): return (s - s.rolling(n).mean()) / s.rolling(n).std()
def flows(x):
    out = {"F0": x["pf14z"], "F3": x["pf14z"].rolling(3).mean(), "F7": x["pf14z"].rolling(7).mean()}
    if "perp_delta" in x and x["perp_delta"].notna().sum() > 400:
        out["F28"] = z(x["perp_delta"].rolling(28).sum() / x["perp_vol"].rolling(28).sum())
    return out
def with_flow(x, s):
    y = x.copy(); y["pf14z"] = s.shift(1); return y            # disponibile dal vivo: fino al giorno prima
PER = {"2021→": (f, "2021-01-01", None), "2021–23": (f, "2021-01-01", "2023-12-31"), "2024→": (f, "2024-01-01", None), "2018–20": (fl, "2018-01-01", "2020-12-31")}
rows, EQ = [], {}
for per, (x, s, e) in PER.items():
    for name, fs in flows(x).items():
        y = with_flow(x, fs); fin, dd, eqs = {}, {}, {}
        for a in DOW:
            r = simulate(y, start=s, end=e, anchor=a); m = metrics(r); fin[a], dd[a], eqs[a] = m["final"], m["dd"], r["equity"]
        E = pd.DataFrame(eqs).ffill()
        def ens(cols):
            q = E[cols].mean(axis=1); return float(q.iloc[-1]), float((q / q.cummax() - 1).min() * 100)
        t3, t7 = ens(["SUN", "WED", "FRI"]), ens(list(DOW))
        rows.append(dict(periodo=per, flusso=name, dom=round(fin["SUN"]), dd_dom=round(dd["SUN"], 1), mediana=round(np.median(list(fin.values()))),
                         minimo=round(min(fin.values())), dd_peggiore=round(min(dd.values()), 1), T3=round(t3[0]), dd_T3=round(t3[1], 1), T7=round(t7[0]), dd_T7=round(t7[1], 1)))
        if per == "2021→": EQ[name] = E
d = pd.DataFrame(rows); d.to_csv("flussi_giorni.csv", index=False)
for per in PER: print("\n==", per); print(d[d.periodo == per].drop(columns="periodo").to_string(index=False))
print("\nB&H 2021→", round(metrics(bh(f))["final"]), "| W2 backtest (flusso domenica):", round(metrics(simulate(f))["final"]))
