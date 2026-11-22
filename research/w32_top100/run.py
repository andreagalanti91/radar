"""w32_top100: W3.2 (radar/weekly.py invariato, R 0,25, parametri di BTC) sulle top 100 crypto. PREREG.md (commit 866f3eb).
Stesse funzioni di research/w32_multi/run.py (met, bh, full, po, verdict); placebo come w32_multi/placebo.py."""
import importlib.util, sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; D = HERE / "data"
spec = importlib.util.spec_from_file_location("w32m", ROOT / "research" / "w32_multi" / "run.py"); R = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / "research" / "w32_multi")); spec.loader.exec_module(R)
W, M, T, met, bh, full, po, setp = R.W, R.M, R.T, R.met, R.bh, R.full, R.po, R.setp
END = "2026-11-10"; EVAL_MAX = "2023-11-10"
CUT_END = {"TON": "2026-06-22"}  # TON delistato da Binance a fine 06/2026: perp fermo a prezzo costante fino al 10/11
CUT = {"LIT": "2025-12-23"}   # LITUSDT fino al 2025 = Litentry (altra moneta, prezzo fermo dal 02/2025); Lighter dal 23/12/2025

def rd(t, k):
    p = D / f"{t}_{k}.csv.gz"
    return pd.read_csv(p, index_col=0, parse_dates=True) if p.exists() else None

def feats(t):                                   # = top10_w3/run.py feats, con spot opzionale (prezzo dal perp)
    sp, pp, fu = rd(t, "spot"), rd(t, "perp"), rd(t, "funding")
    fu = fu["funding"] if fu is not None else pd.Series(dtype=float)
    if t in CUT: sp, pp, fu = (None if x is None else x[x.index >= CUT[t]] for x in (sp, pp, fu)); sp = sp if sp is not None and len(sp) else None
    idx = pd.date_range(min(x.index[0] for x in (sp, pp) if x is not None), END)
    px = pp[["open", "high", "low", "close"]].reindex(idx)
    if sp is not None: px = sp[["open", "high", "low", "close"]].reindex(idx).combine_first(px)
    f = px.copy(); pp = pp.reindex(idx)
    d = 2 * pp["tbv"] - pp["volume"]
    f["pf14z"] = T.z(d.rolling(14).sum() / pp["volume"].rolling(14).sum(), 180)
    f["funding"] = fu.reindex(idx).ffill(limit=3)
    f = f[f["close"].notna()]
    if t in CUT_END: f = f[f.index <= CUT_END[t]]
    st = max(pd.Timestamp("2021-01-01"), f["pf14z"].first_valid_index() + pd.Timedelta(days=200))
    return f, st

def sim(f, s, e=END, r=0.25, k=2.5):
    setp(r, k); o = W.simulate(f[f.index <= pd.Timestamp(e)], start=s); setp(); return o

def halves(fn, S):
    if S <= "2022-12-31": return [(S, "2023-12-31"), ("2024-01-01", END)]
    mid = pd.Timestamp(S) + (pd.Timestamp(END) - pd.Timestamp(S)) / 2
    return [(S, str(mid.date())), (str((mid + pd.Timedelta(days=1)).date()), END)]

def placebo(f, S, o, n_iter=2000):               # w32_multi/placebo.py senza la variabile globale
    g = f[f.index <= END]; st = pd.Timestamp(S)
    tr = o["trades"] + ([o["open"]] if o["open"] else [])
    r = g["close"].pct_change().loc[st:].fillna(0).to_numpy(); n = len(r); idx = g.loc[st:].index
    spec = [((pd.Timestamp(t.get("exit") or idx[-1]) - pd.Timestamp(t["entry"])).days, 1 if t["side"] == "long" else -1, t["expo"]) for t in tr]
    def run(starts, sp):
        m = np.zeros(n)
        for s0, (d, sd, ex) in zip(starts, sp): m[s0:s0 + d] = sd * ex
        e = np.cumprod(1 + m * r) * (1 - 0.003) ** len(sp)
        return (e[-1] ** (365.25 / n) - 1) / abs((e / np.maximum.accumulate(e) - 1).min())
    act = run([idx.searchsorted(pd.Timestamp(t["entry"])) for t in tr], spec)
    rng = np.random.default_rng(7); Dd = sum(s[0] for s in spec); out = []
    for _ in range(n_iter):
        order = rng.permutation(len(spec)); gaps = np.diff(np.sort(np.r_[0, rng.integers(0, n - Dd, len(spec)), n - Dd]))[:-1]
        sp = [spec[i] for i in order]; starts, c = [], 0
        for gp, s in zip(gaps, sp): c += gp; starts.append(c); c += s[0]
        out.append(run(starts, sp))
    out = np.array(out); return round(act, 2), round(float(np.median(out)), 2), (int((out >= act).sum()) + 1) / (n_iter + 1)

def holm(ps, a=0.05):
    order = sorted(ps, key=ps.get); ok, m = {}, len(ps); stop = False
    for i, k in enumerate(order):
        stop = stop or ps[k] > a / (m - i); ok[k] = not stop
    return ok

