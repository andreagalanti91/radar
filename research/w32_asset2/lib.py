"""w32_asset2 · libreria comune del ciclo 2 (PREREG.md, commit f40f7a6). Non modifica radar/, i dati o il PREREG.

Crypto: radar.weekly.simulate (W3.2, R 0,25, trailing 2,5 ATRw), feats() di crypto/counts.py (storia dal 2019-09-01, fine =
ultimo giorno del perp), test dal giorno "completa_da" di crypto/universe.csv. Azioni: ma_lib.s1_sim (W-FRI, 0,05%/lato,
short 3% annuo), filtro di flusso come azioni/count.py (long solo se flusso > 0, short solo se < 0).
Metriche = w32_multi/run.py met/bh; placebo = w32_multi/placebo.py (2.000 prove, seme 7) con le durate in sedute dell'indice
(per le crypto coincide con i giorni di calendario; per le azioni evita di contare i giorni di borsa chiusa)."""
from __future__ import annotations
import importlib.util, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "multi_asset")); sys.path.insert(0, str(HERE / "azioni"))
from radar import weekly as W  # noqa: E402
import ma_lib as M  # noqa: E402
import flow as FL  # noqa: E402

def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
C = _load("w32a2_counts", HERE / "crypto" / "counts.py")

CEND = "2026-11-24"; IS_END = "2022-12-31"; OOS_START = "2023-01-01"; HALF_IF_AFTER = "2022-06-30"
CU = pd.read_csv(HERE / "crypto" / "universe.csv")
AU = pd.read_csv(HERE / "azioni" / "universe.csv")
FLOWS = ["cmf20", "cmf_w4", "obv_slope20", "obv_chg20", "ad_slope20"]

# ------------------------------------------------------------------ metriche (= w32_multi/run.py)
def met(eq, trades, opn=None):
    tr = list(trades) + ([opn] if opn else []); pn = np.array([t["pnl"] for t in tr]) if tr else np.zeros(0)
    e = eq.dropna(); yrs = (e.index[-1] - e.index[0]).days / 365.25; fin = float(e.iloc[-1])
    dd = float((e / e.cummax() - 1).min()); cg = (fin / 10000) ** (1 / yrs) - 1 if yrs > 0 else 0.0
    wo = 10000 * np.prod(1 + np.delete(pn, pn.argmax())) if len(pn) else 10000.0
    return dict(fin=round(fin), cagr=round(cg * 100, 1), dd=round(dd * 100, 1), n=len(pn),
                wr=round(float((pn > 0).mean() * 100)) if len(pn) else None,
                cd=round(cg / abs(dd), 2) if dd < 0 else None, wo=round(wo), ret=round((fin / 10000 - 1) * 100, 1),
                cd_raw=cg / abs(dd) if dd < 0 else None)

def bh(f, s, e, c):
    x = f[(f.index >= pd.Timestamp(s)) & (f.index <= pd.Timestamp(e))]
    return met(x["close"] / (x["open"].iloc[0] * (1 + c)) * (1 - c) * 10000, [])

def bh_curve(f, s, e, c):
    x = f[(f.index >= pd.Timestamp(s)) & (f.index <= pd.Timestamp(e))]
    return x["close"] / (x["open"].iloc[0] * (1 + c)) * (1 - c) * 10000

def periods(S, E):
    """IS/OOS del PREREG; se IS o OOS sono più corti di 6 mesi (inizio dopo il 30/06/2022 o serie finita prima del 30/06/2023)
    si usano le due metà del periodo (come w32_top100)."""
    if S <= HALF_IF_AFTER and E >= "2023-06-30": return [(S, IS_END), (OOS_START, E)], "IS/OOS"
    mid = pd.Timestamp(S) + (pd.Timestamp(E) - pd.Timestamp(S)) / 2
    return [(S, str(mid.date())), (str((mid + pd.Timedelta(days=1)).date()), E)], "metà"

def holm(ps, a=0.05):
    order = sorted(ps, key=ps.get); ok, m = {}, len(ps); stop = False
    for i, k in enumerate(order):
        stop = stop or ps[k] > a / (m - i); ok[k] = not stop
    return ok

