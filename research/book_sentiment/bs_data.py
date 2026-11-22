"""Dati dello studio book_sentiment (PREREG.md). Nessun rendimento qui: solo caricamento.
Cache in $BS_WORK (default /tmp/radar-work/book_sentiment). Non importa nulla da radar/.

Insiemi:
  A "registro"  : data/orderbook.csv (I a ±1%) + liquidazioni reali registrate (data/liq_events, prima data/liquidations.csv)
  B "archivio"  : liquidazioni reali Binance COIN-M BTCUSD_PERP (data.binance.vision, 2023-06-25 → 2024-10-14), solo L
Prezzi: A = candele 1 minuto BTCUSDT spot (data-api.binance.vision); B = data/spot_1h.csv.
"""
from __future__ import annotations

import io
import os
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
WORK = Path(os.environ.get("BS_WORK", "/tmp/radar-work/book_sentiment")); WORK.mkdir(parents=True, exist_ok=True)
S = requests.Session()
THR = 0.2                       # soglia di S (specifica della regia)
CM_BASE = "data/futures/cm/daily/liquidationSnapshot/BTCUSD_PERP/"
CM_CONTRACT_USD = 100.0         # BTCUSD_PERP: 1 contratto = 100 $


# ---------------------------------------------------------------- insieme A
def book() -> pd.DataFrame:
    b = pd.read_csv(DATA / "orderbook.csv")
    b["t"] = pd.to_datetime(b["ts"])
    return b.sort_values("t").reset_index(drop=True)


def liq_live() -> pd.DataFrame:
    """Eventi reali registrati: t, side (lato LIQUIDATO), usd, exchange. data/liq_events (più fonti) dal suo primo evento;
    prima solo OKX da data/liquidations.csv (ultimi 100 eventi per giro: incompleto nelle cascate)."""
    ev = pd.read_csv(DATA / "liq_events" / "2026-11.csv")
    ev["t"] = pd.to_datetime(ev["ts"], unit="ms")
    ev = ev.drop_duplicates(["exchange", "id"])[["t", "side", "usd", "exchange"]]
    old = pd.read_csv(DATA / "liquidations.csv")
    old["t"] = pd.to_datetime(old["time"])
    old = old.rename(columns={"liquidated": "side"}).assign(exchange="okx_csv")[["t", "side", "usd", "exchange"]]
    old = old[old["t"] < ev["t"].min()]
    return pd.concat([old, ev]).sort_values("t").reset_index(drop=True)


def liq_sums(ev: pd.DataFrame, times: pd.Series, minutes: int) -> pd.DataFrame:
    """$ di long e short liquidati nella finestra (T − minuti, T] per ogni T."""
    t = ev["t"].to_numpy("datetime64[ns]")
    cl = np.concatenate([[0.0], np.cumsum(np.where(ev["side"] == "long", ev["usd"], 0.0))])
    cs = np.concatenate([[0.0], np.cumsum(np.where(ev["side"] == "short", ev["usd"], 0.0))])
    T = pd.to_datetime(times).to_numpy("datetime64[ns]")
    hi = np.searchsorted(t, T, side="right")
    lo = np.searchsorted(t, T - np.timedelta64(minutes, "m"), side="right")
    return pd.DataFrame({"liq_long": cl[hi] - cl[lo], "liq_short": cs[hi] - cs[lo], "liq_n": hi - lo}, index=times.index)


def ratio(short_usd, long_usd) -> np.ndarray:
    s, l = np.asarray(short_usd, float), np.asarray(long_usd, float)
    tot = s + l
    return np.where(tot > 0, (s - l) / np.where(tot > 0, tot, 1.0), 0.0)


def panel_A(minutes: int = 30) -> pd.DataFrame:
    """Una riga per foto del book: I (imb_1), L (finestra `minutes` prima della foto), S = 0,5·I + 0,5·L."""
    b = book()
    ls = liq_sums(liq_live(), b["t"], minutes)
    p = pd.concat([b[["t", "mid", "imb_1", "src_1", "n_src", "wall_bid_px", "wall_bid_usd", "wall_bid_dist",
                      "wall_ask_px", "wall_ask_usd", "wall_ask_dist", "bid_1", "ask_1"]], ls], axis=1)
    p["I"] = p["imb_1"]
    p["L"] = ratio(p["liq_short"], p["liq_long"])
    p["S"] = 0.5 * p["I"] + 0.5 * p["L"]
    return p


