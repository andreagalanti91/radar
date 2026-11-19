"""Parte 2 · fase 2: esegue il PREREG (c8b2bd5) alla lettera. Output: risultati.txt, *.csv in questa cartella.
Uso: python3 p2_run.py  (4 processi per i placebo; ~10–20 minuti)"""
from __future__ import annotations

import json
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from p2_data import load  # noqa: E402
import p2_engine as E  # noqa: E402
from radar import weekly as W  # noqa: E402

import os
N_PLA, SEED, ALPHA = int(os.environ.get("P2_NPLA", 2000)), 20261118, 0.05 / 51
d = load()
F, FL = d["f"], d["fl"]
WB_F, WB_L = W.weekly_bars(F), W.weekly_bars(FL)
END = str(F.index[-1].date())
PER = {"ALL": (F, "2021-01-01", None, WB_F), "IS": (F, "2021-01-01", "2023-12-31", WB_F),
       "OOS": (F, "2024-01-01", None, WB_F), "L": (FL, "2018-01-01", "2020-12-31", WB_L)}
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


# ------------------------------------------------------------------------------------------------ serie esterne (PREREG §4)
dv = d["dvol"]["close"]
dvz = (dv - dv.rolling(180, min_periods=90).mean()) / dv.rolling(180, min_periods=90).std()
o = d["opt"]
skew = (o["pw_iv"] - o["cw_iv"]).where((o["pw_btc"] >= 10) & (o["cw_btc"] >= 10))
eb = d["ethbtc"]["close"].resample("W-SUN").last()
bd = d["btcdom"]["close"].resample("W-SUN").last()
lr = np.log(FL["close"]).diff()
vol30 = lr.rolling(30).std() * np.sqrt(365)
vrp = dv / (vol30 * 100).reindex(dv.index)


def at(s, day):
    v = s.get(day, np.nan)
    return np.nan if pd.isna(v) else float(v)


def f_vrp(T):
    return lambda side, day: not (at(vrp, day) > T)


def f_skew(T):
    def a(side, day):
        x = at(skew, day)
        return not ((side > 0 and x > T) or (side < 0 and x < -T))
    return a


def f_rot(series, n, below):
    ema = series.ewm(span=n, adjust=False, min_periods=n).mean()
    def a(side, day):
        x, m = at(series, day), at(ema, day)
        if np.isnan(x) or np.isnan(m):
            return True
        return x < m if below else x > m
    return a


FILTERS = {"O1": (f_vrp, [1.2, 1.1, 1.4], False), "O3": (f_skew, [0.0, 1.0, 2.0], True),
           "R1": (lambda n: f_rot(eb, n, True), [20, 10, 40], True), "R2": (lambda n: f_rot(bd, n, False), [20, 10, 40], False)}
# terzo campo: testabile nel 2018–20


# ------------------------------------------------------------------------------------------------------------- metriche
def run(per, **kw):
    x, s, e, wb = PER[per]
    return E.simulate(x, start=s, end=e, wb=wb, **kw)


def trades_of(r):
    return r["trades"] + ([dict(r["open"], pnl=r["open"]["pnl_close"])] if r["open"] else [])


def met_eq(eq: pd.Series, pn=None, expo=None) -> dict:
    e = eq / eq.iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    tot, dd = float(e.iloc[-1] - 1), float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1)
    m = dict(final=round(10000 * float(e.iloc[-1])), ret=round(100 * tot, 1), dd=round(100 * dd, 1),
             mar=round(tot / abs(dd), 2) if dd < 0 else np.nan, cagr=round(100 * cagr, 1),
             cdd=round(cagr / abs(dd), 3) if dd < 0 else np.nan)
    if pn is not None:
        pn = np.asarray(pn)
        m.update(n=len(pn), wr=round(100 * float((pn > 0).mean()), 1) if len(pn) else np.nan,
                 worst=round(100 * float(pn.min()), 1) if len(pn) else np.nan,
                 pf=round(float(pn[pn > 0].sum() / -pn[pn < 0].sum()), 2) if (pn < 0).any() else np.inf,
                 wo_best=round(10000 * float(np.prod(1 + np.sort(pn)[:-1]))) if len(pn) else 10000)
    if expo is not None:
        m["expo"] = round(float(expo.mean()), 3)
    return m