# ------------------------------------------------------------------ placebo (= w32_multi/placebo.py, durate in sedute)
def placebo(close, S, E, trades, n_iter=2000, seed=7):
    g = close[(close.index >= pd.Timestamp(S)) & (close.index <= pd.Timestamp(E))]
    r = g.pct_change().fillna(0).to_numpy(); n = len(r); idx = g.index
    if not trades or n < 30: return None, None, 1.0
    yrs = (idx[-1] - idx[0]).days / 365.25
    spec, pos = [], []
    for t in trades:
        a = idx.searchsorted(pd.Timestamp(t["entry"])); b = idx.searchsorted(pd.Timestamp(t["exit"])) if t.get("exit") else n
        spec.append((max(b - a, 0), 1 if t["side"] == "long" else -1, t["expo"])); pos.append(a)
    def run(starts, sp):
        m = np.zeros(n)
        for s0, (d, sd, ex) in zip(starts, sp): m[s0:s0 + d] = sd * ex
        e = np.cumprod(1 + m * r) * (1 - 0.003) ** len(sp); dd = abs((e / np.maximum.accumulate(e) - 1).min())
        return (e[-1] ** (1 / yrs) - 1) / dd if dd > 0 else 0.0
    act = run(pos, spec); rng = np.random.default_rng(seed); Dd = sum(s[0] for s in spec); out = []
    if Dd >= n: return round(act, 2), None, 1.0
    for _ in range(n_iter):
        order = rng.permutation(len(spec)); gaps = np.diff(np.sort(np.r_[0, rng.integers(0, n - Dd, len(spec)), n - Dd]))[:-1]
        sp = [spec[i] for i in order]; starts, c = [], 0
        for gp, s in zip(gaps, sp): c += gp; starts.append(c); c += s[0]
        out.append(run(starts, sp))
    out = np.array(out); return round(act, 2), round(float(np.median(out)), 2), (int((out >= act).sum()) + 1) / (n_iter + 1)

# ------------------------------------------------------------------ crypto
def cfeats(t):
    return C.feats(t)

def setp(eng, r=0.25, k=2.5):
    eng.R_LONG = eng.R_SHORT = r; eng.STOP_K = eng.TRAIL_K = k

def csim(f, s, e=CEND, r=0.25, k=2.5, gate=None, eng=W):
    """W3.2 completa. gate: Serie (domeniche) +1/-1/0: ingresso consentito solo nello stesso verso (Q4)."""
    setp(eng, r, k); orig = eng.weekly_bars
    if gate is not None:
        def wb(ff, _o=orig):
            w = _o(ff); g = gate.reindex(w.index).fillna(0)
            w["long"] = w["long"] & (g > 0); w["short"] = w["short"] & (g < 0); return w
        eng.weekly_bars = wb
    try:
        o = eng.simulate(f[f.index <= pd.Timestamp(e)], start=s)
    finally:
        eng.weekly_bars = orig; setp(eng)
    return o

def omet(o):
    opn = dict(o["open"], pnl=o["open"]["pnl_close"]) if o["open"] else None
    return met(o["equity"], o["trades"], opn)

def otrades(o):
    return o["trades"] + ([dict(o["open"], pnl=o["open"]["pnl_close"])] if o["open"] else [])

def crit(m, b, hs):
    return dict(c1=(m["cd"] if m["cd"] is not None else -9) > (b["cd"] if b["cd"] is not None else -9), c2=m["dd"] >= -35,
                c3=(m["wr"] or 0) >= 60, c4=min(hs) > 0, c5=m["n"] >= 8)

def failed(c):
    return ",".join(k[1] for k, v in c.items() if not v) or "–"

def eval_crypto(t, S, E=CEND, r=0.25, k=2.5, gate=None, eng=W, f=None, conf=True, plac=True, neigh_k=(2.0, 3.0)):
    f = cfeats(t) if f is None else f; E = min(pd.Timestamp(E), f.index[-1]); E = str(E.date())
    o = csim(f, S, E, r, k, gate, eng); m = omet(o); b = bh(f, S, E, 0.002)
    ps, kind = periods(S, E); hs = [omet(csim(f, a, e, r, k, gate, eng))["ret"] for a, e in ps]
    c = crit(m, b, hs); row = dict(inizio=S, fine=E, **m, bh_fin=b["fin"], bh_dd=b["dd"], bh_cd=b["cd"], bh_cagr=b["cagr"],
                                   is_ret=hs[0], oos_ret=hs[1], split=kind, **c, passa15=all(c.values()), falliti=failed(c))
    if conf:
        nk = [omet(csim(f, S, E, r, kk, gate, eng))["cd"] for kk in neigh_k]
        row.update(vicini_cd="/".join(str(x) for x in nk),
                   conferma=bool(m["wo"] > 10000 and sum((x if x is not None else -9) > (b["cd"] if b["cd"] is not None else -9) for x in nk) >= len(nk) / 2))
    if plac:
        pa, pm, p = placebo(f["close"], S, E, otrades(o)); row.update(plac_act=pa, plac_med=pm, p=round(p, 4))
    return row, o, f

