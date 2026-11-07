"""Mappa delle liquidazioni stimate (radar/liqmap.py): solo funzioni pure, niente rete."""
import unittest

import numpy as np
import pandas as pd

from radar import liqmap


def hours(prices, oi, spread=0.001):
    t = pd.date_range("2026-01-01", periods=len(prices), freq="h")
    p = np.asarray(prices, float)
    return pd.DataFrame({"high": p * (1 + spread), "low": p * (1 - spread), "close": p, "oi_usd": np.asarray(oi, float)}, index=t)


class TestLiqMap(unittest.TestCase):
    def test_prezzo_di_liquidazione(self):
        self.assertAlmostEqual(liqmap.liq_price(100, 10, "long", 0.005), 90.5)
        self.assertAlmostEqual(liqmap.liq_price(100, 10, "short", 0.005), 109.5)
        self.assertLess(liqmap.liq_price(100, 100, "long"), 100)

    def test_long_sotto_short_sopra(self):
        h = hours([100] * 10, [1000 + 100 * i for i in range(10)])
        m = liqmap.build(h)
        w = liqmap.window(m, 100, 0.2)
        self.assertGreater(w["long"].sum(), 0)
        self.assertTrue((w.loc[w["long"] > 0, "price"] < 100).all())
        self.assertTrue((w.loc[w["short"] > 0, "price"] > 100).all())
        # tutto l'aumento di OI (900) finisce nella mappa, metà per lato (le leve 100x restano fuori dal range dell'ora? no: 0,5% > 0,1%)
        self.assertAlmostEqual(w["long"].sum() + w["short"].sum(), 900, delta=1)
        # il cluster più grande dei long è a 10x/25x: −9,5% o −3,5%
        c = max(liqmap.clusters(w, 100, "long", rng=0.15), key=lambda c: c["usd"])
        self.assertTrue(-10.5 < c["dist_pct"] < -3)

    def test_attraversato_sparisce_e_oi_in_calo_riduce(self):
        base = [100] * 6 + [94] * 2          # il prezzo scende a 94: i long liquidabili sopra 94 spariscono
        h = hours(base, [1000, 1100, 1200, 1300, 1400, 1500, 1500, 1500])
        w = liqmap.window(liqmap.build(h), 94, 0.2)
        self.assertEqual(w.loc[(w["price"] > 94 * 0.999), "long"].sum(), 0)
        h2 = hours([100] * 7, [1000, 1100, 1200, 1300, 1400, 1500, 750])   # OI dimezzato: mappa dimezzata
        a = liqmap.window(liqmap.build(h2.iloc[:6]), 100, 0.2)
        b = liqmap.window(liqmap.build(h2), 100, 0.2)
        self.assertAlmostEqual(b["long"].sum(), a["long"].sum() / 2, delta=1)

    def test_squilibrio_cluster_confluenza(self):
        w = pd.DataFrame({"price": [95, 96, 97, 103, 104, 105], "long": [10, 50, 5, 0, 0, 0], "short": [0, 0, 0, 1, 2, 1]})
        im = liqmap.imbalance(w, 100, 0.06)
        self.assertEqual(im["long_below"], 65); self.assertEqual(im["short_above"], 4); self.assertLess(im["pct"], 0)
        dn = liqmap.clusters(w, 100, "long")
        self.assertEqual(dn[0]["price"], 96); self.assertTrue(dn[0]["sig"])
        lv = {"supports": [{"price": 96, "lo": 95.5, "hi": 96.5}], "resistances": []}
        self.assertEqual(liqmap.confluence(dn[0], lv), "S1")
        s = liqmap.summarize(w, 100, lv)
        self.assertEqual(s["nearest_below"]["price"], 96)
        self.assertEqual(s["zone"]["lo"], 96)

    def test_combine_somma_le_fonti(self):
        a = pd.DataFrame({"price": [99.0, 100.0, 101.0], "long": [1, 0, 0], "short": [0, 0, 2]})
        b = pd.DataFrame({"price": [99.01, 101.02], "long": [3, 0], "short": [0, 4]})
        c = liqmap.combine([a, b])
        self.assertEqual(list(c["long"]), [4, 0, 0]); self.assertEqual(list(c["short"]), [0, 0, 6])

    def test_balene_e_registro(self):
        st = {"0xabc": {"assetPositions": [{"position": {"coin": "BTC", "szi": "-2", "entryPx": "80000", "liquidationPx": "90000", "leverage": {"value": 10}, "unrealizedPnl": "5"}},
                                           {"position": {"coin": "ETH", "szi": "5", "entryPx": "3000"}}]}}
        w = liqmap.whale_levels(st, {"0xabc": "Test"}, 75000)
        self.assertEqual(len(w), 1); self.assertEqual(w[0]["side"], "short"); self.assertAlmostEqual(w[0]["dist_pct"], 20.0)
        now = pd.Timestamp("2026-11-07 12:00")
        liq = pd.DataFrame({"time": pd.to_datetime(["2026-11-07 11:30", "2026-11-07 09:00", "2026-11-06 00:00"]),
                            "liquidated": ["long", "short", "long"], "btc": [1, 2, 3], "price": [70000, 70000, 70000], "usd": [70000, 140000, 210000]})
        f = liqmap.feed_summary(liq, now)
        self.assertEqual(f["totals"]["1h"]["long"], 70000); self.assertEqual(f["totals"]["4h"]["short"], 140000)
        self.assertEqual(f["totals"]["24h"]["n"], 2); self.assertEqual(f["totals"]["7g"]["n"], 3)
        self.assertEqual(f["events"][0][1], "long")


if __name__ == "__main__":
    unittest.main()
