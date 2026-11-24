"""Opzioni · prezzo di regolamento approssimato: apertura della candela oraria Binance BTCUSDT delle 08:00 UTC di ogni giorno
(le opzioni Deribit scadono alle 08:00 UTC) e delle 12:00 UTC (prezzo del momento per la superficie, ADDENDUM-1 punto 3). Fonte pubblica: data-api.binance.vision /api/v3/klines (1h).
Uso una volta: python3 research/opzioni_studio/op_fetch_0800.py → research/opzioni_studio/cache/btc_0800.csv
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent / "cache" / "btc_0800.csv"
URL = "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&startTime={}&limit=1000"


def main(start: str = "2017-12-01") -> None:
    t = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    end = int(pd.Timestamp.now(tz="UTC").timestamp() * 1000)
    rows = []
    while t < end:
        with urllib.request.urlopen(URL.format(t), timeout=30) as r:
            k = json.loads(r.read())
        if not k:
            break
        rows += [(x[0], float(x[1])) for x in k]
        t = k[-1][0] + 3600_000
        time.sleep(0.15)
    h = pd.DataFrame(rows, columns=["t", "open"]).drop_duplicates("t")
    h["t"] = pd.to_datetime(h["t"], unit="ms")
    h["date"] = h["t"].dt.normalize()
    out = h[h["t"].dt.hour == 8].set_index("date")[["open"]].rename(columns={"open": "open_0800"})
    out["open_1200"] = h[h["t"].dt.hour == 12].set_index("date")["open"]
    OUT.parent.mkdir(exist_ok=True)
    out.to_csv(OUT)
    print(OUT, len(out), out.index[0], out.index[-1], int(out["open_1200"].isna().sum()), "mezzogiorni mancanti")


if __name__ == "__main__":
    main()
