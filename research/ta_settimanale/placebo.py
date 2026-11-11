"""Placebo per le regole autonome che superano il buy & hold nei 3 periodi: stato slittato circolarmente (≥ 26 settimane), 300 prove."""
import numpy as np, pandas as pd, lib
f, fl = lib.load(); w, d, mo = lib.indicators(fl)
c = w["wclose"]; ms = w["macd"] > w["sig"]; fab = w["m_close"] > w["m_sma10"]
R = {"T1 long": (c > w["sma200"]) & ms, "T2 long": (c > w["ema200"]) & ms, "T4m long": fab & ms}
rng = np.random.default_rng(3); out = []
for nm, s in R.items():
    s = s[s.index >= "2020-12-20"].astype(float)
    m0 = lib.met(lib.sim_state(fl, s))
    sim = []
    for k in rng.integers(26, len(s) - 26, 300):
        m = lib.met(lib.sim_state(fl, pd.Series(np.roll(s.to_numpy(), k), s.index)))
        sim.append((m["mar"], m["ret"]))
    sim = np.array(sim)
    out.append(f"{nm}: MAR {m0['mar']} rend {m0['ret']}% · placebo mediana MAR {np.median(sim[:,0]):.2f} rend {np.median(sim[:,1]):.0f}% · p(MAR≥regola) {np.mean(sim[:,0] >= m0['mar']):.3f} · p(rend≥regola) {np.mean(sim[:,1] >= m0['ret']):.3f}")
print("\n".join(out)); (lib.HERE / "placebo.txt").write_text("\n".join(out))
