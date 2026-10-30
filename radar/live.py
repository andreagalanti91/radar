"""Valutazione giornaliera: stato del mercato, nuovi segnali, trade aperto, eventi da notificare."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from .backtest import run, summary
from .data import DATA_DIR
from .strategy import Params, compute_score, trade_plan

STATE_FILE = DATA_DIR / "state.json"
BACKTEST_START = "2022-03-01"   # le metrics (long/short ratio) partono da dic 2021 + warm-up
TEST_START = "2024-01-01"       # parametri scelti solo su dati precedenti


def _clean(x):
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    if hasattr(x, "item"):
        return _clean(x.item())
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if hasattr(x, "isoformat"):
        return x.isoformat()
    return x


def evaluate(f: pd.DataFrame, p: Params | None = None) -> dict:
    p = p or Params()
    s = compute_score(f, p)
    s = s.loc[: s["score"].last_valid_index()]  # ultimo giorno con dati derivati completi
    f = f.loc[: s.index[-1]]
    last = s.iloc[-1]
    downtrend = bool((last["close"] < last["sma200"]) and (last["sma50"] < last["sma200"]))
    regime = "rialzista" if bool(last["trend_up"]) else "ribassista" if downtrend else "neutrale"

    signal = None
    if bool(last["long_sig"]):
        signal = trade_plan(last, "long", p)
    elif bool(last["short_sig"]):
        signal = trade_plan(last, "short", p)

    fut = run(f, p, "futures", BACKTEST_START)
    spot = run(f, p, "spot", BACKTEST_START)
    open_fut = fut[fut["exit"] == "open"].to_dict("records")
    open_spot = spot[spot["exit"] == "open"].to_dict("records")

    stats = {}
    for name, t in (("futures", fut), ("spot", spot)):
        stats[name] = {
            "train": summary(t[pd.to_datetime(t["signal_date"]) < TEST_START]),
            "test": summary(t[pd.to_datetime(t["signal_date"]) >= TEST_START]),
            "full": summary(t),
        }

    hist = s[s.index >= pd.Timestamp(BACKTEST_START)]
    return _clean({
        "date": str(last.name.date()),
        "price": float(last["close"]),
        "score": float(last["score"]),
        "threshold": p.threshold,
        "regime": regime,
        "components": {
            "perp_flow_z": float(last["pf_z"]),
            "retail_ls_z": float(last["ls_zz"]),
            "perp_flow14": float(last["perp_flow14"]),
            "spot_flow14": float(last["spot_flow14"]),
            "global_ls": float(last["global_ls"]),
            "funding7_annual_pct": float(last["funding7"] * 365 * 100),
            "oi_chg7_pct": float(last["oi_chg7"] * 100),
            "basis_pct": float(last["basis"] * 100),
            "fng": float(last["fng"]),
            "atr": float(last["atr"]),
            "atr_pct": float(last["atr_pct"] * 100),
            "sma200": float(last["sma200"]),
        },
        "signal": signal,
        "open_trade": {"futures": open_fut[0] if open_fut else None, "spot": open_spot[0] if open_spot else None},
        "stats": stats,
        "params": p.to_dict(),
        "trades": {"futures": fut.to_dict("records"), "spot": spot.to_dict("records")},
        "series": {
            "date": [str(d.date()) for d in hist.index],
            "open": hist["open"].round(1).tolist(), "high": hist["high"].round(1).tolist(),
            "low": hist["low"].round(1).tolist(), "close": hist["close"].round(1).tolist(),
            "score": hist["score"].round(3).tolist(),
            "sma200": hist["sma200"].round(1).tolist(),
        },
    })


def diff_events(report: dict) -> list[dict]:
    """Confronta con lo stato salvato e produce gli eventi da notificare."""
    prev = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    events = []
    sig = report["signal"]
    if sig and prev.get("last_signal_date") != report["date"]:
        events.append({"type": "signal", "plan": sig})
    for market in ("futures", "spot"):
        cur = report["open_trade"][market]
        old = prev.get("open", {}).get(market)
        if cur and old and cur["signal_date"] == old["signal_date"]:
            if cur["tranches"] > old["tranches"]:
                events.append({"type": "dca_fill", "market": market, "trade": cur})
            if cur["tp_hit"] > old["tp_hit"]:
                events.append({"type": "tp_hit", "market": market, "trade": cur})
        if old and (not cur or cur["signal_date"] != old["signal_date"]):
            closed = [t for t in report["trades"][market]
                      if str(t["signal_date"]) == str(old["signal_date"]) and t["exit"] != "open"]
            if closed:
                events.append({"type": "closed", "market": market, "trade": closed[0]})
    return events


def save_state(report: dict) -> None:
    prev = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    state = {
        "date": report["date"],
        "last_signal_date": report["date"] if report["signal"] else prev.get("last_signal_date"),
        "open": report["open_trade"],
    }
    STATE_FILE.write_text(json.dumps(_clean(state), indent=2, default=str))
