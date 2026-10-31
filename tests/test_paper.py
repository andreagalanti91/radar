"""Non regressione del modulo su carta: il motore pulito riproduce H2 del giro 12 (dal 2022-03, rischio 3%)."""
import unittest
from unittest import mock

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


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in FILES + ["taker_1h"]), "dati taker mancanti")
class TestPaperV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar import paper
        from radar.data import load_all
        from radar.features import build_features
        cut = pd.Timestamp("2026-10-30")
        f = build_features(load_all())
        h4 = paper.candles_4h()
        f, h4 = f[f.index < cut], h4[h4.index < cut]
        cls.r = paper.simulate(f, h4, "2022-03-01", risk_fn=paper.v2_risk(f, h4))

    def test_numeri_notte_0147(self):
        # ricerca notte 01:47 (DT_mix): 105 trade, WR 79,0%, +226,0%, DD giornaliero −13,5%, 10.000 $ -> 32.580 $
        s = self.r["stats"]
        self.assertEqual(s["n"], 105)
        self.assertAlmostEqual(s["wr"], 79.0, delta=0.5)
        self.assertAlmostEqual(s["ret"], 226.0, delta=3.0)
        self.assertAlmostEqual(s["dd"], -13.5, delta=0.5)

    def test_rischio(self):
        # rischio tra 0,5×0,6×5,24% e 2×5,24%, mai sopra 5x; 0,6 solo ai long sotto la SMA 40 settimane
        for t in self.r["trades"]:
            self.assertGreaterEqual(t["risk"], 0.0524 * 0.5 * 0.6 - 1e-4)
            self.assertLessEqual(t["risk"], 0.0524 * 2 + 1e-4)
            self.assertLessEqual(t["N"], 5.0)
            if t["risk"] < 0.0524 * 0.5 - 1e-4:
                self.assertTrue(t["side"] == "long" and t["below_sma40w"])


class TestPaperLive(unittest.TestCase):
    """Senza rete: rischio v2 congelato e candele intraday (solo barre 4h complete)."""

    def test_rischio_congelato(self):
        from radar import paper
        dt = {"v": 0.02}

        def fn(sg, d, tc):   # rischio che dipende dal DT corrente (come quando arriva il perp)
            return 0.05 + dt["v"], dict(dt=dt["v"], below_sma40w=False, perp=dt["v"] > 0.05)
        saved = {}
        g = paper.frozen_risk(fn, saved)
        d, tc = pd.Timestamp("2026-11-02"), pd.Timestamp("2026-11-03 08:00")
        r1 = g(1, d, tc)
        dt["v"] = 0.12   # cambia il DT a posteriori
        self.assertEqual(g(1, d, tc), r1)
        self.assertEqual(paper.frozen_risk(fn, dict(saved))(1, d, tc), r1)   # anche dopo ricarica da json
        self.assertEqual(saved["2026-11-02 long"]["dt"], 0.02)
        self.assertAlmostEqual(g(-1, d, tc)[0], 0.17)   # trade diverso: calcolato col DT attuale

    @unittest.skipUnless((DATA_DIR / "spot_1h.csv").exists(), "dati mancanti")
    def test_candele_intraday(self):
        from radar import paper
        base = paper.candles_4h()
        t = pd.read_csv(DATA_DIR / "spot_1h.csv", index_col=0, parse_dates=True).index[-1]
        idx = pd.date_range(t + pd.Timedelta(hours=1), periods=6, freq="h")   # 6 ore chiuse: 1 barra completa + 2 ore
        x = pd.DataFrame({"open": 1.0, "high": range(2, 8), "low": 0.5, "close": 1.5}, index=idx, dtype=float)
        with mock.patch.object(paper, "hours_after", return_value=x):
            live = paper.candles_4h(live=True)
        self.assertTrue(live.iloc[:len(base)].equals(base))
        self.assertEqual(len(live), len(base) + 1)
        self.assertEqual(live.index[-1], idx[0])
        self.assertEqual(live["high"].iloc[-1], 5.0)
        with mock.patch.object(paper, "hours_after", return_value=x.iloc[:0]):   # rete assente: solo dati salvati
            self.assertTrue(paper.candles_4h(live=True).equals(base))

    @unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in FILES + ["taker_1h"]), "dati taker mancanti")
    def test_simulazione_rischio_congelato(self):
        # stessi trade di v2 dal 2026-01 con rischio congelato: un DT diverso dopo l'ingresso non cambia rischio e N
        from radar import paper
        from radar.data import load_all
        from radar.features import build_features
        cut = pd.Timestamp("2026-10-30")
        f = build_features(load_all())
        h4 = paper.candles_4h()
        f, h4 = f[f.index < cut], h4[h4.index < cut]
        saved = {}
        a = paper.simulate(f, h4, "2026-01-01", risk_fn=paper.frozen_risk(paper.v2_risk(f, h4), saved))
        other = lambda sg, d, tc: (0.10, dict(dt=0.15, below_sma40w=False, perp=True))  # noqa: E731
        b = paper.simulate(f, h4, "2026-01-01", risk_fn=paper.frozen_risk(other, saved))
        self.assertGreater(len(a["trades"]), 0)
        self.assertEqual([(t["risk"], t["dt"], t["N"]) for t in a["trades"]], [(t["risk"], t["dt"], t["N"]) for t in b["trades"]])


if __name__ == "__main__":
    unittest.main()
