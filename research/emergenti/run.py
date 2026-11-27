"""emergenti · fase 2: V1–V10 del PREREG (commit 1110e53), vicini, placebo con Holm, descrittive. Nessuna modifica a radar/.
Motore: engine.py (controllo: BTC 84.820 $, ETH 39.572 $ con i parametri di default). Uscite in data/: risultati.csv,
trades_<variante>.csv, out_run.txt; cache dei trade in data/raw/cache/ (fuori da git). Uso: python3 run.py [--placebo N]"""
import importlib.util, json, pickle, sys, warnings; warnings.filterwarnings("ignore")
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; D = HERE / "data"; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402
from radar import scanner as SC  # noqa: E402
spec = importlib.util.spec_from_file_location("w32c", HERE.parent / "w32_asset2" / "crypto" / "counts.py")
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C); C.D = D / "coins"
CACHE = D / "raw" / "cache"; CACHE.mkdir(parents=True, exist_ok=True)
G = pd.date_range("2019-09-01", "2026-11-24"); ND = len(G)
PER = {"intero": ("2021-01-01", "2026-11-24"), "IS": ("2021-01-01", "2023-12-31"), "OOS": ("2024-01-01", "2026-11-24"),
       "ultimo anno": ("2025-11-24", "2026-11-24")}
YEARS = range(2021, 2027)
FEE, MMR, SLOTS, BUDGET = 0.002, 0.01, 5, 10000.0
U = pd.read_csv(D / "universe.csv").set_index("ticker"); CM = pd.read_csv(D / "counts_moneta.csv").set_index("ticker")

def member_year(t, Y, view="pit"):
    r = U.loc[t]
    if view == "oggi": return 100 < (r.rank_oggi if r.rank_oggi == r.rank_oggi else 0) <= 500
    v = r.get(f"rank_{Y}", np.nan); return v == v and 100 < v <= 200

def coins(view="pit"):
    ok = CM[CM.completa_da.notna()].index
    return [t for t in ok if t in U.index and t != "BTC" and any(member_year(t, Y, view) for Y in YEARS)]

_F = {}
def feats(t):
    if t not in _F:
        f = C.feats(t); pp = C.rd(t, "perp")
        qv = (pp["close"] * pp["volume"]).reindex(f.index) if pp is not None else pd.Series(np.nan, index=f.index)
        _F[t] = (f, qv.rolling(90, min_periods=30).mean())
    return _F[t]

_GATE = None
def gate():
    global _GATE
    if _GATE is None:
        fb = C.feats("BTC"); _GATE = SC.cancello(fb, start=str(C.full_start(fb).date()))
    return _GATE

def masks(t, f, w, mask, view):
    sun = w.index; g = gate().reindex(sun).fillna(0)
    mem = pd.Series([member_year(t, (s + pd.Timedelta(days=1)).year, view) for s in sun], index=sun)
    al, as_ = mem.copy(), mem.copy()
    if mask == "long": as_[:] = False
    if mask == "short": al[:] = False
    if mask.startswith("q"):
        wk, vm, fl = {"q52": (52, 10e6, 0.5), "q26": (26, 5e6, 0.25), "q104": (104, 20e6, 1.0)}[mask]
        hist = pd.Series((sun - f.index[0]).days / 7, index=sun) >= wk
        vol = feats(t)[1].reindex(sun) >= vm
        al &= hist & vol & (w["flow"] >= fl); as_ &= hist & vol & (w["flow"] <= -fl)
    if mask == "con": al &= g > 0; as_ &= g < 0
    if mask == "contro": al &= g < 0; as_ &= g > 0
    return al, as_

