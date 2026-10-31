"""Laboratorio (radar/lab.py): JSON con v2 e W2, metriche W2 coerenti con il CSV dei trade."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from radar.data import DATA_DIR

FILES = ["spot_1h", "spot", "perp", "funding", "metrics", "fng", "taker_1h"]
ROOT = Path(__file__).resolve().parent.parent
KEYS = {"trades_per_year", "win_rate", "avg_trade_pct", "total_return_pct", "max_dd_pct", "final_10k_1x", "final_10k_2x"}


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in FILES), "dati mancanti")
class TestLab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar import lab, live, paper
        from radar.data import load_all
        from radar.features import build_features
        cut = pd.Timestamp("2026-10-30")
        F, H = build_features(load_all()), paper.candles_4h()
        cls.report = live.evaluate(F[F.index < cut], h4=H[H.index < cut], frozen={})
        cls.tmp = Path(tempfile.mkdtemp()) / "lab.json"
        cls.lab = lab.build(cls.report, out=cls.tmp)
        cls.by = {c["name"]: c for c in cls.lab["candidates"]}

    def test_json_valido(self):
        L = json.loads(self.tmp.read_text())
        self.assertEqual(L["updated"], self.report["date"])
        self.assertIn("v2 (in uso)", self.by)
        self.assertIn("W2 settimanale (su carta)", self.by)
        for c in L["candidates"]:
            self.assertIn(c["status"], ("in uso", "su carta", "bocciato"))
            self.assertTrue(2 <= len(c["rules"]) <= 3)
            self.assertEqual(set(c["metrics"]), KEYS)
            self.assertTrue(c["trades"])
            for k in ("curve_1x", "curve_2x"):
                d = [p[0] for p in c[k]]
                self.assertEqual(d, sorted(set(d)))   # date crescenti e uniche (richiesto dal grafico)
                self.assertEqual(c[k][0][1], 10000.0)

    def test_v2(self):
        v = self.by["v2 (in uso)"]
        closed = [t for t in self.report["trades"]["futures"] if t["exit"] != "open"]
        self.assertEqual(len(v["trades"]), len(closed))
        self.assertEqual(v["curve_1x"][0][0], "2022-03-01")
        lv = self.report["stats"]["leverage"]   # stesse curve di Statistiche (tetto 5x)
        self.assertAlmostEqual(v["metrics"]["final_10k_1x"], lv["1"]["final_10k"], delta=2)
        self.assertAlmostEqual(v["metrics"]["final_10k_2x"], lv["2"]["final_10k"], delta=2)

    def test_w2_coerente_col_csv(self):
        w = self.by["W2 settimanale (su carta)"]
        with open(ROOT / "research" / "weekly_w2_trades.csv", newline="") as fh:
            rows = list(csv.DictReader(fh))
        p = np.array([float(r["pnl_capitale_%"]) for r in rows])
        m = w["metrics"]
        self.assertEqual(len(w["trades"]), len(rows))
        self.assertAlmostEqual(m["win_rate"], (p > 0).mean() * 100, delta=0.2)
        self.assertAlmostEqual(m["avg_trade_pct"], p.mean(), delta=0.1)
        self.assertAlmostEqual(m["final_10k_1x"], w["curve_1x"][-1][1], delta=0.01 * m["final_10k_1x"])
        self.assertAlmostEqual(m["final_10k_2x"], w["curve_2x"][-1][1], delta=0.01 * m["final_10k_2x"])
        self.assertAlmostEqual(w["curve_1x"][-1][1], float(rows[-1]["capitale_10k_1x"]), delta=20)
        self.assertAlmostEqual(m["total_return_pct"], (m["final_10k_1x"] / 10000 - 1) * 100, delta=1)
        years = (pd.Timestamp(rows[-1]["uscita"]) - pd.Timestamp(rows[0]["ingresso"])).days / 365.25
        self.assertAlmostEqual(m["trades_per_year"], len(rows) / years, delta=0.1)
        eq = np.array([v for _, v in w["curve_1x"]])
        # DD della ricerca sull'equity settimanale: mai migliore di quello della curva a gradini sulle uscite
        self.assertLessEqual(m["max_dd_pct"], (eq / np.maximum.accumulate(eq) - 1).min() * 100)

    def test_dashboard(self):
        from radar.dashboard import render
        out = render(dict(self.report, lab=self.lab), Path(tempfile.mkdtemp()) / "index.html", standalone=False)
        html = out.read_text()
        self.assertIn('id="labTab"', html)
        self.assertIn('"W2 settimanale (su carta)"', html)


if __name__ == "__main__":
    unittest.main()
