"""Scarica spot 1d (API), perp 1d con taker buy (archivio mensile+giornaliero) e funding (archivio mensile) per 12 simboli."""
import io, sys, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
import pandas as pd, requests
OUT = Path(__file__).resolve().parent / "data"
ARC = "https://data.binance.vision/data/futures/um"
S = requests.Session()
SYMS = sys.argv[1:] or "BTC ETH BNB XRP SOL TRX HYPE ZEC XMR DOGE LINK ADA".split()
COLS = ["t", "open", "high", "low", "close", "volume", "ct", "qv", "n", "tbv", "tbqv", "ig"]

def zcsv(url):
    r = S.get(url, timeout=60)
    if r.status_code != 200: return None
    z = zipfile.ZipFile(io.BytesIO(r.content)); raw = z.read(z.namelist()[0]).decode()
    first = raw.split("\n", 1)[0]
    hdr = not first[:1].isdigit()
    return pd.read_csv(io.StringIO(raw), header=0 if hdr else None)

def kl(df):
    df = df.iloc[:, :12].copy(); df.columns = COLS
    df["date"] = pd.to_datetime(pd.to_numeric(df["t"]), unit="ms").dt.normalize()
    return df.set_index("date")[["open", "high", "low", "close", "volume", "tbv"]].astype(float)

months = pd.period_range("2019-09", "2026-10", freq="M")
days = [date(2026, 11, 1) + timedelta(d) for d in range(10)]

def one(s):
    p = f"{s}USDT"; rows, st = [], 1567296000000
    while True:
        r = S.get("https://data-api.binance.vision/api/v3/klines", params=dict(symbol=p, interval="1d", startTime=st, limit=1000), timeout=30).json()
        if not isinstance(r, list) or not r: break
        rows += r; st = r[-1][0] + 86400000
        if len(r) < 1000: break
    if rows: kl(pd.DataFrame(rows)).to_csv(OUT / f"{s}_spot.csv")
    fr = [zcsv(f"{ARC}/monthly/klines/{p}/1d/{p}-1d-{m}.zip") for m in months] + [zcsv(f"{ARC}/daily/klines/{p}/1d/{p}-1d-{d}.zip") for d in days]
    fr = [kl(x) for x in fr if x is not None]
    if fr: pd.concat(fr).sort_index().loc[lambda x: ~x.index.duplicated(keep="last")].to_csv(OUT / f"{s}_perp.csv")
    fu = [zcsv(f"{ARC}/monthly/fundingRate/{p}/{p}-fundingRate-{m}.zip") for m in months]
    fu = [x for x in fu if x is not None]
    if fu:
        x = pd.concat(fu); x["date"] = pd.to_datetime(pd.to_numeric(x["calc_time"]), unit="ms").dt.normalize()
        x.groupby("date")["last_funding_rate"].sum().rename("funding").to_csv(OUT / f"{s}_funding.csv")
    return s, len(rows), sum(len(x) for x in fr), len(fu)

with ThreadPoolExecutor(6) as ex:
    for r in ex.map(one, SYMS): print(r, flush=True)
