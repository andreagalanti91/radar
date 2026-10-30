"""Feature giornaliere di order flow e posizionamento per BTC."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _z(s: pd.Series, n: int) -> pd.Series:
    return (s - s.rolling(n, min_periods=n // 2).mean()) / s.rolling(n, min_periods=n // 2).std()


def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def build_features(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    spot, perp = d["spot"], d["perp"].copy()
    m = d["metrics"]
    f = pd.DataFrame(index=spot.index)
    f["open"], f["high"], f["low"], f["close"] = spot["open"], spot["high"], spot["low"], spot["close"]
    f["perp_close"] = perp["close"]

    # --- order flow: CVD spot e perp (delta = buy aggressivi - sell aggressivi)
    f["spot_delta"] = 2 * spot["taker_buy_volume"] - spot["volume"]
    tb = perp["taker_buy_volume"]
    if "taker_buy_share" in m:  # giorni recenti senza taker volume nell'archivio: stima dalle metrics
        tb = tb.fillna(perp["volume"] * m["taker_buy_share"].reindex(perp.index))
    f["perp_delta"] = 2 * tb - perp["volume"]
    f["spot_vol"], f["perp_vol"] = spot["volume"], perp["volume"]
    for n in (7, 14):
        f[f"spot_flow{n}"] = f["spot_delta"].rolling(n).sum() / f["spot_vol"].rolling(n).sum()
        f[f"perp_flow{n}"] = f["perp_delta"].rolling(n).sum() / f["perp_vol"].rolling(n).sum()
    f["cvd_spot"] = f["spot_delta"].cumsum()
    f["cvd_perp"] = f["perp_delta"].fillna(0).cumsum()
    f["pf14z"] = _z(f["perp_flow14"], 180)
    f["sf14z"] = _z(f["spot_flow14"], 180)
    # spot-led vs perp-led: chi guida il movimento
    f["flow_gap14"] = _z(f["spot_flow14"], 180) - _z(f["perp_flow14"], 180)

    # --- derivati: basis, funding, open interest, long/short
    f["basis"] = f["perp_close"] / f["close"] - 1
    f["funding"] = d["funding"]["funding"].reindex(f.index).ffill(limit=3)
    f["funding7"] = f["funding"].rolling(7).mean()
    f["funding_z"] = _z(f["funding7"], 180)
    if len(m):
        oi = m["oi"].where(m["oi"] > 0).reindex(f.index)  # OI 0 = dato mancante, non un crollo del 100%
        f["oi"] = oi
        f["oi_chg7"] = oi.pct_change(7, fill_method=None)
        f["oi_chg14"] = oi.pct_change(14, fill_method=None)
        f["oi_z"] = _z(f["oi_chg7"], 180)
        f["top_ls"] = m["top_ls_pos"].reindex(f.index)
        f["global_ls"] = m["global_ls"].reindex(f.index)
        f["ls_z"] = _z(f["global_ls"], 180)
    f["fng"] = d["fng"]["fng"].reindex(f.index).ffill(limit=2)

    # --- prezzo / volatilità
    c = f["close"]
    tr = pd.concat([f["high"] - f["low"], (f["high"] - c.shift()).abs(), (f["low"] - c.shift()).abs()], axis=1).max(axis=1)
    f["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    f["atr_pct"] = f["atr"] / c
    for n in (20, 50, 200):
        f[f"sma{n}"] = c.rolling(n).mean()
    f["dist20"] = (c - f["sma20"]) / f["atr"]
    f["dist50"] = (c - f["sma50"]) / f["atr"]
    f["trend_up"] = (c > f["sma200"]) & (f["sma50"] > f["sma200"])
    f["ret7"] = c.pct_change(7)
    f["ret14"] = c.pct_change(14)
    f["dd30"] = c / c.rolling(30).max() - 1
    f["brk20"] = c / c.rolling(20).max().shift() - 1
    f["ret30"] = c.pct_change(30)
    f["pump30"] = c / c.rolling(30).min() - 1
    f["rsi"] = _rsi(c)
    # divergenza prezzo/CVD spot su 14 giorni: prezzo scende ma lo spot compra (assorbimento)
    f["cvd_div14"] = np.sign(f["ret14"]) * -1 * f["spot_flow14"]
    return f
