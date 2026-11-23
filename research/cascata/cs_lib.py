"""cascata · dati e definizioni comuni (23/11/2026). Non modifica radar/.

Grandezze giornaliere, tutte note alla chiusura del giorno t (lato s = +1 long, −1 short):
  atr1  = ATR14 di Wilder alla chiusura di t−1 (radar.features: colonna atr, ritardata di un giorno)
  rA    = s·(C_t − C_{t−1}) / atr1            rendimento a favore in ATR          rP = s·(C_t / C_{t−1} − 1)
  eA    = s·(E_t − C_{t−1}) / atr1            escursione a favore in ATR (E = massimo per i long, minimo per gli short)
  vr    = V_t / media(V_{t−30..t−1})           V = spot_vol + perp_vol (BTC/ETH Binance); 2018–20: solo spot Binance
  tail  = quota dell'escursione restituita in chiusura: s·(E_t − C_t) / (H_t − L_t)
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
from radar.features import build_features  # noqa: E402

CUT, START, SPLIT = "2026-11-15", "2021-01-01", "2024-01-01"


def _atr(f):
    c = f["close"]
    tr = pd.concat([f["high"] - f["low"], (f["high"] - c.shift()).abs(), (f["low"] - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / 14, adjust=False).mean()


def btc():
    from p2_data import load
    return load()["f"]


def btc_long():
    """Frame lungo (proxy 2018–20) + volume spot Binance (2017-08 →) come colonna spot_vol; perp_vol assente."""
    from p2_data import load
    d = load()
    fl, f = d["fl"].copy(), d["f"]
    bn = pd.read_csv(ROOT / "research/short_w2/data/binance_spot_1d_2017_2019.csv", index_col=0, parse_dates=True)
    v = pd.concat([bn["volume"], f["spot_vol"][f.index >= "2019-09-01"]])
    fl["spot_vol"] = v[~v.index.duplicated(keep="last")].reindex(fl.index)
    fl["perp_vol"] = 0.0
    return fl


def eth():
    from radar.data import load_asset
    f = build_features(load_asset("ETH"))
    return f[f["close"].notna() & (f.index <= CUT)]


def btc_live():
    """Dati del tool fino all'ultima candela giornaliera chiusa (per il caso del 21/11)."""
    from radar.data import load_all
    f = build_features(load_all())
    return f[f["close"].notna()]


def feats(f: pd.DataFrame) -> pd.DataFrame:
    """Grandezze per i due lati: colonne rA_L, rP_L, eA_L, tail_L (long) e *_S (short), vr, atr1."""
    o = pd.DataFrame(index=f.index)
    c, h, l = f["close"], f["high"], f["low"]
    o["atr1"] = _atr(f).shift(1)
    pc = c.shift(1)
    v = f["spot_vol"].fillna(0) + f["perp_vol"].fillna(0)
    v = v.where(f["spot_vol"].notna())
    o["vr"] = v / v.rolling(30).mean().shift(1)
    rng = (h - l).replace(0, np.nan)
    for s, tag, e in ((1, "L", h), (-1, "S", l)):
        o[f"rA_{tag}"] = s * (c - pc) / o["atr1"]
        o[f"rP_{tag}"] = s * (c / pc - 1)
        o[f"eA_{tag}"] = s * (e - pc) / o["atr1"]
        o[f"eP_{tag}"] = s * (e / pc - 1)
        o[f"tail_{tag}"] = s * (e - c) / rng
    return o


def trig(x: pd.DataFrame, d: dict, tag: str) -> pd.Series:
    """Cascata a favore del lato tag ("L"/"S") secondo la definizione d (chiavi facoltative: rA, rP, eA, vr, tail)."""
    m = pd.Series(True, index=x.index)
    if "rA" in d:
        m &= x[f"rA_{tag}"] >= d["rA"]
    if "rP" in d:
        m &= x[f"rP_{tag}"] >= d["rP"]
    if "eA" in d:
        m &= x[f"eA_{tag}"] >= d["eA"]
    if "vr" in d:
        m &= x["vr"] >= d["vr"]
    if "tail" in d:
        m &= x[f"tail_{tag}"] >= d["tail"]
    return m.fillna(False)


def w32_days(f: pd.DataFrame, start=START, end=None) -> pd.DataFrame:
    """Per ogni giorno: lato della posizione W3.2 tenuta alla chiusura (0 = flat) e data del segnale del trade."""
    g = f[f.index <= end] if end else f
    r = W.simulate(g, start=start)
    side = pd.Series(0, index=g.index)
    sig = pd.Series("", index=g.index, dtype=object)
    tl = list(r["trades"]) + ([r["open"]] if r["open"] else [])
    for t in tl:
        a, b = pd.Timestamp(t["entry"]), (pd.Timestamp(t["exit"]) - pd.Timedelta(days=1) if t.get("exit") else g.index[-1])
        side[a:b] = 1 if t["side"] == "long" else -1
        sig[a:b] = t["signal"]
    return pd.DataFrame({"side": side, "sig": sig}), tl
