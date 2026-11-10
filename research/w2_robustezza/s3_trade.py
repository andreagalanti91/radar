"""Punto 3: statistiche a livello di trade dal 2021 (bootstrap, win rate, concentrazione, leave-one-out, block bootstrap, sott'acqua)."""
from lib import *
from scipy import stats as st
rng = np.random.default_rng(7)
repo, long = load()
r = run(repo); T = all_trades(r); e = r["equity"] / r["equity"].iloc[0]
pn = np.array([t["pnl"] for t in T]); n = len(pn); yrs = (e.index[-1] - e.index[0]).days / 365.25
b = bh(repo, "2021-01-01"); b = b / b.iloc[0]
print(f"trade {n}, vincenti {(pn>0).sum()}, anni {yrs:.2f}, finale {e.iloc[-1]*1e4:.0f}, prodotto trade {np.prod(1+pn)*1e4:.0f}, B&H {b.iloc[-1]*1e4:.0f}")

def mdd(path):
    c = np.cumprod(path, axis=-1); c = np.concatenate([np.ones(c.shape[:-1] + (1,)), c], axis=-1)
    return (c / np.maximum.accumulate(c, axis=-1) - 1).min(axis=-1)

# a) bootstrap dei trade
S = rng.choice(pn, size=(10000, n), replace=True)
fin = np.prod(1 + S, axis=1); cagr = fin ** (1 / yrs) - 1; dd = mdd(1 + S); wr = (S > 0).mean(axis=1)
q = lambda x, p: np.percentile(x, p)
boot = dict(cagr_p5=q(cagr, 5), cagr_p25=q(cagr, 25), cagr_p50=q(cagr, 50), cagr_p75=q(cagr, 75), cagr_p95=q(cagr, 95),
            finale_p5=q(fin, 5) * 1e4, finale_p50=q(fin, 50) * 1e4, finale_p95=q(fin, 95) * 1e4,
            dd_trade_p50=q(dd, 50), dd_trade_p5=q(dd, 5), p_finale_sotto_bh=(fin < b.iloc[-1]).mean())
print("BOOTSTRAP TRADE", {k: round(float(v), 3) for k, v in boot.items()})
print("  NB: con 1 solo perdente (-4,1%) il ricampionamento non puo' produrre perdite che il campione non contiene: DD sottostimato.")

# b) win rate
k = int((pn > 0).sum())
print(f"WIN RATE {k}/{n}: P(WR<70%) Beta(1,1) = {st.beta.cdf(0.7, k+1, n-k+1):.3f}; Jeffreys = {st.beta.cdf(0.7, k+.5, n-k+.5):.3f}; "
      f"Clopper-Pearson 95% inf = {st.beta.ppf(0.025, k, n-k+1):.3f}; WR=70% darebbe >=13/14 con p = {st.binom.sf(k-1, n, 0.7):.3f}")
L = [t for t in T if t["side"] == "long"]; kl = sum(t["pnl"] > 0 for t in L)
print(f"  solo long {kl}/{len(L)}; versione senza F1 (prima della scelta): ", end="")
r0 = run(repo, f1=False); p0 = np.array([t["pnl"] for t in all_trades(r0)]); print(f"{(p0>0).sum()}/{len(p0)} = {(p0>0).mean()*100:.0f}%")
r18 = run(long, start="2018-01-01", end="2020-12-31"); p18 = np.array([t["pnl"] for t in all_trades(r18)])
print(f"  2018-20 (proxy) {(p18>0).sum()}/{len(p18)}; 2018-26 insieme {(p18>0).sum()+k}/{len(p18)+n} -> P(WR<70%) = {st.beta.cdf(0.7,(p18>0).sum()+k+1,len(p18)+n-(p18>0).sum()-k+1):.3f}")

