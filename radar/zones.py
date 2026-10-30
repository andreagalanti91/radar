"""Previsione della "regione" di prezzo dei prossimi giorni.

Per ogni giorno stima dove BTC andrà a toccare nei prossimi H giorni:
- zona di acquisto: fascia sotto il prezzo che il minimo dei prossimi H giorni raggiunge
  con buona probabilità (dove piazzare ingressi DCA long, spot o a leva);
- zona di vendita: fascia sopra il prezzo che il massimo raggiunge (take profit / short).

Il modello è volutamente semplice e senza look-ahead: la profondità del ritracciamento
è misurata in ATR e se ne prendono i quantili storici condizionati al regime
(trend e score di flusso), usando solo i dati disponibili fino a quel giorno.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

HORIZON = 7
Q_ZONE = (0.35, 0.65)  # fascia della zona: dal ritracciamento "facile" a quello "medio-profondo"
MIN_HISTORY = 250


def _bucket(f: pd.DataFrame) -> pd.Series:
    score = f["pf14z"] - f["ls_z"]
    trend = np.where(f["close"] > f["sma200"], "up", "down")
    flow = np.select([score > 1, score < -1], ["hi", "lo"], "mid")
    return pd.Series(trend, index=f.index) + "_" + pd.Series(flow, index=f.index)


def build_zones(f: pd.DataFrame, horizon: int = HORIZON) -> pd.DataFrame:
    c, atr = f["close"], f["atr"]
    lo = f["low"][::-1].rolling(horizon, min_periods=horizon).min()[::-1].shift(-1)
    hi = f["high"][::-1].rolling(horizon, min_periods=horizon).max()[::-1].shift(-1)
    z = pd.DataFrame(index=f.index)
    z["down_atr"] = (c - lo) / atr   # quanto scende (in ATR) nei prossimi giorni
    z["up_atr"] = (hi - c) / atr
    z["bucket"] = _bucket(f)
    # quantili walk-forward: un'osservazione entra nella storia solo quando il suo esito è noto
    cols = {f"{side}_q{int(q*100)}": np.nan for side in ("down", "up") for q in Q_ZONE + (0.5,)}
    for k in cols:
        z[k] = np.nan
    known = z[["down_atr", "up_atr", "bucket"]].shift(horizon + 1)
    for b in z["bucket"].dropna().unique():
        m = known["bucket"] == b
        for side in ("down", "up"):
            hist = known.loc[m, f"{side}_atr"]
            for q in Q_ZONE + (0.5,):
                est = hist.expanding(MIN_HISTORY // 4).quantile(q)
                z.loc[z["bucket"] == b, f"{side}_q{int(q*100)}"] = est.reindex(z.index).ffill()[z["bucket"] == b]
    z["buy_hi"] = c - z[f"down_q{int(Q_ZONE[0]*100)}"] * atr
    z["buy_lo"] = c - z[f"down_q{int(Q_ZONE[1]*100)}"] * atr
    z["sell_lo"] = c + z[f"up_q{int(Q_ZONE[0]*100)}"] * atr
    z["sell_hi"] = c + z[f"up_q{int(Q_ZONE[1]*100)}"] * atr
    z["lo_fwd"], z["hi_fwd"] = lo, hi
    return z


def evaluate_zones(f: pd.DataFrame, z: pd.DataFrame, start="2021-01-01") -> dict:
    """Quanto spesso il prezzo entra davvero nella zona prevista, e cosa succede dopo."""
    d = z[(z.index >= start) & z["buy_hi"].notna() & z["lo_fwd"].notna()].copy()
    touch_buy = d["lo_fwd"] <= d["buy_hi"]
    touch_sell = d["hi_fwd"] >= d["sell_lo"]
    # esito di un acquisto al centro della zona, se toccata, dopo 14 giorni
    c = f["close"]
    mid = (d["buy_hi"] + d["buy_lo"]) / 2
    filled = d["lo_fwd"] <= mid
    fwd14 = c.shift(-(HORIZON + 14)).reindex(d.index)
    ret_zone = (fwd14 / mid - 1)[filled]
    ret_close = (fwd14 / c.reindex(d.index) - 1)
    return {
        "days": int(len(d)),
        "buy_zone_touch_%": round(float(touch_buy.mean() * 100), 1),
        "buy_zone_mid_fill_%": round(float(filled.mean() * 100), 1),
        "below_zone_%": round(float((d["lo_fwd"] < d["buy_lo"]).mean() * 100), 1),
        "sell_zone_touch_%": round(float(touch_sell.mean() * 100), 1),
        "avg_ret_from_zone_%": round(float(ret_zone.mean() * 100), 2),
        "avg_ret_from_close_%": round(float(ret_close.mean() * 100), 2),
        "zone_entry_advantage_%": round(float(((c.reindex(d.index) / mid - 1)[filled]).mean() * 100), 2),
    }


def latest_zone(f: pd.DataFrame) -> dict:
    z = build_zones(f)
    last = z.iloc[-1]
    return {
        "horizon_days": HORIZON,
        "regime_bucket": last["bucket"],
        "buy": [round(float(last["buy_lo"]), 0), round(float(last["buy_hi"]), 0)],
        "sell": [round(float(last["sell_lo"]), 0), round(float(last["sell_hi"]), 0)],
        "stats": evaluate_zones(f, z),
    }
