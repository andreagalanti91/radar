"""Candele orarie Binance per il controllo orario dello stop di W3.2 (radar/weekly.check_intraday).

Il controllo orario dei livelli di v2 (conferma, limit DCA, stop, take profit) e il suo messaggio Telegram, spenti dal
12/11/2026, sono stati eliminati il 25/11/2026.
"""
from __future__ import annotations

import pandas as pd
import requests

KLINES = "https://data-api.binance.vision/api/v3/klines"


def hourly_since(start, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Candele orarie (UTC) da `start` (timestamp o giorno)."""
    t = pd.Timestamp(start)
    t = t.tz_localize("UTC") if t.tzinfo is None else t
    try:
        r = requests.get(KLINES, params={"symbol": symbol, "interval": "1h", "startTime": int(t.timestamp() * 1000),
                                         "limit": 1000}, timeout=20)
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        print(f"[intraday] {type(e).__name__}")
        return pd.DataFrame()
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows).iloc[:, :5]
    d.columns = ["t", "open", "high", "low", "close"]
    d["t"] = pd.to_datetime(d["t"], unit="ms", utc=True)
    return d.set_index("t").astype(float)
