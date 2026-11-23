"""Previsionale · dataset (PREREG §1–2). Solo lettura dei dati congelati; non modifica radar/.

dataset() -> frame giornaliero 2014 → 15/11/2026 con le 12 variabili (già ritardate come da PREREG) e la chiusura.
features(base) è riusabile dal tool: `base` ha colonne open/high/low/close, pf14z, sf14z, funding_z, oi_chg7, fng.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P2 = ROOT / "research" / "p2_nuovi" / "data"
CUT = "2026-11-15"
PRICE = ["r7", "r30", "r90", "d50", "d200", "rsi", "vol"]
FLOW = ["pf", "sf", "fz", "oi", "fng"]
ALL = PRICE + FLOW
FLOW_N = 3   # come radar.weekly.FLOW_N


def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def features(b: pd.DataFrame) -> pd.DataFrame:
    """Le 12 variabili alla chiusura di t: prezzi di t; flussi, funding e OI di t−1; fear&greed di t."""
    c = b["close"]
    x = pd.DataFrame(index=b.index)
    x["close"] = c
    lc = np.log(c)
    for n in (7, 30, 90):
        x[f"r{n}"] = lc - lc.shift(n)
    x["d50"] = lc - np.log(c.rolling(50).mean())
    x["d200"] = lc - np.log(c.rolling(200).mean())
    x["rsi"] = _rsi(c) / 100 - 0.5
    tr = pd.concat([b["high"] - b["low"], (b["high"] - c.shift()).abs(), (b["low"] - c.shift()).abs()], axis=1).max(axis=1)
    x["vol"] = tr.ewm(alpha=1 / 14, adjust=False).mean() / c
    x["pf"] = b["pf14z"].rolling(FLOW_N, min_periods=2).mean().shift(1)     # = radar.weekly.live_flow
    x["sf"] = b["sf14z"].shift(1)
    x["fz"] = b["funding_z"].shift(1)
    x["oi"] = b["oi_chg7"].shift(1)
    x["fng"] = b["fng"] / 100 - 0.5
    return x


def frozen() -> tuple[pd.DataFrame, pd.DataFrame]:
    rd = lambda n: pd.read_csv(P2 / n, index_col=0, parse_dates=True)  # noqa: E731
    return rd("f_repo.csv.gz"), rd("f_long.csv.gz")


def base_frame(f: pd.DataFrame, fl: pd.DataFrame, fng: pd.Series) -> pd.DataFrame:
    b = fl[["open", "high", "low", "close", "pf14z"]].copy()
    for col in ("sf14z", "funding_z", "oi_chg7"):
        b[col] = f[col].reindex(b.index)
    b["fng"] = fng.reindex(b.index).ffill(limit=2)
    return b


def dataset() -> pd.DataFrame:
    f, fl = frozen()
    fng = pd.read_csv(ROOT / "data" / "fng.csv", index_col=0, parse_dates=True)["fng"]
    fng = fng[fng.index <= CUT]
    x = features(base_frame(f, fl, fng))
    return x[x.index <= CUT]


def labels(x: pd.DataFrame, h: int) -> pd.Series:
    r = x["close"].shift(-h) / x["close"] - 1
    return (r > 0).astype(float).where(r.notna())


if __name__ == "__main__":
    x = dataset()
    print(x.index[0].date(), x.index[-1].date(), len(x))
    print(pd.DataFrame({"dal": x.apply(lambda s: s.first_valid_index()), "n": x.notna().sum()}).to_string())
