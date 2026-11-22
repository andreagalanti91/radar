"""Aggiunte NON preregistrate (solo lettura di griglia.csv, scelte.csv, trade_scelte.csv; nessuna nuova scelta):
ricalcolo a mano di 3 trade, correlazione di rango dentro i soli long, mediane per dimensione dei soli long.
Uso: python3 swm_extra.py → extra.txt"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import swm_engine as M  # noqa: E402

out = []
T, G, S = (pd.read_csv(M.HERE / n) for n in ("trade_scelte.csv", "griglia.csv", "scelte.csv"))
fee, _, slip = M.COSTS["std"]
for a, k in (("SPY", 0), ("SPY", 1), ("TSLA", None)):
    t = T[(T.asset == a) & (T.famiglia == "S*")]
    t = t[t.lato == "short"].iloc[0] if k is None else t.iloc[k]
    f = M.load(a)
    i, j = f.index.get_loc(pd.Timestamp(t.ingresso)), f.index.get_loc(pd.Timestamp(t.uscita))
    c, s = f.close.iloc[i - 1], 1 if t.lato == "long" else -1
    e, stop, tp = f.open.iloc[i] * (1 + slip * s), c * (1 - s * t.stop_pct / 100), c * (1 + s * 0.10)
    o = f.open.iloc[j]
    x = (min(o, stop) if s > 0 else max(o, stop)) * (1 - slip * s) if t.motivo == "stop" else (max(o, tp) if s > 0 else min(o, tp))
    q = 1 / (e * (1 + fee))
    pnl = -q * e * fee + s * q * (x - e) - q * x * fee
    out.append(f"Trade a mano {a} {t.cfg} {t.ingresso} {t.lato} {t.motivo} {t.uscita}: motore {t.pnl_pct:.2f}% · a mano {100*pnl:.2f}%")
    assert abs(100 * pnl - t.pnl_pct) < 0.011
for lab, m in (("tutte", G.side.notna()), ("solo long", G.side == "L")):
    r = []
    for a, g in G[m].groupby("asset"):
        q = g[(g.pre_n >= 30) & (g.n >= 20)]
        r.append(q.pre_cdd.rank().corr(q.cdd.rank()))
    out.append(f"Rango scelta→giudizio ({lab}): mediana fra asset {np.median(r):.2f} · minimo {min(r):.2f} · massimo {max(r):.2f} · positivi {sum(x > 0 for x in r)}/15")
L = G[G.side == "L"].copy()
bh = S[S.famiglia == "S*"].set_index("asset")
out.append(f"Solo long (90 configurazioni × 15 asset): DD entro −20% {100*(L.dd >= -0.2).mean():.0f}% · C/DD > B&H "
           f"{100*(L.cdd > L.asset.map(bh.bh_cdd)).mean():.0f}% · finale > B&H {100*(L.fin > L.asset.map(bh.bh_fin)).mean():.1f}%")
for dim in ("stop", "tp", "entry", "regime"):
    a = L.groupby(dim).agg(fin=("fin", "median"), dd=("dd", "median"), wr=("wr", "median"), pf=("pf", "median"))
    out.append(f"Solo long, mediane per {dim}: " + " · ".join(f"{k}: {v.fin:,.0f} $ DD {100*v.dd:.0f}% WR {100*v.wr:.0f}% PF {v.pf:.2f}" for k, v in a.iterrows()))
for fam in ("S*", "G*"):
    q = S[S.famiglia == fam]
    out.append(f"{fam}: mediane · in posizione {100*q.inpos.median():.0f}% · durata {q.days.median():.0f} barre · dal 2021 {q.fin21.median():,.0f} $ contro B&H "
               f"{q.bh21.median():,.0f} $ · dal 2021 > B&H su {(q.fin21 > q.bh21).sum()}/15 · costi zero {q.fin_zero.median():,.0f} $ · costi doppi {q.fin_x2.median():,.0f} $ "
               f"· placebo: reale > mediana del placebo su {(q.fin > q.pl_med).sum()}/15 · p mediano {q.p.median():.2f}")
print("\n".join(out))
(M.HERE / "extra.txt").write_text("\n".join(out) + "\n")
