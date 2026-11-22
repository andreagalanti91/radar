"""Fase 2 · esegue PREREG.md (commit 08da8cc) alla lettera. Output: risultati.txt, varianti.csv, trade_delta.csv, giorni_g7.csv.
Uso: python3 iu_run.py (~2–4 minuti)."""
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
import iu_engine as E  # noqa: E402
from p2_data import load  # noqa: E402
from radar import weekly as W  # noqa: E402

SEED, N_PLA = 20261122, 2000
d = load()
F, FL = d["f"], d["fl"]
PER = {"ALL": (F, "2021-01-01", None), "IS": (F, "2021-01-01", "2023-12-31"),
       "OOS": (F, "2024-01-01", None), "L": (FL, "2018-01-01", "2020-12-31")}
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def run(cfg, per):
    x, s, e = PER[per]
    if cfg.get("g7"):
        return E.simulate_g7(x, {k: v for k, v in cfg.items() if k != "g7"}, start=s, end=e)
    return E.simulate(x, cfg, start=s, end=e)


def tl(r):
    out = list(r["trades"])
    if r.get("open"):
        out.append(dict(r["open"], pnl=r["open"]["pnl_close"]))
    for o in r.get("open_list", []):
        out.append(dict(o, pnl=o["pnl_close"]))
    return out


