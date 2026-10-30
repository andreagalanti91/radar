"""Valutazione giornaliera: stato del mercato, nuovi segnali, trade aperto, eventi da notificare."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from .backtest import run, summary
from .data import DATA_DIR
from .zones import latest_zone
from .strategy import SETUPS, Params, compute_signals, conditions, explain, trade_plan

STATE_FILE = DATA_DIR / "state.json"
BACKTEST_START = "2022-03-01"   # le metrics (long/short ratio) partono da dic 2021 + warm-up
TEST_START = "2024-01-01"       # parametri scelti solo su dati precedenti
LIVE_START = "2026-10-30"       # da qui i segnali sono reali (registro fuori campione)


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
    s = compute_signals(f, p)
    s = s.loc[: s["score"].last_valid_index()]  # ultimo giorno con dati derivati completi
    f = f.loc[: s.index[-1]]
    last = s.iloc[-1]
    downtrend = bool((last["close"] < last["sma200"]) and (last["sma50"] < last["sma200"]))
    regime = "rialzista" if bool(last["up"]) else "ribassista" if downtrend else "neutrale"

    signal = None
    if bool(last["long_sig"]):
        signal = trade_plan(last, "long", p)
    elif bool(last["short_sig"]):
        signal = trade_plan(last, "short", p)
    if signal:
        signal["why"] = explain(last, signal["setup"], p)

    fut = run(f, p, "futures", BACKTEST_START)
    spot = run(f, p, "spot", BACKTEST_START)
    # il percorso giornaliero mark-to-market serve solo alla ricerca: non va nello stato/dashboard
    fut = fut.drop(columns=["mtm"], errors="ignore")
    spot = spot.drop(columns=["mtm"], errors="ignore")
    open_fut = fut[fut["exit"] == "open"].to_dict("records")
    open_spot = spot[spot["exit"] == "open"].to_dict("records")

    for t in (fut, spot):  # motivo del segnale per ogni trade
        if len(t):
            t["why"] = [explain(s.loc[pd.Timestamp(d)], st, p) for d, st in zip(t["signal_date"], t["setup"])]
    stats = {}
    for name, t in (("futures", fut), ("spot", spot)):
        stats[name] = {
            "train": summary(t[pd.to_datetime(t["signal_date"]) < TEST_START]),
            "test": summary(t[pd.to_datetime(t["signal_date"]) >= TEST_START]),
            "full": summary(t),
        }
    stats["leverage"] = {str(lv): summary(fut, lv) for lv in (1, 2, 3)}
    closed = fut[fut["exit"] != "open"]
    stats["by_setup"] = {
        k: {"trades": int(len(g)), "win_rate": round(float((g["pnl_pct_capital"] > 0).mean() * 100), 1),
            "expectancy_%": round(float(g["pnl_pct_capital"].mean()), 2), "label": SETUPS[k][1], "side": SETUPS[k][0]}
        for k, g in closed.groupby("setup")
    }
    # anatomia del win rate: di che tipo sono le vincite
    pi = closed["pnl_pct_invested"]
    stats["anatomy"] = {
        "loss": int((pi <= 0).sum()), "flat": int(((pi > 0) & (pi < 1)).sum()),
        "small": int(((pi >= 1) & (pi < 3)).sum()), "good": int((pi >= 3).sum()),
        "by_exit": {k: {"n": int(len(g)), "avg": round(float(g.mean()), 2)} for k, g in pi.groupby(closed["exit"])},
    }
    years = (s.index[-1] - pd.Timestamp(BACKTEST_START)).days / 365.25
    stats["trades_per_year"] = round(len(closed) / years, 1)

    # stato attuale di ciascun setup (per la checklist)
    cond = conditions(f.loc[: s.index[-1]], p)
    checklist = []
    detail = {
        "flow": f"score {last['score']:+.2f} (soglia +{p.flow_threshold})",
        "capit": f"drawdown 30g {last['dd30']*100:.1f}% (≤ {p.capit_dd*100:.0f}%) · OI 7g {last['oi_chg7']*100:+.1f}% (≤ {p.capit_oi*100:.0f}%)",
        "fundneg": f"funding 7g {last['funding7']*100:+.4f}% per giorno (< 0)",
        "brk": f"distanza dal max 20g {last['brk20']*100:+.1f}% · CVD perp {last['pf14z']:+.2f}σ (> +{p.brk_flow}) · trend {'ok' if last['up'] else 'no'}",
        "sflow": f"score {last['score']:+.2f} (soglia −{p.flow_threshold}) · regime {'ribassista' if last['down'] else 'non ribassista'}",
        "sfund": f"funding z {last['funding_z']:+.2f} (soglia +{p.sfund_z}) · regime {'ribassista' if last['down'] else 'non ribassista'}",
    }
    for k, (side, label) in SETUPS.items():
        checklist.append({"setup": k, "side": side, "label": label, "active": bool(cond[k].iloc[-1]), "detail": detail[k]})

    # curve di equity (chiusura trade) vs buy & hold
    def curve(t, lev):
        t = t[t["exit"] != "open"]
        eq = (1 + t["pnl_pct_capital"] * lev / 100).cumprod()
        return [{"date": str(d), "eq": round(float(v), 4)} for d, v in zip(t["exit_date"], eq)]
    hist0 = s[s.index >= pd.Timestamp(BACKTEST_START)]["close"]
    equity = {"1x": curve(fut, 1), "2x": curve(fut, 2), "3x": curve(fut, 3),
              "btc": [{"date": str(d.date()), "eq": round(float(v / hist0.iloc[0]), 4)} for d, v in hist0.items()]}

    hist = s[s.index >= pd.Timestamp(BACKTEST_START)]
    return _clean({
        "date": str(last.name.date()),
        "price": float(last["close"]),
        "score": float(last["score"]),
        "threshold": p.flow_threshold,
        "regime": regime,
        "components": {
            "perp_flow_z": float(last["pf14z"]),
            "retail_ls_z": float(last["ls_z"]),
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
        "zone": latest_zone(f),
        "checklist": checklist,
        "equity": equity,
        "open_trade": {"futures": open_fut[0] if open_fut else None, "spot": open_spot[0] if open_spot else None},
        "stats": stats,
        "params": p.to_dict(),
        "trades": {"futures": fut.to_dict("records"), "spot": spot.to_dict("records"),
                   "live": fut[fut["signal_date"].astype(str) >= LIVE_START].to_dict("records") if len(fut) else []},
        "live_start": LIVE_START,
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