def met(r):
    pn = [t["pnl"] for t in trades_of(r)]
    return met_eq(r["equity"], pn, r.get("expo"))


def keyset(r):
    return {(t["signal"], t["side"]) for t in trades_of(r)}


def bh(per):
    x, s, e, _ = PER[per]
    x = x[(x.index >= s) & ((x.index <= e) if e else True)]
    px0 = x["open"].iloc[0] * (1 + W.SLIP) * (1 + W.FEE_SPOT)
    return met_eq(x["close"] / px0 * 10000)


BASE = {p: run(p) for p in PER}
BM = {p: met(BASE[p]) for p in PER}
BH = {p: bh(p) for p in PER}
assert BM["ALL"]["final"] == 78474, BM["ALL"]


def ruin(eq: pd.Series, n_paths=10000, years=6, block=60, seed=SEED) -> dict:
    r = eq.pct_change().dropna().to_numpy()
    T = int(365 * years)
    nb = int(np.ceil(T / block))
    rng = np.random.default_rng(seed)
    out = {"p30": 0, "p50": 0, "half": 0}
    for c in range(0, n_paths, 2000):
        m = min(2000, n_paths - c)
        st = rng.integers(0, len(r) - block, size=(m, nb))
        ix = (st[:, :, None] + np.arange(block)[None, None, :]).reshape(m, -1)[:, :T]
        e = np.cumprod(1 + r[ix], axis=1)
        dd = (e / np.maximum.accumulate(e, axis=1) - 1).min(axis=1)
        out["p30"] += int((dd <= -0.30).sum())
        out["p50"] += int((dd <= -0.50).sum())
        out["half"] += int((e[:, -1] < 0.5).sum())
    return {k: round(100 * v / n_paths, 2) for k, v in out.items()}


RUIN_W3 = ruin(BASE["ALL"]["equity"])


def row(name, per, m, extra=None):
    x = dict(regola=name, periodo=per, **m)
    if extra:
        x.update(extra)
    return x


ROWS = []
for p in PER:
    ROWS.append(row("W3", p, BM[p]))
    ROWS.append(row("B&H", p, BH[p]))


# ------------------------------------------------------------------------------------------------------ placebo (worker)
def _pla_filter(args):
    T_fn_name, prm, probs, seed = args
    rng = np.random.default_rng(seed)
    def allow(side, day):
        h = "IS" if day.year <= 2023 else "OOS"
        return not (rng.random() < probs[h])
    r = run("ALL", allow=allow)
    return met(r)["cdd"]


def _pla_pyr(args):
    pyr, seed = args
    rng = np.random.default_rng(seed)
    days = set()
    for t in PYR_TRADES[str(pyr)]:
        ix = F.index[(F.index >= t["entry"]) & (F.index <= pd.Timestamp(t["exit"]) - pd.Timedelta(days=2))]
        k = min(t["adds"], len(ix))
        if k:
            days |= set(pd.DatetimeIndex(np.sort(rng.choice(ix.to_numpy(), size=k, replace=False))))
    pp = dict(pyr, days=days)
    return met(run("ALL", pyr=pp))["cdd"]


def _pla_vt(args):
    tgt, seed = args
    rng = np.random.default_rng(seed)
    v = vol30.resample("W-SUN").last()
    v = v[v.index >= "2020-06-01"]
    blocks = [v.iloc[i:i + 8].to_numpy() for i in range(0, len(v), 8)]
    perm = np.concatenate([blocks[j] for j in rng.permutation(len(blocks))])
    vp = pd.Series(perm[:len(v)], v.index)
    e = lambda side, wk, day: 1.0 if np.isnan(at(vp, day)) else min(1.0, tgt / at(vp, day))  # noqa: E731
    rb = lambda side, wk, day, tr: None if np.isnan(at(vp, day)) else min(1.0, tgt / at(vp, day))  # noqa: E731
    return met(run("ALL", expo_fn=e, rebal_fn=rb))["cdd"]


def pvalue(vals, obs):
    vals = np.asarray(vals)
    return round((int((vals >= obs - 1e-12).sum()) + 1) / (len(vals) + 1), 5), len(np.unique(np.round(vals, 6)))


PVALS = []


