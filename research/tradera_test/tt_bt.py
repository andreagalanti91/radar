"""tradera_test · motore del backtest (PREREG.md, commit 9da09c8). Funzioni pure su array; nessuna modifica a radar/.

Un trade: ingresso all'apertura dopo il segnale, stop e obiettivo come ordini (stessa barra → stop), nessuna gestione,
chiusura forzata alla fine del periodo. Costi 0,10% per lato; funding per barra = tasso annuo / barre l'anno.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

COST = 0.001


def run_trade(O, H, L, C, e: int, side: int, stop: float, tgt: float, end: int):
    """Indice e = barra d'ingresso (apertura). Ritorna (indice d'uscita, prezzo d'uscita, motivo) o None se non si entra."""
    px = O[e]
    if side > 0 and (px <= stop or px >= tgt):
        return None
    if side < 0 and (px >= stop or px <= tgt):
        return None
    lo = e
    while lo <= end:
        hi = min(end, lo + (63 if lo == e else 1000))
        if side > 0:
            hs, ht = L[lo:hi + 1] <= stop, H[lo:hi + 1] >= tgt
        else:
            hs, ht = H[lo:hi + 1] >= stop, L[lo:hi + 1] <= tgt
        js = int(np.argmax(hs)) if hs.any() else None
        jt = int(np.argmax(ht)) if ht.any() else None
        if js is not None and (jt is None or js <= jt):
            j = lo + js
            x = min(O[j], stop) if side > 0 else max(O[j], stop)
            return j, x, "stop"
        if jt is not None:
            j = lo + jt
            x = max(O[j], tgt) if side > 0 else min(O[j], tgt)
            return j, x, "obiettivo"
        lo = hi + 1
    return end, C[end], "fine periodo"


def trades_from_signals(df: pd.DataFrame, sigs: list[dict], start: str, end: str, fund_long: float, fund_short: float,
                        ppy: int, asset: str, regime: np.ndarray | None = None) -> list[dict]:
    O, H, L, C = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    ix = df.index
    t0, t1 = ix.searchsorted(pd.Timestamp(start)), ix.searchsorted(pd.Timestamp(end), "right") - 1
    out, busy = [], -1
    for s in sorted(sigs, key=lambda x: x["t"]):
        t = s["t"]
        if t < t0 or t > t1 or t + 1 > t1 or t < busy:
            continue
        side = s["side"]
        r = run_trade(O, H, L, C, t + 1, side, s["stop"], s["tgt"], t1)
        if r is None:
            continue
        j, x, why = r
        ent = O[t + 1]
        sd = abs(ent - s["stop"]) / ent
        bars = j - (t + 1) + 1
        fr = (fund_long if side > 0 else fund_short) * bars / ppy
        net = side * (x / ent - 1) - 2 * COST - fr
        out.append(dict(asset=asset, side=side, sig=ix[t], entry=ix[t + 1], exit=ix[j], e=t + 1, j=j, entry_px=ent, exit_px=x,
                        stop=s["stop"], tgt=s["tgt"], sd=sd, td=abs(s["tgt"] / ent - 1), why=why, net=net, R=net / sd,
                        days=(ix[j] - ix[t + 1]).days, conf=s.get("conf", None), kind=s.get("kind", "ritest"),
                        reg=None if regime is None else bool(regime[t])))
        busy = j + 1   # nuovo segnale solo dalla barra dopo l'uscita (ingresso il giorno dopo)
    return out


def portfolio(trades: list[dict], frames: dict, start: str, end: str, mode: str, fund: tuple, ppy: int,
              risk: float = 0.02, cap0: float = 10000.0) -> pd.Series:
    """Equity giornaliera. mode 'risk': capitale condiviso, nozionale = risk/sd del capitale (≤ capitale libero).
    mode 'full': un solo asset, nozionale = tutto il capitale. Mark-to-market alla chiusura."""
    days = sorted(set().union(*[set(f.index[(f.index >= start) & (f.index <= end)]) for f in frames.values()]))
    days = pd.DatetimeIndex(days)
    closes = {a: f["close"].reindex(days).ffill() for a, f in frames.items()}
    by_entry: dict = {}
    for k, tr in enumerate(trades):
        by_entry.setdefault(tr["entry"], []).append(k)
    cash, openp, eq = cap0, {}, np.zeros(len(days))
    for di, d in enumerate(days):
        # equity alla chiusura precedente per dimensionare
        e_prev = eq[di - 1] if di else cap0
        for k in by_entry.get(d, []):
            tr = trades[k]
            used = sum(p["notional"] for p in openp.values())
            free = max(0.0, e_prev - used)
            want = e_prev if mode == "full" else min(e_prev, risk * e_prev / tr["sd"])
            notional = min(want, free)
            if notional <= 1e-9:
                continue
            qty = notional / tr["entry_px"]
            cash -= notional * COST
            openp[k] = dict(qty=qty, notional=notional, tr=tr)
        unreal = 0.0
        for k in list(openp):
            p, tr = openp[k], openp[k]["tr"]
            c = closes[tr["asset"]].loc[d]
            rate = fund[0] if tr["side"] > 0 else fund[1]
            cash -= rate / ppy * p["qty"] * c
            if tr["exit"] == d:
                cash += tr["side"] * p["qty"] * (tr["exit_px"] - tr["entry_px"]) - p["qty"] * tr["exit_px"] * COST
                del openp[k]
            else:
                unreal += tr["side"] * p["qty"] * (c - tr["entry_px"])
        eq[di] = cash + unreal
    return pd.Series(eq, days)


