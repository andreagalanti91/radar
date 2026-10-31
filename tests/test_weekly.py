"""Segnale settimanale W2 (radar/weekly.py): numeri storici della ricerca, stato al 30/10/2026, eventi senza duplicati,
tetto di esposizione sugli short, controllo orario del trailing, dashboard."""
import csv
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from radar.data import DATA_DIR

FILES = ["spot_1h", "spot", "perp", "funding", "metrics", "fng", "taker_1h"]
ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in FILES), "dati mancanti")
class TestWeekly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar import weekly
        from radar.data import load_all
        from radar.features import build_features
        cls.wk = weekly
        cls.F = build_features(load_all())
        cls.cur = weekly.evaluate(cls.F[cls.F.index < "2026-10-31"], capital=50000.0)   # dati fino al 30/10/2026

    def test_numeri_storici(self):
        M, H = self.cur["history"]["m1"], self.cur["history"]
        self.assertEqual(M["n"], 19)
        self.assertAlmostEqual(M["per_year"], 3.26, delta=0.05)
        self.assertAlmostEqual(M["win_rate"], 68.4, delta=0.5)
        self.assertAlmostEqual(M["avg_pct"], 13.4, delta=0.3)
        self.assertAlmostEqual(M["worst_pct"], -18.3, delta=0.3)
        self.assertAlmostEqual(M["total_pct"], 617.6, delta=10)
        self.assertAlmostEqual(M["max_dd_pct"], -42.6, delta=0.5)
        self.assertAlmostEqual(M["mar"], 14.50, delta=0.3)
        self.assertAlmostEqual(H["final_10k_1x"], 71761, delta=700)

    def test_trade_come_la_ricerca(self):
        with open(ROOT / "research" / "weekly_w2_sr25_trades.csv", newline="") as fh:
            ref = list(csv.DictReader(fh))
        T = self.cur["history"]["trades"]
        self.assertEqual([(t["entry"], t["side"]) for t in T], [(r["ingresso"], r["lato"]) for r in ref])
        for t, r in zip(T, ref):
            self.assertAlmostEqual(t["entry_px"], float(r["prezzo_ingresso"]), delta=1)
            self.assertAlmostEqual(t["expo"], float(r["esposizione"]), delta=0.01)
            if t["reason"] != "open":
                self.assertEqual(t["reason"], r["motivo"])
                self.assertAlmostEqual(t["pnl_pct"], float(r["pnl_capitale_%"]), delta=0.1)

    def test_stato_30_ottobre(self):
        c = self.cur
        self.assertEqual((c["status"], c["side"], c["entry"], c["market"]), ("aperto", "long", "2026-08-24", "spot"))
        self.assertAlmostEqual(c["entry_px"], 77812, delta=2)
        self.assertEqual(c["expo"], 1.0)
        self.assertTrue(c["stop0"] <= c["trail"] < c["price"])
        self.assertAlmostEqual(c["trail"], c["best"] - 2.5 * c["atr_w"], delta=1)   # trailing dalla miglior chiusura
        self.assertAlmostEqual(c["notional"], 50000, delta=1)

    def test_tetto_short(self):
        wk = self.wk
        for t in self.cur["history"]["trades"]:
            if t["side"] == "short":
                self.assertLessEqual(t["expo"], 1.0)
        self.assertAlmostEqual(wk.exposure(-1, 100.0, 10.0), 1.0)          # stop al 25%: tetto non attivo
        self.assertAlmostEqual(wk.exposure(-1, 100.0, 20.0), 0.5)          # stop al 50%: metà esposizione
        self.assertAlmostEqual(wk.exposure(1, 100.0, 20.0), 1.0)           # i long restano 1x in spot
        p = wk.plan(-1, 100.0, 20.0, 110.0, 10000.0)
        self.assertEqual(p["market"], "perp")
        self.assertAlmostEqual(p["notional"] * p["stop_pct"] / 100, 2500, delta=1)   # 25% del capitale allo stop

    def test_primo_avvio_e_dedupe(self):
        wk = self.wk
        ev, st = wk.diff_events(self.cur, None)
        self.assertEqual([e["type"] for e in ev], ["w_info"])   # il long del 24/08 non è un segnale nuovo
        self.assertIn("Posizione settimanale in corso", wk.format_event(ev[0]))
        ev2, st2 = wk.diff_events(self.cur, st)
        self.assertEqual(ev2, [])
        self.assertEqual(st2["notified"], ["2026-08-23"])

    def test_sequenza_eventi(self):
        """Giro per giro dal 17/08 al 05/09/2026: uscita dello short, segnale long, trailing, nessun duplicato."""
        wk, prev, seen = self.wk, None, []
        for d in pd.date_range("2026-08-17", "2026-09-05"):
            c = wk.evaluate(self.F[self.F.index < d], capital=50000.0)
            for _ in range(2):   # due giri orari con gli stessi dati: il secondo non manda nulla
                ev, prev = wk.diff_events(c, prev)
                seen += [(str(d.date()), e["type"]) for e in ev]
                for e in ev:
                    self.assertIn("RADAR SIGNAL BTC", wk.format_event(e))
            if str(d.date()) == "2026-08-24":
                self.assertEqual(c["status"], "segnale")
                self.assertEqual(c["plan"]["market"], "spot")
                self.assertIn("SEGNALE SETTIMANALE · 🟢 LONG", wk.format_event({"type": "w_signal", "w": c}))
        types = [t for _, t in seen]
        self.assertEqual(types[0], "w_info")                     # primo avvio con lo short aperto
        self.assertIn(("2026-08-21", "w_exit"), seen)            # short chiuso dal trailing il 20/08
        self.assertEqual(types.count("w_signal"), 1)
        self.assertIn(("2026-08-24", "w_signal"), seen)
        self.assertEqual(types.count("w_exit"), 1)
        self.assertEqual(len(seen), len(set(seen)))

    def test_controllo_orario(self):
        wk, c = self.wk, self.cur
        h = pd.DataFrame({"open": [c["price"]], "high": [c["price"]], "low": [c["trail"] - 10], "close": [c["trail"] + 5]})
        ev, keys = wk.check_intraday(c, [], h)
        self.assertEqual(len(ev), 1)
        self.assertIn("stop toccato", wk.format_intraday(ev))
        self.assertEqual(wk.check_intraday(c, keys, h)[0], [])   # una sola allerta per livello
        ok = h.assign(low=c["trail"] + 100)
        self.assertEqual(wk.check_intraday(c, [], ok)[0], [])

    def test_dashboard(self):
        from radar import live, paper
        from radar.dashboard import render
        from radar.telegram import daily_brief
        cut = pd.Timestamp("2026-10-30")
        H = paper.candles_4h()
        report = live.evaluate(self.F[self.F.index < cut], h4=H[H.index < cut], frozen={})
        report["weekly"] = self.cur
        html = render(report, Path(tempfile.mkdtemp()) / "index.html", standalone=False).read_text()
        for k in ('id="wkSec"', 'id="wkStatSec"', "renderWeekly", '"weekly"'):
            self.assertIn(k, html)
        self.assertIn("Settimanale W2", daily_brief(report))
