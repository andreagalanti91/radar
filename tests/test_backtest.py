"""Test del motore di backtest su dati sintetici: proteggono i risultati dalle modifiche automatiche."""
import unittest

import numpy as np
import pandas as pd

from radar.backtest import run, summary
from radar.strategy import Params


def frame(prices, atr=1.0, signal_day=0, side="long"):
    n = len(prices)
    idx = pd.date_range("2024-01-01", periods=n)
    c = pd.Series(prices, index=idx, dtype=float)
    f = pd.DataFrame({"open": c, "high": c + 0.2, "low": c - 0.2, "close": c, "atr": atr, "funding": 0.0}, index=idx)
    f["long_sig"] = False
    f["short_sig"] = False
    f["setup"] = "test"
    f.loc[idx[signal_day], "long_sig" if side == "long" else "short_sig"] = True
    return f


class TestBacktest(unittest.TestCase):
    def setUp(self):
        self.p = Params(cooldown=0)

    def test_ingresso_al_giorno_dopo(self):
        # il segnale alla chiusura di t entra all'apertura di t+1 (niente look-ahead)
        f = frame([100, 105] + [105] * 50)
        t = run(f, self.p, "futures", signals=f)
        self.assertEqual(t.iloc[0]["events"][1]["price"], 105.0)

    def test_stop_pieno(self):
        # discesa continua: tutte le tranche si riempiono e scatta lo stop, perdita
        f = frame([100] + [100 - i for i in range(1, 30)])
        t = run(f, self.p, "futures", signals=f)
        self.assertEqual(t.iloc[0]["exit"], "stop")
        self.assertEqual(t.iloc[0]["tranches"], 3)
        self.assertLess(t.iloc[0]["pnl_pct_capital"], 0)

    def test_take_profit_e_pareggio(self):
        # sale di 1,2 ATR (TP1) e poi torna giù: chiude a pareggio con un piccolo guadagno
        f = frame([100, 100, 101.3, 100.2, 99.0] + [99] * 40)
        t = run(f, self.p, "futures", signals=f)
        self.assertEqual(t.iloc[0]["tp_hit"], 1)
        self.assertEqual(t.iloc[0]["exit"], "stop_be")
        self.assertGreater(t.iloc[0]["pnl_pct_capital"], 0)

    def test_short_simmetrico(self):
        f = frame([100] + [100 + i for i in range(1, 30)], side="short")
        t = run(f, self.p, "futures", signals=f)
        self.assertEqual(t.iloc[0]["side"], "short")
        self.assertLess(t.iloc[0]["pnl_pct_capital"], 0)

    def test_spot_niente_short(self):
        f = frame([100] + [100 + i for i in range(1, 30)], side="short")
        self.assertTrue(run(f, self.p, "spot", signals=f).empty)

    def test_commissioni(self):
        # prezzo fermo per l'intera durata: esce a tempo con una perdita pari alle sole commissioni
        f = frame([100] * 60)
        f["high"] = f["close"] + 0.01
        f["low"] = f["close"] - 0.01
        t = run(f, self.p, "futures", signals=f)
        self.assertEqual(t.iloc[0]["exit"], "time")
        self.assertAlmostEqual(t.iloc[0]["pnl_pct_capital"], -0.04, places=2)

    def test_summary(self):
        t = pd.DataFrame({"exit": ["tp", "stop"], "pnl_pct_capital": [2.0, -1.0], "pnl_pct_invested": [2.0, -1.0], "days": [5, 3]})
        s = summary(t)
        self.assertEqual(s["trades"], 2)
        self.assertEqual(s["win_rate"], 50.0)


class TestRiferimento(unittest.TestCase):
    """Numeri di riferimento della strategia sui dati reali: cambiano solo con una promozione voluta."""

    def test_metriche_di_riferimento(self):
        from radar.data import DATA_DIR, load_all
        from radar.features import build_features
        if not (DATA_DIR / "spot.csv").exists():
            self.skipTest("dati non presenti")
        t = run(build_features(load_all()), Params(), "futures", "2022-03-01", "2026-10-01")
        s = summary(t)
        self.assertEqual(s["trades"], 48)
        self.assertAlmostEqual(s["total_return_%"], 57.0, delta=0.3)


if __name__ == "__main__":
    unittest.main()
