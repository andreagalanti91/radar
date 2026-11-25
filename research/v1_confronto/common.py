"""Caricamento comune: modulo v1 dell'utente (import/v1.py, NON modificato), dati dell'utente e dati di Radar."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
IMP = HERE / "import"
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("v1_utente", IMP / "v1.py")
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)


def user_daily() -> pd.DataFrame:
    return pd.read_csv(IMP / "btc_giornaliero.csv", index_col=0, parse_dates=True)


def radar_daily() -> pd.DataFrame:
    """data/spot.csv (giorni chiusi) + data/funding.csv; btc_giornaliero.csv solo prima dell'inizio di spot.csv."""
    s = pd.read_csv(ROOT / "data" / "spot.csv", index_col=0, parse_dates=True)
    s = s[s["close"].notna()]
    s = s[s.index < pd.Timestamp.utcnow().tz_localize(None).normalize()]   # solo giorni chiusi
    fu = pd.read_csv(ROOT / "data" / "funding.csv", index_col=0, parse_dates=True)["funding"]
    fu = fu[~fu.index.duplicated(keep="last")]
    d = s[["open", "high", "low", "close", "volume"]].copy()
    d["funding"] = fu.reindex(d.index)
    h = user_daily()
    h = h[h.index < d.index[0]]
    out = pd.concat([h[["open", "high", "low", "close", "volume", "funding"]], d]).sort_index()
    return out