def met(r, per):
    e = r["equity"] / r["equity"].iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1)
    ts = tl(r)
    pn = np.array([t["pnl"] for t in ts])
    m = dict(final=round(10000 * float(e.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1),
             cdd=round(cagr / abs(dd), 3), n=len(pn), wr=round(100 * float((pn > 0).mean()), 1),
             worst=round(100 * float(pn.min()), 1))
    if "runs" in r:   # G7: senza il trade migliore di ciascun sotto-portafoglio (deviazione dichiarata)
        wb = sum(float(rr["equity"].iloc[-1]) / (1 + max([t["pnl"] for t in tl(rr)] or [0]))
                 for rr in r["runs"].values())
        m["wo_best"] = round(wb)
        m["risk_max"] = round(100 * max(t.get("risk_plan", 0) for t in ts) / 7, 1)
    else:
        m["wo_best"] = round(10000 * float(np.prod(1 + np.sort(pn)[:-1])))
        m["risk_max"] = round(100 * max(t.get("risk_plan", 0) for t in ts), 1)
    m["expo"] = round(float(r["expo"].mean()), 3) if "expo" in r else np.nan
    return m


def bh(per):
    x, s, e = PER[per]
    x = x[(x.index >= s) & ((x.index <= e) if e else True)]
    px0 = x["open"].iloc[0] * (1 + W.SLIP) * (1 + W.FEE_SPOT)
    eq = x["close"] / px0
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    dd = float((eq / eq.cummax() - 1).min())
    cagr = float(eq.iloc[-1] ** (1 / yrs) - 1)
    return dict(final=round(10000 * float(eq.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1),
                cdd=round(cagr / abs(dd), 3))


def boot(trades_pool, n=13, paths=10000):
    rng = np.random.default_rng(SEED)
    pn = np.asarray(trades_pool)
    x = pn[rng.integers(0, len(pn), size=(paths, n))]
    e = np.cumprod(1 + x, axis=1)
    e = np.concatenate([np.ones((paths, 1)), e], axis=1)
    dd = (e / np.maximum.accumulate(e, axis=1) - 1).min(axis=1)
    return round(100 * float((dd <= -0.20).mean()), 2)


def key(t):
    return (t["signal"], t["side"])


def deltas(r, b):
    bt = {key(t): t["pnl"] for t in tl(b)}
    vt = {key(t): t["pnl"] for t in tl(r)}
    out = {}
    for k in sorted(set(bt) | set(vt)):
        out[k] = np.log1p(vt.get(k, 0.0)) - np.log1p(bt.get(k, 0.0))
    return out


def changed(r, b, size_change=False):
    """Trade cambiati (criterio 1): tolti, nuovi, uscita/motivo/riempimenti/prese diverse; per K anche la sola dimensione."""
    bt = {key(t): t for t in tl(b)}
    vt = {key(t): t for t in tl(r)}
    ch = set(bt) ^ set(vt)
    for k in set(bt) & set(vt):
        a, v = bt[k], vt[k]
        if (a.get("exit"), a.get("reason")) != (v.get("exit"), v.get("reason")) or v.get("n_fills", 1) != 1 \
                or v.get("partial", 0) or v.get("tp_done", 0) or (size_change and abs(a["expo"] - v["expo"]) > 1e-6):
            ch.add(k)
    return sorted(ch)


def signflip(dl):
    x = np.array([v for v in dl if abs(v) > 1e-12])
    m = len(x)
    if m == 0:
        return 1.0, 0
    obs = x.sum()
    if m <= 20:
        signs = np.array(list(itertools.product([1, -1], repeat=m)))
        s = signs @ np.abs(x)
        return float((s >= obs - 1e-12).mean()), m
    rng = np.random.default_rng(SEED)
    s = (rng.choice([1, -1], size=(100000, m)) * np.abs(x)).sum(axis=1)
    return float(((s >= obs - 1e-12).sum() + 1) / 100001), m


# ---------------------------------------------------------------- configurazioni (PREREG §4)
MAIN = {
    "E1": ("E", dict(entry=("E1", (0, 2, 4))), [dict(entry=("E1", (0, 3))), dict(entry=("E1", (0, 1, 2, 3, 4)))]),
    "E2": ("E", dict(entry=("E2", 3)), [dict(entry=("E2", 2)), dict(entry=("E2", 4))]),
    "E3": ("E", dict(entry=("E3", 0.5, 14)), [dict(entry=("E3", 0.25, 14)), dict(entry=("E3", 0.75, 14))]),
    "U1": ("U", dict(exit=("U1", 0.5)), [dict(exit=("U1", 1 / 3)), dict(exit=("U1", 2 / 3))]),
    "U2": ("U", dict(exit=("U2", 2.0, 3.0)), [dict(exit=("U2", 2.25, 2.75)), dict(exit=("U2", 1.75, 3.25))]),
    "T1": ("T", dict(tp=dict(levels=(3,), frac=1 / 3)), [dict(tp=dict(levels=(2,), frac=1 / 3)),
                                                         dict(tp=dict(levels=(4,), frac=1 / 3))]),
    "K2,25": ("K", dict(k=2.25), [dict(k=2.0), {}]),
    "K2,75": ("K", dict(k=2.75), [{}, dict(k=3.0)]),
    "K3,0": ("K", dict(k=3.0), [dict(k=2.75), dict(k=3.25)]),
    "D1": ("D", dict(dist=("D1",)), []),
    "D2": ("D", dict(dist=("D2", 2)), [dict(dist=("D2", 3))]),
    "D3a": ("D", dict(dist=("D3", 0.8)), [dict(dist=("D3", 0.7)), dict(dist=("D3", 0.9))]),
    "D3b": ("D", dict(dist=("D3", 1.2)), [dict(dist=("D3", 1.1)), dict(dist=("D3", 1.3))]),
    "G7": ("G", dict(g7=True), []),
}
LABEL = {"E1": "E1 DCA lun/mer/ven", "E2": "E2 DCA 3 settimane", "E3": "E3 1/2 + ritracc. 0,5 ATR",
         "U1": "U1 uscita 1/2 + conferma", "U2": "U2 trailing 2,0/3,0", "T1": "T1 1/3 a +3R (controllo)",
         "K2,25": "K 2,25 ATR", "K2,75": "K 2,75 ATR", "K3,0": "K 3,0 ATR", "D1": "D1 senza distribuzione",
         "D2": "D2 distribuzione 2 dom.", "D3a": "D3a soglie ×0,8", "D3b": "D3b soglie ×1,2", "G7": "G7 sette giorni"}

BASE = {p: run({}, p) for p in PER}
BM = {p: met(BASE[p], p) for p in PER}
assert BM["ALL"]["final"] == 27190 and BM["ALL"]["dd"] == -9.8 and BM["L"]["dd"] == -19.2
POOL_B = [t["pnl"] for t in tl(BASE["L"])] + [t["pnl"] for t in tl(BASE["ALL"])]
BOOT_B = boot(POOL_B)
BH = {p: bh(p) for p in PER}

rows, drows, res = [], [], {}


def evaluate(name, cfg, neigh, size_change=False):
    R = {p: run(cfg, p) for p in PER}
    M = {p: met(R[p], p) for p in PER}
    g7 = bool(cfg.get("g7"))
    ch = {p: (None if g7 else changed(R[p], BASE[p], size_change)) for p in ("ALL", "IS", "OOS")}
    if g7:
        c1 = True
    else:
        c1 = len(ch["ALL"]) >= 3 and len(ch["IS"]) >= 1 and len(ch["OOS"]) >= 1
    c2 = all(M[p]["cdd"] > BM[p]["cdd"] and M[p]["final"] > BM[p]["final"] for p in ("IS", "OOS"))
    c3 = M["L"]["dd"] >= BM["L"]["dd"]
    NM = [met(run(c, "ALL"), "ALL") for c in neigh]
    c4 = all(n["cdd"] > BM["ALL"]["cdd"] and n["final"] > BM["ALL"]["final"] for n in NM) if NM else None
    dl, top, c5, p, m = {}, [], None, None, None
    if not g7:
        dl = deltas(R["ALL"], BASE["ALL"])
        vals = np.array(list(dl.values()))
        pos = np.sort(vals[vals > 0])[::-1]
        c5 = bool(vals.sum() > 0 and vals.sum() - pos[:2].sum() > 0)
        top = sorted(((k, v) for k, v in dl.items() if abs(v) > 0.001), key=lambda z: -abs(z[1]))
        p, m = signflip(list(dl.values()))
        for (sg, sd), v in dl.items():
            drows.append(dict(variante=name, segnale=sg, lato=sd, delta_log_pct=round(100 * v, 2)))
    c6 = M["ALL"]["wo_best"] >= BM["ALL"]["wo_best"]
    pool = [t["pnl"] for t in tl(R["L"])] + [t["pnl"] for t in tl(R["ALL"])]
    bt = None if g7 else boot(pool)
    res[name] = dict(M=M, NM=NM, ch=ch, c=[c1, c2, c3, c4, c5, c6], p=p, m=m, top=top, boot=bt, R=R)
    return res[name]


for nm, (dim, cfg, neigh) in MAIN.items():
    evaluate(nm, cfg, neigh, size_change=(dim == "K"))

# ---------------------------------------------------------------- placebo P-D (valore dell'uscita per distribuzione)
bt = tl(BASE["ALL"])
dist_tr = [t for t in bt if t.get("reason") == "dist"]
wb = W.weekly_bars(F)
cands = []
for t in dist_tr:
    s0 = pd.Timestamp(t["signal"])
    ex = pd.Timestamp(t["exit"]) - pd.Timedelta(days=1)          # domenica della decisione reale
    cands.append([dd for dd in wb.index if s0 < dd <= ex])
rng = np.random.default_rng(SEED)
pla = []
for _ in range(N_PLA):
    force = {c[rng.integers(0, len(c))] for c in cands}
    r = E.simulate(F, dict(force_exit=force, dist=("D1",)), start="2021-01-01")
    pla.append(float(r["equity"].iloc[-1]))
pla = np.array(pla)
P_D = float(((pla >= BM["ALL"]["final"]).sum() + 1) / (N_PLA + 1))

# ---------------------------------------------------------------- Holm sui 14 test con p-value
fam = {nm: res[nm]["p"] for nm in MAIN if nm != "G7"}
fam["P-D"] = P_D
order = sorted(fam, key=lambda z: fam[z])
holm, stop = {}, False
for i, nm in enumerate(order):
    thr = 0.05 / (len(fam) - i)
    ok = (not stop) and fam[nm] <= thr
    if not ok:
        stop = True
    holm[nm] = (ok, thr)

# ---------------------------------------------------------------- G7: mediana dei 7 giorni
g7r = res["G7"]["R"]["ALL"]["runs"]
g7days = {dname: round(float(rr["equity"].iloc[-1]) * 7) for dname, rr in g7r.items()}
g7med = int(np.median(list(g7days.values())))


def verdict(nm):
    c = res[nm]["c"]
    crit = [x for x in c if x is not None]
    if not c[0]:
        return "senza potenza (non batte)"
    if all(crit):
        return "proponibile" if holm.get(nm, (False,))[0] else "batte W3.1, su carta"
    return "non batte W3.1"


VER = {nm: verdict(nm) for nm in MAIN}

# ---------------------------------------------------------------- combinazione (PREREG §7)
passing = {}
for nm, (dim, _, _) in MAIN.items():
    if VER[nm] in ("proponibile", "batte W3.1, su carta"):
        sc = min(res[nm]["M"]["IS"]["cdd"], res[nm]["M"]["OOS"]["cdd"])
        if dim not in passing or sc > passing[dim][1]:
            passing[dim] = (nm, sc)
COMBO = None
if len(passing) >= 2:
    cfg = {}
    for dim, (nm, _) in passing.items():
        cfg.update(MAIN[nm][1])
    if "exit" in cfg and cfg["exit"][0] == "U2" and "k" in cfg:
        cfg["exit"] = ("U2", cfg["k"] - 0.5, cfg["k"] + 0.5)
    COMBO = evaluate("COMBO", cfg, [], size_change=True)

# ---------------------------------------------------------------- output
H = "| Regola | Finale 2021+ | CAGR | DD | CAGR/DD | Trade | WR | Peggiore | Perdita allo stop max | IS fin. / CDD | OOS fin. / CDD | 2018–20 fin. / DD | Senza migliore | P(DD≥20%) |"
say("# Risultati · ingressi/uscite W3.1 (PREREG 08da8cc)\n")
say(H)
say("|" + "---|" * 14)


def line(lbl, M, b):
    a = M["ALL"]
    say(f"| {lbl} | {a['final']:,} | {a['cagr']} | {a['dd']} | {a['cdd']} | {a['n']} | {a['wr']} | {a['worst']} | "
        f"{a['risk_max']} | {M['IS']['final']:,} / {M['IS']['cdd']} | {M['OOS']['final']:,} / {M['OOS']['cdd']} | "
        f"{M['L']['final']:,} / {M['L']['dd']} | {a['wo_best']:,} | {b if b is not None else 'n.d.'} |")
    rows.append(dict(regola=lbl, **{f"{p}_{k}": v for p in M for k, v in M[p].items()}, boot_p20=b))


line("W3.1 (vecchia)", BM, BOOT_B)
for nm in MAIN:
    line(LABEL[nm], res[nm]["M"], res[nm]["boot"])
if COMBO:
    line("COMBINAZIONE", COMBO["M"], COMBO["boot"])
say(f"| Buy & hold | {BH['ALL']['final']:,} | {BH['ALL']['cagr']} | {BH['ALL']['dd']} | {BH['ALL']['cdd']} | 1 | | | | "
    f"{BH['IS']['final']:,} / {BH['IS']['cdd']} | {BH['OOS']['final']:,} / {BH['OOS']['cdd']} | "
    f"{BH['L']['final']:,} / {BH['L']['dd']} | | |")

say("\n## Criteri (1 potenza, 2 IS e OOS migliori, 3 DD 2018–20, 4 vicini, 5 non da ≤ 2 trade, 6 senza il migliore), p, Holm, esito")
say("| Variante | cambiati 2021+/IS/OOS | 1 | 2 | 3 | 4 | 5 | 6 | m | p | Holm | Esito |")
say("|---|---|---|---|---|---|---|---|---|---|---|---|")
fmt = lambda x: "n.a." if x is None else ("sì" if x else "no")  # noqa: E731
for nm in MAIN:
    r = res[nm]
    ch = r["ch"]
    cs = "—" if ch["ALL"] is None else f"{len(ch['ALL'])}/{len(ch['IS'])}/{len(ch['OOS'])}"
    hp = holm.get(nm)
    say(f"| {LABEL[nm]} | {cs} | " + " | ".join(fmt(x) for x in r["c"]) +
        f" | {r['m'] if r['m'] is not None else '—'} | {('%.4f' % r['p']) if r['p'] is not None else '—'} | "
        f"{('sì' if hp[0] else 'no') if hp else '—'} | {VER[nm]} |")
say(f"\nPlacebo P-D (uscite per distribuzione spostate a caso nei 4 trade, {N_PLA} estrazioni): p = {P_D:.4f}; "
    f"W3.1 {BM['ALL']['final']:,} contro mediana placebo {int(np.median(pla)):,} (5°–95°: {int(np.percentile(pla, 5)):,}–"
    f"{int(np.percentile(pla, 95)):,}); Holm {'sì' if holm['P-D'][0] else 'no'}")

say("\n## Vicini (dal 2021: finale / CAGR/DD)")
for nm, (dim, cfg, neigh) in MAIN.items():
    if res[nm]["NM"]:
        say(f"- {LABEL[nm]}: " + "; ".join(f"{n['final']:,} / {n['cdd']}" for n in res[nm]["NM"]))
say("\n## Trade che cambiano (Δ log-rendimento del trade, punti %, |Δ| > 0,1)")
for nm in MAIN:
    if res[nm]["top"]:
        say(f"- {LABEL[nm]}: " + ", ".join(f"{k[0]} {k[1]} {100*v:+.1f}" for k, v in res[nm]["top"]))
say(f"\n## G7: finale dei 7 giorni singoli (×7 della quota) {g7days}; mediana {g7med:,}; G7 {res['G7']['M']['ALL']['final']:,}")
say(f"\nDimensioni promosse: {passing or 'nessuna'}; combinazione: {'eseguita' if COMBO else 'non prevista (meno di 2 dimensioni)'}")

(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
pd.DataFrame(rows).to_csv(HERE / "varianti.csv", index=False)
pd.DataFrame(drows).to_csv(HERE / "trade_delta.csv", index=False)
pd.DataFrame([dict(giorno=k, finale=v) for k, v in g7days.items()]).to_csv(HERE / "giorni_g7.csv", index=False)
pd.Series(pla).to_csv(HERE / "placebo_pd.csv", index=False, header=["finale"])
