"""Fase 2 dello studio preregistrato (PREREG.md): 18 configurazioni + K0/K1, IS/OOS, vicini, placebo, senza top 5, W3.

Uso: python research/mm_assorbimento/mm_run.py  → risultati.txt, riepilogo.csv, vicini.csv, sensibilita.csv, w3.csv,
trades_<regola>.csv in research/mm_assorbimento/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mm_bt import Cfg, Data, K0_START, OOS0, IS0, daily_equity, halves, run, stats, variants  # noqa: E402
from mm_data import ROOT, load  # noqa: E402
from mm_placebo import Placebo  # noqa: E402

ALPHA = 0.05 / 18
OUT = []


def say(s=""):
    print(s); OUT.append(s)


def configs():
    A1 = Cfg("A1", "A1h", win=24)
    A2 = Cfg("A2", "A4h", win=48)
    B1 = Cfg("B1", "B", absf=True)
    B2 = variants(B1, name="B2", mapthr=0.10)
    C1 = variants(B1, name="C1", w3=True)
    C2 = variants(A1, name="C2", w3=True)
    nb = {}
    for b in (A1, A2, C2):
        nb[b.name] = [variants(b, name=b.name + "a", vp=90, rp=20), variants(b, name=b.name + "b", th=0.05, oi=False)]
    for b in (B1, C1):
        nb[b.name] = [variants(b, name=b.name + "a", N=48, k=1.25), variants(b, name=b.name + "b", k=0.8)]
    nb["B2"] = [variants(B2, name="B2a", mapthr=1e-12), variants(B2, name="B2b", mapthr=0.30)]
    K0 = Cfg("K0", "B")
    K1 = Cfg("K1", "K1", N=24, cap=None)
    return [A1, A2, B1, B2, C1, C2], nb, [K0, K1]


def eval_cfg(dt, c):
    res = run(dt, c)
    eq = daily_equity(dt, res)
    tr = res.trades
    full = stats(tr, eq)
    i, o = halves(tr)
    si, so = stats(i), stats(o)
    top = tr.sort_values("r").iloc[:-5] if len(tr) > 5 else tr.iloc[:0]
    s5 = stats(top)
    row = dict(cfg=c.name, n=full["n"], wr=full["wr"], pf=full["pf"], mean=full["mean"], cap=full["cap"], ret=full["ret"],
               dd=full["dd"], mar=full["mar"], nl=full.get("nl", 0), ns=full.get("ns", 0),
               n_is=si["n"], pf_is=si["pf"], mean_is=si["mean"], cap_is=si["cap"],
               n_oos=so["n"], pf_oos=so["pf"], mean_oos=so["mean"], cap_oos=so["cap"], cap_no5=s5["cap"])
    return res, eq, row


def subper(eq: pd.Series, a, b):
    base = eq[eq.index < a]
    e0 = base.iloc[-1] if len(base) else 10000.0
    s = eq[(eq.index >= a) & (eq.index <= b)]
    e = pd.concat([pd.Series([e0]), s.reset_index(drop=True)])
    dd = float((e / e.cummax() - 1).min())
    ret = float(e.iloc[-1] / e0 - 1)
    return dict(cap=10000 * (1 + ret), ret=ret * 100, dd=dd * 100, mar=ret / abs(dd) if dd < 0 else np.nan)


def fmt(r):
    f = lambda x, d=2: "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"
    return (f"{r['cfg']:5s} n {r['n']:4d} (IS {r['n_is']:3d}/OOS {r['n_oos']:3d}, L {r['nl']}/S {r['ns']}) WR {f(r['wr'],1)}% "
            f"PF {f(r['pf'])} [IS {f(r['pf_is'])} OOS {f(r['pf_oos'])}] media {f(r['mean'],3)}% [IS {f(r['mean_is'],3)} "
            f"OOS {f(r['mean_oos'],3)}] cap {r['cap']:,.0f} DD {f(r['dd'],1)}% MAR {f(r['mar'])} senza top5 {r['cap_no5']:,.0f}")


def main():
    d = load()
    dt = Data(d)
    pl = Placebo(dt)
    rules, nb, ctrls = configs()
    say(f"Dati: {dt.idx[0]} → {dt.idx[-1]} (1h perp Binance), taker da 2022-01-01, mappe fino a {d['I'].index[-1]}; "
        f"ore mancanti riempite piatte: {len(d['missing'])}")
    say(f"IS {IS0.date()} → 2023-12-31, OOS {OOS0.date()} → {dt.idx[-1].date()}; Bonferroni α = 0,05/18 = {ALPHA:.4f}")
    rows, res_all, eqs = {}, {}, {}
    for c in rules + [x for v in nb.values() for x in v] + ctrls:
        res, eq, row = eval_cfg(dt, c)
        rows[c.name], res_all[c.name], eqs[c.name] = row, res, eq
    # placebo sulle 18 configurazioni + controlli
    for name, res in res_all.items():
        if len(res.trades) == 0:
            rows[name].update(p=np.nan, pk=np.nan, pmed=np.nan)
            continue
        p = pl.run(res.trades, w3=res.cfg.w3)
        rows[name].update(p=p["p"], pk=p["k"], pmed=p["med"] * 10000, preal=p["real"] * 10000)
    # controlli informativi dal 2021-01-22 e K0 + sola mappa
    extra = {}
    for c in [variants(ctrls[0], name="K0_2021", start=K0_START), variants(ctrls[1], name="K1_2021", start=K0_START),
              variants(ctrls[0], name="K0+mappa", mapthr=0.10)]:
        _, _, row = eval_cfg(dt, c); extra[c.name] = row
    # sensibilità (informative)
    sens = []
    for c in rules + ctrls:
        for tag, kw in (("2W", dict(tmode="2W")), ("24h", dict(tmax=24)), ("72h", dict(tmax=72))):
            _, _, row = eval_cfg(dt, variants(c, name=f"{c.name}_{tag}", **kw)); sens.append(row)
    # W3 e buy & hold
    w3eq = d["w3"]["equity"]
    w3eq = w3eq[w3eq.index <= dt.idx[-1].normalize()]
    spot = pd.read_csv(ROOT / "data/spot.csv", parse_dates=["date"]).set_index("date")["close"]
    bh = spot[(spot.index >= "2020-12-31") & (spot.index <= dt.idx[-1].normalize())]
    bh = bh / bh.iloc[0] * 10000
    bh22 = spot[(spot.index >= "2022-01-31") & (spot.index <= dt.idx[-1].normalize())]
    bh22 = bh22 / bh22.iloc[0] * 10000

    def eqstat(e):
        x = e / e.iloc[0]
        dd = float((x / x.cummax() - 1).min()); ret = float(x.iloc[-1] - 1)
        return dict(cap=10000 * (1 + ret) if e.iloc[0] == 10000 else float(e.iloc[-1]), ret=ret * 100, dd=dd * 100, mar=ret / abs(dd))
    w3s = eqstat(pd.concat([pd.Series([10000.0], [pd.Timestamp("2020-12-31")]), w3eq]))
    bhs, bh22s = eqstat(bh), eqstat(bh22)
    w3_22 = w3eq[w3eq.index >= "2022-01-31"]; w3_22s = eqstat(w3_22 / w3_22.iloc[0] * 10000)
    w3tr = d["w3"]["trades"] + [d["w3"]["open"]]
    # effetto su W3 (C1, C2 e vicini; informativo per le altre regole a W3 flat non applicabile: solo C)
    w3rows = []
    w3full = pd.concat([pd.Series([10000.0], [pd.Timestamp("2020-12-31")]), w3eq])
    for name in ["C1", "C1a", "C1b", "C2", "C2a", "C2b"]:
        ce = eqs[name] / 10000
        ce = ce.reindex(w3eq.index).ffill().fillna(1.0)
        comb = w3eq * ce
        combf = pd.concat([pd.Series([10000.0], [pd.Timestamp("2020-12-31")]), comb])
        r = dict(cfg=name)
        for tag, a, b in (("tot", pd.Timestamp("2021-01-01"), w3eq.index[-1]), ("21_23", pd.Timestamp("2021-01-01"), pd.Timestamp("2023-12-31")),
                          ("24_", OOS0, w3eq.index[-1])):
            s, s0 = subper(combf, a, b), subper(w3full, a, b)
            r.update({f"cap_{tag}": s["cap"], f"dd_{tag}": s["dd"], f"mar_{tag}": s["mar"],
                      f"w3cap_{tag}": s0["cap"], f"w3dd_{tag}": s0["dd"], f"w3mar_{tag}": s0["mar"]})
        w3rows.append(r)
    W3R = pd.DataFrame(w3rows).set_index("cfg")

    # ---- criteri
    say("\n== Configurazioni principali, vicini e controlli (10.000 $ al 01/01/2021, regole attive dal 2022-02-01)")
    for name in [r.name for r in rules]:
        say(fmt(rows[name]) + f" | placebo p {rows[name]['p']:.4f} (k {rows[name]['pk']}, mediana {rows[name]['pmed']:,.0f})")
        for v in nb[name]:
            say("   vicino " + fmt(rows[v.name]) + f" | placebo p {rows[v.name]['p']:.4f}")
    for c in ctrls:
        say("ctrl " + fmt(rows[c.name]) + f" | placebo p {rows[c.name]['p']:.4f}")
    for k, r in extra.items():
        say("info " + fmt(r).replace(r["cfg"] + " ", k + " "))
    say(f"\nW3 dal 2021: {w3s['cap']:,.0f} $ ({w3s['ret']:.1f}%), DD {w3s['dd']:.1f}%, MAR {w3s['mar']:.2f}, trade {len(w3tr)} "
        f"(WR {np.mean([t['pnl'] > 0 for t in w3tr]) * 100:.0f}%)")
    say(f"Buy & hold dal 2021: {bhs['cap']:,.0f} $ ({bhs['ret']:.1f}%), DD {bhs['dd']:.1f}%, MAR {bhs['mar']:.2f}")
    say(f"Dal 2022-02-01: buy & hold {bh22s['cap']:,.0f} $ DD {bh22s['dd']:.1f}%; W3 {w3_22s['cap']:,.0f} $ DD {w3_22s['dd']:.1f}%")

    say("\n== Criteri (configurazione principale)")
    K0, K1 = rows["K0"], rows["K1"]
    verdict = {}
    for c in rules:
        r = rows[c.name]
        c1 = r["n_is"] >= 30 and r["n_oos"] >= 30
        c2 = r["pf_is"] >= 1.2 and r["pf_oos"] >= 1.2 and r["cap"] > 10000 and (r["mar"] or 0) > 0
        refs = [K0, K1] + ([rows["B1"]] if c.name == "B2" else [])
        c3 = all(r["mean_oos"] > x["mean_oos"] and r["pf_oos"] > x["pf_oos"] for x in refs)
        c4 = r["p"] < ALPHA
        c5 = all(rows[v.name]["pf"] > 1 and rows[v.name]["mean_oos"] > 0 for v in nb[c.name])
        c6 = r["cap_no5"] > 10000
        crit = [c1, c2, c3, c4, c5, c6]
        c7 = None
        if c.w3:
            w = W3R.loc[c.name]
            c7 = all(w[f"cap_{t}"] > w[f"w3cap_{t}"] and w[f"mar_{t}"] > w[f"w3mar_{t}"] and w[f"dd_{t}"] >= w[f"w3dd_{t}"] - 2
                     for t in ("21_23", "24_"))
            crit.append(c7)
        ok = all(bool(x) for x in crit)
        v = "ACCETTATA per carta" if ok else ("SENZA POTENZA" if c.w3 and not c1 else "RESPINTA")
        verdict[c.name] = v
        say(f"{c.name}: 1 trade≥30/metà {c1} · 2 PF≥1,2 IS e OOS {c2} · 3 batte K0/K1 OOS {c3} · 4 placebo {c4} · "
            f"5 vicini {c5} · 6 senza top5 {c6}" + (f" · 7 W3+C {c7}" if c.w3 else "") + f" → {v}")
    say("\n== Effetto su W3 (portafoglio W3 + C a W3 flat)")
    for name, w in W3R.iterrows():
        say(f"{name}: tot {w['cap_tot']:,.0f} DD {w['dd_tot']:.1f}% MAR {w['mar_tot']:.2f} (W3 {w['w3cap_tot']:,.0f} DD {w['w3dd_tot']:.1f}% "
            f"MAR {w['w3mar_tot']:.2f}) · 21–23 {w['cap_21_23']:,.0f}/{w['w3cap_21_23']:,.0f} MAR {w['mar_21_23']:.2f}/{w['w3mar_21_23']:.2f} · "
            f"24→ {w['cap_24_']:,.0f}/{w['w3cap_24_']:,.0f} MAR {w['mar_24_']:.2f}/{w['w3mar_24_']:.2f}")
    say("\n== Sensibilità (informative)")
    for r in sens:
        say(fmt(r))
    # anni singoli e uscite delle principali
    say("\n== Anni (media % per trade / n) e motivi d'uscita delle principali e dei controlli")
    for name in [c.name for c in rules] + ["K0", "K1"]:
        tr = res_all[name].trades
        if len(tr) == 0:
            say(f"{name}: nessun trade"); continue
        y = tr.groupby(tr["entry"].dt.year)["r"].agg(["mean", "count"])
        ys = " ".join(f"{a}: {m * 100:+.2f}/{n}" for a, (m, n) in y.iterrows())
        rs = tr["reason"].value_counts().to_dict(); tt = tr["ttype"].value_counts().to_dict()
        lo, sh = tr[tr.side > 0]["r"], tr[tr.side < 0]["r"]
        say(f"{name}: {ys} · uscite {rs} · target {tt} · long media {lo.mean() * 100 if len(lo) else np.nan:+.3f}% ({len(lo)}) "
            f"short {sh.mean() * 100 if len(sh) else np.nan:+.3f}% ({len(sh)}) · W mediana {tr['W'].median() * 100:.2f}%")
    # output
    pd.DataFrame(rows.values()).to_csv(HERE / "riepilogo.csv", index=False, float_format="%.4f")
    pd.DataFrame(list(extra.values()) + sens).to_csv(HERE / "sensibilita.csv", index=False, float_format="%.4f")
    pd.DataFrame([rows[v.name] | {"base": k} for k, vs in nb.items() for v in vs]).to_csv(HERE / "vicini.csv", index=False,
                                                                                            float_format="%.4f")
    W3R.to_csv(HERE / "w3.csv", float_format="%.4f")
    for name in [c.name for c in rules] + ["K0", "K1"]:
        if len(res_all[name].trades):                          # le regole senza trade non scrivono file
            res_all[name].trades.to_csv(HERE / f"trades_{name}.csv", index=False, float_format="%.6f")
    (HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
    pd.to_pickle(dict(rows=rows, extra=extra, sens=sens, W3R=W3R, verdict=verdict, w3s=w3s, bhs=bhs, bh22s=bh22s,
                      w3_22s=w3_22s), "/tmp/radar-work/mm/out.pkl")


if __name__ == "__main__":
    main()
