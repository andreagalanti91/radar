import unittest

from radar import wallets as W


def pos(szi, ntl, entry=100.0):
    return {"szi": szi, "ntl": ntl, "entry": entry}


class DiffTest(unittest.TestCase):
    def test_nothing_changed(self):
        s = {"pos": {"BTC": pos(10, 1e6)}, "ord": {}}
        self.assertEqual(W.diff("X", s, s), [])

    def test_open_close_flip(self):
        old = {"pos": {"ETH": pos(5, 2e5), "SOL": pos(-3, 3e5)}, "ord": {}}
        new = {"pos": {"BTC": pos(1, 1e6), "SOL": pos(4, 4e5)}, "ord": {}}
        out = "\n".join(W.diff("X", old, new))
        self.assertIn("Apre <b>LONG BTC</b>", out)
        self.assertIn("Chiude <b>LONG ETH</b>", out)
        self.assertIn("Gira <b>SOL</b>", out)

    def test_small_changes_ignored(self):
        old = {"pos": {"BTC": pos(10, 1e6), "DOGE": pos(1, 1e3)}, "ord": {}}
        new = {"pos": {"BTC": pos(11, 1.1e6), "PEPE": pos(1, 2e4)}, "ord": {}}   # +10% e posizioni sotto soglia
        self.assertEqual(W.diff("X", old, new), [])

    def test_increase_and_new_orders(self):
        old = {"pos": {"BTC": pos(-10, 1e6)}, "ord": {"1": {}}}
        new = {"pos": {"BTC": pos(-20, 2e6)}, "ord": {"1": {}, "2": {"coin": "BTC", "side": "sell", "px": 1e5, "ntl": 5e5, "type": "Limit", "ro": False, "tpsl": False},
                                                       "3": {"coin": "ETH", "side": "buy", "px": 3e3, "ntl": 1e4, "type": "Limit", "ro": False, "tpsl": False}}}
        out = "\n".join(W.diff("X", old, new))
        self.assertIn("Aumenta <b>SHORT BTC</b>", out)
        self.assertIn("Nuovo ordine vendita <b>BTC</b>", out)
        self.assertNotIn("ETH", out)   # ordine sotto soglia


if __name__ == "__main__":
    unittest.main()
