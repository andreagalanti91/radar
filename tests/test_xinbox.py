import unittest

import pandas as pd

from radar import xinbox as X


def candles(rows, start="2026-11-01 00:00"):
    idx = pd.date_range(start, periods=len(rows), freq="h")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)


class ParseTest(unittest.TestCase):
    def test_levels(self):
        lv = X.parse_levels("Long limit 73.2k, stop 72,100 TP1 77600 target $87,350")
        self.assertEqual(lv, {"side": "long", "entry": 73200, "stop": 72100, "tp1": 77600, "target": 87350})

    def test_no_numbers(self):
        self.assertEqual(X.parse_levels("Tempo di DCA, 60%-25% = 45%"), {})


class EvalTest(unittest.TestCase):
    rec = {"side": "long", "entry": 100_000, "stop": 99_000, "tp1": 101_000, "target": 103_000,
           "post_utc": "2026-11-01 00:00"}

    def test_not_filled(self):
        c = candles([[101_500, 102_000, 100_500, 101_000]] * 200)
        self.assertEqual(X.evaluate(self.rec, c)["status"], "non eseguito")

    def test_stop_first_in_same_candle(self):
        c = candles([[100_500, 101_000, 99_900, 100_000], [100_000, 103_500, 98_000, 100_000]])
        o = X.evaluate(self.rec, c)
        self.assertEqual(o["status"], "stop")
        self.assertEqual(o["r"], -1.0)

    def test_tp1_then_target(self):
        c = candles([[100_500, 100_600, 99_900, 100_200], [100_200, 101_200, 100_100, 101_000],
                     [101_000, 103_100, 100_900, 103_000]])
        o = X.evaluate(self.rec, c)
        self.assertEqual(o["status"], "target")
        self.assertEqual(o["r"], 2.0)   # metà a +1R, metà a +3R


if __name__ == "__main__":
    unittest.main()
