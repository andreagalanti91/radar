"""Non regressione del modulo su carta: il motore pulito riproduce H2 del giro 12 (dal 2022-03, rischio 3%)."""
import unittest

import pandas as pd

from radar.data import DATA_DIR

FILES = ["spot_1h", "spot", "perp", "funding", "metrics", "fng"]


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in FILES), "dati mancanti")
class TestPaperH2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar import paper
        from radar.data import load_all
        from radar.features import build_features
        cut = pd.Timestamp("2026-10-30")   # dati del giro 12: i numeri non cambiano con gli aggiornamenti
        f = build_features(load_all())
        h4 = paper.candles_4h()
        cls.r = paper.simulate(f[f.index < cut], h4[h4.index < cut], "2022-03-01")

    def test_numeri_giro12(self):
        # rapporto giro 12 (eng.py): 105 trade, WR 79,0%, +85,4%, DD giornaliero −11,4%
        s = self.r["stats"]
        self.assertEqual(s["n"], 105)
        self.assertAlmostEqual(s["wr"], 79.0, delta=0.5)
        self.assertAlmostEqual(s["ret"], 85.4, delta=0.5)
        self.assertAlmostEqual(s["dd"], -11.4, delta=0.3)
        self.assertAlmostEqual(self.r["equity"].iloc[-1], 18541.59, delta=1.0)

    def test_regole(self):
        # stop a 1 ATR dall'ingresso e TP a +1R; esposizione mai oltre 5x
        for t in self.r["trades"]:
            sg = 1 if t["side"] == "long" else -1
            self.assertGreater(sg * (t["entry"] - t["stop"]), 0)
            self.assertGreater(sg * (t["tp"] - t["avg"]), 0)
            self.assertLessEqual(t["N"], 5.0)
            self.assertIn(t["exit"], ("tp", "stop", "time"))


if __name__ == "__main__":
    unittest.main()