# ------------------------------------------------------------------ azioni
def aload(sym):
    f = pd.read_csv(HERE / "azioni" / "data" / "px" / f"{sym}.csv.gz", index_col=0, parse_dates=True)
    return f[f["close"].notna()]

def astart(f):
    return str(max(pd.Timestamp("2020-01-01"), f.index[0] + pd.DateOffset(years=1)).date())

def with_flow(wb, fw, col):          # = azioni/count.py
    w = wb.copy()
    if col is None: return w
    x = fw[col].reindex(w.index)
    w["long"] = w["long"] & (x > 0).fillna(False); w["short"] = w["short"] & (x < 0).fillna(False); return w

def abars(f):
    fl = FL.daily(f); fw = FL.weekly(f, fl); wb = M.s1_weekly(f)
    return wb, fw

def asim(f, wb, fw, col, s, e, r=0.25, k=2.5):
    return M.s1_sim(f, s, e, risk=r, k=k, wb=with_flow(wb, fw, col))

def ametrics(o):
    return met(o["equity"], o["trades"], o["open"])

def eval_stock(sym, col, r=0.25, k=2.5, conf=True, plac=True, f=None, bars=None):
    f = aload(sym) if f is None else f; wb, fw = abars(f) if bars is None else bars
    S, E = astart(f), str(f.index[-1].date())
    o = asim(f, wb, fw, col, S, E, r, k); m = ametrics(o); b = bh(f, S, E, M.FEE)
    ps, kind = periods(S, E); hs = [ametrics(asim(f, wb, fw, col, a, e, r, k))["ret"] for a, e in ps]
    c = crit(m, b, hs); row = dict(inizio=S, fine=E, **m, bh_fin=b["fin"], bh_dd=b["dd"], bh_cd=b["cd"], bh_cagr=b["cagr"],
                                   is_ret=hs[0], oos_ret=hs[1], split=kind, **c, passa15=all(c.values()), falliti=failed(c))
    if conf:
        nb = [ametrics(asim(f, wb, fw, col, S, E, r, kk))["cd"] for kk in (2.0, 3.0)]
        if col == "cmf20": nb += [ametrics(asim(f, wb, fw, c2, S, E, r, k))["cd"] for c2 in FLOWS if c2 != "cmf20"]
        bc = b["cd"] if b["cd"] is not None else -9
        row.update(vicini_cd="/".join(str(x) for x in nb), conferma=bool(m["wo"] > 10000 and sum((x if x is not None else -9) > bc for x in nb) >= len(nb) / 2))
    if plac:
        tr = o["trades"] + ([o["open"]] if o["open"] else [])
        pa, pm, p = placebo(f["close"], S, E, tr); row.update(plac_act=pa, plac_med=pm, p=round(p, 4))
    return row, o, f

# ------------------------------------------------------------------ portafogli
def port(curves, start, end=CEND):
    """Capitali uguali e separati (quote indipendenti), liquidità prima dell'inizio / dopo la fine di ogni serie."""
    if not curves: return None, None
    idx = pd.date_range(start, end)
    tot = sum((c / 10000).reindex(idx).ffill().fillna(1.0) for c in curves) / len(curves) * 10000
    yrs = (idx[-1] - idx[0]).days / 365.25; dd = float((tot / tot.cummax() - 1).min()); cg = (tot.iloc[-1] / 10000) ** (1 / yrs) - 1
    return dict(n=len(curves), fin=round(float(tot.iloc[-1])), cagr=round(cg * 100, 1), dd=round(dd * 100, 1),
                cd=round(cg / abs(dd), 2) if dd < 0 else None), tot

def flag(x):
    return "sì" if x in (True, "True", "si", "sì") else "no"
