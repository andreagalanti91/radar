"""Segnali reali v2 (radar/live.py): stato su dati storici tagliati, eventi, numeri storici, messaggi Telegram."""
import os
import unittest

import pandas as pd

from radar.data import DATA_DIR

FILES = ["spot_1h", "spot", "perp", "funding", "metrics", "fng", "taker_1h"]
CUTS = ["2026-08-19 23:00", "2026-08-20 08:00", "2026-08-20 12:00", "2026-08-20 16:00", "2026-08-21 04:00"]


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in FILES), "dati mancanti")
class TestLiveV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar import live, paper
        from radar.data import load_all
        from radar.features import build_features
        F, H = build_features(load_all()), paper.candles_4h()
        cls.live = live
        cls.reports = []
        for c in CUTS:   # il trade long del 19/08/2026 visto ora per ora (dati come li avrebbe visti il bot)
            T = pd.Timestamp(c)
            cls.reports.append(live.evaluate(F[F.index < T.normalize()], h4=H[H.index + pd.Timedelta(hours=4) <= T], frozen={}))
        cut = pd.Timestamp("2026-10-30")
        cls.full = live.evaluate(F[F.index < cut], h4=H[H.index < cut], frozen={})

    def test_stati(self):
        st = [r["v2"]["status"] for r in self.reports]
        self.assertEqual(st, ["nessuno", "conferma", "ingresso", "aperto", "nessuno"])
        c, i, a = (self.reports[k]["v2"] for k in (1, 2, 3))
        self.assertEqual(c["signal_date"], "2026-08-19")
        self.assertEqual(c["deadline"], "2026-08-23 00:00:00")   # 72h dalla mezzanotte dopo il segnale
        self.assertLess(c["plan"]["risk_lo"], c["plan"]["risk_hi"])
        # ingresso: rischio noto, leva = rischio / distanza dello stop, stop 1 ATR sotto l'ingresso
        p = i["plan"]
        self.assertAlmostEqual(p["lev"], min(5, p["risk"] / p["stop_pct"]), delta=0.02)
        self.assertAlmostEqual(p["entry"] - p["stop"], i["atr"], delta=1)
        self.assertGreater(p["tp_full"], p["entry"] - 0.5 * i["atr"])
        self.assertEqual(a["fills"], 2)
        self.assertEqual(a["risk"], i["risk"])   # rischio congelato alla conferma

    def test_eventi(self):
        prev, seq = {}, []
        for r in self.reports:
            ev = self.live.diff_events(r, prev)
            seq.append([e["type"] for e in ev])
            v = r["v2"]
            prev = dict(prev, last_signal_date=v.get("signal_date") or prev.get("last_signal_date"),
                        v2={k: v.get(k) for k in ("status", "signal_date", "side", "fills")})
        self.assertEqual(seq, [[], ["signal"], ["entry"], ["dca_fill"], ["tp"]])
        # stesso stato due volte: nessun evento doppio
        self.assertEqual(self.live.diff_events(self.reports[3], dict(prev, v2=dict(prev["v2"], status="aperto", signal_date="2026-08-19", fills=2))), [])

    @unittest.skipIf("RADAR_RISK" in os.environ, "rischio base personalizzato")
    def test_numeri_storici(self):
        # v2 al rischio base dal vivo 4,3% (slippage 0,1%): 105 trade, WR 79%, +170,5%, DD giornaliero −11,1%
        T = self.full["stats"]["periods"]["Totale"]
        self.assertEqual(T["trades"], 105)
        self.assertAlmostEqual(T["win_rate"], 79.0, delta=0.5)
        self.assertAlmostEqual(T["total_return_%"], 170.5, delta=3.0)
        self.assertAlmostEqual(T["max_dd_%"], -11.1, delta=0.5)
        for k in ("2024–25", "2026"):   # walk-forward positivo
            self.assertGreater(self.full["stats"]["periods"][k]["total_return_%"], 0)

    @unittest.skipIf("RADAR_RISK" in os.environ, "rischio base personalizzato")
    def test_slippage_validato(self):
        # ricerca notte 01:47: con slippage 0,2% e rischio 4,67% → +140%
        from radar import paper
        from radar.data import load_all
        from radar.features import build_features
        cut = pd.Timestamp("2026-10-30")
        f, h4 = build_features(load_all()), paper.candles_4h()
        f, h4 = f[f.index < cut], h4[h4.index < cut]
        r = paper.simulate(f, h4, "2022-03-01", risk_fn=paper.v2_risk(f, h4, 0.0467), slip=0.002)
        self.assertAlmostEqual(r["stats"]["ret"], 140.0, delta=3.0)

    def test_telegram(self):
        from radar import telegram
        prev, n = {}, 0
        for r in self.reports:
            for ev in self.live.diff_events(r, prev):
                txt = telegram.format_event(ev, r)
                self.assertIn("RADAR SIGNAL BTC", txt)
                n += 1
            self.assertIn("RADAR SIGNAL BTC", telegram.daily_brief(r))
            v = r["v2"]
            prev = dict(prev, last_signal_date=v.get("signal_date") or prev.get("last_signal_date"),
                        v2={k: v.get(k) for k in ("status", "signal_date", "side", "fills")})
        self.assertEqual(n, 4)
        self.assertIn("in attesa di conferma 4h", telegram.format_event({"type": "signal", "v2": self.reports[1]["v2"]}))
        txt = telegram.format_event({"type": "entry", "v2": self.reports[2]["v2"]})
        self.assertIn("Leva", txt)
        self.assertIn("Stop", txt)
        ev = self.live.diff_events(self.reports[0], {"v2": dict(status="conferma", signal_date="2026-08-10", side="long")})
        self.assertEqual([e["type"] for e in ev], ["expired"])   # nessuna conferma entro 72h
        self.assertIn("scaduto", telegram.format_event(ev[0]))

    def test_intraday(self):
        from radar import intraday
        r = self.reports[3]
        v = r["v2"]
        idx = pd.date_range(v["entry_time"], periods=3, freq="h", tz="UTC")
        h = pd.DataFrame({"open": v["entry"], "high": v["tp"] + 10, "low": v["entry"], "close": v["tp"]}, index=idx)
        ev, keys = intraday.check(r, [], h)
        self.assertEqual([e["kind"] for e in ev], ["tp"])
        self.assertEqual(intraday.check(r, keys, h)[0], [])   # niente doppioni
        self.assertIn("take profit", intraday.format_events(ev))
        c = self.reports[1]
        h2 = pd.DataFrame({"open": 1.0, "high": c["v2"]["trigger"] + 1, "low": 1.0, "close": 1.0}, index=idx)
        ev, _ = intraday.check(c, [], h2)
        self.assertEqual([e["kind"] for e in ev], ["confirm"])


if __name__ == "__main__":
    unittest.main()
