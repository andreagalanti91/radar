"""Modulo CANDIDATO (ricerca, non usato dal tool): stato corrente delle regole squeeze L1/L2/S1 (research/liq_squeeze/PREREG.md).

state(report, ...) -> dict con: setup sì/no, lato, squilibrio S entro ±6%, pulizia (cascata nelle ultime 72 ore / percentile),
fascia DCA (3 limit), stop, target 1/2, uscita a tempo e motivazione. Usa solo chiavi già presenti nel report del radar:
report["liqmap"] (bins [[prezzo, long $, short $]], price), report["liqcascade"] (active, side, end_utc), report["levels"].
Esito dello studio nel README: lo stato è CONTESTO, non un segnale operativo.
"""
from __future__ import annotations

import pandas as pd

THR = 0.50          # |S| minimo
RAD = 0.06          # raggio dello squilibrio
SIG = 0.30          # fascia densa (liqmap.SIG)
CLEAN_H = 72        # cascata del lato opposto nelle ultime 72 ore
PCT = 0.20          # oppure liquidazioni del lato "pulito" sotto il 20° percentile di 90 giorni
DCA_MIN, DCA_MAX = 0.01, 0.03
HOLD_H = 120
LIMIT_H = 24


def _clusters(w: pd.DataFrame, price: float, side: str) -> list[dict]:
    from radar.liqmap import clusters
    return [c for c in clusters(w, price, side, rng=0.10, sig=0.0) if c["rel"] >= SIG]


def imbalance(w: pd.DataFrame, price: float, rad: float = RAD) -> tuple[float, float, float]:
    k = (w["price"] - price).abs() <= rad * price
    s = float(w.loc[k & (w["price"] > price), "short"].sum())
    l = float(w.loc[k & (w["price"] < price), "long"].sum())
    return ((s - l) / (s + l) if s + l > 0 else 0.0), s, l


def atr4h(candles_1h: pd.DataFrame | None, n: int = 14) -> float | None:
    """ATR a 14 barre di 4 ore (00, 04, … UTC) dalle candele orarie chiuse."""
    if candles_1h is None or len(candles_1h) < 4 * (n + 2):
        return None
    b = candles_1h[["open", "high", "low", "close"]].resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    b = b.iloc[:-1] if (candles_1h.index[-1] + pd.Timedelta(hours=1)) < b.index[-1] + pd.Timedelta(hours=4) else b
    tr = pd.concat([b.high - b.low, (b.high - b.close.shift()).abs(), (b.low - b.close.shift()).abs()], axis=1).max(axis=1)
    v = tr.rolling(n).mean().iloc[-1]
    return float(v) if pd.notna(v) else None


def plan(w: pd.DataFrame, price: float, side: int, atr: float, levels: dict | None) -> dict | None:
    """Fascia DCA (3 limit), stop e target per il lato dato. None se manca il target 1 (nessuna fascia densa dal lato opposto)."""
    lv = levels or {}
    if side > 0:
        c = [x["price"] for x in _clusters(w, price, "long") if price * (1 - DCA_MAX) <= x["price"] <= price * (1 - DCA_MIN)]
        c += [z["hi"] for z in lv.get("supports", []) if z.get("hi") and price * (1 - DCA_MAX) <= z["hi"] <= price * (1 - DCA_MIN)]
        F = max(c) if c else price * (1 - DCA_MAX)
        stop = F - atr
        tg = sorted([x for x in _clusters(w, price, "short") if x["price"] >= price * 1.005], key=lambda x: x["price"])
        t2 = next((x for x in tg[1:] if x["price"] >= tg[0]["price"] * 1.005), None) if tg else None
    else:
        c = [x["price"] for x in _clusters(w, price, "short") if price * (1 + DCA_MIN) <= x["price"] <= price * (1 + DCA_MAX)]
        c += [z["lo"] for z in lv.get("resistances", []) if z.get("lo") and price * (1 + DCA_MIN) <= z["lo"] <= price * (1 + DCA_MAX)]
        F = min(c) if c else price * (1 + DCA_MAX)
        stop = F + atr
        tg = sorted([x for x in _clusters(w, price, "long") if x["price"] <= price * 0.995], key=lambda x: -x["price"])
        t2 = next((x for x in tg[1:] if x["price"] <= tg[0]["price"] * 0.995), None) if tg else None
    if not tg:
        return None
    lim = [round(price - (price - F) * k / 3, 0) for k in (1, 2, 3)]
    avg = sum(lim) / 3
    return {"limits": lim, "band_edge": round(F, 0), "from_support_or_band": bool(c), "stop": round(stop, 0),
            "stop_dist_pct_from_avg": round(abs(avg - stop) / avg * 100, 2),
            "t1": {"price": tg[0]["price"], "usd": tg[0]["usd"], "dist_pct": tg[0]["dist_pct"]},
            "t2": ({"price": t2["price"], "usd": t2["usd"], "dist_pct": t2["dist_pct"]} if t2 else None),
            "limit_valid_h": LIMIT_H, "time_exit_h": HOLD_H}


