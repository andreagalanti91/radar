"""W3.2 nei testi per l'utente (Telegram, avvisi, riepilogo "Oggi", pre-analisi) e blocco "Sentiment di mercato" della
pre-analisi (radar/preview.sentiment, da data/book_sentiment.csv). Nessun effetto sulle decisioni di W3.2."""
import re
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from radar import cli, preview, telegram, weekly
from test_alerts import cur, trade
from test_preview_today import PV, REPORT, _synth

BAD = re.compile(r"W3\.1|W2|\bv2\b|\(W3[),]|<b>W3</b>|\bW3 |decide W3\.$|Settimanale W3<")
COLS = ["ts", "price", "I", "L", "S", "n_src", "sources", "bid_usd", "ask_usd", "liq_short_usd", "liq_long_usd", "liq_n",
        "liq_src", "liq_age_min", "pulled_bid", "pulled_ask", "filled_bid", "filled_ask", "still_bid", "still_ask",
        "walls_prev", "walls_gap_min", "range_src", "dropped", "note"]
NOW = pd.Timestamp("2026-11-22 15:00:00")


def _messages() -> list[str]:
    x = trade("2026-11-09", 74777.0, "ema")
    w_open, w_exit = cur("aperto", dist_now=True), cur("uscita")
    ev = [{"type": "w_signal", "w": cur("segnale")}, {"type": "w_signal", "w": w_open},
          {"type": "w_entry", "trade": trade(), "w": w_open}, {"type": "w_info", "w": w_open},
          {"type": "w_trail", "w": w_open, "old": 69000.0}, {"type": "w_dist", "w": w_open},
          {"type": "w_restore", "w": w_open, "last": x}, {"type": "w_exit_next", "w": w_exit},
          {"type": "w_exit", "trade": x, "w": cur("nessuno")},
          {"type": "w_retract", "kind": "signal", "w": cur("nessuno"), "key": "2026-08-23", "side": "long", "why": "x"},
          {"type": "w_retract", "kind": "exit", "w": w_open, "key": "2026-08-23", "side": "long", "why": "x"}]
    out = [weekly.format_event(e) for e in ev]
    out.append(weekly.format_heartbeat(w_open, "2026-11-21", "10:00", [], "2026-11-22"))
    out.append(weekly.format_intraday([{"level": 70000.0, "model": 70000.0, "told": None, "which": "modello",
                                        "side": "long", "last": 69000.0, "time": "10:00 UTC"}]))
    out.append(telegram.today_brief({"preview": PV, "weekly": {"date": "2026-11-17"}}, "2026-11-18"))
    out.append(telegram.today_brief({"preview": dict(PV, position_block=None), "weekly": None}, "2026-11-18"))
    out.append(telegram.today_brief({"weekly": cur("nessuno", regime="neutro")}, "2026-11-18"))
    sent: list[str] = []
    cli.source_alerts({"spot": "timeout"}, {"perp": "2026-11-19"}, {}, NOW, "2026-11-19", send=lambda t: sent.append(t) or 1)
    return out + sent


class TestTestiW32(unittest.TestCase):
    def test_messaggi_solo_w32(self):
        for t in _messages():
            self.assertIsNone(BAD.search(t), t)
        joined = "\n".join(_messages())
        self.assertIn("(W3.2)", joined)
        self.assertIn("<b>W3.2</b>", joined)
        self.assertIn("decide W3.2.", joined)
        self.assertIn("W3.2 valutato sui dati", joined)

    def test_preanalisi_solo_w32(self):
        p = preview.build(_synth(), REPORT)
        self.assertEqual(p["today"]["note"], "Contesto, non segnale: decide W3.2.")
        for it in p["today"]["items"]:
            for k in ("label", "value", "read", "reliability"):
                self.assertIsNone(re.search(r"W3\.1|W2|\bv2\b|\bW3\b(?!\.2)", it[k]), it)


def _csv(rows: list[dict]) -> Path:
    d = Path(tempfile.mkdtemp())
    pd.DataFrame([{c: r.get(c) for c in COLS} for r in rows]).to_csv(d / "book_sentiment.csv", index=False)
    return d / "book_sentiment.csv"


ROW = {"ts": "2026-11-22 14:30:00", "price": 60600.0, "I": 0.1, "L": 0.6, "S": 0.35, "n_src": 6,
       "liq_short_usd": 400000.0, "liq_long_usd": 100000.0, "pulled_bid": 2, "pulled_ask": 1, "filled_bid": 7,
       "filled_ask": 8, "walls_gap_min": 30}


