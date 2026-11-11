"""Parte 2 · regole T1–T8 preregistrate (una sola corsa). Uso: python3 regole.py → regole.csv, regole.txt, trade_w2_diagnosi.csv"""
import numpy as np
import pandas as pd
import lib
from radar import weekly as W

f, fl = lib.load()
w, d, mo = lib.indicators(fl)
wk = W.weekly_bars(fl)                      # W2 sulla storia lunga: dal 2021 identica al tool (verificato)
OUT = []
def log(s=""):
    print(s); OUT.append(str(s))

c = w["wclose"]
ms, mz = w["macd"] > w["sig"], w["macd"] > 0
fab = w["m_close"] > w["m_sma10"]
def ls(lo, sh, short):
    return (lo.astype(float) - (sh.astype(float) if short else 0.0))
def state(name, short=False):
    if name == "T1": return ls((c > w["sma200"]) & ms, (c < w["sma200"]) & ~ms, short)
    if name == "T2": return ls((c > w["ema200"]) & ms, (c < w["ema200"]) & ~ms, short)
    if name == "T3": return ls((w["slope28"] > 0) & mz, (w["slope28"] < 0) & ~mz, short)
    if name == "T4":
        up = mo["m_close"] > mo["m_sma10"]
        return ls(up, ~up & mo["m_sma10"].notna(), short)
    if name == "T4m": return ls(fab & ms, ~fab & ~ms, short)
hot, h = [], False
for v in w["mayer"]:
    h = True if v > 2.4 else (False if v < 2.0 else h)
    hot.append(h)
hot = pd.Series(hot, w.index)
GATES = {"T5 Mayer>2,4 esce": dict(gate=~hot, xexit=hot), "T6 volume>media20": dict(gate=w["vr20"] > 1.0),
         "T7a MACD mensile>0": dict(gate=w["m_hist"] > 0), "T7b RSI mensile>50": dict(gate=w["m_rsi"] > 50),
         "T8 SMA200g+pendenza": dict(gate=(c > w["sma200"]) & (w["slope28"] > 0))}
SPL = (("2021-01-01", "2023-12-31"), ("2024-01-01", None))
rows = []
def add(name, r, rp, base=None, basep=None):
    m = lib.met(r)
    a, b = lib.met(r, *SPL[0]), lib.met(r, *SPL[1])
    p = lib.met(rp)
    row = dict(regola=name, finale=m["final"], rend=m["ret"], dd=m["dd"], n=m["n"], wr=m["wr"], mar=m["mar"], tim=m["tim"],
               senza_best=m["nobest"], r2123=a["ret"], dd2123=a["dd"], mar2123=a["mar"], r24=b["ret"], dd24=b["dd"], mar24=b["mar"],
               pre_rend=p["ret"], pre_dd=p["dd"], pre_mar=p["mar"], pre_n=p["n"])
    if base is not None:
        row["cambiati_2021"] = "%d/%d" % lib.changed(base, r)
        row["cambiati_pre"] = "%d/%d" % lib.changed(basep, rp)
    rows.append(row)

# riferimenti
w2 = lib.sim_w2(fl, wk); w2p = lib.sim_w2(fl, wk, start="2018-01-01", end="2020-12-31")
add("W2 com'è (pre=2018-20)", w2, w2p)
add("Buy&hold (pre=2018-20)", lib.bh(fl), lib.bh(fl, "2018-01-01", "2020-12-31"))
add("Buy&hold (pre=2014-20)", lib.bh(fl), lib.bh(fl, "2014-01-01", "2020-12-31"))
for nm in ("T1", "T2", "T3", "T4", "T4m"):
    for short in (False, True):
        t = state(nm, short)
        add(f"{nm} {'L/S' if short else 'long'} (pre=2014-20)", lib.sim_state(fl, t), lib.sim_state(fl, t, "2014-01-01", "2020-12-31"))
res = {}
for nm, kw in GATES.items():
    r, rp = lib.sim_w2(fl, wk, **kw), lib.sim_w2(fl, wk, start="2018-01-01", end="2020-12-31", **kw)
    res[nm] = (r, rp)
    add("W2+" + nm, r, rp, w2, w2p)
t = pd.DataFrame(rows)
t.to_csv(lib.HERE / "regole.csv", index=False)
pd.set_option("display.width", 250)
log(t.to_string(index=False))

# diagnosi: stato dei filtri al segnale di ogni long W2 (2018→oggi) + cosa cambia
log("\n== Long W2 e stato dei filtri alla domenica del segnale (True = ingresso ammesso)")
diag = []
for per, r in (("2018-20", w2p), ("2021+", w2)):
    for tr in r["trades"]:
        if tr["side"] != "long": continue
        s = pd.Timestamp(tr["signal"])
        row = dict(periodo=per, segnale=tr["signal"], uscita=tr["exit"], pnl=round(tr["pnl"] * 100, 1), mayer=round(w["mayer"].loc[s], 2),
                   macd12269_su=bool(ms.loc[s]), faber=bool(fab.loc[s]))
        for nm, kw in GATES.items():
            row[nm.split()[0]] = bool(kw["gate"].reindex(w.index).fillna(True).loc[s])
        diag.append(row)
dg = pd.DataFrame(diag)
dg.to_csv(lib.HERE / "trade_w2_diagnosi.csv", index=False)
log(dg.to_string(index=False))
log("\n== Trade delle varianti che differiscono da W2")
for nm, (r, rp) in res.items():
    for per, base, var in (("2018-20", w2p, rp), ("2021+", w2, r)):
        kb = {(x["entry"], x["exit"]): x for x in base["trades"]}; kv = {(x["entry"], x["exit"]): x for x in var["trades"]}
        out = [f"−{k[0]}→{k[1]} {v['pnl']*100:+.0f}%" for k, v in kb.items() if k not in kv] + [f"+{k[0]}→{k[1]} {v['pnl']*100:+.0f}%" for k, v in kv.items() if k not in kb]
        log(f"{nm} · {per}: " + ("; ".join(out) if out else "nessuna differenza"))
log("\n== Stato dei filtri fra 12/2017 e 02/2018 (top del ciclo; W2 nel mio motore ha flusso proxy solo dal 2018)")
g = pd.DataFrame({k.split()[0]: v["gate"] for k, v in GATES.items()}).loc["2017-12-03":"2018-02-11"]
g["mayer"] = w["mayer"].round(2); g["W2long"] = wk["long"].reindex(g.index); g["flow"] = wk["flow"].reindex(g.index).round(2)
log(g.to_string())
(lib.HERE / "regole.txt").write_text("\n".join(OUT))
