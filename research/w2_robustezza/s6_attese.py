"""Punto 6: attese a 3 anni (block bootstrap dei rendimenti settimanali, blocchi 8 sett.) e casi peggiori."""
from lib import *
rng = np.random.default_rng(11)
repo, long = load()
H = 156
def mdd(path):
    c = np.cumprod(path, axis=-1); c = np.concatenate([np.ones(c.shape[:-1] + (1,)), c], axis=-1)
    return (c / np.maximum.accumulate(c, axis=-1) - 1).min(axis=-1)
def boot(w, B=10000, blk=8):
    nb = int(np.ceil(H / blk)); s = rng.integers(0, len(w) - blk + 1, size=(B, nb))
    X = w[(s[:, :, None] + np.arange(blk)).reshape(B, -1)[:, :H]]
    c = np.prod(1 + X, 1) ** (1 / 3) - 1; d = mdd(1 + X); p = np.percentile
    return dict(cagr_p10=p(c, 10), cagr_p50=p(c, 50), cagr_p90=p(c, 90), dd_p50=p(d, 50), dd_p10=p(d, 10), dd_p1=p(d, 1),
                p_cagr_neg=(c < 0).mean(), p_dd_oltre_30=(d < -.3).mean(), p_dd_oltre_40=(d < -.4).mean(), finale10k_p10=1e4 * (1 + p(c, 10)) ** 3,
                finale10k_p50=1e4 * (1 + p(c, 50)) ** 3, finale10k_p90=1e4 * (1 + p(c, 90)) ** 3)
wk = lambda e: e.resample("W-SUN").last().pct_change().dropna().to_numpy()
e21 = run(repo)["equity"]; e18 = run(long, start="2018-01-01")["equity"]; e18n = run(long, start="2018-01-01", f1=False)["equity"]
e15 = run(long, start="2015-01-01", flow="none")["equity"]
sc = {"A 2021-26 (in campione, ottimista)": wk(e21), "B 2018-26 in uso (proxy flusso pre-2020)": wk(e18)}
w = wk(e18); sc["C = B con haircut 35% della media"] = w - 0.35 * w.mean()
sc["D 2018-26 senza F1 (regola prima della scelta)"] = wk(e18n)
sc["E 2015-26 senza flusso, con F1"] = wk(e15)
rows = [dict(scenario=k, sett=len(v), **{a: round(float(b), 3) for a, b in boot(v).items()}) for k, v in sc.items()]
df = pd.DataFrame(rows); df.to_csv(HERE / "s6_attese.csv", index=False); pd.set_option("display.width", 300); print(df.to_string(index=False))

print("\nCASI PEGGIORI (anno solare, equity giornaliera)")
def yr(e, a, b):
    s = e[(e.index >= a) & (e.index <= b)]; return round((s.iloc[-1] / s.iloc[0] - 1) * 100, 1), round((s / s.cummax() - 1).min() * 100, 1)
wc = []
for name, kw in [("in uso", {}), ("senza F1", dict(f1=False)), ("MACD 12/26/9", dict(macd=(12, 26, 9))), ("MACD 10/24/7", dict(macd=(10, 24, 7))),
                 ("senza flusso", dict(flow="none")), ("senza flusso e F1", dict(flow="none", f1=False))]:
    eL = run(long, start="2017-06-01", **kw)["equity"]; eR = run(repo, **kw)["equity"]
    eL2 = run(long, start="2018-01-01", **kw)["equity"]
    wc.append(dict(versione=name, r2018_dal_top=yr(eL, "2017-12-17", "2018-12-31")[0], dd2018_dal_top=yr(eL, "2017-12-17", "2018-12-31")[1],
                   r2018_flat_1gen=yr(eL2, "2018-01-01", "2018-12-31")[0], dd2018_flat=yr(eL2, "2018-01-01", "2018-12-31")[1],
                   r2022=yr(eR, "2021-11-08", "2022-12-31")[0], dd2022=yr(eR, "2021-11-08", "2022-12-31")[1],
                   dd_2021_26=round((eR / eR.cummax() - 1).min() * 100, 1), r2025=yr(eR, "2025-01-01", "2025-12-31")[0]))
b = long["close"]; br = repo["close"]
wc.append(dict(versione="buy & hold", r2018_dal_top=yr(b, "2017-12-17", "2018-12-31")[0], dd2018_dal_top=yr(b, "2017-12-17", "2018-12-31")[1],
               r2018_flat_1gen=yr(b, "2018-01-01", "2018-12-31")[0], dd2018_flat=yr(b, "2018-01-01", "2018-12-31")[1],
               r2022=yr(br, "2021-11-08", "2022-12-31")[0], dd2022=yr(br, "2021-11-08", "2022-12-31")[1], dd_2021_26=-76.6, r2025=yr(br, "2025-01-01", "2025-12-31")[0]))
d2 = pd.DataFrame(wc); d2.to_csv(HERE / "s6_casi_peggiori.csv", index=False); print(d2.to_string(index=False))
# dove nasce il DD 2018 della versione in uso
e = run(long, start="2018-01-01")["equity"]; s = e[:"2019-06-30"]; d = s / s.cummax() - 1
print("DD 2018 in uso: minimo", d.idxmin().date(), round(d.min() * 100, 1), "| massimo precedente", s[:d.idxmin()].idxmax().date())
# finestre mobili di 3 anni realmente osservate (2018-26, in uso)
r3 = (e.shift(-1095) / e - 1).dropna(); c3 = (1 + r3) ** (1 / 3) - 1
print("finestre mobili 3 anni 2018-26 (in uso): CAGR min %.1f%% mediana %.1f%% max %.1f%%" % (c3.min() * 100, c3.median() * 100, c3.max() * 100))
