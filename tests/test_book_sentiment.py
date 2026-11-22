"""Registro del sentiment del book (radar/orderbook: imbalance, liq_imbalance, sentiment_row, log_sentiment), fonti del book
che falliscono (snapshot), book composto di Hyperliquid (hl_merge) e minimo/massimo dalle candele (price_range). Niente rete."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from radar import orderbook as ob

NOW = pd.Timestamp("2026-11-22 11:02:00")
NOW_MS = int(NOW.timestamp() * 1000)


def book(mid=60000.0, n=1000, tick=1.0, bq=0.1, aq=0.1):
    return [(mid - 0.5 - i * tick, bq) for i in range(n)], [(mid + 0.5 + i * tick, aq) for i in range(n)]


def flat(mid, bid_usd, ask_usd, far=0.02):
    """Book con tutto il denaro a ±0,5% dal mid e un livello minuscolo a ±far (copertura)."""
    return ([(mid - 0.5, 1e-9), (mid * 0.995, bid_usd / (mid * 0.995)), (mid * (1 - far), 1e-9)],
            [(mid + 0.5, 1e-9), (mid * 1.005, ask_usd / (mid * 1.005)), (mid * (1 + far), 1e-9)])


def ev(minutes_ago, side, usd, ex="okx"):
    return {"ts": NOW_MS - int(minutes_ago * 60_000), "exchange": ex, "id": f"{minutes_ago}-{side}-{usd}", "side": side,
            "price": 60000.0, "btc": usd / 60000.0, "usd": float(usd)}


class TestImbalance(unittest.TestCase):
    def test_i_valori_noti(self):
        r = ob.imbalance({"a": flat(60000, 3e6, 1e6), "b": flat(60050, 1e6, 1e6)})
        self.assertAlmostEqual(r["bid_usd"], 4e6, delta=1)
        self.assertAlmostEqual(r["ask_usd"], 2e6, delta=1)
        self.assertAlmostEqual(r["I"], (4 - 2) / (4 + 2), places=6)
        self.assertEqual(r["sources"], ["a", "b"])

    def test_solo_entro_la_fascia_e_fonti_corte(self):
        b, a = flat(60000, 1e6, 1e6)
        b.insert(2, (60000 * 0.985, 100.0))                       # 5,9 M$ a −1,5%: fuori da ±1%, non conta
        self.assertAlmostEqual(ob.imbalance({"a": (b, a)})["I"], 0.0, places=6)
        r = ob.imbalance({"a": flat(60000, 3e6, 1e6), "corta": flat(60000, 9e6, 1e6, far=0.006)})
        self.assertEqual((r["sources"], r["short"]), (["a"], ["corta"]))   # copre solo ±0,6%: esclusa e dichiarata
        self.assertAlmostEqual(r["I"], 0.5, places=6)
        self.assertIsNone(ob.imbalance({})["I"])
        self.assertIsNone(ob.imbalance({"corta": flat(60000, 1, 1, far=0.006)})["I"])

    def test_l_valori_noti(self):
        evs = [ev(5, "short", 300_000), ev(29, "long", 100_000, "gate"), ev(31, "long", 9e6), ev(-1, "long", 9e6)]
        r = ob.liq_imbalance(evs, NOW_MS)
        self.assertEqual((r["short_usd"], r["long_usd"], r["n"], r["exchanges"]), (300_000, 100_000, 2, ["gate", "okx"]))
        self.assertAlmostEqual(r["L"], 0.5)
        self.assertEqual(ob.liq_imbalance([], NOW_MS)["L"], 0.0)                       # nessuna liquidazione: 0
        self.assertEqual(ob.liq_imbalance([ev(40, "long", 1e6)], NOW_MS)["L"], 0.0)
        self.assertEqual(ob.liq_imbalance([ev(1, "long", 1e6)], NOW_MS)["L"], -1.0)

    def test_riga_s(self):
        books = {"a": flat(60000, 3e6, 1e6), "b": flat(60100, 1e6, 1e6)}
        liq = {"events": [ev(5, "short", 100_000), ev(6, "long", 300_000)], "sources": ["gate", "okx"], "age_min": 0.4}
        out = {"n": 12, "gap_min": 60, "range_src": "binance_spot_1m",
               "counts": {"bid": {**{o: 0 for o in ob.OUTCOMES}, "ritirato": 2, "presente": 3, "eseguito": 1},
                          "ask": {**{o: 0 for o in ob.OUTCOMES}, "eseguito": 4, "incerto": 2}}}
        r = ob.sentiment_row(NOW, books, liq, out, dropped=["kraken"])
        self.assertEqual(list(r), ob.SENT_COLS)
        self.assertEqual((r["I"], r["L"]), (0.3333, -0.5))
        self.assertAlmostEqual(r["S"], 0.5 * 0.3333 + 0.5 * -0.5, places=4)
        self.assertEqual((r["price"], r["n_src"], r["sources"]), (60050.0, 2, "a+b"))
        self.assertEqual((r["pulled_bid"], r["pulled_ask"], r["filled_bid"], r["filled_ask"], r["still_bid"], r["still_ask"]), (2, 0, 1, 4, 3, 0))
        self.assertEqual((r["walls_prev"], r["walls_gap_min"], r["liq_src"], r["dropped"], r["note"]), (12, 60, "gate+okx", "kraken", ""))

    def test_riga_dati_mancanti(self):
        # liquidazioni non aggiornate: L e S vuoti (non 0); nessun esito valutato: conteggi vuoti (non 0)
        r = ob.sentiment_row(NOW, {"a": flat(60000, 3e6, 1e6)}, {"events": None, "sources": [], "age_min": 300}, None)
        self.assertEqual((r["I"], r["L"], r["S"], r["pulled_bid"], r["liq_age_min"]), (0.5, None, None, None, 300))
        self.assertIn("liquidazioni non aggiornate", r["note"])
        # nessuna liquidazione in 30 minuti con fonte aggiornata: L = 0 e S = 0,5·I
        r = ob.sentiment_row(NOW, {"a": flat(60000, 3e6, 1e6)}, {"events": [], "sources": ["okx"], "age_min": 1}, None)
        self.assertEqual((r["L"], r["S"], r["liq_n"]), (0.0, 0.25, 0))
        # nessun book: I e S vuoti, la riga resta
        r = ob.sentiment_row(NOW, {}, {"events": [], "sources": ["okx"], "age_min": 1}, None)
        self.assertEqual((r["price"], r["I"], r["S"], r["n_src"], r["L"]), (None, None, None, 0, 0.0))


class TestSentimentFile(unittest.TestCase):
    LIQ = {"events": [ev(5, "short", 300_000), ev(6, "long", 100_000)], "sources": ["okx"], "age_min": 0.5}

    def test_file_inesistente_vuoto_idempotenza(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / "book_sentiment.csv"
            books = {"a": flat(60000, 3e6, 1e6)}
            r = ob.log_sentiment(d, NOW, books, liq=self.LIQ)                  # file inesistente
            self.assertEqual((r["I"], r["L"], r["S"]), (0.5, 0.5, 0.5))
            one = p.read_bytes()
            self.assertIsNone(ob.log_sentiment(d, NOW, books, liq=self.LIQ))   # stesso istante: niente doppioni
            self.assertIsNone(ob.log_sentiment(d, NOW + pd.Timedelta(minutes=10), books, liq=self.LIQ))
            self.assertEqual(p.read_bytes(), one)
            ob.log_sentiment(d, NOW + pd.Timedelta(hours=1), {}, liq={"events": None, "sources": [], "age_min": None},
                             checks={"a": ["non raggiungibile (ConnectionError)"]})
            df = pd.read_csv(p)
            self.assertEqual(list(df.columns), ob.SENT_COLS)
            self.assertEqual(len(df), 2)
            self.assertTrue(p.read_bytes().startswith(one))                    # sola aggiunta: le righe vecchie non cambiano
            self.assertTrue(pd.isna(df["S"].iloc[1]) and pd.isna(df["I"].iloc[1]) and df["n_src"].iloc[1] == 0)
            self.assertEqual(df["dropped"].iloc[1], "a")
            p.write_text("")                                                   # file vuoto
            ob.log_sentiment(d, NOW, books, liq=self.LIQ)
            self.assertEqual(len(pd.read_csv(p)), 1)

    def test_hyperliquid_grosso_e_liquidazioni_dai_file(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "liq_events").mkdir()
            run = (NOW - pd.Timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
            (d / "liq_events" / "coverage.csv").write_text(f"run,exchange,stato,scaricati,nuovi,nota\n{run},okx,ok,2,2,\n{run},gate,errore,0,0,x\n")
            (d / "liq_events" / "2026-11.csv").write_text("ts,exchange,id,side,price,btc,usd\n"
                                                          f"{NOW_MS - 600_000},okx,a,short,60000,1,60000\n{NOW_MS - 7_200_000},okx,b,long,60000,9,540000\n")
            fine = flat(60000, 1e6, 1e6, far=0.003)                            # book fine: solo ±0,3% → fuori da I
            r = ob.log_sentiment(d, NOW, {"hyperliquid": fine}, extra={"hyperliquid": {"coarse": flat(60000, 1e6, 3e6)}})
            self.assertEqual((r["I"], r["sources"], r["L"], r["liq_src"], r["liq_n"], r["S"]), (-0.5, "hyperliquid", 1.0, "okx", 1, 0.25))
            # raccolta delle liquidazioni vecchia di 3 ore: L non si inventa
            old = ob.load_liq(d, NOW + pd.Timedelta(hours=3))
            self.assertIsNone(old["events"])
            self.assertIsNone(ob.load_liq(Path(d) / "manca", NOW)["events"])


class TestSources(unittest.TestCase):
    def test_fonte_che_fallisce(self):
        def rotta():
            raise ConnectionError("451")
        now = time.time()
        b, a = book(60000.0)
        srcs = {"buona": lambda: (b, a, now), "altra": lambda: (*book(60010.0), None, {"coarse": book(60010.0)}),
                "rotta": rotta, "vuota": lambda: ([], [], now), "vecchia": lambda: (b, a, now - 3600), "lontana": lambda: (*book(61000.0), now)}
        good, checks, extra = ob.snapshot(srcs)
        self.assertEqual(set(good), {"buona", "altra"})                        # le fonti sane passano comunque
        self.assertEqual(checks["rotta"], ["non raggiungibile (ConnectionError)"])
        self.assertTrue(checks["vuota"] and any("vecchi" in e for e in checks["vecchia"]) and any("consenso" in e for e in checks["lontana"]))
        self.assertEqual((checks["buona"], list(extra)), ([], ["altra"]))

    def test_giro_con_fonti_rotte(self):
        # tutte le fonti del book giù: update() non solleva, non scrive muri, lascia una riga di sentiment senza I
        def rotta():
            raise TimeoutError()
        with tempfile.TemporaryDirectory() as d, mock.patch.object(ob, "SOURCES", {"x": rotta, "y": rotta}), \
                mock.patch.object(ob, "price_range", lambda *a, **k: None):
            d = Path(d)
            out = ob.update(d, NOW)
            self.assertFalse((d / "book_walls.csv").exists())
            df = pd.read_csv(d / "book_sentiment.csv")
            self.assertEqual((len(df), df["n_src"].iloc[0], df["dropped"].iloc[0]), (1, 0, "x+y"))
            self.assertTrue(pd.isna(df["I"].iloc[0]) and pd.isna(df["S"].iloc[0]))
            self.assertEqual(out["wall_outcomes"], None)

    def test_giro_completo_senza_rete(self):
        now = time.time()
        srcs = {"a": lambda: (*book(60000.0, 3000), now), "b": lambda: (*book(60005.0, 3000, bq=0.3), now),
                "rotta": lambda: (_ for _ in ()).throw(ConnectionError())}
        rng = {"low": 59995.0, "high": 60005.0, "close": 60000.0, "src": "finta_1m"}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(ob, "SOURCES", srcs), mock.patch.object(ob, "price_range", lambda *a, **k: rng):
            d = Path(d)
            ob.update(d, NOW)
            ob.update(d, NOW)                                                  # giro doppio: nessun doppione in nessun registro
            out = ob.update(d, NOW + pd.Timedelta(hours=1))
            w, s, o = pd.read_csv(d / "book_walls.csv"), pd.read_csv(d / "book_sentiment.csv"), pd.read_csv(d / "orderbook.csv")
            self.assertEqual((len(w), len(s), len(o)), (24, 2, 2))
            self.assertEqual(set(w["outcome"].dropna()), {"presente"})
            self.assertEqual((s["still_bid"].iloc[1], s["still_ask"].iloc[1], s["walls_prev"].iloc[1], s["range_src"].iloc[1]), (6, 6, 12, "finta_1m"))
            self.assertAlmostEqual(s["I"].iloc[1], (0.4 - 0.2) / (0.4 + 0.2), places=2)
            self.assertEqual(s["dropped"].iloc[1], "rotta")
            self.assertTrue(pd.isna(s["L"].iloc[1]) and pd.isna(s["S"].iloc[1]))   # nessun file di liquidazioni: L non inventato
            self.assertEqual(out["sentiment"]["n_src"], 2)

    def test_fonti_solo_registro_fuori_dalla_foto(self):
        # Hyperliquid entra nei registri (muri, sentiment) ma non nella foto/modello: la serie di orderbook.csv non cambia
        now = time.time()
        fine = book(60002.0, 190)                                              # ±0,3%
        srcs = {"a": lambda: (*book(60000.0, 3000), now), "b": lambda: (*book(60005.0, 3000), now),
                "hyperliquid": lambda: (*fine, now, {"coarse": book(60002.0, 3000, bq=0.5)})}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(ob, "SOURCES", srcs), mock.patch.object(ob, "price_range", lambda *a, **k: None):
            d = Path(d)
            ob.update(d, NOW)
            o, w, s = pd.read_csv(d / "orderbook.csv"), pd.read_csv(d / "book_walls.csv"), pd.read_csv(d / "book_sentiment.csv")
            self.assertEqual((o["sources"].iloc[0], o["n_src"].iloc[0]), ("a,b", 2))
            self.assertEqual(set(w["exchange"]), {"a", "b", "hyperliquid"})
            self.assertEqual((s["sources"].iloc[0], s["n_src"].iloc[0]), ("a+b+hyperliquid", 3))
            self.assertGreater(s["I"].iloc[0], 0.2)                            # il book grosso di Hyperliquid pesa in I


class TestHyperliquid(unittest.TestCase):
    def test_passo(self):
        self.assertEqual((ob.hl_step(60738.0, 5), ob.hl_step(60738.0, 4), ob.hl_step(60738.0, 3), ob.hl_step(104000.0, 4)), (1, 10, 100, 100))

    def test_unione_acquisto(self):
        fine = [(60738.0, 1.0), (60731.0, 2.0), (60719.0, 3.0)]                 # livelli veri fino a 60719
        mid_ = [(60730.0, 3.0), (60710.0, 7.0), (60700.0, 5.0)]                 # passi da 10 $: [P, P+10)
        out = ob.hl_merge([(fine, 1.0), (mid_, 10.0)], "bid")
        # 60730: tutta coperta → saltata; 60710: a cavallo, 7 − 3 (il 60719) = 4; 60700: tutta nuova
        self.assertEqual(out, [(60738.0, 1.0), (60731.0, 2.0), (60719.0, 3.0), (60710.0, 4.0), (60700.0, 5.0)])
        self.assertAlmostEqual(sum(q for _, q in out), 1 + 2 + 7 + 5)           # nessun doppio conteggio

    def test_unione_vendita(self):
        fine = [(60739.0, 1.0), (60745.0, 2.0)]
        mid_ = [(60740.0, 1.0), (60750.0, 6.0), (60760.0, 5.0)]                 # passi da 10 $: (P−10, P]
        out = ob.hl_merge([(fine, 1.0), (mid_, 10.0)], "ask")
        self.assertEqual(out, [(60739.0, 1.0), (60745.0, 2.0), (60750.0, 4.0), (60760.0, 5.0)])
        self.assertEqual(ob.hl_merge([([], 1.0), (mid_, 10.0)], "ask"), mid_)


class TestRange(unittest.TestCase):
    A, B = 1_000_000_000_000, 1_000_000_000_000 + 60 * 60_000

    def candles(self, n=61, low=59900.0, high=60100.0):
        return [(self.A + i * 60_000, high if i == 30 else 60010.0, low if i == 10 else 59990.0, 60000.0 + i / 10) for i in range(n)]

    def test_candele(self):
        r = ob.range_from_candles(self.candles() + [(self.A - 600_000, 70000.0, 50000.0, 60000.0)], self.A, self.B)
        self.assertEqual((r["low"], r["high"], r["close"], r["n"]), (59900.0, 60100.0, 60006.0, 61))   # fuori intervallo: ignorate
        self.assertIsNone(ob.range_from_candles([], self.A, self.B))
        self.assertIsNone(ob.range_from_candles(self.candles(20), self.A, self.B))                       # copre un terzo: incompleto
        self.assertIsNone(ob.range_from_candles([(self.A, 100.0, 200.0, 150.0)], self.A, self.A + 60_000))   # high < low

    def test_riserve(self):
        a, b = pd.Timestamp(self.A, unit="ms"), pd.Timestamp(self.B, unit="ms")

        def rotta(*_):
            raise ConnectionError()
        r = ob.price_range(a, b, sources={"prima": rotta, "corta": lambda *_: self.candles(5), "terza": lambda *_: self.candles()})
        self.assertEqual((r["src"], r["low"]), ("terza_1m", 59900.0))
        self.assertIsNone(ob.price_range(a, b, sources={"prima": rotta}))
        with tempfile.TemporaryDirectory() as d:                               # ultima riserva: candele orarie locali, marcate
            d = Path(d)
            t = pd.date_range(a.floor("h") - pd.Timedelta(hours=3), periods=6, freq="h")
            pd.DataFrame({"t": t.astype(str), "open": 60000.0, "high": 60300.0, "low": 59700.0, "close": 60050.0}).to_csv(d / "spot_1h.csv", index=False)
            r = ob.price_range(a, b, data_dir=d, sources={"prima": rotta})
            self.assertEqual((r["src"], r["low"], r["high"]), ("spot_1h_locale_largo", 59700.0, 60300.0))


if __name__ == "__main__":
    unittest.main()
