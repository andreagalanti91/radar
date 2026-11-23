"""Esegue PREREG.md (commit 9e437db). Output: risultati.txt, varianti.csv, eventi_trade.csv, eventi_mercato.csv, placebo.csv,
trade_delta.csv, vicini.csv. Uso: python3 cs_run.py"""
from __future__ import annotations

import itertools
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import cs_engine as E  # noqa: E402
import cs_lib as L  # noqa: E402
from cs_lib import W  # noqa: E402

SEED, N_PLA, HERE = 20261123, 500, L.HERE
D1, D3 = dict(rA=2, vr=2), dict(eA=1.25, vr=2, tail=0.5)
FB, FL, FE = L.btc(), L.btc_long(), L.eth()
XB, XL, XE = L.feats(FB), L.feats(FL), L.feats(FE)
PER = {"ALL": (FB, XB, "2021-01-01", None), "IS": (FB, XB, "2021-01-01", "2023-12-31"), "OOS": (FB, XB, "2024-01-01", None),
       "L": (FL, XL, "2018-01-01", "2020-12-31"), "ETH": (FE, XE, "2021-01-01", None)}
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def tg(x, d):
    return (L.trig(x, d, "L"), L.trig(x, d, "S"))


# variante = funzione (x, windows) -> cfg
VAR = {"C1 D1 tutto R1": lambda x, w: dict(trig=tg(x, D1)),
       "C2 D1 tutto R2 5%": lambda x, w: dict(trig=tg(x, D1), reentry=("R2", 0.05)),
       "C3 D1 tutto R3": lambda x, w: dict(trig=tg(x, D1), reentry="R3", windows=w),
       "C4 D1 metà": lambda x, w: dict(trig=tg(x, D1), frac=0.5),
       "C5 D3 tutto R1": lambda x, w: dict(trig=tg(x, D3)),
       "C6 LIM 2ATR tutto R1": lambda x, w: dict(lim=2.0)}
EVDEF = {"C1 D1 tutto R1": D1, "C2 D1 tutto R2 5%": D1, "C3 D1 tutto R3": D1, "C4 D1 metà": D1, "C5 D3 tutto R1": D3,
         "C6 LIM 2ATR tutto R1": dict(eA=2.0)}
NEIGH = {"C1 D1 tutto R1": {"rA1,5": dict(rA=1.5, vr=2), "rA2,5": dict(rA=2.5, vr=2), "vr1,5": dict(rA=2, vr=1.5),
                            "vr2,5": dict(rA=2, vr=2.5), "rP7%": dict(rP=0.07, vr=2)},
         "C5 D3 tutto R1": {"eA1": dict(eA=1, vr=2, tail=0.5), "eA1,5": dict(eA=1.5, vr=2, tail=0.5), "eA2": dict(eA=2, vr=2, tail=0.5),
                            "tail1/3": dict(eA=1.25, vr=2, tail=1 / 3), "vr1,5": dict(eA=1.25, vr=1.5, tail=0.5)}}


def tl(r):
    return list(r["trades"]) + ([dict(r["open"], pnl=r["open"]["pnl_close"], exit=None)] if r["open"] else [])


def windows(r):
    return [(t["entry"], t.get("exit")) for t in tl(r)]


def run(cfgfn, per, base=None):
    f, x, s, e = PER[per]
    cfg = cfgfn(x, windows(base) if base else []) if callable(cfgfn) else cfgfn
    return E.simulate(f, cfg, start=s, end=e)


