"""zeiierman3 · esecuzione completa del PREREG (b421b1c). Uso: python3 z3_run.py  → risultati.txt e CSV in questa cartella."""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
import z3_lib as Z
import z3_w32 as V

warnings.filterwarnings("ignore")
D = Z.HERE
OUT = []
RNG = np.random.default_rng(20261123)
NP = 2000


def say(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); OUT.append(s)


d, a = Z.load()
z1, z4 = Z.indicators(d), Z.indicators(a)
FUND = Z.funding()
f_repo, f_long = V.frames()
P3 = ("P1 2018-20", "P2 2021-23", "P3 2024-26")

# ---------- W3.2: riferimento per periodo, stato (in posizione) per R5 ----------
w32 = {}
for p, (s, e) in Z.PERIODS.items():
    fr = f_long if p.startswith("P1") else f_repo
    w32[p] = V.simulate(fr, s, min(e, "2026-11-15"))
inpos = pd.Series(False, d.index); entry_day = pd.Series(False, d.index)
for p in ("P1 2018-20", "dal 2021"):
    r = w32[p]; pend_ = str((pd.Timestamp(Z.PERIODS[p][1]) + pd.Timedelta(days=1)).date())
    for t in r["trades"] + ([dict(r["open"], exit=pend_)] if r["open"] else []):
        inpos.loc[t["entry"]:pd.Timestamp(t["exit"]) - pd.Timedelta(days=1)] = True; entry_day.loc[t["entry"]] = True
inpos.loc["2026-11-16":] = True; entry_day.loc["2026-11-16"] = True          # short reale di W3.2 (segnale 15/11)
day4 = a.index.normalize()
gate4 = ~inpos.reindex(day4).fillna(False).to_numpy()
force4 = entry_day.reindex(day4).fillna(False).to_numpy() & (a.index.hour == 0)

CONF = {  # nome: (df, z, regola, linea, ent, ex, stop, opzioni)
    "V1 R1 tz 1D": ("1D", "R1", "tz", -90, -20, None),
    "V2 R2 tz 1D": ("1D", "R2", "tz", -90, -20, None),
    "V3 R3 tz 1D": ("1D", "R3", "tz", -90, -20, ("atr", 2.0)),
    "V4 R1 tz 4h": ("4h", "R1", "tz", -90, -20, None),
    "V5 R2 tz 4h": ("4h", "R2", "tz", -90, -20, None),
    "V6 R3 tz 4h": ("4h", "R3", "tz", -90, -20, ("atr", 2.0)),
    "V7 R5 4h": ("4h", "R5", "tz", -70, -30, ("atr", 2.5)),
    "A1 R1 pz 1D": ("1D", "R1", "pz", -90, -20, None),
    "A2 R2 pz 1D": ("1D", "R2", "pz", -90, -20, None),
    "A3 R1 cz 1D": ("1D", "R1", "cz", -90, -20, None),
    "A4 R2 cz 1D": ("1D", "R2", "cz", -90, -20, None),
}


def run(name, s, e, ent=None, ex=None, stop="def"):
    tf, rule, line, en0, ex0, st0 = CONF[name]
    df, z, bpd = (d, z1, 1) if tf == "1D" else (a, z4, 6)
    kw = dict(gate=gate4, force_exit=force4) if rule == "R5" else {}
    return Z.simulate(df, z, rule, s, e, line=line, ent=en0 if ent is None else ent, ex=ex0 if ex is None else ex,
                      stop=st0 if stop == "def" else stop, bars_per_day=bpd, **kw)


def placebo(df, t, s, e, n=NP):
    """Stesse durate dei trade e degli intervalli flat, ordine casuale; open→open con costi, senza stop. Statistica: finale."""
    if len(t) == 0:
        return np.nan, np.nan
    idx = df.index; O = df.open.to_numpy(float); C = df.close.to_numpy(float)
    i0 = idx.searchsorted(pd.Timestamp(s)); i1 = idx.searchsorted(pd.Timestamp(e) + pd.Timedelta(days=1)) - 1
    ins = [idx.get_loc(x) for x in t.ingresso]; outs = [idx.get_loc(x) for x in t.uscita]
    dur = np.array([max(b - a_, 1) for a_, b in zip(ins, outs)])
    gaps = np.array([max(ins[0] - i0, 0)] + [max(ins[k] - outs[k - 1], 0) for k in range(1, len(ins))] + [max(i1 + 1 - outs[-1], 0)])
    real = float(np.prod(1 + t.pnl))
    cnt = 0; vals = []
    for _ in range(n):
        dd_, gg = RNG.permutation(dur), RNG.permutation(gaps)
        k = i0 + gg[0]; m = 1.0
        for j, du in enumerate(dd_):
            if k >= i1:
                break
            b = k + du
            px_out = O[b] if b <= i1 else C[i1]
            m *= (px_out * (1 - Z.SLIP) / (O[k] * (1 + Z.SLIP))) * (1 - Z.FEE) ** 2
            k = b + gg[j + 1]
        vals.append(m); cnt += m >= real
    return round((1 + cnt) / (n + 1), 4), round(float(np.median(vals)) * Z.CAP)


