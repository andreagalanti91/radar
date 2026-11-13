"""Raccoglitore WebSocket (radar/liqstream.py): parser sui messaggi di esempio delle documentazioni, archivio orario, git. Niente rete."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from radar import liqsources, liqstream

# esempi dalle documentazioni ufficiali (Binance USDⓈ-M "Liquidation Order Streams", Bybit v5 "All Liquidation", OKX "Liquidation orders")
BINANCE = {"e": "forceOrder", "E": 1568014460893, "o": {"s": "BTCUSDT", "S": "SELL", "o": "LIMIT", "f": "IOC", "q": "0.014", "p": "9910",
                                                       "ap": "9910", "X": "FILLED", "l": "0.014", "z": "0.014", "T": 1568014460893}}
BYBIT = {"topic": "allLiquidation.BTCUSDT", "type": "snapshot", "ts": 1739502303204,
         "data": [{"T": 1739502302929, "s": "BTCUSDT", "S": "Sell", "v": "0.5", "p": "96000.5"},
                  {"T": 1739502302930, "s": "BTCUSDT", "S": "Buy", "v": "0.25", "p": "95000"}]}
OKX = {"arg": {"channel": "liquidation-orders", "instType": "SWAP"},
       "data": [{"details": [{"bkLoss": "0", "bkPx": "0.007831", "ccy": "", "posSide": "short", "side": "buy", "sz": "13", "ts": "1692266434010"}],
                 "instFamily": "IOST-USDT", "instId": "IOST-USDT-SWAP", "instType": "SWAP", "uly": "IOST-USDT"},
                {"details": [{"bkLoss": "0", "bkPx": "69000.1", "ccy": "", "posSide": "long", "side": "sell", "sz": "150", "ts": "1692266434011"}],
                 "instFamily": "BTC-USDT", "instId": "BTC-USDT-SWAP", "instType": "SWAP", "uly": "BTC-USDT"}]}


class TestParser(unittest.TestCase):
    def test_binance(self):
        e = liqstream.parse("binance", json.dumps(BINANCE))
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["exchange"], e[0]["side"], e[0]["price"], e[0]["btc"]), ("binance", "long", 9910.0, 0.014))
        self.assertAlmostEqual(e[0]["usd"], 138.74)
        # flusso combinato e !forceOrder@arr: stesso ordine → stesso id; altri simboli scartati
        wrapped = {"stream": "!forceOrder@arr", "data": BINANCE}
        self.assertEqual(liqstream.parse("binance", json.dumps(wrapped))[0]["id"], e[0]["id"])
        eth = json.loads(json.dumps(BINANCE)); eth["o"]["s"] = "ETHUSDT"
        self.assertEqual(liqstream.parse("binance", json.dumps(eth)), [])
        buy = json.loads(json.dumps(BINANCE)); buy["o"]["S"] = "BUY"
        self.assertEqual(liqstream.parse_binance(buy)[0]["side"], "short")

    def test_bybit(self):
        e = liqstream.parse("bybit", json.dumps(BYBIT))
        self.assertEqual([x["side"] for x in e], ["short", "long"])   # doc: S = Buy → posizione long liquidata
        self.assertAlmostEqual(e[0]["usd"], 48000.25)
        self.assertEqual(liqstream.parse("bybit", json.dumps({"success": True, "op": "subscribe"})), [])
        self.assertEqual(liqstream.parse("bybit", json.dumps({"op": "pong"})), [])
        rose = {"topic": "allLiquidation.ROSEUSDT", "data": [{"T": 1, "s": "ROSEUSDT", "S": "Sell", "v": "20000", "p": "0.04499"}]}
        self.assertEqual(liqstream.parse("bybit", json.dumps(rose)), [])

    def test_okx_stessi_id_del_rest(self):
        e = liqstream.parse("okx", json.dumps(OKX))
        self.assertEqual(len(e), 1)   # solo BTC-USDT-SWAP
        self.assertEqual((e[0]["side"], e[0]["btc"]), ("long", 1.5))   # 150 contratti × 0,01 BTC
        self.assertEqual(e[0]["id"], liqsources.parse_okx(OKX["data"][1]["details"])[0]["id"])
        self.assertEqual(liqstream.parse("okx", "pong"), [])
        self.assertEqual(liqstream.parse("okx", "{non json"), [])


class TestStore(unittest.TestCase):
    def test_ore_chiuse_senza_doppioni_e_fusione(self):
        with tempfile.TemporaryDirectory() as d:
            st = liqstream.Store(Path(d))
            t0 = 1794592800000   # 2026-11-13 18:00 UTC
            a = liqstream.parse_bybit({"topic": "allLiquidation.BTCUSDT", "data": [{"T": t0 + 5, "s": "BTCUSDT", "S": "Buy", "v": "1", "p": "69000"}]})
            b = liqstream.parse_bybit({"topic": "allLiquidation.BTCUSDT", "data": [{"T": t0 + 3_600_005, "s": "BTCUSDT", "S": "Sell", "v": "1", "p": "69100"}]})
            self.assertEqual(st.add(a + a, "bybit"), 1)
            st.add(b, "bybit")
            files = st.flush(now_ms=t0 + 3_600_100)          # l'ora 19 è ancora aperta
            self.assertEqual([p.relative_to(d).as_posix() for p in files], ["2026-11-13/18.csv"])
            st.add(a, "bybit")                                # evento ripetuto dopo il flush: si fonde senza doppioni
            st.flush(now_ms=t0 + 7_200_100)
            with open(Path(d) / "2026-11-13/18.csv") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(list(rows[0]), liqsources.COLS)
            self.assertTrue((Path(d) / "2026-11-13/19.csv").exists())
            ev = liqsources.load_stream(48, d, now_ms=t0 + 7_200_100)
            self.assertEqual(sorted(e["exchange"] for e in ev), ["bybit", "bybit"])
            s = liqsources.stream_status(d, now_ms=t0 + 7_200_100)
            self.assertFalse(s["stale"])
            self.assertTrue(liqsources.stream_status(d, now_ms=t0 + 10 * 3_600_000)["stale"])
            self.assertIsNone(liqsources.stream_status(Path(d) / "manca"))
            summ = liqsources.summary(ev, now_ms=t0 + 7_200_100)
            self.assertEqual(summ["total"]["24h"]["n"], 2)
            self.assertEqual(liqsources.merge(ev, ev), ev)


class TestGit(unittest.TestCase):
    def test_token_mai_nella_riga_di_comando(self):
        env = liqstream.git_env({"LIQSTREAM_GIT_TOKEN": "segreto123", "PATH": "/bin"})
        self.assertNotIn("LIQSTREAM_GIT_TOKEN", env)
        self.assertNotIn("segreto123", json.dumps(env))   # solo in base64 nell'header
        self.assertTrue(env["GIT_CONFIG_VALUE_0"].startswith("AUTHORIZATION: basic "))
        cmds = liqstream.push_commands("data/liq_stream", "main", "msg")
        self.assertNotIn("segreto123", json.dumps(cmds))
        self.assertEqual(cmds[-1][-1], "HEAD:main")
        env = liqstream.git_env({"LIQSTREAM_SSH_KEY": "/home/u/.ssh/radar_deploy"})
        self.assertIn("/home/u/.ssh/radar_deploy", env["GIT_SSH_COMMAND"])


if __name__ == "__main__":
    unittest.main()