class TestSentiment(unittest.TestCase):
    def _items(self, s):
        return {i["key"]: i for i in s["items"]}

    def test_valori_noti(self):
        s = preview.sentiment(_csv([ROW]), NOW)
        self.assertTrue(s["available"])
        self.assertEqual(s["age_min"], 30)
        it = self._items(s)
        self.assertEqual(it["sentiment"]["value"], "+0,35")
        self.assertIn("pressione al rialzo", it["sentiment"]["read"])
        self.assertIn("30 min fa", it["sentiment"]["read"])
        self.assertEqual(it["sentiment"]["reliability"], preview.SENT_NOTE)
        self.assertEqual(preview.SENT_NOTE, "Contesto descrittivo, non un segnale: nei test (lezione 108) il sentiment "
                                            "non ha anticipato il prezzo a 1, 4 o 24 ore.")
        self.assertEqual(it["sent_i"]["value"], "+0,10")
        self.assertIn("6 fonti", it["sent_i"]["read"])
        self.assertEqual(it["sent_l"]["value"], "+0,60")
        self.assertIn("short liquidati 400.000 $", it["sent_l"]["read"])
        self.assertIn("long liquidati 100.000 $", it["sent_l"]["read"])
        self.assertEqual(it["sent_walls"]["value"], "ritirati bid 2 · ask 1 · eseguiti bid 7 · ask 8")
        for i in s["items"]:   # stesso formato delle altre voci della sezione Oggi: la dashboard le mostra senza modifiche
            self.assertEqual(set(i), {"key", "label", "value", "read", "reliability"})
            self.assertTrue(all(isinstance(v, str) and v for v in i.values()))

    def test_etichette(self):
        for S, lab in ((-0.35, "pressione al ribasso"), (0.1, "neutro"), (-0.2, "neutro")):
            s = preview.sentiment(_csv([dict(ROW, S=S)]), NOW)
            self.assertIn(lab, self._items(s)["sentiment"]["read"])

    def test_L_vuoto(self):
        s = preview.sentiment(_csv([dict(ROW, L=None, S=None, liq_short_usd=279.0, liq_long_usd=18312.0)]), NOW)
        it = self._items(s)
        self.assertEqual(it["sentiment"]["value"], "n.d.")
        self.assertEqual(it["sent_l"]["value"], "vuoto")
        self.assertIn("sotto 250.000 $", it["sent_l"]["read"])
        self.assertIn("long liquidati 18.312 $", it["sent_l"]["read"])

    def test_dato_vecchio(self):
        s = preview.sentiment(_csv([dict(ROW, ts="2026-11-22 11:30:00")]), NOW)   # 3 h 30 min
        self.assertFalse(s["available"])
        self.assertEqual(len(s["items"]), 1)
        self.assertIn("dato non disponibile", s["items"][0]["read"])
        self.assertEqual(s["items"][0]["reliability"], preview.SENT_NOTE)
        self.assertTrue(preview.sentiment(_csv([dict(ROW, ts="2026-11-22 12:10:00")]), NOW)["available"])

    def test_file_mancante(self):
        s = preview.sentiment(Path(tempfile.mkdtemp()) / "book_sentiment.csv", NOW)
        self.assertFalse(s["available"])
        self.assertIn("dato non disponibile", s["items"][0]["read"])

    def test_media_24_ore_e_direzione(self):
        t0 = NOW - pd.Timedelta(hours=48)
        rows = [dict(ROW, ts=str(t0 + pd.Timedelta(hours=k)), S=(-0.1 if k <= 24 else 0.3)) for k in range(1, 49)]
        it = self._items(preview.sentiment(_csv(rows), NOW))
        self.assertEqual(it["sent_ma24"]["value"], "+0,30")
        self.assertIn("in salita", it["sent_ma24"]["read"])
        self.assertIn("−0,10", it["sent_ma24"]["read"])
        rows = [dict(r, S=0.3 - (0.0 if i < 24 else 0.5)) for i, r in enumerate(rows)]
        self.assertIn("in calo", self._items(preview.sentiment(_csv(rows), NOW))["sent_ma24"]["read"])
        few = [dict(r, S=None) for r in rows[:-5]] + rows[-5:]
        ma = self._items(preview.sentiment(_csv(few), NOW))["sent_ma24"]
        self.assertEqual(ma["value"], "n.d.")
        self.assertIn("storico insufficiente", ma["read"])

    def test_nella_preanalisi_senza_effetto_su_w32(self):
        f = _synth()
        base = preview.build(f, dict(REPORT, sentiment={"items": []}))
        rep = dict(REPORT, sentiment=preview.sentiment(_csv([ROW]), NOW))
        p = preview.build(f, rep)
        keys = [i["key"] for i in p["today"]["items"]]
        self.assertEqual(keys[-5:], ["sentiment", "sent_i", "sent_l", "sent_walls", "sent_ma24"])
        self.assertTrue(p["today"]["sentiment"]["available"])
        for k in ("conditions", "scenarios", "if_signal", "position_block", "flow"):
            self.assertEqual(p[k], base[k])


if __name__ == "__main__":
    unittest.main()
