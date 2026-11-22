"""W3.2 su ETH (dal 22/11/2026, decisione dell'utente "Mantieni ETH nella strategia, inserisci dentro il Tool"): numeri della
ricerca research/w32_multi riprodotti dal tool, BTC invariato, capitale separato RADAR_ETH_CAPITAL, avvisi con l'asset nel titolo,
dati ETH mancanti che non bloccano il giro di BTC."""
import unittest
from unittest import mock

import pandas as pd

from radar import cli, coherence, guard, telegram, weekly
from radar.data import DATA_DIR

from tests.test_alerts import Sender, cur, trade

ETH_FILES = ["eth_spot", "eth_perp", "eth_funding", "eth_metrics", "fng"]
BTC_FILES = ["spot", "perp", "funding", "metrics", "fng"]


def eth_cur(status, **kw):
    c = cur(status, **kw)
    c.update(asset="ETH", asset_share=None, capital=10000.0, price=1700.0)
    c.pop("btc", None)
    if status in ("aperto", "uscita"):
        c.update(entry_px=2125.33, trail=2310.6, qty=6.9, notional=14700.0, side="short", pnl_pct=16.7, move_pct=20.7)
    if status == "segnale":
        c["plan"] = dict(c["plan"], qty=6.9)
        c["plan"].pop("btc", None)
    return c


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in ETH_FILES + BTC_FILES), "dati mancanti")
class TestNumeri(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar.data import load_all, load_asset
        from radar.features import build_features
        cls.FE = build_features(load_asset("ETH"))
        cls.FB = build_features(load_all())

    def test_eth_come_la_ricerca(self):
        # research/w32_multi: 10.000 $ dal 2021 al 10/11/2026 → 34.760 $, DD −27,5%, 15 trade, WR 60%
        r = weekly.simulate(self.FE[self.FE.index <= "2026-11-10"], start="2021-01-01")
        m = weekly.metrics(r)
        self.assertAlmostEqual(float(r["equity"].iloc[-1]), 34760, delta=35)   # funding OKX di novembre: scarto di ~2 $
        self.assertEqual(m["n"], 15)
        self.assertAlmostEqual(m["win_rate"], 60.0, delta=0.1)
        self.assertAlmostEqual(m["max_dd_pct"], -27.5, delta=0.1)

    def test_btc_invariato(self):
        # BTC con i dati congelati al 15/11: 78.474 $, 13 trade, WR 92% (W3.2, memoria/01-strategia/W3.2.md)
        g = self.FB[self.FB.index <= "2026-11-15"]
        r = weekly.simulate(g)
        m = weekly.metrics(r)
        self.assertAlmostEqual(float(r["equity"].iloc[-1]), 78474, delta=5)
        self.assertEqual((m["n"], m["win_rate"], m["max_dd_pct"]), (13, 92.3, -21.1))
        a, b = weekly.evaluate(g, capital=50000.0), weekly.evaluate(g, capital=50000.0, asset="BTC")
        self.assertEqual(a["history"], b["history"])
        self.assertEqual(a["asset"], "BTC")
        self.assertIn("btc", a.get("plan") or a)                           # chiave storica dei report BTC

    def test_eth_evaluate(self):
        e = weekly.evaluate(self.FE[self.FE.index <= "2026-11-21"], capital=15000.0, asset="ETH")
        self.assertEqual(e["asset"], "ETH")
        self.assertNotIn("btc", e)
        self.assertEqual(e["history"]["m1"]["n"], 15)
        if e["status"] in ("aperto", "uscita"):
            self.assertAlmostEqual(e["notional"], 15000.0 * e["expo"], delta=1)


class TestQuota(unittest.TestCase):
    def test_capitali_separati(self):
        # "non suddividere 70-30: 10k su ETH, 10k su BTC" (22/11): BTC resta su RADAR_CAPITAL × SHARE, ETH ha il suo capitale
        self.assertAlmostEqual(weekly.ETH_CAPITAL, 10000.0)
        self.assertAlmostEqual(weekly.asset_capital("ETH"), 10000.0)
        self.assertAlmostEqual(weekly.asset_capital("BTC"), weekly.CAPITAL * weekly.SHARE)
        self.assertAlmostEqual(weekly.asset_capital("BTC", 10000.0), 10000.0)

    def test_rischio_sulla_quota(self):
        p = weekly.plan(-1, 2000.0, 200.0, 2100.0, 15000.0, "ETH")       # stop al 25% del prezzo: esposizione 1x
        self.assertEqual(p["notional"], 15000.0)
        self.assertNotIn("btc", p)
        self.assertAlmostEqual(p["qty"], 7.5)
        self.assertLessEqual(p["loss_usd"], 15000.0 * 0.27)


class TestAvvisi(unittest.TestCase):
    def test_titoli_con_asset(self):
        for status in ("segnale", "aperto"):
            ev, _ = weekly.diff_events(eth_cur(status), {}, lost=False)
            self.assertTrue(ev)
            for e in ev:
                txt = weekly.format_event(e)
                self.assertIn("RADAR SIGNAL ETH", txt)
                self.assertNotIn("BTC", txt)
        txt = weekly.format_event({"type": "w_trail", "w": eth_cur("aperto"), "old": 2400.0})
        self.assertIn("RADAR SIGNAL ETH · Settimanale: trailing aggiornato", txt)
        x = dict(trade(exit_="2026-11-16", exit_px=1900.0, reason="trail", pnl=8.0), side="short")
        txt = weekly.format_event({"type": "w_exit", "trade": x, "w": eth_cur("nessuno")})
        self.assertIn("RADAR SIGNAL ETH · USCITA SETTIMANALE ESEGUITA", txt)
        # BTC invariato
        self.assertIn("RADAR SIGNAL BTC · SEGNALE", weekly.format_event({"type": "w_signal", "w": cur("segnale")}))

    def test_stop_in_tempo_reale(self):
        c = eth_cur("aperto")
        h = pd.DataFrame({"open": [2200.0], "high": [2350.0], "low": [2150.0], "close": [2340.0]})
        ev, keys = weekly.check_intraday(c, [], h)
        self.assertEqual(len(ev), 1)
        self.assertTrue(keys[0].startswith("W:ETH:"))
        self.assertIn("RADAR SIGNAL ETH · Settimanale: stop toccato", weekly.format_intraday(ev))

    def test_stato_separato_e_primo_avvio(self):
        st = {"weekly": {"notified": ["x"]}}
        s = Sender()
        cli.weekly_alerts(eth_cur("aperto", date="2026-11-22"), st, s, h=pd.DataFrame())
        self.assertEqual(st["weekly"], {"notified": ["x"]})                 # stato BTC non toccato
        self.assertIn("weekly_eth", st)
        self.assertEqual(st["weekly_eth_since"], "2026-11-22")
        self.assertEqual(len(s.texts), 1)
        self.assertIn("Posizione settimanale in corso", s.texts[0])         # primo avvio: "in corso", non stato perso
        self.assertIn("RADAR SIGNAL ETH", s.texts[0])
        s2 = Sender()
        cli.weekly_alerts(eth_cur("aperto", date="2026-11-23"), st, s2, h=pd.DataFrame())
        self.assertEqual(s2.texts, [])                                      # niente doppioni

    def test_riepilogo_oggi_e_guard(self):
        txt = telegram.today_brief({"weekly": cur("aperto"), "weekly_eth": eth_cur("aperto")}, "2026-11-22")
        self.assertIn("<b>ETH · W3.2</b>: SHORT", txt)
        self.assertIn("su $10.000", txt)
        self.assertIn("RADAR SIGNAL ETH · Soglia", guard.format_alarm({"why": ["x"], "since": "2026-11-22"}, "ETH"))
        self.assertIn("RADAR SIGNAL ETH · Controllo", coherence.format_alert(["x"], "ETH"))
        hb = weekly.format_heartbeat(cur("aperto"), "2026-11-21", "22/11", [], "2026-11-22", {"ETH": eth_cur("aperto")})
        self.assertIn("ETH short aperto", hb)


class TestIsolamento(unittest.TestCase):
    def test_dati_eth_mancanti(self):
        errors = {"eth_perp": "RuntimeError: rotta"}
        out = cli.asset_round("ETH", {}, {}, pd.Timestamp("2026-11-22"), errors, send=Sender(), fetch=lambda a, e: None)
        self.assertIsNone(out)
        from radar.data import is_critical
        self.assertTrue(is_critical("eth_perp"))
        s, st = Sender(), {}
        cli.source_alerts(errors, {}, st, pd.Timestamp("2026-11-22 08:00"), "2026-11-21", send=s)
        self.assertIn("eth_perp", s.texts[0])

    def test_update_asset_senza_rete(self):
        from radar import data
        boom = mock.Mock(side_effect=RuntimeError("rete"))
        with mock.patch.multiple(data, fetch_spot=boom, fetch_perp=boom, fetch_funding=boom, fetch_metrics=boom), \
                mock.patch.object(data, "_cached", lambda n: None), mock.patch("builtins.print"):
            errors = {}
            self.assertIsNone(data.update_asset("ETH", errors))             # nessuna eccezione
            self.assertIn("eth_spot", errors)

    @unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in BTC_FILES), "dati mancanti")
    def test_giro_btc_prosegue(self):
        """daily(): ETH che fallisce non ferma BTC (valutato e avvisato prima) né il resto del giro."""
        from radar.data import load_all
        d = load_all()
        st, seen = {}, []
        with mock.patch.object(cli, "update_all", return_value=d), \
                mock.patch.object(cli, "update_asset", side_effect=RuntimeError("ETH rotto")), \
                mock.patch.object(cli, "weekly_alerts", side_effect=lambda c, s, *a, **k: seen.append(weekly.asset_of(c)) or []), \
                mock.patch.object(cli, "_load_state", return_value=st), mock.patch.object(cli, "_save_state"), \
                mock.patch.object(cli.journal, "poll", return_value=0), mock.patch.object(cli.telegram, "send", return_value=False), \
                mock.patch("radar.provlog.update", return_value=None), mock.patch("radar.guard.update", return_value=None), \
                mock.patch("radar.coherence.update", return_value={"problems": []}), \
                mock.patch.object(cli, "collect_liquidations"), mock.patch.object(cli, "daily_brief"), \
                mock.patch.object(cli, "evaluate", side_effect=RuntimeError("v2 fermo qui")), mock.patch("builtins.print"):
            cli.daily()
        self.assertEqual(seen, ["BTC"])                                     # BTC avvisato, ETH non calcolato
        self.assertIn("last_run", st)                                       # il giro è arrivato in fondo

if __name__ == "__main__":
    unittest.main()
