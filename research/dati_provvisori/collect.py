"""Scarica le fonti pubbliche per lo studio dei dati provvisori (nessuna chiave, nessuno scraping).

- OKX: candele giornaliere BTC-USDT-SWAP (1Dutc, storia completa) e funding pagato (funding-rate-history, ~3 mesi:
  l'API pubblica non va più indietro).
- data.binance.vision: premiumIndexKlines 1m di BTCUSDT (mensili dal 2021, giornalieri per il mese corrente) per ricostruire
  il funding Binance con la formula pubblica.
- Copia dei CSV del tool (spot, perp, funding, metrics, fng) dal ramo dati remoto, passata come cartella.
Uso: python3 -I collect.py CARTELLA_RAW CARTELLA_CSV_TOOL
"""
from __future__ import annotations

import io
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

S = requests.Session()
OKX = "https://www.okx.com/api/v5"
ARCH = "https://data.binance.vision/data/futures/um"


def okx_pages(url: str, params: dict, key: int = 0, pages: int = 60) -> list:
    rows, after = [], None
    for _ in range(pages):
        p = dict(params, **({"after": after} if after else {}))
        d = S.get(url, params=p, timeout=30).json()["data"]
        if not d:
            break
        rows += d
        after = d[-1][key] if isinstance(d[-1], list) else d[-1]["fundingTime"]
        time.sleep(0.15)
    return rows


def okx_daily(raw: Path) -> pd.DataFrame:
    rows = okx_pages(f"{OKX}/market/history-candles", {"instId": "BTC-USDT-SWAP", "bar": "1Dutc", "limit": 100})
    d = pd.DataFrame(rows).iloc[:, :9]
    d.columns = ["ts", "open", "high", "low", "close", "vol", "volCcy", "volQuote", "confirm"]
    d["date"] = pd.to_datetime(pd.to_numeric(d["ts"]), unit="ms").dt.normalize()
    d = d.set_index("date").drop(columns=["ts"]).astype(float).sort_index()
    d = d[~d.index.duplicated()]
    d.to_csv(raw / "okx_perp_1d.csv")
    return d


def okx_funding(raw: Path) -> pd.DataFrame:
    rows = okx_pages(f"{OKX}/public/funding-rate-history", {"instId": "BTC-USDT-SWAP", "limit": 100})
    d = pd.DataFrame(rows)
    d["t"] = pd.to_datetime(pd.to_numeric(d["fundingTime"]), unit="ms")
    d["realizedRate"] = pd.to_numeric(d["realizedRate"])
    d["fundingRate"] = pd.to_numeric(d["fundingRate"])
    d = d.drop_duplicates("t").sort_values("t")[["t", "fundingRate", "realizedRate", "method", "formulaType"]]
    d.to_csv(raw / "okx_funding_8h.csv", index=False)
    return d


def _zip(url: str) -> pd.DataFrame | None:
    for i in range(4):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                raw = z.read(z.namelist()[0]).decode()
            hdr = 0 if raw.startswith("open_time") else None
            df = pd.read_csv(io.StringIO(raw), header=hdr).iloc[:, :5]
            df.columns = ["open_time", "open", "high", "low", "close"]
            return df
        except requests.RequestException:
            time.sleep(2 ** i)
    return None


def premium(raw: Path, start: date = date(2021, 1, 1), today: date | None = None) -> pd.DataFrame:
    today = today or date.today()
    months, m = [], start
    this = date(today.year, today.month, 1)
    while m < this:
        months.append(m)
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    days = [this + timedelta(days=i) for i in range((today - this).days)]
    urls = [f"{ARCH}/monthly/premiumIndexKlines/BTCUSDT/1m/BTCUSDT-1m-{m:%Y-%m}.zip" for m in months]
    urls += [f"{ARCH}/daily/premiumIndexKlines/BTCUSDT/1m/BTCUSDT-1m-{d:%Y-%m-%d}.zip" for d in days]
    with ThreadPoolExecutor(6) as ex:
        frames = [x for x in ex.map(_zip, urls) if x is not None]
    df = pd.concat(frames)
    ot = pd.to_numeric(df["open_time"], errors="coerce")
    df = df[ot.notna()]
    ot = ot[ot.notna()].astype("int64")
    ot = ot.where(ot < 10**14, ot // 1000)
    df = pd.DataFrame({"t": pd.to_datetime(ot.values, unit="ms"),
                       "close": pd.to_numeric(df["close"]).values}).drop_duplicates("t").sort_values("t")
    df.to_parquet(raw / "premium_1m.parquet") if _has_pyarrow() else df.to_csv(raw / "premium_1m.csv.gz", index=False)
    return df


def _has_pyarrow() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    raw = Path(sys.argv[1])
    raw.mkdir(parents=True, exist_ok=True)
    what = sys.argv[2:] or ["okx", "funding", "premium"]
    if "okx" in what:
        d = okx_daily(raw)
        print("OKX 1d:", d.index.min().date(), "→", d.index.max().date(), len(d))
    if "funding" in what:
        d = okx_funding(raw)
        print("OKX funding:", d.t.min(), "→", d.t.max(), len(d))
    if "premium" in what:
        d = premium(raw)
        print("premium 1m:", d.t.min(), "→", d.t.max(), len(d))
