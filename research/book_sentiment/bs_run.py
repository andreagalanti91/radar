"""Studio book_sentiment: esecuzione della preregistrazione (PREREG.md, commit dacb01d). Output: risultati.txt + csv.
Uso: BS_WORK=<cache> python3 research/book_sentiment/bs_run.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bs_data as D  # noqa: E402

RNG = np.random.default_rng(20261122)
OUT: list[str] = []
COST = 0.0010            # per lato: commissione 0,05% + slippage 0,05%
HS = (1, 4, 24)
EFF_UTILE, EFF_PLAUS = 0.40, 0.10     # punti percentuali
Z80, ZHOLM = 1.96 + 0.8416, 2.9137 + 0.8416   # α 0,05 a due code; α 0,05/14 a due code


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


# ------------------------------------------------------------------ pannelli con prezzi
def build_A(minutes=30) -> pd.DataFrame:
    p = D.panel_A(minutes)
    m = D.m1()
    idx = m.index.to_numpy("datetime64[ns]")
    op = m["open"].to_numpy()
    t = p["t"].to_numpy("datetime64[ns]")
    i0 = np.searchsorted(idx, t, side="right")
    ok0 = i0 < len(idx)
    p["px"] = np.where(ok0, op[np.minimum(i0, len(idx) - 1)], np.nan)
    tx = idx[np.minimum(i0, len(idx) - 1)]

    def at(delta_h):
        tt = tx + np.timedelta64(int(delta_h * 60), "m")
        j = np.searchsorted(idx, tt, side="left")
        good = (j < len(idx)) & ok0
        jj = np.minimum(j, len(idx) - 1)
        good &= (idx[jj] - tt) <= np.timedelta64(5, "m")
        return np.where(good, op[jj], np.nan)
    for h in HS:
        p[f"r{h}"] = (at(h) / p["px"] - 1) * 100
    p["past1"] = (p["px"] / at(-1) - 1) * 100
    p["past24"] = (p["px"] / at(-24) - 1) * 100
    p["block"] = p["t"].dt.normalize()
    return p


def build_B() -> pd.DataFrame:
    p = D.panel_B()
    h = D.h1()
    o = h["open"].reindex(pd.date_range(h.index.min(), h.index.max(), freq="h"))
    p["px"] = o.reindex(p["t"]).to_numpy()
    for k in HS:
        p[f"r{k}"] = (o.shift(-k).reindex(p["t"]).to_numpy() / p["px"] - 1) * 100
    p["past1"] = (p["px"] / o.shift(1).reindex(p["t"]).to_numpy() - 1) * 100
    p["past24"] = (p["px"] / o.shift(24).reindex(p["t"]).to_numpy() - 1) * 100
    p["block"] = p["t"].dt.to_period("W").dt.start_time
    return p


# ------------------------------------------------------------------ statistica Δ, placebo a blocchi, bootstrap
def delta(sig, r):
    ok = ~np.isnan(r)
    a, b = r[ok & (sig > 0)], r[ok & (sig < 0)]
    return (a.mean() - b.mean()) if len(a) and len(b) else np.nan


def shifts(n, kmin, reps):
    return RNG.integers(kmin, n - kmin + 1, size=reps)


def placebo_delta(sig, r, kmin, reps):
    ok = ~np.isnan(r)
    rr = np.where(ok, r, 0.0)
    okf = ok.astype(float)
    pos, neg = (sig > 0).astype(float), (sig < 0).astype(float)
    out = np.empty(reps)
    for i, k in enumerate(shifts(len(sig), kmin, reps)):
        pp, nn = np.roll(pos, k), np.roll(neg, k)
        out[i] = (pp @ rr) / max(pp @ okf, 1) - (nn @ rr) / max(nn @ okf, 1)
    return out


def boot_ci(sig, r, block, reps=2000):
    ub = pd.unique(block)
    groups = [np.flatnonzero(block == b) for b in ub]
    vals = []
    for _ in range(reps):
        ix = np.concatenate([groups[j] for j in RNG.integers(0, len(groups), len(groups))])
        vals.append(delta(sig[ix], r[ix]))
    return np.nanpercentile(vals, [2.5, 97.5])


def spearman(x, y):
    ok = ~(np.isnan(x) | np.isnan(y))
    if ok.sum() < 5:
        return np.nan
    return float(np.corrcoef(pd.Series(x[ok]).rank(), pd.Series(y[ok]).rank())[0, 1])


def cell(name, p, col, h, kmin, reps, mid_t, weeks):
    sig = np.sign(p[col].to_numpy(float))
    r = p[f"r{h}"].to_numpy(float)
    ok = ~np.isnan(r)
    d = delta(sig, r)
    pl = placebo_delta(sig, r, kmin, reps)
    se0 = float(np.std(pl))
    pv = (1 + (np.abs(pl) >= abs(d)).sum()) / (1 + reps)
    lo, hi = boot_ci(sig, r, p["block"].to_numpy())
    m1 = (p["t"] <= mid_t).to_numpy()
    d1, d2 = delta(sig[m1], r[m1]), delta(sig[~m1], r[~m1])
    hit = float(((sig * r)[ok & (sig != 0)] > 0).mean())
    mde, mdeh = Z80 * se0, ZHOLM * se0
    return dict(test=name, insieme=name[0], segnale=col, h=h, n=int((ok & (sig != 0)).sum()), n_pos=int((ok & (sig > 0)).sum()),
                n_neg=int((ok & (sig < 0)).sum()), delta=d, ic_lo=lo, ic_hi=hi, p=pv, meta1=d1, meta2=d2, hit=hit,
                rho=spearman(p[col].to_numpy(float), r), se0=se0, mde80=mde, mde80_holm=mdeh,
                sett_utile=weeks * (mde / EFF_UTILE) ** 2, sett_plaus=weeks * (mde / EFF_PLAUS) ** 2)


# ------------------------------------------------------------------ regola
def simulate(t, px, st, cost=COST):
    """Posizione st[i] dal prezzo px[i] al prezzo px[i+1]; costi su ogni variazione di posizione; chiusura all'ultimo prezzo."""
    t, px, st = np.asarray(t), np.asarray(px, float), np.asarray(st, float).copy()
    st[-1] = 0
    r = np.diff(px) / px[:-1]
    eq = np.empty(len(px)); eq[0] = 10_000.0
    prev, cur = 0.0, 10_000.0
    trades, open_eq, gross = [], None, 0.0
    for i in range(len(px) - 1):
        if st[i] != prev:
            if prev != 0:
                cur *= 1 - cost; trades.append(cur / open_eq - 1); open_eq = None
            if st[i] != 0:
                open_eq = cur; cur *= 1 - cost
            prev = st[i]
        cur *= 1 + prev * r[i]
        gross += np.log1p(prev * r[i])
        eq[i + 1] = cur
    if prev != 0:
        cur *= 1 - cost; trades.append(cur / open_eq - 1); eq[-1] = cur
    e = pd.Series(eq, index=pd.DatetimeIndex(t))
    daily = e.groupby(e.index.normalize()).last()
    daily = pd.concat([pd.Series([10_000.0]), daily])
    dd = float((daily / daily.cummax() - 1).min())
    yrs = (e.index[-1] - e.index[0]).total_seconds() / (365.25 * 86400)
    cagr = (cur / 10_000) ** (1 / yrs) - 1 if cur > 0 else -1
    tr = np.array(trades)
    return dict(finale=cur, rend=(cur / 10_000 - 1) * 100, dd=dd * 100, trade=len(tr), wr=float((tr > 0).mean() * 100) if len(tr) else np.nan,
                mar=cagr / abs(dd) if dd < 0 else np.nan, lordo=(np.exp(gross) - 1) * 100,
                senza_migliore=(cur / (1 + tr.max()) / 10_000 - 1) * 100 if len(tr) else np.nan, esposto=float((st[:-1] != 0).mean() * 100))