def criteria(name, cfg_m, cfg_runs, nb_ok, L_testable, neigh_mar_all, ref=None):
    """Criteri 2–5 (PREREG §7). ref: dict periodo -> metriche di riferimento (W3 o W3 scalata)."""
    ref = ref or BM
    c2 = all(cfg_m[p]["final"] > ref[p]["final"] and cfg_m[p]["mar"] > ref[p]["mar"] and cfg_m[p]["dd"] >= ref[p]["dd"] - 2
             for p in ("IS", "OOS"))
    c3 = (cfg_m["L"]["mar"] >= ref["L"]["mar"]) if L_testable else None
    c4 = all(nm > ref["ALL"]["mar"] for nm in neigh_mar_all) if not isinstance(neigh_mar_all, dict) else all(
        neigh_mar_all[k] for k in neigh_mar_all)
    c5 = cfg_m["ALL"]["wo_best"] >= ref["ALL"]["wo_best"]
    return dict(c1=nb_ok, c2=c2, c3=c3, c4=c4, c5=c5)


def verdict(c, p):
    if not c["c1"]:
        return "senza potenza"
    core = c["c2"] and c["c4"] and c["c5"] and (c["c3"] is not False)
    if not core:
        return "respinta"
    if c["c3"] is None:
        return "su carta (2018–20 non testabile)" + ("" if p < ALPHA else "; placebo non passa")
    return "proponibile" if p < ALPHA else "su carta (placebo non passa)"


VERD = []
pool = Pool(4)

# ================================================================================================ F1/F3 · filtri di W3
say("=" * 100, "\nW3 di riferimento:", json.dumps({p: {k: BM[p][k] for k in ("final", "dd", "cdd", "mar", "n")} for p in PER}))
say("Buy & hold:", json.dumps({p: {k: BH[p][k] for k in ("final", "dd", "cdd", "mar")} for p in PER}))
say("Rischio di rovina W3 (bootstrap a blocchi, 6 anni):", RUIN_W3)
for name, (mk, prms, Ltest) in FILTERS.items():
    say("\n" + "=" * 100 + f"\n{name}")
    res = {}
    for prm in prms:
        mm, ch = {}, {}
        for p in PER:
            calls = {"IS": 0, "OOS": 0}
            fn = mk(prm)
            def allow(side, day, fn=fn, calls=calls):
                calls["IS" if day.year <= 2023 else "OOS"] += 1
                return fn(side, day)
            r = run(p, allow=allow)
            mm[p] = met(r)
            b, a = keyset(BASE[p]), keyset(r)
            ch[p] = len(b - a) + len(a - b)
            if p == "ALL":
                blocked = {"IS": 0, "OOS": 0}
                for ev in r["events"]:
                    if ev["kind"] == "blocked":
                        blocked["IS" if ev["day"] <= "2023-12-31" else "OOS"] += 1
                probs = {h: (blocked[h] / calls[h] if calls[h] else 0.0) for h in blocked}
                res_calls = (dict(calls), blocked)
            ROWS.append(row(f"{name}({prm})", p, mm[p], dict(cambiati=ch[p])))
        seeds = [(name, prm, probs, SEED + 7919 * i + 101 * list(FILTERS).index(name) + prms.index(prm)) for i in range(N_PLA)]
        vals = pool.map(_pla_filter, seeds, chunksize=50)
        pv, nd = pvalue(vals, mm["ALL"]["cdd"])
        PVALS.append(dict(config=f"{name}({prm})", p=pv, distinti=nd, oss=mm["ALL"]["cdd"],
                          pla_med=round(float(np.median(vals)), 3)))
        res[prm] = (mm, ch, pv, nd, res_calls)
        say(f"{name}({prm}) | " + " | ".join(f"{p}: {mm[p]['final']} $ DD {mm[p]['dd']}% CAGR/DD {mm[p]['cdd']} MAR {mm[p]['mar']} "
                                             f"n {mm[p]['n']} cambiati {ch[p]}" for p in PER)
            + f" | senza migliore {mm['ALL']['wo_best']} (W3 {BM['ALL']['wo_best']}) | placebo p {pv} (distinti {nd}) "
              f"| blocchi/chiamate {res_calls[1]}/{res_calls[0]}")
    main = prms[0]
    mm, ch, pv, nd, _ = res[main]
    nb_ok = (ch["IS"] + ch["OOS"] >= 3) and ch["IS"] >= 1 and ch["OOS"] >= 1
    c = criteria(name, mm, None, nb_ok, Ltest, [res[q][0]["ALL"]["mar"] for q in prms[1:]])
    c["c6"] = pv < ALPHA
    v = verdict(c, pv)
    VERD.append(dict(regola=name, **c, p=pv, verdetto=v))
    say(f"{name} criteri {c} → {v}")

