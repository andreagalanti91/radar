"""Punto 2: stesse regole sulla storia lunga (2015 -> 2020), 4 versioni {flusso si/no} x {F1 si/no}, per ciclo."""
from lib import *
repo, long = load()
print("pf14z vero dal", repo["pf14z"].first_valid_index().date(), "| proxy CVD spot dal", long["pf14z"].first_valid_index().date(),
      "| funding dal", repo["funding"].first_valid_index().date())
CYC = [("2015-17 toro", "2015-01-01", "2017-12-31"), ("2018 orso", "2018-01-01", "2018-12-31"), ("2019-20", "2019-01-01", "2020-12-31"),
       ("2015-20 tutto", "2015-01-01", "2020-12-31"), ("2018-20", "2018-01-01", "2020-12-31"), ("2021-oggi", "2021-01-01", None)]
VER = [("flusso+F1 (in uso)", dict()), ("flusso, no F1", dict(f1=False)), ("no flusso, F1", dict(flow="none")),
       ("no flusso, no F1", dict(flow="none", f1=False))]
rows, tr_rows = [], []
for name, kw in VER:
    r = run(long, start="2015-01-01", **kw)          # una sola simulazione continua 2015 -> oggi
    e = r["equity"]; T = all_trades(r)
    for t in T:
        tr_rows.append(dict(versione=name, **{k: t[k] for k in ("signal", "entry", "side", "exit", "reason")}, pnl=round(t["pnl"] * 100, 1)))
    for cn, a, b in CYC:
        seg = e[(e.index >= a) & (e.index <= (b or e.index[-1]))]
        tt = [t for t in T if a <= t["entry"] <= (b or "9999")]
        rows.append(dict(versione=name, ciclo=cn, **stats(seg, tt)))
for cn, a, b in CYC:
    rows.append(dict(versione="buy & hold", ciclo=cn, **stats(bh(long, a, b))))
df = pd.DataFrame(rows); df.to_csv(HERE / "s2_storia.csv", index=False)
pd.DataFrame(tr_rows).to_csv(HERE / "s2_trades.csv", index=False)
pd.set_option("display.width", 250)
print(df.to_string(index=False))
t = pd.DataFrame(tr_rows)
print(t[(t.versione == "flusso+F1 (in uso)") & (t.entry < "2021")].to_string(index=False))
print(t[(t.versione == "no flusso, F1") & (t.entry < "2021")].to_string(index=False))
