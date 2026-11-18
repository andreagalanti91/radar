"""Pre-analisi W3, sezione Oggi (radar/preview.py: position_block, today) e riepilogo giornaliero "Oggi" su Telegram
(radar/telegram.today_brief, radar/cli.daily_brief/brief_due)."""
import inspect
import json
import os
import unittest
from unittest import mock

import numpy as np
import pandas as pd

from radar import cli, preview, telegram
from radar.data import DATA_DIR

FILES = ["spot", "perp", "funding", "metrics", "fng"]
POS_KEYS = {"side", "entry_date", "entry_px", "price", "pnl_pct", "pnl_usd", "capital_usd", "stop", "stop_dist_pct",
            "trail_best", "exit_ema21_threshold", "dist_rule", "days_open"}
TODAY_KEYS = {"updated_utc", "items", "sr", "analog", "note"}
ITEM_KEYS = {"key", "label", "value", "read", "reliability"}
SR_KEYS = {"name", "lo", "hi", "dist_pct", "hold_pct", "random_pct"}
AN_KEYS = {"label", "n", "p7", "ci7", "p30", "ci30", "mean7"}
LEVELS = {"supports": [{"price": 60000, "lo": 59000, "hi": 61000, "touches": 3, "weekly": True, "dist_pct": -6.0},
                       {"price": 40000, "lo": 39000, "hi": 41000, "touches": 0, "weekly": False, "dist_pct": -38.0}],
          "resistances": [{"price": 66000, "lo": 65000, "hi": 67000, "touches": 2, "weekly": False, "dist_pct": 2.5}]}
REPORT = {"levels": LEVELS, "liqsources": {"total": {"24h": {"long_usd": 3e7, "short_usd": 1e7, "n": 10}}, "stale": False},
          "liqmap": {"price": 65000, "bins": [[62000, 500, 0], [68000, 0, 100]]}}


def _synth(drop=()) -> pd.DataFrame:
    """Dati giornalieri sintetici in calo (regime short) con le colonne che usa la pre-analisi."""
    idx = pd.date_range("2018-01-01", periods=2000, freq="D")
    rng = np.random.default_rng(7)
    c = 20000 * np.exp(np.cumsum(rng.normal(0, 0.02, len(idx))))
    f = pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99, "close": c, "pf14z": rng.normal(0, 1, len(idx)),
                      "sf14z": rng.normal(0, 1, len(idx)), "funding": 0.0001, "funding_z": 0.1, "oi_chg7": 0.02,
                      "oi_z": 0.5}, index=idx)
    return f.drop(columns=list(drop))