# ---------- riferimenti ----------
say("# zeiierman3 · risultati (PREREG b421b1c). 10.000 $ per periodo, 1x, costi 0,1% + 0,1% per lato.")
rows = []
for p, (s, e) in Z.PERIODS.items():
    rows.append(dict(conf="Buy & hold", periodo=p, **Z.buyhold(d, s, e)))
    rows.append(dict(conf="W3.2 (al 15/11)", periodo=p, **V.met(w32[p])))

# ---------- configurazioni giudicate ----------
crit, trades_all = [], {}
for name in CONF:
    tf = CONF[name][0]; df = d if tf == "1D" else a
    per_ok = {}
    for p, (s, e) in Z.PERIODS.items():
        t, cv = run(name, s, e); m = Z.metrics(t, cv)
        m["senza_top2"] = Z.without_top(t, 2)
        rows.append(dict(conf=name, periodo=p, **m)); per_ok[p] = m
        if len(t):
            t.assign(conf=name, periodo=p).to_csv(D / "trades" / f"{name.split()[0]}_{p.split()[0]}.csv", index=False)
    tt, cvt = run(name, "2018-01-01", Z.END); trades_all[name] = tt
    pp, pmed = placebo(df, tt, "2018-01-01", Z.END)
    bh = {p: [r for r in rows if r["conf"] == "Buy & hold" and r["periodo"] == p][0] for p in P3}
    c = dict(conf=name, n_tot=len(tt), finale_2018=round(float(np.prod(1 + tt.pnl)) * Z.CAP) if len(tt) else Z.CAP,
             c1_positivo=all(per_ok[p]["finale"] > Z.CAP for p in P3),
             c2_batte_bh=all((per_ok[p]["cagr_dd"] if per_ok[p]["cagr_dd"] == per_ok[p]["cagr_dd"] else -9) > bh[p]["cagr_dd"] for p in P3),
             c3_dd35=all(per_ok[p]["dd"] >= -35 for p in P3),
             c4_non_conc=len(tt) >= 8 and all(per_ok[p]["senza_top2"] > Z.CAP for p in P3),
             placebo_p=pp, placebo_mediana=pmed)
    # vicini
    tf, rule = CONF[name][0], CONF[name][1]
    if rule == "R5":
        nb = [(en, ex, "def") for en in (-65, -75) for ex in (-25, -35)]
    else:
        nb = [(en, ex, "def") for en in (-85, -90, -95) for ex in (-15, -20, -25, -30) if not (en == -90 and ex == -20)]
        if rule == "R3":
            nb += [(-90, -20, ("atr", 1.5)), (-90, -20, ("atr", 2.5)), (-90, -20, ("low", 10))]
    okn = 0; vr = []
    for en, ex, stp in nb:
        fins = []
        for p in P3:
            s, e = Z.PERIODS[p]; t, cv = run(name, s, e, en, ex, stp); fins.append(Z.metrics(t, cv)["finale"])
        okn += all(x > Z.CAP for x in fins); vr.append(dict(conf=name, ent=en, ex=ex, stop=str(stp), **dict(zip(P3, fins))))
    pd.DataFrame(vr).to_csv(D / "vicini" / f"{name.split()[0]}.csv", index=False)
    c.update(vicini_ok=f"{okn}/{len(nb)}", c6_vicini=okn >= 0.75 * len(nb))
    crit.append(c); say(name, c)

res = pd.DataFrame(rows)
res.to_csv(D / "risultati.csv", index=False)

# ---------- R4 short descrittivo ----------
r4 = []
for tf, df, z, bpd in (("1D", d, z1, 1), ("4h", a, z4, 6)):
    for p, (s, e) in Z.PERIODS.items():
        t, cv = Z.simulate(df, z, "R4", s, e, side=-1, fund=FUND, bars_per_day=bpd)
        r4.append(dict(conf=f"R4 short tz {tf}", periodo=p, **Z.metrics(t, cv)))
r4 = pd.DataFrame(r4); r4.to_csv(D / "r4_short.csv", index=False)

# ---------- dentro W3.2 ----------
tzd = z1["tz"]
wrows, wtouch = [], []
for var in ("W1", "W2"):
    for p, (s, e) in Z.PERIODS.items():
        fr = f_long if p.startswith("P1") else f_repo
        r = V.simulate(fr, s, min(e, "2026-11-15"), var=var, tz=tzd)
        wrows.append(dict(conf=var, periodo=p, **V.met(r)))
        if p in ("P1 2018-20", "dal 2021"):
            for t in r["trades"] + ([r["open"]] if r["open"] else []):
                if var == "W2" and t.get("half") not in (None,):
                    wtouch.append(dict(var=var, entry=t["entry"], side=t["side"], half=t["half"], pnl=round(t.get("pnl", np.nan) * 100, 2)))
            for t in r["x_trades"]:
                wtouch.append(dict(var=var, entry=t["entry"], side=1, half="", exit=t.get("exit"), pnl=round(t["pnl"] * 100, 2)))
