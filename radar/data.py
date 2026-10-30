"""Raccolta dati BTC (giornaliero) da fonti pubbliche, con cache CSV incrementale.

Fonti:
- Spot klines (con taker buy volume -> CVD spot): data-api.binance.vision
- Perp klines USDT-M (taker buy volume -> CVD perp): data.binance.vision (archivio)
  con fallback OKX per gli ultimi giorni non ancora archiviati
- Funding rate: archivio Binance mensile + OKX per il mese corrente
- Metrics (open interest, long/short ratio, taker ratio, 5m -> giornaliero): archivio Binance
- Fear & Greed index: alternative.me
"""
from __future__ import annotations

import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SYMBOL = "BTCUSDT"
START = date(2019, 9, 1)  # nascita del perp USDT-M Binance
METRICS_START = date(2021, 12, 1)
ARCHIVE = "https://data.binance.vision/data/futures/um"
KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
              "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]

_session = requests.Session()


def _get(url: str, params: dict | None = None, retries: int = 4) -> requests.Response | None:
    for i in range(retries):
        try:
            r = _session.get(url, params=params, timeout=30)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r
        except requests.RequestException:
            if i == retries - 1:
                raise
            time.sleep(2 ** (i + 1))
    return None


def _zip_csv(url: str, header_hint: str | None = None) -> pd.DataFrame | None:
    r = _get(url)
    if r is None:
        return None
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        raw = z.read(z.namelist()[0]).decode()
    first = raw.split("\n", 1)[0]
    has_header = header_hint is not None and header_hint in first
    return pd.read_csv(io.StringIO(raw), header=0 if has_header else None)


