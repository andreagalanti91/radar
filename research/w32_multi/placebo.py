"""Placebo per ETH (unico asset che passa 1-5): stessi trade (durata, lato, esposizione) in date casuali non sovrapposte, 2000 prove."""
import numpy as np, pandas as pd
from run import T, W, CEND
f, st = T.feats("ETH"); g = f[f.index <= CEND]; o = W.simulate(g, start=str(st.date()))
tr = o["trades"] + ([o["open"]] if o["open"] else [])
r = g["close"].pct_change().loc[st:].fillna(0).to_numpy(); n = len(r); idx = g.loc[st:].index
spec = [((pd.Timestamp(t.get("exit") or idx[-1]) - pd.Timestamp(t["entry"])).days, 1 if t["side"] == "long" else -1, t["expo"]) for t in tr]
def run(starts):
    m = np.zeros(n)
    for s0, (d, sd, ex) in zip(starts, spec): m[s0:s0 + d] = sd * ex
    e = np.cumprod(1 + m * r) * (1 - 0.003) ** len(spec); yrs = n / 365.25
    return ((e[-1]) ** (1 / yrs) - 1) / abs((e / np.maximum.accumulate(e) - 1).min())
pos = [idx.searchsorted(pd.Timestamp(t["entry"])) for t in tr]; act = run(pos)
rng = np.random.default_rng(7); D = sum(s[0] for s in spec); out = []
for _ in range(2000):
    order = rng.permutation(len(spec)); gaps = np.diff(np.sort(np.r_[0, rng.integers(0, n - D, len(spec)), n - D]))[:-1]
    sp = [spec[i] for i in order]; starts, c = [], 0
    for gp, s in zip(gaps, sp): c += gp; starts.append(c); c += s[0]
    globals()["spec_backup"] = spec; spec_o = spec; spec = sp; out.append(run(starts)); spec = spec_o
out = np.array(out); print(f"ETH CAGR/DD reale (motore semplice) {act:.2f}; placebo mediana {np.median(out):.2f}, 95° {np.quantile(out,.95):.2f}; p = {(out >= act).mean():.4f}")