# ================================================================================================ F4 · piramide
say("\n" + "=" * 100 + "\nP1 piramidazione")
PYRS = [dict(base=1 / 3, steps=(1.0, 2.0), adds=(1 / 3, 1 / 3)), dict(base=0.5, steps=(1.0, 2.0), adds=(0.25, 0.25)),
        dict(base=1 / 3, steps=(0.5, 1.0), adds=(1 / 3, 1 / 3))]
PYR_TRADES = {}
res = {}
for j, pyr in enumerate(PYRS):
    mm, nadd = {}, {}
    for p in PER:
        r = run(p, pyr=pyr)
        mm[p] = met(r)
        nadd[p] = sum(t.get("adds", 0) >= 1 for t in trades_of(r))
        if p == "ALL":
            PYR_TRADES[str(pyr)] = [dict(entry=t["entry"], exit=t.get("exit") or END, adds=t.get("adds", 0)) for t in trades_of(r)]
            mm[p]["ruin"] = ruin(r["equity"])
        ROWS.append(row(f"P1[{j}]", p, {k: v for k, v in mm[p].items() if k != "ruin"}, dict(con_aggiunte=nadd[p])))
    res[j] = (mm, nadd)
pool.close()
pool = Pool(4)
for j, pyr in enumerate(PYRS):
    mm, nadd = res[j]
    vals = pool.map(_pla_pyr, [(pyr, SEED + 31 * i + j) for i in range(N_PLA)], chunksize=50)
    pv, nd = pvalue(vals, mm["ALL"]["cdd"])
    PVALS.append(dict(config=f"P1[{j}]", p=pv, distinti=nd, oss=mm["ALL"]["cdd"], pla_med=round(float(np.median(vals)), 3)))
    res[j] = (mm, nadd, pv)
    say(f"P1[{j}] {pyr} | " + " | ".join(f"{p}: {mm[p]['final']} $ DD {mm[p]['dd']}% CAGR/DD {mm[p]['cdd']} MAR {mm[p]['mar']} "
                                         f"expo {mm[p]['expo']} con aggiunte {nadd[p]}" for p in PER)
        + f" | senza migliore {mm['ALL']['wo_best']} | rovina {mm['ALL']['ruin']} | placebo p {pv} (distinti {nd})")
mm, nadd, pv = res[0]
nb_ok = nadd["IS"] + nadd["OOS"] >= 3 and nadd["IS"] >= 1 and nadd["OOS"] >= 1
c = criteria("P1", mm, None, nb_ok, True, [res[1][0]["ALL"]["mar"], res[2][0]["ALL"]["mar"]])
c["c6"] = pv < ALPHA
VERD.append(dict(regola="P1", **c, p=pv, verdetto=verdict(c, pv)))
say(f"P1 criteri {c} → {VERD[-1]['verdetto']}")

# ================================================================================================ F2 · V vol targeting
say("\n" + "=" * 100 + "\nV vol targeting settimanale")


def vt(tgt):
    e = lambda side, wk, day: 1.0 if np.isnan(at(vol30, day)) else min(1.0, tgt / at(vol30, day))  # noqa: E731
    rb = lambda side, wk, day, tr: None if np.isnan(at(vol30, day)) else min(1.0, tgt / at(vol30, day))  # noqa: E731
    return dict(expo_fn=e, rebal_fn=rb)


def w3_scaled(per, target_dd):
    """W3 con quota q di liquidità (esposizione q·E) allo stesso DD giornaliero; q ≤ 1 (niente leva)."""
    lo, hi = 0.02, 1.0
    if BM[per]["dd"] >= target_dd:   # W3 piena ha già DD minore o uguale: confronto con W3 piena
        return BM[per], 1.0
    for _ in range(30):
        q = (lo + hi) / 2
        mq = met(run(per, expo_fn=lambda side, wk, day, q=q: q * W.exposure(side, wk["close"], wk["atr"])))
        if mq["dd"] < target_dd:
            hi = q
        else:
            lo = q
    q = lo
    return met(run(per, expo_fn=lambda side, wk, day, q=q: q * W.exposure(side, wk["close"], wk["atr"]))), round(q, 3)