# c) concentrazione e leave-one-out
lg = np.log1p(pn); o = np.argsort(-lg)
print(f"TOP3 quota del log-rendimento: {lg[o[:3]].sum()/lg.sum()*100:.0f}% (top1 {lg[o[0]]/lg.sum()*100:.0f}%); senza i 3 migliori finale {np.prod(1+np.delete(pn,o[:3]))*1e4:.0f}")
loo = pd.DataFrame([dict(signal=t["signal"], side=t["side"], exit=t["exit"], reason=t["reason"], pnl=round(t["pnl"] * 100, 1),
                         finale_senza=round(np.prod(1 + np.delete(pn, i)) * 1e4)) for i, t in enumerate(T)])
loo.to_csv(HERE / "s3_leave_one_out.csv", index=False); print(loo.to_string(index=False))
by = pd.Series(lg, index=[t["entry"][:4] for t in T]).groupby(level=0).sum(); print("log-rendimento per anno di ingresso (%):", (by / lg.sum() * 100).round(0).to_dict())

# d) block bootstrap settimanale strategia vs B&H (blocchi 8 sett., appaiati)
ws = e.resample("W-SUN").last().pct_change().dropna().to_numpy(); wb = b.resample("W-SUN").last().pct_change().dropna().to_numpy()
m = min(len(ws), len(wb)); ws, wb = ws[-m:], wb[-m:]
def bb(a_list, horizon, B=10000, blk=8):
    nb = int(np.ceil(horizon / blk)); starts = rng.integers(0, len(a_list[0]) - blk + 1, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(blk)[None, None, :]).reshape(B, -1)[:, :horizon]
    return [a[idx] for a in a_list]
Xs, Xb = bb([ws, wb], m)
fs, fb = np.prod(1 + Xs, 1), np.prod(1 + Xb, 1); ds, db = mdd(1 + Xs), mdd(1 + Xb); y = m / 52.18
cs, cb = fs ** (1 / y) - 1, fb ** (1 / y) - 1
blk = dict(strat_cagr_p5=q(cs, 5), strat_cagr_p50=q(cs, 50), strat_cagr_p95=q(cs, 95), strat_dd_p50=q(ds, 50), strat_dd_p5=q(ds, 5),
           bh_cagr_p5=q(cb, 5), bh_cagr_p50=q(cb, 50), bh_cagr_p95=q(cb, 95), bh_dd_p50=q(db, 50), bh_dd_p5=q(db, 5),
           p_strat_batte_bh=(fs > fb).mean(), p_calmar_migliore=((cs / -ds) > (cb / -db)).mean(), p_strat_cagr_neg=(cs < 0).mean(),
           p_dd_oltre_30=(ds < -0.30).mean(), p_dd_oltre_40=(ds < -0.40).mean())
print("BLOCK BOOTSTRAP 2021-26 (settimanale, 8 sett.)", {k: round(float(v), 3) for k, v in blk.items()})
pd.DataFrame([{**{"tipo": "trade"}, **boot}]).to_csv(HERE / "s3_bootstrap_trade.csv", index=False)
pd.DataFrame([blk]).to_csv(HERE / "s3_block_bootstrap.csv", index=False)

# e) tempo sott'acqua
def uw(x):
    u = x < x.cummax() * 0.9999; g = (u != u.shift()).cumsum()[u]; longest = g.groupby(g).size().max() if len(g) else 0
    deep = (x / x.cummax() - 1 < -0.10).mean()
    return round(u.mean() * 100), int(longest), round(deep * 100)
print("SOTT'ACQUA (quota giorni sotto il massimo, giorni del periodo piu' lungo, quota giorni oltre -10%): strategia", uw(e), "B&H", uw(b))
inpos = pd.Series(0, index=e.index)
for t in T:
    inpos[(inpos.index >= t["entry"]) & (inpos.index <= (t["exit"] if t["exit"] != "open" else "9999"))] = 1
print("tempo in posizione %:", round(inpos.mean() * 100), "| anni con rendimento < 5%:", W.metrics(r)["years"])
