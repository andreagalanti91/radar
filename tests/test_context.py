"""Riquadro "Contesto" (radar/context.py): regime e direzioni con valori noti, fonte assente, dato vecchio, nessuna probabilità."""
import json
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from radar import context as cx

NOW = pd.Timestamp("2026-11-23")
NOTE = ("Contesto, non segnale: regimi e politica economica descrivono il mercato ma nei test non ne hanno anticipato la "
        "direzione (lezione 113). Decide W3.2.")
BANKS = [{"bank": "BCE", "date": "2026-12-03"}, {"bank": "Fed", "date": "2026-12-09"}, {"bank": "Fed", "date": "2027-01-27"}]


def days(n, end="2026-11-21"):
    return pd.date_range(end=end, periods=n)


def write_spot(d: Path, close: pd.Series):
    pd.DataFrame({"date": close.index.strftime("%Y-%m-%d"), "close": close.values}).to_csv(d / "spot.csv", index=False)


def fred_ok(end="2026-11-19"):
    """Serie sintetiche: tasso 3,63 → 3,88 il 17/09/2026 (con un'oscillazione di fine mese da ignorare), bilancio fermo,
    conto del Tesoro in calo (liquidità netta in aumento), CPI annuo 3,0% → 3,5%, VIX 28,44."""
    i = pd.date_range("2024-06-01", end)
    dff = pd.Series(3.63, index=i)
    dff[i >= "2026-09-17"] = 3.88
    dff[i == "2026-09-30"] = 3.70                   # un giorno solo (fine mese): non è una mossa
    w = pd.date_range("2024-06-05", end, freq="W-WED")
    walcl = pd.Series(6_740_000.0, index=w)
    tga = pd.Series(np.linspace(900_000, 800_000, len(w)), index=w)
    rrp = pd.Series(50.0, index=pd.bdate_range("2024-06-03", end))
    m = pd.date_range("2025-01-01", "2026-10-01", freq="MS")
    c = pd.Series(100.0, index=m)
    c[m >= "2026-01-01"] = 103.0
    c[pd.Timestamp("2026-10-01")] = 103.5
    vix = pd.Series(20.0, index=pd.bdate_range("2026-09-01", end))
    vix.iloc[-1] = 28.44
    return {"DFF": dff, "WALCL": walcl, "WTREGEN": tga, "RRPONTSYD": rrp, "CPIAUCSL": c, "VIXCLS": vix}


def fetcher(data, calls=None):
    def f(sid, today):
        if calls is not None:
            calls.append(sid)
        return data[sid]
    return f


def broken(sid, today):
    raise ConnectionError("fonte non raggiungibile")


def texts(o) -> str:
    """Tutto il testo mostrato dal riquadro e dai dettagli."""
    return " ".join([o["title"], o["note"], o.get("warn") or "", o["source"]] + [r["label"] + " " + r["text"] for r in o["rows"]]
                    + [f"{r['label']} {r['value']} {r['text']}" for r in o["details"]])


class TestMercato(unittest.TestCase):
    def test_ribasso_volatilita_alta(self):
        i = days(700)
        c = pd.Series(np.r_[np.full(400, 100.0), np.linspace(100, 60, 300)], index=i)
        c.iloc[-30::2] *= 1.05                      # ultimi 30 giorni agitati
        m = cx.market(c)
        self.assertEqual((m["trend"], m["trend_code"], m["sma_slope"], m["vol"]), ("ribasso", "D", "in discesa", "alta"))
        sma = float(c.iloc[-200:].mean())
        self.assertAlmostEqual(m["dist_pct"], round((float(c.iloc[-1]) / sma - 1) * 100, 1))
        self.assertLess(m["dist_pct"], 0)

    def test_rialzo_volatilita_bassa(self):
        i = days(700)
        r = np.where(np.arange(700) < 600, np.where(np.arange(700) % 2, 0.03, -0.02), 0.004)
        m = cx.market(pd.Series(100 * np.exp(np.cumsum(r)), index=i))
        self.assertEqual((m["trend"], m["vol"]), ("rialzo", "bassa"))
        self.assertGreater(m["dist_pct"], 0)

    def test_laterale(self):
        c = pd.Series(np.linspace(60, 100, 700), index=days(700))
        c.iloc[-3:] = 80.0                          # sotto la media, ma la media sale ancora
        m = cx.market(c)
        self.assertEqual((m["trend"], m["trend_code"], m["sma_slope"]), ("laterale", "M", "in salita"))

    def test_storia_corta(self):
        self.assertIsNone(cx.market(pd.Series(100.0, index=days(150))))
        m = cx.market(pd.Series(np.linspace(100, 120, 300), index=days(300)))   # trend sì, mediana a un anno no
        self.assertEqual(m["trend"], "rialzo")
        self.assertIsNone(m["vol"])


