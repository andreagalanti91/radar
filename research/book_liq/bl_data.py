"""Dati dello studio book_liq (PREREG.md): candele 1m e 1h Binance spot, OI Binance orario, mappe stimate, on-chain, S/R.
Uso: python research/book_liq/bl_data.py   → cache in $BL_WORK (default /tmp/radar-work/book_liq)
"""
from __future__ import annotations

import io
import os
import sys
import time
import zipfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import levels, liqmap, liqsnap  # noqa: E402

DATA = ROOT / "data"
WORK = Path(os.environ.get("BL_WORK", "/tmp/radar-work/book_liq")); WORK.mkdir(parents=True, exist_ok=True)
S = requests.Session()


def klines(interval: str, start: pd.Timestamp, end: pd.Timestamp | None = None) -> pd.DataFrame:
    out, t = [], int(start.timestamp() * 1000)
    end_ms = int((end or pd.Timestamp.utcnow().tz_localize(None)).timestamp() * 1000)
    while t < end_ms:
        r = S.get("https://data-api.binance.vision/api/v3/klines",
                  params={"symbol": "BTCUSDT", "interval": interval, "startTime": t, "limit": 1000}, timeout=30).json()
        if not r:
            break
        out += r
        t = int(r[-1][0]) + 1
        time.sleep(0.05)
    now = time.time() * 1000
    k = pd.DataFrame([[pd.to_datetime(x[0], unit="ms"), *map(float, x[1:5])] for x in out if int(x[6]) < now],
                     columns=["t", "open", "high", "low", "close"]).drop_duplicates("t").set_index("t")
    return k


def m1() -> pd.DataFrame:
    p = WORK / "m1.pkl"
    if p.exists() and time.time() - p.stat().st_mtime < 3 * 3600:
        return pd.read_pickle(p)
    k = klines("1m", pd.Timestamp("2026-11-06"))
    k.to_pickle(p)
    return k


def oi_hourly() -> pd.Series:
    p = WORK / "oi.pkl"
    if p.exists():
        return pd.read_pickle(p)
    fr = []
    d0 = date(2026, 10, 12)
    while d0 <= date(2026, 11, 22):
        r = S.get(f"https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{d0:%Y-%m-%d}.zip", timeout=30)
        if r.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                fr.append(pd.read_csv(z.open(z.namelist()[0]))[["create_time", "sum_open_interest_value"]])
        d0 += timedelta(days=1)
    m = pd.concat(fr)
    m["t"] = pd.to_datetime(m["create_time"])
    v = pd.to_numeric(m["sum_open_interest_value"], errors="coerce")
    oi = v.where(v > 0).groupby(m["t"].dt.floor("h")).last()   # ultimo valore dentro l'ora (noto alla chiusura)
    oi.to_pickle(p)
    return oi


def h1() -> pd.DataFrame:
    p = WORK / "h1.pkl"
    if p.exists() and time.time() - p.stat().st_mtime < 3 * 3600:
        return pd.read_pickle(p)
    a = pd.read_csv(DATA / "spot_1h.csv", parse_dates=["t"]).set_index("t")
    a = a[a.index >= "2026-10-10"]
    b = klines("1h", a.index[-1] + pd.Timedelta(hours=1))
    h = pd.concat([a[["open", "high", "low", "close"]], b]).sort_index()
    h = h[~h.index.duplicated()]
    oi = oi_hourly()
    # candela con indice = inizio ora; OI "dell'ora" = ultimo valore dentro l'ora → stessa convenzione di liqmap.binance_hourly
    h["oi_usd"] = oi.reindex(h.index).ffill(limit=2)
    h.loc[h.index > oi.dropna().index.max(), "oi_usd"] = np.nan
    h.to_pickle(p)
    return h


def est_map(h: pd.DataFrame, T: pd.Timestamp) -> tuple[list[dict], list[dict], float] | None:
    """Mappa stimata con le sole ore CHIUSE prima di T (504 ore): cluster densi long sotto e short sopra, prezzo di riferimento."""
    win = h[(h.index < T.floor("h") - pd.Timedelta(hours=0)) & (h.index >= T.floor("h") - pd.Timedelta(hours=liqmap.LOOKBACK_H + 1))]
    win = win[win.index + pd.Timedelta(hours=1) <= T]                 # solo ore chiuse a T
    win = win[["high", "low", "close", "oi_usd"]].dropna()
    if len(win) < 400:
        return None
    p = float(win["close"].iloc[-1])
    w = liqmap.window(liqmap.build(win), p, 0.12)
    dn = [c for c in liqmap.clusters(w, p, "long") if c["sig"]]
    up = [c for c in liqmap.clusters(w, p, "short") if c["sig"]]
    k = (w["price"] - p).abs() <= 0.05 * p
    return dn, up, p, float(w.loc[k & (w["price"] < p), "long"].sum()), float(w.loc[k & (w["price"] > p), "short"].sum())


def onchain() -> pd.DataFrame:
    fr = []
    for ex in ("hl", "lighter"):
        x = pd.read_csv(DATA / "liqsnap" / f"{ex}_2026-11.csv.gz")
        x["ex"] = ex
        fr.append(x)
    x = pd.concat(fr)
    x["t"] = pd.to_datetime(x["ts"])
    return x


def onchain_at(oc: pd.DataFrame, T: pd.Timestamp) -> dict | None:
    """Ultima fotografia on-chain ≤ T per ogni exchange (non più vecchia di 3 ore), fasce sommate; cluster e $ entro ±5%."""
    b: dict[int, list] = {}
    mid = None
    for ex, g in oc.groupby("ex"):
        g = g[(g["t"] <= T) & (g["t"] >= T - pd.Timedelta(hours=3))]
        if g.empty:
            continue
        last = g[g["t"] == g["t"].max()]
        mid = float(last["mid"].iloc[0]) if mid is None else mid
        for _, r in last.iterrows():
            v = b.setdefault(int(r["k"]), [0.0, 0.0, 0, 0])
            v[0] += r["long_usd"]; v[1] += r["short_usd"]; v[2] += r["n_long"]; v[3] += r["n_short"]
    if not b:
        return None
    cl = liqsnap.clusters(b, mid, "long") + liqsnap.clusters(b, mid, "short")
    lo = sum(v[0] for k, v in b.items() if -20 <= k < 0)
    sh = sum(v[1] for k, v in b.items() if 0 <= k < 20)
    return {"mid": mid, "clusters": cl, "long5": lo, "short5": sh}


def sr_at(T: pd.Timestamp) -> dict:
    """Livelli S/R del tool con le sole candele giornaliere chiuse prima del giorno di T."""
    f = pd.read_csv(DATA / "spot.csv", parse_dates=["date"]).set_index("date")
    f = f[f.index < T.normalize()]
    tr = pd.concat([f["high"] - f["low"], (f["high"] - f["close"].shift()).abs(), (f["low"] - f["close"].shift()).abs()], axis=1).max(axis=1)
    f = f.assign(atr=tr.rolling(14).mean(), spot_vol=f["volume"])
    return levels.compute(f)


if __name__ == "__main__":
    print("1m", m1().shape, "1h", h1().shape, "oi fino a", oi_hourly().dropna().index.max())
