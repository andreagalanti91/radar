"""Raccolta delle liquidazioni reali di BTC (OKX, perpetual USDT) da oggi in avanti.

Lo storico delle liquidazioni non è disponibile gratis: lo costruiamo noi. Ogni ora si scaricano le
liquidazioni recenti e si aggiungono a data/liquidations.csv senza doppioni. Fra qualche mese ci saranno
dati reali per testare segnali basati sulle liquidazioni (oggi usiamo solo un sostituto).
"""
from __future__ import annotations

import pandas as pd
import requests

from .data import DATA_DIR

URL = "https://www.okx.com/api/v5/public/liquidation-orders"
CT_VAL = 0.01  # BTC per contratto BTC-USDT-SWAP


def collect() -> int:
    try:
        r = requests.get(URL, params={"instType": "SWAP", "uly": "BTC-USDT", "state": "filled", "limit": 100}, timeout=20)
        r.raise_for_status()
        det = (r.json().get("data") or [{}])[0].get("details", [])
    except Exception as e:
        print(f"[liquidazioni] {type(e).__name__}")
        return 0
    if not det:
        return 0
    df = pd.DataFrame(det)
    df["time"] = pd.to_datetime(pd.to_numeric(df["ts"]), unit="ms")
    df["btc"] = pd.to_numeric(df["sz"]) * CT_VAL
    df["price"] = pd.to_numeric(df["bkPx"])
    df["usd"] = df["btc"] * df["price"]
    df["liquidated"] = df["posSide"]  # long = long liquidati (vendite forzate), short = short liquidati
    new = df[["time", "liquidated", "btc", "price", "usd"]]
    path = DATA_DIR / "liquidations.csv"
    if path.exists():
        new = pd.concat([pd.read_csv(path, parse_dates=["time"]), new])
    new = new.drop_duplicates().sort_values("time")
    new.to_csv(path, index=False)
    return len(new)
