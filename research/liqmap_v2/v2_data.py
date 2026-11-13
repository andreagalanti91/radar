"""Dati dello studio liqmap v2 (PREREG.md): candele 1h + OI + flusso taker + top trader Binance USDT-M, liquidazioni reali cm.

Archivi data.binance.vision già scaricati negli studi del 03/11 e del 13/11 (/tmp/radar-work/liq/data, /tmp/radar-work/liqfasce/dl).
Candele e OI: cache dello studio liq_fasce (h.pkl). Uso: python research/liqmap_v2/v2_data.py
"""
from __future__ import annotations

import glob
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

SRC = [Path("/tmp/radar-work/liq/data"), Path("/tmp/radar-work/liqfasce/dl")]
H_PKL = Path("/tmp/radar-work/liqfasce/work/h.pkl")
WORK = Path("/tmp/radar-work/liqmap_v2")
WORK.mkdir(parents=True, exist_ok=True)


def _rd(p):
    with zipfile.ZipFile(p) as z:
        return pd.read_csv(z.open(z.namelist()[0]))


def metrics() -> pd.DataFrame:
    """Per ora: b = quota taker in acquisto (media sui 5 minuti di r/(1+r)), top = quota long top trader (ultimo valore)."""
    out = WORK / "metrics_h.pkl"
    if out.exists():
        return pd.read_pickle(out)
    cols = ["create_time", "sum_toptrader_long_short_ratio", "sum_taker_long_short_vol_ratio", "count_long_short_ratio"]
    fs = [p for s in SRC for p in sorted(glob.glob(str(s / "metrics/*.zip")))]
    m = pd.concat([_rd(p)[cols] for p in fs])
    m["t"] = pd.to_datetime(m["create_time"])
    m = m.drop_duplicates("t").sort_values("t")
    r = pd.to_numeric(m["sum_taker_long_short_vol_ratio"], errors="coerce")
    R = pd.to_numeric(m["sum_toptrader_long_short_ratio"], errors="coerce")
    # create_time hh:00 … hh:55: valori dentro l'ora, noti alla chiusura dell'ora
    g = m["t"].dt.floor("h")
    b = (r.where(r > 0) / (1 + r.where(r > 0))).groupby(g).mean()
    top = (R.where(R > 0) / (1 + R.where(R > 0))).groupby(g).last()
    x = pd.DataFrame({"b": b, "top": top})
    x.to_pickle(out)
    return x


def hourly() -> pd.DataFrame:
    h = pd.read_pickle(H_PKL)[["high", "low", "close", "oi_usd"]]
    return h.join(metrics(), how="left")


def liq_cm() -> pd.DataFrame:
    """Liquidazioni reali Binance BTCUSD_PERP: time, side (long/short liquidato), price, usd."""
    out = WORK / "liqcm.pkl"
    if out.exists():
        return pd.read_pickle(out)
    fr = []
    for p in sorted(glob.glob(str(SRC[0] / "liqcm/*.zip"))):
        d = _rd(p).drop_duplicates()
        d = d[d["order_status"].isin(["FILLED", "PARTIALLY_FILLED"])] if "order_status" in d else d
        fr.append(pd.DataFrame({"time": pd.to_datetime(d["time"], unit="ms"), "side": np.where(d["side"] == "SELL", "long", "short"),
                                "price": d["average_price"].astype(float), "usd": d["last_fill_quantity"].astype(float) * 100.0}))
    x = pd.concat(fr).sort_values("time").reset_index(drop=True)
    x.to_pickle(out)
    return x


if __name__ == "__main__":
    h = hourly()
    print(h.index[0], h.index[-1], len(h), h[["b", "top"]].describe().T)
    lq = liq_cm()
    print(len(lq), lq["time"].min(), lq["time"].max(), lq.groupby("side")["usd"].sum() / 1e6)
