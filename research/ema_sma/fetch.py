"""ema_sma · scarica le candele 4h BTCUSDT spot dall'archivio pubblico data.binance.vision (mensili dal 2017-08 + giornalieri
del mese in corso) e salva data/BTCUSDT_4h.csv.gz (UTC, apertura della candela). Solo dati, nessun rendimento."""
import io, sys, zipfile
from pathlib import Path
import pandas as pd, requests
HERE = Path(__file__).resolve().parent; D = HERE / "data"
BASE = "https://data.binance.vision/data/spot"
COLS = ["t", "open", "high", "low", "close", "volume", "ct", "qv", "n", "tb", "tq", "ig"]

def get(url):
    for _ in range(4):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404: return None
            r.raise_for_status()
            z = zipfile.ZipFile(io.BytesIO(r.content))
            df = pd.read_csv(z.open(z.namelist()[0]), header=None, names=COLS)
            if not str(df["t"].iloc[0]).isdigit(): df = df.iloc[1:]
            return df
        except Exception as e: err = e
    raise err

parts, miss = [], []
for m in pd.period_range("2017-08", pd.Timestamp.utcnow().strftime("%Y-%m"), freq="M"):
    df = get(f"{BASE}/monthly/klines/BTCUSDT/4h/BTCUSDT-4h-{m}.zip")
    if df is None:
        for d in pd.date_range(m.start_time, min(m.end_time, pd.Timestamp.utcnow().tz_localize(None)), freq="D"):
            dd = get(f"{BASE}/daily/klines/BTCUSDT/4h/BTCUSDT-4h-{d.date()}.zip")
            if dd is None: miss.append(str(d.date()))
            else: parts.append(dd)
    else: parts.append(df)
a = pd.concat(parts, ignore_index=True)
t = a["t"].astype("int64")
t = t.where(t < 10**14, t // 1000)          # dal 2025 l'archivio usa i microsecondi
a["time"] = pd.to_datetime(t, unit="ms")
a = a.drop_duplicates("time").sort_values("time").set_index("time")[["open", "high", "low", "close", "volume"]].astype(float)
a.to_csv(D / "BTCUSDT_4h.csv.gz")
print(len(a), a.index[0], a.index[-1], "mancanti:", miss)