def sim_coin(args):
    t, start, end, cfg, mask, view = args
    f, qv = feats(t); f = f[f.index <= pd.Timestamp(end)]
    fs = pd.Timestamp(CM.loc[t, "completa_da"]); s0 = max(pd.Timestamp(start), fs)
    if not len(f) or s0 > f.index[-1]: return t, []
    w = E.weekly_bars(f, cfg.get("exit_span", 21)); al, as_ = masks(t, f, w, mask, view)
    o = E.simulate(f, start=str(s0.date()), trail_k=cfg.get("trail_k", 2.5), exit_span=cfg.get("exit_span", 21),
                   allow_long=al, allow_short=as_, all_perp=True)
    out = []
    A = {k: f[c].to_numpy(float) for k, c in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}
    A["FU"] = f["funding"].fillna(0).to_numpy(float)
    for tr in E.all_trades(o):
        sd = 1 if tr["side"] == "long" else -1; d = abs(tr["entry_px"] - tr["stop0"]) / tr["entry_px"]
        s = pd.Timestamp(tr["signal"])
        out.append(dict(ticker=t, side=tr["side"], signal=tr["signal"], entry=tr["entry"], exit=tr["exit"], reason=tr["reason"],
                        d=d, expo=tr["expo"], flow=tr["flow"], i_entry=tr["i_entry"], i_exit=tr["i_exit"], entry_px=tr["entry_px"],
                        exit_px=tr["exit_px"], stops=tr["stops"], btc=int(gate().get(s, 0)) * sd,
                        vol90=float(qv.get(s, np.nan)) if s in qv.index else np.nan, sett=int((s - f.index[0]).days // 7),
                        dates=f.index[tr["i_entry"]:tr["i_exit"] + 1]))
    return t, out

def tradeset(start, end, cfg, mask, view="pit", key=None):
    key = key or f"{view}_{mask}_{cfg.get('trail_k', 2.5)}_{cfg.get('exit_span', 21)}_{start}_{end}"
    p = CACHE / f"{key}.pkl"
    if p.exists(): return pickle.loads(p.read_bytes())
    jobs = [(t, start, end, cfg, mask, view) for t in coins(view)]
    with Pool(4) as pool: res = pool.map(sim_coin, jobs)
    trs = [x for _, xs in res for x in xs]; p.write_bytes(pickle.dumps(trs)); return trs

_A = {}
def arrays(t):
    if t in _A: return _A[t]
    f = feats(t)[0]
    _A[t] = {k: f[c].to_numpy(float) for k, c in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))} | {"FU": f["funding"].fillna(0).to_numpy(float)}
    return _A[t]
    return {k: f[c].to_numpy(float) for k, c in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))} | {"FU": f["funding"].fillna(0).to_numpy(float)}

def cands(trs, kfun, fee=FEE, mmr=MMR, max_days=None):
    out = []
    for tr in trs:
        A = arrays(tr["ticker"]); k = kfun(tr)
        r0, r1, v, liq = E.outcome(tr, A, k, fee=fee, mmr=mmr, max_days=max_days)
        dates = tr["dates"][r0 - tr["i_entry"]:r1 - tr["i_entry"] + 1]; g0, g1 = G.searchsorted(dates[0]), G.searchsorted(dates[-1])
        vg = pd.Series(v, index=dates).reindex(G[g0:g1 + 1]).ffill().to_numpy() if g1 - g0 != r1 - r0 else v
        intra = liq or (tr["reason"] in ("stop", "trail") and max_days is None and r1 == tr["i_exit"])
        out.append(dict(tr, i0=g0, i1=g1, v=vg, k=k, liq=liq, intra=intra, pri=tr["vol90"] if tr["vol90"] == tr["vol90"] else 0,
                        pnl=float(vg[-1] - 1)))
    return out

