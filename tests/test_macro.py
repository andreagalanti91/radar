"""Chiusura multi-asset (radar/macro.py): schema per la UI, cache con fonte caduta, regime, flag, riga Telegram, niente rete."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd
import requests

from radar import macro as M
from radar import telegram

TODAY = pd.Timestamp("2026-11-22")
ASSET_KEYS = {"key", "name", "close", "d1_pct", "d5_pct", "d20_pct", "above_ma200", "date"}


def series(n=260, start=100.0, step=0.1, end="2026-11-20"):
    idx = pd.bdate_range(end=end, periods=n)
    return pd.Series([start + step * i for i in range(n)], index=idx)


def write_spot(d: Path, s: pd.Series):
    pd.DataFrame({"close": s.values, "open": s.values}, index=pd.Index(s.index, name="date")).to_csv(d / "spot.csv")


def ok_sources(over=None):
    base = {"spx": series(), "ndx": series(start=200), "vix": series(start=15, step=0.0), "us10y": series(start=4, step=0.0),
            "usd": series(start=120, step=-0.01), "gold": series(start=3000), "silver": series(start=40)}
    base.update(over or {})
    return {k: [(f"test {k}", (lambda v=v: v))] for k, v in base.items()}


def broken():
    raise requests.ConnectionError("rete assente")


class TestSchema(unittest.TestCase):
    def test_schema_e_regime(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            write_spot(d, series(start=60000, step=10))
            m = M.build(d, weekly={"status": "aperto", "side": "short"}, sources=ok_sources(), now=TODAY)
            self.assertEqual(set(m), {"updated_utc", "assets", "regime", "flags", "note"})
            self.assertEqual([a["key"] for a in m["assets"]], ["btc", "spx", "ndx", "gold", "silver", "usd", "vix", "us10y"])
            for a in m["assets"]:
                self.assertEqual(set(a), ASSET_KEYS)
                self.assertIsInstance(a["above_ma200"], bool)
            self.assertEqual(set(m["regime"]), {"label", "detail"})
            self.assertEqual(m["regime"]["label"], "rischio acceso")        # S&P > MA200, VIX 15, dollaro in calo
            self.assertIn("posizione W3 (short) contro il regime (rischio acceso)", m["flags"])
            self.assertTrue(m["note"].startswith(M.NOTE))
            self.assertTrue((d / M.FILE).exists())
            a = {x["key"]: x for x in m["assets"]}
            self.assertEqual(a["vix"]["d20_pct"], 0.0)                     # VIX e 10 anni in punti
            self.assertAlmostEqual(a["spx"]["d1_pct"], (series().iloc[-1] / series().iloc[-2] - 1) * 100, places=2)

    def test_storia_corta_ma200_null(self):
        with tempfile.TemporaryDirectory() as d:
            m = M.build(Path(d), sources=ok_sources({"silver": series(n=50)}), now=TODAY)
            a = {x["key"]: x for x in m["assets"]}
            self.assertIsNone(a["silver"]["above_ma200"])
            self.assertNotIn("btc", a)                                     # niente spot.csv: BTC assente, non inventato
            self.assertIn("Non disponibili: BTC", m["note"])


class TestCache(unittest.TestCase):
    def test_fonte_caduta_usa_cache(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            M.build(d, sources=ok_sources(), now=pd.Timestamp("2026-11-21"))
            src = ok_sources()
            src["gold"] = [("rotta", broken)]
            m = M.build(d, sources=src, now=TODAY)
            a = {x["key"]: x for x in m["assets"]}
            self.assertEqual(a["gold"]["date"], "2026-11-20")
            self.assertIn("Oro (dato del 20/11)", m["note"])
            c = M.load_cache(d / M.FILE)
            self.assertEqual(set(c.loc[c["key"] == "gold", "fetched"]), {"2026-11-21"})   # si riprova al giro dopo
            self.assertEqual(set(c.loc[c["key"] == "spx", "fetched"]), {"2026-11-22"})

    def test_una_volta_al_giorno(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            M.build(d, sources=ok_sources(), now=TODAY)
            calls = []
            src = {"spx": [("x", lambda: calls.append(1) or series())]}
            M.build(d, sources=src, now=TODAY)
            self.assertEqual(calls, [])

    def test_riserva(self):
        c, err = M.refresh(M.load_cache(Path("/non/esiste.csv")), "2026-11-22",
                           {"gold": [("prima", broken), ("riserva", lambda: series(start=3000))]})
        self.assertEqual(err, {})
        self.assertEqual(set(c["source"]), {"riserva"})

    def test_senza_rete_nessuna_eccezione(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(M.requests, "get", side_effect=requests.ConnectionError("no")), \
                mock.patch.object(M.requests, "post", side_effect=requests.ConnectionError("no")):
            self.assertIsNone(M.build(Path(d), now=TODAY))                # nessun dato e nessuna cache: None
            write_spot(Path(d), series(start=60000))
            m = M.build(Path(d), now=TODAY)
            self.assertEqual([a["key"] for a in m["assets"]], ["btc"])
            self.assertEqual(m["regime"]["label"], "non determinabile")


class TestFlags(unittest.TestCase):
    def a(self, **kw):
        base = {"spx": {"above_ma200": True, "d20_pct": 2.0}, "vix": {"close": 18.0}, "usd": {"d20_pct": -1.0},
                "btc": {"d20_pct": 1.0}}
        for k, v in kw.items():
            base[k] = dict(base.get(k, {}), **v)
        return base

    def test_flags(self):
        a = self.a(vix={"close": 36.2}, spx={"above_ma200": False, "d20_pct": -6.0}, btc={"d20_pct": 8.0})
        reg = M.regime(a)
        self.assertEqual(reg["label"], "misto")                             # dollaro in calo, il resto contro
        f = M.flags(a, reg, {"status": "aperto", "side": "long"})
        self.assertIn("VIX sopra 34 (36,2)", f)
        self.assertIn("S&P 500 sotto la media a 200 giorni", f)
        self.assertIn("BTC e S&P 500 divergono a 20 giorni (BTC +8,0%, S&P −6,0%)", f)
        self.assertFalse(any("posizione W3" in x for x in f))               # regime misto: nessun contrasto

    def test_regime_spento_e_posizione(self):
        a = self.a(vix={"close": 30.0}, spx={"above_ma200": False}, usd={"d20_pct": 2.0})
        reg = M.regime(a)
        self.assertEqual(reg["label"], "rischio spento")
        self.assertIn("posizione W3 (long) contro il regime (rischio spento)", M.flags(a, reg, {"status": "aperto", "side": "long"}))
        self.assertFalse(any("posizione" in x for x in M.flags(a, reg, {"status": "aperto", "side": "short"})))
        self.assertFalse(any("posizione" in x for x in M.flags(a, reg, {"status": "flat"})))
        self.assertEqual(M.flags(self.a(), M.regime(self.a()), None), [])

    def test_divergenza_piccola_no(self):
        a = self.a(btc={"d20_pct": 2.0}, spx={"d20_pct": -1.0})
        self.assertFalse(any("divergono" in x for x in M.flags(a, M.regime(a))))


class TestTelegram(unittest.TestCase):
    M = {"assets": [{"key": "spx", "close": 7175.83, "d1_pct": -2.02}, {"key": "ndx", "close": 23879.2, "d1_pct": -2.27},
                    {"key": "gold", "close": 3550.16, "d1_pct": 0.1}, {"key": "usd", "close": 122.65, "d1_pct": 0.09},
                    {"key": "vix", "close": 28.44, "d1_pct": 3.88}],
         "flags": ["a", "b", "c"]}

    def test_riga(self):
        ls = M.telegram_lines(self.M)
        self.assertEqual(ls[0], "Mercati: S&P 7.176 (−2,0%) · Nasdaq 23.879 (−2,3%) · oro 3.550 (+0,1%) · "
                                "dollaro 122,7 (+0,1%) · VIX 28,4 (+3,9)")
        self.assertEqual(ls[1:], ["Da rivedere: a", "Da rivedere: b"])      # al massimo 2 flag
        self.assertEqual(M.telegram_lines(None), [])
        self.assertEqual(M.telegram_lines({"assets": [{"key": "spx"}]}), [])

    def test_nel_riepilogo(self):
        t = telegram.today_brief({"macro": self.M}, "2026-11-22").splitlines()
        self.assertTrue(t[-4].startswith("Mercati: S&P"))
        self.assertEqual(t[-1], "Contesto, non segnale: decide W3.")
        self.assertNotIn("Mercati", telegram.today_brief({"macro": {"assets": "rotto"}}))


if __name__ == "__main__":
    unittest.main()