def met(r):
    e = r["equity"] / r["equity"].iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1)
    pn = np.array([t["pnl"] for t in tl(r)])
    return dict(final=round(10000 * float(e.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1),
                cdd=round(cagr / abs(dd), 3), n=len(pn), wr=round(100 * float((pn > 0).mean()), 1),
                worst=round(100 * float(pn.min()), 1), wo_best=round(10000 * float(e.iloc[-1]) / (1 + pn.max())), n_ev=r["n_ev"])


def bh(per):
    f, _, s, e = PER[per]
    x = f[(f.index >= s) & ((f.index <= e) if e else True)]
    eq = x["close"] / (x["open"].iloc[0] * (1 + W.SLIP) * (1 + W.FEE_SPOT))
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    dd = float((eq / eq.cummax() - 1).min())
    cagr = float(eq.iloc[-1] ** (1 / yrs) - 1)
    return dict(final=round(10000 * float(eq.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1), cdd=round(cagr / abs(dd), 3))


def groups(rv, rb):
    bt, vt = tl(rb), tl(rv)
    out, used = {}, set()
    for b in bt:
        lo, hi = b["signal"], b["exit"] or "9999"
        lv = 0.0
        for j, v in enumerate(vt):
            if lo <= v["signal"] <= hi:
                lv += np.log1p(v["pnl"])
                used.add(j)
        out[b["signal"]] = lv - np.log1p(b["pnl"])
    for j, v in enumerate(vt):
        if j not in used:
            out["nuovo " + v["signal"]] = np.log1p(v["pnl"])
    return out


def signflip(x):
    x = np.array([v for v in x if abs(v) > 1e-12])
    m = len(x)
    if m == 0:
        return 1.0, 0
    s = np.array(list(itertools.product([1, -1], repeat=m))) @ np.abs(x) if m <= 20 else None
    return float((s >= x.sum() - 1e-12).mean()), m


def held(f, x, rb, d, s, e):
    """Giorni tenuti da W3.2 con lato, trade, guadagno aperto in chiusura e bandiera evento (definizione d)."""
    rows = []
    for k, t in enumerate(tl(rb)):
        sd = 1 if t["side"] == "long" else -1
        a = pd.Timestamp(t["entry"])
        b = pd.Timestamp(t["exit"]) - pd.Timedelta(days=1) if t.get("exit") else (pd.Timestamp(e) if e else f.index[-1])
        g = f.loc[a:b]
        ev = L.trig(x, d, "L" if sd > 0 else "S").reindex(g.index)
        for day, cl, v in zip(g.index, g["close"], ev):
            rows.append(dict(day=day, trade=k, signal=t["signal"], side=sd, gain=sd * (cl / t["entry_px"] - 1), ev=bool(v)))
    return pd.DataFrame(rows)


# ================= 1. Descrittivo: cascate a favore dentro i trade W3.2 =================
base = {p: run({}, p) for p in PER}
bm = {p: met(base[p]) for p in PER}
say("== W3.2 riprodotta:", {p: (bm[p]["final"], bm[p]["dd"], bm[p]["n"], bm[p]["wr"]) for p in PER})
erows = []
for lab, per in (("BTC 2021+", "ALL"), ("BTC 2018-20", "L"), ("ETH 2021+", "ETH")):
    f, x, s, e = PER[per]
    O, H, Lo, C = f["open"], f["high"], f["low"], f["close"]
    for dn, d in (("D1", D1), ("D3", D3)):
        hd = held(f, x, base[per], d, s, e)
        ev = hd[hd.ev]
        for _, r in ev.iterrows():
            t = tl(base[per])[int(r.trade)]
            sd, i = int(r.side), f.index.get_loc(r.day)
            if i + 1 >= len(f):
                continue
            xp = O.iloc[i + 1]
            fw = {h: (sd * (C.iloc[i + h] / xp - 1) if i + h < len(f) else np.nan) for h in (3, 7, 14)}
            end = pd.Timestamp(t["exit"]) if t.get("exit") else (pd.Timestamp(e) + pd.Timedelta(days=1) if e else f.index[-1])
            aft = f.loc[f.index[i + 1]:end - pd.Timedelta(days=1)]
            ext_day = H.iloc[i] if sd > 0 else Lo.iloc[i]
            b_in = len(aft) > 0 and ((aft["high"].max() > ext_day) if sd > 0 else (aft["low"].min() < ext_day))
            b_cl = len(aft) > 0 and ((aft["close"].max() > C.iloc[i]) if sd > 0 else (aft["close"].min() < C.iloc[i]))
            mfe_after = (sd * ((aft["high"].max() if sd > 0 else aft["low"].min()) / xp - 1)) if len(aft) else np.nan
            w32 = sd * (t["exit_px"] / xp - 1) if t.get("exit") else np.nan
            erows.append(dict(campione=lab, definizione=dn, giorno=str(r.day.date()), trade=r.signal, lato="long" if sd > 0 else "short",
                              guadagno_aperto=round(100 * r.gain, 1), rA=round(float(x.loc[r.day, f"rA_{'L' if sd > 0 else 'S'}"]), 2),
                              vr=round(float(x.loc[r.day, "vr"]), 2), prezzo_uscita=round(xp, 1),
                              f3=round(100 * fw[3], 1), f7=round(100 * fw[7], 1), f14=round(100 * fw[14], 1),
                              estremo_migliore_intra=bool(b_in), estremo_migliore_chiusura=bool(b_cl),
                              mfe_dopo=round(100 * mfe_after, 1), w32_dopo=round(100 * w32, 1), uscita_w32=t.get("exit")))
ev_df = pd.DataFrame(erows)
ev_df.to_csv(HERE / "eventi_trade.csv", index=False)
say("\n== 1. Cascate a favore dentro i trade W3.2 (movimento nel verso del trade dall'apertura successiva; >0 prosegue, <0 rimbalza)")
say(ev_df[ev_df.campione == "BTC 2021+"].drop(columns=["campione"]).to_string(index=False))
for (cmp_, dn), g in ev_df.groupby(["campione", "definizione"], sort=False):
    say(f"{cmp_} {dn}: n {len(g)} in {g.trade.nunique()} trade | media 3/7/14 g {g.f3.mean():+.1f}/{g.f7.mean():+.1f}/{g.f14.mean():+.1f}"
        f" | mediana {g.f3.median():+.1f}/{g.f7.median():+.1f}/{g.f14.median():+.1f}"
        f" | prosegue (>0) {int((g.f3 > 0).sum())}/{int((g.f7 > 0).sum())}/{int((g.f14 > 0).sum())}"
        f" | estremo migliore dopo: intra {int(g.estremo_migliore_intra.sum())}/{len(g)}, chiusura {int(g.estremo_migliore_chiusura.sum())}/{len(g)}"
        f" | W3.2 esce meglio dell'apertura successiva {int((g.w32_dopo > 0).sum())}/{int(g.w32_dopo.notna().sum())}"
        f" (media {g.w32_dopo.mean():+.1f}, mediana {g.w32_dopo.median():+.1f})")

# ================= 2. Varianti =================
say("\n== 2. Risultati (10.000 $, IS/OOS/2018-20/ETH ripartono da 10.000 $)")
rows, res = [], {}
for nm in ["W3.2"] + list(VAR):
    rr = base if nm == "W3.2" else {p: run(VAR[nm], p, base[p]) for p in PER}
    res[nm] = rr
    m = {p: (bm[p] if nm == "W3.2" else met(rr[p])) for p in PER}
    rows.append(dict(variante=nm, **{f"{p}_{k}": v for p in PER for k, v in m[p].items()}))
    a = m["ALL"]
    say(f"{nm:22s} fin {a['final']:>6} CAGR {a['cagr']:5.1f} DD {a['dd']:6.1f} C/DD {a['cdd']:.3f} n {a['n']:2d} WR {a['wr']:5.1f} peg {a['worst']:5.1f}"
        f" usc {a['n_ev']:2d} sMigl {a['wo_best']:>6} | IS {m['IS']['final']}/{m['IS']['cdd']:.3f} OOS {m['OOS']['final']}/{m['OOS']['cdd']:.3f}"
        f" | 18-20 {m['L']['final']}/{m['L']['dd']}/{m['L']['cdd']:.3f} usc {m['L']['n_ev']} | ETH {m['ETH']['final']}/{m['ETH']['dd']}/{m['ETH']['cdd']:.3f} usc {m['ETH']['n_ev']}")
for p in PER:
    say(f"Buy & hold {p}: {bh(p)}")
pd.DataFrame(rows).to_csv(HERE / "varianti.csv", index=False)

say("\n== Criteri")
pv, crit, trows = {}, {}, []
for nm in VAR:
    m = {p: met(res[nm][p]) for p in PER}
    g = groups(res[nm]["ALL"], base["ALL"])
    for k, v in g.items():
        trows.append(dict(variante=nm, trade=k, delta_log_pct=round(100 * v, 2)))
    dl = np.array(list(g.values()))
    p, nz = signflip(dl)
    pv[nm] = p
    c1 = m["IS"]["cdd"] > bm["IS"]["cdd"] and m["OOS"]["cdd"] > bm["OOS"]["cdd"]
    c2 = m["L"]["cdd"] >= bm["L"]["cdd"]
    c3 = m["ALL"]["dd"] >= -30
    c4 = m["ALL"]["wr"] >= 70
    c5 = float(np.sort(dl)[:-2].sum()) > 0
    c8 = m["ETH"]["cdd"] >= bm["ETH"]["cdd"]
    crit[nm] = dict(c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c8=c8)
    say(f"{nm}: c1 IS/OOS {c1} | c2 2018-20 {c2} | c3 DD {c3} | c4 WR {c4} | c5 senza 2 Δ migliori {c5} (ΣΔ {100*dl.sum():+.1f}, senza 2 "
        f"{100*np.sort(dl)[:-2].sum():+.1f} punti log; Δ>0 {int((dl > 1e-12).sum())}, Δ<0 {int((dl < -1e-12).sum())}) | segni p {p:.3f} (non nulli {nz}) | c8 ETH {c8}")
pd.DataFrame(trows).to_csv(HERE / "trade_delta.csv", index=False)
order = sorted(pv, key=pv.get)
holm = {}
for i, nm in enumerate(order):
    holm[nm] = pv[nm] <= 0.05 / (len(order) - i) and all(holm[o] for o in order[:i])
say("Holm:", {k: (round(pv[k], 3), holm[k]) for k in order})

say("\n== Placebo (uscita in un giorno a caso dello stesso trade, non di cascata, con guadagno aperto entro ±5 punti; 500 ripetizioni)")
pla = []
f, x, s, e = PER["ALL"]
for nm in VAR:
    cfg0 = VAR[nm](x, windows(base["ALL"]))
    hd = held(f, x, base["ALL"], EVDEF[nm], s, e)
    evs = hd[hd.ev]
    if cfg0.get("frac", 1.0) < 1:
        evs = evs.groupby("trade").head(1)
    rng = np.random.default_rng(SEED)
    obs = met(res[nm]["ALL"])["cdd"]
    vals, fins = [], []
    for _ in range(N_PLA):
        days = set()
        for _, r in evs.iterrows():
            cand = hd[(hd.trade == r.trade) & (~hd.ev)]
            band = cand[(cand.gain - r.gain).abs() <= 0.05]
            if len(band) == 0:
                band = cand.iloc[(cand.gain - r.gain).abs().argsort()[:5]]
            days.add(band.day.iloc[int(rng.integers(len(band)))])
        c2 = {k: v for k, v in cfg0.items() if k not in ("trig", "lim")}
        mm = met(E.simulate(f, dict(c2, force=days), start=s, end=e))
        vals.append(mm["cdd"])
        fins.append(mm["final"])
    vals = np.array(vals)
    pp = float((vals >= obs).mean())
    pla.append(dict(variante=nm, eventi=len(evs), osservato=obs, mediana=round(float(np.median(vals)), 3),
                    finale_mediano=int(np.median(fins)), p=pp))
    crit[nm].update(c6=holm[nm], c7=pp < 0.05)
    say(f"{nm}: eventi {len(evs)} | C/DD {obs:.3f} | placebo mediana {np.median(vals):.3f} (5–95% {np.percentile(vals, 5):.3f}–{np.percentile(vals, 95):.3f}),"
        f" finale mediano {int(np.median(fins))} | p {pp:.3f}")
pd.DataFrame(pla).to_csv(HERE / "placebo.csv", index=False)

say("\n== Vicini (2021+ finale/DD/C/DD/WR · IS · OOS · 2018-20 · ETH C/DD)")
nrows = []


def neigh(nm, lab, cfgfn):
    m = {p: met(run(cfgfn, p, base[p])) for p in PER}
    nrows.append(dict(variante=nm, vicino=lab, **{f"{p}_{k}": m[p][k] for p in PER for k in ("final", "dd", "cdd", "wr", "n_ev")}))
    say(f"{nm} · {lab}: fin {m['ALL']['final']} DD {m['ALL']['dd']} C/DD {m['ALL']['cdd']} WR {m['ALL']['wr']} usc {m['ALL']['n_ev']} | IS {m['IS']['cdd']}"
        f" OOS {m['OOS']['cdd']} 18-20 {m['L']['cdd']} ETH {m['ETH']['cdd']}")


for nm, nb in NEIGH.items():
    for lab, d in nb.items():
        neigh(nm, lab, lambda x, w, d=d: dict(trig=tg(x, d)))
for X in (0.03, 0.08):
    neigh("C2 D1 tutto R2 5%", f"X {X:.0%}", lambda x, w, X=X: dict(trig=tg(x, D1), reentry=("R2", X)))
for k in (1.25, 1.5, 2.5):
    neigh("C6 LIM 2ATR tutto R1", f"k {k}", lambda x, w, k=k: dict(lim=k))
pd.DataFrame(nrows).to_csv(HERE / "vicini.csv", index=False)
say(f"W3.2 C/DD: ALL {bm['ALL']['cdd']} IS {bm['IS']['cdd']} OOS {bm['OOS']['cdd']} 18-20 {bm['L']['cdd']} ETH {bm['ETH']['cdd']}")

say("\n== Verdetto per variante (c1 IS/OOS, c2 2018-20, c3 DD, c4 WR, c5 ≤2 trade, c6 Holm, c7 placebo, c8 ETH)")
for nm, c in crit.items():
    say(f"{nm}: {'PASSA' if all(c.values()) else 'NON PASSA'} {[k for k in sorted(c) if c[k]]} veri, {[k for k in sorted(c) if not c[k]]} falsi")

say("\n== Trade delle varianti C1 e C5 (2021+)")
for nm in ("C1 D1 tutto R1", "C5 D3 tutto R1"):
    for t in tl(res[nm]["ALL"]):
        say(f"{nm[:2]} {t['signal']} {t['side']:5s} {t['entry']}→{t.get('exit')} {t.get('reason', 'aperto'):7s} {t.get('kind')} move {100*t['move']:+.1f} pnl {100*t['pnl']:+.1f}")
say("W3.2:")
for t in tl(base["ALL"]):
    say(f"   {t['signal']} {t['side']:5s} {t['entry']}→{t.get('exit')} {t.get('reason', 'aperto'):7s} move {100*t['move']:+.1f} pnl {100*t['pnl']:+.1f}")

# ================= 3. Test evento generale =================
say("\n== 3. Test evento: dopo una cascata (primo giorno, pausa 7 g) rendimento dall'apertura successiva alla chiusura a 3/7/14 g, in eccesso sulla media")
mrows = []


def events(m: pd.Series, pause=7):
    out, last = [], None
    for d in m.index[m.values]:
        if last is None or (d - last).days > pause:
            out.append(d)
        last = d
    return out


def evtest(lab, f, x, s, e, d, tag, seed):
    g = f.loc[s:e] if e else f.loc[s:]
    O, C = f["open"], f["close"]
    fw = {h: (C.shift(-h) / O.shift(-1) - 1).reindex(g.index) for h in (3, 7, 14)}
    m = L.trig(x, d, tag).reindex(g.index).fillna(False)
    ev = events(m)
    res_ = dict(campione=lab, lato="ribasso" if tag == "S" else "rialzo", n=len(ev))
    rng = np.random.default_rng(seed)
    pos = np.arange(len(g) - 14)
    draws = []
    while len(draws) < 10000 and len(ev) >= 3:
        pk = np.sort(rng.choice(pos, size=len(ev), replace=False))
        if len(pk) > 1 and np.diff(pk).min() <= 7:
            continue
        draws.append(pk)
    for h in (3, 7, 14):
        v = fw[h].reindex(ev).dropna()
        allm = float(fw[h].mean())
        eff = float(v.mean() - allm) if len(v) else np.nan
        p = np.nan
        if draws:
            a = fw[h].to_numpy()
            dm = np.array([np.nanmean(a[pk]) for pk in draws]) - allm
            p = float((np.abs(dm) >= abs(eff) - 1e-12).mean())
        res_.update({f"media{h}": round(100 * float(v.mean()), 2) if len(v) else np.nan, f"eccesso{h}": round(100 * eff, 2),
                     f"mediana{h}": round(100 * float(v.median()), 2) if len(v) else np.nan,
                     f"pos{h}": f"{int((v > 0).sum())}/{len(v)}", f"p{h}": round(p, 3), f"tutti{h}": round(100 * allm, 2)})
    return res_, ev


for dn, d in (("D1", D1), ("D3", D3)):
    for tag in ("S", "L"):
        for lab, (f, x, s, e) in {"BTC 2021+": (FB, XB, "2021-01-01", None), "BTC 2021-23": (FB, XB, "2021-01-01", "2023-12-31"),
                                  "BTC 2024-26": (FB, XB, "2024-01-01", None), "BTC 2018-20": (FL, XL, "2018-01-01", "2020-12-31"),
                                  "ETH 2021+": (FE, XE, "2021-01-01", None)}.items():
            r, ev = evtest(lab, f, x, s, e, d, tag, SEED)
            r = dict(definizione=dn, **r)
            mrows.append(r)
            say(f"{dn} {r['lato']:7s} {lab:11s} n {r['n']:2d} | media 3/7/14 {r['media3']:+.2f}/{r['media7']:+.2f}/{r['media14']:+.2f} (tutti i giorni {r['tutti3']:+.2f}/{r['tutti7']:+.2f}/{r['tutti14']:+.2f})"
                f" | eccesso {r['eccesso3']:+.2f}/{r['eccesso7']:+.2f}/{r['eccesso14']:+.2f} | p {r['p3']}/{r['p7']}/{r['p14']} | >0 {r['pos3']} {r['pos7']} {r['pos14']} | mediana 7 g {r['mediana7']:+.2f}")
            if lab == "BTC 2021+" and tag == "S":
                say("     giorni:", ", ".join(str(t.date()) for t in ev))
pd.DataFrame(mrows).to_csv(HERE / "eventi_mercato.csv", index=False)
pm = sorted([(r["p7"], r["definizione"]) for r in mrows if r["campione"] == "BTC 2021+" and r["lato"] == "ribasso"])
say(f"Holm sui 2 test primari (ribasso, 7 g, BTC 2021+): {pm} → soglie 0,025 / 0,05: {'nessuno passa' if pm[0][0] > 0.025 else 'da verificare'}")
for nm, nb in (("D1", {"rA1,5": dict(rA=1.5, vr=2), "vr1,5": dict(rA=2, vr=1.5), "rP7%": dict(rP=0.07, vr=2), "senza volume": dict(rA=2)}),
               ("D3", {"eA1,5": dict(eA=1.5, vr=2, tail=0.5), "eA2": dict(eA=2, vr=2, tail=0.5), "tail1/3": dict(eA=1.25, vr=2, tail=1 / 3),
                       "vr1,5": dict(eA=1.25, vr=1.5, tail=0.5), "senza volume": dict(eA=1.25, tail=0.5)})):
    for lab, d in nb.items():
        r, _ = evtest("BTC 2021+", FB, XB, "2021-01-01", None, d, "S", SEED)
        say(f"vicino {nm} {lab}: n {r['n']} eccesso 3/7/14 {r['eccesso3']:+.2f}/{r['eccesso7']:+.2f}/{r['eccesso14']:+.2f} p {r['p3']}/{r['p7']}/{r['p14']}")
(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
