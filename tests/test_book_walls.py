"""Registro dei muri del book (radar/orderbook.book_walls, update_walls, settle_walls: esito dei muri del giro
precedente) e fonte del funding. Niente rete."""
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
            first = df[df["ts"] == "2026-11-22 10:07:00"]
            self.assertEqual(set(first["outcome"]), {"presente"})       # book identico un'ora dopo: muri ancora lì
            self.assertEqual(set(first["out_min"]), {60})
            self.assertTrue(df[df["ts"] == "2026-11-22 11:07:00"]["outcome"].isna().all())   # ultimo giro: esito al prossimo


def wall_book(mid=60000.0, bid_wall=None, ask_wall=None):
    """Book uniforme (0,1 BTC ogni dollaro, ±4000 $) con un muro da 50 BTC a un prezzo per lato."""
    b, a = book(mid)
    if bid_wall:
        b.append((bid_wall, 50.0))
    if ask_wall:
        a.append((ask_wall, 50.0))
    return sorted(b, key=lambda x: -x[0]), sorted(a, key=lambda x: x[0])


class TestWallOutcome(unittest.TestCase):
    """Esito dei muri del giro precedente (settle_walls, update_walls): eseguito / ritirato / presente e casi dubbi."""
    T0, T1 = pd.Timestamp("2026-11-22 10:02"), pd.Timestamp("2026-11-22 11:02")

    def run2(self, after, rng, tmp=None, before=None):
        with tempfile.TemporaryDirectory() as d:
            d = Path(tmp or d)
            ob.update_walls(d, {"okx_spot": before or wall_book(bid_wall=59410.0, ask_wall=60610.0)}, self.T0)
            _, summ = ob.update_walls(d, after, self.T1, range_fn=(lambda a, b: rng) if rng else None)
            df = pd.read_csv(d / "book_walls.csv")
            prev = df[df["ts"] == str(self.T0)]
            return {(r.side, r.price): r for r in prev.itertuples()}, summ, df

    def test_presente(self):
        o, summ, _ = self.run2({"okx_spot": wall_book(bid_wall=59410.0, ask_wall=60610.0)},
                               {"low": 59990.0, "high": 60010.0, "close": 60000.0, "src": "binance_spot_1m"})
        self.assertEqual(o[("bid", 59425.0)].outcome, "presente")
        self.assertEqual(o[("ask", 60625.0)].outcome, "presente")
        self.assertAlmostEqual(o[("bid", 59425.0)].remain_pct, 100.0, places=0)
        self.assertEqual(o[("bid", 59425.0)].range_src, "binance_spot_1m")
        self.assertEqual(summ["counts"]["bid"]["presente"], 3)
        self.assertEqual((summ["n"], summ["gap_min"]), (6, 60))

    def test_ritirato(self):
        # il muro in acquisto sparisce (resta la liquidità di fondo: ~10%) e il prezzo non è mai sceso fin lì
        o, summ, _ = self.run2({"okx_spot": wall_book(ask_wall=60610.0)}, {"low": 59800.0, "high": 60100.0, "close": 60000.0, "src": "x"})
        r = o[("bid", 59425.0)]
        self.assertEqual(r.outcome, "ritirato")
        self.assertLess(r.remain_pct, 30)
        self.assertEqual(o[("ask", 60625.0)].outcome, "presente")
        self.assertEqual((summ["counts"]["bid"]["ritirato"], summ["counts"]["ask"]["ritirato"]), (1, 0))

    def test_eseguito(self):
        # il minimo dell'intervallo attraversa la fascia 59400–59450, poi il prezzo torna su: muro eseguito anche se rimesso
        o, summ, _ = self.run2({"okx_spot": wall_book(bid_wall=59410.0, ask_wall=60610.0)},
                               {"low": 59390.0, "high": 60700.0, "close": 60000.0, "src": "x"})
        self.assertEqual(o[("bid", 59425.0)].outcome, "eseguito")
        self.assertEqual(o[("ask", 60625.0)].outcome, "eseguito")
        self.assertEqual(o[("bid", 59425.0)].px_low, 59390.0)
        self.assertEqual((summ["counts"]["bid"]["eseguito"], summ["counts"]["ask"]["eseguito"]), (3, 1))   # in acquisto anche le fasce a ridosso del prezzo

    def test_incerto_toccato_e_sparito(self):
        # il prezzo entra nella fascia (59430) senza attraversarla e il muro non c'è più: non si distingue eseguito da tolto
        o, _, _ = self.run2({"okx_spot": wall_book(ask_wall=60610.0)}, {"low": 59430.0, "high": 60100.0, "close": 60000.0, "src": "x"})
        self.assertEqual(o[("bid", 59425.0)].outcome, "incerto")

    def test_base_fra_fonte_e_candele(self):
        # candele di una borsa che quota 30 $ sopra la fonte: il minimo 59470 riportato sulla fonte è 59440 → fascia toccata
        o, _, _ = self.run2({"okx_spot": wall_book(ask_wall=60610.0)}, {"low": 59470.0, "high": 60100.0, "close": 60030.0, "src": "x"})
        self.assertEqual(o[("bid", 59425.0)].outcome, "incerto")
        self.assertAlmostEqual(o[("bid", 59425.0)].px_low, 59470.0 * 60000.0 / 60030.0, places=0)

    def test_fonte_sparita_e_senza_candele(self):
        # la fonte del muro in questo giro non risponde: senza attraversamento l'esito non è verificabile (mai inventato)
        o, summ, df = self.run2({"coinbase": book()}, {"low": 59990.0, "high": 60010.0, "close": 60000.0, "src": "x"})
        self.assertEqual({r.outcome for r in o.values()}, {"non_verificabile"})
        self.assertEqual(set(df[df["ts"] == str(self.T1)]["exchange"]), {"coinbase"})   # il giro continua con le altre fonti
        o, _, _ = self.run2({"coinbase": book()}, {"low": 59000.0, "high": 60100.0, "close": 60000.0, "src": "x"})
        self.assertEqual(o[("bid", 59425.0)].outcome, "eseguito")                        # l'attraversamento non richiede il book
        # nessuna candela: restano solo i prezzi delle due foto, e si dichiara
        o, _, _ = self.run2({"okx_spot": wall_book(ask_wall=60610.0)}, None)
        self.assertEqual((o[("bid", 59425.0)].outcome, o[("bid", 59425.0)].range_src), ("ritirato", "solo_foto"))

    def test_book_che_non_arriva_al_muro(self):
        short = book(n=300)                                   # adesso il book copre solo ±300 $
        o, _, _ = self.run2({"okx_spot": short}, {"low": 59800.0, "high": 60100.0, "close": 60000.0, "src": "x"})
        self.assertEqual(o[("bid", 59425.0)].outcome, "non_verificabile")

    def test_candele_che_falliscono(self):
        def boom(a, b):
            raise RuntimeError("rete")
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            bk = {"okx_spot": wall_book(bid_wall=59410.0)}
            ob.update_walls(d, bk, self.T0)
            _, summ = ob.update_walls(d, bk, self.T1, range_fn=boom)
            self.assertEqual(summ["range_src"], "solo_foto")
            self.assertEqual(summ["counts"]["bid"]["presente"], 3)

    def test_idempotenza_e_giro_vecchio(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            bk = {"okx_spot": wall_book(bid_wall=59410.0)}
            ob.update_walls(d, bk, self.T0)
            one = (d / "book_walls.csv").read_bytes()
            rows, summ = ob.update_walls(d, bk, self.T0)                       # stesso istante: nulla di nuovo
            self.assertEqual((len(rows), summ), (6, None))
            ob.update_walls(d, {"okx_spot": wall_book()}, self.T0 + pd.Timedelta(minutes=5))
            self.assertEqual((d / "book_walls.csv").read_bytes(), one)         # né righe né esiti dal giro doppio
            ob.update_walls(d, bk, self.T1)
            two = (d / "book_walls.csv").read_bytes()
            ob.update_walls(d, bk, self.T1)
            self.assertEqual((d / "book_walls.csv").read_bytes(), two)
            self.assertTrue(two.startswith(one.split(b"\n")[0]))              # intestazione invariata
            _, summ = ob.update_walls(d, bk, self.T1 + pd.Timedelta(hours=9))  # giro precedente troppo vecchio: scaduto
            df = pd.read_csv(d / "book_walls.csv")
            self.assertEqual(set(df[df["ts"] == str(self.T1)]["outcome"]), {"scaduto"})
            self.assertEqual(set(df[df["ts"] == str(self.T0)]["outcome"]), {"presente"})   # esiti già scritti: mai riscritti
            self.assertEqual(len(df), 18)

    def test_file_vuoto_vecchio_schema_e_corrotto(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / "book_walls.csv"
            bk = {"okx_spot": wall_book(bid_wall=59410.0)}
            p.write_text("")                                                   # file vuoto: si riparte con l'intestazione
            ob.update_walls(d, bk, self.T0)
            self.assertEqual(list(pd.read_csv(p).columns), ob.WALL_COLS)
            # schema vecchio (8 colonne, come il registro partito il 22/11/2026): le righe restano identiche e ricevono l'esito
            old = pd.read_csv(p)[ob.WALL_BASE]
            old.to_csv(p, index=False)
            before = p.read_text().splitlines()[1:]
            ob.update_walls(d, bk, self.T1)
            df = pd.read_csv(p)
            self.assertEqual(list(df.columns), ob.WALL_COLS)
            self.assertEqual(len(df), 12)
            self.assertEqual(set(df["outcome"].dropna()), {"presente"})
            after = p.read_text().splitlines()[1:7]
            self.assertTrue(all(a.startswith(b + ",") for a, b in zip(after, before)))
            p.write_text("non,un,registro\n1,2,3\n")                         # illeggibile: messo da parte, non perso
            ob.update_walls(d, bk, self.T1 + pd.Timedelta(hours=1))
            self.assertTrue((d / "book_walls.csv.illeggibile").exists())
            self.assertEqual(len(pd.read_csv(p)), 6)

    def test_nessuna_fonte_valida(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self.assertEqual(ob.update_walls(d, {}, self.T0), ([], None))
            self.assertFalse((d / "book_walls.csv").exists())                  # nessun dato: nessun file inventato


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