if __name__ == "__main__":
    u = pd.read_csv(HERE / "universe.csv"); u = u[u.escluso.isna()]
    rows, EQ, EQB = [], {}, {}
    for x in u.itertuples():
        t = x.ticker; row = dict(rank=x.rank, sym=x.symbol)
        if isinstance(x.perp, str) and rd(t, "perp") is not None:
            f, st = feats(t); S = str(st.date())
            if st > f.index[-1] - pd.Timedelta(days=180):
                row.update(versione="completa", inizio=S, valutabile=False, nota="< 180 g di test"); rows.append(row); print(row); continue
            o = sim(f, S)
            opn = dict(o["open"], pnl=o["open"]["pnl_close"]) if o["open"] else None
            m = met(o["equity"], o["trades"], opn); b = bh(f, S, END, 0.002)
            hs = [met(*(lambda q: (q["equity"], q["trades"], dict(q["open"], pnl=q["open"]["pnl_close"]) if q["open"] else None))(sim(f, a, e)))["ret"]
                  for a, e in halves(None, S)]
            c = dict(c1=(m["cd"] or -9) > (b["cd"] or -9), c2=m["dd"] >= -35, c3=(m["wr"] or 0) >= 60, c4=min(hs) > 0, c5=m["n"] >= 8)
            row.update(versione="completa", inizio=S, valutabile=S <= EVAL_MAX, **m, bh_fin=b["fin"], bh_dd=b["dd"], bh_cd=b["cd"],
                       meta1=hs[0], meta2=hs[1], **c, passa15=all(c.values()))
            EQ[x.symbol] = o["equity"].dropna(); bx = f[(f.index >= st) & (f.index <= END)]
            EQB[x.symbol] = bx["close"] / (bx["open"].iloc[0] * 1.002) * 0.998 * 10000
            if row["passa15"] and row["valutabile"]:
                k2, k3 = met(sim(f, S, k=2.0)["equity"], []), met(sim(f, S, k=3.0)["equity"], [])
                pa, pm, pp_ = placebo(f, S, o)
                row.update(k2=k2["cd"], k3=k3["cd"], conferma=(m["wo"] > 10000) and max(k2["cd"] or -9, k3["cd"] or -9) > b["cd"],
                           plac_act=pa, plac_med=pm, p=round(pp_, 4))
        elif x.spot == True and rd(t, "spot") is not None:
            f = rd(t, "spot")[["open", "high", "low", "close"]]; f = f[f.index <= END]
            S = str(max(pd.Timestamp("2021-01-01"), f.index[0] + pd.Timedelta(days=300)).date())
            m = po(f, S, END, True); b = bh(f, S, END, 0.002); hs = [po(f, a, e, True)["ret"] for a, e in halves(None, S)]
            c = dict(c1=(m["cd"] or -9) > (b["cd"] or -9), c2=m["dd"] >= -35, c3=(m["wr"] or 0) >= 60, c4=min(hs) > 0, c5=m["n"] >= 8)
            row.update(versione="solo prezzo", inizio=S, valutabile=S <= EVAL_MAX, **m, bh_fin=b["fin"], bh_dd=b["dd"], bh_cd=b["cd"],
                       meta1=hs[0], meta2=hs[1], **c, passa15=all(c.values()))
        else:
            row.update(versione="nessun dato Binance")
        rows.append(row); print(row, flush=True)
    d = pd.DataFrame(rows)
    pas = d[(d.versione == "completa") & d.valutabile.fillna(False) & d.passa15.fillna(False)]
    hk = holm(dict(zip(pas.sym, pas.p))) if len(pas) else {}
    d["holm"] = d.sym.map(hk); d["passa_davvero"] = d.passa15.fillna(False) & d.conferma.fillna(False) & d.holm.fillna(False)
    d.to_csv(HERE / "risultati.csv", index=False)
    # portafogli equipesati dal 01/01/2021 (quote indipendenti, liquidità prima dell'inizio)
    idx = pd.date_range("2021-01-01", END)
    def port(E, names):
        if not names: return None
        tot = sum((E[n] / 10000).reindex(idx).ffill().fillna(1.0) for n in names) / len(names) * 10000
        yrs = (idx[-1] - idx[0]).days / 365.25; dd = float((tot / tot.cummax() - 1).min()); cg = (tot.iloc[-1] / 10000) ** (1 / yrs) - 1
        h = [f"{(q.iloc[-1] / q.iloc[0] - 1) * 100:.0f}%" for q in (tot[:"2023-12-31"], tot["2024-01-01":])]
        return dict(n=len(names), fin=round(float(tot.iloc[-1])), cagr=round(cg * 100, 1), dd=round(dd * 100, 1), cd=round(cg / abs(dd), 2), h1=h[0], h2=h[1])
    ev = list(d[(d.versione == "completa") & d.valutabile.fillna(False)].sym); evalt = [s for s in ev if s != "BTC"]
    sel = list(d[d.passa_davvero].sym); sel15 = list(pas.sym)
    P = {"W3.2 solo BTC": port(EQ, ["BTC"]), "B&H solo BTC": port(EQB, ["BTC"]),
         "(a) W3.2 EW valutabili": port(EQ, ev), "B&H EW valutabili": port(EQB, ev),
         "(a') W3.2 EW altcoin valutabili": port(EQ, evalt), "B&H EW altcoin valutabili": port(EQB, evalt),
         "(b) W3.2 EW passano 1-5 [a posteriori]": port(EQ, sel15), "B&H EW passano 1-5": port(EQB, sel15),
         "(b') W3.2 EW passano davvero [a posteriori]": port(EQ, sel), "B&H EW passano davvero": port(EQB, sel)}
    for k, v in P.items(): print(k, v)
    pd.DataFrame({k: v for k, v in P.items() if v}).T.to_csv(HERE / "portafogli.csv")
