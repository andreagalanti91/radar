"""w32_multi: indici da Yahoo (stessa funzione di research/multi_asset/fetch.py, taglio 20/11/2026) ed ETH spot Binance dal 2017."""
import sys, time
from pathlib import Path
import pandas as pd, requests
HERE = Path(__file__).resolve().parent; D = HERE / "data"
sys.path.insert(0, str(HERE.parent / "multi_asset"))
from fetch import yahoo  # noqa: E402
IDX = {"NDX": "^NDX", "DJI": "^DJI", "DAX": "^GDAXI", "FTSEMIB": "FTSEMIB.MI", "N225": "^N225", "RUT": "^RUT", "SX5E": "^STOXX50E"}
for n, s in (IDX.items() if "binance" not in sys.argv else []):
    try:
        df = yahoo(s); df.to_csv(D / f"{n}.csv.gz"); print(n, s, df.index[0].date(), df.index[-1].date(), len(df))
    except Exception as e: print(n, s, "ERRORE", e)
    time.sleep(0.5)
# ETH e BTC spot Binance dal 17/08/2017 (data-api pubblica, come top10_w3/fetch.py)
for sym in ("ETH", "BTC"):
    rows, st = [], 1500000000000
    while True:
        r = requests.get("https://data-api.binance.vision/api/v3/klines", params=dict(symbol=f"{sym}USDT", interval="1d", startTime=st, limit=1000), timeout=30).json()
        if not isinstance(r, list) or not r: break
        rows += r; st = r[-1][0] + 86400000
        if len(r) < 1000: break
    df = pd.DataFrame([x[:6] for x in rows], columns=["t", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["t"], unit="ms").dt.normalize()
    df.set_index("date")[["open", "high", "low", "close", "volume"]].astype(float).to_csv(D / f"{sym}_spot_long.csv.gz")
    print(sym, "spot", df["date"].iloc[0].date(), df["date"].iloc[-1].date(), len(df))
