"""Sanity tests for engine.py on hand-made bars (no network, no data files).
Run: python3 -m unittest research/intraday2/test_engine.py   (or: cd research/intraday2 && python3 -m unittest -q)"""
import os
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Costs, Exits, Sizing, backtest, metrics, resample  # noqa: E402

ZERO = Costs(fee=0, slip=0, slip_stop=0, funding=False, liquidation=False)
CAP = 10_000.0


def make_bars(rows, funding=None, start="2024-01-01"):
    idx = pd.date_range(start, periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    df["funding"] = 0.0 if funding is None else funding
    df["atr"] = 1.0
    return df


def sig(bars, entries, **cols):
    s = pd.DataFrame(index=bars.index, data={"side": 0})
    for i, v in entries.items():
        s.iloc[i, 0] = v
    for c, d in cols.items():
        s[c] = np.nan
        for i, v in d.items():
            s.iloc[i, s.columns.get_loc(c)] = v
    return s


def run(rows, entries, exits, sizing=None, costs=ZERO, funding=None, **cols):
    b = make_bars(rows, funding)
    return backtest({"X": b}, {"X": sig(b, entries, **cols)}, exits,
                    sizing or Sizing(mode="fixed", leverage=1, capital=CAP), costs)


FLAT = (100, 100.5, 99.5, 100)


class EngineTests(unittest.TestCase):
    def test_tp1_tp2(self):
        rows = [FLAT, (100, 101, 99, 100), (100, 106, 99, 104), (104, 111, 103, 110), FLAT]
        r = run(rows, {0: 1}, Exits(stop_pct=0.02, tp=[(0.05, .5), (0.10, .5)]))
        t = r.trades.iloc[0]
        self.assertEqual(len(r.trades), 1)
        self.assertAlmostEqual(t.pnl, 50 * 5 + 50 * 10)
        self.assertAlmostEqual(t.R, 750 / 200)
        self.assertEqual(t.reason, "tp1+tp2")
        self.assertEqual(t.entry_time, r.trades.signal_time.iloc[0] + pd.Timedelta("1h"))
        self.assertAlmostEqual(r.equity.iloc[-1], CAP + 750)

    def test_stop_first_same_bar(self):
        rows = [FLAT, (100, 101, 99, 100), (100, 106, 97, 104), FLAT]
        r = run(rows, {0: 1}, Exits(stop_pct=0.02, tp=[(0.05, 1.0)]))
        self.assertAlmostEqual(r.trades.pnl.iloc[0], -200)
        self.assertEqual(r.trades.reason.iloc[0], "stop")

    def test_tp_in_R(self):
        rows = [FLAT, (100, 101, 99, 100), (100, 104.5, 99, 104), FLAT]
        r = run(rows, {0: 1}, Exits(stop_pct=0.02, tp=[(2, 1.0)], tp_unit="R"))  # TP at 104
        self.assertAlmostEqual(r.trades.pnl.iloc[0], 400)
        self.assertAlmostEqual(r.trades.R.iloc[0], 2.0)

    def test_breakeven_next_bar_and_same_bar(self):
        ex = Exits(stop_pct=0.02, tp=[(0.05, .5), (0.10, .5)], be_after_tp1=True)
        rows = [FLAT, (100, 101, 99.5, 100), (100, 106, 101, 104), (104, 104, 99.5, 100), FLAT]
        r = run(rows, {0: 1}, ex)
        self.assertAlmostEqual(r.trades.pnl.iloc[0], 250)
        self.assertEqual(r.trades.reason.iloc[0], "tp1+be")
        rows = [FLAT, (100, 101, 99.5, 100), (100, 106, 99.9, 104), FLAT]
        r = run(rows, {0: 1}, ex)  # TP1 and BE inside the same bar -> conservative BE exit
        self.assertAlmostEqual(r.trades.pnl.iloc[0], 250)

    def test_trailing_pct(self):
        rows = [FLAT, (100, 101, 99.5, 100), (100, 110, 104, 108), (106, 107, 103, 104), FLAT]
        r = run(rows, {0: 1}, Exits(stop_pct=0.02, trail_pct=0.05))
        self.assertAlmostEqual(r.trades.pnl.iloc[0], 100 * 4.5)
        self.assertEqual(r.trades.reason.iloc[0], "trail")

    def test_trailing_atr_after_tp1(self):
        rows = [FLAT, (100, 101, 99.5, 100), (100, 106, 103, 105.5), (105, 105, 103.5, 104), FLAT]
        ex = Exits(stop_pct=0.02, tp=[(0.05, .5)], trail_atr=2.0, trail_after_tp1=True)  # atr = 1
        r = run(rows, {0: 1}, ex)  # trail = 106 - 2 = 104 after bar 2
        self.assertAlmostEqual(r.trades.pnl.iloc[0], 50 * 5 + 50 * 4)

    def test_gap_through_stop(self):
        rows = [FLAT, (100, 101, 99, 100), (95, 96, 94, 95), FLAT]
        r = run(rows, {0: 1}, Exits(stop_pct=0.02))
        self.assertAlmostEqual(r.trades.pnl.iloc[0], -500)

    def test_short_mirror(self):
        rows = [FLAT, (100, 101, 99, 100), (100, 101, 94, 95), FLAT]
        r = run(rows, {0: -1}, Exits(stop_pct=0.02, tp=[(0.05, 1.0)]))
        self.assertAlmostEqual(r.trades.pnl.iloc[0], 500)
        rows = [FLAT, (100, 101, 99, 100), (100, 103, 99, 102), FLAT]
        r = run(rows, {0: -1}, Exits(stop_pct=0.02, tp=[(0.05, 1.0)]))
        self.assertAlmostEqual(r.trades.pnl.iloc[0], -200)

    def test_time_exit_and_funding(self):
        rows = [FLAT] * 8
        f = np.zeros(8); f[[2, 3, 5]] = 0.0001; f[1] = 0.01  # bar 1 = entry bar open: not charged
        c = Costs(fee=0, slip=0, slip_stop=0, funding=True, liquidation=False)
        r = run(rows, {0: 1}, Exits(time_bars=4), costs=c, funding=f)  # entry bar1, exit open of bar5
        t = r.trades.iloc[0]
        self.assertEqual(t.reason, "time")
        self.assertAlmostEqual(t.funding, 100 * 100 * 0.0001 * 2)  # bars 2 and 3 (bar 5 exits at its open)
        self.assertAlmostEqual(t.pnl, -2.0)
        r = run(rows, {0: -1}, Exits(time_bars=4), costs=c, funding=f)
        self.assertAlmostEqual(r.trades.pnl.iloc[0], +2.0)  # shorts receive positive funding

    def test_costs(self):
        rows = [FLAT, (100, 101, 99, 100), (100, 106, 99, 104), FLAT]
        c = Costs(fee=0.0005, slip=0.0002, slip_stop=0.0005, funding=False, liquidation=False)
        r = run(rows, {0: 1}, Exits(stop_pct=0.02, tp=[(0.05, 1.0)]), costs=c)
        ef = 100 * 1.0002; q = CAP / ef; px = 105 * (1 - 0.0002)
        self.assertAlmostEqual(r.trades.pnl.iloc[0], q * (px - ef) - CAP * 0.0005 - q * px * 0.0005, places=6)
        rows = [FLAT, (100, 101, 97, 100), FLAT]
        r = run(rows, {0: 1}, Exits(stop_pct=0.02), costs=c)  # stop at 2% of the RAW open
        px = 98 * (1 - 0.0005)
        self.assertAlmostEqual(r.trades.pnl.iloc[0], q * (px - ef) - CAP * 0.0005 - q * px * 0.0005, places=6)

    def test_liquidation(self):
        rows = [FLAT, (100, 101, 99, 100), (100, 100, 80, 85), FLAT]
        c = Costs(fee=0, slip=0, slip_stop=0, funding=False, liquidation=True, mmr=0.005)
        r = run(rows, {0: 1}, Exits(), sizing=Sizing(mode="fixed", leverage=5, capital=CAP), costs=c)
        t = r.trades.iloc[0]
        self.assertEqual(t.reason, "liq")
        self.assertAlmostEqual(t.liq_px, 80.5)
        self.assertAlmostEqual(t.pnl, -CAP)  # whole isolated margin (= notional/5)
        r = run(rows, {0: 1}, Exits(stop_pct=0.1), sizing=Sizing(mode="fixed", leverage=5, capital=CAP), costs=c)
        self.assertEqual(r.trades.reason.iloc[0], "stop")  # stop at 90 fills before liq at 80.5
        self.assertAlmostEqual(r.trades.pnl.iloc[0], -5000)

    def test_risk_sizing_and_cap(self):
        rows = [FLAT, (100, 101, 99, 100), (100, 101, 97, 100), FLAT]
        r = run(rows, {0: 1}, Exits(stop_pct=0.02), sizing=Sizing(mode="risk", risk_pct=0.01, leverage=5, capital=CAP))
        self.assertAlmostEqual(r.trades.notional.iloc[0], 5000)
        self.assertAlmostEqual(r.trades.pnl.iloc[0], -100)
        self.assertAlmostEqual(r.trades.R.iloc[0], -1)
        r = run(rows, {0: 1}, Exits(stop_pct=0.002), sizing=Sizing(mode="risk", risk_pct=0.01, leverage=3, capital=CAP))
        self.assertAlmostEqual(r.trades.notional.iloc[0], 30000)  # capped at 3x

    def test_reversal(self):
        rows = [FLAT] * 3 + [(100, 101, 99, 103), (103, 104, 102, 103), (104, 105, 103, 104), FLAT]
        r = run(rows, {0: 1, 3: -1}, Exits())
        self.assertEqual(len(r.trades), 2)
        self.assertEqual(r.trades.reason.iloc[0], "signal")
        self.assertAlmostEqual(r.trades.pnl.iloc[0], 100 * 3)  # 100 -> open of bar 4 = 103
        self.assertEqual(r.trades.side.iloc[1], -1)
        self.assertEqual(r.trades.entry_time.iloc[1], r.trades.exit_time.iloc[0])
        self.assertEqual(r.trades.reason.iloc[1], "end")

    def test_one_position_per_asset_and_mtm(self):
        rows = [FLAT, (100, 101, 99, 102), (102, 103, 101, 102), (102, 107, 101, 104), FLAT]
        r = run(rows, {0: 1, 1: 1, 2: 1}, Exits(stop_pct=0.05, tp=[(0.05, 1.0)]))
        self.assertEqual(len(r.trades), 1)
        self.assertAlmostEqual(r.equity.iloc[1], CAP + 200)   # MTM at bar-1 close
        self.assertAlmostEqual(r.equity.iloc[-1], CAP + 500)
        m = metrics(r)
        self.assertEqual(m["trades"], 1)

    def test_resample_4h(self):
        rows = [(1, 2, 0.5, 1.5), (1.5, 3, 1, 2), (2, 2.5, 0.2, 1), (1, 1.2, 0.9, 1.1), (1.1, 9, 1, 2)]
        b = make_bars(rows).drop(columns="atr")
        b["volume"] = 1.0
        b.loc[b.index[1], "funding"] = 0.001
        r = resample(b, "4h")
        self.assertEqual(len(r), 1)  # the incomplete second bar is dropped
        self.assertEqual(tuple(r.iloc[0][["open", "high", "low", "close", "volume"]]), (1, 3, 0.2, 1.1, 4))
        self.assertAlmostEqual(r.funding.iloc[0], 0.001)


if __name__ == "__main__":
    unittest.main()
