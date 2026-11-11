import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "w2_migliorie"))
from eng import simulate, metrics, bh, load_repo  # noqa
import numpy as np, pandas as pd
D = HERE / "data"; END = "2026-11-10"
ASSETS = "BTC ETH BNB XRP SOL TRX HYPE ZEC XMR DOGE".split()
cap = lambda wk, d: min(1.0, 0.25 / (2.5 * wk["atr"] / wk["close"]))

def z(s, n): return (s - s.rolling(n, min_periods=n // 2).mean()) / s.rolling(n, min_periods=n // 2).std()

def feats(s):
    sp = pd.read_csv(D / f"{s}_spot.csv", index_col=0, parse_dates=True)
    pp = pd.read_csv(D / f"{s}_perp.csv", index_col=0, parse_dates=True)
    fu = pd.read_csv(D / f"{s}_funding.csv", index_col=0, parse_dates=True)["funding"]
    idx = pd.date_range(min(sp.index[0], pp.index[0]), END)
    px = sp[["open", "high", "low", "close"]].reindex(idx).combine_first(pp[["open", "high", "low", "close"]].reindex(idx))
    f = px.copy(); pp = pp.reindex(idx)
    d = 2 * pp["tbv"] - pp["volume"]
    f["pf14z"] = z(d.rolling(14).sum() / pp["volume"].rolling(14).sum(), 180)
    f["funding"] = fu.reindex(idx).ffill(limit=3)
    f = f[f["close"].notna()]
    st = max(pd.Timestamp("2021-01-01"), f["pf14z"].first_valid_index() + pd.Timedelta(days=200))
    return f, st

def w3f(f): g = f.copy(); g["pf14z"] = f["pf14z"].rolling(3).mean().shift(1); return g
def W3(f, s, e=None, **k): return simulate(w3f(f), start=s, end=e, anchor="SUN", ratchet=True, lev_fn=cap, **k)
def W2(f, s, e=None, **k): return simulate(f, start=s, end=e, anchor="SUN", **k)

def tim(r):
    e = r["equity"]; days = 0
    for t in r["trades"]:
        a = pd.Timestamp(t["entry"]); b = pd.Timestamp(t["exit"]) if t["exit"] else e.index[-1]
        days += (b - a).days
    return 100 * days / max(1, (e.index[-1] - e.index[0]).days)

def mstr(r):
    m = metrics(r); return dict(fin=round(m["final"]), ret=round(m["ret"]), dd=round(m["dd"], 1), n=m["n"],
                                wr=round(m["wr"]) if m["n"] else None, mar=round(m["mar"], 2), wo=round(m["final_wo"]))

def bhe(f, s, e=None):
    x = f[(f.index >= pd.Timestamp(s))]; x = x[x.index <= pd.Timestamp(e)] if e else x
    return x["close"] / (x["open"].iloc[0] * 1.001) * 0.999 * 10000

if __name__ == "__main__":
    # verifica BTC contro i dati del repo
    rep = load_repo(); fb, _ = feats("BTC")
    print("verifica W2 BTC repo", mstr(W2(rep, "2021-01-01", END)), "| nostri dati", mstr(W2(fb, "2021-01-01", END)))
    print("verifica W3 BTC repo", mstr(W3(rep, "2021-01-01", END)), "| nostri dati", mstr(W3(fb, "2021-01-01", END)))
    rows, EQ, EQB, HALF = [], {}, {}, {}
    for s in ASSETS:
        f, st = feats(s); S = str(st.date())
        r3, r2 = W3(f, S, END), W2(f, S, END); b = bh(f, S, END)
        EQ[s], EQB[s] = r3["equity"], bhe(f, S, END)
        row = dict(asset=s, start=S, **{f"W3_{k}": v for k, v in mstr(r3).items()}, W3_tim=round(tim(r3)),
                   **{f"W2_{k}": v for k, v in mstr(r2).items()},
                   BH_fin=round(b["final"]), BH_dd=round(b["dd"], 1), BH_mar=round(b["mar"], 2))
        for nm, a, e in (("h1", S, "2023-12-31"), ("h2", max(S, "2024-01-01"), END)):
            if pd.Timestamp(e) - pd.Timestamp(a) < pd.Timedelta(days=180): row[f"{nm}"] = "n/d"; continue
            m3, m2, mb = mstr(W3(f, a, e)), mstr(W2(f, a, e)), bh(f, a, e)
            row[nm] = f"W3 {m3['ret']}%/{m3['dd']} MAR{m3['mar']} | W2 {m2['ret']}%/{m2['dd']} | BH {mb['ret']:.0f}%/{mb['dd']:.1f} MAR{mb['mar']:.2f}"
            row[f"{nm}_beat"] = m3["mar"] > mb["mar"]
        for k in (2.0, 3.0):
            row[f"W3_tr{k}"] = round(metrics(W3(f, S, END, stop=k, trail=k))["final"])
        rows.append(row); print(row, flush=True)
    d = pd.DataFrame(rows); d.to_csv(HERE / "per_asset.csv", index=False)
    idx = pd.date_range("2021-01-01", END)
    def port(E, names, w=None):
        w = w or {n: 1 / len(names) for n in names}
        tot = sum((E[n] / 10000).reindex(idx).bfill().fillna(1.0).ffill() * w[n] for n in names) * 10000
        yrs = (idx[-1] - idx[0]).days / 365.25; dd = float((tot / tot.cummax() - 1).min()); cg = (tot.iloc[-1] / 10000) ** (1 / yrs) - 1
        out = dict(fin=round(float(tot.iloc[-1])), dd=round(dd * 100, 1), cagr=round(cg * 100, 1), mar=round(cg / abs(dd), 2))
        for nm, a, b in (("h1", "2021-01-01", "2023-12-31"), ("h2", "2024-01-01", END)):
            q = tot[a:b]; out[nm] = f"{(q.iloc[-1] / q.iloc[0] - 1) * 100:.0f}% DD{(q / q.cummax() - 1).min() * 100:.1f}"
        return out
    sel = ["BTC"] + [s for s in ASSETS[1:] if d.set_index("asset").loc[s].get("h1_beat") == True and d.set_index("asset").loc[s].get("h2_beat") == True]
    P = {"(i) W3 solo BTC": port(EQ, ["BTC"]), "(ii) W3 EW 10": port(EQ, ASSETS), f"(iii) W3 BTC+{'/'.join(sel[1:]) or 'nessuno'} [selezione]": port(EQ, sel),
         "(iv) B&H EW 10": port(EQB, ASSETS), "B&H solo BTC": port(EQB, ["BTC"]), "W3 EW 9 senza BTC": port(EQ, ASSETS[1:])}
    for s in ASSETS[1:]: P[f"W3 50/50 BTC+{s}"] = port(EQ, ["BTC", s])
    for k, v in P.items(): print(k, v)
    pd.DataFrame(P).T.to_csv(HERE / "portafogli.csv")