class TestFed(unittest.TestCase):
    def test_tasso_direzione_e_ultima_mossa(self):
        f = fred_ok()
        r = cx.rate(f["DFF"])
        self.assertEqual((r["value"], r["direction"], r["change"]), (3.88, "in rialzo", 0.25))
        self.assertEqual(r["last_move"], {"date": "2026-09-17", "change": 0.25})
        i = pd.date_range("2025-01-01", "2026-11-19")
        cut = pd.Series(4.33, index=i)
        cut[i >= "2026-10-29"] = 4.08
        r = cx.rate(cut)
        self.assertEqual((r["direction"], r["last_move"]), ("in calo", {"date": "2026-10-29", "change": -0.25}))
        r = cx.rate(pd.Series(3.63, index=i))
        self.assertEqual((r["direction"], r["last_move"]), ("fermo", None))

    def test_bilancio_e_liquidita(self):
        w = pd.date_range("2026-01-07", "2026-11-18", freq="W-WED")
        self.assertEqual(cx.balance(pd.Series(6_740_000.0, index=w))["direction"], "stabile")
        self.assertEqual(cx.balance(pd.Series(np.linspace(6_000_000, 6_800_000, len(w)), index=w))["direction"], "in aumento")
        self.assertEqual(cx.balance(pd.Series(np.linspace(7_500_000, 6_800_000, len(w)), index=w))["direction"], "in calo")
        walcl = pd.Series(6_740_000.0, index=w)
        rrp = pd.Series(50.0, index=pd.bdate_range("2026-01-05", "2026-11-20"))
        up = cx.net_liquidity(walcl, pd.Series(np.linspace(900_000, 800_000, len(w)), index=w), rrp)
        self.assertEqual(up["direction"], "in aumento")
        self.assertEqual(up["value_bn"], round((6_740_000 - 800_000 - 50_000) / 1000))
        dn = cx.net_liquidity(walcl, pd.Series(np.linspace(700_000, 900_000, len(w)), index=w), rrp)
        self.assertEqual(dn["direction"], "in calo")
        self.assertGreater(up["chg13_pct"], 0)
        self.assertLess(dn["chg13_pct"], 0)

    def test_cpi_annuo_e_mese_mancante(self):
        c = cx.cpi(fred_ok()["CPIAUCSL"])
        self.assertEqual((c["yoy"], c["month"], c["prev"], c["direction"]), (3.5, "10/2026", 3.0, "in salita"))
        s = fred_ok()["CPIAUCSL"].drop(pd.Timestamp("2025-10-01"))            # 10/2025 non pubblicato: 10/2026 non calcolabile
        c = cx.cpi(s)
        self.assertEqual((c["yoy"], c["month"], c["direction"], c["published"]), (3.0, "09/2026", "ferma", "2026-10-01"))

    def test_prossima_riunione(self):
        self.assertEqual(cx.next_fomc(BANKS, NOW), "2026-12-09")
        self.assertEqual(cx.next_fomc(BANKS, pd.Timestamp("2026-12-10")), "2027-01-27")
        self.assertIsNone(cx.next_fomc([], NOW))


