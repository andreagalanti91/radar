"""Avviso VIX (radar/vix.py): isteresi (Buy sopra 30, riarmo sotto 25; Sell sotto 15, riarmo sopra 17), controllo ogni 4
ore, primo avvio, rete caduta senza invii né cambi di stato, ripiego FRED, HTML di Telegram valido. Rete finta."""
import unittest
from unittest import mock

import pandas as pd

from radar import vix
from test_telegram_formato import LIMIT, check_html

DAY = pd.Timestamp("2026-11-25")


def q(v, closes=(20.0, 21.0, 22.0), live=True):
    idx = pd.bdate_range(end=DAY - pd.Timedelta(days=1), periods=len(closes))
    return {"value": v, "time": DAY + pd.Timedelta(hours=16, minutes=35), "day": DAY, "live": live,
            "closes": pd.Series(list(closes), index=idx), "prev": closes[-1] if closes else None,
            "source": "Yahoo ^VIX" if live else "FRED VIXCLS"}


class Sender:
    def __init__(self, ok=True):
        self.ok, self.texts = ok, []

    def __call__(self, t):
        self.texts.append(t)
        return 123 if self.ok else False


def at(h, day=25):
    return pd.Timestamp(f"2026-11-{day:02d} {h:02d}:07")


def armed(zona="neutra", aa=True, ab=True):
    return {"vix": {"zona": zona, "armato_alto": aa, "armato_basso": ab, "ultimo_check": "2000-01-01T00"}}