def _cascade_recent(report: dict, side: str, now: pd.Timestamp, last_cascade_utc: dict | None) -> str | None:
    lc = (report or {}).get("liqcascade") or {}
    ts = []
    if lc.get("active") and lc.get("side") == side and lc.get("end_utc"):
        ts.append(pd.Timestamp(lc["end_utc"]))
    if last_cascade_utc and last_cascade_utc.get(side):
        ts.append(pd.Timestamp(last_cascade_utc[side]))
    ok = [t for t in ts if now - pd.Timedelta(hours=CLEAN_H) < t + pd.Timedelta(hours=1) <= now]
    return str(max(ok)) if ok else None


def state(report: dict, candles_1h: pd.DataFrame | None = None, now: pd.Timestamp | None = None, atr: float | None = None,
          last_cascade_utc: dict | None = None, hist_rad: dict | None = None) -> dict:
    """Stato delle regole squeeze. hist_rad = {"long": serie delle liquidazioni long entro ±6% delle ultime 90 giorni,
    "short": idem} per la pulizia a percentile (facoltativa); last_cascade_utc = {"long": ora UTC, "short": ...} se nota."""
    lm = (report or {}).get("liqmap") or {}
    bins = lm.get("bins")
    if not bins:
        return {"ok": False, "why": "mappa delle liquidazioni assente"}
    w = pd.DataFrame(bins, columns=["price", "long", "short"]).astype(float)
    price = float(lm.get("price") or (candles_1h["close"].iloc[-1] if candles_1h is not None else 0))
    now = now or pd.Timestamp.utcnow().tz_localize(None).floor("h")
    a = atr if atr is not None else atr4h(candles_1h)
    S, s_up, l_dn = imbalance(w, price)
    out = {"ok": True, "price": round(price, 0), "S_pct": round(S * 100, 1), "short_above_6": round(s_up, 0), "long_below_6": round(l_dn, 0),
           "atr4h": round(a, 0) if a else None, "setup": None, "side": None, "note": "Regola di ricerca, non un segnale (vedi README)."}
    clean = {}
    for side in ("long", "short"):
        c = _cascade_recent(report, side, now, last_cascade_utc)
        pct = None
        hs = (hist_rad or {}).get(side)
        if hs is not None and len(hs) >= 720:
            cur = l_dn if side == "long" else s_up
            pct = float((pd.Series(hs) < cur).mean())
        clean[side] = {"cascade_end_utc": c, "percentile": round(pct, 3) if pct is not None else None,
                       "ok": bool(c) or (pct is not None and pct < PCT)}
    out["clean"] = clean
    why = []
    for sd, name in ((1, "long"), (-1, "short")):
        cond_s = S >= THR if sd > 0 else S <= -THR
        if not cond_s or not clean[name]["ok"]:
            continue
        if not a:
            why.append("ATR 4h non disponibile"); continue
        pl = plan(w, price, sd, a, report.get("levels"))
        if pl is None:
            why.append(f"{name}: nessuna fascia densa da usare come target"); continue
        out.update(setup=("L2" if sd > 0 else "S1"), side=name, plan=pl)
        out["why"] = (f"Squilibrio {S*100:+.0f}% entro ±6% ({s_up/1e6:,.0f}M short sopra, {l_dn/1e6:,.0f}M long sotto) e pulizia "
                      f"{'long' if sd > 0 else 'short'} ({'cascata ' + clean[name]['cascade_end_utc'] if clean[name]['cascade_end_utc'] else 'percentile basso'}).")
        return out
    side_s = "long" if S > 0 else "short"
    reasons = [f"squilibrio {S*100:+.0f}% (serve ≥ +{THR*100:.0f}% per L1/L2, ≤ −{THR*100:.0f}% per S1)"]
    reasons.append(f"pulizia long {'sì' if clean['long']['ok'] else 'no'}, short {'sì' if clean['short']['ok'] else 'no'}")
    out["setup"] = False
    out["why"] = "Nessun setup: " + "; ".join(reasons + why) + "."
    if a:   # piano ipotetico del lato verso cui pende lo squilibrio, solo informativo
        out["plan_if_" + side_s] = plan(w, price, 1 if S > 0 else -1, a, report.get("levels"))
    return out