def _months(start: date, end: date):
    d = date(start.year, start.month, 1)
    while d <= end:
        yield d
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def _days(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _months_end(m: date) -> date:
    return date(m.year + (m.month == 12), m.month % 12 + 1, 1) - timedelta(days=1)


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _klines_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    df = df.iloc[:, :12].copy()
    df.columns = KLINE_COLS
    df = df[pd.to_numeric(df["open_time"], errors="coerce").notna()]
    ot = pd.to_numeric(df["open_time"]).astype("int64")
    # alcuni file recenti dello spot sono in microsecondi
    ot = ot.where(ot < 10**14, ot // 1000)
    df["date"] = pd.to_datetime(ot, unit="ms").dt.normalize()
    for c in ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_volume"]:
        df[c] = pd.to_numeric(df[c])
    return df.set_index("date")[["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_volume"]]


def _merge_cache(name: str, new: pd.DataFrame) -> pd.DataFrame:
    path = DATA_DIR / f"{name}.csv"
    if path.exists():
        old = pd.read_csv(path, index_col=0, parse_dates=True)
        new = pd.concat([old, new])
    new = new[~new.index.duplicated(keep="last")].sort_index()
    DATA_DIR.mkdir(exist_ok=True)
    new.to_csv(path)
    return new


def _cache_last(name: str) -> date | None:
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        return None
    idx = pd.read_csv(path, index_col=0, parse_dates=True, usecols=[0]).index
    return idx.max().date() if len(idx) else None


# ---------------------------------------------------------------- spot
def fetch_spot() -> pd.DataFrame:
    rows, start_ms = [], int(datetime(START.year, START.month, START.day, tzinfo=timezone.utc).timestamp() * 1000)
    while True:
        r = _get("https://data-api.binance.vision/api/v3/klines",
                 {"symbol": SYMBOL, "interval": "1d", "startTime": start_ms, "limit": 1000})
        batch = r.json()
        if not batch:
            break
        rows += batch
        start_ms = batch[-1][0] + 86_400_000
        if len(batch) < 1000:
            break
    df = _klines_to_daily(pd.DataFrame(rows))
    df = df[df.index.date < _today()]  # solo candele chiuse
    return _merge_cache("spot", df)


# ---------------------------------------------------------------- perp
def _okx_perp_daily() -> pd.DataFrame:
    r = _get("https://www.okx.com/api/v5/market/history-candles",
             {"instId": "BTC-USDT-SWAP", "bar": "1Dutc", "limit": 100})
    d = pd.DataFrame(r.json()["data"]).iloc[:, :8]
    d.columns = ["ts", "open", "high", "low", "close", "vol", "volCcy", "volQuote"]
    d["date"] = pd.to_datetime(pd.to_numeric(d["ts"]), unit="ms").dt.normalize()
    out = d.set_index("date").astype(float)
    out = out.rename(columns={"volCcy": "volume", "volQuote": "quote_volume"})
    return out[["open", "high", "low", "close", "volume", "quote_volume"]].sort_index()


def fetch_perp() -> pd.DataFrame:
    last = _cache_last("perp")
    today = _today()
    start = (last - timedelta(days=10)) if last else START  # riprova gli ultimi giorni: l'archivio può avere buchi
    frames = []
    this_month = date(today.year, today.month, 1)
    months = [m for m in _months(start, today) if m < this_month]
    days = list(_days(max(start, this_month), today - timedelta(days=1)))
    with ThreadPoolExecutor(8) as ex:
        for m, df in zip(months, ex.map(lambda m: _zip_csv(f"{ARCHIVE}/monthly/klines/{SYMBOL}/1d/{SYMBOL}-1d-{m:%Y-%m}.zip", "open_time"), months)):
            if df is not None:
                frames.append(_klines_to_daily(df))
            elif m >= START:  # mese appena chiuso non ancora archiviato: usa i file giornalieri
                days += [d for d in _days(max(m, start), min(_months_end(m), today - timedelta(days=1)))]
    with ThreadPoolExecutor(8) as ex:
        for df in ex.map(lambda d: _zip_csv(f"{ARCHIVE}/daily/klines/{SYMBOL}/1d/{SYMBOL}-1d-{d:%Y-%m-%d}.zip", "open_time"), days):
            if df is not None:
                frames.append(_klines_to_daily(df))
    new = pd.concat(frames) if frames else pd.DataFrame()
    if len(new):
        new["source"] = "binance"
    out = _merge_cache("perp", new) if len(new) else pd.read_csv(DATA_DIR / "perp.csv", index_col=0, parse_dates=True)
    out = out[out.get("source", "binance") == "binance"] if "source" in out else out
    # riempi gli ultimi giorni non ancora archiviati con OKX (taker buy stimato dopo, dalle metrics)
    have = set(out.index.date)
    missing = [d for d in _days(today - timedelta(days=60), today - timedelta(days=1)) if d not in have]
    if missing:
        okx = _okx_perp_daily()
        okx = okx[okx.index.isin(pd.to_datetime(missing))]
        if len(okx):
            okx["taker_buy_volume"] = float("nan")
            okx["source"] = "okx"
            out = pd.concat([out, okx]).sort_index()
    return out


# ---------------------------------------------------------------- funding
def fetch_funding() -> pd.DataFrame:
    last = _cache_last("funding")
    today = _today()
    # i giorni recenti arrivano da OKX; si riscaricano i mesi Binance per sovrascriverli appena archiviati
    start = (last - timedelta(days=45)) if last else START
    this_month = date(today.year, today.month, 1)
    months = [m for m in _months(start, today) if m < this_month]
    frames = []
    with ThreadPoolExecutor(8) as ex:
        for df in ex.map(lambda m: _zip_csv(f"{ARCHIVE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{m:%Y-%m}.zip", "calc_time"), months):
            if df is not None:
                df = df.rename(columns={"last_funding_rate": "rate"})
                if "calc_time" not in df:  # file senza header: calc_time, interval, rate
                    df = df.set_axis(["calc_time", "interval_h", "rate"][: len(df.columns)], axis=1)
                df["date"] = pd.to_datetime(pd.to_numeric(df["calc_time"]), unit="ms").dt.normalize()
                frames.append(df.groupby("date")["rate"].sum().to_frame("funding"))
    out = _merge_cache("funding", pd.concat(frames)) if frames else pd.read_csv(DATA_DIR / "funding.csv", index_col=0, parse_dates=True)
    # mese corrente da OKX (stesso ordine di grandezza del funding Binance)
    r = _get("https://www.okx.com/api/v5/public/funding-rate-history", {"instId": "BTC-USDT-SWAP", "limit": 100})
    okx = pd.DataFrame(r.json()["data"])
    if len(okx):
        okx["date"] = pd.to_datetime(pd.to_numeric(okx["fundingTime"]), unit="ms").dt.normalize()
        okx = okx.groupby("date")["realizedRate"].apply(lambda s: pd.to_numeric(s).sum()).to_frame("funding")
        okx = okx[(okx.index > out.index.max()) & (okx.index.date < today)]
        if len(okx):
            out = _merge_cache("funding", okx)
    return out


# ---------------------------------------------------------------- metrics (OI, L/S)
def _metrics_day(d: date) -> pd.DataFrame | None:
    df = _zip_csv(f"{ARCHIVE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{d:%Y-%m-%d}.zip", "create_time")
    if df is None or not len(df):
        return None
    for c in df.columns[2:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    tr = df["sum_taker_long_short_vol_ratio"]
    return pd.DataFrame({
        "oi": [df["sum_open_interest"].iloc[-1]],
        "oi_usd": [df["sum_open_interest_value"].iloc[-1]],
        "top_ls": [df["count_toptrader_long_short_ratio"].mean()],
        "top_ls_pos": [df["sum_toptrader_long_short_ratio"].mean()],
        "global_ls": [df["count_long_short_ratio"].mean()],
        "taker_buy_share": [(tr / (1 + tr)).mean()],
    }, index=pd.DatetimeIndex([pd.Timestamp(d)], name="date"))


def fetch_metrics() -> pd.DataFrame:
    last = _cache_last("metrics")
    start = (last - timedelta(days=3)) if last else METRICS_START
    days = list(_days(start, _today() - timedelta(days=1)))
    frames = []
    with ThreadPoolExecutor(16) as ex:
        for df in ex.map(_metrics_day, days):
            if df is not None:
                frames.append(df)
    if frames:
        return _merge_cache("metrics", pd.concat(frames))
    return pd.read_csv(DATA_DIR / "metrics.csv", index_col=0, parse_dates=True)


# ---------------------------------------------------------------- fear & greed
def fetch_fng() -> pd.DataFrame:
    r = _get("https://api.alternative.me/fng/", {"limit": 0, "format": "json"})
    d = pd.DataFrame(r.json()["data"])
    d["date"] = pd.to_datetime(pd.to_numeric(d["timestamp"]), unit="s").dt.normalize()
    out = d.set_index("date")[["value"]].astype(float).rename(columns={"value": "fng"})
    return _merge_cache("fng", out)


def update_all(verbose: bool = True) -> dict[str, pd.DataFrame]:
    out = {}
    for name, fn in [("spot", fetch_spot), ("perp", fetch_perp), ("funding", fetch_funding),
                     ("metrics", fetch_metrics), ("fng", fetch_fng)]:
        t = time.time()
        out[name] = fn()
        if verbose:
            df = out[name]
            print(f"[data] {name:8s} {len(df):5d} righe  {df.index.min().date()} -> {df.index.max().date()}  ({time.time()-t:.1f}s)")
    return out


def load_all() -> dict[str, pd.DataFrame]:
    return {n: pd.read_csv(DATA_DIR / f"{n}.csv", index_col=0, parse_dates=True)
            for n in ["spot", "perp", "funding", "metrics", "fng"]}
