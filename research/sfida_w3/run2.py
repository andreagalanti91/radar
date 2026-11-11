import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "../w2_migliorie"); from eng import *
import numpy as np, pandas as pd
f = load_repo(); fl = load_long(f)
def wf(x, n):
    y = x.copy(); y["pf14z"] = x["pf14z"].rolling(n).mean().shift(1); return y
cap = lambda R: (lambda wk, d: min(1.0, R / (2.5 * wk["atr"] / wk["close"])))
def run(x, s, e, days, n=1, **kw):
    E = pd.DataFrame({a: simulate(wf(x, n), start=s, end=e, anchor=a, **kw)["equity"] for a in days}).ffill(); q = E.mean(axis=1)
    yrs = (q.index[-1] - q.index[0]).days / 365.25; dd = float((q / q.cummax() - 1).min()); cg = (q.iloc[-1] / q.iloc[0]) ** (1 / yrs) - 1
    ntr = sum(len(simulate(wf(x, n), start=s, end=e, anchor=a, **kw)["trades"]) for a in days)
    return dict(finale=round(float(q.iloc[-1])), cagr=round(cg * 100, 1), dd=round(dd * 100, 1), mar=round(cg / abs(dd), 2), trade=ntr), q
D3, D7 = ["SUN", "WED", "FRI"], list(DOW)
CFG = {"W2 dal vivo (domenica, flusso 1g)": (["SUN"], 1, {}),
       "W2 'giorno medio' (7 tranche, flusso 1g)": (D7, 1, {}),
       "A · 3 tranche (dom-mer-ven)": (D3, 1, {}),
       "B · A + flusso medio 3 giorni": (D3, 3, {}),
       "C · B + cricchetto + liquidità 3,5%": (D3, 3, dict(ratchet=True, idle=0.035)),
       "W3 · C + tetto di rischio long 25%": (D3, 3, dict(ratchet=True, idle=0.035, lev_fn=cap(0.25))),
       "W3 su 7 tranche": (D7, 3, dict(ratchet=True, idle=0.035, lev_fn=cap(0.25))),
       "Domenica sola + flusso 3g + cricchetto + liquidità + tetto": (["SUN"], 3, dict(ratchet=True, idle=0.035, lev_fn=cap(0.25)))}
rows = []; EQ = {}
for name, (days, n, kw) in CFG.items():
    r = dict(strategia=name)
    for per, (x, s, e) in {"21": (f, "2021-01-01", None), "2123": (f, "2021-01-01", "2023-12-31"), "24": (f, "2024-01-01", None), "1820": (fl, "2018-01-01", "2020-12-31"), "18": (fl, "2018-01-01", "2018-12-31")}.items():
        m, q = run(x, s, e, days, n, **kw)
        if per == "21": r.update(finale=m["finale"], cagr=m["cagr"], dd=m["dd"], mar=m["mar"], trade=m["trade"]); EQ[name] = q
        else: r.update({f"fin_{per}": m["finale"], f"dd_{per}": m["dd"]})
    rows.append(r)
d = pd.DataFrame(rows); d.to_csv("confronto.csv", index=False); print(d.to_string(index=False))
b = metrics(bh(f)); print("B&H 2021→", round(b["final"]), round(b["dd"], 1))
q = EQ["W3 · C + tetto di rischio long 25%"]; q.round(0).to_csv("equity_W3.csv")
print("W3 per anno:", {y: round((g.iloc[-1] / g.iloc[0] - 1) * 100, 1) for y, g in q.groupby(q.index.year)})
q0 = EQ["W2 dal vivo (domenica, flusso 1g)"]; print("W2 vivo per anno:", {y: round((g.iloc[-1] / g.iloc[0] - 1) * 100, 1) for y, g in q0.groupby(q0.index.year)})