def state(s: pd.Series | np.ndarray, thr: float = THR) -> np.ndarray:
    s = np.asarray(s, float)
    return np.where(s > thr, 1, np.where(s < -thr, -1, 0))


# ---------------------------------------------------------------- prezzi
def klines(interval: str, start: pd.Timestamp, end: pd.Timestamp | None = None) -> pd.DataFrame:
    out, t = [], int(start.timestamp() * 1000)
    end_ms = int((end or pd.Timestamp.now("UTC").tz_localize(None)).timestamp() * 1000)
    while t < end_ms:
        r = S.get("https://data-api.binance.vision/api/v3/klines",
                  params={"symbol": "BTCUSDT", "interval": interval, "startTime": t, "limit": 1000}, timeout=30).json()
        if not r:
            break
        out += r
        t = int(r[-1][0]) + 1
        time.sleep(0.05)
    now = time.time() * 1000
    return pd.DataFrame([[pd.to_datetime(x[0], unit="ms"), *map(float, x[1:5])] for x in out if int(x[6]) < now],
                        columns=["t", "open", "high", "low", "close"]).drop_duplicates("t").set_index("t")


def m1() -> pd.DataFrame:
    p = WORK / "m1.pkl"
    if p.exists():
        return pd.read_pickle(p)
    k = klines("1m", pd.Timestamp("2026-11-06"))
    k.to_pickle(p)
    return k


def h1() -> pd.DataFrame:
    return pd.read_csv(DATA / "spot_1h.csv", parse_dates=["t"]).set_index("t")[["open", "high", "low", "close"]]


# ---------------------------------------------------------------- insieme B
def cm_events() -> pd.DataFrame:
    p = WORK / "cm_events.pkl"
    if p.exists():
        return pd.read_pickle(p)
    x = S.get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision", params={"delimiter": "/", "prefix": CM_BASE}, timeout=60).text
    keys = re.findall(r"<Key>([^<]+\d{4}-\d\d-\d\d\.zip)</Key>", x)

    def get(k):
        for _ in range(3):
            r = requests.get("https://data.binance.vision/" + k, timeout=60)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    return pd.read_csv(z.open(z.namelist()[0]))
            time.sleep(1)
        raise RuntimeError(k)

    with ThreadPoolExecutor(8) as ex:
        fr = list(ex.map(get, keys))
    e = pd.concat(fr).drop_duplicates()
    e = e[e["order_status"].isin(["FILLED", "PARTIALLY_FILLED"])]
    e = e.sort_values(["time", "accumulated_fill_quantity"]).drop_duplicates(["time", "side", "price", "original_quantity"], keep="last")
    out = pd.DataFrame({"t": pd.to_datetime(e["time"], unit="ms"),
                        "side": np.where(e["side"] == "SELL", "long", "short"),       # SELL = long liquidato
                        "usd": e["accumulated_fill_quantity"].astype(float) * CM_CONTRACT_USD,
                        "exchange": "binance_cm"}).sort_values("t").reset_index(drop=True)
    out.attrs["days"] = len(keys)
    out.to_pickle(p)
    return out


def panel_B() -> pd.DataFrame:
    """Una riga per ora H (decisione all'inizio dell'ora H): liquidazioni dell'ora precedente [H−1, H), L, S = 0,5·L (I = 0)."""
    e = cm_events()
    days = pd.DatetimeIndex(sorted(e["t"].dt.normalize().unique()))
    hrs = pd.date_range(days.min() + pd.Timedelta(hours=1), days.max() + pd.Timedelta(hours=24), freq="h")
    g = e.assign(h=e["t"].dt.floor("h") + pd.Timedelta(hours=1)).pivot_table(index="h", columns="side", values="usd", aggfunc="sum")
    g = g.reindex(hrs).fillna(0.0)
    p = pd.DataFrame({"t": hrs, "liq_long": g["long"].to_numpy(), "liq_short": g["short"].to_numpy()})
    p["L"] = ratio(p["liq_short"], p["liq_long"])
    p["S"] = 0.5 * p["L"]
    return p


if __name__ == "__main__":
    print("A", panel_A().shape, "| m1", m1().shape, "| B", panel_B().shape)