def met(eq, start, end, taken):
    s, e = G.searchsorted(pd.Timestamp(start)), G.searchsorted(pd.Timestamp(end))
    x = pd.Series(eq, index=G[s:s + len(eq)]).loc[:end]
    yrs = (x.index[-1] - x.index[0]).days / 365.25; fin = float(x.iloc[-1]); dd = float((x / x.cummax() - 1).min())
    cg = (fin / BUDGET) ** (1 / yrs) - 1 if fin > 0 else -1
    pn = np.array([p["pnl"] for p in taken])
    return dict(fin=round(fin), ret=round((fin / BUDGET - 1) * 100, 1), cagr=round(cg * 100, 1), dd=round(dd * 100, 1),
                cd=round(cg / abs(dd), 2) if dd < 0 else None, n=len(pn), wr=round(float((pn > 0).mean() * 100)) if len(pn) else None,
                liq=int(sum(p["liq"] for p in taken)), cd_raw=cg / abs(dd) if dd < 0 else 0.0)

def run_port(cs, start, end, slots=SLOTS):
    s, e = G.searchsorted(pd.Timestamp(start)), G.searchsorted(pd.Timestamp(end))
    cs = [c for c in cs if s <= c["i0"] <= e]
    eq, taken = E.portfolio(cs, e + 1, slots=slots, budget=BUDGET, start_i=s)
    return eq, taken

def evaluate(cs, start, end, slots=SLOTS):
    eq, taken = run_port(cs, start, end, slots); return met(eq, start, end, taken), eq, taken

def without_top(cs, taken, start, end, frac=0.10):
    n = int(np.ceil(len(taken) * frac)); top = sorted(taken, key=lambda p: -p["pnl"])[:n]
    ids = {(p["ticker"], p["i0"]) for p in top}
    return evaluate([c for c in cs if (c["ticker"], c["i0"]) not in ids], start, end)[0]["fin"]

# ------------------------------------------------------------------ buy & hold equipesato delle idonee (ribilanciato al 1/1)
def bh_ew(start, end, view="pit", fee=FEE):
    s0, e0 = pd.Timestamp(start), pd.Timestamp(end); eq = []; val = BUDGET
    cuts = [s0] + [pd.Timestamp(f"{Y}-01-01") for Y in range(s0.year + 1, e0.year + 1)] + [e0 + pd.Timedelta(days=1)]
    for a, b in zip(cuts[:-1], cuts[1:]):
        Y = a.year; days = G[(G >= a) & (G < b)]
        ids = [t for t in coins(view) if member_year(t, Y, view) and pd.Timestamp(CM.loc[t, "completa_da"]) <= pd.Timestamp(f"{Y}-01-01")
               and feats(t)[0].index[0] <= a and feats(t)[0].index[-1] >= a]
        if not ids: eq.append(pd.Series(val, index=days)); continue
        parts = []
        for t in ids:
            c = feats(t)[0]["close"].reindex(days).ffill(); o0 = float(feats(t)[0]["open"].reindex(days).dropna().iloc[0])
            parts.append(c / (o0 * (1 + fee)))
        seg = pd.concat(parts, axis=1).mean(axis=1) * val
        seg.iloc[-1] *= (1 - fee); val = float(seg.iloc[-1]); eq.append(seg)
    x = pd.concat(eq); yrs = (x.index[-1] - x.index[0]).days / 365.25; dd = float((x / x.cummax() - 1).min())
    cg = (x.iloc[-1] / BUDGET) ** (1 / yrs) - 1
    return dict(fin=round(float(x.iloc[-1])), cagr=round(cg * 100, 1), dd=round(dd * 100, 1), cd=round(cg / abs(dd), 2), cd_raw=cg / abs(dd))

# ------------------------------------------------------------------ placebo
_PL = {}
def pool_days(view="pit"):
    """monete-giorno idonee per anno: lista dell'anno, versione completa iniziata, prezzo presente."""
    if view in _PL: return _PL[view]
    out = {}
    for Y in YEARS:
        rows = []
        for t in coins(view):
            if not member_year(t, Y, view): continue
            f = feats(t)[0]; fs = pd.Timestamp(CM.loc[t, "completa_da"])
            pos = np.flatnonzero((f.index.year == Y) & (f.index >= fs) & f["open"].notna().to_numpy())
            rows += [(t, int(x)) for x in pos]; arrays(t)
        out[Y] = rows
    _PL[view] = out; return out