def metrics(eq: pd.Series, trades: list[dict]) -> dict:
    yrs = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    fin = float(eq.iloc[-1])
    cagr = (fin / 10000.0) ** (1 / yrs) - 1 if fin > 0 else -1.0
    dd = float((eq / eq.cummax() - 1).min())
    R = np.array([t["R"] for t in trades]) if trades else np.array([])
    srt = np.sort(R)[::-1]
    return dict(fin=round(fin), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1),
                cdd=round(cagr / abs(dd), 2) if dd < 0 else float("nan"), n=len(trades),
                wr=round(100 * float((R > 0).mean()), 1) if len(R) else float("nan"),
                mR=round(float(R.mean()), 3) if len(R) else float("nan"),
                mnet=round(100 * float(np.mean([t["net"] for t in trades])), 2) if trades else float("nan"),
                dur=round(float(np.mean([t["days"] for t in trades])), 1) if trades else float("nan"),
                sumR=round(float(R.sum()), 1) if len(R) else 0.0, sumR_no3=round(float(srt[3:].sum()), 1) if len(R) else 0.0,
                mR_no1=round(float(srt[1:].mean()), 3) if len(R) > 1 else float("nan"))


def placebo(trades: list[dict], arrays: dict, periods: dict, ndraw: int, rng, fund: dict, ppy: dict) -> dict:
    """Media degli R di ndraw insiemi placebo (stesso asset, periodo, lato e regime EMA200; stesse distanze in %)."""
    pools = {}
    for tr in trades:
        a = arrays[tr["asset"]]
        key = (tr["asset"], tr["per"], tr["reg"])
        if key not in pools:
            t0, t1 = periods[tr["per"]][tr["asset"]]
            cand = np.arange(t0, t1 - 1)
            pools[key] = cand[a["reg"][cand] == tr["reg"]]
    pers = sorted({tr["per"] for tr in trades})
    out = {p: np.zeros(ndraw) for p in pers + ["tutti"]}
    for k in range(ndraw):
        Rs = {p: [] for p in pers}
        for tr in trades:
            a = arrays[tr["asset"]]
            pool = pools[(tr["asset"], tr["per"], tr["reg"])]
            if not len(pool):
                continue
            t = int(rng.choice(pool))
            e = t + 1
            ent = a["O"][e]
            s = tr["side"]
            stop, tgt = ent * (1 - s * tr["sd"]), ent * (1 + s * tr["td"])
            t1 = periods[tr["per"]][tr["asset"]][1]
            j, x, _ = run_trade(a["O"], a["H"], a["L"], a["C"], e, s, stop * (1 - 1e-12 * s), tgt, t1) or (e, ent, "")
            bars = j - e + 1
            fr = (fund[tr["asset"]][0] if s > 0 else fund[tr["asset"]][1]) * bars / ppy[tr["asset"]]
            Rs[tr["per"]].append((s * (x / ent - 1) - 2 * COST - fr) / tr["sd"])
        for p in pers:
            out[p][k] = np.mean(Rs[p]) if Rs[p] else np.nan
        out["tutti"][k] = np.mean(sum(Rs.values(), []))
    return out


def flip_signals(df: pd.DataFrame, atr: np.ndarray, k: int = 3, life_weeks: int = 104) -> list[dict]:
    """Regola "flip" (lezione 114) generalizzata: livelli = pivot settimanali noti dalla conferma (settimana i+k)."""
    w = df[["high", "low"]].resample("W").agg({"high": "max", "low": "min"}).dropna()
    h, l, wi = w["high"].to_numpy(float), w["low"].to_numpy(float), w.index
    lv = []
    for i in range(k, len(w) - k):
        for arr, fn in ((h, np.max), (l, np.min)):
            if arr[i] == fn(arr[i - k:i + k + 1]):
                lv.append((wi[i + k], wi[i + k] + pd.Timedelta(weeks=life_weeks), float(arr[i])))
    ix = df.index
    a0 = ix.searchsorted(pd.DatetimeIndex([x[0] for x in lv]), "right")   # noto dal giorno dopo la domenica di conferma
    a1 = ix.searchsorted(pd.DatetimeIndex([x[1] for x in lv]))
    px = np.array([x[2] for x in lv])
    C = df["close"].to_numpy(float)
    out = []
    for t in range(1, len(ix)):
        act = np.sort(px[(a0 <= t) & (a1 > t)])
        if not len(act):
            continue
        below, above = act[act < C[t - 1]], act[act > C[t - 1]]
        if len(below) and C[t] < below[-1]:
            sup = below[-1]
            nxt = act[act < min(sup, C[t])]
            if len(nxt):
                out.append(dict(t=t, side=-1, stop=sup + atr[t], tgt=nxt[-1], kind="flip"))
                continue
        if len(above) and C[t] > above[0]:
            res = above[0]
            nxt = act[act > max(res, C[t])]
            if len(nxt):
                out.append(dict(t=t, side=1, stop=res - atr[t], tgt=nxt[0], kind="flip"))
    return out
