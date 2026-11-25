"""Segnali reali v2 (radar/live.py): stato su dati storici tagliati, eventi, numeri storici (nessun messaggio Telegram)."""
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

    def test_eventi_v2_senza_messaggi(self):
        """Eventi di v2 (stato per la dashboard): calcolati come prima; i messaggi Telegram di v2 (spenti dal 12/11/2026) e il
        controllo orario dei livelli v2 sono stati eliminati il 25/11/2026."""
        from radar import intraday, telegram
        prev, n = {}, 0
        for r in self.reports:
            n += len(self.live.diff_events(r, prev))
            v = r["v2"]
            prev = dict(prev, last_signal_date=v.get("signal_date") or prev.get("last_signal_date"),
                        v2={k: v.get(k) for k in ("status", "signal_date", "side", "fills")})
        self.assertEqual(n, 4)
        ev = self.live.diff_events(self.reports[0], {"v2": dict(status="conferma", signal_date="2026-08-10", side="long")})
        self.assertEqual([e["type"] for e in ev], ["expired"])   # nessuna conferma entro 72h
        for name in ("format_event", "daily_brief", "_plan_lines", "_status_line", "_weekly_line"):
            self.assertFalse(hasattr(telegram, name), name)
        for name in ("check", "format_events"):
            self.assertFalse(hasattr(intraday, name), name)
        self.assertTrue(callable(intraday.hourly_since))          # resta: candele orarie per lo stop di W3.2


if __name__ == "__main__":
    unittest.main()
