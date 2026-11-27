"""sol_ciclo · FASE 2 · varianti V1, V2, V3a, V3b (V3c/V3d solo se V1 o V2 operabile), esattamente come PREREG.md (commit d38c760).
Uscite: out_v.txt, risultati_v.csv, trades_v.csv."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "w32_asset2")); sys.path.insert(0, str(HERE))
import lib as L  # noqa: E402
from rapporto_a import table  # noqa: E402

S, IS_E, OOS_S, Y24 = "2021-01-11", "2022-12-31", "2023-01-01", "2024-01-01"
OUT, ROWS, TR = [], [], []
def p(s=""):
    print(s, flush=True); OUT.append(s)

f = L.cfeats("SOL"); E = str(f.index[-1].date()); fb, fe = L.cfeats("BTC"), L.cfeats("ETH")
sun = f.index[f.index.dayofweek == 6]

def gate_from(o, idx):                      # = w32_asset2/q4.py
    g = pd.Series(0, index=idx)
    for t in L.otrades(o):
        a, sd = pd.Timestamp(t["entry"]), (1 if t["side"] == "long" else -1)
        b = pd.Timestamp(t["exit"]) if t.get("exit") else idx[-1] + pd.Timedelta(days=1)
        g[(g.index >= a) & (g.index < b)] = sd
        if pd.Timestamp(t["signal"]) in g.index: g[pd.Timestamp(t["signal"])] = sd
    return g

def wpos(trs, idx):
    s = pd.Series(0, index=idx)
    for t in trs:
        a = pd.Timestamp(t["entry"]); b = pd.Timestamp(t["exit"]) if t.get("exit") else idx[-1] + pd.Timedelta(days=1)
        s[(s.index >= a) & (s.index < b)] = 1 if t["side"] == "long" else -1
    return s

esun = fe.index[fe.index.dayofweek == 6]
GATES = {"V1": pd.Series(1, index=sun), "V2": gate_from(L.csim(fe, "2020-06-01"), esun)}
bS = L.bh(f, S, E, 0.002); mETH = L.omet(L.csim(fe, S, E)); p(f"B&H SOL CAGR/DD {bS['cd']} · W3.2 ETH CAGR/DD {mETH['cd']} (soglia ★)")

# ------------------------------------------------------------------ V1, V2
res = {}
for v, g in GATES.items():
    o = L.csim(f, S, E, r=0.25, gate=g); m = L.omet(o); d = table(L.otrades(o), v, 0.25)
    cl = d[~d.uscita.str.startswith("aperta")]; wr_cl = float((cl.pnl_conto_pct > 0).mean() * 100) if len(cl) else 0
    per = {k: L.omet(L.csim(f, a, e, r=0.25, gate=g)) for k, a, e in (("IS", S, IS_E), ("OOS", OOS_S, E), ("2021-23", S, "2023-12-31"), ("2024", Y24, E))}
    nk = {k: L.omet(L.csim(f, S, E, r=0.25, k=k, gate=g)) for k in (2.0, 3.0)}
    pa, pm, pv = L.placebo(f["close"], S, E, L.otrades(o))
    c = dict(c1=(m["cd"] or -9) > bS["cd"] and (m["cd"] or -9) >= mETH["cd"], c2=m["dd"] >= -35, c3=wr_cl >= 60,
             c4=per["IS"]["ret"] > 0 and per["OOS"]["ret"] > 0 and per["2024"]["ret"] > 0, c5=m["n"] >= 8)
    conf = m["wo"] > 10000 and all((nk[k]["cd"] or -9) > bS["cd"] for k in nk)
    res[v] = dict(variante=v, fin=m["fin"], cagr=m["cagr"], dd=m["dd"], cd=m["cd"], n=m["n"], chiuse=len(cl), wr_chiuse=round(wr_cl),
                  wo=m["wo"], is_ret=per["IS"]["ret"], oos_ret=per["OOS"]["ret"], r2124=per["2021-23"]["ret"], r24=per["2024"]["ret"], dd24=per["2024"]["dd"],
                  k20_cd=nk[2.0]["cd"], k30_cd=nk[3.0]["cd"], plac_act=pa, plac_med=pm, p=round(pv, 4), **c, crit15=all(c.values()), conferma=conf)
    TR.append(d)
    lo, sh = cl[cl.lato == "long"], cl[cl.lato == "short"]
    p(f"\n=== {v} · rischio 25% · {S} → {E} ===")
    p(f"{m['fin']:,} $ ({m['ret']:+.0f}%, CAGR {m['cagr']}%), DD {m['dd']}%, CAGR/DD {m['cd']} · {len(cl)} chiuse + {len(d) - len(cl)} aperta, "
      f"WR chiuse {wr_cl:.0f}% · long {len(lo)} (vinti {(lo.pnl_conto_pct > 0).sum()}), short {len(sh)} (vinti {(sh.pnl_conto_pct > 0).sum()}) · "
      f"senza il migliore {m['wo']:,} $")
    p(f"IS {per['IS']['ret']:+.0f}% (DD {per['IS']['dd']}) · OOS {per['OOS']['ret']:+.0f}% (DD {per['OOS']['dd']}) · 2021–23 {per['2021-23']['ret']:+.0f}% "
      f"(DD {per['2021-23']['dd']}) · 2024→ {per['2024']['ret']:+.0f}% (DD {per['2024']['dd']})")
    p(f"vicini: trailing 2,0 CAGR/DD {nk[2.0]['cd']} ({nk[2.0]['fin']:,} $, DD {nk[2.0]['dd']}) · 3,0 {nk[3.0]['cd']} ({nk[3.0]['fin']:,} $, DD {nk[3.0]['dd']}) · "
      f"placebo: reale {pa}, mediana {pm}, p {pv:.4f}")
    p(f"criteri: {c} · 1–5 {all(c.values())} · conferma {conf}")
    e = o["equity"]; y = e.resample("YE").last(); y0 = pd.concat([pd.Series([10000.0], index=[e.index[0]]), y])
    p("per anno: " + " · ".join(f"{a.year} {b * 100:+.0f}%" for a, b in zip(y.index, y0.pct_change().dropna())))
    for r in (0.15, 0.10):
        oo = L.csim(f, S, E, r=r, gate=g); mm = L.omet(oo); TR.append(table(L.otrades(oo), v, r))
        m24 = L.omet(L.csim(f, Y24, E, r=r, gate=g))
        p(f"   (descrittivo) rischio {int(r * 100)}%: {mm['fin']:,} $, DD {mm['dd']}%, CAGR/DD {mm['cd']}, senza il migliore {mm['wo']:,} $, 2024→ {m24['ret']:+.0f}% (DD {m24['dd']})")
    op = o["open"]
    p("posizione al 24/11: " + (f"{op['side']} dal {op['entry']} a {op['entry_px']}, ultimo {op['last']:.2f}, trailing {op['trail']:.2f}, {op['pnl_close'] * 100:+.1f}%" if op else "flat")
      + f" · decisione in sospeso: {o['pending']}")
    p(d.drop(columns=["versione", "rischio"]).to_string(index=False))

# Holm m = 6
ps = sorted(((res[v]["p"], v) for v in res)); stop = False
for i, (pv, v) in enumerate(ps):
    thr = 0.05 / (6 - i); stop = stop or pv > thr; res[v]["holm_soglia"] = round(thr, 4); res[v]["holm_ok"] = not stop
for v in res:
    res[v]["operabile"] = bool(res[v]["crit15"] and res[v]["conferma"] and res[v]["holm_ok"])
    p(f"{v}: Holm soglia {res[v]['holm_soglia']} → {res[v]['holm_ok']} · OPERABILE {res[v]['operabile']}")
ROWS += list(res.values())

# ------------------------------------------------------------------ V3
def sleeves(a, e, sol_gate=None, r_sol=0.10):
    ob, oe, os_ = L.csim(fb, a, e), L.csim(fe, a, e), L.csim(f, a, e, r=r_sol, gate=sol_gate)
    return ob, oe, os_

def account(curves_w, a, e):
    idx = pd.date_range(a, e); tot = sum(w * (c / 10000).reindex(idx).ffill().fillna(1.0) for c, w in curves_w) * 10000
    cap = sum(w for _, w in curves_w) * 10000; yrs = (idx[-1] - idx[0]).days / 365.25
    dd = float((tot / tot.cummax() - 1).min()); cg = (tot.iloc[-1] / cap) ** (1 / yrs) - 1
    return dict(fin=round(float(tot.iloc[-1])), cap=round(cap), cagr=round(cg * 100, 1), dd=round(dd * 100, 1), cd=round(cg / abs(dd), 2)), tot

def no_best(o):
    e = o["equity"].copy(); tr = L.otrades(o); b = max(tr, key=lambda t: t["pnl"])
    r = e.pct_change().fillna(0); a = pd.Timestamp(b["entry"]); z = pd.Timestamp(b["exit"]) if b.get("exit") else e.index[-1]
    r[(r.index >= a) & (r.index <= z)] = 0.0
    return (1 + r).cumprod() * e.iloc[0], b

def v3(name, sol_gate, r_sol):
    out = {}
    for lab, a, e in (("intero", S, E), ("IS", S, IS_E), ("OOS", OOS_S, E), ("2021-23", S, "2023-12-31"), ("2024→", Y24, E)):
        ob, oe, os_ = sleeves(a, e, sol_gate, r_sol)
        mA, tA = account([(ob["equity"], 3), (oe["equity"], 3)], a, e); mB, tB = account([(ob["equity"], 3), (oe["equity"], 3), (os_["equity"], 1)], a, e)
        ok = mB["cd"] > mA["cd"] and mB["dd"] >= mA["dd"] - 3
        out[lab] = ok
        p(f"[{name} · {lab}] A (BTC 30k + ETH 30k): {mA['fin']:,} $ CAGR {mA['cagr']}% DD {mA['dd']}% C/DD {mA['cd']} · B (+ SOL 10k): {mB['fin']:,} $ "
          f"CAGR {mB['cagr']}% DD {mB['dd']}% C/DD {mB['cd']} → {'migliora' if ok else 'NON migliora'}")
        ROWS.append(dict(variante=name, periodo=lab, A_fin=mA["fin"], A_cagr=mA["cagr"], A_dd=mA["dd"], A_cd=mA["cd"], fin=mB["fin"], cagr=mB["cagr"],
                         dd=mB["dd"], cd=mB["cd"], migliora=ok))
        if lab == "intero":
            nb, b = no_best(os_); mN, _ = account([(ob["equity"], 3), (oe["equity"], 3), (nb, 1)], a, e)
            okn = mN["cd"] > mA["cd"] and mN["dd"] >= mA["dd"] - 3; out["senza_migliore"] = okn
            p(f"   senza il trade migliore di SOL ({b['entry']}, {b['pnl'] * 100:+.0f}%): B {mN['fin']:,} $ DD {mN['dd']}% C/DD {mN['cd']} → {'migliora' if okn else 'NON migliora'}")
            ROWS.append(dict(variante=name, periodo="intero senza migliore SOL", A_cd=mA["cd"], A_dd=mA["dd"], fin=mN["fin"], dd=mN["dd"], cd=mN["cd"], migliora=okn))
            idx = pd.date_range(a, e); rs = (os_["equity"]).reindex(idx).ffill().pct_change().dropna(); ra = tA.pct_change().dropna()
            inpos = pd.Series(False, index=idx)
            for t in L.otrades(os_):
                inpos[(inpos.index >= pd.Timestamp(t["entry"])) & (inpos.index <= (pd.Timestamp(t["exit"]) if t.get("exit") else idx[-1]))] = True
            j = rs.index.intersection(ra.index); jp = j[inpos.reindex(j).to_numpy()]
            ws, wa = os_["equity"].reindex(idx).ffill().resample("W-SUN").last().pct_change().dropna(), tA.resample("W-SUN").last().pct_change().dropna()
            yrs = (pd.Timestamp(e) - pd.Timestamp(a)).days / 365.25; ntr = len(L.otrades(os_))
            sw = sun[(sun >= pd.Timestamp(a))]; ps_ = wpos(L.otrades(os_), sw); pb_ = wpos(L.otrades(ob), sw); pe_ = wpos(L.otrades(oe), sw)
            ip = ps_ != 0
            def ov(x): return (f"stesso verso {100 * (x[ip] == ps_[ip]).mean():.0f}%, opposto {100 * ((x[ip] != 0) & (x[ip] != ps_[ip])).mean():.0f}%, "
                               f"flat {100 * (x[ip] == 0).mean():.0f}%")
            p(f"   correlazione giornaliera SOL–A {rs[j].corr(ra[j]):.2f} (solo giorni SOL in posizione {rs[jp].corr(ra[jp]):.2f}), settimanale "
              f"{ws.corr(wa.reindex(ws.index)):.2f} · operazioni SOL {ntr} ({ntr / yrs:.1f} l'anno; A ne fa {(len(L.otrades(ob)) + len(L.otrades(oe))) / yrs:.1f}) · "
              f"settimane SOL in posizione {int(ip.sum())}: BTC {ov(pb_)}; ETH {ov(pe_)}")
            yA = tA.resample("YE").last(); yB = tB.resample("YE").last()
            yA0 = pd.concat([pd.Series([60000.0]), yA.reset_index(drop=True)]).pct_change().dropna().to_numpy()
            yB0 = pd.concat([pd.Series([70000.0]), yB.reset_index(drop=True)]).pct_change().dropna().to_numpy()
            p("   per anno A / B: " + " · ".join(f"{d.year} {x * 100:+.0f}%/{z * 100:+.0f}%" for d, x, z in zip(yA.index, yA0, yB0)))
    verdict = out["intero"] and out["IS"] and out["OOS"] and out["senza_migliore"]
    p(f"{name}: MIGLIORA secondo PREREG = {verdict} ({out})"); ROWS.append(dict(variante=name, periodo="VERDETTO", migliora=verdict))
    return verdict

p("\n=== V3 · portafoglio (conto unico in dollari, pesi 30/30/10) ===")
v3a = v3("V3a (SOL base 10%)", None, 0.10); v3b = v3("V3b (SOL base 25%)", None, 0.25)
opv = [v for v in res if res[v]["operabile"]]
if opv:
    best = max(opv, key=lambda v: res[v]["cd"]); v3(f"V3c ({best} 10%)", GATES[best], 0.10); v3(f"V3d ({best} 25%)", GATES[best], 0.25)
else:
    p("V3c/V3d non calcolate: né V1 né V2 operabili (PREREG).")
pd.DataFrame(ROWS).to_csv(HERE / "risultati_v.csv", index=False); pd.concat(TR).to_csv(HERE / "trades_v.csv", index=False)
(HERE / "out_v.txt").write_text("\n".join(OUT) + "\n")