def gross_log(px, st):
    r = np.diff(px) / px[:-1]
    return float(np.log1p(st[:-1] * r).sum())


def every(t, st, hours):
    """Decisione solo ogni `hours` ore: fra una decisione e l'altra la posizione resta quella presa."""
    t = pd.DatetimeIndex(t)
    out, last, cur = np.empty(len(st)), None, 0
    for i in range(len(st)):
        if last is None or (t[i] - last) >= pd.Timedelta(hours=hours) - pd.Timedelta(minutes=10):
            cur, last = st[i], t[i]
        out[i] = cur
    return out


def rule_block(tag, p, variants, kmin, reps, mid_t, bh_note):
    p = p[p["px"].notna()].reset_index(drop=True)
    t, px = p["t"].to_numpy(), p["px"].to_numpy(float)
    rows = []
    for nm, st in variants(p).items():
        s = simulate(t, px, st)
        m1 = (p["t"] <= mid_t).to_numpy()
        a, b = simulate(t[m1], px[m1], st[m1]), simulate(t[~m1], px[~m1], st[~m1])
        s075 = simulate(t, px, st, 0.00075)
        rows.append(dict(insieme=tag, variante=nm, **s, finale_m1=a["finale"], finale_m2=b["finale"], finale_costo075=s075["finale"]))
    st = variants(p)["V1 regola S ±0,2"]
    obs = gross_log(px, np.r_[st[:-1], 0])
    pl = np.array([gross_log(px, np.r_[np.roll(st, k)[:-1], 0]) for k in shifts(len(st), kmin, reps)])
    pv = (1 + (pl >= obs).sum()) / (1 + reps)
    bh = (px[-1] / px[0] * (1 - COST) ** 2 - 1) * 100
    e = pd.Series(px, index=pd.DatetimeIndex(t)); dly = e.groupby(e.index.normalize()).last()
    bhdd = float((dly / dly.cummax() - 1).min() * 100)
    rows.append(dict(insieme=tag, variante="Buy & hold (stessa finestra)", finale=10_000 * (1 + bh / 100), rend=bh, dd=bhdd, trade=1))
    say(f"\n--- Regola · insieme {tag} · {pd.Timestamp(t[0]):%d/%m/%Y} → {pd.Timestamp(t[-1]):%d/%m/%Y} · costi {COST*100:.2f}% per lato ---")
    df = pd.DataFrame(rows)
    say(df[["variante", "finale", "rend", "dd", "trade", "wr", "mar", "lordo", "senza_migliore", "esposto", "finale_m1", "finale_m2", "finale_costo075"]]
        .to_string(index=False, float_format=lambda x: f"{x:,.1f}"))
    say(f"placebo a blocchi sul rendimento LORDO di V1: osservato {(np.exp(obs) - 1) * 100:+.2f}%, placebo mediana {(np.exp(np.median(pl)) - 1) * 100:+.2f}% "
        f"(5°–95° {(np.exp(np.percentile(pl, 5)) - 1) * 100:+.2f}% / {(np.exp(np.percentile(pl, 95)) - 1) * 100:+.2f}%), p a una coda {pv:.4f}")
    say(bh_note)
    return df, pv, rows[0]


