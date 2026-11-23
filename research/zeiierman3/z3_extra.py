"""zeiierman3 · complemento descrittivo: attraversamenti di −90 (tz 1D) secondo lo stato di W3.2 e confronto con giorni casuali."""
import numpy as np, pandas as pd
import z3_lib as Z, z3_w32 as V
d, a = Z.load(); ev = pd.read_csv(Z.HERE / "eventi_1d.csv", parse_dates=["data"]); ev = ev[ev.linea_ind == "tz"]
f, fl = V.frames(); st = pd.Series(0, d.index)
for fr, s, e in ((fl, "2018-01-01", "2020-12-31"), (f, "2021-01-01", "2026-11-15")):
    r = V.simulate(fr, s, e)
    for t in r["trades"] + ([dict(r["open"], exit=e)] if r["open"] else []):
        st.loc[t["entry"]:pd.Timestamp(t["exit"]) - pd.Timedelta(days=1)] = t["side"]
st.loc["2026-11-16":] = -1
ev["W32"] = st.reindex(ev.data + pd.Timedelta(days=1)).map({1: "long", -1: "short", 0: "flat"}).to_numpy()
out = []
g = ev.groupby(["evento", "W32"]).agg(n=("r30", "size"), r7=("r7", "mean"), r30=("r30", "mean"), r60=("r60", "mean"),
                                      min60_med=("min60", "median")).round(1)
out.append(g.to_string())
# giorni casuali: probabilità che 22 giorni presi a caso dal 2018 abbiano media a 30/60 giorni >= quella osservata
C, O = d.close.to_numpy(), d.open.to_numpy(); i0 = d.index.searchsorted(pd.Timestamp("2018-01-01")); rng = np.random.default_rng(1)
for k in ("scende sotto -90", "sale sopra -20", "risale sopra -90"):
    e_ = ev[ev.evento == k]
    for h in (30, 60):
        obs = e_[f"r{h}"].dropna(); n = len(obs)
        pool = np.arange(i0, len(C) - h - 1); rr = C[pool + h] / O[pool + 1] - 1
        sims = np.array([rr[rng.integers(0, len(rr), n)].mean() for _ in range(5000)]) * 100
        out.append(f"{k} r{h}: media {obs.mean():.1f} (n {n}), giorni casuali mediana {np.median(sims):.1f}, p(≥) {(sims >= obs.mean()).mean():.3f}")
open(Z.HERE / "descrittivo_extra.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))
