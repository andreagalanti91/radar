"""Fase 4 · scelta sul 2014–2020, giudizio sul 2021+, placebo, vicini, portafoglio 70/30 (PREREG.md). Uso: python3 sw_run.py
Output: risultati.txt, griglia.csv, trade_scelta.csv, placebo.csv, equity.csv"""
from __future__ import annotations

import itertools
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sw_engine as E  # noqa: E402
from radar import weekly as W  # noqa: E402

F, FL = E.frames()
OUT = []
NPL = 1000
RNG = np.random.default_rng(20261122)


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def fm(m):
    return (f"{m['fin']:>7,} $ · CAGR {100*m['cagr']:5.1f}% · DD {100*m['dd']:6.1f}% · C/DD {m['cdd']:5.2f} · trade {m['n']:3d} · "
            f"WR {100*m['wr']:4.1f}% · PF {m['pf']:4.2f} · medio {100*m['avg']:5.2f}% · peggiore {100*m['worst']:5.1f}% · "
            f"durata {m['days']:.0f} g · in posizione {100*m['inpos']:.0f}%")


def run(S, cfg, a, b=None, **kw):
    r = E.simulate(S, *cfg, start=a, end=b, **kw)
    return r, E.metrics(r)


# ------------------------------------------------------------------ 0. controlli del motore
SL, ST = E.signals(FL), E.signals(F)
cut = F[F.index <= "2024-06-30"]
SC = E.signals(cut)
n = len(cut)
same = all(np.array_equal(SC["sig"][k], ST["sig"][k][:n]) and np.allclose(SC["stp"][k], ST["stp"][k][:n], equal_nan=True)
           for k in SC["sig"]) and all(np.array_equal(SC["reg"][k], ST["reg"][k][:n]) for k in SC["reg"])
say("Controllo 1 · nessuna informazione dal futuro (segnali e regimi identici troncando i dati al 30/06/2024):", same)
assert same
r, m = run(ST, ("X", "R0", "L", "SF", "T10"), "2021-01-01")
t = r["trades"][0]
i0 = t["i0"]
c = ST["C"][i0 - 1]
say(f"Controllo 2 · primo trade X/R0/L/SF/T10: segnale {ST['idx'][i0-1].date()} chiusura {c:.0f}, ingresso {t['entry_px']:.0f} "
    f"(apertura {ST['O'][i0]:.0f} + 0,1%), stop {t['stop']:.0f} (−7,5%), TP {c*1.1:.0f}, uscita {t['parts']}, pnl {100*t['pnl']:.2f}%")
assert abs(t["stop"] / c - 0.925) < 1e-9 and abs(t["entry_px"] / ST["O"][i0] - 1.001) < 1e-9
pn = np.array([x["pnl"] for x in r["trades"]])
say(f"Controllo 3 · prodotto dei trade = equity finale: {np.prod(1+pn):.6f} = {r['equity'].iloc[-1]:.6f}")
assert abs(np.prod(1 + pn) - r["equity"].iloc[-1]) < 1e-9
w31 = W.simulate(F)["equity"]
assert round(float(w31.iloc[-1])) == 27190
bh = F.loc["2021-01-01":, "close"]
say(f"Riferimenti 2021+: W3.1 {w31.iloc[-1]:,.0f} $ (DD {100*(w31/w31.cummax()-1).min():.1f}%) · buy & hold "
    f"{10000*bh.iloc[-1]/F.loc['2021-01-01','open']:,.0f} $ (DD {100*(bh/bh.cummax()-1).min():.1f}%)")

# ------------------------------------------------------------------ 1. griglia: scelta 2014–20 e descrittivo 2021+
CFGS = list(itertools.product(E.ENTRIES, E.REGIMES, E.SIDES, E.STOPS, E.TPS))
rows = []
for cfg in CFGS:
    _, p = run(SL, cfg, "2014-06-01", "2020-12-31")
    _, p1 = run(SL, cfg, "2014-06-01", "2017-12-31")
    _, p2 = run(SL, cfg, "2018-01-01", "2020-12-31")
    _, j = run(ST, cfg, "2021-01-01")
    _, j1 = run(ST, cfg, "2021-01-01", "2023-12-31")
    _, j2 = run(ST, cfg, "2024-01-01")
    rows.append(dict(cfg="/".join(cfg), entry=cfg[0], regime=cfg[1], side=cfg[2], stop=cfg[3], tp=cfg[4],
                     pre_fin=p["fin"], pre_cagr=p["cagr"], pre_dd=p["dd"], pre_cdd=p["cdd"], pre_n=p["n"], pre_pf=p["pf"],
                     pre_pf_1417=p1["pf"], pre_pf_1820=p2["pf"],
                     fin=j["fin"], cagr=j["cagr"], dd=j["dd"], cdd=j["cdd"], n=j["n"], wr=j["wr"], pf=j["pf"], worst=j["worst"],
                     days=j["days"], inpos=j["inpos"], is_fin=j1["fin"], is_pf=j1["pf"], oos_fin=j2["fin"], oos_pf=j2["pf"]))
