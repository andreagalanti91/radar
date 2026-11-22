"""Scelta, giudizio (una sola volta), placebo, vicini, buy & hold, descrittivo (PREREG.md, commit beb05af).
Uso: python3 swm_run.py            → risultati.txt, griglia.csv, scelte.csv, placebo.csv, trade_scelte.csv, dimensioni.csv
     python3 swm_run.py --dry DIR  → prova a secco su 3 serie casuali (nessun dato reale), output in DIR"""
from __future__ import annotations

import itertools
import sys
import warnings
import zlib
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import swm_engine as M  # noqa: E402

DRY = "--dry" in sys.argv
OUTDIR = Path(sys.argv[sys.argv.index("--dry") + 1]) if DRY else M.HERE
NPL = 20 if DRY else 1000
NASSET = 3 if DRY else len(M.ASSETS)
CFGS = list(itertools.product(M.ENTRIES, M.REGIMES, M.SIDES, M.STOPS, M.TPS))
MIN_CH, MIN_J, DDMAX, PFMIN, ALPHA = 30, 20, -0.20, 1.2, 0.05
NEIGH = (("K=2", dict(k=2)), ("K=4", dict(k=4)), ("vita 52", dict(life=52)), ("vita 156", dict(life=156)))
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def load(name):
    if not DRY:
        return M.load(name)
    rng = np.random.default_rng(zlib.crc32(name.encode()))
    idx = pd.bdate_range("2004-01-01", M.END)
    c = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.015, len(idx))))
    o = np.r_[c[0], c[:-1]] * np.exp(rng.normal(0, 0.004, len(idx)))
    h = np.maximum(o, c) * np.exp(np.abs(rng.normal(0, 0.006, len(idx))))
    lo = np.minimum(o, c) * np.exp(-np.abs(rng.normal(0, 0.006, len(idx))))
    return pd.DataFrame(dict(open=o, high=h, low=lo, close=c, funding=0.0, pf14z=np.nan), index=idx)


def run(S, cfg, a, b=None, **kw):
    r = M.simulate(S, cfg, a, b, **kw)
    return r, M.metrics(r)


def bh(f, a, b=None):
    """Buy & hold: acquisto all'apertura del primo giorno (slippage + commissione), valutato alla chiusura."""
    fee, _, slip = M.COSTS["std"]
    x = f.loc[a:b] if b is not None else f.loc[a:]
    e = x["close"] / (x["open"].iloc[0] * (1 + slip) * (1 + fee))
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1]) ** (1 / yrs) - 1
    return dict(fin=round(10000 * float(e.iloc[-1])), cagr=cagr, dd=dd, cdd=cagr / abs(dd))


def grid(name):
    f = load(name)
    P = M.periods(f)
    S = M.signals(f)
    rows = []
    for cfg in CFGS:
        _, c = run(S, cfg, P["c0"], P["c1"])
        _, c1 = run(S, cfg, P["c0"], P["cm"] - pd.Timedelta(days=1))
        _, c2 = run(S, cfg, P["cm"], P["c1"])
        _, j = run(S, cfg, P["j0"])
        _, j1 = run(S, cfg, P["j0"], P["jm"] - pd.Timedelta(days=1))
        _, j2 = run(S, cfg, P["jm"])
        rows.append(dict(asset=name, cfg="/".join(cfg), entry=cfg[0], regime=cfg[1], side=cfg[2], stop=cfg[3], tp=cfg[4],
                         pre_fin=c["fin"], pre_cagr=c["cagr"], pre_dd=c["dd"], pre_cdd=c["cdd"], pre_n=c["n"], pre_pf=c["pf"],
                         pre_pf_a=c1["pf"], pre_pf_b=c2["pf"],
                         fin=j["fin"], cagr=j["cagr"], dd=j["dd"], cdd=j["cdd"], n=j["n"], wr=j["wr"], pf=j["pf"], worst=j["worst"],
                         days=j["days"], inpos=j["inpos"], h1_fin=j1["fin"], h1_pf=j1["pf"], h2_fin=j2["fin"], h2_pf=j2["pf"]))
    return pd.DataFrame(rows)


