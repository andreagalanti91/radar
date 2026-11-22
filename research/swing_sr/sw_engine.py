"""Swing su supporti/resistenze settimanali · motore di ricerca (22/11/2026). Non modifica radar/.

Dati: research/p2_nuovi/data (congelati al 15/11/2026). BTC giornaliero; 2014–2020 dal frame lungo (flusso proxy), 2021+ dal frame
del tool. Una posizione per volta, esposizione 1x del conto (long spot, short perp), costi e funding di W3.1.

Livelli: massimi e minimi di swing SETTIMANALI (candele W-SUN): la settimana i è un pivot se il suo massimo (minimo) è l'estremo
delle settimane i−K…i+K; il livello è noto dalla chiusura della settimana i+K e resta attivo LIFE settimane dalla conferma.
Ogni livello vale sia come supporto (se sta sotto il prezzo) sia come resistenza (se sta sopra).

Segnali (alla chiusura giornaliera t, ingresso all'apertura t+1), lato long (short speculare):
- B rimbalzo: S = livello più vicino sotto la chiusura t−1; minimo t ≤ S·(1+TOL), chiusura t > S, chiusura t > apertura t.
              Stop strutturale = min(minimo t, S)·(1−BUF).
- X rottura:  Rr = livello più vicino sopra la chiusura t−1; chiusura t > Rr. Stop strutturale = Rr·(1−BUF).
- T ritest:   entro RET giorni da una rottura X del livello Lv, senza chiusure sotto Lv·(1−INV): minimo t ≤ Lv·(1+TOL),
              chiusura t > Lv, chiusura t > apertura t. Stop strutturale = min(minimo t, Lv)·(1−BUF).

Regime (ultima candela settimanale chiusa entro t): R0 nessuno; R1 solo prezzo (long: chiusura > SMA40, EMA20 in salita, chiusura
> EMA21; short: chiusura < SMA40, SMA40 in calo su 4 settimane, EMA20 in calo, chiusura < EMA21); R2 = colonne long/short di
radar.weekly (R1 + flusso perp + filtro MACD dei trend vecchi).

Stop: "ST" strutturale con distanza d dalla chiusura del segnale: d > SMAX → niente trade; d < SMIN → stop a SMIN.
      "SS" strutturale puro: come ST ma con minimo SSMIN (2%) invece di SMIN (5%).
      "SF" fisso a SFIX dalla chiusura del segnale.
Uscite: "T10"/"T15" tutto a +10%/+15% dalla chiusura del segnale; "TSR" tutto al livello successivo distante fra 5% e 30%
        (se non c'è: +15%); "TH" metà a +10%, poi stop almeno a pareggio e trailing a TRK·ATR14 giornaliero dal massimo;
        "TT" nessun TP, trailing a TRK·ATR14 dal massimo fin dall'ingresso.
Ordine nel giorno: ingresso all'apertura → stop (prima dello stop mai TP: ipotesi prudente) → TP → funding → trailing → segnale.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "p2_nuovi"))
from radar import weekly as W  # noqa: E402
from p2_data import load  # noqa: E402

K, LIFE = 3, 104
TOL, BUF, RET, INV = 0.01, 0.01, 20, 0.03
SMIN, SMAX, SFIX, TRK, SSMIN = 0.05, 0.10, 0.075, 3.0, 0.02
ENTRIES, REGIMES, SIDES, STOPS, TPS = ("B", "X", "T"), ("R0", "R1", "R2"), ("L", "S", "LS"), ("ST", "SS", "SF"), ("T10", "T15", "TSR", "TH", "TT")


def frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    d = load()
    return d["f"], d["fl"]


def levels(f: pd.DataFrame, k: int = K, life: int = LIFE) -> list[tuple[pd.Timestamp, pd.Timestamp, float]]:
    """(da, a, prezzo): livello noto dalla chiusura della settimana i+k (domenica), attivo per `life` settimane."""
    w = f[["high", "low"]].resample("W-SUN").agg({"high": "max", "low": "min"}).dropna()
    w = w[w.index <= f.index[-1]]
    h, l, ix = w["high"].to_numpy(float), w["low"].to_numpy(float), w.index
    out = []
    for i in range(k, len(w) - k):
        for arr, fn in ((h, np.max), (l, np.min)):
            if arr[i] == fn(arr[i - k:i + k + 1]):
                out.append((ix[i + k], ix[i + k] + pd.Timedelta(weeks=life), float(arr[i])))
    return out


def signals(f: pd.DataFrame, k: int = K, life: int = LIFE, tol: float = TOL) -> dict:
    """Array giornalieri: per ogni tipo e lato, segnale (bool), stop strutturale, livello; regimi; livelli attivi per giorno."""
    f = f[f["close"].notna()]
    idx = f.index
    O, H, L, C = (f[c].to_numpy(float) for c in ("open", "high", "low", "close"))
    n = len(idx)
    lv = levels(f, k, life)
    a0 = idx.searchsorted(pd.DatetimeIndex([x[0] for x in lv]))
    a1 = idx.searchsorted(pd.DatetimeIndex([x[1] for x in lv]))
    px = np.array([x[2] for x in lv])
    act = [np.sort(px[(a0 <= t) & (a1 > t)]) for t in range(n)]   # noti alla chiusura del giorno t (conferma di domenica compresa)
    sig = {(e, s): np.zeros(n, bool) for e in ENTRIES for s in (1, -1)}
    stp = {key: np.full(n, np.nan) for key in sig}
    brk: dict[int, list] = {1: [], -1: []}   # rotture recenti: [livello, giorno]
    for t in range(1, n):
        a = act[t - 1]   # livelli noti ieri: supporto/resistenza definiti rispetto alla chiusura di ieri
        for s in (1, -1):
            lo_t, hi_t = (L[t], H[t]) if s > 0 else (-H[t], -L[t])   # lato short: tutto con il segno cambiato
            c_t, o_t, c_p = s * C[t], s * O[t], s * C[t - 1]
            b = np.sort(s * a)
            below, above = b[b < c_p], b[b > c_p]
            # T ritest (prima di aggiungere la rottura di oggi)
            keep = []
            for lev, day in brk[s]:
                if t - day > RET or c_t < lev - abs(lev) * INV:
                    continue
                keep.append([lev, day])
                touch = lo_t <= lev + abs(lev) * tol
                if touch and c_t > lev and c_t > o_t and not sig[("T", s)][t]:
                    sig[("T", s)][t] = True
                    stp[("T", s)][t] = s * (min(lo_t, lev) - abs(min(lo_t, lev)) * BUF)
            brk[s] = keep
            if len(below):
                sup = below[-1]
                if lo_t <= sup + abs(sup) * tol and c_t > sup and c_t > o_t:
                    sig[("B", s)][t] = True
                    stp[("B", s)][t] = s * (min(lo_t, sup) - abs(min(lo_t, sup)) * BUF)
            if len(above):
                res = above[0]
                if c_t > res:
                    sig[("X", s)][t] = True
                    stp[("X", s)][t] = s * (res - abs(res) * BUF)
                    brk[s].append([res, t])
    w = W.weekly_bars(f)
    c = w["close"]
    r1l = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1)) & (c > w["ema21"])
    r1s = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1)) & (c < w["ema21"])
    day = lambda x: x.astype(float).reindex(idx, method="ffill").fillna(0).to_numpy() > 0  # noqa: E731
    reg = {("R0", 1): np.ones(n, bool), ("R0", -1): np.ones(n, bool), ("R1", 1): day(r1l), ("R1", -1): day(r1s),
           ("R2", 1): day(w["long"]), ("R2", -1): day(w["short"])}
    tr = np.maximum(H - L, np.maximum(np.abs(H - np.roll(C, 1)), np.abs(L - np.roll(C, 1))))
    tr[0] = H[0] - L[0]
    atr = pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()
    fu = f["funding"].fillna(0).to_numpy(float) if "funding" in f else np.zeros(n)
    return dict(idx=idx, O=O, H=H, L=L, C=C, sig=sig, stp=stp, reg=reg, act=act, atr=atr, fu=fu, nlev=len(lv))


def plan(S: dict, t: int, side: int, entry: str, stop: str, tp: str, dist: float | None = None):
    """Stop e TP fissati alla chiusura del segnale t. None se il trade non si apre (stop strutturale oltre SMAX)."""
    c = S["C"][t]
    if dist is not None:
        d = dist
    elif stop == "SF":
        d = SFIX
    else:
        d = side * (c - S["stp"][(entry, side)][t]) / c
        if not np.isfinite(d) or d > SMAX:
            return None
        d = max(d, SMIN if stop == "ST" else SSMIN)   # "SS": strutturale puro, minimo SSMIN
    tgt = None
    if tp == "T10":
        tgt = c * (1 + side * 0.10)
    elif tp == "T15":
        tgt = c * (1 + side * 0.15)
    elif tp == "TH":
        tgt = c * (1 + side * 0.10)
    elif tp == "TSR":
        a = S["act"][t]
        m = side * (a / c - 1)
        ok = a[(m >= 0.05) & (m <= 0.30)]
        tgt = (ok.min() if side > 0 else ok.max()) if len(ok) else c * (1 + side * 0.15)
    return c * (1 - side * d), tgt, d


def simulate(S: dict, entry: str, regime: str, sides: str, stop: str, tp: str, start: str, end: str | None = None,
             forced: dict | None = None, trk: float = TRK) -> dict:
    """forced: {indice giorno: (lato, distanza stop)} sostituisce i segnali (placebo)."""
    idx, O, H, L, C, FU, ATR = S["idx"], S["O"], S["H"], S["L"], S["C"], S["fu"], S["atr"]
    t0 = idx.searchsorted(pd.Timestamp(start))
    t1 = len(idx) if end is None else idx.searchsorted(pd.Timestamp(end), "right")
    allow = {1: sides in ("L", "LS"), -1: sides in ("S", "LS")}
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    trades, eq = [], np.full(len(idx), np.nan)

    def fee() -> float:
        return W.FEE_SPOT if side > 0 else W.FEE_PERP

    def sell(frac: float, px: float, i: int, reason: str) -> None:
        nonlocal cash, qty, cost, side, tr
        q, k = qty * frac, cost * frac
        cash += q * px - k - abs(q) * px * fee()
        qty, cost = qty - q, cost - k
        tr["parts"].append((reason, round(px, 2)))
        if abs(qty) < 1e-15:
            tr.update(exit=idx[i], reason=reason, pnl=cash / tr["eq0"] - 1, days=i - tr["i0"])
            trades.append(tr)
            tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, t1):
        if pend is not None and not side:
            side, stp_px, tgt, d = pend
            px = O[i] * (1 + W.SLIP * side)
            eq0 = cash
            q = side * cash / (px * (1 + fee()))   # esposizione 1x compresa la commissione d'ingresso
            qty, cost = q, q * px
            cash -= abs(q) * px * fee()
            tr = dict(entry=idx[i], i0=i, side=side, entry_px=px, stop=stp_px, tgt=tgt, d=d, eq0=eq0, best=px, half=False,
                      trail=tp == "TT", parts=[])
        pend = None
        if side:
            s = side
            hit_stop = L[i] <= tr["stop"] if s > 0 else H[i] >= tr["stop"]
            if hit_stop:
                px = (min(O[i], tr["stop"]) if s > 0 else max(O[i], tr["stop"])) * (1 - W.SLIP * s)
                sell(1.0, px, i, "trail" if tr["trail"] and (tr["half"] or tp == "TT") and s * (tr["stop"] - tr["entry_px"]) >= 0
                     else "stop")
            elif tr["tgt"] is not None and (H[i] >= tr["tgt"] if s > 0 else L[i] <= tr["tgt"]):
                px = max(O[i], tr["tgt"]) if s > 0 else min(O[i], tr["tgt"])
                if tp == "TH":
                    sell(0.5, px, i, "tp")
                    tr["half"], tr["trail"], tr["tgt"] = True, True, None
                    tr["stop"] = max(tr["stop"], tr["entry_px"]) if s > 0 else min(tr["stop"], tr["entry_px"])
                else:
                    sell(1.0, px, i, "tp")
        if side:
            if side < 0:
                cash -= qty * C[i] * FU[i]
            tr["best"] = max(tr["best"], H[i]) if side > 0 else min(tr["best"], L[i])
            if tr["trail"]:
                tl = tr["best"] - side * trk * ATR[i]
                tr["stop"] = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if not side and i < t1 - 1:
            if forced is not None:
                if i in forced:
                    s, d = forced[i]
                    p = plan(S, i, s, entry, stop, tp, dist=d)
                    pend = (s,) + p
            else:
                c = [s for s in (1, -1) if allow[s] and S["sig"][(entry, s)][i] and S["reg"][(regime, s)][i]]
                if len(c) == 1:
                    p = plan(S, i, c[0], entry, stop, tp)
                    if p is not None:
                        pend = (c[0],) + p
    if side:   # posizione aperta: chiusa all'ultima chiusura con commissione (come nella ricerca W3.1)
        i = t1 - 1
        sell(1.0, C[i], i, "open")
        eq[i] = cash
    return {"trades": trades, "equity": pd.Series(eq[t0:t1], idx[t0:t1])}


def metrics(r: dict, capital: float = 10000.0) -> dict:
    e = r["equity"]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    fin = float(e.iloc[-1])
    dd = float((e / e.cummax() - 1).min())
    cagr = fin ** (1 / yrs) - 1 if fin > 0 else -1.0
    pn = np.array([t["pnl"] for t in r["trades"]])
    g, l = pn[pn > 0].sum(), -pn[pn < 0].sum()
    return dict(fin=round(fin * capital), cagr=cagr, dd=dd, cdd=cagr / abs(dd) if dd < 0 else np.nan, n=len(pn),
                wr=float((pn > 0).mean()) if len(pn) else np.nan, pf=float(g / l) if l > 0 else np.inf if g > 0 else np.nan,
                avg=float(pn.mean()) if len(pn) else np.nan, worst=float(pn.min()) if len(pn) else np.nan,
                days=float(np.median([t["days"] for t in r["trades"]])) if len(pn) else np.nan,
                inpos=float(sum(t["days"] for t in r["trades"]) / max(len(e), 1)))
