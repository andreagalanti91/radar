"""Mappe orarie delle liquidazioni stimate (radar/liqmap.build, 504 ore PRIMA di T) dal 2021 per lo studio squeeze (PREREG.md).
Uso: python research/liq_squeeze/sq_data.py [--refresh]  → cache /tmp/radar-work/liqsqueeze/hmaps.pkl
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "liq_fasce")); sys.path.insert(0, str(HERE.parents[1]))
from lf_data import hourly  # noqa: E402
from radar import liqmap  # noqa: E402

WORK = Path("/tmp/radar-work/liqsqueeze"); WORK.mkdir(parents=True, exist_ok=True)
RADII = (0.04, 0.06, 0.08)
_H = None


def feats(w: pd.DataFrame, p: float) -> dict:
    out = {"p": p}
    for r in RADII:
        k = (w["price"] - p).abs() <= r * p
        out[f"S{int(r*100)}"] = float(w.loc[k & (w["price"] > p), "short"].sum())
        out[f"L{int(r*100)}"] = float(w.loc[k & (w["price"] < p), "long"].sum())
    out["dn"] = [(c["price"], c["usd"], c["rel"]) for c in liqmap.clusters(w, p, "long", sig=0.0) if c["rel"] >= 0.2]
    out["up"] = [(c["price"], c["usd"], c["rel"]) for c in liqmap.clusters(w, p, "short", sig=0.0) if c["rel"] >= 0.2]
    return out


def one(T):
    h = _H
    a, b = h.index.searchsorted(T - pd.Timedelta(hours=liqmap.LOOKBACK_H)), h.index.searchsorted(T)
    win = h.iloc[a:b][["high", "low", "close", "oi_usd"]].dropna()
    if len(win) < 400:
        return None
    p = float(win["close"].iloc[-1])
    w = liqmap.window(liqmap.build(win), p, 0.12)
    return {"T": T, **feats(w, p)}


def _init(h):
    global _H
    _H = h


def hourly_maps(refresh: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    hp, mp = WORK / "h.pkl", WORK / "hmaps.pkl"
    h = hourly(refresh=refresh) if (refresh or not hp.exists()) else pd.read_pickle(hp)
    h.to_pickle(hp)
    old = pd.read_pickle(mp) if mp.exists() else None
    Ts = pd.date_range("2021-01-22", h.index[-1] + pd.Timedelta(hours=1), freq="h")
    if old is not None:
        old = old[old.index < h.index[-1] - pd.Timedelta(hours=72)]     # ricalcola le ultime ore (OI esteso può cambiare)
        Ts = Ts[Ts > old.index[-1]]
    with Pool(4, initializer=_init, initargs=(h,)) as pool:
        rows = [r for r in pool.map(one, list(Ts), chunksize=200) if r]
    M = pd.DataFrame(rows).set_index("T") if rows else None
    M = pd.concat([old, M]) if old is not None else M
    M.to_pickle(mp)
    return h, M


if __name__ == "__main__":
    h, M = hourly_maps(refresh="--refresh" in sys.argv)
    print(h.index[0], h.index[-1], len(h), h.attrs.get("oi_info"))
    print(len(M), M.index[0], M.index[-1])
    print(M[["p", "S6", "L6"]].tail())
