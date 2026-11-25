"""Scarica MVRV giornaliero di BTC (CoinMetrics community API, CapMVRVCur) in mvrv.csv. Uso: python3 up_fetch.py"""
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
P = dict(assets="btc", metrics="CapMVRVCur", frequency="1d", page_size=10000, start_time="2011-01-01")

rows, tok = [], None
while True:
    q = dict(P, **({"next_page_token": tok} if tok else {}))
    j = requests.get(URL, params=q, timeout=60).json()
    rows += j.get("data", [])
    tok = j.get("next_page_token")
    if not tok:
        break
d = pd.DataFrame(rows)
d["date"] = pd.to_datetime(d["time"]).dt.tz_localize(None).dt.normalize()
d["mvrv"] = d["CapMVRVCur"].astype(float)
d = d[["date", "mvrv"]].drop_duplicates("date").sort_values("date")
d.to_csv(HERE / "mvrv.csv", index=False)
print(len(d), d["date"].iloc[0].date(), d["date"].iloc[-1].date(), d.tail(3).to_string(index=False))
