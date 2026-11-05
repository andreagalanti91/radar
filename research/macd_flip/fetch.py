"""Scarica klines giornaliere spot Binance (data-api.binance.vision) -> data/<SYM>_1d.csv"""
import os, time, requests, pandas as pd
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
def fetch(sym):
    rows, start = [], 1483228800000  # 2017-01-01
    while True:
        r = requests.get("https://data-api.binance.vision/api/v3/klines",
                         params=dict(symbol=sym, interval="1d", startTime=start, limit=1000), timeout=30)
        r.raise_for_status(); b = r.json()
        if not b: break
        rows += b; start = b[-1][0] + 86400000
        if len(b) < 1000: break
        time.sleep(0.3)
    df = pd.DataFrame(rows).iloc[:, :6]; df.columns = ["ts","open","high","low","close","volume"]
    df["date"] = pd.to_datetime(df.ts, unit="ms").dt.strftime("%Y-%m-%d")
    df[["date","open","high","low","close","volume"]].to_csv(os.path.join(D, f"{sym}_1d.csv"), index=False)
    print(sym, len(df), df.date.iloc[0], df.date.iloc[-1])
if __name__ == "__main__":
    os.makedirs(D, exist_ok=True)
    for s in ["BTCUSDT","ETHUSDT","SOLUSDT"]: fetch(s)