res = {}
for tgt in (0.5, 0.4, 0.6):
    mm, sc = {}, {}
    for p in PER:
        r = run(p, **vt(tgt))
        mm[p] = met(r)
        sc[p] = w3_scaled(p, mm[p]["dd"])
        if p == "ALL":
            mm[p]["ruin"] = ruin(r["equity"])
        ROWS.append(row(f"V({tgt:.0%})", p, {k: v for k, v in mm[p].items() if k != "ruin"},
                        dict(w3_scalata_final=sc[p][0]["final"], w3_scalata_mar=sc[p][0]["mar"], quota=sc[p][1])))
    vals = pool.map(_pla_vt, [(tgt, SEED + 17 * i) for i in range(N_PLA)], chunksize=50)
    pv, nd = pvalue(vals, mm["ALL"]["cdd"])
    PVALS.append(dict(config=f"V({tgt:.0%})", p=pv, distinti=nd, oss=mm["ALL"]["cdd"], pla_med=round(float(np.median(vals)), 3)))
    res[tgt] = (mm, sc, pv)
    say(f"V({tgt:.0%}) | " + " | ".join(f"{p}: {mm[p]['final']} $ DD {mm[p]['dd']}% CAGR/DD {mm[p]['cdd']} MAR {mm[p]['mar']} "
                                         f"expo {mm[p]['expo']} vs W3 scalata q {sc[p][1]}: {sc[p][0]['final']} $ MAR {sc[p][0]['mar']}"
                                         for p in PER)
        + f" | rovina {mm['ALL']['ruin']} | placebo p {pv} (distinti {nd})")
mm, sc, pv = res[0.5]
ref = {p: sc[p][0] for p in PER}
c = criteria("V", mm, None, True, True, {q: res[q][0]["ALL"]["mar"] > res[q][1]["ALL"][0]["mar"] for q in (0.4, 0.6)}, ref=ref)
c["c6"] = pv < ALPHA
c["ruin_ok"] = mm["ALL"]["ruin"]["p50"] <= RUIN_W3["p50"]
v = verdict(c, pv)
if not c["ruin_ok"] and v.startswith(("su carta", "proponibile")):
    v = "respinta (rovina)"
VERD.append(dict(regola="V", **c, p=pv, verdetto=v))
say(f"V criteri {c} → {v}")

# ================================================================================================ F1 · O2 autonomo
say("\n" + "=" * 100 + "\nO2 picco di DVOL rientrato (autonomo e complemento di W3)")
sunz = dvz.resample("W-SUN").last()
IDX = F.index
O_, H_, L_, C_ = (F[k].to_numpy(float) for k in ("open", "high", "low", "close"))
COST = W.FEE_SPOT


def w3_busy(per):
    """Giorni in cui W3 è in posizione nel periodo: dall'apertura d'ingresso all'apertura d'uscita esclusa."""
    busy, entries = set(), set()
    for t in trades_of(BASE[per]):
        e0, e1 = pd.Timestamp(t["entry"]), pd.Timestamp(t.get("exit") or END)
        entries.add(e0)
        busy |= set(IDX[(IDX >= e0) & (IDX < e1)])
    return busy, entries


BUSY = {p: w3_busy(p) for p in ("ALL", "IS", "OOS")}


