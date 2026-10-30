"""Segnale swing BTC: order flow perp + posizionamento retail, con piano DCA.

Score = z(CVD perp 14g) - z(long/short ratio retail)
  - flusso aggressivo d'acquisto sui perp => continuazione (momentum)
  - retail sbilanciato short => carburante per il rialzo (contrarian)
Il lato short viene attivato solo in regime ribassista (sotto SMA200) perché
storicamente lo short contro-trend non ha edge.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .features import _z


@dataclass
class Params:
    threshold: float = 2.0      # soglia dello score per aprire
    z_window: int = 180         # finestra z-score
    # DCA in entrata (multipli di ATR sotto/sopra il prezzo del primo ingresso)
    entry_weights: tuple = (0.4, 0.3, 0.3)
    entry_step_atr: float = 1.0
    entry_window: int = 7       # giorni di validità dei limit DCA
    stop_atr: float = 3.5       # stop dal primo ingresso
    # DCA in uscita (multipli di ATR dal prezzo medio)
    tp_atr: tuple = (1.5, 3.0)  # TP1, TP2; il resto in trailing
    tp_weights: tuple = (0.35, 0.35)
    trail_atr: float = 3.0
    max_hold: int = 30
    cooldown: int = 3
    allow_short: bool = True
    short_needs_downtrend: bool = True

    def to_dict(self):
        return asdict(self)


def compute_score(f: pd.DataFrame, p: Params) -> pd.DataFrame:
    f = f.copy()
    f["pf_z"] = _z(f["perp_flow14"], p.z_window)
    f["ls_zz"] = _z(f["global_ls"], p.z_window)
    f["score"] = f["pf_z"] - f["ls_zz"]
    downtrend = (f["close"] < f["sma200"]) & (f["sma50"] < f["sma200"])
    f["long_sig"] = (f["score"] > p.threshold) & (f["score"].shift() <= p.threshold)
    short = (f["score"] < -p.threshold) & (f["score"].shift() >= -p.threshold)
    if p.short_needs_downtrend:
        short &= downtrend
    f["short_sig"] = short & p.allow_short
    return f


def trade_plan(row: pd.Series, side: str, p: Params) -> dict:
    """Piano operativo leggibile (per alert e dashboard) a partire dalla chiusura del giorno del segnale."""
    sgn = 1 if side == "long" else -1
    px, atr = float(row["close"]), float(row["atr"])
    entries = [(px - sgn * i * p.entry_step_atr * atr, w) for i, w in enumerate(p.entry_weights)]
    avg = sum(e * w for e, w in entries) / sum(w for _, w in entries)
    stop = px - sgn * p.stop_atr * atr
    tps = [avg + sgn * k * atr for k in p.tp_atr]
    return {
        "side": side,
        "date": str(row.name.date()),
        "price": px,
        "atr": atr,
        "score": float(row["score"]),
        "entries": [{"price": round(e, 1), "weight": w} for e, w in entries],
        "avg_entry_if_full": round(avg, 1),
        "stop": round(stop, 1),
        "take_profits": [{"price": round(t, 1), "weight": w} for t, w in zip(tps, p.tp_weights)],
        "trail_atr": p.trail_atr,
        "trail_weight": round(1 - sum(p.tp_weights), 2),
        "max_hold_days": p.max_hold,
        "risk_pct_full": round(abs(avg - stop) / avg * 100, 2),
    }
