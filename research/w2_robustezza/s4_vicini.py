"""Punto 4 (vicini) + punto 1 (deflated Sharpe): un fattore o una coppia alla volta attorno alla config in uso."""
from lib import *
from scipy import stats as st
repo, long = load()
END0 = "2020-12-31"

def wsr(e):
    r = e.resample("W-SUN").last().pct_change().dropna()
    return r.mean() / r.std(), r

def one(tag, lab, **kw):
    r = run(repo, **kw); T = all_trades(r); s = stats(r["equity"], T); sr, _ = wsr(r["equity"])
    r0 = run(long, start="2018-01-01", end=END0, **kw); s0 = stats(r0["equity"], all_trades(r0))
    return dict(gruppo=tag, config=lab, **s, sr_w=round(sr, 4), **{k + "_1820": s0[k] for k in ("rend", "dd", "mar", "n")})

rows = []
for sma in (30, 35, 40, 45, 50):
    for ema in (15, 18, 20, 23, 26):
        rows.append(one("SMAxEMA", f"SMA{sma}/EMA{ema}", sma=sma, ema_t=ema, ema_x=ema + 1))
for k in (2.0, 2.5, 3.0, 3.5):
    rows.append(one("trailing", f"{k} ATR", trail=k, stop=k))
for m in ((6, 19, 4), (8, 21, 5), (10, 24, 7), (12, 26, 9)):
    for old in (12, 14, 16, 18, 20):
        rows.append(one("MACDxETA", f"MACD{m[0]}/{m[1]}/{m[2]} eta{old}", macd=m, old=old))
for thr in (-0.5, -0.25, 0.0, 0.25, 0.5):
    rows.append(one("flusso", f"soglia {thr:+.2f}", thr=thr))
rows.append(one("moduli", "senza F1", f1=False))
rows.append(one("moduli", "senza flusso", flow="none"))
rows.append(one("moduli", "senza flusso e F1", flow="none", f1=False))
df = pd.DataFrame(rows); df.to_csv(HERE / "s4_vicini.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(df.drop(columns=["calmar", "cagr"]).to_string(index=False))

base = df[df.config == "SMA40/EMA20"].iloc[0]
nb = df[(df.gruppo != "moduli")].drop_duplicates("config")
nb = nb[~nb.config.isin(["SMA40/EMA20", "2.5 ATR", "MACD8/21/5 eta16", "soglia +0.00"])]
print(f"\nBASE finale {base.finale} MAR {base.mar} | vicini n={len(nb)}")
for col in ("mar", "finale"):
    print(col, "mediana vicini", nb[col].median(), "min", nb[col].min(), "max", nb[col].max(),
          "| percentile della base", round((nb[col] < base[col]).mean() * 100), "| quota vicini >= meta' base", round((nb[col] >= base[col] / 2).mean() * 100))
print("DD vicini: mediana", nb.dd.median(), "peggiore", nb.dd.min(), "| quota vicini che battono B&H (25.7k)", round((nb.finale > 25695).mean() * 100))
print("2018-20: base MAR", base.mar_1820, "mediana vicini", nb.mar_1820.median(), "percentile base", round((nb.mar_1820 < base.mar_1820).mean() * 100),
      "| corr ranghi MAR 2021-26 vs 2018-20:", round(st.spearmanr(nb.mar, nb.mar_1820)[0], 2))
for g in ("SMAxEMA",):
    p = df[df.gruppo == g].copy(); p["sma"] = p.config.str.extract(r"SMA(\d+)").astype(int); p["ema"] = p.config.str.extract(r"EMA(\d+)").astype(int)
    for col in ("finale", "dd", "mar_1820"):
        t = p.pivot(index="sma", columns="ema", values=col); t.to_csv(HERE / f"s4_heat_sma_ema_{col}.csv"); print("\n", col, "\n", t.to_string())
p = df[df.gruppo == "MACDxETA"].copy(); p["macd"] = p.config.str.extract(r"(MACD\S+)"); p["eta"] = p.config.str.extract(r"eta(\d+)").astype(int)
for col in ("finale", "dd", "mar_1820"):
    t = p.pivot(index="macd", columns="eta", values=col); t.to_csv(HERE / f"s4_heat_macd_eta_{col}.csv"); print("\n", col, "\n", t.to_string())

# ---- punto 1: deflated Sharpe sui rendimenti settimanali
r = run(repo); sr, rw = wsr(r["equity"]); T = len(rw); sk, ku = st.skew(rw), st.kurtosis(rw, fisher=False)
V_nb = df[df.gruppo != "moduli"].sr_w.var()
V_wide = df.sr_w.var() * 2          # prove eterogenee (famiglie diverse): varianza piu' larga dei soli vicini
g = 0.5772156649
out = []
for Vn, V in (("vicini", V_nb), ("larga", max(V_wide, V_nb * 2))):
    for N in (31, 150, 900):
        sr0 = np.sqrt(V) * ((1 - g) * st.norm.ppf(1 - 1 / N) + g * st.norm.ppf(1 - 1 / (N * np.e)))
        dsr = st.norm.cdf((sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2))
        out.append(dict(varianza=Vn, N=N, sr_ann=round(sr * np.sqrt(52), 2), sr0_ann=round(sr0 * np.sqrt(52), 2),
                        sr_netto_ann=round((sr - sr0) * np.sqrt(52), 2), haircut_pct=round(sr0 / sr * 100), DSR=round(dsr, 3)))
d1 = pd.DataFrame(out); d1.to_csv(HERE / "s1_dsr.csv", index=False)
print(f"\nSharpe settimanale {sr:.3f} (annuo {sr*np.sqrt(52):.2f}), T={T}, skew {sk:.2f}, kurt {ku:.1f}; PSR(SR>0) {st.norm.cdf(sr*np.sqrt(T-1)/np.sqrt(1-sk*sr+(ku-1)/4*sr**2)):.3f}")
print(d1.to_string(index=False))