G = pd.DataFrame(rows)
G["ammissibile"] = (G.pre_n >= 40) & (G.pre_pf_1417 >= 1.2) & (G.pre_pf_1820 >= 1.2) & (G.pre_dd >= -0.30)
G.to_csv(HERE / "griglia.csv", index=False)

say(f"\n== SCELTA (2014-06 → 2020-12) == configurazioni {len(G)} · con ≥ 40 trade {(G.pre_n >= 40).sum()} · ammissibili {G.ammissibile.sum()}")
say(f"buy & hold 2014-06 → 2020-12: {10000*FL.loc['2020-12-31','close']/FL.loc['2014-06-01','open']:,.0f} $")
pool = G[G.ammissibile] if G.ammissibile.any() else G[G.pre_n >= 40]
if not G.ammissibile.any():
    say("NESSUNA configurazione ammissibile: S* = migliore CAGR/DD fra quelle con ≥ 40 trade (come da PREREG)")
pool = pool.sort_values("pre_cdd", ascending=False)
say("Prime 10 per CAGR/DD nel 2014–20 (fra le ammissibili):")
for _, x in pool.head(10).iterrows():
    say(f"  {x.cfg:18s} 2014–20: {x.pre_fin:>9,.0f} $ · DD {100*x.pre_dd:6.1f}% · C/DD {x.pre_cdd:5.2f} · trade {x.pre_n:3d} · "
        f"PF {x.pre_pf_1417:.2f}/{x.pre_pf_1820:.2f}  ||  2021+: {x.fin:>7,.0f} $ · DD {100*x.dd:6.1f}% · PF {x.pf:.2f}")
STAR = tuple(pool.iloc[0].cfg.split("/"))
say("S* =", "/".join(STAR))
say("Finalisti per tipo d'ingresso (migliore ammissibile):")
for e in E.ENTRIES:
    q = pool[pool.entry == e]
    if len(q):
        x = q.iloc[0]
        say(f"  {x.cfg:18s} 2014–20 C/DD {x.pre_cdd:5.2f} ({x.pre_fin:,.0f} $) || 2021+: {x.fin:,.0f} $ · DD {100*x.dd:.1f}% · PF {x.pf:.2f} "
            f"· IS {x.is_fin:,.0f} / OOS {x.oos_fin:,.0f}")
    else:
        say(f"  {e}: nessuna ammissibile")

# ------------------------------------------------------------------ 2. giudizio di S* sul 2021+
say("\n== GIUDIZIO di S* (2021-01-01 → 2026-11-15, 10.000 $) ==")
rs, ms = run(ST, STAR, "2021-01-01")
_, mi = run(ST, STAR, "2021-01-01", "2023-12-31")
_, mo = run(ST, STAR, "2024-01-01")
say("2021+   :", fm(ms))
say("IS 21–23:", fm(mi))
say("OOS 24–26:", fm(mo))
eq = rs["equity"]
say("Per anno: " + " · ".join(f"{y} {100*(g.iloc[-1]/(eq[:str(y-1)].iloc[-1] if y > 2021 else 1.0)-1):+.1f}%"
                              for y, g in eq.groupby(eq.index.year)))
tr = pd.DataFrame([dict(ingresso=x["entry"].date(), lato="long" if x["side"] > 0 else "short", prezzo=round(x["entry_px"], 0),
                        stop_pct=round(100 * x["d"], 1), uscita=x["exit"].date(), motivo=x["reason"], giorni=x["days"],
                        pnl_pct=round(100 * x["pnl"], 2)) for x in rs["trades"]])
