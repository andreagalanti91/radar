"""Registro dei trade reali via Telegram (radar/journal.py): parsing dei comandi, filtro della chat, offset di getUpdates,
confronto col segnale. getUpdates/sendMessage simulati: nessun messaggio reale inviato."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from radar import journal

CHAT = "12345"


def _msg(uid, text, chat=CHAT, ts=1793433600):   # 1793433600 = 2026-10-31 08:00 UTC
    return {"update_id": uid, "message": {"message_id": uid, "date": ts, "chat": {"id": int(chat)}, "text": text}}


class TestParsing(unittest.TestCase):
    def test_numeri(self):
        n = journal.num
        self.assertEqual(n("67500"), 67500)
        self.assertEqual(n("67.500"), 67500)
        self.assertEqual(n("67,500"), 67500)
        self.assertEqual(n("67500,5"), 67500.5)
        self.assertEqual(n("67.500,5"), 67500.5)
        self.assertEqual(n("67,500.5"), 67500.5)
        self.assertEqual(n("0,015", price=False), 0.015)
        self.assertEqual(n("1,5", price=False), 1.5)
        self.assertIsNone(n("tp"))

    def test_comandi(self):
        cmd, a = journal.parse("/Entrato 67.500 0,015 W2 SHORT")
        self.assertEqual((cmd, a["price"], a["qty"], a["strategy"], a["side"]), ("entrato", 67500, 0.015, "w2", "short"))
        cmd, a = journal.parse("/uscito@RadarBot 69100,5 take profit")
        self.assertEqual((cmd, a["price"], a["words"]), ("uscito", 69100.5, ["take", "profit"]))
        self.assertEqual(journal.parse("ciao")[0], "")


class TestHandle(unittest.TestCase):
    def setUp(self):
        self.j = {"exchange": "bybit/okx", "trades": [], "ref": {}}

    def test_deduce_dal_segnale_e_confronto(self):
        st = {"v2": {"status": "aperto", "side": "long", "signal_date": "2026-10-30"}, "weekly": {"status": "nessuno"}}
        self.j["ref"]["v2"] = {"signal_date": "2026-10-30", "entry": 67000.0, "entry_time": "2026-10-31 04:00:00", "limit": 66500.0}
        r = journal.handle("/entrato 67.134 0,01 v2", "2026-10-31 08:00:00", self.j, st)   # v2 solo se scritta
        self.assertIn("long V2", r)
        t = self.j["trades"][0]
        self.assertEqual((t["strategy"], t["side"], t["signal_date"]), ("v2", "long", "2026-10-30"))
        self.assertAlmostEqual(t["compare"]["slip_entry_pct"], 0.2, places=3)   # comprato 0,2% più caro
        self.assertEqual(t["compare"]["delay_entry_h"], 4.0)
        journal.handle("/limit 66500 0,015", "2026-10-31 12:00:00", self.j, st)
        self.assertAlmostEqual(t["avg"], (67134 * 0.01 + 66500 * 0.015) / 0.025, places=1)
        self.assertEqual(t["compare"]["slip_limit_pct"], 0.0)
        r = journal.handle("/uscito 68000 tp", "2026-11-01 09:00:00", self.j, st)
        self.assertIn("risultato", r)
        self.assertGreater(t["result_pct"], 0)
        self.assertEqual(t["exit"]["reason"], "tp")

    def test_chiede_se_ambiguo(self):
        st = {"v2": {"status": "aperto", "side": "long", "signal_date": "2026-10-30"},
              "weekly": {"status": "aperto", "side": "long", "signal_date": "2026-08-23"}}
        r = journal.handle("/entrato 67000", "2026-10-31 08:00:00", self.j, st)   # dal 26/11: W3.2 se non scritto
        self.assertIn("W3.2 BTC", r)
        self.assertEqual(self.j["trades"][0]["strategy"], "w2")
        self.j["trades"].clear()
        r = journal.handle("/entrato 67000 v2 short", "2026-10-31 08:00:00", {**self.j}, {})
        self.assertIn("Registrato", r)
        self.assertIn("specifica il lato", journal.handle("/entrato 67000 w2", "2026-10-31 08:00:00", self.j, {}))
        self.assertIn("Nessun trade", journal.handle("/uscito 1000", "2026-10-31 08:00:00",
                                                     {"exchange": "x", "trades": [], "ref": {}}, {}))

    def test_short_e_exchange(self):
        journal.handle("/exchange OKX", "2026-10-31 08:00:00", self.j, {})
        journal.handle("/entrato 70000 w2 short", "2026-10-31 08:00:00", self.j, {})
        t = self.j["trades"][0]
        t["signal"] = {"entry": 70350.0, "entry_time": "2026-10-31 00:00:00", "exit": 65000.0, "exit_time": "2026-11-09"}
        journal.handle("/uscito 65325 trailing", "2026-11-09 03:00:00", self.j, {})
        self.assertEqual(t["exchange"], "okx")
        self.assertAlmostEqual(t["compare"]["slip_entry_pct"], 0.498, places=2)   # short venduto più basso: peggio
        self.assertAlmostEqual(t["compare"]["slip_exit_pct"], 0.5, places=3)      # ricomprato più caro: peggio
        self.assertEqual(t["compare"]["delay_exit_h"], 3.0)
        self.assertAlmostEqual(t["result_pct"], (1 - 65325 / 70000) * 100, places=2)
        self.assertIn("Medie su 1 trade", journal.summary(self.j))


class TestPoll(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = [mock.patch.object(journal, "JOURNAL_FILE", self.tmp / "journal.json"),
                  mock.patch.object(journal, "STATE_FILE", self.tmp / "state.json"),
                  mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "finto", "TELEGRAM_CHAT_ID": CHAT})]
        for x in self.p:
            x.start()
        (self.tmp / "state.json").write_text(json.dumps(
            {"tg_offset": 10, "v2": {"status": "aperto", "side": "long", "signal_date": "2026-10-30"},
             "weekly": {"status": "aperto", "side": "long", "signal_date": "2026-10-25"}}))

    def tearDown(self):
        for x in self.p:
            x.stop()

    def test_filtro_chat_offset_e_risposte(self):
        ups = [_msg(10, "/entrato 67000 0,01"), _msg(11, "/entrato 1", chat="999"), _msg(12, "testo libero"),
               _msg(13, "/registro")]
        calls = []

        def fake(method, **kw):
            calls.append((method, kw))
            return {"ok": True, "result": ups} if method == "getUpdates" else {"ok": True}

        with mock.patch.object(journal, "_api", side_effect=fake), mock.patch("requests.post") as post:
            self.assertEqual(journal.poll(), 2)
            post.assert_not_called()
        self.assertEqual(calls[0][1]["offset"], 10)
        sent = [kw for m, kw in calls if m == "sendMessage"]
        self.assertEqual(len(sent), 2)
        self.assertTrue(all(kw["chat_id"] == CHAT for kw in sent))
        st = json.loads((self.tmp / "state.json").read_text())
        self.assertEqual(st["tg_offset"], 14)
        self.assertEqual(st["v2"]["side"], "long")   # il resto dello stato resta intatto
        j = json.loads((self.tmp / "journal.json").read_text())
        self.assertEqual(len(j["trades"]), 1)
        self.assertEqual(j["trades"][0]["entries"][0]["time"], "2026-10-31 08:00:00")

    def test_senza_token_non_fa_nulla(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}), mock.patch.object(journal, "_api") as api:
            self.assertEqual(journal.poll(), 0)
            api.assert_not_called()

    def test_link_col_segnale(self):
        journal.save({"exchange": "bybit", "ref": {}, "trades": [
            {"id": "a", "strategy": "v2", "side": "long", "exchange": "bybit", "signal_date": "2026-10-30",
             "entries": [{"price": 67100.0, "qty": None, "time": "2026-10-31 06:00:00", "kind": "ingresso"}],
             "exit": {"price": 68200.0, "time": "2026-11-02 10:00:00", "reason": "tp"}, "signal": {}}]})
        rep = {"v2": {"status": "nessuno"}, "trades": {"futures": [
            {"signal_date": "2026-10-30", "entry": 67000.0, "entry_time": "2026-10-31 04:00:00", "levels": [67000.0, 66500.0],
             "exit": "tp", "exit_px": 68300.0, "exit_time": "2026-11-02 08:00:00", "pnl_pct_invested": 1.94}]}}
        journal.link(rep)
        t = journal.load()["trades"][0]
        self.assertEqual(t["signal"]["exit"], 68300.0)
        self.assertEqual(t["compare"]["delay_entry_h"], 2.0)
        self.assertEqual(t["compare"]["delay_exit_h"], 2.0)
        self.assertAlmostEqual(t["compare"]["slip_exit_pct"], 0.146, places=3)
        self.assertIn("result_vs_signal_pct", t["compare"])


# ---------------------------------------------------------------- W3.2 su BTC ed ETH (26/11/2026: diario delle operazioni vere)

ST_W3 = {"weekly": {"status": "aperto", "side": "short", "signal_date": "2026-11-15"},
         "weekly_eth": {"status": "aperto", "side": "short", "signal_date": "2026-11-08"},
         "v2": {"status": "ingresso", "side": "long", "signal_date": "2026-11-21"}}   # v2 spenta: non deve contare


def _rep(btc_exit=None):
    b = {"signal": "2026-11-15", "entry": "2026-11-16", "side": "short", "market": "perp", "expo": 0.97,
         "entry_px": 65285.7, "exit": None, "exit_px": None, "reason": "open", "move_pct": 8.0, "pnl_pct": 7.5}
    if btc_exit:
        b.update(exit="2026-12-01", exit_px=btc_exit, reason="trail")
    e = {"signal": "2026-11-08", "entry": "2026-11-09", "side": "short", "market": "perp", "expo": 0.81,
         "entry_px": 2125.33, "exit": None, "exit_px": None, "reason": "open", "move_pct": 20.0, "pnl_pct": 16.0}
    return {"weekly": {"status": "nessuno" if btc_exit else "aperto", "signal_date": "2026-11-15", "side": "short",
                       "entry_px": 65285.7, "entry": "2026-11-16", "market": "perp", "history": {"trades": [b]}},
            "weekly_eth": {"status": "aperto", "signal_date": "2026-11-08", "side": "short", "entry_px": 2125.33,
                           "entry": "2026-11-09", "market": "perp", "history": {"trades": [e]}}}


class TestW32(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = mock.patch.object(journal, "JOURNAL_FILE", self.tmp / "journal.json")
        self.p.start()
        self.j = {"exchange": "bybit", "trades": [], "ref": {}}

    def tearDown(self):
        self.p.stop()

    def test_parse_commissioni_importo_asset(self):
        cmd, a = journal.parse("/entrato 2.120,5 eth importo 14.000 comm 7,25 w3.2")
        self.assertEqual((cmd, a["price"], a["asset"], a["amount"], a["fee"], a["strategy"]),
                         ("entrato", 2120.5, "ETH", 14000.0, 7.25, "w2"))
        self.assertAlmostEqual(a["qty"], 14000 / 2120.5, places=5)   # quantità dall'importo
        cmd, a = journal.parse("/uscito 59800 0,2 btc comm 6 trailing")
        self.assertEqual((a["price"], a["qty"], a["asset"], a["fee"], a["words"]), (59800, 0.2, "BTC", 6.0, ["trailing"]))

    def test_ingresso_btc_ed_eth_dedotti(self):
        r = journal.handle("/entrato 65.150 0,45 comm 14,7", "2026-11-16 09:00:00", self.j, ST_W3)
        self.assertIn("W3.2 BTC", r)
        r2 = journal.handle("/entrato 2120,5 importo 14000 comm 7", "2026-11-09 08:00:00", self.j, ST_W3)
        self.assertIn("W3.2 ETH", r2)
        b, e = self.j["trades"]
        self.assertEqual((b["strategy"], b["asset"], b["side"], b["signal_date"]), ("w2", "BTC", "short", "2026-11-15"))
        self.assertEqual((e["asset"], e["signal_date"]), ("ETH", "2026-11-08"))
        self.assertEqual(b["fees"], 14.7)
        self.assertAlmostEqual(e["qty"] * e["avg"], 14000, places=0)
        self.assertIn("commissioni $14,70", r)

    def test_uscita_parziale_poi_totale_e_confronto(self):
        journal.handle("/entrato 65150 0,45 btc comm 14,7", "2026-11-16 09:00:00", self.j, ST_W3)
        r = journal.handle("/uscito 59800 0,2 comm 6", "2026-12-01 09:00:00", self.j, ST_W3)
        self.assertIn("Uscita parziale", r)
        t = self.j["trades"][0]
        self.assertIsNone(t["exit"])
        r = journal.handle("/uscito 59900 0,25 btc comm 7 trailing", "2026-12-01 10:00:00", self.j, ST_W3)
        self.assertIn("Uscita W3.2 BTC short", r)
        xa = (59800 * 0.2 + 59900 * 0.25) / 0.45
        self.assertAlmostEqual(t["exit"]["price"], xa, places=1)
        self.assertAlmostEqual(t["pnl_usd"], 0.45 * (65150 - xa) - 27.7, places=1)   # short: guadagno quando scende
        journal.save(self.j)
        journal.link(_rep(btc_exit=59950.0))
        t = journal.load()["trades"][0]
        c = t["compare"]
        self.assertAlmostEqual(c["slip_entry_pct"], (65285.7 - 65150) / 65285.7 * 100, places=2)   # venduto più basso: peggio
        self.assertAlmostEqual(c["slip_exit_pct"], (59950 - xa) / 59950 * -100, places=2)          # ricomprato più basso: meglio
        self.assertEqual(c["delay_entry_h"], 9.0)
        model = 0.45 * (65285.7 - 59950) - 0.45 * (65285.7 + 59950) * 0.0005   # perp: 0,05% per lato
        self.assertAlmostEqual(t["model_usd"], model, places=1)
        self.assertAlmostEqual(c["effect_usd"], t["pnl_usd"] - model, places=1)

    def test_totale_reale_contro_modello(self):
        journal.handle("/entrato 65150 0,45 comm 14,7", "2026-11-16 09:00:00", self.j, ST_W3)
        journal.handle("/entrato 2120,5 importo 14000 comm 7", "2026-11-09 08:00:00", self.j, ST_W3)
        journal.handle("/uscito 59900 btc comm 13", "2026-12-01 10:00:00", self.j, ST_W3)
        journal.handle("/entrato 67000 0,01 v2", "2026-11-22 10:00:00", self.j, ST_W3)   # v2: fuori dalla vista W3.2
        journal.save(self.j)
        journal.link(_rep(btc_exit=59950.0))
        rv = journal.real_vs_model(journal.load())
        self.assertEqual((rv["n"], rv["closed"], rv["n_effect"]), (2, 1, 2))
        b = next(r for r in rv["rows"] if r["asset"] == "BTC")
        e = next(r for r in rv["rows"] if r["asset"] == "ETH")
        self.assertFalse(e["closed"])
        self.assertAlmostEqual(e["effect_usd"], -(14000 / 2120.5) * (2125.33 - 2120.5) - (7 - 14000 / 2120.5 * 2125.33 * 0.0005), places=1)
        self.assertAlmostEqual(rv["effect_usd"], b["effect_usd"] + e["effect_usd"], places=2)
        self.assertEqual(b["model_entry"], 65285.7)
        self.assertIn("Esecuzione reale contro modello", journal.summary(journal.load()))

    def test_asset_sbagliato_non_chiude_altro(self):
        journal.handle("/entrato 65150 0,45 btc", "2026-11-16 09:00:00", self.j, ST_W3)
        r = journal.handle("/uscito 2050", "2026-12-01 09:00:00", self.j, ST_W3)   # prezzo da ETH, ETH non aperto
        self.assertIn("Nessun trade ETH aperto", r)
        self.assertIsNone(self.j["trades"][0]["exit"])

    def test_senza_operazioni_vere(self):
        rv = journal.real_vs_model({"trades": []})
        self.assertEqual((rv["n"], rv["effect_usd"]), (0, None))
        self.assertIn("/entrato", rv["help"])

    def test_aggancio_senza_segnale_attivo(self):
        journal.handle("/entrato 65200 0,1 btc short", "2026-11-17 12:00:00", self.j, {})   # stato perso: nessun segnale
        self.assertIsNone(self.j["trades"][0]["signal_date"])
        journal.save(self.j)
        journal.link(_rep())
        t = journal.load()["trades"][0]
        self.assertEqual(t["signal_date"], "2026-11-15")   # operazione del modello più vicina, stesso lato
        self.assertEqual(t["signal"]["entry"], 65285.7)

    def test_aiuto_w32_e_html(self):
        from test_telegram_formato import check_html
        h = journal.handle("/aiuto", "2026-11-26 10:00:00", self.j, {})
        self.assertIn("W3.2 su BTC ed ETH", h)
        for c in ("/entrato", "/aggiungi", "/uscito", "comm", "importo", "/registro"):
            self.assertIn(c, h)
        for txt in (journal.HELP, journal.handle("/uscito 59800 0,2", "2026-12-01 09:00:00",
                                                {"exchange": "x", "ref": {}, "trades": [
                                                    {"id": "a", "strategy": "w2", "asset": "BTC", "side": "short",
                                                     "exchange": "x", "signal_date": None, "signal": {},
                                                     "entries": [{"price": 65000.0, "qty": 0.5, "time": "2026-11-16 09:00:00"}],
                                                     "exits": [], "exit": None}]}, {})):
            self.assertEqual(check_html(txt)[0], [], txt)


if __name__ == "__main__":
    unittest.main()
