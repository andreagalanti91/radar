"""Esegue PREREG.md (commit 69dc968). Output: risultati.txt, varianti.csv, mfe.csv, trade_varianti.csv. Uso: python3 tp_run.py"""
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
sys.path.insert(0, str(HERE.parents[1] / "research" / "p2_nuovi"))
import tp_engine as E  # noqa: E402
from p2_data import load  # noqa: E402
from radar import weekly as W  # noqa: E402

SEED, N_PLA = 20261122, 500
d = load()
F, FL = d["f"], d["fl"]
PER = {"ALL": (F, "2021-01-01", None), "IS": (F, "2021-01-01", "2023-12-31"),
       "OOS": (F, "2024-01-01", None), "L": (FL, "2018-01-01", "2020-12-31")}
VAR = {"V1 TP10 tutto A": dict(tp=(0.10, 1.0)), "V2 TP12,5 tutto A": dict(tp=(0.125, 1.0)),
       "V3 TP15 tutto A": dict(tp=(0.15, 1.0)), "V4 TP10 metà": dict(tp=(0.10, 0.5)),
       "V5 TP12,5 metà": dict(tp=(0.125, 0.5)), "V6 TP15 metà": dict(tp=(0.15, 0.5)),
       "V7 TP12,5 tutto B5%": dict(tp=(0.125, 1.0), reentry=("B", 0.05)), "V8 trail 1,5 dopo +10%": dict(trail2=(0.10, 1.5))}
NEIGH = {"V7 TP12,5 tutto B5%": {"B2,5%": dict(tp=(0.125, 1.0), reentry=("B", 0.025)),
                                 "B7,5%": dict(tp=(0.125, 1.0), reentry=("B", 0.075))},
         "V8 trail 1,5 dopo +10%": {"k1,25": dict(trail2=(0.10, 1.25)), "k1,75": dict(trail2=(0.10, 1.75)),
                                    "att 7,5%": dict(trail2=(0.075, 1.5)), "att 12,5%": dict(trail2=(0.125, 1.5))}}
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def run(cfg, per):
    x, s, e = PER[per]
    return E.simulate(x, cfg, start=s, end=e)


def tl(r):
    return list(r["trades"]) + ([dict(r["open"], pnl=r["open"]["pnl_close"], exit=None)] if r["open"] else [])