def rand_outcome(t, r, dur, sd, k, fee=FEE, mmr=MMR):
    A = arrays(t); n = len(A["C"]); r1 = min(r + dur, n - 1)
    O, H, L, Cc, FU = A["O"], A["H"], A["L"], A["C"], A["FU"]
    Ep = O[r] * (1 + 0.001 * sd); comm = fee - 0.001
    c = Cc[r:r1 + 1]
    if np.isnan(c).any(): c = pd.Series(c).ffill().to_numpy()
    cumf = np.cumsum(np.nan_to_num(FU[r:r1 + 1]) * sd * k * c / Ep)
    v = 1 + k * sd * (c / Ep - 1) - k * comm - cumf
    q = 1 / k - mmr; liq = Ep * (1 - q) if sd > 0 else Ep * (1 + q)
    adv = (L[r:r1] <= liq) if sd > 0 else (H[r:r1] >= liq)          # giorni prima dell'uscita all'apertura di r1
    hit = np.flatnonzero(np.nan_to_num(adv, nan=0).astype(bool))
    oo = (O[r:r1 + 1] <= liq) if sd > 0 else (O[r:r1 + 1] >= liq)
    ho = np.flatnonzero(np.nan_to_num(oo, nan=0).astype(bool))
    j = min([x for x in (hit[0] if len(hit) else None, ho[0] if len(ho) else None) if x is not None], default=None)
    if j is not None: return r, r + j, np.r_[v[:j], 0.0], True
    X = O[r1] * (1 - 0.001 * sd) if r1 > r else c[-1]
    v[-1] = 1 + k * sd * (X / Ep - 1) - k * comm - k * comm * X / Ep - (cumf[-2] if len(cumf) > 1 else 0)
    return r, r1, v, False

def _placebo_iter(args):
    spec_, seed, start, end, view = args
    rng = np.random.default_rng(seed); pdays = pool_days(view); cs = []
    for (Y, sd, dur, k) in spec_:
        pool = pdays.get(Y) or []
        if not pool: continue
        t, r = pool[rng.integers(len(pool))]
        r0, r1, v, liq = rand_outcome(t, r, dur, sd, k)
        idx = feats(t)[0].index; g0, g1 = G.searchsorted(idx[r0]), G.searchsorted(idx[r1])
        if g1 - g0 != r1 - r0: v = pd.Series(v, index=idx[r0:r1 + 1]).reindex(G[g0:g1 + 1]).ffill().to_numpy()
        cs.append(dict(ticker=t, i0=g0, i1=g1, v=v, pri=rng.random(), intra=liq, liq=liq, pnl=float(v[-1] - 1)))
    eq, taken = run_port(cs, start, end)
    return met(eq, start, end, taken)["cd_raw"]

def placebo(cs, start, end, n_iter, view="pit", seed=7):
    spec_ = [(pd.Timestamp(G[c["i0"]]).year, 1 if c["side"] == "long" else -1, int(c["i1"] - c["i0"]), c["k"]) for c in cs]
    act = evaluate(cs, start, end)[0]["cd_raw"]; pool_days(view)
    with Pool(4) as pool:
        out = np.array(pool.map(_placebo_iter, [(spec_, seed * 100000 + i, start, end, view) for i in range(n_iter)], chunksize=25))
    return round(act, 2), round(float(np.median(out)), 2), (int((out >= act).sum()) + 1) / (n_iter + 1)

def holm(ps, a=0.05):
    order = sorted(ps, key=ps.get); m = len(ps); adj, run = {}, 0.0
    for i, k in enumerate(order): run = max(run, min(1.0, ps[k] * (m - i))); adj[k] = run
    return adj