def holm(ps: dict) -> dict:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        out[k] = run
    return out


def controls(tag, p):
    say(f"\n--- Controlli non di conferma · insieme {tag} ---")
    for col in [c for c in ("I", "L", "S") if c in p.columns]:
        x = p[col].to_numpy(float)
        say(f"  {col}: Spearman con rendimento PRECEDENTE 1h {spearman(x, p['past1'].to_numpy(float)):+.2f}, 24h {spearman(x, p['past24'].to_numpy(float)):+.2f}; "
            f"con rendimento SUCCESSIVO 1h {spearman(x, p['r1'].to_numpy(float)):+.3f}, 4h {spearman(x, p['r4'].to_numpy(float)):+.3f}, 24h {spearman(x, p['r24'].to_numpy(float)):+.3f}")
    mom = np.sign(p["past1"].to_numpy(float))
    for h in HS:
        r = p[f"r{h}"].to_numpy(float)
        st = D.state(p["S"])
        big = np.where((p["liq_long"] + p["liq_short"]).to_numpy() >= 1e5, np.sign(p["L"].to_numpy(float)), 0)
        ok = ~(np.isnan(r) | np.isnan(p["past1"].to_numpy(float)))
        X = np.c_[np.ones(ok.sum()), np.sign(p["L"].to_numpy(float))[ok], p["past1"].to_numpy(float)[ok]]
        beta = np.linalg.lstsq(X, r[ok], rcond=None)[0]
        say(f"  h {h:>2}h: Δ etichette S ±0,2 {delta(st, r):+.3f}% | Δ L con ≥ 100k$ {delta(big, r):+.3f}% (n {int((big != 0).sum())}) | "
            f"Δ segno del rendimento dell'ora precedente (momentum 1h) {delta(mom, r):+.3f}% | coeff. di segno(L) al netto del rendimento precedente {beta[1]:+.3f}% (Δ ≈ {2 * beta[1]:+.3f}%)")


# ================================================================== esecuzione
res = []
A = build_A(30)
wA = (A["t"].max() - A["t"].min()).total_seconds() / (7 * 86400)
midA = A["t"].min() + (A["t"].max() - A["t"].min()) / 2
say(f"=== INSIEME A · {len(A)} foto, {wA:.2f} settimane; prezzi 1m fino a {D.m1().index.max()} ===")
for col in ("S", "I", "L"):
    for h in HS:
        res.append(cell(f"A·{col}→{h}h", A, col, h, 24, 5000, midA, wA))

B = build_B()
wB = (B["t"].max() - B["t"].min()).total_seconds() / (7 * 86400)
midB = B["t"].min() + (B["t"].max() - B["t"].min()) / 2
say(f"=== INSIEME B · {len(B)} ore, {wB:.1f} settimane ===")
for h in HS:
    res.append(cell(f"B·L→{h}h", B, "L", h, 48, 2000, midB, wB))