def met(r):
    e = r["equity"] / r["equity"].iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1)
    pn = np.array([t["pnl"] for t in tl(r)])
    return dict(final=round(10000 * float(e.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1),
                cdd=round(cagr / abs(dd), 3), n=len(pn), wr=round(100 * float((pn > 0).mean()), 1),
                worst=round(100 * float(pn.min()), 1), wo_best=round(10000 * float(e.iloc[-1]) / (1 + pn.max())),
                n_tp=r["n_tp"])


def bh(per):
    x, s, e = PER[per]
    x = x[(x.index >= s) & ((x.index <= e) if e else True)]
    eq = x["close"] / (x["open"].iloc[0] * (1 + W.SLIP) * (1 + W.FEE_SPOT))
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    dd = float((eq / eq.cummax() - 1).min())
    cagr = float(eq.iloc[-1] ** (1 / yrs) - 1)
    return dict(final=round(10000 * float(eq.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1),
                cdd=round(cagr / abs(dd), 3))


def groups(rv, rb):
    """Δ log per trade W3.2: i trade della variante con segnale dentro la finestra [segnale, uscita] di un trade W3.2 si
    sommano a quel trade; quelli fuori finestra formano un gruppo a sé."""
    bt, vt = tl(rb), tl(rv)
    out = {}
    used = set()
    for b in bt:
        lo, hi = b["signal"], b["exit"] or "9999"
        lv = 0.0
        for j, v in enumerate(vt):
            if lo <= v["signal"] <= hi:
                lv += np.log1p(v["pnl"])
                used.add(j)
        out[b["signal"]] = lv - np.log1p(b["pnl"])
    for j, v in enumerate(vt):
        if j not in used:
            out["nuovo " + v["signal"]] = np.log1p(v["pnl"])
    return out


def signflip(x):
    x = np.array([v for v in x if abs(v) > 1e-12])
    m = len(x)
    if m == 0:
        return 1.0, 0
    obs = x.sum()
    if m <= 20:
        s = np.array(list(itertools.product([1, -1], repeat=m))) @ np.abs(x)
    else:
        rng = np.random.default_rng(SEED)
        s = (rng.choice([1, -1], size=(20000, m)) * np.abs(x)).sum(axis=1)
    return float((s >= obs - 1e-12).mean()), m


def mfe_table(r, lbl):
    rows = []
    for t in tl(r):
        sd = 1 if t["side"] == "long" else -1
        mfe = (t["ext"] / t["entry_px"] - 1) * sd
        mfec = (t["best"] / t["entry_px"] - 1) * sd
        mv = t["move"]
        rows.append(dict(periodo=lbl, segnale=t["signal"], lato=t["side"], ingresso=t["entry_px"], uscita=t.get("exit"),
                         motivo=t.get("reason", "aperto"), expo=t["expo"], mfe_pct=round(100 * mfe, 1),
                         mfe_chiusura_pct=round(100 * mfec, 1), uscita_pct=round(100 * mv, 1),
                         restituito_pct=round(100 * (mfe - mv), 1),
                         quota_restituita=round((mfe - mv) / mfe, 2) if mfe > 0 else np.nan,
                         pnl_pct=round(100 * t["pnl"], 1), tocca10=mfe >= 0.10, tocca125=mfe >= 0.125, tocca15=mfe >= 0.15))
    return rows


# ---------- 1. MFE di W3.2 ----------
base = {p: run({}, p) for p in PER}
mf = pd.DataFrame(mfe_table(base["ALL"], "2021+") + mfe_table(base["L"], "2018-20"))
mf.to_csv(HERE / "mfe.csv", index=False)
say("== MFE dei trade W3.2 ==")
say(mf.drop(columns=["tocca10", "tocca125", "tocca15"]).to_string(index=False))
for lbl, g in mf.groupby("periodo", sort=False):
    say(f"{lbl}: trade {len(g)} | toccano +10% {int(g.tocca10.sum())}, +12,5% {int(g.tocca125.sum())}, +15% {int(g.tocca15.sum())}"
        f" | MFE mediano {g.mfe_pct.median():.1f}% | uscita mediana {g.uscita_pct.median():.1f}%"
        f" | restituito mediano {g.restituito_pct.median():.1f} punti | quota restituita mediana {g.quota_restituita.median():.2f}"
        f" (vincenti {g[g.pnl_pct > 0].quota_restituita.median():.2f}) | MFE/uscita somma {g.mfe_pct.sum():.0f}/{g.uscita_pct.sum():.0f}")
    g10 = g[g.tocca10]
    say(f"   tra i trade che toccano +10%: uscita mediana {g10.uscita_pct.median():.1f}%, sotto +10% all'uscita "
        f"{int((g10.uscita_pct < 10).sum())}/{len(g10)}, in perdita {int((g10.uscita_pct < 0).sum())}")

# ---------- 2. Varianti ----------
say("\n== Risultati (10.000 $) ==")
rows, res = [], {}
bm = {p: met(base[p]) for p in PER}
for nm, cfg in [("W3.2", {})] + list(VAR.items()):
    rr = base if nm == "W3.2" else {p: run(cfg, p) for p in PER}
    res[nm] = rr
    m = {p: (bm[p] if nm == "W3.2" else met(rr[p])) for p in PER}
    rows.append(dict(variante=nm, **{f"{p}_{k}": v for p in PER for k, v in m[p].items()}))
    a = m["ALL"]
    say(f"{nm:24s} fin {a['final']:>7} CAGR {a['cagr']:5.1f} DD {a['dd']:6.1f} C/DD {a['cdd']:.3f} n {a['n']:2d} WR {a['wr']:5.1f}"
        f" peg {a['worst']:5.1f} TP {a['n_tp']:2d} sMigl {a['wo_best']:>6} | IS {m['IS']['final']}/{m['IS']['cdd']:.3f}"
        f" OOS {m['OOS']['final']}/{m['OOS']['cdd']:.3f} | 18-20 {m['L']['final']}/{m['L']['dd']}/{m['L']['cdd']:.3f}"
        f" n{m['L']['n']} WR{m['L']['wr']}")
for p in PER:
    say(f"Buy & hold {p}: {bh(p)}")
pd.DataFrame(rows).to_csv(HERE / "varianti.csv", index=False)

# ---------- 3. Criteri ----------
say("\n== Criteri ==")
pv, crit = {}, {}
trows = []
for nm, cfg in VAR.items():
    rr = res[nm]
    m = {p: met(rr[p]) for p in PER}
    g = groups(rr["ALL"], base["ALL"])
    for k, v in g.items():
        trows.append(dict(variante=nm, trade=k, delta_log_pct=round(100 * v, 2)))
    dl = np.array(list(g.values()))
    p, nz = signflip(dl)
    pv[nm] = p
    c1 = m["IS"]["cdd"] > bm["IS"]["cdd"] and m["OOS"]["cdd"] > bm["OOS"]["cdd"]
    c2 = m["L"]["cdd"] >= bm["L"]["cdd"]
    c3 = m["ALL"]["dd"] >= -30
    c4 = float(np.sort(dl)[:-2].sum()) > 0
    crit[nm] = [c1, c2, c3, c4]
    say(f"{nm}: c1 IS/OOS {c1} | c2 2018-20 {c2} | c3 DD {c3} | c4 senza 2 Δ migliori {c4} (somma Δ {100*dl.sum():.1f}, "
        f"senza 2 {100*np.sort(dl)[:-2].sum():.1f} punti) | signflip p {p:.3f} (Δ non nulli {nz})")
pd.DataFrame(trows).to_csv(HERE / "trade_varianti.csv", index=False)
order = sorted(pv, key=pv.get)
holm = {}
for i, nm in enumerate(order):
    holm[nm] = pv[nm] <= 0.05 / (len(order) - i) and all(holm.get(o, True) for o in order[:i])
say("Holm:", {k: (round(pv[k], 3), holm[k]) for k in order})

say("\n== Placebo (livello TP / attivazione a caso per trade, U[5%,30%]) ==")
pla = []
for nm, cfg in VAR.items():
    obs = met(res[nm]["ALL"])["cdd"]
    rng = np.random.default_rng(SEED)
    vals = []
    for _ in range(N_PLA):
        if "trail2" in cfg:
            c2 = dict(trail2=(float(rng.uniform(0.05, 0.30)), cfg["trail2"][1]))
        else:
            c2 = dict(cfg, tp_rng=rng)
        vals.append(met(run(c2, "ALL"))["cdd"])
    vals = np.array(vals)
    pp = float((vals >= obs).mean())
    pla.append(dict(variante=nm, osservato=obs, mediana=round(float(np.median(vals)), 3), p=pp))
    crit[nm] += [holm[nm], pp < 0.05]
    say(f"{nm}: C/DD {obs:.3f} placebo mediana {np.median(vals):.3f} (5-95% {np.percentile(vals,5):.3f}-{np.percentile(vals,95):.3f}) p {pp:.3f}")
pd.DataFrame(pla).to_csv(HERE / "placebo.csv", index=False)

say("\n== Vicini (2021+, IS, OOS, 2018-20 C/DD) ==")
for nm, nb in NEIGH.items():
    for lab, cfg in nb.items():
        m = {p: met(run(cfg, p)) for p in PER}
        say(f"{nm} · {lab}: fin {m['ALL']['final']} DD {m['ALL']['dd']} C/DD {m['ALL']['cdd']} WR {m['ALL']['wr']} | "
            f"IS {m['IS']['cdd']} OOS {m['OOS']['cdd']} 18-20 {m['L']['cdd']}")
say(f"W3.2 C/DD: ALL {bm['ALL']['cdd']} IS {bm['IS']['cdd']} OOS {bm['OOS']['cdd']} 18-20 {bm['L']['cdd']}")

say("\n== Verdetto per variante (c1..c4, Holm, placebo) ==")
for nm, c in crit.items():
    say(f"{nm}: {'PASSA' if all(c) else 'NON PASSA'} {c}")

say("\n== Trade delle varianti TP tutto (2021+) ==")
for nm in ["V2 TP12,5 tutto A", "V7 TP12,5 tutto B5%"]:
    for t in tl(res[nm]["ALL"]):
        say(f"{nm[:3]} {t['signal']} {t['side']:5s} {t['entry']}→{t.get('exit')} {t.get('reason','aperto'):6s} {t.get('kind')} "
            f"move {100*t['move']:.1f} pnl {100*t['pnl']:.1f}")
(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
