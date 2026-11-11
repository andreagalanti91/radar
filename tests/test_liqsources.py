import tempfile
import unittest

from radar import liqsources as L


class TestParsers(unittest.TestCase):
    def test_okx(self):
        e = L.parse_okx([{"ts": "1000", "bkPx": "70000", "sz": "100", "posSide": "long"}])[0]
        self.assertEqual((e["side"], e["btc"], e["usd"]), ("long", 1.0, 70000.0))

    def test_gate_sign(self):
        r = L.parse_gate([{"time": 1, "size": -20000, "fill_price": "70000"}, {"time": 2, "size": 0, "order_size": 0}])
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["side"], r[0]["btc"]), ("short", 2.0))

    def test_deribit_flags(self):
        base = {"timestamp": 1, "trade_id": "a", "direction": "sell", "price": 70000, "amount": 70000}
        r = L.parse_deribit([dict(base, liquidation="T"), dict(base, trade_id="b", liquidation="M"), dict(base, trade_id="c")])
        self.assertEqual([x["side"] for x in r], ["long", "short"])
        self.assertAlmostEqual(r[0]["btc"], 1.0)

    def test_kraken_dydx_lighter(self):
        k = L.parse_kraken([{"type": "liquidation", "time": "2026-01-01T00:00:00.123456789Z", "trade_id": 1,
                             "price": 1, "size": 2, "side": "buy"}, {"type": "fill"}])
        self.assertEqual(k[0]["side"], "short")
        d = L.parse_dydx([{"type": "LIQUIDATED", "createdAt": "2026-01-01T00:00:00.000Z", "id": "x",
                           "side": "SELL", "price": "1", "size": "3"}, {"type": "LIMIT"}])
        self.assertEqual((d[0]["side"], d[0]["btc"]), ("long", 3.0))
        li = L.parse_lighter([{"type": "liquidation", "is_maker_ask": True, "timestamp": 1, "trade_id": 9,
                               "price": "1", "size": "1"}, {"type": "trade"}])
        self.assertEqual(li[0]["side"], "short")


class TestStore(unittest.TestCase):
    def ev(self, i, px=70000.0, ts=1767225600000, side="long", ex="okx", btc=1.0):
        return L._ev(ts + i, ex, i, side, px, btc)

    def test_check(self):
        good, notes = L.check([self.ev(1), self.ev(2), self.ev(3, px=10.0), self.ev(4, px=0)], now_ms=1767225600000 + 10)
        self.assertEqual(len(good), 2)
        self.assertEqual(len(notes), 2)

    def test_dedupe_and_collect(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(L.store([self.ev(1), self.ev(1)], d), {"okx": 1})
            self.assertEqual(L.store([self.ev(1), self.ev(2)], d), {"okx": 1})

            def broken():
                raise RuntimeError("giù")
            res = L.collect(d, {"x": broken, "y": lambda: [self.ev(5, ex="y")]})
            self.assertEqual(res["status"]["x"][0], "errore")
            self.assertEqual(res["added"], {"y": 1})
            self.assertEqual(len(L.load(2, d)), 3)

    def test_summary(self):
        now = 1767225600000 + 2 * 3600_000
        evs = [self.ev(0, btc=10), self.ev(2 * 3600_000 - 60_000, side="short", ex="gate", btc=0.1)]
        s = L.summary(evs, now_ms=now)
        self.assertEqual(s["per_exchange"]["okx"]["1h"]["n"], 0)
        self.assertEqual(s["per_exchange"]["okx"]["24h"]["long_usd"], 700000.0)
        self.assertEqual(s["total"]["1h"]["short_usd"], 7000.0)
        self.assertEqual(len(s["big"]), 1)
        self.assertFalse(s["stale"])
        self.assertTrue(L.summary([], now_ms=now)["stale"])


if __name__ == "__main__":
    unittest.main()
