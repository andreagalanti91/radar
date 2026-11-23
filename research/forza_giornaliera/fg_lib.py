"""forza_giornaliera · dati e definizioni comuni (23/11/2026). Non modifica radar/.

Flussi (Binance BTCUSDT/ETHUSDT spot e perp USDT-M, taker buy − taker sell):
  pfN = somma(perp_delta, N giorni) / somma(perp_vol, N giorni); sfN idem spot; pzN, szN = z su 180 giorni (radar.features._z).
Movimento: upN = chiusura / minimo degli ultimi N giorni (oggi compreso) − 1; dnN = chiusura / massimo degli ultimi N giorni − 1.
Classe di chi guida (acquisti, lato +1; vendite speculari con i segni cambiati):
  "perp"  = pz·lato > 0 e (pz − sz)·lato ≥ D0      (i perp spingono molto più dello spot)
  "spot"  = sz·lato > 0 e (sz − pz)·lato ≥ D0      (lo spot spinge più dei perp)
  "misto" = il resto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "p2_nuovi"))
from radar import weekly as W  # noqa: E402
from radar.features import _z, build_features  # noqa: E402

CUT = "2026-11-15"
START = "2021-01-01"
SPLIT = "2024-01-01"
PAUSE = 7


def btc() -> pd.DataFrame:
    from p2_data import load
    return load()["f"]


def btc_long() -> pd.DataFrame:
    from p2_data import load
    return load()["fl"]


def eth() -> pd.DataFrame:
    from radar.data import load_asset
    f = build_features(load_asset("ETH"))
    return f[f["close"].notna() & (f.index <= CUT)]


def add_flows(f: pd.DataFrame, ns=(1, 2, 3, 5)) -> pd.DataFrame:
    f = f.copy()
    for n in ns:
        pf = f["perp_delta"].rolling(n).sum() / f["perp_vol"].rolling(n).sum()
        sf = f["spot_delta"].rolling(n).sum() / f["spot_vol"].rolling(n).sum()
        f[f"pf{n}"], f[f"sf{n}"] = pf, sf
        f[f"pz{n}"], f[f"sz{n}"] = _z(pf, 180), _z(sf, 180)
        f[f"up{n}"] = f["close"] / f["low"].rolling(n).min() - 1
        f[f"dn{n}"] = f["close"] / f["high"].rolling(n).max() - 1
        # versione "del trader": dollari netti e rapporto contro il rapporto normale dei volumi
        f[f"pusd{n}"] = (f["perp_delta"] * f["close"]).rolling(n).sum()
        f[f"susd{n}"] = (f["spot_delta"] * f["close"]).rolling(n).sum()
    f["vratio"] = (f["perp_vol"] / f["spot_vol"]).rolling(180).median()
    for L in (10, 20):
        f[f"hi{L}"] = f["high"].rolling(L).max().shift(1)
        f[f"lo{L}"] = f["low"].rolling(L).min().shift(1)
    return f


def klass(f: pd.DataFrame, n: int, side: int, d0: float) -> pd.Series:
    """Chi guida gli acquisti (side=+1) o le vendite (side=−1) negli ultimi n giorni."""
    pz, sz = f[f"pz{n}"] * side, f[f"sz{n}"] * side
    out = pd.Series("misto", index=f.index)
    out[(pz > 0) & (pz - sz >= d0)] = "perp"
    out[(sz > 0) & (sz - pz >= d0)] = "spot"
    out[pz.isna() | sz.isna()] = "nd"
    return out


def klass_trader(f: pd.DataFrame, n: int, side: int) -> pd.Series:
    """Versione in dollari: perp = netto perp nel verso e (spot contrario oppure rapporto ≥ 2 × rapporto normale dei volumi)."""
    p, s, vr = f[f"pusd{n}"] * side, f[f"susd{n}"] * side, f["vratio"]
    out = pd.Series("misto", index=f.index)
    out[(p > 0) & ((s <= 0) | (p / s.where(s > 0) >= 2 * vr))] = "perp"
    out[(s > 0) & ((p <= 0) | (p / s <= vr))] = "spot"
    out[p.isna() | s.isna() | vr.isna()] = "nd"
    return out


def first_days(cond: pd.Series, pause: int = PAUSE) -> list[pd.Timestamp]:
    """Primo giorno in cui la condizione è vera, poi pausa di `pause` giorni."""
    out, last = [], None
    for day, v in cond.items():
        if v and (last is None or (day - last).days > pause):
            out.append(day)
            last = day
    return out


def w3(f: pd.DataFrame, start: str = START) -> dict:
    return W.simulate(f, start=start)


def trades(r: dict) -> list[dict]:
    return list(r["trades"]) + ([dict(r["open"], exit=None)] if r["open"] else [])