# ------------------------------------------------------------------ varianti
BASE = {}
K_W32 = lambda tr: tr["expo"]                                            # noqa: E731  size di W3.2 nella quota (1x)
def k_adapt(L, marg=0.05): return lambda tr: min(L, 1 / (tr["d"] + marg))
VAR = {  # nome: (maschera, cfg, kfun, fee, mmr)
    "V1": ("both", {}, K_W32), "V2": ("long", {}, K_W32), "V3": ("short", {}, K_W32),
    "V4": ("both", {}, k_adapt(2)), "V5": ("both", {}, k_adapt(5)), "V6": ("q52", {}, K_W32),
    "V7": ("con", {}, K_W32), "V8": ("contro", {}, K_W32), "V9": ("both", {"trail_k": 2.0}, K_W32),
    "V10": ("both", {"exit_span": 10}, K_W32)}
NEIGH = {"V1": [("both", {}, K_W32, 0.004, MMR), ("both", {}, K_W32, FEE, 0.025)],
         "V2": [("long", {}, K_W32, 0.004, MMR), ("long", {}, K_W32, FEE, 0.025)],
         "V3": [("short", {}, K_W32, 0.004, MMR), ("short", {}, K_W32, FEE, 0.025)],
         "V4": [("both", {}, k_adapt(2, 0.03), FEE, MMR), ("both", {}, k_adapt(2, 0.08), FEE, MMR)],
         "V5": [("both", {}, k_adapt(5, 0.03), FEE, MMR), ("both", {}, k_adapt(5, 0.08), FEE, MMR)],
         "V6": [("q26", {}, K_W32, FEE, MMR), ("q104", {}, K_W32, FEE, MMR)],
         "V7": [("con", {}, K_W32, 0.004, MMR), ("con", {}, K_W32, FEE, 0.025)],
         "V8": [("contro", {}, K_W32, 0.004, MMR), ("contro", {}, K_W32, FEE, 0.025)],
         "V9": [("both", {"trail_k": 1.5}, K_W32, FEE, MMR), ("both", {"trail_k": 2.5}, K_W32, FEE, MMR)],
         "V10": [("both", {"exit_span": 8}, K_W32, FEE, MMR), ("both", {"exit_span": 13}, K_W32, FEE, MMR)]}
DESC = {"V1 nozionale 1x (quota piena)": lambda tr: 1.0, "V1 2x fisso": lambda tr: 2.0, "V1 5x fisso": lambda tr: 5.0,
        "V1 per rischio (5% del budget allo stop, max 2x)": lambda tr: min(2.0, 0.25 / tr["d"])}

def cs_for(mask, cfg, kfun, start, end, fee=FEE, mmr=MMR, view="pit", max_days=None):
    return cands(tradeset(start, end, cfg, mask, view), kfun, fee, mmr, max_days)

def fmt(m): return f"{m['fin']:>7} | {m['cagr']:>6} | {m['dd']:>6} | {m['cd']} | {m['n']} | {m['wr']} | {m['liq']}"

