"""Parte 2 · fase 1: CONTA gli eventi che ogni regola candidata produce (lezione 98). Stampa SOLO conteggi:
nessun capitale, rendimento, drawdown o esito di trade. Le definizioni sono quelle di PREREG.md (sezione 4)."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from p2_data import load  # noqa: E402
import p2_engine as E  # noqa: E402
from radar import weekly as W  # noqa: E402

d = load()
F, FL = d["f"], d["fl"]
PER = {"2021–23": (F, "2021-01-01", "2023-12-31"), "2024–26": (F, "2024-01-01", None), "2018–20": (FL, "2018-01-01", "2020-12-31")}

# ---------------------------------------------------------------- serie esterne (valore noto alla decisione della domenica)
dv = d["dvol"]["close"]
dvz = (dv - dv.rolling(180, min_periods=90).mean()) / dv.rolling(180, min_periods=90).std()
o = d["opt"]
skew = (o["pw_iv"] - o["cw_iv"]).where((o["pw_btc"] >= 10) & (o["cw_btc"] >= 10))
skz = (skew - skew.rolling(26, min_periods=13).mean().shift(1)) / skew.rolling(26, min_periods=13).std().shift(1)
eb = d["ethbtc"]["close"].resample("W-SUN").last()
bd = d["btcdom"]["close"].resample("W-SUN").last()
lr = np.log(FL["close"]).diff()
vol30 = lr.rolling(30).std() * np.sqrt(365)


def at(s: pd.Series, day):
    v = s.get(day, np.nan)
    return np.nan if pd.isna(v) else float(v)


vrp = dv / (vol30 * 100).reindex(dv.index)          # premio della volatilità implicita: DVOL / vol. realizzata 30 g


def f_vrp(T):
    return lambda side, day: not (at(vrp, day) > T)


def f_skew(T):
    def a(side, day):
        x = at(skew, day)
        return not ((side > 0 and x > T) or (side < 0 and x < -T))
    return a


def f_rot(series, n, dom_up_when_below):
    ema = series.ewm(span=n, adjust=False, min_periods=n).mean()
    def a(side, day):
        x, m = at(series, day), at(ema, day)
        if np.isnan(x) or np.isnan(m):
            return True
        return x < m if dom_up_when_below else x > m
    return a


def vt_expo(target):
    def e(side, wk, day):
        v = at(vol30, day)
        return 1.0 if np.isnan(v) else min(1.0, target / v)
    return e


def vt_rebal(target):
    def r(side, wk, day, tr):
        v = at(vol30, day)
        return None if np.isnan(v) else min(1.0, target / v)
    return r


def risk_expo(r, k):
    return lambda side, wk, day: min(1.0, r / (k * wk["atr"] / wk["close"]))


def keyset(res):
    tt = res["trades"] + ([res["open"]] if res["open"] else [])
    return {(t["signal"], t["side"]) for t in tt}


def run(per, **kw):
    x, s, e = PER[per]
    return E.simulate(x, start=s, end=e, **kw)


BASE = {p: run(p) for p in PER}


def count_filter(name, mk, params):
    for prm in params:
        cells = []
        for p in PER:
            r = run(p, allow=mk(prm))
            nb = sum(ev["kind"] == "blocked" for ev in r["events"])
            b, a = keyset(BASE[p]), keyset(r)
            cells.append(f"{p}: domeniche bloccate {nb:2d}, trade W3 tolti {len(b - a)}, nuovi {len(a - b)}")
        print(f"{name}({prm}) | " + " | ".join(cells))


print("W3 trade per periodo:", {p: len(keyset(BASE[p])) for p in PER})
print("\n# F1 · O1 filtro premio IV: DVOL/vol30 > T blocca ogni ingresso (DVOL dal 24/03/2021; 2018–20 non testabile)")
count_filter("O1", f_vrp, [1.2, 1.1, 1.4])
print("\n# F1 · O3 filtro skew (IV put OTM − IV call OTM, punti di vol): long bloccati se skew > T, short se skew < −T")
count_filter("O3", f_skew, [0.0, 1.0, 2.0])
print("   [solo informativo, scartato per assenza di eventi] DVOL z180 > T:")
count_filter("O1-scartato z180", lambda T: (lambda side, day: not (at(dvz, day) > T)), [1.5, 1.0, 2.0])
print("\n# F3 · R1 ETHBTC: ingressi W3 solo se ETHBTC < EMA n settimane (dominanza BTC in salita)")
count_filter("R1", lambda n: f_rot(eb, n, True), [20, 10, 40])
print("\n# F3 · R2 BTCDOM (Binance, dal 21/06/2021): ingressi W3 solo se BTCDOM > EMA n settimane")
count_filter("R2", lambda n: f_rot(bd, n, False), [20, 10, 40])
both = pd.concat([np.log(eb).diff(), np.log(bd).diff()], axis=1).dropna()
print(f"   correlazione delle variazioni settimanali log ETHBTC/BTCDOM: {both.corr().iloc[0, 1]:.2f} (n={len(both)})")

print("\n# F1 · O2 autonomo 'picco di DVOL rientrato': domeniche-segnale e trade non sovrapposti (occupazione = durata)")
sun = dvz.resample("W-SUN").last()
for S, Rr, H in ((2.0, 1.5, 4), (1.5, 1.0, 4), (2.0, 1.0, 8)):
    sig = (sun.rolling(4).max().shift(1) >= S) & (sun <= Rr)
    busy, n = None, {}
    for dd in sig[sig].index:
        if busy is None or dd > busy:
            busy = dd + pd.Timedelta(weeks=H)
            key = "2021–23" if dd.year <= 2023 else "2024–26"
            n[key] = n.get(key, 0) + 1
    print(f"O2(picco {S}, rientro {Rr}, {H} sett.) | domeniche-segnale {int(sig.sum())} | trade: {n}")
print("   [informativo] episodi indipendenti di DVOL z180 >= 2 dal 2021:",
      int(((sun >= 2) & ~(sun.shift(1) >= 2)).sum()))

print("\n# F2 · V vol targeting settimanale (esposizione = min(1, target/vol30)): ribilanciamenti >= 0,10")
for tgt in (0.5, 0.4, 0.6):
    cells = []
    for p in PER:
        r = run(p, expo_fn=vt_expo(tgt), rebal_fn=vt_rebal(tgt))
        nreb = sum(ev["kind"] == "rebal" for ev in r["events"])
        ntr = len(keyset(r))
        cap = sum(ev["kind"] == "enter" and ev["to_expo"] < 0.999 for ev in r["events"])
        cells.append(f"{p}: trade {ntr}, ingressi sotto 1x {cap}, ribilanciamenti {nreb}")
    print(f"V({tgt:.0%}) | " + " | ".join(cells))

print("\n# F2 · G griglia rischio allo stop × distanza ATR × presa parziale (stessi segnali W3, max 1x)")
for k in (2.0, 2.5, 3.0):
    for rr in (0.05, 0.10, 0.15, 0.20, 0.25):
        cells = []
        for p in PER:
            r0 = run(p, expo_fn=risk_expo(rr, k), k=k)
            r1 = run(p, expo_fn=risk_expo(rr, k), k=k, tp=dict(levels=(2, 3), frac=1 / 3))
            ntr = len(keyset(r0))
            capb = sum(ev["kind"] == "enter" and ev["to_expo"] < 0.999 for ev in r0["events"])
            ntp = sum(ev["kind"] == "tp" for ev in r1["events"])
            cells.append(f"{p}: trade {ntr:2d}, sotto 1x {capb:2d}, prese parziali {ntp:2d}")
        print(f"G(r {rr:.0%}, k {k}) | " + " | ".join(cells))

print("\n# F4 · P1 piramidazione (base·E all'ingresso, aggiunte a +k1/+k2 ATRw dalla chiusura del segnale, stop comune)")
for nm, pyr in (("P1 base 1/3, +1/+2 ATR", dict(base=1 / 3, steps=(1.0, 2.0), adds=(1 / 3, 1 / 3))),
                ("vicino a: base 1/2, +1/+2 ATR", dict(base=0.5, steps=(1.0, 2.0), adds=(0.25, 0.25))),
                ("vicino b: base 1/3, +0,5/+1 ATR", dict(base=1 / 3, steps=(0.5, 1.0), adds=(1 / 3, 1 / 3)))):
    cells = []
    for p in PER:
        r = run(p, pyr=pyr)
        tt = r["trades"] + ([r["open"]] if r["open"] else [])
        a1 = sum(t.get("adds", 0) >= 1 for t in tt)
        a2 = sum(t.get("adds", 0) >= 2 for t in tt)
        cells.append(f"{p}: trade {len(tt)}, con 1ª aggiunta {a1}, con 2ª {a2}")
    print(f"{nm} | " + " | ".join(cells))