def o2_sim(sig_days, H, start="2021-01-01", end=None, w3=None):
    """Long spot 1x: ingresso all'apertura del lunedì dopo la domenica-segnale, stop 2,5 ATRw dalla chiusura del segnale +
    trailing W3 a cricchetto (controllo giornaliero, anche il giorno d'ingresso), uscita a tempo all'apertura del lunedì dopo
    la H-esima domenica. w3 = (giorni W3 in posizione, giorni d'ingresso W3): O2 solo a W3 flat, chiude se W3 entra.
    Restituisce i rendimenti giornalieri sull'equity e i P&L dei trade."""
    end = end or END
    sel = (IDX >= start) & (IDX <= end)
    ix = np.where(sel)[0]
    ret = pd.Series(0.0, IDX[sel])
    pn, i_sig, pos = [], set(sig_days), None
    for i in ix:
        day = IDX[i]
        prev_close = None
        if pos is not None:                                   # uscite all'apertura: tempo o ingresso di W3
            if day >= pos["tex"] or (w3 and day in w3[1]):
                v1 = O_[i] * (1 - W.SLIP) * (1 - COST)
                ret[day] = v1 / pos["last"] - 1
                pn.append(v1 / pos["px0"] - 1)
                pos = None
                continue                                      # il segnale di ieri era a posizione aperta: ignorato
        if pos is None and i != ix[0] and IDX[i - 1] in i_sig and not (w3 and day in w3[0]):
            s = IDX[i - 1]
            wk = WB_F.loc[s]
            eff = O_[i] * (1 + W.SLIP) * (1 + COST)
            pos = dict(px0=eff, last=eff, stop=float(wk["close"] - 2.5 * wk["atr"]), atr=float(wk["atr"]), best=O_[i],
                       tex=s + pd.Timedelta(days=7 * H + 1))
        if pos is None:
            continue
        pos["stop"] = max(pos["stop"], pos["best"] - 2.5 * pos["atr"])
        if L_[i] <= pos["stop"]:
            v1 = min(O_[i], pos["stop"]) * (1 - W.SLIP) * (1 - COST)
            ret[day] = v1 / pos["last"] - 1
            pn.append(v1 / pos["px0"] - 1)
            pos = None
            continue
        ret[day] = C_[i] / pos["last"] - 1
        pos["last"] = C_[i]
        pos["best"] = max(pos["best"], C_[i])
        if day.dayofweek == 6 and day in WB_F.index:
            pos["atr"] = float(WB_F.loc[day, "atr"])
    if pos is not None:
        pn.append(C_[ix[-1]] * (1 - W.SLIP) * (1 - COST) / pos["px0"] - 1)
    return ret, pn


def o2_signals(S, R):
    sig = (sunz.rolling(4).max().shift(1) >= S) & (sunz <= R)
    return list(sig[sig].index)


def _pla_o2(args):
    H, n_is, n_oos, seed = args
    rng = np.random.default_rng(seed)
    suns = sunz.dropna().index
    out = []
    for lo, hi, n in (("2021-01-01", "2023-12-31", n_is), ("2024-01-01", END, n_oos)):
        cand = suns[(suns >= lo) & (suns <= hi)]
        cand = cand[cand <= pd.Timestamp(hi) - pd.Timedelta(days=1)]
        for _ in range(200):
            pick = np.sort(rng.choice(cand.to_numpy(), size=n, replace=False)) if n else np.array([], dtype="datetime64[ns]")
            if n <= 1 or (np.diff(pick).astype("timedelta64[D]").astype(int) > 7 * H).all():
                break
        out += list(pd.DatetimeIndex(pick))
    ret, _ = o2_sim(out, H)
    return met_eq((1 + ret).cumprod())["cdd"]


O2CFG = [(2.0, 1.5, 4), (1.5, 1.0, 4), (2.0, 1.0, 8)]
pool.close()
pool = Pool(4)   # nuovo pool: i processi devono vedere le funzioni di O2
w3ret = BASE["ALL"]["equity"].pct_change().fillna(0)
res = {}
for j, (S, R, H) in enumerate(O2CFG):
    sig = o2_signals(S, R)
    mm = {}
    pns = {}
    for p, (lo, hi) in {"ALL": ("2021-01-01", END), "IS": ("2021-01-01", "2023-12-31"), "OOS": ("2024-01-01", END)}.items():
        ret, pn = o2_sim(sig, H, lo, hi)
        mm[p] = met_eq((1 + ret).cumprod() * 10000, pn)
        pns[p] = pn
        # portafoglio W3 + O2 (O2 solo a W3 flat): rendimenti giornalieri sommati (mai sovrapposti)
        r2, pn2 = o2_sim(sig, H, lo, hi, w3=BUSY[p])
        wr = BASE[p]["equity"].pct_change().fillna(0) if p != "ALL" else w3ret
        port = (1 + wr.reindex(r2.index).fillna(0) + r2).cumprod() * 10000
        mm[p]["port"] = met_eq(port, [t["pnl"] for t in trades_of(BASE[p])] + pn2)
        ROWS.append(row(f"O2[{j}]", p, {k: v for k, v in mm[p].items() if k != "port"},
                        dict(port_final=mm[p]["port"]["final"], port_dd=mm[p]["port"]["dd"], port_mar=mm[p]["port"]["mar"])))
    n_is, n_oos = mm["IS"]["n"], mm["OOS"]["n"]
    vals = pool.map(_pla_o2, [(H, n_is, n_oos, SEED + 13 * i + j) for i in range(N_PLA)], chunksize=50)
    pv, nd = pvalue(vals, mm["ALL"]["cdd"])
    PVALS.append(dict(config=f"O2[{j}]", p=pv, distinti=nd, oss=mm["ALL"]["cdd"], pla_med=round(float(np.median(vals)), 3)))
    res[j] = (mm, pv)
    say(f"O2[{j}] picco {S} rientro {R} {H} sett. | " + " | ".join(
        f"{p}: {mm[p]['final']} $ DD {mm[p]['dd']}% CAGR/DD {mm[p]['cdd']} MAR {mm[p]['mar']} n {mm[p]['n']} WR {mm[p]['wr']} PF {mm[p]['pf']}"
        f" · W3+O2 {mm[p]['port']['final']} $ DD {mm[p]['port']['dd']}% MAR {mm[p]['port']['mar']}" for p in ("ALL", "IS", "OOS"))
        + f" | placebo p {pv} (distinti {nd})")