tr.to_csv(HERE / "trade_scelta.csv", index=False)
say("Motivi d'uscita:", tr.groupby("motivo").pnl_pct.agg(["count", "mean"]).round(2).to_dict("index"))
say("Per lato:", tr.groupby("lato").pnl_pct.agg(["count", "mean", "sum"]).round(2).to_dict("index"))
pn = np.sort(np.array([x["pnl"] for x in rs["trades"]]))
no2 = 10000 * np.prod(1 + pn[:-2]) if len(pn) > 2 else 10000
c1 = ms["fin"] > 10000 and mi["pf"] >= 1.2 and mo["pf"] >= 1.2
c2 = ms["dd"] >= -0.20
c4 = no2 > 10000
say(f"Criterio 1 (finale > 10k e PF ≥ 1,2 in IS e OOS): {c1} · PF IS {mi['pf']:.2f} · PF OOS {mo['pf']:.2f}")
say(f"Criterio 2 (DD entro −20%): {c2} · DD {100*ms['dd']:.1f}%")
say(f"Criterio 4 (senza i 2 trade migliori): {c4} · {no2:,.0f} $")


def placebo(S, cfg, a, real, nrun=NPL):
    """Ingressi a caso nei giorni in cui il regime ammette il lato; stesso numero per lato; distanze ricampionate."""
    idx = S["idx"]
    t0 = idx.searchsorted(pd.Timestamp(a))
    dist = {s: np.array([x["d"] for x in real if x["side"] == s]) for s in (1, -1)}
    need = {s: len(dist[s]) for s in (1, -1)}
    days = {s: np.arange(t0, len(idx) - 2)[S["reg"][(cfg[1], s)][t0:len(idx) - 2]] for s in (1, -1)}
    out = []
    for _ in range(nrun):
        forced = {}
        for it in range(8):
            got = {1: 0, -1: 0}
            if forced:
                rr = E.simulate(S, *cfg, start=a, forced=forced)
                for x in rr["trades"]:
                    got[x["side"]] += 1
            miss = {s: need[s] - got[s] for s in (1, -1)}
            if all(v <= 0 for v in miss.values()):
                break
            for s in (1, -1):
                if miss[s] > 0 and len(days[s]):
                    for d in RNG.choice(days[s], size=min(miss[s], len(days[s])), replace=False):
                        forced.setdefault(int(d), (s, float(RNG.choice(dist[s]))))
        rr = E.simulate(S, *cfg, start=a, forced=forced)
        out.append((rr["equity"].iloc[-1] * 10000, len(rr["trades"])))
    return np.array(out)


pl = placebo(ST, STAR, "2021-01-01", rs["trades"])
p3 = (1 + (pl[:, 0] >= ms["fin"]).sum()) / (1 + len(pl))
c3 = p3 <= 0.05
say(f"Criterio 3 (placebo, {len(pl)} simulazioni): {c3} · p = {p3:.3f} · placebo mediana {np.median(pl[:,0]):,.0f} $ "
    f"(5°–95° {np.percentile(pl[:,0],5):,.0f}–{np.percentile(pl[:,0],95):,.0f}) · trade mediani {np.median(pl[:,1]):.0f} contro {ms['n']}")
nb = []
for lab, kw in (("K=2", dict(k=2)), ("K=4", dict(k=4)), ("tol 0,5%", dict(tol=0.005)), ("tol 2%", dict(tol=0.02))):
    Sn = E.signals(F, **kw)
    _, mn = run(Sn, STAR, "2021-01-01")
    nb.append(mn["fin"] > 10000 and mn["pf"] > 1)
    say(f"  vicino {lab:8s}: {fm(mn)}")
c5 = sum(nb) >= 3
say(f"Criterio 5 (vicini, ≥ 3 su 4 positivi): {c5} · {sum(nb)}/4")
valid = c1 and c2 and c3 and c4 and c5
say("VERDETTO S*:", "VALIDA" if valid else "NON VALIDA", "· criteri 1–5:", [c1, c2, c3, c4, c5])


def port(sw, w=0.3):
    e = (1 - w) * w31 + w * 10000 * sw.reindex(w31.index).ffill()
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    cagr = (e.iloc[-1] / 10000) ** (1 / yrs) - 1
    dd = (e / e.cummax() - 1).min()
    return e, cagr, dd


e73, cg, dd = port(eq)
yrs = (w31.index[-1] - w31.index[0]).days / 365.25
wc, wd = (w31.iloc[-1] / 10000) ** (1 / yrs) - 1, (w31 / w31.cummax() - 1).min()
say(f"\nPortafoglio 70/30 (7.000 $ W3.1 + 3.000 $ S*): {e73.iloc[-1]:,.0f} $ · CAGR {100*cg:.1f}% · DD {100*dd:.1f}% · C/DD {cg/abs(dd):.3f}")
say(f"W3.1 da sola: {w31.iloc[-1]:,.0f} $ · CAGR {100*wc:.1f}% · DD {100*wd:.1f}% · C/DD {wc/abs(wd):.3f}")
say(f"70% W3.1 + 30% liquidità: {0.7*w31.iloc[-1]+3000:,.0f} $")
say("Correlazione dei rendimenti settimanali S* / W3.1:",
    round(float(eq.resample("W").last().pct_change().corr(w31.resample("W").last().pct_change())), 2))
