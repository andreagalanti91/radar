"""Motore dello studio squeeze (PREREG.md): segnali orari da mappe senza look-ahead, trade con DCA/stop/target/tempo,
selezione una posizione alla volta, equity 10k a 1x, controlli (momentum, placebo, vicini) e integrazione W3.
Uso: python research/liq_squeeze/sq_bt.py  → risultati.txt, regole.csv, trade_*.csv, vicini.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
from radar import levels, weekly as W  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

WORK = Path("/tmp/radar-work/liqsqueeze")
FEE, THRU, SIG = 0.0008, 0.0005, 0.30
SPLIT = pd.Timestamp("2024-01-01")
START = pd.Timestamp("2021-01-22")
BASE = dict(thr=0.50, rad=6, H=120, cw=72, pct=0.20, clean="or")
N_RULES = 6

# ------------------------------------------------------------------ dati
h = pd.read_pickle(WORK / "h.pkl")
M = pd.read_pickle(WORK / "hmaps.pkl")
f = build_features(load_all()); f = f[f["close"].notna()]
O, Hh, Ll, C = (h[k].to_numpy(float) for k in ("open", "high", "low", "close"))
TI = h.index
NB = len(TI)
fund_day = f["funding"].reindex(TI.normalize()).ffill().fillna(0).to_numpy(float) / 24   # funding per ora
CF = np.r_[0.0, np.cumsum(fund_day)]                                                       # somma fino alla barra b esclusa

# ATR 4h (barre chiuse prima di T)
b4 = h[["open", "high", "low", "close"]].resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
tr4 = pd.concat([b4.high - b4.low, (b4.high - b4.close.shift()).abs(), (b4.low - b4.close.shift()).abs()], axis=1).max(axis=1)
atr4 = tr4.rolling(14).mean()
atr4.index = atr4.index + pd.Timedelta(hours=4)        # disponibile alla chiusura
ATR = atr4.reindex(M.index, method="ffill")

# supporti/resistenze del giorno prima
_LV = {}


def lv(day):
    if day not in _LV:
        _LV[day] = levels.compute(f[f.index < day])
    return _LV[day]


# ------------------------------------------------------------------ segnali
def imbalance(rad):
    s, l = M[f"S{rad}"], M[f"L{rad}"]
    return ((s - l) / (s + l)).where(s + l > 0, 0.0)


def cascades(side):
    """Ora j valida se: movimento ≥ 3% in ≤ 8 ore dalla partenza (regola liqcascade) e ≥ 2 fasce dense del lato liquidato
    (mappa all'ora di partenza) fra partenza ed estremo. Serie booleana sulle barre orarie (nota alla chiusura di j)."""
    BIN = 0.0025
    ok = np.zeros(NB, bool)
    Mi = M.index
    for j in range(NB):
        a = max(0, j - 7)
        seg = O[a:j + 1]
        if side == "long":
            ref = seg.max(); i = a + int(np.flatnonzero(seg >= ref * (1 - BIN)).max())
            ext = Ll[i:j + 1].min(); mv = ext / O[i] - 1
            if mv > -0.03:
                continue
        else:
            ref = seg.min(); i = a + int(np.flatnonzero(seg <= ref * (1 + BIN)).max())
            ext = Hh[i:j + 1].max(); mv = ext / O[i] - 1
            if mv < 0.03:
                continue
        T0 = TI[i]
        if T0 not in Mi:
            continue
        bands = M.at[T0, "dn" if side == "long" else "up"]
        if side == "long":
            n = sum(1 for b in bands if b[2] >= SIG and ext <= b[0] < O[i])
        else:
            n = sum(1 for b in bands if b[2] >= SIG and O[i] < b[0] <= ext)
        ok[j] = n >= 2
    return pd.Series(ok, TI)


def clean_flags(side, cw, pct, mode, casc, rad=6):
    """Pulizia all'ora T (dati fino a T−1)."""
    c = casc.astype(float).rolling(cw, min_periods=1).max().shift(1).reindex(M.index).fillna(0) > 0   # ore j in [T−cw, T−1]
    x = M[f"L{rad}"] if side == "long" else M[f"S{rad}"]
    q = x.shift(1).rolling(2160, min_periods=720).quantile(pct)
    p = x < q
    return {"or": c | p, "casc": c, "pct": p}[mode]


def r24():
    cl = pd.Series(C, TI)
    r = cl / cl.shift(24) - 1                     # r[j] = chiusura j / chiusura j−24
    return r.shift(1).reindex(M.index)           # alla decisione T: barra T−1


# ------------------------------------------------------------------ geometria e trade
def geometry(T, side):
    """F (fondo/tetto fascia DCA), stop, T1, T2 alla decisione T. None se non c'è T1."""
    r = M.loc[T]; p = r.p; a = ATR.get(T, np.nan)
    if not np.isfinite(a):
        return None
    L = lv(T.normalize())
    if side > 0:
        c = [b[0] for b in r.dn if b[2] >= SIG and p * 0.97 <= b[0] <= p * 0.99]
        c += [z["hi"] for z in L.get("supports", []) if p * 0.97 <= z["hi"] <= p * 0.99]
        F = max(c) if c else p * 0.97
        stop = F - a
        tg = [b[0] for b in r.up if b[2] >= SIG and b[0] >= p * 1.005]
    else:
        c = [b[0] for b in r.up if b[2] >= SIG and p * 1.01 <= b[0] <= p * 1.03]
        c += [z["lo"] for z in L.get("resistances", []) if p * 1.01 <= z["lo"] <= p * 1.03]
        F = min(c) if c else p * 1.03
        stop = F + a
        tg = [b[0] for b in r.dn if b[2] >= SIG and b[0] <= p * 0.995]
    if not tg:
        return None
    tg = sorted(tg, key=lambda x: abs(x - p))
    T1 = tg[0]
    T2 = next((x for x in tg[1:] if (x >= T1 * 1.005 if side > 0 else x <= T1 * 0.995)), None)
    return dict(p=p, F=F, stop=stop, T1=T1, T2=T2, atr=a)


def _first(mask, start=0):
    k = np.flatnonzero(mask[start:])
    return start + int(k[0]) if len(k) else None


def trade(T, side, mode, H, g=None):
    """Trade indipendente dalla decisione T. Ritorna dict con unità (peso, barra/prezzo di ingresso, barra/prezzo di uscita)
    e rendimento netto sul nozionale 1x, o None (niente geometria / nessun riempimento)."""
    g = g or geometry(T, side)
    if g is None:
        return None
    k = TI.searchsorted(T)
    if k >= NB or TI[k] != T:
        return None
    e = min(k + H, NB)                         # barre k..e−1
    o, hi, lo = O[k:e], Hh[k:e], Ll[k:e]
    n = e - k
    if side > 0:
        hit_stop = lo <= g["stop"]
        t1m = hi >= g["T1"] * (1 + THRU)
        t2m = hi >= g["T2"] * (1 + THRU) if g["T2"] else np.zeros(n, bool)
    else:
        hit_stop = hi >= g["stop"]
        t1m = lo <= g["T1"] * (1 - THRU)
        t2m = lo <= g["T2"] * (1 - THRU) if g["T2"] else np.zeros(n, bool)
    # ingressi
    if mode == "mkt":
        fills = [(1.0, 0, o[0])]
        first_fill = 0
        t1_from = 0
    else:
        p, F = g["p"], g["F"]
        lev = [p - (p - F) * x / 3 for x in (1, 2, 3)]
        fills = []
        for L_ in lev:
            m = (lo[:24] <= L_ * (1 - THRU)) if side > 0 else (hi[:24] >= L_ * (1 + THRU))
            b = _first(m)
            if b is not None:
                px = min(o[b], L_) if side > 0 else max(o[b], L_)
                fills.append((1 / 3, b, px))
        if not fills:
            return {"nofill": True, "k": k}
        first_fill = min(b for _, b, _ in fills)
        t1_from = first_fill + 1
    s = _first(hit_stop, first_fill)
    t1 = _first(t1m, t1_from)
    units = []   # (peso, barra in, prezzo in, barra out, prezzo out, motivo)
    stop_px = lambda b: (min(o[b], g["stop"]) if side > 0 else max(o[b], g["stop"]))
    tgt_px = lambda b, X: (max(o[b], X) if side > 0 else min(o[b], X))
    if t1 is not None and (s is None or t1 < s):
        live = [u for u in fills if u[1] <= t1]          # i limit non riempiti al target 1 si annullano
        for w, b, px in live:
            units.append((w / 2, b, px, t1, tgt_px(t1, g["T1"]), "T1"))
        t2 = _first(t2m, t1 + 1)
        s2 = _first(hit_stop, t1 + 1)
        for w, b, px in live:
            if t2 is not None and (s2 is None or t2 < s2):
                units.append((w / 2, b, px, t2, tgt_px(t2, g["T2"]), "T2"))
            elif s2 is not None:
                units.append((w / 2, b, px, s2, stop_px(s2), "stop"))
            else:
                units.append((w / 2, b, px, n - 1, C[k + n - 1], "tempo"))
    elif s is not None:
        for w, b, px in fills:
            if b <= s:
                units.append((w, b, px, s, stop_px(s), "stop"))
    else:
        for w, b, px in fills:
            units.append((w, b, px, n - 1, C[k + n - 1], "tempo"))
    ret = 0.0
    for w, bi, pi, bo, po, _ in units:
        fu = CF[k + bo + 1] - CF[k + bi]
        ret += w * (side * (po / pi - 1) - 2 * FEE - side * fu)
    exit_b = max(u[3] for u in units)
    return dict(T=T, k=k, side=side, ret=ret, exit=k + exit_b, units=[(w, k + bi, pi, k + bo, po, why) for w, bi, pi, bo, po, why in units],
                filled=sum(u[0] for u in fills), complete=(k + H <= NB), why="/".join(sorted({u[5] for u in units})), **g)


_CACHE: dict = {}


def all_trades(side, mode, H):
    key = (side, mode, H)
    if key not in _CACHE:
        p = WORK / f"tr_{'L' if side > 0 else 'S'}_{mode}_{H}.pkl"
        if p.exists() and pd.read_pickle(p).get("_n") == len(M):
            _CACHE[key] = pd.read_pickle(p)
        else:
            d = {T: trade(T, side, mode, H) for T in M.index}
            d["_n"] = len(M)
            pd.to_pickle(d, p)
            _CACHE[key] = d
    return _CACHE[key]


def select(sig: pd.Series, side, mode, H, allow=None):
    """Una posizione alla volta: trade al primo segnale con geometria dopo l'uscita precedente (o dopo 24h se nessun limit)."""
    D = all_trades(side, mode, H)
    out, free = [], -1
    for T in sig.index[sig.to_numpy()]:
        k = TI.searchsorted(T)
        if k <= free or (allow is not None and not allow.get(T, True)):
            continue
        t = D.get(T)
        if t is None:
            continue
        if t.get("nofill"):
            free = k + 23          # limit non riempiti: il segnale resta occupato 24 ore
            continue
        out.append(t); free = t["exit"]
    return out


def equity(trs, scale=None):
    """Equity oraria (10k, 1x o nozionale scale(t)), DD sul giornaliero."""
    eq = np.ones(NB)
    cap = 1.0
    k0 = TI.searchsorted(START)
    last = k0
    for t in trs:
        sc = 1.0 if scale is None else scale(t)
        k, e = t["k"], t["exit"]
        eq[last:k] = cap
        mk = np.zeros(e - k + 1)
        for w, bi, pi, bo, po, _ in t["units"]:
            seg = np.arange(k, e + 1)
            op = (seg >= bi) & (seg < bo)
            mk[op] += w * t["side"] * (C[seg[op]] / pi - 1)
            fu = CF[bo + 1] - CF[bi]
            mk[seg >= bo] += w * (t["side"] * (po / pi - 1) - 2 * FEE - t["side"] * fu)
        eq[k:e + 1] = cap * (1 + sc * mk)
        cap *= 1 + sc * t["ret"]
        last = e + 1
    eq[last:] = cap
    s = pd.Series(eq[k0:], TI[k0:]) * 10000
    return s


def stats(trs, scale=None, lab=""):
    if not trs:
        return dict(regola=lab, trade=0)
    e = equity(trs, scale)
    d = e.resample("D").last()
    dd = float((d / d.cummax() - 1).min())
    sc = [1.0 if scale is None else scale(t) for t in trs]
    r = np.array([t["ret"] * s for t, s in zip(trs, sc)])
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    fin = float(e.iloc[-1])
    rend = fin / 10000 - 1
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    cagr = (fin / 10000) ** (1 / yrs) - 1
    top3 = np.sort(r)[-3:]
    return dict(regola=lab, finale=round(fin), rend=round(rend * 100, 1), dd=round(dd * 100, 1), mar=round(rend / abs(dd), 2) if dd < 0 else np.nan, cagr=round(cagr * 100, 1),
                trade=len(r), wr=round((r > 0).mean() * 100, 1), pf=round(gp / gl, 2) if gl > 0 else np.inf,
                media=round(r.mean() * 100, 3), senza_top3=round(fin / np.prod(1 + top3)))


def split_stats(trs, lab, scale=None):
    a = [t for t in trs if t["T"] < SPLIT]; b = [t for t in trs if t["T"] >= SPLIT]
    ra = np.array([t["ret"] for t in a]); rb = np.array([t["ret"] for t in b])
    return dict(n_IS=len(a), media_IS=round(ra.mean() * 100, 3) if len(a) else np.nan,
                pf_IS=round(ra[ra > 0].sum() / -ra[ra < 0].sum(), 2) if (ra < 0).any() else np.nan,
                n_OOS=len(b), media_OOS=round(rb.mean() * 100, 3) if len(b) else np.nan,
                pf_OOS=round(rb[rb > 0].sum() / -rb[rb < 0].sum(), 2) if (rb < 0).any() else np.nan)


def bh():
    c = pd.Series(C, TI)[START:]
    e = c / c.iloc[0] * 10000 * (1 - 0.002)
    d = e.resample("D").last()
    dd = float((d / d.cummax() - 1).min())
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    cagr = (e.iloc[-1] / 10000) ** (1 / yrs) - 1
    return dict(regola="Buy & hold", finale=round(float(e.iloc[-1])), rend=round((e.iloc[-1] / 10000 - 1) * 100, 1), dd=round(dd * 100, 1),
                mar=round((e.iloc[-1] / 10000 - 1) / abs(dd), 2), cagr=round(cagr * 100, 1), trade=1)