def varA(p):
    A60 = D.panel_A(60).set_index("t").reindex(p["t"])
    v = {"V1 regola S ±0,2": D.state(p["S"]), "V2 soglia ±0,1": D.state(p["S"], 0.1), "V3 soglia ±0,3": D.state(p["S"], 0.3),
         "V4 solo I (±0,2)": D.state(p["I"]), "V5 solo L (±0,2)": D.state(p["L"]), "V6 L a 60 minuti": D.state(A60["S"].to_numpy()),
         "V7 rovesciata": -D.state(p["S"]), "V8 decisione ogni 4 ore": every(p["t"], D.state(p["S"]), 4)}
    return {k: np.asarray(x, float) for k, x in v.items()}


def varB(p):
    v = {"V1 regola S ±0,2": D.state(p["S"]), "V2 soglia ±0,1": D.state(p["S"], 0.1), "V3 soglia ±0,3": D.state(p["S"], 0.3),
         "V7 rovesciata": -D.state(p["S"]), "V8 decisione ogni 4 ore": every(p["t"], D.state(p["S"]), 4)}
    return {k: np.asarray(x, float) for k, x in v.items()}


pxA = A["px"].dropna()
w31 = 0.389 * (65286 / pxA.iloc[-1] - 1) * 100       # contesto: short W3.1 dal 16/11 a 65.286 $, esposizione 0,389 (research/book_liq)
dfA, pRA, _ = rule_block("A", A, varA, 24, 5000, midA,
                         f"contesto W3.1 nella finestra: flat fino al 16/11, poi short da 65.286 $ con esposizione 0,389 → circa {w31:+.1f}% lordo sul capitale (posizione aperta)")
A11 = A[A["t"] >= "2026-11-11"].reset_index(drop=True)
s11 = simulate(A11["t"].to_numpy(), A11["px"].to_numpy(float), np.asarray(D.state(A11["S"]), float))
say(f"V1 solo dal 11/11 (liquidazioni multi-fonte): finale {s11['finale']:,.0f} $, lordo {s11['lordo']:+.2f}%, trade {s11['trade']}, DD {s11['dd']:.1f}%")
dfB, pRB, _ = rule_block("B", B, varB, 48, 2000, midB,
                         "contesto W3 nella finestra (research/weekly_w3_trades.csv): long fino al 17/08/2023, long 23/10/2023–01/01/2024 (+40,5%), "
                         "long 12/02–11/03/2024 (+42,2%), long dal 23/09/2024: vedi README")

ps = {r["test"]: r["p"] for r in res}
ps["RA regola su A"], ps["RB regola su B"] = pRA, pRB
hp = holm(ps)
T = pd.DataFrame(res)
T["p_holm"] = T["test"].map(hp)
say("\n=== DOMANDA 1 · Δ = rendimento medio dopo segno + meno dopo segno − (punti %) ===")
say(T[["test", "n", "n_pos", "n_neg", "delta", "ic_lo", "ic_hi", "p", "p_holm", "meta1", "meta2", "hit", "rho"]].to_string(index=False, float_format=lambda x: f"{x:+.3f}"))
say("\n=== POTENZA · SE₀ dal placebo a blocchi; MDE 80% (α 0,05) e al primo passo di Holm; settimane necessarie (foto/ore orarie) ===")
say(T[["test", "se0", "mde80", "mde80_holm", "sett_utile", "sett_plaus"]].to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
say(f"\nRegole: RA p {pRA:.4f} (Holm {hp['RA regola su A']:.3f}); RB p {pRB:.4f} (Holm {hp['RB regola su B']:.3f})")
controls("A", A)
controls("B", B)

# Domanda 4: descrittivo sui muri "ritirati" in senso largo (nessun valore probatorio)
say("\n=== DOMANDA 4 · descrittivo, definizione larga (46 eventi), nessun test ===")
wl = pd.read_csv(HERE / "muri_coppie.csv", parse_dates=["t"])
ev = wl[(~wl.touched) & wl.inwin & wl.moved & (wl["drop"] > 0)].merge(A[["t", "r1", "r4"]], on="t", how="left")
for side in ("bid", "ask"):
    g = ev[ev.side == side]
    say(f"  muro {side} ritirato (largo): n {len(g)}, rendimento medio 1h {g.r1.mean():+.3f}% (dev. st. {g.r1.std():.2f}), 4h {g.r4.mean():+.3f}% (dev. st. {g.r4.std():.2f}); "
        f"tutte le foto: 1h {A.r1.mean():+.3f}%, 4h {A.r4.mean():+.3f}%")
sd1 = A.r1.std()
say(f"  dev. st. del rendimento a 1h {sd1:.2f}%: per vedere una differenza bid−ask di 0,10% (0,40%) con potenza 80% servono ~{int(2 * (Z80 * sd1 / 0.10) ** 2):,} "
    f"({int(2 * (Z80 * sd1 / 0.40) ** 2):,}) eventi per lato")

T.to_csv(HERE / "q1_celle.csv", index=False)
pd.concat([dfA, dfB]).to_csv(HERE / "q2_regola.csv", index=False)
(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
