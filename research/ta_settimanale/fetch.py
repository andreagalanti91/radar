"""Scarica lo storico giornaliero BTC/USD 2011-09 → 2013-12 dall'API pubblica Bitstamp (nessuna chiave)."""
import csv, json, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
OUT = Path(__file__).resolve().parent / "data/bitstamp_1d_2011_2013.csv"
start = int(datetime(2011, 9, 1, tzinfo=timezone.utc).timestamp())
end = int(datetime(2014, 1, 1, tzinfo=timezone.utc).timestamp())
rows = {}
while start < end:
    url = f"https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=86400&limit=1000&start={start}"
    req = urllib.request.Request(url, headers={"User-Agent": "python-research-client"})
    d = json.load(urllib.request.urlopen(req, timeout=30))["data"]["ohlc"]
    if not d:
        break
    for x in d:
        ts = int(x["timestamp"])
        if ts < end:
            rows[ts] = x
    start = int(d[-1]["timestamp"]) + 86400
    time.sleep(0.5)
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["date", "open", "high", "low", "close", "volume"])
    for ts in sorted(rows):
        x = rows[ts]
        w.writerow([datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d"), x["open"], x["high"], x["low"], x["close"], x["volume"]])
print(len(rows), OUT)
