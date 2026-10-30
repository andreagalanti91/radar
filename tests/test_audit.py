"""Non regressione per gli errori trovati dall'audit del 30/10/2026."""
import unittest

import pandas as pd

from radar.backtest import run
from radar.data import DATA_DIR, load_all
from radar.features import build_features
from radar.strategy import Params


class TestAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (DATA_DIR / "spot.csv").exists() or not (DATA_DIR / "spot_1h.csv").exists():
            raise unittest.SkipTest("dati non presenti")
        cls.f = build_features(load_all())

    def test_oi_zero_non_e_un_crollo(self):
        # righe con open interest 0 nell'archivio facevano leggere un calo del 100% (segnali capit falsi)
        self.assertGreater(self.f["oi_chg7"].dropna().min(), -0.6)

    def test_stop_pareggio_nel_giorno_del_tp1(self):
        t = run(self.f, Params(), "futures", "2025-09-01", "2025-11-01")
        tr = t[t["signal_date"] == pd.Timestamp("2025-10-03").date()].iloc[0]
        self.assertEqual(tr["exit"], "stop_be")
        self.assertEqual(str(tr["exit_date"]), "2025-10-05")


if __name__ == "__main__":
    unittest.main()
