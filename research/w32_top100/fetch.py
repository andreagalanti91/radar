"""w32_top100: spot 1d (data-api), perp 1d con taker buy (archivio mensile+giornaliero) e funding (archivio mensile) per le
monete di universe.csv (stesso metodo di top10_w3/fetch.py). Cache compressa in data/<SYM>_{spot,perp,funding}.csv.gz."""
import io, time, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
import pandas as pd, requests
HERE = Path(__file__).resolve().parent; OUT = HERE / "data"
ARC = "https://data.binance.vision/data/futures/um"
S = requests.Session()
COLS = ["t", "open", "high", "low", "close", "volume", "ct", "qv", "n", "tbv", "tbqv", "ig"]
RENAME = {"POL": "MATIC", "RENDER": "RNDR"}
months = pd.period_range("2019-09", "2026-10", freq="M")
days = [date(2026, 11, 1) + timedelta(d) for d in range(10)]

def get(url, **kw):
    for a in range(4):
        try:
            r = S.get(url, timeout=60, **kw)
            if r.status_code in (200, 404, 400): return r
        except requests.RequestException: pass
        time.sleep(2 + 3 * a)
    return None

def zcsv(url):
    r = get(url); time.sleep(0.05)
    if r is None or r.status_code != 200: return None
    z = zipfile.ZipFile(io.BytesIO(r.content)); raw = z.read(z.namelist()[0]).decode()
    hdr = not raw.split("\n", 1)[0][:1].isdigit()
    return pd.read_csv(io.StringIO(raw), header=0 if hdr else None)

def kl(df):
    df = df.iloc[:, :12].copy(); df.columns = COLS
    df["date"] = pd.to_datetime(pd.to_numeric(df["t"]), unit="ms").dt.normalize()
    return df.set_index("date")[["open", "high", "low", "close", "volume", "tbv"]].astype(float)

def spot(p):
    rows, st = [], 1567296000000
    while True:
        r = get("https://data-api.binance.vision/api/v3/klines", params=dict(symbol=p, interval="1d", startTime=st, limit=1000))
        r = r.json() if r is not None and r.status_code == 200 else []
        if not isinstance(r, list) or not r: break
        rows += r; st = r[-1][0] + 86400000
        if len(r) < 1000: break
        time.sleep(0.2)
    return kl(pd.DataFrame(rows)) if rows else None

def perp(p):
    fr = [zcsv(f"{ARC}/monthly/klines/{p}/1d/{p}-1d-{m}.zip") for m in months] + [zcsv(f"{ARC}/daily/klines/{p}/1d/{p}-1d-{d}.zip") for d in days]
    fr = [kl(x) for x in fr if x is not None]
    if not fr: return None
    x = pd.concat(fr).sort_index(); x = x[~x.index.duplicated(keep="last")]
    if p.startswith("1000"): x[["open", "high", "low", "close"]] /= 1000
    if p.startswith("1M"): x[["open", "high", "low", "close"]] /= 1e6
    return x

def funding(p):
    fu = [x for x in (zcsv(f"{ARC}/monthly/fundingRate/{p}/{p}-fundingRate-{m}.zip") for m in months) if x is not None]
    if not fu: return None
    x = pd.concat(fu); x["date"] = pd.to_datetime(pd.to_numeric(x["calc_time"]), unit="ms").dt.normalize()
    return x.groupby("date")["last_funding_rate"].sum().rename("funding").to_frame()

def stitch(new, old):
    if old is None: return new
    if new is None: return old
    return pd.concat([old[old.index < new.index[0]], new])

def one(row):
    t, pp = row.ticker, row.perp if isinstance(row.perp, str) else None
    if all((OUT / f"{t}_{k}.csv.gz").exists() for k in (("spot", "perp", "funding") if pp else ("spot",))): return t, "cache"
    o = RENAME.get(t)
    sp = stitch(spot(f"{t}USDT"), spot(f"{o}USDT") if o else None)
    if sp is not None: sp.to_csv(OUT / f"{t}_spot.csv.gz")
    if pp:
        pe = stitch(perp(pp), perp(f"{o}USDT") if o else None); fu = stitch(funding(pp), funding(f"{o}USDT") if o else None)
        if pe is not None: pe.to_csv(OUT / f"{t}_perp.csv.gz")
        if fu is not None: fu.to_csv(OUT / f"{t}_funding.csv.gz")
        return t, None if sp is None else len(sp), None if pe is None else len(pe), None if fu is None else len(fu)
    return t, None if sp is None else len(sp)

if __name__ == "__main__":
    u = pd.read_csv(HERE / "universe.csv"); u = u[u.escluso.isna() & ((u.spot == True) | u.perp.notna())]
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(one, u.itertuples()): print(r, flush=True)
