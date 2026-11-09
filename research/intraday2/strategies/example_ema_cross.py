"""Example plug-in strategy for the intraday2 engine: EMA cross on 4h with a trend filter.

Plug-in contract (copy this file):
  TF       bar timeframe ("1h" or "4h")
  PARAMS   dict of default parameters
  signals(bars, **params) -> DataFrame[side, stop?, stop_pct?, max_bars?, exit?]  (decided at bar close)
  exits(**params) -> engine.Exits
  SIZING   engine.Sizing (optional)

This is a BASELINE to show the API, not a recommended strategy.
Run: python3 research/intraday2/strategies/example_ema_cross.py
"""
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import Exits, Sizing, Costs, load_all, backtest, split, report, metrics, placebo, neighbours  # noqa

TF = "4h"
PARAMS = {"fast": 20, "slow": 50, "trend": 200, "stop_atr": 2.0, "tp1_R": 1.5, "tp2_R": 3.0}
SIZING = Sizing(mode="risk", risk_pct=0.01, leverage=3, allocation="equal", max_exposure=3.0)


def signals(bars: pd.DataFrame, fast=20, slow=50, trend=200, **_) -> pd.DataFrame:
    c = bars["close"]
    ef, es, et = (c.ewm(span=n, adjust=False).mean() for n in (fast, slow, trend))
    up = (ef > es) & (ef.shift() <= es.shift())
    dn = (ef < es) & (ef.shift() >= es.shift())
    side = up.astype(int) * (c > et) - dn.astype(int) * (c < et)
    # exit when the cross reverses even if the trend filter blocks the opposite entry
    return pd.DataFrame({"side": side, "exit": up | dn})


def exits(stop_atr=2.0, tp1_R=1.5, tp2_R=3.0, **_) -> Exits:
    return Exits(stop_atr=stop_atr, tp=[(tp1_R, 0.5), (tp2_R, 0.5)], tp_unit="R", be_after_tp1=True,
                 reverse_exit=True, reverse_entry=True)


if __name__ == "__main__":
    t0 = time.perf_counter()
    bars = load_all(TF)
    print(f"data loaded in {time.perf_counter() - t0:.1f}s")
    res = split(signals, PARAMS, exits(**PARAMS), SIZING, Costs(), bars=bars)
    for k in ("IS", "OOS", "ALL"):
        print(report(res[k], f"EMA cross {TF} {k}"))
    print(res["ALL"].trades.tail(5).to_string())
    t1 = time.perf_counter()
    pl = placebo(res["ALL"], bars, exits(**PARAMS), SIZING, Costs(), n=50)
    print(f"placebo (50 runs, {time.perf_counter() - t1:.1f}s): real={pl['real']} percentile={pl['pctl']}")
    print(pl["runs"].describe().loc[["mean", "50%"]].round(2).to_string())
    t1 = time.perf_counter()
    nb = neighbours(lambda p: backtest(bars, {a: signals(b, **p) for a, b in bars.items()}, exits(**p), SIZING,
                                       Costs(), "2021-01-01"), PARAMS, rel=(0.8, 1.2))
    print(f"neighbours ({len(nb)} runs, {time.perf_counter() - t1:.1f}s), share PF>1: {nb.attrs['share_pf_gt_1']:.2f}")
    print(nb.to_string(index=False))