mm, pv = res[0]
c = dict(c1=mm["ALL"]["n"] >= 10, pf=mm["IS"]["pf"] >= 1.2 and mm["OOS"]["pf"] >= 1.2, mar_bh=mm["ALL"]["mar"] > BH["ALL"]["mar"],
         c6=pv < ALPHA, port=all(mm[p]["port"]["final"] > BM[p]["final"] and mm[p]["port"]["mar"] > BM[p]["mar"]
                                 and mm[p]["port"]["dd"] >= BM[p]["dd"] - 2 for p in ("IS", "OOS")))
v = "senza potenza" if not c["c1"] else ("proponibile" if all(c.values()) else
                                           ("su carta (placebo non passa)" if all(c[k] for k in ("pf", "mar_bh", "port")) else "respinta"))
VERD.append(dict(regola="O2", **c, p=pv, verdetto=v))
say(f"O2 criteri {c} → {v}")
pool.close()

# ================================================================================================ F2 · griglia G
say("\n" + "=" * 100 + "\nG griglia rischio × k × presa parziale")
G = {}
for tp in (False, True):
    for k in (2.0, 2.5, 3.0):
        for rr in (0.05, 0.10, 0.15, 0.20, 0.25):
            mm = {}
            for p in PER:
                r = run(p, expo_fn=lambda side, wk, day, rr=rr, k=k: min(1.0, rr / (k * wk["atr"] / wk["close"])), k=k,
                        tp=dict(levels=(2, 3), frac=1 / 3) if tp else None)
                mm[p] = met(r)
                if p == "ALL":
                    mm[p]["ruin"] = ruin(r["equity"])
                ROWS.append(row(f"G(r{int(rr*100)},k{k},{'TP' if tp else 'noTP'})", p, {kk: v for kk, v in mm[p].items() if kk != "ruin"}))
            G[(rr, k, tp)] = mm
RS, KS = (0.05, 0.10, 0.15, 0.20, 0.25), (2.0, 2.5, 3.0)
w3_oos_cdd = BM["OOS"]["cdd"]
grid_rows = []
for (rr, k, tp), mm in G.items():
    a = mm["ALL"]
    cons = dict(a=a["dd"] >= -15, b=mm["L"]["dd"] >= -25, c=rr <= 0.15 and a["worst"] >= -15 and mm["L"]["worst"] >= -15,
                d=mm["OOS"]["cdd"] >= w3_oos_cdd)
    nb = []
    i_r, i_k = RS.index(rr), KS.index(k)
    for di in (-1, 1):
        if 0 <= i_r + di < len(RS):
            nb.append(G[(RS[i_r + di], k, tp)]["ALL"]["cdd"])
        if 0 <= i_k + di < len(KS):
            nb.append(G[(rr, KS[i_k + di], tp)]["ALL"]["cdd"])
    cons["e"] = all(x >= 0.8 * a["cdd"] for x in nb)
    grid_rows.append(dict(r=rr, k=k, tp=tp, final=a["final"], dd=a["dd"], cagr=a["cagr"], cdd=a["cdd"], mar=a["mar"], n=a["n"],
                          wr=a["wr"], worst=a["worst"], expo=a["expo"], wo_best=a["wo_best"],
                          IS_final=mm["IS"]["final"], IS_dd=mm["IS"]["dd"], IS_cdd=mm["IS"]["cdd"],
                          OOS_final=mm["OOS"]["final"], OOS_dd=mm["OOS"]["dd"], OOS_cdd=mm["OOS"]["cdd"],
                          L_final=mm["L"]["final"], L_dd=mm["L"]["dd"], L_cdd=mm["L"]["cdd"], L_worst=mm["L"]["worst"],
                          vicini_min=round(min(nb), 3), ruin_p30=a["ruin"]["p30"], ruin_p50=a["ruin"]["p50"],
                          **{f"v_{x}": y for x, y in cons.items()}, ok=all(cons.values())))
