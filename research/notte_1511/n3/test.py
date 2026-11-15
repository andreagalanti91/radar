"""N3 · test preregistrati (PREREG.md): H1 stablecoin, H2 liquidità netta Fed, H3 FOMC, H4 premio Coinbase; filtro su W3.
Uso: python research/notte_1511/n3/test.py → risultati.txt, segnali.csv, condizionati.csv, fomc_eventi.csv, w3_filtro.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D = HERE / "data"
sys.path.insert(0, str(HERE.parents[2]))
from radar import weekly as W  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

RNG = np.random.default_rng(1511)
IS, OOS = ("2021-01-01", "2023-12-31"), ("2024-01-01", "2026-12-31")
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


# ---------- dati
f = build_features(load_all())
f = f[f["close"].notna()]
px = f["close"]
lp = np.log(px)
fwd = {h: (lp.shift(-h) - lp) * 100 for h in (1, 7, 30)}


def fred(name):
    s = pd.read_csv(D / f"{name}.csv", na_values=["."])
    s.columns = ["date", name]
    s["date"] = pd.to_datetime(s["date"])
    return s.set_index("date")[name].astype(float)


days = pd.date_range("2019-01-01", px.index[-1], freq="D")

# H1 stablecoin
js = json.load(open(D / "stablecoins_all.json"))
st = pd.Series({pd.Timestamp(int(r["date"]), unit="s").normalize(): r["totalCirculatingUSD"].get("peggedUSD", np.nan) for r in js})
st = st.reindex(days).ffill()
st_g30 = (st / st.shift(30) - 1).shift(1)
sig_h1 = (st_g30 > 0).where(st_g30.notna())
_med = st_g30.rolling(365, min_periods=200).median()
sig_h1b = (st_g30 > _med).where(_med.notna())

# H2 liquidità netta
walcl = fred("WALCL").reindex(days).ffill().shift(2)
tga = fred("WTREGEN").reindex(days).ffill().shift(2)
rrp = fred("RRPONTSYD").reindex(days).ffill().shift(1) * 1000
nl = walcl - tga - rrp
_dnl = nl - nl.shift(28)
sig_h2 = (_dnl > 0).where(_dnl.notna())

# H4 premio Coinbase
cb = pd.read_csv(D / "coinbase_btcusd_1d.csv", parse_dates=["date"]).set_index("date")["close"]
ut = pd.read_csv(D / "coinbase_usdtusd_1d.csv", parse_dates=["date"]).set_index("date")["close"]
ut = ut.reindex(days).ffill().fillna(1.0)
prem = (cb.reindex(days) / (px.reindex(days) * ut) - 1) * 100
prem7 = prem.rolling(7, min_periods=5).mean().shift(1)
sig_h4 = (prem7 > 0).where(prem7.notna())

sigs = pd.DataFrame({"stable_g30": st_g30, "H1": sig_h1, "H1b": sig_h1b, "netliq": nl, "H2": sig_h2,
                     "cb_prem7": prem7, "H4": sig_h4}).reindex(px.index)
sigs.join(pd.DataFrame({"close": px})).loc["2020-10-01":].to_csv(HERE / "segnali.csv", float_format="%.6g")


def cond_test(sig: pd.Series, h: int, per, n_plac=2000):
    a, b = pd.Timestamp(per[0]), pd.Timestamp(per[1])
    r = fwd[h].loc[a:b]
    s = sig.reindex(r.index)
    ok = r.notna() & s.notna()
    r, s = r[ok].to_numpy(), s[ok].astype(bool).to_numpy()
    if s.sum() < 20 or (~s).sum() < 20:
        return dict(n=len(r), on=s.mean(), base=r.mean(), m_on=np.nan, m_off=np.nan, diff=np.nan, p=np.nan)
    d = r[s].mean() - r[~s].mean()
    n = len(r)
    pl = np.empty(n_plac)
    for i in range(n_plac):
        k = RNG.integers(60, n - 60)
        ss = np.roll(s, k)
        pl[i] = r[ss].mean() - r[~ss].mean()
    return dict(n=n, on=s.mean(), base=r.mean(), m_on=r[s].mean(), m_off=r[~s].mean(), diff=d, p=(pl >= d).mean())


rows = []
say("=" * 100)
say("N3 · risultati dei test preregistrati (PREREG.md). Rendimenti futuri log in punti %; diff = media ON − media OFF;")
say("p = placebo unilaterale (spostamento circolare, 2.000). IS 2021–23, OOS 2024–26.")
say("=" * 100)
VERD = {}
for name, sig, prim, sec in (("H1 stablecoin 30g > 0", sig_h1, 30, 7), ("H1b stablecoin 30g > mediana 365g (descrittiva)", sig_h1b, 30, 7),
                             ("H2 liquidità netta Fed 28g > 0", sig_h2, 30, 7), ("H4 premio Coinbase 7g > 0", sig_h4, 7, 30)):
    say(f"\n{name}  (primario {prim} g, secondario {sec} g)")
    res = {}
    for per_name, per in (("IS", IS), ("OOS", OOS)):
        for h in (1, 7, 30):
            t = cond_test(sig.reindex(px.index), h, per)
            res[(per_name, h)] = t
            rows.append(dict(ipotesi=name, periodo=per_name, h=h, **{k: round(v, 4) if isinstance(v, float) else v for k, v in t.items()}))
            say(f"  {per_name:3s} h={h:2d}: n={t['n']:4d} ON={t['on']*100:5.1f}%  base={t['base']:+6.2f}  ON={t['m_on']:+6.2f}  "
                f"OFF={t['m_off']:+6.2f}  diff={t['diff']:+6.2f}  p={t['p']:.3f}")
    ok = all(res[(p, prim)]["diff"] > 0 and res[(p, prim)]["p"] < 0.10 for p in ("IS", "OOS")) and \
        all(res[(p, sec)]["diff"] > 0 for p in ("IS", "OOS"))
    VERD[name] = ok
    say(f"  → criterio preregistrato: {'PASSA' if ok else 'NON PASSA'}")
pd.DataFrame(rows).to_csv(HERE / "condizionati.csv", index=False)

# correlazione H4 con pf14z / flusso W3
c = pd.concat([prem7, W.live_flow(f)], axis=1).dropna()
say(f"\nCorrelazione premio Coinbase 7g con flusso perp W3 (pf14z 3g): {c.corr().iloc[0, 1]:+.2f} (n={len(c)})")
c2 = pd.concat([st_g30.reindex(px.index), nl.diff(28).reindex(px.index), prem7.reindex(px.index)], axis=1).dropna()
c2.columns = ["stable", "netliq", "cbprem"]
say("Correlazioni fra i segnali continui:\n" + c2.corr().round(2).to_string())

# ---------- H3 FOMC
fo = pd.read_csv(D / "fomc_dates.csv", parse_dates=["date"])["date"]
fo = fo[(fo >= "2021-01-01") & (fo <= px.index[-9])]
C = px


def win(t, a, b):
    i = C.index.get_loc(t)
    return (np.log(C.iloc[i + b]) - np.log(C.iloc[i + a])) * 100


WINS = {"pre (t-3→t-1)": (-3, -1), "reazione (t-1→t+1)": (-1, 1), "dopo (t+1→t+8)": (1, 8)}
ev = pd.DataFrame({"date": fo.dt.date.astype(str)})
for k, (a, b) in WINS.items():
    ev[k] = [win(t, a, b) for t in fo]
ev.to_csv(HERE / "fomc_eventi.csv", index=False, float_format="%.3f")
fo_set = set(fo)
weds = [d for d in C.index[10:-10] if d.dayofweek == 2 and d >= pd.Timestamp("2021-01-01")
        and min(abs((d - x).days) for x in fo_set) >= 8]
say("\n" + "=" * 100)
say(f"H3 FOMC: {len(fo)} decisioni 2021-01 → {fo.iloc[-1].date()}; placebo su {len(weds)} mercoledì lontani ≥ 8 g (5.000 estrazioni)")
VERD_H3 = False
for k, (a, b) in WINS.items():
    x = ev[k].to_numpy()
    base = np.array([win(d, a, b) for d in weds])
    pl = np.array([RNG.choice(base, len(x), replace=False).mean() for _ in range(5000)])
    p2 = (np.abs(pl - base.mean()) >= abs(x.mean() - base.mean())).mean()
    isx = ev.loc[ev["date"] < "2024-01-01", k].mean()
    oosx = ev.loc[ev["date"] >= "2024-01-01", k].mean()
    same = np.sign(isx - base.mean()) == np.sign(oosx - base.mean())
    ok = p2 < 0.0167 and same
    VERD_H3 |= ok
    say(f"  {k:20s}: FOMC media {x.mean():+6.2f} (mediana {np.median(x):+5.2f}, positivi {np.mean(x>0)*100:4.0f}%) | "
        f"mercoledì qualsiasi {base.mean():+5.2f} | IS {isx:+5.2f} OOS {oosx:+5.2f} | p bilaterale {p2:.3f} → "
        f"{'PASSA' if ok else 'NON PASSA'}")
    say(f"  {'':20s}  |rendimento| medio FOMC {np.abs(x).mean():5.2f} contro {np.abs(base).mean():5.2f} (volatilità)")
VERD["H3 FOMC"] = VERD_H3

# ---------- filtro su W3 per le ipotesi che passano (e, per trasparenza, per tutte)
say("\n" + "=" * 100)
say("Filtro su W3 (nuovi long solo con segnale ON alla domenica del segnale; short invariati). Baseline 78.474 $.")
orig_wb = W.weekly_bars


def run_with(sig_daily: pd.Series | None):
    def wb(ff):
        w = orig_wb(ff)
        if sig_daily is not None:
            s = sig_daily.reindex(w.index).fillna(True).astype(bool)   # dato mancante = nessun blocco
            w["long"] = w["long"] & s
        return w
    W.weekly_bars = wb
    try:
        r = W.simulate(f)
    finally:
        W.weekly_bars = orig_wb
    m = W.metrics(r)
    e = r["equity"]
    h1 = e.loc[:"2023-12-31"]
    h2 = e.loc["2024-01-01":]
    ret1 = h1.iloc[-1] / h1.iloc[0] - 1
    ret2 = e.iloc[-1] / h1.iloc[-1] - 1
    dd1 = (h1 / h1.cummax() - 1).min()
    dd2 = (h2 / h2.cummax() - 1).min()
    return dict(final=e.iloc[-1], n=m["n"], wr=m["win_rate"], dd=m["max_dd_pct"], mar=m["mar"],
                r2123=ret1 * 100, r2426=ret2 * 100, dd2123=dd1 * 100, dd2426=dd2 * 100)


wrows = []
base = run_with(None)
wrows.append(dict(variante="W3 base", **base))
say(f"  W3 base: {base['final']:,.0f} $  trade {base['n']}  DD {base['dd']:.1f}%  2021–23 {base['r2123']:+.0f}%  2024–26 {base['r2426']:+.0f}%")
for name, sig in (("H1 stablecoin", sig_h1), ("H2 liquidità netta", sig_h2), ("H4 premio Coinbase", sig_h4)):
    s = sig.reindex(px.index).astype(float)
    r = run_with(s.astype(bool).where(s.notna(), True))
    # placebo: 200 spostamenti circolari
    vals = s.to_numpy()
    pl = []
    for _ in range(200):
        k = RNG.integers(60, len(vals) - 60)
        ps = pd.Series(np.roll(vals, k), s.index)
        pl.append(run_with(ps.astype(bool).where(ps.notna(), True))["final"])
    pl = np.array(pl)
    q90 = np.quantile(pl, 0.9)
    passed = VERD.get([k for k in VERD if k.startswith(name.split()[0] + " ")][0], False)
    wrows.append(dict(variante=f"W3 + filtro {name}", **r, placebo_med=np.median(pl), placebo_q90=q90))
    say(f"  + {name:20s}: {r['final']:,.0f} $  trade {r['n']}  DD {r['dd']:.1f}%  MAR {r['mar']:.1f}  2021–23 {r['r2123']:+.0f}%  "
        f"2024–26 {r['r2426']:+.0f}% | placebo mediana {np.median(pl):,.0f} $, 90° pct {q90:,.0f} $"
        f"{'' if passed else '  (ipotesi non passata: solo descrittivo)'}")
pd.DataFrame(wrows).to_csv(HERE / "w3_filtro.csv", index=False, float_format="%.2f")

say("\nVerdetti preregistrati: " + "; ".join(f"{k}: {'PASSA' if v else 'NO'}" for k, v in VERD.items()))
(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
