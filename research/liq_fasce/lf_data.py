"""Dati comuni dello studio (PREREG.md): candele 1h + OI Binance, mappe giornaliere e orarie con radar/liqmap.

Archivio data.binance.vision in /tmp/radar-work/liq/data (studio 03/11) + giorni nuovi in /tmp/radar-work/liqfasce/dl.
Uso: python research/liq_fasce/lf_data.py  (crea le cache in /tmp/radar-work/liqfasce/work)
"""
from __future__ import annotations

import glob
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import liqmap  # noqa: E402

SRC = [Path("/tmp/radar-work/liq/data"), Path("/tmp/radar-work/liqfasce/dl")]
WORK = Path("/tmp/radar-work/liqfasce/work")
WORK.mkdir(parents=True, exist_ok=True)


def _rd(p, header=True):
    with zipfile.ZipFile(p) as z:
        return pd.read_csv(z.open(z.namelist()[0]), header=0 if header else None)


def hourly(refresh: bool = False) -> pd.DataFrame:
    out = WORK / "h.pkl"
    if out.exists() and not refresh:
        return pd.read_pickle(out)
    ms = [_rd(p)[["create_time", "sum_open_interest_value"]] for s in SRC for p in sorted(glob.glob(str(s / "metrics/*.zip")))]
    m = pd.concat(ms)
    m["t"] = pd.to_datetime(m["create_time"])
    v = pd.to_numeric(m["sum_open_interest_value"], errors="coerce")
    oi = v.where(v > 0).groupby(m["t"].dt.floor("h")).last()        # ultimo valore DENTRO l'ora (noto alla chiusura)
    ks = []
    for s in SRC:
        for p in sorted(glob.glob(str(s / "k1h/*.zip"))):
            k = _rd(p)
            if not str(k.columns[0]).startswith("open"):
                k = _rd(p, header=False)
            k = k.iloc[:, :6]
            k.columns = ["open_time", "open", "high", "low", "close", "volume"]
            ks.append(k)
    k = pd.concat(ks)
    k["t"] = pd.to_datetime(pd.to_numeric(k["open_time"]), unit="ms")
    k = k.drop_duplicates("t").set_index("t").sort_index()[["open", "high", "low", "close", "volume"]].astype(float)
    # ore successive all'archivio klines: candele spot Binance (come la dashboard)
    start = int((k.index[-1] + pd.Timedelta(hours=1)).timestamp() * 1000)
    js = requests.get("https://data-api.binance.vision/api/v3/klines",
                      {"symbol": "BTCUSDT", "interval": "1h", "startTime": start, "limit": 1000}, timeout=30).json()
    sp = pd.DataFrame(js).iloc[:, :6]
    sp.columns = ["t", "open", "high", "low", "close", "volume"]
    sp["t"] = pd.to_datetime(sp["t"], unit="ms")
    sp = sp.set_index("t").astype(float)
    now = pd.Timestamp.now(tz="UTC").tz_localize(None).floor("h")
    sp = sp[sp.index < now]                                            # solo ore chiuse
    sp["volume"] = np.nan                                              # volume spot non confrontabile con il perp
    k = pd.concat([k, sp])
    k["oi_usd"] = oi.reindex(k.index).ffill(limit=3)
    k.loc[k.index > oi.dropna().index.max(), "oi_usd"] = np.nan      # niente OI ricopiato oltre la fine dell'archivio
    # prolungamento dell'OI oltre l'archivio con OKX (stessa funzione della dashboard)
    try:
        okx = liqmap.okx_hourly(72)
        k2, info = liqmap.extend_oi(k[["high", "low", "close", "oi_usd"]], okx, max_h=48)
        k.loc[k2.index, "oi_usd"] = k2["oi_usd"]
        k.attrs["oi_info"] = info
    except Exception as e:  # noqa: BLE001
        k.attrs["oi_info"] = {"error": str(e)}
    k.to_pickle(out)
    return k


def map_at(h: pd.DataFrame, T: pd.Timestamp, rng: float = 0.12):
    """Mappa con le 504 ore che FINISCONO prima di T (decisione all'istante T). Ritorna (prezzo, finestra, cluster long, short)."""
    win = h[(h.index >= T - pd.Timedelta(hours=liqmap.LOOKBACK_H)) & (h.index < T)][["high", "low", "close", "oi_usd"]].dropna()
    if len(win) < 400:
        return None
    p = float(win["close"].iloc[-1])
    w = liqmap.window(liqmap.build(win), p, rng)
    return p, w, liqmap.clusters(w, p, "long", sig=0.0), liqmap.clusters(w, p, "short", sig=0.0)


def daily_maps(h: pd.DataFrame) -> pd.DataFrame:
    """Una mappa al giorno alle 00:00 UTC (tutti i cluster con 'rel'; sig si sceglie dopo)."""
    out = WORK / "daily_maps.pkl"
    if out.exists():
        Z = pd.read_pickle(out)
        if Z.index[-1] >= h.index[-1].normalize():
            return Z
    rows = []
    for d in pd.date_range("2021-01-22", h.index[-1] + pd.Timedelta(hours=1), freq="D"):
        r = map_at(h, d)
        if r is None:
            continue
        p, w, dn, up = r
        rows.append({"date": d, "price": p, "dn": dn, "up": up})
    Z = pd.DataFrame(rows).set_index("date")
    Z.to_pickle(out)
    return Z


if __name__ == "__main__":
    h = hourly(refresh=True)
    print(h.index[0], h.index[-1], len(h), "OI nan", int(h["oi_usd"].isna().sum()), h.attrs.get("oi_info"))
    print(h.tail(10))
    Z = daily_maps(h)
    print(len(Z), Z.index[0], Z.index[-1])