def placebo(S, cfg, a, real, rng, nrun):
    """Come research/swing_sr/sw_run.placebo: ingressi a caso nei giorni in cui il regime ammette il lato; stesso numero per
    lato; distanze di stop ricampionate dai trade veri; stessa uscita."""
    idx = S["idx"]
    t0 = idx.searchsorted(pd.Timestamp(a))
    dist = {s: np.array([x["d"] for x in real if x["side"] == s]) for s in (1, -1)}
    need = {s: len(dist[s]) for s in (1, -1)}
    days = {s: np.arange(t0, len(idx) - 2)[S["reg"][(cfg[1], s)][t0:len(idx) - 2]] for s in (1, -1)}
    out = []
    for _ in range(nrun):
        forced = {}
        for _it in range(8):
            got = {1: 0, -1: 0}
            if forced:
                for x in M.simulate(S, cfg, a, forced=forced)["trades"]:
                    got[x["side"]] += 1
            miss = {s: need[s] - got[s] for s in (1, -1)}
            if all(v <= 0 for v in miss.values()):
                break
            for s in (1, -1):
                if miss[s] > 0 and len(days[s]):
                    for d in rng.choice(days[s], size=min(miss[s], len(days[s])), replace=False):
                        forced.setdefault(int(d), (s, float(rng.choice(dist[s]))))
        rr = M.simulate(S, cfg, a, forced=forced)
        out.append((rr["equity"].iloc[-1] * 10000, len(rr["trades"])))
    return np.array(out)


def judge(arg):
    name, cfgs, fam = arg
    cfg = tuple(cfgs.split("/"))
    f = load(name)
    P = M.periods(f)
    S = M.signals(f)
    r, m = run(S, cfg, P["j0"])
    _, m1 = run(S, cfg, P["j0"], P["jm"] - pd.Timedelta(days=1))
    _, m2 = run(S, cfg, P["jm"])
    pn = np.sort(np.array([t["pnl"] for t in r["trades"]]))
    no2 = 10000 * float(np.prod(1 + pn[:-2])) if len(pn) > 2 else 10000.0
    rng = np.random.default_rng(zlib.crc32(f"{name}|{cfgs}|{fam}".encode()))
    pl = placebo(S, cfg, P["j0"], r["trades"], rng, NPL) if len(pn) else np.zeros((0, 2))
    p = (1 + int((pl[:, 0] >= m["fin"]).sum())) / (1 + len(pl)) if len(pl) else 1.0
    nb = {}
    for lab, kw in NEIGH:
        _, mn = run(M.signals(f, **kw), cfg, P["j0"])
        nb[lab] = (mn["fin"], mn["pf"], mn["n"])
    b = bh(f, P["j0"])
    start21 = max(pd.Timestamp("2021-01-01"), P["j0"])
    _, m21 = run(S, cfg, start21)
    b21 = bh(f, start21)
    _, mz = run(S, cfg, P["j0"], cost="zero")
    _, mx = run(S, cfg, P["j0"], cost="x2")
    tr = pd.DataFrame([dict(famiglia=fam, asset=name, cfg=cfgs, ingresso=x["entry"].date(), lato="long" if x["side"] > 0 else "short",
                            prezzo=round(x["entry_px"], 4), stop_pct=round(100 * x["d"], 1), uscita=x["exit"].date(),
                            motivo=x["reason"], giorni=x["days"], pnl_pct=round(100 * x["pnl"], 2)) for x in r["trades"]])
    row = dict(famiglia=fam, asset=name, cfg=cfgs, j0=P["j0"].date(), fin=m["fin"], cagr=m["cagr"], dd=m["dd"], cdd=m["cdd"], n=m["n"],
               wr=m["wr"], pf=m["pf"], worst=m["worst"], days=m["days"], inpos=m["inpos"],
               h1_fin=m1["fin"], h1_pf=m1["pf"], h2_fin=m2["fin"], h2_pf=m2["pf"], no2=round(no2), p=p,
               pl_med=float(np.median(pl[:, 0])) if len(pl) else np.nan, pl_n=float(np.median(pl[:, 1])) if len(pl) else np.nan,
               nb_ok=sum(v[0] > 10000 and v[1] > 1 for v in nb.values()),
               nb=" · ".join(f"{k}: {v[0]:,} $ PF {v[1]:.2f}" for k, v in nb.items()),
               bh_fin=b["fin"], bh_cagr=b["cagr"], bh_dd=b["dd"], bh_cdd=b["cdd"],
               fin21=m21["fin"], dd21=m21["dd"], n21=m21["n"], bh21=b21["fin"], bh21_dd=b21["dd"],
               fin_zero=mz["fin"], fin_x2=mx["fin"],
               stop_n=int((tr.motivo == "stop").sum()) if len(tr) else 0,
               stop_avg=float(tr[tr.motivo == "stop"].pnl_pct.mean()) if len(tr) else np.nan,
               tp_n=int((tr.motivo == "tp").sum()) if len(tr) else 0)
    return row, tr, pd.DataFrame({"famiglia": fam, "asset": name, "placebo": pl[:, 0].round(0)})


