"""Motore del book (radar/orderbook.py): feature, controlli dei dati, etichette, modello. Niente rete."""
import unittest

import numpy as np
import pandas as pd

from radar import orderbook as ob


def book(mid=100.0, n=400, tick=0.01, bq=1.0, aq=1.0):
    bids = [(mid - tick / 2 - i * tick, bq) for i in range(n)]
    asks = [(mid + tick / 2 + i * tick, aq) for i in range(n)]
    return bids, asks


class TestOrderbook(unittest.TestCase):
    def test_feature(self):
        b, a = book(100, 300, 0.01, bq=2, aq=1)       # copre ±3%
        f = ob.book_features(b, a)
        self.assertAlmostEqual(f["mid"], 100)
        self.assertGreater(f["micro_bps"], 0)           # più quantità in bid: microprezzo sopra il mid
        self.assertGreater(f["bid_1"], f["ask_1"])
        self.assertIsNotNone(f["bid_2"])
        b2, a2 = book(100, 50, 0.01)                    # copre solo ±0,5%
        g = ob.book_features(b2, a2)
        self.assertIsNone(g["bid_1"]); self.assertIsNotNone(g["bid_0.25"])

    def test_controlli(self):
        b, a = book()
        self.assertEqual(ob.check("x", b, a, 1000, 1010, 100.0), [])
        self.assertIn("book incrociato", ob.check("x", [(101, 1)] + b, a, None, 0))
        self.assertTrue(any("vecchi" in e for e in ob.check("x", b, a, 0, 1000)))
        self.assertTrue(any("consenso" in e for e in ob.check("x", b, a, None, 0, ref_mid=101.0)))
        self.assertTrue(ob.check("x", b[:5], a[:5], None, 0))
        wide = [(p - 1, q) for p, q in b]
        self.assertIn("spread anomalo", ob.check("x", wide, a, None, 0))

    def test_aggregato_e_muri(self):
        b, a = book(100, 300, 0.01, bq=3, aq=1)
        b = b + [(98.5, 5000.0)]                        # muro in acquisto a −1,5%
        agg, per = ob.aggregate({"a": (b, a), "b": book(100, 300, 0.01)})
        self.assertGreater(agg["imb_1"], 0)
        self.assertEqual(agg["n_src"], 2)
        self.assertAlmostEqual(agg["wall_bid_dist"], -1.5, delta=0.06)

    def test_etichette(self):
        df = pd.DataFrame({"ts": ["2026-01-01 00:00", "2026-01-01 01:05", "2026-01-01 02:00", "2026-01-01 04:10"], "mid": [100, 101, 99, 103]})
        y1 = ob.label(df, "1h")
        self.assertAlmostEqual(y1[0], 0.01); self.assertAlmostEqual(y1[1], 99 / 101 - 1); self.assertTrue(np.isnan(y1[2]))
        y4 = ob.label(df, "4h")
        self.assertAlmostEqual(y4[0], 0.03)

    def test_modello_e_registro(self):
        rng = np.random.default_rng(1)
        n = 300
        x = rng.normal(size=n)
        y = (x + rng.normal(scale=0.5, size=n) > 0).astype(float)
        w = ob.fit_logistic(x[:, None], y)
        self.assertGreater(w[1], 0.5)
        self.assertEqual(ob.predict(None, {})["1h"], 0.5)
        t = pd.date_range("2026-01-01", periods=n, freq="h")
        mid = 100 * np.exp(np.cumsum(rng.normal(scale=0.002, size=n)))
        df = pd.DataFrame({"ts": t.astype(str), "mid": mid, **{f: rng.normal(size=n) for f in ob.FEATS}})
        model = ob.learn(df)
        self.assertGreaterEqual(model["1h"]["n"], n - 2)
        p = ob.predict(model, df.iloc[-1].to_dict())
        self.assertTrue(0 < p["1h"] < 1)
        df["p_1h"], df["p_4h"] = 0.6, 0.4
        ev = ob.evaluate(df)
        self.assertEqual(ev["1h"]["n"], n - 1)
        self.assertAlmostEqual(ev["1h"]["model_acc"], ev["1h"]["always_up_acc"])


if __name__ == "__main__":
    unittest.main()
