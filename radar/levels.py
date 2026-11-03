"""Supporti e resistenze di BTC per la dashboard (livelli di riferimento, non segnali di trading).

Metodo oggettivo, ricalcolato a ogni giro sui dati giornalieri:
1. massimi e minimi swing (frattali): giornalieri con finestra di 10 giorni sugli ultimi 2 anni e settimanali con finestra
   di 4 settimane su tutto lo storico disponibile;
2. profilo di volume degli ultimi 365 giorni (volume di ogni giorno distribuito sul suo range): i picchi (HVN) sono
   zone dove si è scambiato molto;
3. i punti vicini si uniscono in una zona larga al massimo ~1,8 ATR giornalieri; la forza (1–5) cresce con i tocchi, il peso
   del timeframe (settimanale > giornaliero), il volume e la recenza.
Sotto il prezzo = supporto, sopra = resistenza. La ricerca (RESEARCH.md, TA1 e lezione 68) non ha trovato un vantaggio
nel fare trading sui soli S/R: qui servono come mappa per leggere il grafico, stop e prese di profitto.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _pivots(h: pd.Series, l: pd.Series, k: int) -> list[tuple[pd.Timestamp, float, str]]:
    out = []
    hv, lv, idx = h.to_numpy(float), l.to_numpy(float), h.index
    for i in range(k, len(hv) - k):
        if hv[i] == hv[i - k:i + k + 1].max():
            out.append((idx[i], hv[i], "massimo"))
        if lv[i] == lv[i - k:i + k + 1].min():
            out.append((idx[i], lv[i], "minimo"))
    return out


def _volume_nodes(f: pd.DataFrame, bins: int = 120, top: int = 6) -> list[tuple[float, float]]:
    """Picchi del profilo di volume (prezzo, quota del volume) sugli ultimi 365 giorni."""
    d = f.iloc[-365:]
    vol = d["spot_vol"] if "spot_vol" in d else d.get("volume")
    if vol is None:
        return []
    lo, hi = float(d["low"].min()), float(d["high"].max())
    edges = np.linspace(lo, hi, bins + 1)
    prof = np.zeros(bins)
    for l, h, v in zip(d["low"].to_numpy(float), d["high"].to_numpy(float), vol.fillna(0).to_numpy(float)):
        a, b = np.searchsorted(edges, l, "right") - 1, np.searchsorted(edges, h, "right") - 1
        a, b = max(a, 0), min(max(b, a), bins - 1)
        prof[a:b + 1] += v / (b - a + 1)
    sm = np.convolve(prof, np.ones(3) / 3, mode="same")
    peaks = [i for i in range(1, bins - 1) if sm[i] >= sm[i - 1] and sm[i] >= sm[i + 1]]
    peaks = sorted(peaks, key=lambda i: -sm[i])[:top]
    tot = sm.sum() or 1.0
    return [((edges[i] + edges[i + 1]) / 2, float(sm[i] / tot)) for i in peaks]


def compute(f: pd.DataFrame, n_side: int = 6) -> dict:
    f = f[f["close"].notna()]
    price, date = float(f["close"].iloc[-1]), f.index[-1]
    atr = float(f["atr"].iloc[-1]) if "atr" in f and pd.notna(f["atr"].iloc[-1]) else price * 0.03
    w = f[["high", "low"]].resample("W-SUN").agg({"high": "max", "low": "min"}).dropna()
    pts = [(t, p, k, "giornaliero", 1.0) for t, p, k in _pivots(f["high"].iloc[-730:], f["low"].iloc[-730:], 10)]
    pts += [(t, p, k, "settimanale", 2.0) for t, p, k in _pivots(w["high"], w["low"], 4)]
    pts = [x for x in pts if 0.55 * price <= x[1] <= 1.6 * price]
    pts.sort(key=lambda x: x[1])
    tol = 1.2 * atr
    zones: list[dict] = []
    for t, p, k, tf, wgt in pts:
        z = zones[-1] if zones else None
        if z and p - z["lo"] <= 1.5 * tol:   # zona larga al massimo ~1,8 ATR: niente catene di livelli
            z["pts"].append((t, p, k, tf, wgt)); z["hi"] = max(z["hi"], p); z["lo"] = min(z["lo"], p)
        else:
            zones.append({"lo": p, "hi": p, "pts": [(t, p, k, tf, wgt)]})
    nodes = _volume_nodes(f)
    out = []
    for z in zones:
        ps = z["pts"]
        mid = float(np.mean([p for _, p, *_ in ps]))
        age = [(date - t).days for t, *_ in ps]
        rec = max(0.0, 1 - min(age) / 730)                                  # 1 = toccato di recente
        vol = sum(s for c, s in nodes if z["lo"] - tol <= c <= z["hi"] + tol)
        score = sum(wgt for *_, wgt in ps) + 0.8 * rec + 25 * vol
        out.append({"price": round(mid, 0), "lo": round(z["lo"], 0), "hi": round(z["hi"], 0), "score": score,
                    "touches": len(ps), "weekly": any(tf == "settimanale" for *_, tf, _ in ps),
                    "last": str(max(t for t, *_ in ps).date()), "volume": round(vol * 100, 1),
                    "kind": "supporto" if mid < price else "resistenza", "dist_pct": round((mid / price - 1) * 100, 2)})
    for c, s in nodes:                                                       # nodi di volume senza pivot vicini
        if not any(o["lo"] - tol <= c <= o["hi"] + tol for o in out) and 0.55 * price <= c <= 1.6 * price:
            out.append({"price": round(c, 0), "lo": round(c - atr / 2, 0), "hi": round(c + atr / 2, 0), "score": 25 * s,
                        "touches": 0, "weekly": False, "last": None, "volume": round(s * 100, 1),
                        "kind": "supporto" if c < price else "resistenza", "dist_pct": round((c / price - 1) * 100, 2)})
    if out:
        sc = np.array([o["score"] for o in out])
        q = np.quantile(sc, [0.2, 0.4, 0.6, 0.8])
        for o in out:
            o["strength"] = int(1 + (o["score"] > q).sum())
            del o["score"]
    sup = sorted([o for o in out if o["kind"] == "supporto"], key=lambda o: -o["price"])[:n_side]
    res = sorted([o for o in out if o["kind"] == "resistenza"], key=lambda o: o["price"])[:n_side]
    return {"date": str(date.date()), "price": price, "atr": round(atr, 0), "supports": sup, "resistances": res}