class TestIsteresi(unittest.TestCase):
    def run_seq(self, st, values):
        """Un controllo per fascia di 4 ore; restituisce i testi inviati."""
        s = Sender()
        for i, v in enumerate(values):
            vix.update(st, at(4 * (i % 6), 1 + i // 6), send=s, fetch_fn=lambda v=v: q(v))
        return s.texts

    def test_buy_un_solo_avviso_per_attraversamento(self):
        st = armed()
        t = self.run_seq(st, [28, 31, 33, 29, 27, 31, 26, 24.5, 26, 31.5, 35])
        self.assertEqual(len(t), 2)                       # 31 (primo) e 31,5 dopo il ritorno sotto 25
        self.assertTrue(all(x.startswith("🟢 <b>VIX sopra 30 · segnale Buy (paura alta)</b>") for x in t))
        self.assertIn("31,50", t[1])
        self.assertFalse(st["vix"]["armato_alto"])
        self.assertEqual(st["vix"]["zona"], "alta")
        self.assertEqual(st["vix"]["ultimo_avviso"]["tipo"], "buy")

    def test_30_25_30(self):
        st = armed()
        self.assertEqual(len(self.run_seq(st, [31, 25, 31])), 1)     # 25 non è "sotto 25": nessun riarmo
        self.assertEqual(len(self.run_seq(st, [24.9, 31])), 1)

    def test_sell_15_17_15(self):
        st = armed()
        t = self.run_seq(st, [16, 14, 13, 16, 14.5, 17, 14.9, 17.5, 14])
        self.assertEqual(len(t), 2)                       # 14 e 14 dopo il ritorno sopra 17 (17 esatto non riarma)
        self.assertTrue(all(x.startswith("🔴 <b>VIX sotto 15 · segnale Sell (mercato tranquillo)</b>") for x in t))
        self.assertFalse(st["vix"]["armato_basso"])
        self.assertTrue(st["vix"]["armato_alto"])

    def test_invio_fallito_ripropone(self):
        st = armed()
        prima = dict(st["vix"])
        vix.update(st, at(8), send=Sender(ok=False), fetch_fn=lambda: q(32))
        self.assertEqual(st["vix"], prima)                # nessun marcatore: il giro orario dopo riprova
        s = Sender()
        vix.update(st, at(9), send=s, fetch_fn=lambda: q(32))
        self.assertEqual(len(s.texts), 1)
        self.assertEqual(st["vix"]["ultimo_check"], "2026-11-25T08")
        vix.update(st, at(12), send=s, fetch_fn=lambda: q(33))
        self.assertEqual(len(s.texts), 1)


class TestFinestra(unittest.TestCase):
    def test_un_controllo_per_fascia(self):
        st = armed()
        calls = []

        def f():
            calls.append(1)
            return q(20)
        for h in range(24):
            for m in (7, 37):
                vix.update(st, pd.Timestamp(f"2026-11-25 {h:02d}:{m:02d}"), send=Sender(), fetch_fn=f)
        self.assertEqual(len(calls), 6)                    # 00, 04, 08, 12, 16, 20
        self.assertEqual(st["vix"]["ultimo_check"], "2026-11-25T20")

    def test_fasce(self):
        self.assertEqual(vix.slot(pd.Timestamp("2026-11-25 03:59")), "2026-11-25T00")
        self.assertEqual(vix.slot(pd.Timestamp("2026-11-25 04:07")), "2026-11-25T04")
        self.assertEqual(vix.slot(pd.Timestamp("2026-11-25 23:37", tz="UTC")), "2026-11-25T20")
        self.assertEqual(vix.slot(pd.Timestamp("2026-11-25 01:00", tz="Europe/Rome")), "2026-11-25T00")

    def test_fascia_controllata_niente_rete(self):
        st = armed()
        st["vix"]["ultimo_check"] = "2026-11-25T16"
        f = mock.Mock(side_effect=AssertionError("rete chiamata"))
        self.assertEqual(vix.giro(st, at(17), f), [])
        self.assertEqual(vix.giro(st, at(19), f), [])
        f.assert_not_called()


class TestPrimoAvvio(unittest.TestCase):
    def first(self, v, closes):
        st, s = {}, Sender()
        vix.update(st, at(16), send=s, fetch_fn=lambda: q(v, closes))
        self.assertEqual(len(s.texts), 1)
        return st["vix"], s.texts[0]

    def test_sopra_30(self):
        v, t = self.first(33.54, (35.89, 26.62, 26.36))
        self.assertTrue(t.startswith("📊 <b>VIX 33,54 · condizione di mercato: paura alta</b>"))
        self.assertIn("Sopra 30 da oggi (25/11)", t)
        self.assertIn("episodio precedente", t)
        self.assertIn("ti avviso quando supera 30 o scende sotto 15, controllo ogni 4 ore".lower(), t.lower())
        self.assertEqual((v["zona"], v["armato_alto"], v["armato_basso"]), ("alta", False, True))
        s = Sender()   # nessun Buy finché non torna sotto 25
        vix.update({"vix": v}, at(20), send=s, fetch_fn=lambda: q(36))
        self.assertEqual(s.texts, [])

    def test_neutra(self):
        v, t = self.first(22.0, (35.0, 31.0, 20.0, 21.0))
        self.assertIn("condizione di mercato: normale", t)
        self.assertIn("ultima chiusura sopra 30", t)
        self.assertEqual((v["zona"], v["armato_alto"], v["armato_basso"]), ("neutra", True, True))

    def test_sotto_15(self):
        v, t = self.first(13.4, (16.0, 14.0, 13.8))
        self.assertIn("condizione di mercato: tranquillo", t)
        self.assertRegex(t, r"Sotto 15 dal \d\d/11")
        self.assertEqual((v["zona"], v["armato_alto"], v["armato_basso"]), ("bassa", True, False))

    def test_primo_invio_fallito(self):
        st = {}
        vix.update(st, at(16), send=Sender(ok=False), fetch_fn=lambda: q(20))
        self.assertNotIn("vix", st)


class TestRete(unittest.TestCase):
    def test_errore_di_rete(self):
        for st in ({}, armed()):
            prima = {k: dict(v) for k, v in st.items()}
            s = Sender()
            with mock.patch("radar.vix.requests.get", side_effect=vix.requests.ConnectionError("giù")):
                with self.assertRaises(Exception):
                    vix.update(st, at(8), send=s)
            self.assertEqual(s.texts, [])
            self.assertEqual(st, prima)

    def test_ripiego_fred(self):
        csv = "observation_date,VIXCLS\n2026-11-20,35.89\n2026-11-23,26.62\n2026-11-24,.\n2026-11-25,31.2\n"

        def get(url, **k):
            if "yahoo" in url:
                raise vix.requests.ConnectionError("yahoo giù")
            r = mock.Mock(text=csv)
            r.raise_for_status = lambda: None
            return r
        with mock.patch("radar.vix.requests.get", side_effect=get):
            d = vix.fetch()
        self.assertEqual((d["source"], d["value"], d["prev"], d["live"]), ("FRED VIXCLS", 31.2, 26.62, False))
        t = vix.format_buy(d)
        self.assertIn("chiusura del 25/11", t)
        self.assertIn("FRED VIXCLS", t)

    def test_yahoo(self):
        body = {"chart": {"result": [{"meta": {"regularMarketPrice": 33.54, "regularMarketTime": 1795624441,
                                               "gmtoffset": -21600},
                                      "timestamp": [1795413600, 1795500000, 1795586400],
                                      "indicators": {"quote": [{"close": [26.62, 26.36, 33.5]}]}}]}}
        r = mock.Mock(json=lambda: body)
        r.raise_for_status = lambda: None
        with mock.patch("radar.vix.requests.get", return_value=r):
            d = vix.fetch()
        self.assertEqual((d["source"], d["value"], d["prev"], d["live"]), ("Yahoo ^VIX", 33.54, 26.36, True))
        self.assertEqual(len(d["closes"]), 2)              # la barra del giorno non è una chiusura


class TestFormato(unittest.TestCase):
    def test_html_e_lunghezza(self):
        cases = [vix.format_buy(q(31.2)), vix.format_sell(q(14.1, (16, 15.5, 15.2))), vix.format_first(q(22.0)),
                 vix.format_first(q(33.5, (35.89, 26.62, 26.36))), vix.format_first(q(13.0, (), live=False)),
                 vix.format_buy(q(31.0, live=False))]
        for t in cases:
            errs, text = check_html(t)
            self.assertEqual(errs, [], t)
            self.assertLess(len(t), LIMIT)
            self.assertLessEqual(len(text.split("\n")[0]), 80)
            self.assertIn("non un segnale di W3.2", text)

    def test_testi_dati(self):
        _, b = check_html(vix.format_buy(q(31.2)))
        self.assertIn("Storico S&P 500: +5,5% mediano a 90 giorni (giorno qualsiasi +3,1%); su BTC misto.", b)
        self.assertIn("Condizione di mercato, non un segnale di W3.2.", b)
        self.assertIn("oggi +9,20 punti", b)
        _, s = check_html(vix.format_sell(q(14.1)))
        self.assertIn("Storicamente dopo un VIX sotto 15 le azioni hanno continuato a salire (+6,2% mediano a 180 "
                      "giorni): segnale debole.", s)


if __name__ == "__main__":
    unittest.main()
