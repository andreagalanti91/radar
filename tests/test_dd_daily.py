"""Test dell'equity giornaliera mark-to-market (drawdown reale) usata da scorecard e gate."""
import unittest

import pandas as pd

from radar.backtest import run, summary
from radar.research import daily_equity, dd_daily, drawdown_stats, path_from_events
from radar.strategy import Params
from tests.test_backtest import frame


class TestDailyEquity(unittest.TestCase):
    def setUp(self):
        self.p = Params(cooldown=0)

    def test_mark_to_market_singola_tranche(self):
        # una sola tranche al 100%: ingresso a 100 all'apertura del giorno 1, chiusura a 95 il giorno 2
        p = Params(cooldown=0, entry_weights=(1.0,), stop_atr=50, tp_atr=(100.0, 200.0))
        f = frame([100, 100, 95] + [95] * 60, atr=1.0)
        t = run(f, p, "futures", signals=f)
        path = dict(t.iloc[0]["mtm"])
        self.assertAlmostEqual(path["2024-01-03"], -0.05 - 0.0005, places=6)
        eq = daily_equity(t, leverage=2)
        self.assertAlmostEqual(eq["2024-01-03"], 1 + 2 * (-0.0505), places=6)

    def test_equity_finale_uguale_trade_per_trade(self):
        # l'ultimo giorno di ogni trade vale il risultato finale: l'equity finale coincide con quella di summary
        f = frame([100, 100, 101.3, 100.2, 99.0] + [99] * 10 + [99 + 0.4 * i for i in range(40)] + [115] * 60)
        f.loc[f.index[20], "long_sig"] = True
        t = run(f, self.p, "futures", signals=f)
        self.assertGreaterEqual(len(t), 2)
        for L in (1, 2, 3):
            eq = daily_equity(t, leverage=L)
            self.assertAlmostEqual((eq.iloc[-1] - 1) * 100, summary(t, L)["total_return_%"], delta=0.06)
        for _, r in t.iterrows():
            self.assertAlmostEqual(r["mtm"][-1][1] * 100, r["pnl_pct_capital"], places=6)

    def test_drawdown_giornaliero_almeno_quello_per_trade(self):
        # un trade che va sotto e poi chiude a pareggio dopo il TP1: il DD per trade è 0, quello giornaliero no
        f = frame([100, 100, 98, 97.6, 99, 101.5, 100.5, 99.5, 98.5] + [98.5] * 50)
        f["open"] = f["close"].shift(1).fillna(100)  # apertura = chiusura precedente: niente gap
        f["high"] = f[["open", "close"]].max(axis=1) + 0.2
        f["low"] = f[["open", "close"]].min(axis=1) - 0.2
        t = run(f, self.p, "futures", signals=f)
        self.assertGreater(t.iloc[0]["pnl_pct_capital"], 0)
        dd = dd_daily(t, levels=(1, 2))
        self.assertLess(dd["1x"]["max_dd_%"], -1.0)
        self.assertLess(dd["2x"]["max_dd_%"], dd["1x"]["max_dd_%"])  # la leva amplifica

    def test_uscite_parziali_e_tranche(self):
        # il percorso ricostruito dagli eventi coincide con quello esatto a meno di commissioni e arrotondamenti
        f = frame([100, 100, 99.4, 98.9, 100.5, 102.5, 104, 103, 101] + [101] * 50)
        t = run(f, self.p, "futures", signals=f)
        r = t.iloc[0]
        self.assertGreater(r["tranches"], 1)
        self.assertGreaterEqual(r["tp_hit"], 1)
        exact, approx = dict(r["mtm"]), dict(path_from_events(r.to_dict(), f["close"]))
        self.assertEqual(set(exact), set(approx))
        for k in exact:
            self.assertAlmostEqual(exact[k], approx[k], delta=0.003)

    def test_statistiche_drawdown(self):
        idx = pd.date_range("2024-01-01", periods=6)
        eq = pd.Series([1.0, 1.2, 0.9, 1.0, 1.25, 1.1], index=idx)
        s = drawdown_stats(eq)
        self.assertEqual(s["max_dd_%"], -25.0)
        self.assertEqual(s["peak"], "2024-01-02")
        self.assertEqual(s["trough"], "2024-01-03")
        self.assertEqual(s["recovery"], "2024-01-05")
        self.assertEqual(s["days_underwater"], 3)


class TestRiferimentoDD(unittest.TestCase):
    def test_dd_giornaliero_di_riferimento(self):
        from radar.data import DATA_DIR, load_all
        from radar.features import build_features
        if not (DATA_DIR / "spot.csv").exists():
            self.skipTest("dati non presenti")
        f = build_features(load_all())
        t = run(f, Params(), "futures", "2022-03-01", "2026-10-01")
        self.assertEqual(len(t), 47)
        dd = dd_daily(t, f["close"])
        self.assertAlmostEqual(dd["1x"]["max_dd_%"], -22.4, delta=0.3)
        self.assertLessEqual(dd["2x"]["max_dd_%"], summary(t, 2)["max_dd_%"])


if __name__ == "__main__":
    unittest.main()