say("MIGLIORA IL PORTAFOGLIO:", bool(valid and cg / abs(dd) > wc / abs(wd)), "(richiede anche il verdetto VALIDA)")
pd.DataFrame({"w31": w31, "swing": 10000 * eq.reindex(w31.index).ffill(), "p7030": e73}).round(1).to_csv(HERE / "equity.csv")

# ------------------------------------------------------------------ 3. descrittivo
say("\n== DESCRITTIVO (non cambia il verdetto) ==")
say(f"Configurazioni con finale > 10.000 $ nel 2021+: {(G.fin > 10000).sum()}/{len(G)} · con finale > buy & hold: "
    f"{(G.fin > 10000*bh.iloc[-1]/F.loc['2021-01-01','open']).sum()} · con finale > W3.1: {(G.fin > 27190).sum()} · mediana {G.fin.median():,.0f} $")
q = G[(G.pre_n >= 40) & (G.n >= 20)]
say(f"Spearman CAGR/DD 2014–20 contro 2021+ ({len(q)} configurazioni con ≥ 40 e ≥ 20 trade): {q.pre_cdd.rank().corr(q.cdd.rank()):.2f}")
say(f"Ammissibili nel 2014–20: {G.ammissibile.sum()} · di queste positive nel 2021+: {(G[G.ammissibile].fin > 10000).sum()} "
    f"· mediana 2021+ {G[G.ammissibile].fin.median():,.0f} $")
for dim in ("entry", "regime", "side", "stop", "tp"):
    a = G.groupby(dim).agg(fin=("fin", "median"), dd=("dd", "median"), pf=("pf", "median"), pos=("fin", lambda v: (v > 10000).mean()),
                           pre=("pre_cdd", "median"), n=("n", "median"))
    say(f"Mediane per {dim}: " + " · ".join(f"{k}: {v.fin:,.0f} $ DD {100*v.dd:.0f}% PF {v.pf:.2f} positive {100*v.pos:.0f}% "
                                              f"(trade {v.n:.0f}; 2014–20 C/DD {v.pre:.2f})" for k, v in a.iterrows()))
say("Stop × uscita, finale mediano 2021+ (solo R1 e R2, tutti i tipi e lati):")
pv = G[G.regime != "R0"].pivot_table(index="stop", columns="tp", values="fin", aggfunc="median").round(0)
say(pv.to_string())
best = G[G.n >= 20].sort_values("cdd", ascending=False)
say("Prime 10 del 2021+ per CAGR/DD (≥ 20 trade) — SCELTA A POSTERIORI, NON UTILIZZABILE:")
for _, x in best.head(10).iterrows():
    say(f"  {x.cfg:18s} {x.fin:>7,.0f} $ · DD {100*x.dd:6.1f}% · C/DD {x.cdd:5.2f} · trade {x.n:3d} · PF {x.pf:.2f} · IS {x.is_fin:,.0f} / OOS "
        f"{x.oos_fin:,.0f} || 2014–20: {x.pre_fin:,.0f} $ · DD {100*x.pre_dd:.0f}% · PF {x.pre_pf_1417:.2f}/{x.pre_pf_1820:.2f} · amm. {x.ammissibile}")
bc = tuple(best.iloc[0].cfg.split("/"))
rb, mb = run(ST, bc, "2021-01-01")
plb = placebo(ST, bc, "2021-01-01", rb["trades"])
pb = (1 + (plb[:, 0] >= mb["fin"]).sum()) / (1 + len(plb))
say(f"Placebo della migliore a posteriori {'/'.join(bc)}: p = {pb:.3f} (soglia di Bonferroni {0.05/len(G):.5f}) · placebo mediana "
    f"{np.median(plb[:,0]):,.0f} $")
eb, cb, db = port(rb["equity"])
say(f"70/30 con la migliore a posteriori: {eb.iloc[-1]:,.0f} $ · DD {100*db:.1f}% · C/DD {cb/abs(db):.3f}")
pd.DataFrame({"scelta": pl[:, 0], "posteriori": plb[:, 0]}).round(0).to_csv(HERE / "placebo.csv", index=False)
(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