class TestSchema(unittest.TestCase):
    def _check_today(self, td):
        self.assertEqual(set(td), TODAY_KEYS)
        self.assertEqual(td["note"], "Contesto, non segnale: decide W3.")
        for it in td["items"]:
            self.assertEqual(set(it), ITEM_KEYS)
            self.assertTrue(all(isinstance(it[k], str) and it[k] for k in ITEM_KEYS))
        for z in td["sr"]:
            self.assertEqual(set(z), SR_KEYS)
        if td["analog"] is not None:
            self.assertEqual(set(td["analog"]), AN_KEYS)
            self.assertEqual(len(td["analog"]["ci7"]), 2)
            self.assertLessEqual(td["analog"]["ci30"][0], td["analog"]["p30"])
        json.dumps(td, allow_nan=False)    # mai NaN nel report

    def test_today_sintetico_schema_e_voci(self):
        f = _synth()
        p = preview.build(f, REPORT)
        self.assertIsNotNone(p)
        self.assertIn("position_block", p)
        self._check_today(p["today"])
        keys = [x["key"] for x in p["today"]["items"]]
        for k in ("pf14z", "sf14z", "div", "funding", "oi7", "liq24h", "liqmap_imb", "dist_sma40", "dist_ema21"):
            self.assertIn(k, keys)
        self.assertTrue(all("lezion" in x["reliability"] or "stima" in x["reliability"] for x in p["today"]["items"]))

    def test_sr_tenuta_n4(self):
        sr = preview.sr_rows(LEVELS)
        self.assertEqual([z["name"] for z in sr], ["R1", "S1", "S2"])
        r1, s1, s2 = sr
        self.assertEqual((r1["hold_pct"], r1["random_pct"]), (80.0, 77.2))   # resistenza, 0–3%: tipo G con 8 tocchi → tutti i tipi
        self.assertEqual((s1["hold_pct"], s1["random_pct"]), (70.9, 74.0))   # supporto settimanale 3–8% (86 tocchi)
        self.assertIsNone(s2["hold_pct"])                                     # oltre il 15%: fuori dal test
        self.assertEqual(preview.sr_rows(None), [])

    def test_analog_terzili(self):
        a = preview.analog(-1.24, 0.24)
        self.assertEqual(a["n"], 50)
        self.assertEqual((a["p7"], a["ci7"], a["p30"]), (52.0, [42.1, 62.1], 36.5))
        self.assertIn("pf14z basso", a["label"])
        self.assertIn("sf14z medio", a["label"])
        self.assertIn("sf14z alto", preview.analog(None, 1.0)["label"])         # ripiego sul terzile singolo
        self.assertIsNone(preview.analog(None, None))
        self.assertIsNone(preview.analog(0.0, 0.0, tab={}))

    def test_dati_mancanti_nessuna_eccezione(self):
        f = _synth(drop=("sf14z", "oi_chg7", "oi_z", "funding_z"))
        p = preview.build(f, None)
        self.assertIsNotNone(p)
        self._check_today(p["today"])
        keys = [x["key"] for x in p["today"]["items"]]
        self.assertNotIn("sf14z", keys)
        self.assertNotIn("oi7", keys)
        self.assertEqual(p["today"]["sr"], [])
        td = preview.today(f.iloc[-50:], pd.DataFrame({"sma": [np.nan], "ema21": [np.nan]}), {"liqsources": None, "levels": {}},
                           float(f["close"].iloc[-1]))
        self._check_today(td)
        self.assertIsNone(preview.build(None, None))


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in FILES), "dati mancanti")
class TestPosizioneReale(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from radar import weekly
        from radar.data import load_all
        from radar.features import build_features
        cls.W = weekly
        cls.F = build_features(load_all())
        cls.F = cls.F[cls.F["close"].notna()]

    def test_flat(self):
        p = preview.build(self.F[self.F.index <= "2026-11-13"], {"liqsources": None})   # W3 flat dopo l'uscita EMA del 09/11
        self.assertEqual(p["position"], "flat")
        self.assertIsNone(p["position_block"])
        self.assertTrue({b["outcome"] for b in p["scenarios"]} <= {"none", "short", "long"})

    def test_uscita_decisa_flat(self):
        p = preview.build(self.F[self.F.index <= "2026-11-08"], {"liqsources": None})   # domenica: uscita EMA decisa
        self.assertIsNone(p["position_block"])

    def test_short_aperto(self):
        f = self.F[self.F.index <= "2026-11-17"]
        p = preview.build(f, {"liqsources": None})
        pb = p["position_block"]
        self.assertEqual(set(pb), POS_KEYS)
        self.assertEqual((pb["side"], pb["entry_date"], pb["days_open"]), ("short", "2026-11-16", 2))
        o = self.W.simulate(f)["open"]
        cap = self.W.CAPITAL * self.W.SHARE
        self.assertAlmostEqual(pb["pnl_usd"], round(cap * o["pnl"], 0))
        self.assertAlmostEqual(pb["stop"], round(o["trail"], 2))
        self.assertGreater(pb["stop_dist_pct"], 0)                     # short: stop sopra il prezzo
        self.assertIn("Short", pb["dist_rule"])
        thr = pb["exit_ema21_threshold"]                                # soglia d'uscita = esito di W3 sulla settimana proiettata
        self.assertEqual(preview.outcome(f, thr + 1, -1), "exit")
        self.assertEqual(preview.outcome(f, thr - 1, -1), "hold")
        self.assertEqual({b["outcome"] for b in p["scenarios"]}, {"hold", "exit"})   # in posizione: solo uscita/mantieni
        json.dumps(p, allow_nan=False, default=str)

    def test_long_aperto(self):
        p = preview.build(self.F[self.F.index <= "2026-10-30"], {"liqsources": None})   # long dal 24/08/2026
        pb = p["position_block"]
        self.assertEqual(pb["side"], "long")
        self.assertLess(pb["stop_dist_pct"], 0)
        self.assertIn("Long", pb["dist_rule"])
        self.assertEqual({b["outcome"] for b in p["scenarios"]}, {"hold", "exit"})

    def test_segnale_in_apertura(self):
        pb = preview.build(self.F[self.F.index <= "2026-11-15"], {"liqsources": None})["position_block"]   # segnale short 15/11
        self.assertEqual((pb["side"], pb["entry_date"], pb["entry_px"], pb["pnl_usd"]), ("short", "2026-11-16", None, None))


PV = {"price": 64947.35, "week_close_utc": "2026-11-22",
      "position_block": {"side": "short", "entry_date": "2026-11-16", "entry_px": 65285.7, "price": 64947.35, "pnl_pct": 0.46,
                         "pnl_usd": 232.0, "capital_usd": 50000.0, "stop": 81695.12, "stop_dist_pct": 25.79,
                         "trail_best": 64882.87, "exit_ema21_threshold": 75573.68, "dist_rule": "Short: … non attiva.",
                         "days_open": 2},
      "scenarios": [{"lo": None, "hi": 75573.68, "outcome": "hold"}, {"lo": 75573.68, "hi": None, "outcome": "exit"}],
      "today": {"items": [{"key": "pf14z", "label": "", "value": "−1,24σ", "read": "terzile basso: perp in vendita; x",
                           "reliability": ""},
                          {"key": "funding", "label": "", "value": "0,0098%/giorno · 3,6%/anno", "read": "", "reliability": ""}],
                "sr": [{"name": "R1", "lo": 64854.0, "hi": 69000.0, "dist_pct": 2.6, "hold_pct": 80.0, "random_pct": 77.2}],
                "analog": {"label": "pf14z basso · sf14z medio, dal 2021", "n": 50, "p7": 52.0, "ci7": [42.1, 62.1],
                           "p30": 36.5, "ci30": [22.2, 53.2], "mean7": 1.22}, "note": "Contesto, non segnale: decide W3."}}


class TestBrief(unittest.TestCase):
    def test_testo_in_posizione(self):
        t = telegram.today_brief({"preview": PV, "weekly": {"date": "2026-11-17"}}, "2026-11-18")
        lines = t.splitlines()
        self.assertLessEqual(len(lines), 8)
        self.assertTrue(lines[0].startswith("<b>RADAR SIGNAL BTC · Oggi</b>"))
        self.assertIn("SHORT dal 16/11", t)
        self.assertIn("$81.695", t)
        self.assertIn("sopra $75.574", t)
        self.assertEqual(lines[-1], "Contesto, non segnale: decide W3.")
        self.assertNotIn("<b>W3</b>: nessuna", t)

    def test_testo_flat_soglia_segnale(self):
        pv = dict(PV, position_block=None, scenarios=[{"lo": None, "hi": 60000.0, "outcome": "short"},
                                                       {"lo": 60000.0, "hi": None, "outcome": "none"}])
        t = telegram.today_brief({"preview": pv}, "2026-11-18")
        self.assertIn("nessuna posizione", t)
        self.assertIn("short se chiude sotto $60.000", t)

    def test_dati_mancanti(self):
        for rep in ({}, None, {"weekly": {"status": "aperto"}}, {"preview": {"today": None}},
                    {"preview": {"position_block": {"side": "short"}}}):
            t = telegram.today_brief(rep)
            self.assertIn("RADAR SIGNAL BTC · Oggi", t)
            self.assertLessEqual(len(t.splitlines()), 8)

    def test_una_volta_al_giorno_indipendente_da_v2(self):
        T = pd.Timestamp
        sent, st = [], {}
        with mock.patch.dict(os.environ, {"RADAR_DAILY_BRIEF": "1", "RADAR_V2_ALERTS": "0"}):
            self.assertFalse(cli.daily_brief({"preview": PV}, st, T("2026-11-18 00:20"), "2026-11-17", send=lambda m: False))
            self.assertNotIn("daily_brief", st)                                   # Telegram non conferma: si riprova
            self.assertTrue(cli.daily_brief({"preview": PV}, st, T("2026-11-18 01:20"), "2026-11-17",
                                            send=lambda m: sent.append(m) or 123))
            self.assertEqual(st["daily_brief"], "2026-11-18")
            self.assertFalse(cli.daily_brief({"preview": PV}, st, T("2026-11-18 02:20"), "2026-11-17",
                                             send=lambda m: sent.append(m) or 1))
            self.assertEqual(len(sent), 1)
            self.assertIn("RADAR SIGNAL BTC · Oggi", sent[0])
            self.assertTrue(cli.brief_due(st, T("2026-11-19 00:05"), "2026-11-18"))
        with mock.patch.dict(os.environ, {"RADAR_DAILY_BRIEF": "0"}):
            self.assertFalse(cli.brief_due({}, T("2026-11-19 00:05"), "2026-11-18"))
        src = inspect.getsource(cli.daily)
        call = src.index('_soft("riepilogo giornaliero", daily_brief, report')
        self.assertNotIn("if v2_on", src[src.rfind("\n", 0, call - 1) - 80: call])   # non più legato agli alert di v2


if __name__ == "__main__":
    unittest.main()
