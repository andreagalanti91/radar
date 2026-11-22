"""Registro dei muri del book (radar/orderbook.book_walls, log_walls) e fonte del funding. Niente rete."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from radar import data, orderbook as ob


def book(mid=60000.0, n=4000, tick=1.0, q=0.1):
    return [(mid - 0.5 - i * tick, q) for i in range(n)], [(mid + 0.5 + i * tick, q) for i in range(n)]


class TestWalls(unittest.TestCase):
    def test_cluster(self):
        b, a = book()
        b.append((58810.0, 50.0))                     # muro in acquisto a ~−2%
        a.append((61000.0, 20.0))
        b.sort(key=lambda x: -x[0]); a.sort(key=lambda x: x[0])
        w = ob.book_walls("okx_perp", b, a, "t")
        bid = [r for r in w if r["side"] == "bid"]
        ask = [r for r in w if r["side"] == "ask"]
        self.assertEqual((len(bid), len(ask)), (3, 3))
        self.assertEqual(bid[0]["price"], 58825)       # centro della fascia 58800–58850
        self.assertAlmostEqual(bid[0]["dist_pct"], -1.958, places=2)
        self.assertGreater(bid[0]["x_mean"], 5)
        self.assertEqual(ask[0]["price"], 61025)
        self.assertTrue(all(abs(r["dist_pct"]) <= 3 for r in w))
        self.assertEqual(ob.book_walls("x", [], a, "t"), [])

    def test_copertura_parziale(self):
        b, a = book(n=300)                             # il book arriva solo a ±0,5%
        w = ob.book_walls("kraken", b, a, "t")
        self.assertTrue(all(r["cover_pct"] < 0.6 for r in w))
        self.assertTrue(all(0.9 < r["x_mean"] < 1.6 for r in w))   # livelli uniformi: media sulle sole fasce coperte

    def test_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            books = {"coinbase": book(), "okx_spot": book()}
            ob.log_walls(tmp, books, pd.Timestamp("2026-11-22 10:07"))
            ob.log_walls(tmp, books, pd.Timestamp("2026-11-22 10:20"))   # stesso giro (<20 min): niente doppioni
            ob.log_walls(tmp, books, pd.Timestamp("2026-11-22 11:07"))
            df = pd.read_csv(tmp / "book_walls.csv")
            self.assertEqual(list(df.columns), ob.WALL_COLS)
            self.assertEqual(len(df), 2 * 2 * 6)
            self.assertEqual(set(df["exchange"]), {"coinbase", "okx_spot"})


class TestFundingSource(unittest.TestCase):
    def test_etichetta(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(data, "DATA_DIR", Path(tmp)):
            idx = pd.to_datetime(["2026-10-30", "2026-10-31", "2026-11-01", "2026-11-02"])
            df = pd.DataFrame({"funding": [1e-4, 2e-4, 3e-4, 4e-4]}, index=idx)
            out = data._funding_sources(df, pd.Timestamp("2026-11-01").date())
            self.assertEqual(list(out["source"]), ["binance", "binance", "okx", "okx"])
            self.assertEqual(list(out["funding"]), [1e-4, 2e-4, 3e-4, 4e-4])
            self.assertTrue((Path(tmp) / "funding.csv").exists())
            df2 = out.copy(); df2.loc[idx[2], "source"] = "binance"
            self.assertEqual(data._funding_sources(df2, idx[2].date())["source"].iloc[2], "binance")   # etichetta esistente


if __name__ == "__main__":
    unittest.main()
