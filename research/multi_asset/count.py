"""Multi-asset · fase 1: conta gli eventi (trade) di ogni regola per asset, SENZA calcolare rendimenti.
Uscita: conteggi.txt e conteggi.csv. Per ogni regola: trade sul periodo intero e in ciascun sottoperiodo (simulazione
indipendente che parte flat all'inizio del sottoperiodo), più la soglia DVOL equivalente (parametro, non risultato)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ma_lib as M  # noqa: E402
import p2_engine as E  # noqa: E402

OUT = M.HERE
rows, lines = [], []


def log(s=""):
    print(s)
    lines.append(s)


def nper(fn, f, periods, start0, cut):
    """Conteggi: intero (da start0) + sottoperiodi con >= 3 anni testabili (altrimenti None)."""
    out = {"tot": fn(start0, cut)}
    for p, (a, b) in periods.items():
        a = max(pd.Timestamp(a), start0)
        out[p] = fn(a, b) if (pd.Timestamp(b) - a).days >= 3 * 365 else None
    out["dal2021"] = fn(max(pd.Timestamp("2021-01-01"), start0), cut)
    return out


vix = M.load_vix()
log("Soglie VIX → percentile nello storico VIX 1990–2020 → soglia DVOL (storico DVOL 2021-03-24 → 2026-11-17)")
btc = M.load_btc()
dvol = btc["dvol"]["close"]
thr_d = {}
for t in (30, 34, 38):
    q, d = M.dvol_threshold(t, dvol, vix)
    thr_d[t] = round(d, 1)
    log(f"  VIX {t}: percentile {q*100:.2f}% → DVOL {d:.1f}")
log()
log("Incroci al rialzo della soglia (eventi grezzi, prima del filtro 'solo se flat')")
log(f"  VIX 1991→{M.CUT}: " + ", ".join(f"{t}: {M.vix_crossings(vix, t, '1991-01-01')}" for t in (30, 34, 38)))
log(f"  VIX 2021→{M.BTC_CUT}: " + ", ".join(f"{t}: {M.vix_crossings(vix, t, '2021-01-01', M.BTC_CUT)}" for t in (30, 34, 38)))
log(f"  DVOL 2021→{M.BTC_CUT}: " + ", ".join(f"{t}→{thr_d[t]}: {M.vix_crossings(dvol, thr_d[t], '2021-01-01', M.BTC_CUT)}" for t in (30, 34, 38)))
log()


def n_s1(f, long_only, k=2.5):
    def g(a, b):
        r = M.s1_sim(f, a, b, long_only=long_only, k=k, wb=wb)
        return len(r["trades"]) + (1 if r["open"] else 0)
    return g


def n_ema(close, vol, use_vix, **kw):
    def g(a, b):
        t = M.ema_vix(close, vol, a, b, use_vix=use_vix, **kw)
        return f"{len(t)}({sum(x['origin'] == 'vix' for x in t)}v)" if use_vix else len(t)
    return g


hdr = f"{'asset':7s} {'dati da':10s} {'test da':10s} | {'regola':16s} | {'tot':>8s} {'A 00-10':>8s} {'B 11-20':>8s} {'C 21-oggi':>9s}"
log("Trade per regola (parametri principali). S3: n(di cui ingressi VIX). '-' = sottoperiodo con < 3 anni testabili")
log(hdr)
for name in M.MAIN + M.DOW:
    f = M.load(name)
    wb = M.s1_weekly(f)
    s0, s0v = M.test_start(f), M.test_start(f, True)
    rules = [("S1 long/short", n_s1(f, False), s0), ("S1 solo long", n_s1(f, True), s0),
             ("S2 EMA200", n_ema(f["close"], None, False), s0), ("S3 EMA200+VIX", n_ema(f["close"], vix, True), s0v)]
    for rn, fn, st in rules:
        c = nper(fn, f, M.PERIODS, st, M.CUT)
        rows.append(dict(asset=name, group="main" if name in M.MAIN else "dow2000", rule=rn, start=str(st.date()), **c))
        fmt = lambda x: "-" if x is None else str(x)  # noqa: E731
        log(f"{name:7s} {str(f.index[0].date()):10s} {str(st.date()):10s} | {rn:16s} | {fmt(c['tot']):>8s} {fmt(c['A']):>8s} "
            f"{fmt(c['B']):>8s} {fmt(c['C']):>9s}")
    if name == M.MAIN[-1]:
        log("--- controllo: componenti Dow Jones al 01/01/2000 con storia continua ---")

# ---------------------------------------------------------------- BTC dal 2021
log()
log("BTC dal 2021 (sottoperiodi 2021–22 / 2023–24 / 2025–oggi)")
f = btc["f"]
bclose = f["close"]
dv = dvol


def bt(fn):
    out = {"tot": fn("2021-01-01", M.BTC_CUT)}
    for p, (a, b) in M.BTC_PERIODS.items():
        out[p] = fn(a, b)
    return out


def n_w(rr):
    return len(rr["trades"]) + (1 if rr["open"] else 0)


w31 = E.simulate(f)
lst = [("W3.1 (riferimento)", lambda a, b: n_w(E.simulate(f, start=a, end=b))),
       ("S1 long/short", lambda a, b: n_w(M.s1_btc(f, a, b))),
       ("S1 solo long", lambda a, b: n_w(M.s1_btc(f, a, b, long_only=True))),
       ("S2 EMA200", n_ema(bclose, None, False)),
       ("S3 VIX 34", n_ema(bclose, vix, True)),
       (f"S3 DVOL {thr_d[34]}", n_ema(bclose, dv, True, thr=thr_d[34]))]
for rn, fn in lst:
    c = bt(fn)
    rows.append(dict(asset="BTC", group="btc", rule=rn, start="2021-01-01", **c))
    log(f"{'BTC':7s} {rn:22s} | tot {c['tot']!s:>8s} | A {c['A']!s:>7s} B {c['B']!s:>7s} C {c['C']!s:>7s}")

# V6/V7: ingressi "panic" quando W3.1 è flat (né in posizione né con un ingresso in sospeso)
busy = pd.Series(False, index=f.index)
for t in w31["trades"] + ([w31["open"]] if w31["open"] else []):
    busy.loc[pd.Timestamp(t["signal"]):pd.Timestamp(t.get("exit") or f.index[-1])] = True
w_entries = sorted(pd.Timestamp(t["entry"]) for t in w31["trades"] + ([w31["open"]] if w31["open"] else []))
for lab, vol, thr in (("V6 W3.1+panic VIX 34", vix, 34.0), (f"V7 W3.1+panic DVOL {thr_d[34]}", dv, thr_d[34])):
    raw = M.ema_vix(bclose, vol, "2021-01-01", M.BTC_CUT, thr=thr)
    pan = [t for t in raw if t["origin"] == "vix" and not busy.get(t["entry"], False)]
    cut = sum(any(t["entry"] < e <= (t["exit"] or f.index[-1]) for e in w_entries) for t in pan)
    rows.append(dict(asset="BTC", group="btc", rule=lab, start="2021-01-01", tot=len(pan)))
    log(f"BTC     {lab:22s} | trade panic aggiunti {len(pan)} (di cui troncati da un ingresso W3.1: {cut}); "
        f"date: {', '.join(str(t['entry'].date()) for t in pan)}")

# V8: W3.1 con filtro EMA200D (long solo sopra, short solo sotto, alla chiusura della domenica di decisione)
e200 = bclose.ewm(span=200, adjust=False).mean()
r8 = E.simulate(f, allow=lambda side, day: (bclose[day] > e200[day]) if side > 0 else (bclose[day] < e200[day]))
blk = [e for e in r8["events"] if e["kind"] == "blocked"]
rows.append(dict(asset="BTC", group="btc", rule="V8 W3.1 filtro EMA200D", start="2021-01-01", tot=n_w(r8)))
log(f"BTC     V8 W3.1 filtro EMA200D   | trade {n_w(r8)} (W3.1: {n_w(w31)}); domeniche bloccate {len(blk)} "
    f"(lati: {sum(e['side'] > 0 for e in blk)} long, {sum(e['side'] < 0 for e in blk)} short)")

pd.DataFrame(rows).to_csv(OUT / "conteggi.csv", index=False)
(OUT / "conteggi.txt").write_text("\n".join(lines) + "\n")
