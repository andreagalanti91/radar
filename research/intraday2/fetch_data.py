"""Download and build the intraday2 research dataset.

Sources (public, no keys):
  * data.binance.vision  futures/um monthly klines 1h (+ daily klines for the current month)
  * data.binance.vision  futures/um monthly fundingRate (current month: OKX public funding history)
  * data.binance.vision  futures/um daily metrics (5m OI + long/short ratios, from 2021-12)

Raw zips are cached outside the repo (RAW dir, default: $INTRADAY2_RAW or ~/.cache/intraday2_raw).
Outputs (csv.gz, small) go to research/intraday2/data/:
  {SYM}_1h.csv.gz       ts,open,high,low,close,volume,quote_volume,trades,taker_buy_volume,taker_buy_quote
  {SYM}_funding.csv.gz  ts,rate,interval_h,source
  {SYM}_metrics_1h.csv.gz  ts,oi,oi_value,top_acc_ls,top_pos_ls,glob_acc_ls,taker_ls   (last 5m sample in each hour)
  data_checks.txt       data quality log

Run:  python3 research/intraday2/fetch_data.py            (incremental, cached)
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
RAW = os.environ.get("INTRADAY2_RAW", os.path.expanduser("~/.cache/intraday2_raw"))
BASE = "https://data.binance.vision/data/futures/um"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
OKX_ID = {"BTCUSDT": "BTC-USDT-SWAP", "ETHUSDT": "ETH-USDT-SWAP", "SOLUSDT": "SOL-USDT-SWAP"}
START = date(2020, 9, 1)
METRICS_START = date(2021, 12, 1)
LOG: list[str] = []


def log(msg: str) -> None:
    print(msg)
    LOG.append(msg)


def fetch(url: str, dest: str) -> str | None:
    """Download url to dest with curl (cached). Returns path or None on 404/failure."""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    if os.path.exists(dest + ".404"):
        return None
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    r = subprocess.run(["curl", "-sS", "-L", "--retry", "3", "-o", tmp, "-w", "%{http_code}", url],
                       capture_output=True, text=True, timeout=120)
    code = r.stdout.strip()
    if code == "200":
        os.replace(tmp, dest)
        return dest
    if os.path.exists(tmp):
        os.remove(tmp)
    if code == "404":
        open(dest + ".404", "w").close() if not _is_recent(url) else None
    return None


def _is_recent(url: str) -> bool:
    # do not memoise 404s for files that may still be published (last ~10 days / current month)
    today = datetime.now(timezone.utc).date()
    for d in range(0, 40):
        s = (today - timedelta(days=d))
        if s.isoformat() in url or s.strftime("%Y-%m") + ".zip" in url:
            return True
    return False


def read_zip_csv(path: str, names: list[str]) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        raw = z.read(z.namelist()[0])
    first = raw[:200].decode("utf-8", "ignore").split("\n")[0]
    header = 0 if any(c.isalpha() for c in first.split(",")[0]) else None
    df = pd.read_csv(io.BytesIO(raw), header=header)
    df = df.iloc[:, : len(names)]
    df.columns = names
    return df


def months(a: date, b: date):
    y, m = a.year, a.month
    while (y, m) <= (b.year, b.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


KL_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
           "trades", "taker_buy_volume", "taker_buy_quote", "ignore"]


def build_klines(sym: str, today: date) -> pd.DataFrame:
    cur_month = (today.year, today.month)
    jobs = []
    for y, m in months(START, today):
        if (y, m) == cur_month:
            d = date(y, m, 1)
            while d < today:
                f = f"{sym}-1h-{d.isoformat()}.zip"
                jobs.append((f"{BASE}/daily/klines/{sym}/1h/{f}", os.path.join(RAW, "klines", sym, f)))
                d += timedelta(days=1)
        else:
            f = f"{sym}-1h-{y}-{m:02d}.zip"
            jobs.append((f"{BASE}/monthly/klines/{sym}/1h/{f}", os.path.join(RAW, "klines", sym, f)))
    with ThreadPoolExecutor(16) as ex:
        paths = list(ex.map(lambda j: fetch(*j), jobs))
    missing = [j[0].rsplit("/", 1)[1] for j, p in zip(jobs, paths) if p is None]
    if missing:
        log(f"  {sym} klines: {len(missing)} files not available: {missing[:5]}{'...' if len(missing) > 5 else ''}")
    frames = [read_zip_csv(p, KL_COLS) for p in paths if p]
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["open_time"].astype("int64"), unit="ms", utc=True)
    df = df[["ts", "open", "high", "low", "close", "volume", "quote_volume", "trades",
             "taker_buy_volume", "taker_buy_quote"]]
    return df


def build_funding(sym: str, today: date) -> pd.DataFrame:
    jobs = []
    for y, m in months(START, today):
        f = f"{sym}-fundingRate-{y}-{m:02d}.zip"
        jobs.append((f"{BASE}/monthly/fundingRate/{sym}/{f}", os.path.join(RAW, "funding", sym, f)))
    with ThreadPoolExecutor(8) as ex:
        paths = list(ex.map(lambda j: fetch(*j), jobs))
    frames = [read_zip_csv(p, ["calc_time", "interval_h", "rate"]) for p in paths if p]
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["calc_time"].astype("int64"), unit="ms", utc=True).dt.floor("h")
    df["source"] = "binance"
    df = df[["ts", "rate", "interval_h", "source"]]
    # Fill the tail (current month not yet published) from OKX public funding history.
    last = df["ts"].max()
    okx = okx_funding(sym, last)
    if len(okx):
        log(f"  {sym} funding: {len(okx)} OKX rows appended after {last} (Binance monthly not yet published)")
        df = pd.concat([df, okx], ignore_index=True)
    return df


def okx_funding(sym: str, after: pd.Timestamp) -> pd.DataFrame:
    rows, before = [], ""
    for _ in range(10):
        url = f"https://www.okx.com/api/v5/public/funding-rate-history?instId={OKX_ID[sym]}&limit=100{before}"
        r = subprocess.run(["curl", "-sS", url], capture_output=True, text=True, timeout=30)
        try:
            data = json.loads(r.stdout).get("data", [])
        except Exception:
            log(f"  {sym} OKX funding: bad response")
            break
        if not data:
            break
        rows += data
        oldest = min(int(d["fundingTime"]) for d in data)
        if pd.Timestamp(oldest, unit="ms", tz="UTC") <= after:
            break
        before = f"&after={oldest}"
    if not rows:
        return pd.DataFrame(columns=["ts", "rate", "interval_h", "source"])
    o = pd.DataFrame({"ts": pd.to_datetime([int(d["fundingTime"]) for d in rows], unit="ms", utc=True),
                      "rate": [float(d.get("realizedRate") or d["fundingRate"]) for d in rows]})
    o = o[o["ts"] > after].drop_duplicates("ts").sort_values("ts")
    o["interval_h"] = 8
    o["source"] = "okx"
    return o


MET_COLS = ["create_time", "symbol", "oi", "oi_value", "top_acc_ls", "top_pos_ls", "glob_acc_ls", "taker_ls"]


def build_metrics(sym: str, today: date) -> pd.DataFrame:
    jobs = []
    d = METRICS_START
    while d < today:
        f = f"{sym}-metrics-{d.isoformat()}.zip"
        jobs.append((f"{BASE}/daily/metrics/{sym}/{f}", os.path.join(RAW, "metrics", sym, f)))
        d += timedelta(days=1)
    with ThreadPoolExecutor(24) as ex:
        paths = list(ex.map(lambda j: fetch(*j), jobs))
    missing = [j[0].rsplit("-metrics-", 1)[1][:10] for j, p in zip(jobs, paths) if p is None]
    if missing:
        log(f"  {sym} metrics: {len(missing)} daily files missing (e.g. {missing[:6]})")
    frames = []
    for p in paths:
        if not p:
            continue
        try:
            frames.append(read_zip_csv(p, MET_COLS))
        except Exception as e:  # corrupt file: skip, never invent
            log(f"  {sym} metrics: unreadable {os.path.basename(p)}: {e}")
    df = pd.concat(frames, ignore_index=True)
    df["t"] = pd.to_datetime(df["create_time"], utc=True)
    for c in MET_COLS[2:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # Sample at the hour: last 5m sample with time <= hour close. Bar opened at ts closes at ts+1h,
    # so we label by bar-open ts the value observed at ts+1h (i.e. known at bar close).
    df = df.sort_values("t").drop_duplicates("t")
    df["ts"] = (df["t"] - pd.Timedelta(minutes=1)).dt.floor("h")  # 01:00 sample -> bar 00:00
    h = df.groupby("ts")[MET_COLS[2:]].last().reset_index()
    return h


def okx_fill_gaps(sym: str, df: pd.DataFrame, max_gap_h: int = 96) -> pd.DataFrame:
    """Fill missing 1h bars (gaps <= max_gap_h, missing in the Binance archive) with OKX swap 1H OHLC.
    Filled bars carry filled=1 and NaN volumes (OKX volume is not comparable with Binance)."""
    df = df.sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    df["filled"] = 0
    gaps = df["ts"].diff()
    add = []
    for i in np.flatnonzero((gaps > pd.Timedelta("1h")).to_numpy()):
        t0, t1 = df["ts"].iloc[i - 1], df["ts"].iloc[i]
        if (t1 - t0) > pd.Timedelta(hours=max_gap_h):
            continue
        url = (f"https://www.okx.com/api/v5/market/history-candles?instId={OKX_ID[sym]}&bar=1H"
               f"&after={int(t1.timestamp() * 1000)}&limit=100")
        r = subprocess.run(["curl", "-sS", url], capture_output=True, text=True, timeout=30)
        try:
            rows = json.loads(r.stdout).get("data", [])
        except Exception:
            rows = []
        got = [(pd.Timestamp(int(x[0]), unit="ms", tz="UTC"), *map(float, x[1:5])) for x in rows]
        got = [g for g in got if t0 < g[0] < t1]
        need = int((t1 - t0) / pd.Timedelta("1h")) - 1
        log(f"  {sym} gap {t0:%Y-%m-%d %H:%M} -> {t1:%Y-%m-%d %H:%M}: {need} bars missing, {len(got)} filled from OKX")
        for ts, o, h, l, c in got:
            add.append({"ts": ts, "open": o, "high": h, "low": l, "close": c, "filled": 1})
    if add:
        df = pd.concat([df, pd.DataFrame(add)], ignore_index=True).sort_values("ts").reset_index(drop=True)
    return df


def checks_ohlc(sym: str, df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)
    df = df.sort_values("ts")
    dup = df["ts"].duplicated().sum()
    df = df.drop_duplicates("ts", keep="last").reset_index(drop=True)
    gaps = df["ts"].diff().dt.total_seconds().div(3600)
    big = df.loc[gaps > 1, "ts"]
    bad = ((df["high"] < df[["open", "close"]].max(axis=1)) | (df["low"] > df[["open", "close"]].min(axis=1))
           | (df["low"] <= 0)).sum()
    ret = np.log(df["close"]).diff().abs()
    out = df.loc[ret > 0.15, ["ts", "close"]]
    zero = (df["volume"] == 0).sum()
    log(f"  {sym} 1h: {n0} rows, {dup} duplicates removed, monotonic={df['ts'].is_monotonic_increasing}, "
        f"{df.ts.min()} -> {df.ts.max()}")
    log(f"  {sym} 1h: {len(big)} gaps >1h (missing {int((gaps[gaps > 1] - 1).sum())} bars); "
        + ", ".join(f"{t:%Y-%m-%d %H:%M} ({g:.0f}h)" for t, g in zip(big, gaps[gaps > 1])))
    log(f"  {sym} 1h: OHLC inconsistencies={bad}, zero-volume bars={zero}, |1h log-ret|>15%: "
        + (", ".join(f"{t:%Y-%m-%d %H:%M}" for t in out['ts']) or "none"))
    return df


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    today = datetime.now(timezone.utc).date()
    log(f"# intraday2 data build {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC (raw cache: {RAW})")
    for sym in SYMBOLS:
        log(f"## {sym}")
        k = build_klines(sym, today)
        checks_ohlc(sym, k)  # raw archive checks
        k = checks_ohlc(sym, okx_fill_gaps(sym, k))  # after OKX gap fill
        k.to_csv(os.path.join(OUT, f"{sym}_1h.csv.gz"), index=False, float_format="%.10g")
        f = build_funding(sym, today).sort_values("ts")
        fd = f["ts"].duplicated().sum()
        f = f.drop_duplicates("ts", keep="first")
        iv = f["interval_h"].value_counts().to_dict()
        fg = f["ts"].diff().dt.total_seconds().div(3600)
        log(f"  {sym} funding: {len(f)} rows {f.ts.min()} -> {f.ts.max()}, dup={fd}, intervals={iv}, "
            f"gaps>8h={int((fg > 8.5).sum())}, |rate|>0.5%: {int((f.rate.abs() > 0.005).sum())}, "
            f"mean={f.rate.mean():.6f}")
        f.to_csv(os.path.join(OUT, f"{sym}_funding.csv.gz"), index=False, float_format="%.10g")
        m = build_metrics(sym, today)
        mg = m["ts"].diff().dt.total_seconds().div(3600)
        log(f"  {sym} metrics(1h): {len(m)} rows {m.ts.min()} -> {m.ts.max()}, gaps>1h={int((mg > 1).sum())}, "
            f"NaN top_acc_ls={int(m.top_acc_ls.isna().sum())}, NaN oi={int(m.oi.isna().sum())}")
        m.to_csv(os.path.join(OUT, f"{sym}_metrics_1h.csv.gz"), index=False, float_format="%.8g")
    with open(os.path.join(OUT, "data_checks.txt"), "w") as fh:
        fh.write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    sys.exit(main())
