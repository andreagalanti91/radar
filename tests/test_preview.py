"""Pre-analisi della prossima decisione W3 (radar/preview.py): soglie coerenti con weekly_bars, schema, dati mancanti."""
import json
import unittest

import pandas as pd

from radar.data import DATA_DIR

FILES = ["spot", "perp", "funding", "metrics", "fng"]
EPS = 1.0   # $ sotto/sopra la soglia


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in FILES), "dati mancanti")
class TestPreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar import preview, weekly
        from radar.data import load_all
        from radar.features import build_features
        cls.pv, cls.W = preview, weekly
        F = build_features(load_all())
        cls.F = F[F.index <= "2026-11-13"]            # venerdì 13/11/2026: W3 flat dopo l'uscita EMA del 09/11
        cls.Flong = F[F.index <= "2026-10-30"]        # long aperto dal 24/08/2026
        cls.p = preview.build(cls.F, {"liqmap": {"price": 70000, "bins": [[66000, 300, 0], [74000, 0, 100], [90000, 0, 999]]}})

    def _bar(self, f, C):
        return self.pv.proj_bar(f, C)

    def test_proiezione_come_weekly_bars(self):
        f = self.F
        b = self._bar(f, 70000.0)
        self.assertEqual(str(b.name.date()), "2026-11-15")
        self.assertEqual(b["close"], 70000.0)
        self.assertAlmostEqual(b["flow"], self.pv.current_flow(f), places=9)      # flusso proiettato = flusso attuale
        w = self.W.weekly_bars(f)
        self.assertAlmostEqual(b["sma"], (w["close"].iloc[-39:].sum() + 70000.0) / 40, places=6)
        self.assertEqual(b["high"], max(f.loc["2026-11-09":, "high"].max(), 70000.0))

    def test_soglie_coerenti(self):
        f, W = self.F, self.W
        th = self.pv.thresholds(W.weekly_bars(f))
        w0 = W.weekly_bars(f)
        for C, below in ((th["sma40"] - EPS, True), (th["sma40"] + EPS, False)):
            b = self._bar(f, C)
            self.assertEqual(bool(b["close"] < b["sma"]), below)
        for C, falling in ((th["sma40_falling"] - EPS, True), (th["sma40_falling"] + EPS, False)):
            self.assertEqual(bool(self._bar(f, C)["sma"] < w0["sma"].iloc[-4]), falling)
        for C, falling in ((th["ema20"] - EPS, True), (th["ema20"] + EPS, False)):
            self.assertEqual(bool(self._bar(f, C)["ema20"] < w0["ema20"].iloc[-1]), falling)
        for C, below in ((th["ema21"] - EPS, True), (th["ema21"] + EPS, False)):
            b = self._bar(f, C)
            self.assertEqual(bool(b["close"] < b["ema21"]), below)
        for k, col in (("macd_cross", "sig"), ("macd_zero", None)):
            for C, above in ((th[k] - EPS, False), (th[k] + EPS, True)):
                b = self._bar(f, C)
                self.assertEqual(bool(b["macd"] > (b["macd_sig"] if col else 0)), above)

    def test_segnale_cambia_alle_soglie(self):
        """Oggi: short sotto la SMA40 proiettata (~72,3k), nessun segnale sopra; ogni fascia confermata da weekly_bars."""
        sc = self.p["scenarios"]
        self.assertEqual(sc[0]["outcome"], "short")
        self.assertIsNone(sc[0]["lo"])
        self.assertAlmostEqual(sc[0]["hi"], 72334, delta=150)
        self.assertTrue(all(s["outcome"] == "none" for s in sc[1:]))
        self.assertTrue(any(abs(s["lo"] - 76596) < 150 for s in sc[1:]))     # EMA21 proiettata
        th = sc[0]["hi"]
        self.assertTrue(self._bar(self.F, th - EPS)["short"])
        self.assertFalse(self._bar(self.F, th + EPS)["short"])
        for s in sc:   # copertura completa, fasce contigue e crescenti, esito = weekly_bars al centro
            lo, hi = s["lo"], s["hi"]
            x = (lo + hi) / 2 if lo and hi else (hi - 500 if hi else lo + 500)
            self.assertEqual(self.pv.outcome(self.F, x, 0), s["outcome"])
        for a, b in zip(sc[:-1], sc[1:]):
            self.assertEqual(a["hi"], b["lo"])
            self.assertLess(b["lo"], b["hi"] if b["hi"] else float("inf"))
        self.assertIsNone(sc[-1]["hi"])

    def test_flusso_cambia_il_segnale(self):
        x = self.p["scenarios"][0]["hi"] - 1000
        self.assertEqual(self.pv.outcome(self.F, x, 0, flow=-0.5), "short")
        self.assertEqual(self.pv.outcome(self.F, x, 0, flow=+0.5), "none")

    def test_storico_short(self):
        h = self.p["history"]
        self.assertEqual(h["side"], "short")
        self.assertEqual([t["entry"] for t in h["trades"]], ["2022-01-03", "2022-08-15", "2025-12-01", "2026-05-25"])
        self.assertEqual((h["wins"], h["n"]), (4, 4))
        for t in h["trades"]:
            self.assertLessEqual(t["drop_from_8w_high_pct"], 0)
            self.assertGreaterEqual(t["adverse_pct"], 0)

    def test_if_signal_come_plan(self):
        s, W = self.p["if_signal"], self.W
        self.assertEqual(s["side"], "short")
        self.assertEqual(self.p["flow"]["sign_needed"], "neg")
        b = self._bar(self.F, self.p["price"])
        self.assertAlmostEqual(s["stop"], self.p["price"] + 2.5 * b["atr"], delta=0.02)
        self.assertAlmostEqual(s["expo"], round(W.exposure(-1, self.p["price"], b["atr"]), 3), places=3)
        self.assertAlmostEqual(s["capital_usd"], W.CAPITAL * W.SHARE, delta=1)
        self.assertGreater(s["loss_at_stop_usd"], 0)

    def test_schema(self):
        p = self.p
        self.assertEqual(set(p), {"decision_utc", "week_close_utc", "price", "position", "conditions", "scenarios", "flow",
                                  "if_signal", "history", "liq_context", "note", "updated_utc"})
        self.assertEqual((p["decision_utc"], p["week_close_utc"], p["position"]), ("2026-11-16 00:00", "2026-11-15", "flat"))
        for c in p["conditions"]:
            self.assertEqual(set(c), {"key", "label", "now", "value", "depends_on_close"})
        for s in p["scenarios"]:
            self.assertEqual(set(s), {"lo", "hi", "outcome", "label", "detail"})
            self.assertIn(s["outcome"], ("short", "long", "exit", "hold", "none"))
        self.assertEqual(set(p["flow"]), {"value", "sign_needed", "note"})
        self.assertEqual(set(p["if_signal"]), {"side", "close_est", "stop", "stop_pct", "expo", "loss_at_stop_pct",
                                               "capital_usd", "loss_at_stop_usd", "exits"})
        self.assertEqual(set(p["history"]), {"side", "trades", "wins", "n"})
        for t in p["history"]["trades"]:
            self.assertEqual(set(t), {"entry", "px", "drop_from_8w_high_pct", "move_pct", "adverse_pct", "reason"})
        lc = p["liq_context"]
        self.assertEqual(set(lc), {"rows", "base", "regime_rows", "imb_now", "note"})
        self.assertEqual(sum(r["days"] for r in lc["rows"]), 1622)
        self.assertEqual(lc["base"], {"r7": 0.6, "r14": 1.2, "r30": 2.3})
        self.assertAlmostEqual(lc["imb_now"], (100 - 300) / 400, places=3)    # entro ±8%: 90.000 escluso
        json.dumps(p)

    def test_in_posizione(self):
        p = self.pv.build(self.Flong, {})
        self.assertEqual(p["position"], "long")
        self.assertIsNone(p["if_signal"])
        sc = p["scenarios"]
        self.assertEqual([s["outcome"] for s in sc], ["exit", "hold"])
        th = sc[0]["hi"]
        self.assertEqual(self.pv.outcome(self.Flong, th - EPS, 1), "exit")
        self.assertEqual(self.pv.outcome(self.Flong, th + EPS, 1), "hold")
        self.assertIn("trail", [c["key"] for c in p["conditions"]])
        self.assertEqual(p["history"]["side"], "long")

    def test_dati_mancanti(self):
        self.assertIsNone(self.pv.build(None, {}))
        self.assertIsNone(self.pv.build(pd.DataFrame(), {}))
        self.assertIsNone(self.pv.build(self.F.drop(columns=["pf14z"]), {}))
        self.assertIsNone(self.pv.build(self.F.iloc[-100:], {}))
        p = self.pv.build(self.F, None)
        self.assertIsNone(p["liq_context"]["imb_now"])
        p = self.pv.build(self.F, {"liqmap": {"price": None}})
        self.assertIsNotNone(p)


if __name__ == "__main__":
    unittest.main()
