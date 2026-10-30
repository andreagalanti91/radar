"""Segnali swing BTC: portafoglio di 6 setup di order flow e posizionamento, con piano DCA.

Setup long (spot e futures):
  flow     score = z(CVD perp 14g) - z(long/short retail) > 1.5
           acquisti aggressivi sui perp + retail scettico => continuazione
  capit    drawdown 30g < -12% e open interest -8% in 7g
           flush della leva: le liquidazioni hanno ripulito il mercato
  fundneg  funding medio 7g negativo
           shorts che pagano per restare aperti => carburante per uno squeeze
  brk      nuovo massimo a 20g in trend rialzista con CVD perp > +1σ
           breakout confermato dal flusso
Setup short (solo futures, solo in regime ribassista: prezzo < SMA200 e SMA50 < SMA200):
  sflow    score < -1.5
  sfund    funding 7g > +1σ: rimbalzo a leva dentro un trend ribassista
Una sola posizione alla volta; se più setup scattano insieme il long ha priorità.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

SETUPS = {
    "flow": ("long", "Flusso perp forte + retail scettico"),
    "capit": ("long", "Capitolazione: flush di leva dopo un calo"),
    "fundneg": ("long", "Funding negativo: short affollati"),
    "brk": ("long", "Breakout a 20 giorni confermato dal flusso"),
    "sflow": ("short", "Flusso perp debole + retail long, trend ribassista"),
    "sfund": ("short", "Rimbalzo a leva (funding alto) in trend ribassista"),
}


@dataclass
class Params:
    flow_threshold: float = 1.5
    capit_dd: float = -0.12
    capit_oi: float = -0.08
    brk_flow: float = 1.0
    sfund_z: float = 1.0
    # DCA in entrata (multipli di ATR dal prezzo del primo ingresso)
    entry_weights: tuple = (0.4, 0.3, 0.3)
    entry_step_atr: float = 0.75
    entry_window: int = 7       # giorni di validità dei limit DCA
    stop_atr: float = 3.0       # stop dal primo ingresso
    # DCA in uscita (multipli di ATR dal prezzo medio)
    tp_atr: tuple = (1.0, 3.0)
    tp_weights: tuple = (0.3, 0.3)  # il restante 40% in trailing
    trail_atr: float = 3.0
    max_hold: int = 45
    cooldown: int = 1
    leverage: float = 2.0       # leva consigliata sui futures (sizing nel piano)
    allow_short: bool = True

    def to_dict(self):
        return asdict(self)


def _edge(m: pd.Series) -> pd.Series:
    m = m.fillna(False).astype(bool)
    return m & ~m.shift(1, fill_value=False)


def conditions(f: pd.DataFrame, p: Params) -> dict[str, pd.Series]:
    """Condizioni (livello, non fronte) di ciascun setup."""
    c = f["close"]
    up = (c > f["sma200"]) & (f["sma50"] > f["sma200"])
    down = (c < f["sma200"]) & (f["sma50"] < f["sma200"])
    score = f["pf14z"] - f["ls_z"]
    return {
        "flow": score > p.flow_threshold,
        "capit": (f["dd30"] < p.capit_dd) & (f["oi_chg7"] < p.capit_oi),
        "fundneg": f["funding7"] < 0,
        "brk": (f["brk20"] > 0) & (f["pf14z"] > p.brk_flow) & up,
        "sflow": down & (score < -p.flow_threshold),
        "sfund": down & (f["funding_z"] > p.sfund_z),
    }


def explain(row: pd.Series, setup: str, p: Params) -> str:
    """Perché il setup è scattato: i valori che hanno superato le soglie quel giorno."""
    score = row["pf14z"] - row["ls_z"]
    trend = "rialzista" if row["close"] > row["sma200"] and row["sma50"] > row["sma200"] else \
        "ribassista" if row["close"] < row["sma200"] and row["sma50"] < row["sma200"] else "neutrale"
    txt = {
        "flow": f"score di flusso {score:+.2f} sopra +{p.flow_threshold}: CVD perp {row['pf14z']:+.2f}σ, long/short retail {row['ls_z']:+.2f}σ",
        "capit": f"calo dal massimo a 30 giorni {row['dd30']*100:.1f}% e open interest {row['oi_chg7']*100:+.1f}% in 7 giorni: leva ripulita",
        "fundneg": f"funding medio 7 giorni {row['funding7']*100:+.4f}% al giorno: gli short pagano per restare aperti",
        "brk": f"chiusura sopra il massimo a 20 giorni ({row['brk20']*100:+.1f}%) con CVD perp {row['pf14z']:+.2f}σ in trend rialzista",
        "sflow": f"score di flusso {score:+.2f} sotto −{p.flow_threshold} in trend ribassista",
        "sfund": f"funding {row['funding_z']:+.2f}σ sopra la media in trend ribassista: rimbalzo a leva",
    }.get(setup, "")
    atr = f"{row['atr']:,.0f}".replace(",", ".")
    return f"{txt} · trend {trend}, ATR {atr} $"


def compute_signals(f: pd.DataFrame, p: Params) -> pd.DataFrame:
    s = f.copy()
    s["score"] = s["pf14z"] - s["ls_z"]
    s["up"] = (s["close"] > s["sma200"]) & (s["sma50"] > s["sma200"])
    s["down"] = (s["close"] < s["sma200"]) & (s["sma50"] < s["sma200"])
    s["long_sig"] = False
    s["short_sig"] = False
    s["setup"] = ""
    for name, cond in conditions(f, p).items():
        side = SETUPS[name][0]
        if side == "short" and not p.allow_short:
            continue
        e = _edge(cond)
        col = "long_sig" if side == "long" else "short_sig"
        if side == "short":
            e &= ~s["long_sig"]
        s.loc[e & (s["setup"] == ""), "setup"] = name
        s[col] |= e
    return s


# compatibilità con il nome precedente
compute_score = compute_signals


def trade_plan(row: pd.Series, side: str, p: Params) -> dict:
    """Piano operativo leggibile (per alert e dashboard) dalla chiusura del giorno del segnale."""
    sgn = 1 if side == "long" else -1
    px, atr = float(row["close"]), float(row["atr"])
    entries = [(px - sgn * i * p.entry_step_atr * atr, w) for i, w in enumerate(p.entry_weights)]
    avg = sum(e * w for e, w in entries) / sum(w for _, w in entries)
    stop = px - sgn * p.stop_atr * atr
    tps = [avg + sgn * k * atr for k in p.tp_atr]
    risk = abs(avg - stop) / avg * 100
    setup = row.get("setup", "")
    return {
        "side": side,
        "setup": setup,
        "setup_label": SETUPS.get(setup, ("", ""))[1],
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
        "risk_pct_full": round(risk, 2),
        "leverage": p.leverage,
        "risk_pct_capital_at_leverage": round(risk * p.leverage, 1),
        "liquidation_distance_pct": round(100 / p.leverage * 0.9, 1),
    }
