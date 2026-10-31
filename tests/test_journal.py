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
        r = journal.handle("/entrato 67.134 0,01", "2026-10-31 08:00:00", self.j, st)
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
        r = journal.handle("/entrato 67000", "2026-10-31 08:00:00", self.j, st)
        self.assertIn("specifica la strategia", r)
        self.assertEqual(self.j["trades"], [])
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
            {"tg_offset": 10, "v2": {"status": "aperto", "side": "long", "signal_date": "2026-10-30"}, "weekly": {}}))

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


if __name__ == "__main__":
    unittest.main()