class TestRiquadro(unittest.TestCase):
    def build(self, d, fetch, now=NOW, banks=BANKS, spot=True):
        if spot and not (Path(d) / "spot.csv").exists():
            write_spot(Path(d), pd.Series(np.r_[np.full(400, 100.0), np.linspace(100, 60, 300)], index=days(700)))
        return cx.build(Path(d), banks=banks, fetch=fetch, now=now)

    def test_righe_e_dicitura_fissa(self):
        with tempfile.TemporaryDirectory() as d:
            o = self.build(d, fetcher(fred_ok()))
        self.assertEqual(cx.NOTE, NOTE)
        self.assertEqual(o["note"], NOTE)
        self.assertEqual([r["label"] for r in o["rows"]], ["Mercato", "Fed", "Dati"])
        self.assertLessEqual(len(o["rows"]) + 2, 6)                             # titolo + righe + dicitura: al massimo 6
        self.assertRegex(o["rows"][0]["text"], r"^ribasso, prezzo −\d+,\d% dalla media a 200 giorni · volatilità (alta|bassa)$")
        self.assertEqual(o["rows"][1]["text"], "tasso 3,88% in rialzo (+0,25 il 17/09) · bilancio stabile · liquidità in aumento")
        self.assertEqual(o["rows"][2]["text"], "CPI annuo 3,5% in salita (10/2026) · VIX 28,4 · FOMC 09/12")
        self.assertIsNone(o["warn"])
        self.assertIn("ultima mossa +0,25 il 17/09/2026", texts(o))
        self.assertIn("09/12/2026", texts(o))
        json.dumps(o)                                                           # serializzabile nel report

    def test_nessuna_probabilita(self):
        with tempfile.TemporaryDirectory() as d:
            o = self.build(d, fetcher(fred_ok()))
        t = texts(o).lower()
        for w in ("probabilit", "prevision", "previst", "attes", "in media", "storicamente", "rialzi a", "episodi"):
            self.assertNotIn(w, t, w)
        # i soli "%" ammessi: distanza dalla media, tasso, variazioni a 13 settimane, volatilità, CPI
        for r in o["rows"] + o["details"]:
            if "%" in (r["text"] + str(r.get("value", ""))):
                self.assertIn(r["label"], ("Mercato", "Fed", "Dati", "Trend", "Volatilità", "Tasso Fed", "Bilancio Fed", "Liquidità netta",
                                           "Inflazione CPI"), r)
        self.assertNotIn("%", o["note"])
        keys = re.findall(r'"(\w+)":', json.dumps(o))
        self.assertFalse([k for k in keys if re.search(r"prob|forecast|expected|h7|h30|base_rate", k)])

    def test_fonte_assente_senza_cache(self):
        with tempfile.TemporaryDirectory() as d:
            o = self.build(d, broken)                                           # solo mercato e riunione: nessuna eccezione
            self.assertEqual([r["label"] for r in o["rows"]], ["Mercato", "Dati"])
            self.assertEqual(o["rows"][1]["text"], "FOMC 09/12")
            self.assertEqual(o["note"], NOTE)
            self.assertIsNone(self.build(tempfile.mkdtemp(), broken, banks=[], spot=False))

    def test_fonte_caduta_usa_cache_con_data(self):
        with tempfile.TemporaryDirectory() as d:
            first = self.build(d, fetcher(fred_ok()))
            calls = []

            def down(sid, today):
                calls.append(sid)
                raise ConnectionError("giù")
            o = self.build(d, down, now=NOW + pd.Timedelta(days=1), banks=[])
            self.assertEqual(o["rows"][1]["text"], first["rows"][1]["text"])    # ultimo dato in cache
            self.assertEqual(calls, ["DFF"])                                    # dopo il primo errore non insiste nel giro
            self.assertIn("tasso (dato del 19/11)", o["warn"])
            self.assertIn("VIX (dato del 19/11)", o["warn"])
            self.assertIn("FOMC 09/12", o["rows"][2]["text"])                   # riunione dalla cache

    def test_dato_vecchio_con_data(self):
        with tempfile.TemporaryDirectory() as d:
            o = self.build(d, fetcher(fred_ok(end="2026-10-30")), banks=[])     # la fonte risponde ma è ferma al 30/10
            self.assertIn("tasso (dato del 30/10)", o["warn"])
            self.assertIn("bilancio (dato del 28/10)", o["warn"])
            self.assertIn("tasso effettivo del 30/10", texts(o))

    def test_una_volta_al_giorno(self):
        with tempfile.TemporaryDirectory() as d:
            calls = []
            self.build(d, fetcher(fred_ok(), calls))
            self.build(d, fetcher(fred_ok(), calls))
            self.assertEqual(calls, list(cx.SERIES))
            self.build(d, fetcher(fred_ok(), calls), now=NOW + pd.Timedelta(days=1))
            self.assertEqual(len(calls), 2 * len(cx.SERIES))

    def test_cache_illeggibile(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / cx.FILE).write_text("non,un\ncsv valido")
            self.assertIsNotNone(self.build(d, broken))


class TestRete(unittest.TestCase):
    def test_requests_poi_curl(self):
        """requests che fallisce (proxy locale) → curl; entrambi falliti → eccezione, assorbita da build."""
        import subprocess
        from unittest import mock

        class P:
            returncode, stdout, stderr = 0, "observation_date,DFF\n2026-11-18,3.88\n2026-11-19,.\n", ""
        with mock.patch("requests.get", side_effect=ConnectionError("proxy")), mock.patch.object(cx.shutil, "which", return_value="/usr/bin/curl"), \
                mock.patch.object(subprocess, "run", return_value=P()) as run:
            s = cx.fetch_fred("DFF", NOW)
            self.assertEqual((len(s), float(s.iloc[-1])), (1, 3.88))            # "." scartato
            self.assertEqual(run.call_args[0][0][0], "curl")
        with mock.patch("requests.get", side_effect=ConnectionError("proxy")), mock.patch.object(cx.shutil, "which", return_value=None):
            self.assertRaises(ConnectionError, cx.fetch_fred, "DFF", NOW)


class TestIntegrazione(unittest.TestCase):
    def test_dashboard_e_giro(self):
        root = Path(__file__).resolve().parents[1]
        t = (root / "radar" / "dashboard_template.html").read_text()
        self.assertIn('id="ogCtx"', t)   # variante B: tessera "contesto" in Oggi
        self.assertIn("R.context", t)
        blk = t[t.index("(function renderContext()"):t.index("function renderToday()")]
        self.assertNotRegex(blk.lower(), r"probabilit|prevision")
        cli = (root / "radar" / "cli.py").read_text()
        self.assertIn('report["context"] = _soft(', cli)

    def test_nessun_effetto_su_w3(self):
        root = Path(__file__).resolve().parents[1]
        for f in ("weekly.py", "strategy.py", "preview.py", "guard.py"):
            self.assertNotRegex((root / "radar" / f).read_text(), r"\bcontext\b\s*(import|\.build)|from \.context|report\[.context.\]", f)


if __name__ == "__main__":
    unittest.main()
