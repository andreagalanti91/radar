"""w32_multi: W3.2 (radar/weekly.py, stessi parametri di BTC) su ETH, SOL e 8 indici. PREREG.md (commit b99fe66). Non modifica radar/."""
import importlib.util, sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; D = HERE / "data"
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "multi_asset"))
from radar import weekly as W  # noqa: E402
import ma_lib as M  # noqa: E402
spec = importlib.util.spec_from_file_location("t10", ROOT / "research" / "top10_w3" / "run.py"); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
CEND, IEND = "2026-11-10", "2026-11-20"
IDX = {"SPX": "S&P 500", "NDX": "Nasdaq 100", "DJI": "Dow Jones", "DAX": "DAX", "FTSEMIB": "FTSE MIB", "N225": "Nikkei 225",
       "RUT": "Russell 2000", "SX5E": "Euro Stoxx 50"}

def setp(r=0.25, k=2.5): W.R_LONG = W.R_SHORT = r; W.STOP_K = W.TRAIL_K = k

def met(eq, trades, opn=None):
    tr = list(trades) + ([opn] if opn else []); pn = np.array([t["pnl"] for t in tr]) if tr else np.zeros(0)
    e = eq.dropna(); yrs = (e.index[-1] - e.index[0]).days / 365.25; fin = float(e.iloc[-1])
    dd = float((e / e.cummax() - 1).min()); cg = (fin / 10000) ** (1 / yrs) - 1
    wo = 10000 * np.prod(1 + np.delete(pn, pn.argmax())) if len(pn) else 10000.0
    return dict(fin=round(fin), cagr=round(cg * 100, 1), dd=round(dd * 100, 1), n=len(pn), wr=round(float((pn > 0).mean() * 100)) if len(pn) else None,
                cd=round(cg / abs(dd), 2) if dd < 0 else None, wo=round(wo), ret=round((fin / 10000 - 1) * 100, 1))

def bh(f, s, e, c):
    x = f[(f.index >= pd.Timestamp(s)) & (f.index <= pd.Timestamp(e))]
    eq = x["close"] / (x["open"].iloc[0] * (1 + c)) * (1 - c) * 10000
    return met(eq, [])

def full(f, s, e, r=0.25, k=2.5):          # W3.2 completa (radar.weekly.simulate)
    setp(r, k); g = f[f.index <= pd.Timestamp(e)]; o = W.simulate(g, start=s); setp()
    opn = dict(o["open"], pnl=o["open"]["pnl_close"]) if o["open"] else None
    return met(o["equity"], o["trades"], opn)

def po(f, s, e, crypto, r=0.25, k=2.5):     # W3.2 solo prezzo (ma_lib.s1_sim)
    kw = dict(fee=0.002, short_cost=0.10, wb=M.s1_weekly(f[f.index <= pd.Timestamp(e)], "W-SUN")) if crypto else dict(fee=M.FEE, short_cost=M.SHORT_COST)
    o = M.s1_sim(f, s, e, risk=r, k=k, **kw)
    return met(o["equity"], o["trades"], o["open"])

def halves(fn, f, s, e):
    return [fn(f, s, "2023-12-31")["ret"], fn(f, "2024-01-01", e)["ret"]]

def verdict(m, b, h, crypto_fn=None):
    c = dict(c1=(m["cd"] or -9) > (b["cd"] or -9), c2=m["dd"] >= -35, c3=(m["wr"] or 0) >= 60, c4=min(h) > 0, c5=m["n"] >= 8)
    return c, all(c.values())

rows = []
def add(asset, version, period, m, b, h=None, crit=None):
    rows.append(dict(asset=asset, versione=version, periodo=period, **m, bh_fin=b["fin"], bh_dd=b["dd"], bh_cd=b["cd"],
                     meta1=h[0] if h else None, meta2=h[1] if h else None, **(crit or {})))
    print(rows[-1], flush=True)

if __name__ == "__main__":
    # BTC di riferimento (dati top10_w3 = repo)
    fb, sb = T.feats("BTC"); fbl = pd.read_csv(D / "BTC_spot_long.csv.gz", index_col=0, parse_dates=True)
    for r in (0.25, 0.10):
        add("BTC", f"W3.2 completa r{r}", "2021", full(fb, "2021-01-01", CEND, r), bh(fb, "2021-01-01", CEND, 0.002))
    add("BTC", "solo prezzo r0.25", "2021", po(fbl, "2021-01-01", CEND, True), bh(fbl, "2021-01-01", CEND, 0.002))
    add("BTC", "solo prezzo r0.25", "2018", po(fbl, "2018-01-01", CEND, True), bh(fbl, "2018-01-01", CEND, 0.002))
    # ETH e SOL: completa (flusso perp e funding Binance)
    for a in ("ETH", "SOL"):
        f, st = T.feats(a); S = str(st.date())
        first = str((f["pf14z"].first_valid_index() + pd.Timedelta(days=200)).date())
        for r in (0.25, 0.10):
            m = full(f, S, CEND, r); b = bh(f, S, CEND, 0.002); h = halves(lambda g, x, y: full(g, x, y, r), f, S, CEND)
            c, ok = verdict(m, b, h)
            extra = {}
            if r == 0.25:
                extra = dict(**c, passa=ok, k2=full(f, S, CEND, r, 2.0)["cd"], k3=full(f, S, CEND, r, 3.0)["cd"])
            add(a, f"W3.2 completa r{r}", S[:4] if a == "ETH" else S, m, b, h, extra)
            if first < S:
                add(a, f"W3.2 completa r{r}", f"dal {first}", full(f, first, CEND, r), bh(f, first, CEND, 0.002))
        fl = pd.read_csv(D / "ETH_spot_long.csv.gz", index_col=0, parse_dates=True) if a == "ETH" else f
        for r in (0.25, 0.10):
            for P in (("2018-01-01", "2021-01-01") if a == "ETH" else (S,)):
                add(a, f"solo prezzo r{r}", P[:4], po(fl, P, CEND, True, r), bh(fl, P, CEND, 0.002))
    # Indici: solo prezzo
    for a in IDX:
        p = (ROOT / "research/multi_asset/data/SPX.csv.gz") if a == "SPX" else D / f"{a}.csv.gz"
        f = pd.read_csv(p, index_col=0, parse_dates=True); f = f[f.index <= IEND][["open", "high", "low", "close"]]
        for r in (0.25, 0.10):
            for P in ("2021-01-01", "2018-01-01"):
                m = po(f, P, IEND, False, r); b = bh(f, P, IEND, M.FEE)
                h, extra = None, {}
                if P == "2021-01-01":
                    h = halves(lambda g, x, y: po(g, x, y, False, r), f, P, IEND)
                    if r == 0.25:
                        c, ok = verdict(m, b, h)
                        extra = dict(**c, passa=ok, k2=po(f, P, IEND, False, r, 2.0)["cd"], k3=po(f, P, IEND, False, r, 3.0)["cd"])
                add(IDX[a], f"solo prezzo r{r}", P[:4], m, b, h, extra)
    pd.DataFrame(rows).to_csv(HERE / "risultati.csv", index=False)