def holm(p: pd.Series, alpha=ALPHA) -> pd.Series:
    order = p.sort_values().index
    ok, alive = pd.Series(False, index=p.index), True
    for i, k in enumerate(order):
        alive = alive and p[k] <= alpha / (len(p) - i)
        ok[k] = alive
    return ok


def choose(g: pd.DataFrame) -> tuple[str, bool]:
    adm = g[g.ammissibile]
    pool = adm if len(adm) else g[g.pre_n >= MIN_CH]
    pool = pool[pool.pre_cdd.notna()].sort_values("pre_cdd", ascending=False)
    return pool.iloc[0].cfg, bool(len(adm))


if __name__ == "__main__":
    names = list(M.ASSETS)[:NASSET]
    with Pool(4) as pool:
        G = pd.concat(pool.map(grid, names), ignore_index=True)
    G["ammissibile"] = (G.pre_n >= MIN_CH) & (G.pre_pf_a >= PFMIN) & (G.pre_pf_b >= PFMIN) & (G.pre_dd >= DDMAX)
    G.to_csv(OUTDIR / "griglia.csv", index=False)

    say(f"== SCELTA (solo periodo di scelta di ogni asset) · {len(CFGS)} configurazioni × {len(names)} asset ==")
    star = {}
    for a in names:
        g = G[G.asset == a]
        star[a], ok = choose(g)
        x = g[g.cfg == star[a]].iloc[0]
        say(f"  {a:6s} ≥ {MIN_CH} trade: {(g.pre_n >= MIN_CH).sum():3d} · ammissibili: {g.ammissibile.sum():3d} · S* = {star[a]:16s}"
            f"{'' if ok else ' (NESSUNA ammissibile: migliore CAGR/DD con ≥ 30 trade)'} · scelta: {x.pre_fin:>9,.0f} $ · DD {100*x.pre_dd:6.1f}% · "
            f"C/DD {x.pre_cdd:5.2f} · trade {x.pre_n:3d} · PF {x.pre_pf_a:.2f}/{x.pre_pf_b:.2f}")
    piv_adm = G.pivot(index="cfg", columns="asset", values="ammissibile")
    piv_cdd = G.pivot(index="cfg", columns="asset", values="pre_cdd")
    piv_n = G.pivot(index="cfg", columns="asset", values="pre_n")
    rank = pd.DataFrame({"n_amm": piv_adm.sum(axis=1), "med_cdd": piv_cdd.median(axis=1), "n30": (piv_n >= MIN_CH).sum(axis=1)})
    if rank.n_amm.max() > 0:
        gstar = rank.sort_values(["n_amm", "med_cdd"], ascending=False).index[0]
    else:
        gstar = rank[rank.n30 >= (len(names) + 1) // 2].sort_values("med_cdd", ascending=False).index[0]
    say(f"G* (una per tutti) = {gstar} · ammissibile su {int(rank.loc[gstar, 'n_amm'])}/{len(names)} asset · CAGR/DD mediano di scelta "
        f"{rank.loc[gstar, 'med_cdd']:.2f}")
    say("  prime 5 per numero di asset ammissibili: " + " · ".join(
        f"{k} ({int(v.n_amm)}; {v.med_cdd:.2f})" for k, v in rank.sort_values(["n_amm", "med_cdd"], ascending=False).head(5).iterrows()))

    jobs = [(a, star[a], "S*") for a in names] + [(a, gstar, "G*") for a in names]
    with Pool(4) as pool:
        res = pool.map(judge, jobs, chunksize=1)
    R = pd.DataFrame([r[0] for r in res])
    pd.concat([r[1] for r in res], ignore_index=True).to_csv(OUTDIR / "trade_scelte.csv", index=False)
    pd.concat([r[2] for r in res], ignore_index=True).to_csv(OUTDIR / "placebo.csv", index=False)
    R["c0"] = R.n >= MIN_J
    R["c1"] = (R.fin > 10000) & (R.h1_fin > 10000) & (R.h2_fin > 10000) & (R.h1_pf >= PFMIN) & (R.h2_pf >= PFMIN)
    R["c2"] = R.dd >= DDMAX
    R["c3"] = False
    for fam in ("S*", "G*"):
        m = R.famiglia == fam
        R.loc[m, "c3"] = holm(R.loc[m, "p"])
    R["c4"] = R.no2 > 10000
    R["c5"] = R.nb_ok >= 3
    R["valida"] = R[["c0", "c1", "c2", "c3", "c4", "c5"]].all(axis=1)
    R["batte_bh"] = R.cdd > R.bh_cdd
    R["conveniente"] = R.valida & R.batte_bh
    R.to_csv(OUTDIR / "scelte.csv", index=False)

    need = (len(names) + 1) // 2
    for fam, lab in (("S*", "FAMIGLIA PRIMARIA · S*(asset), scelta asset per asset"), ("G*", f"FAMIGLIA SECONDARIA · G* = {gstar} per tutti")):
        q = R[R.famiglia == fam]
        say(f"\n== GIUDIZIO (una sola volta, 10.000 $) · {lab} ==")
        for _, x in q.iterrows():
            say(f"{x.asset:6s} {x.cfg:16s} dal {x.j0}: {x.fin:>7,} $ · CAGR {100*x.cagr:5.1f}% · DD {100*x.dd:6.1f}% · C/DD {x.cdd:5.2f} · trade {x.n:3d} · "
                f"WR {100*x.wr:4.1f}% · PF {x.pf:4.2f} · metà {x.h1_fin:,}/{x.h2_fin:,} $ (PF {x.h1_pf:.2f}/{x.h2_pf:.2f}) · senza i 2 migliori "
                f"{x.no2:,} $ · placebo p {x.p:.3f} (mediana {x.pl_med:,.0f} $, {x.pl_n:.0f} trade) · vicini {x.nb_ok}/4 || buy & hold "
                f"{x.bh_fin:,} $ · DD {100*x.bh_dd:.1f}% · C/DD {x.bh_cdd:.2f} || criteri 0–5 "
                f"{''.join('S' if x[c] else 'n' for c in ('c0', 'c1', 'c2', 'c3', 'c4', 'c5'))} → {'VALIDA' if x.valida else 'non valida'}"
                f"{' · batte il B&H in C/DD' if x.batte_bh else ''}")
            say(f"       vicini: {x.nb} · peggior trade {100*x.worst:.1f}% · durata mediana {x.days:.0f} barre · in posizione {100*x.inpos:.0f}% · "
                f"stop {x.stop_n} (media {x.stop_avg:.2f}%) · TP {x.tp_n} · costi zero {x.fin_zero:,} $ · costi doppi {x.fin_x2:,} $ · "
                f"dal 2021: {x.fin21:,} $ (DD {100*x.dd21:.1f}%, {x.n21} trade) contro B&H {x.bh21:,} $ (DD {100*x.bh21_dd:.1f}%)")
        say(f"Criteri superati (su {len(q)}): " + " · ".join(f"{c} {int(q[c].sum())}" for c in ("c0", "c1", "c2", "c3", "c4", "c5")) +
            f" · finale > 10.000 $: {(q.fin > 10000).sum()} · batte il B&H in C/DD: {q.batte_bh.sum()} · finale > B&H: {(q.fin > q.bh_fin).sum()}")
        say(f"p del placebo ≤ 0,05 senza correzione: {(q.p <= 0.05).sum()} · minimo {q.p.min():.3f} (soglia di Holm per il minimo {ALPHA/len(q):.4f})")
        say(f"Mediane: finale {q.fin.median():,.0f} $ · DD {100*q.dd.median():.1f}% · PF {q.pf.median():.2f} · WR {100*q.wr.median():.0f}% · "
            f"B&H {q.bh_fin.median():,.0f} $ (DD {100*q.bh_dd.median():.1f}%)")
        etf = q.asset.isin(["SPY", "QQQ", "GLD", "SLV", "USO"])
        say(f"VALIDE: {q.valida.sum()}/{len(q)} (ne servono {need}) · CONVENIENTI: {q.conveniente.sum()}/{len(q)} · per classe: ETF "
            f"{q[etf].valida.sum()}/{etf.sum()}, azioni {q[~etf].valida.sum()}/{(~etf).sum()}")
    v1 = int(R[R.famiglia == "S*"].valida.sum())
    v2 = int(R[R.famiglia == "G*"].valida.sum())
    c1 = int(R[R.famiglia == "S*"].conveniente.sum())
    verdict = ("FUNZIONA fuori da BTC" + (" e CONVIENE" if c1 >= need else " (ma non conviene rispetto al buy & hold)")) if v1 >= need else \
        ("INDICAZIONE da confermare su dati nuovi (solo G*)" if v2 >= need else "NON FUNZIONA")
    say(f"\nVERDETTO DI TRASFERIBILITÀ: {verdict} · S* valide {v1}/{len(names)} · G* valide {v2}/{len(names)}")

    say("\n== DESCRITTIVO (non cambia il verdetto) ==")
    B = R[R.famiglia == "S*"].set_index("asset")
    G["bh_cdd"], G["bh_fin"] = G.asset.map(B.bh_cdd), G.asset.map(B.bh_fin)
    for a in names:
        g = G[G.asset == a]
        q = g[(g.pre_n >= MIN_CH) & (g.n >= MIN_J)]
        rho = q.pre_cdd.rank().corr(q.cdd.rank()) if len(q) > 5 else np.nan
        best = g[g.n >= MIN_J].sort_values("cdd", ascending=False).iloc[0]
        say(f"  {a:6s} > 10.000 $: {(g.fin > 10000).sum():3d}/{len(g)} · C/DD > B&H: {(g.cdd > g.bh_cdd).sum():3d} · finale > B&H: "
            f"{(g.fin > g.bh_fin).sum():3d} · mediana {g.fin.median():>7,.0f} $ (DD {100*g.dd.median():.0f}%) · rango scelta→giudizio {rho:5.2f} "
            f"({len(q)}) · ammissibili {g.ammissibile.sum()} di cui positive {(g[g.ammissibile].fin > 10000).sum()} · migliore a posteriori "
            f"(NON utilizzabile) {best.cfg} {best.fin:,.0f} $ DD {100*best.dd:.0f}% C/DD {best.cdd:.2f}")
    say(f"Totale asset × configurazione: > 10.000 $ {100*(G.fin > 10000).mean():.0f}% · C/DD > B&H {100*(G.cdd > G.bh_cdd).mean():.1f}% · finale > B&H "
        f"{100*(G.fin > G.bh_fin).mean():.1f}% · DD entro −20% {100*(G.dd >= DDMAX).mean():.0f}% · mediana {G.fin.median():,.0f} $")
    dims = []
    for dim in ("entry", "regime", "side", "stop", "tp"):
        per_asset = G.groupby(["asset", dim]).fin.median().unstack()
        wins = per_asset.idxmax(axis=1).value_counts()
        a = G.groupby(dim).agg(fin=("fin", "median"), dd=("dd", "median"), pf=("pf", "median"), wr=("wr", "median"), n=("n", "median"),
                               pos=("fin", lambda v: (v > 10000).mean()), days=("days", "median"))
        say(f"Mediane per {dim}: " + " · ".join(
            f"{k}: {v.fin:,.0f} $ DD {100*v.dd:.0f}% PF {v.pf:.2f} WR {100*v.wr:.0f}% positive {100*v.pos:.0f}% (trade {v.n:.0f}, durata {v.days:.0f}; "
            f"migliore su {int(wins.get(k, 0))} asset)" for k, v in a.iterrows()))
        for k, v in a.iterrows():
            dims.append(dict(dimensione=dim, valore=k, finale_mediano=v.fin, dd_mediano=v.dd, pf_mediano=v.pf, wr_mediano=v.wr,
                             trade_mediani=v.n, quota_positive=v.pos, asset_migliore=int(wins.get(k, 0))))
    pd.DataFrame(dims).to_csv(OUTDIR / "dimensioni.csv", index=False)
    say("Stop × uscita, finale mediano di giudizio (tutti gli asset, ingressi, regimi e lati):")
    say(G.pivot_table(index="stop", columns="tp", values="fin", aggfunc="median").round(0).to_string())
    say("Regime × lato, finale mediano di giudizio:")
    say(G.pivot_table(index="regime", columns="side", values="fin", aggfunc="median").round(0).to_string())
    say("Solo long in R1 (il caso più favorevole a priori), stop × uscita, finale mediano e quota con C/DD > B&H:")
    q = G[(G.regime == "R1") & (G.side == "L")]
    say(q.pivot_table(index="stop", columns="tp", values="fin", aggfunc="median").round(0).to_string())
    say(f"  C/DD > B&H: {100*(q.cdd > q.bh_cdd).mean():.1f}% · finale > B&H: {100*(q.fin > q.bh_fin).mean():.1f}% · DD mediano {100*q.dd.median():.0f}%")
    (OUTDIR / "risultati.txt").write_text("\n".join(OUT) + "\n")