wres = pd.DataFrame(wrows); wres.to_csv(D / "w32_varianti.csv", index=False)
pd.DataFrame(wtouch).to_csv(D / "w32_trade_toccati.csv", index=False)


def w_placebo(var, n=1000):
    """Statistica: CAGR/|DD| dal 2021 (f_repo, fino al 15/11)."""
    fr = f_repo; s, e = "2021-01-01", "2026-11-15"
    real = V.simulate(fr, s, e, var=var, tz=tzd); rv = V.met(real)["cagr_dd"]
    idx = fr[fr.index <= e].index; t0 = idx.searchsorted(pd.Timestamp(s))
    base = V.simulate(fr, s, e)
    if var == "W2":
        tr = [t for t in real["trades"] + ([real["open"]] if real["open"] else []) if t.get("half")]
        spans = [(idx.get_loc(pd.Timestamp(t["entry"])), idx.get_loc(pd.Timestamp(t.get("exit", e))) - 1) for t in tr]
    else:
        flat = np.ones(len(idx), bool); flat[:t0] = False
        for t in base["trades"] + ([base["open"]] if base["open"] else []):
            flat[idx.get_loc(pd.Timestamp(t["entry"])) - 1: idx.get_loc(pd.Timestamp(t.get("exit", e))) + 1] = False
        durs = [idx.get_loc(pd.Timestamp(t["exit"] if t["exit"] != "fine" else e)) - idx.get_loc(pd.Timestamp(t["entry"])) for t in real["x_trades"]]
        cand = np.flatnonzero(flat)
    vals = []
    for _ in range(n):
        if var == "W2":
            days = {int(RNG.integers(a_, max(a_ + 1, b))) for a_, b in spans if b > a_}
            r = V.simulate(fr, s, e, var="W2", tz=tzd, w2_days=days)
        else:
            plan = {}; used = np.zeros(len(idx), bool)
            for du in durs:
                for _try in range(50):
                    k = int(RNG.choice(cand))
                    if not used[k:k + du + 1].any():
                        plan[k] = k + max(du, 1); used[k:k + du + 1] = True; break
            r = V.simulate(fr, s, e, var="W1", tz=tzd, w1_plan=plan)
        vals.append(V.met(r)["cagr_dd"])
    vals = np.array(vals)
    return rv, round((1 + (vals >= rv).sum()) / (n + 1), 4), round(float(np.median(vals)), 2)


wp = {v: w_placebo(v) for v in ("W1", "W2")}

# ---------- Holm ----------
ps = {c["conf"]: c["placebo_p"] for c in crit}
ps.update({v: wp[v][1] for v in wp})
order = sorted(ps, key=lambda k: (np.inf if ps[k] != ps[k] else ps[k]))
m = len(order); holm = {}; stop_ = False
for j, k in enumerate(order):
    thr = 0.05 / (m - j); ok = (not stop_) and ps[k] == ps[k] and ps[k] <= thr
    if not ok:
        stop_ = True
    holm[k] = (round(thr, 4), ok)
for c in crit:
    c["holm_soglia"], c["c5_holm"] = holm[c["conf"]]
    c["VALIDA"] = all(c[k] for k in ("c1_positivo", "c2_batte_bh", "c3_dd35", "c4_non_conc", "c5_holm", "c6_vicini"))
cr = pd.DataFrame(crit); cr.to_csv(D / "criteri.csv", index=False)

# ---------- stampa ----------
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
cols = ["conf", "periodo", "finale", "rend", "cagr", "dd", "cagr_dd", "mar", "trade", "wr", "espo", "senza_top2"]
say("\n## Configurazioni per periodo (P3 indicatore al 22/11; W3.2 al 15/11)")
say(res[cols].to_string(index=False))
say("\n## Criteri (PREREG): c1 positivo nei 3 periodi, c2 CAGR/DD > B&H nei 3, c3 DD ≥ −35%, c4 ≥ 8 trade e senza i 2 migliori > 10k, c5 placebo+Holm (m=13), c6 vicini ≥ 75%")
say(cr.to_string(index=False))
say("\n## R4 short (solo descrittivo, funding incluso)")
say(r4[["conf", "periodo", "finale", "rend", "cagr", "dd", "cagr_dd", "trade", "wr", "espo"]].to_string(index=False))
say("\n## Dentro W3.2 (dati congelati al 15/11)")
wall = pd.concat([res[res.conf == "W3.2 (al 15/11)"], wres])
say(wall[["conf", "periodo", "finale", "rend", "cagr", "dd", "cagr_dd", "mar", "trade", "wr"]].to_string(index=False))
for v in wp:
    say(f"placebo {v}: CAGR/DD reale dal 2021 {wp[v][0]}, p {wp[v][1]}, mediana placebo {wp[v][2]}, Holm {holm[v]}")
say("trade toccati:\n" + pd.DataFrame(wtouch).to_string(index=False))
open(D / "risultati.txt", "w").write("\n".join(OUT) + "\n")