gdf = pd.DataFrame(grid_rows)
gdf.to_csv(HERE / "griglia_G.csv", index=False)
say(gdf.drop(columns=["wo_best"]).to_string(index=False))
elig = gdf[(~gdf["tp"]) & gdf["ok"]]
if len(elig):
    best = elig["cdd"].max()
    tie = elig[elig["cdd"] >= best * 0.95].copy()
    tie["kd"] = (tie["k"] - 2.5).abs()
    choice = tie.sort_values(["r", "kd", "k"]).iloc[0]
    how = f"scelta fra {len(elig)} eleggibili (massimo CAGR/DD {best}, {len(tie)} entro il 5%)"
else:
    choice = gdf[(~gdf["tp"]) & (gdf["r"] == 0.10) & (gdf["k"] == 2.5)].iloc[0]
    how = "nessuna configurazione rispetta i vincoli → ripiego preregistrato r 10%, k 2,5"
say(f"\nSCELTA G: r {choice['r']:.0%}, k {choice['k']}, TP {'sì' if choice['tp'] else 'no'} · {how}")
say(choice.to_string())

# Kelly informativo (trade W3 2021–23, multipli di R)
tt = trades_of(BASE["IS"])
R = np.array([t["pnl"] / (t["expo"] * 2.5 * t["atr"] / t["sig_close"]) for t in tt])
if (R < 0).any() and (R > 0).any():
    pw = float((R > 0).mean())
    b = float(R[R > 0].mean() / -R[R < 0].mean())
    rk = pw - (1 - pw) / b
    say(f"\nKelly (IS, {len(R)} trade, R = {np.round(R, 2).tolist()}): p {pw:.2f}, b {b:.2f}, r* {rk:.2f} → ¼ {rk/4:.1%}, ½ {rk/2:.1%}")
else:
    say(f"\nKelly non stimabile: nell'IS {len(R)} trade e nessun perdente (R = {np.round(R, 2).tolist()})")

# Applicazione al trade short aperto dal 16/11/2026 (decisione della domenica 15/11)
wk = WB_F.loc[pd.Timestamp(END)]
cur = pd.read_csv(HERE.parents[1] / "data" / "spot.csv", index_col=0, parse_dates=True)
px_in = float(cur.loc["2026-11-16", "open"]) if pd.Timestamp("2026-11-16") in cur.index else np.nan
for nm, rr, k in (("W3 attuale", 0.25, 2.5), ("scelta G", float(choice["r"]), float(choice["k"]))):
    sd = k * wk["atr"] / wk["close"]
    ex = min(1.0, rr / sd)
    loss = ex * (sd + W.SLIP + 2 * W.FEE_PERP)
    say(f"Short 16/11 · {nm}: segnale short {bool(wk['short'])}, chiusura {wk['close']:.0f}, ATRw {wk['atr']:.0f}, stop {wk['close'] + k * wk['atr']:.0f} "
        f"({sd:.1%}), esposizione {ex:.3f}, perdita allo stop ≈ {loss:.1%} dell'equity; apertura del 16/11 {px_in:.0f}")

# ================================================================================================ Bonferroni e salvataggi
pdf = pd.DataFrame(PVALS)
pdf["passa_bonferroni"] = pdf["p"] < ALPHA
pdf.to_csv(HERE / "placebo.csv", index=False)
say("\nPlacebo (soglia Bonferroni", round(ALPHA, 5), "):\n" + pdf.to_string(index=False))
vdf = pd.DataFrame(VERD)
vdf.to_csv(HERE / "verdetti.csv", index=False)
say("\nVerdetti:\n" + vdf.to_string(index=False))
pd.DataFrame(ROWS).to_csv(HERE / "riepilogo.csv", index=False)
(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