if __name__ == "__main__":
    NP = int(sys.argv[sys.argv.index("--placebo") + 1]) if "--placebo" in sys.argv else 5000
    print("controllo motore:", E.check(), flush=True)
    L, rows = [], []
    bh = {p: bh_ew(*PER[p]) for p in PER}; L.append("B&H equipesato idonee: " + json.dumps({p: {k: v for k, v in m.items() if k != 'cd_raw'} for p, m in bh.items()}))
    res, cs_full, taken_full = {}, {}, {}
    for v, (mask, cfg, kf) in VAR.items():
        res[v] = {}
        for p, (s, e) in PER.items():
            cs = cs_for(mask, cfg, kf, s, e); m, eq, tk = evaluate(cs, s, e); res[v][p] = m
            if p == "intero": cs_full[v], taken_full[v] = cs, tk; res[v]["eq"] = eq
        m = res[v]["intero"]; res[v]["senza10"] = without_top(cs_full[v], taken_full[v], *PER["intero"])
        res[v]["vicini"] = [evaluate(cs_for(mk, cf, kk, *PER["intero"], fee=fe, mmr=mr), *PER["intero"])[0] for mk, cf, kk, fe, mr in NEIGH[v]]
        print(v, fmt(m), flush=True)
    for v in VAR:
        res[v]["placebo"] = placebo(cs_full[v], *PER["intero"], NP); print(v, "placebo", res[v]["placebo"], flush=True)
    adj = holm({v: res[v]["placebo"][2] for v in VAR})
    for v in VAR:
        r = res[v]; m = r["intero"]
        c = dict(c1=m["cd_raw"] > bh["intero"]["cd_raw"], c2=m["dd"] >= -40, c3=(m["wr"] or 0) >= 50,
                 c4=r["IS"]["ret"] > 0 and r["OOS"]["ret"] > 0 and r["ultimo anno"]["ret"] > 0, c5=m["n"] >= 20 and r["OOS"]["n"] >= 10,
                 c6=r["senza10"] > BUDGET and sum(x["cd_raw"] > bh["intero"]["cd_raw"] for x in r["vicini"]) >= 1, c7=adj[v] <= 0.05)
        ref = "V2" if v == "V2" else "V3" if v == "V3" else "V1"
        mig = v not in ("V1", "V2", "V3") and r["IS"]["cd_raw"] > res[ref]["IS"]["cd_raw"] and r["OOS"]["cd_raw"] > res[ref]["OOS"]["cd_raw"]
        rows.append(dict(variante=v, **{f"{p}_{k}": r[p][k] for p in PER for k in ("fin", "ret", "cagr", "dd", "cd", "n", "wr", "liq")},
                         senza10=r["senza10"], vicini_cd=[x["cd"] for x in r["vicini"]], vicini_fin=[x["fin"] for x in r["vicini"]],
                         p=round(r["placebo"][2], 5), p_holm=round(adj[v], 4), placebo_med=r["placebo"][1], **c,
                         falliti=",".join(k[1] for k, x in c.items() if not x) or "–", operabile=all(c.values()), migliora_V1=mig))
    pd.DataFrame(rows).to_csv(D / "risultati.csv", index=False)
    for v in VAR:
        pd.DataFrame([{k: p[k] for k in ("ticker", "side", "signal", "entry", "exit", "reason", "d", "k", "liq", "pnl", "btc", "vol90", "sett", "m")}
                      for p in taken_full[v]]).to_csv(D / f"trades_{v}.csv", index=False)
    # descrittive
    s, e = PER["intero"]; trs = tradeset(s, e, {}, "both")
    for name, kf in DESC.items():
        L.append(f"{name}: " + fmt(evaluate(cands(trs, kf), s, e)[0]))
    for sl in (3, 10): L.append(f"V1 tetto {sl} posizioni: " + fmt(evaluate(cs_full["V1"], s, e, slots=sl)[0]))
    for md in (28, 56): L.append(f"V1 uscita forzata dopo {md} giorni: " + fmt(evaluate(cands(trs, K_W32, max_days=md), s, e)[0]))
    for p in PER: L.append(f"vista oggi (101-500) {p}: " + fmt(evaluate(cs_for('both', {}, K_W32, *PER[p], view='oggi'), *PER[p])[0]) + " | B&H " + json.dumps({k: v for k, v in bh_ew(*PER[p], view='oggi').items() if k != 'cd_raw'}))
    allc = cands(trs, K_W32)
    tdf = pd.DataFrame([{k: c[k] for k in ("ticker", "side", "signal", "entry", "pnl", "btc", "sett", "d", "vol90", "liq")} for c in allc])
    tdf.to_csv(D / "trades_V1_tutti_candidati.csv", index=False)
    pickle.dump(res, open(CACHE / "res.pkl", "wb"))
    (D / "out_run.txt").write_text("\n".join(L) + "\n"); print("\n".join(L))
