"""Ciclo on-chain (radar/onchain.py, scheda nella pagina Posizioni): zone e soglie solo sul passato, stato e "da quando",
statistiche dopo gli ingressi, ripiego senza rete, frase per verso × zona, scheda nella pagina. Niente rete (fetch finto)."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from radar import onchain as O
from radar.dashboard import render

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()


def serie(n=2200, end="2026-11-24", seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(end=end, periods=n, freq="D")
    return pd.Series(1.8 + 0.5 * np.sin(np.arange(n) / 160) + rng.normal(0, .02, n), index=idx, name="mvrv")


def fake_http(s, pages=2):
    """Risposte della community API divise in `pages` pagine con next_page_token."""
    rows = [{"asset": "btc", "time": f"{d:%Y-%m-%d}T00:00:00.000000000Z", "CapMVRVCur": f"{v:.6f}"} for d, v in s.items()]
    k = -(-len(rows) // pages)
    calls = []

    def http(url, params):
        calls.append(dict(params))
        i = int(params.get("next_page_token", 0))
        out = {"data": rows[i * k:(i + 1) * k]}
        if (i + 1) * k < len(rows):
            out["next_page_token"] = str(i + 1)
        return json.dumps(out)
    http.calls = calls
    return http


def down(url, params):
    raise ConnectionError("rete giù")


class TestZone(unittest.TestCase):
    def test_soglie_solo_sul_passato(self):
        m = serie()
        z = O.zones(m)
        d = m.index[1600]
        prev = m[m.index < d].iloc[-1460:]
        self.assertAlmostEqual(z.loc[d, "lo"], prev.quantile(.10), places=9)
        self.assertAlmostEqual(z.loc[d, "hi"], prev.quantile(.90), places=9)
        self.assertTrue(z["zone"].iloc[:1460].isna().all())   # meno di 4 anni di passato: nessuna zona
        # il futuro non cambia il passato: zone identiche tagliando la serie
        cut = O.zones(m[m.index <= d])
        pd.testing.assert_frame_equal(cut, z[z.index <= d])

    def test_giorno_stesso_escluso(self):
        m = serie()
        m.iloc[-1] = 0.2   # crollo oggi: non deve abbassare la soglia di oggi
        z = O.zones(m)
        self.assertAlmostEqual(z["lo"].iloc[-1], m.iloc[-1461:-1].quantile(.10), places=9)
        self.assertEqual(z["zone"].iloc[-1], "cap")

    def test_stato_e_da_quando(self):
        z = pd.Series(["norm"] * 5 + ["cap", "norm", "cap", "cap", "cap"], index=pd.date_range("2026-11-10", periods=10))
        self.assertEqual(O.since(z), pd.Timestamp("2026-11-17"))
        self.assertEqual(O.since(pd.Series(["eup"] * 3, index=pd.date_range("2026-01-01", periods=3))), pd.Timestamp("2026-01-01"))


class TestStatistiche(unittest.TestCase):
    def test_ingressi_e_rendimenti(self):
        idx = pd.date_range("2015-06-01", "2020-12-31")
        z = pd.Series("norm", index=idx)
        for a, b in (("2015-08-01", "2015-08-10"), ("2017-01-10", "2017-01-20"), ("2017-02-05", "2017-02-08"),
                     ("2018-05-01", "2018-05-03"), ("2020-12-20", "2020-12-25")):
            z[a:b] = "cap"
        px = pd.Series(100.0, index=idx)
        px["2017-02-09":] = 120.0                      # +20% a 30 giorni dal 10/01/2017
        px["2017-04-10":] = 150.0
        px["2018-05-31":] = 90.0                       # 2018: 150 → 90 a 30 giorni (−40%)
        ev = O.entries(z, "cap")
        # 2015 escluso (prima del 2016); 05/02/2017 è lo stesso episodio del 10/01 (meno di 30 giorni fuori zona)
        self.assertEqual([d.strftime("%Y-%m-%d") for d in ev], ["2017-01-10", "2018-05-01", "2020-12-20"])
        s = O.stats(z, px, "cap")
        self.assertEqual(s["n_entries"], 3)
        self.assertEqual(s["d30"]["n"], 2)             # 20/12/2020 senza 30 giorni di prezzi: fuori
        self.assertEqual(s["d30"]["max"], 20.0)
        self.assertEqual(s["d30"]["min"], -40.0)
        self.assertEqual(s["d30"]["median"], -10.0)
        self.assertEqual(s["d30"]["up"], 1)
        self.assertEqual(s["d90"]["max"], 50.0)        # 10/01 → 10/04/2017
        self.assertIsNone(s["episodes"][-1]["d90"])


class TestFonteERipiego(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.today = pd.Timestamp("2026-11-25")

    def tearDown(self):
        self.tmp.cleanup()

    def test_scarica_pagine_salva_5_anni_e_non_riscrive(self):
        m = serie()
        http = fake_http(m, pages=3)
        full, note = O.load(self.dir, http=http, today=self.today, study=None)
        self.assertEqual(len(http.calls), 3)
        self.assertIsNone(note)
        self.assertEqual(len(full), len(m))
        saved = pd.read_csv(self.dir / O.FILE)
        self.assertLessEqual(len(saved), O.KEEP_DAYS)
        self.assertEqual(saved["date"].iloc[-1], "2026-11-24")
        mt = (self.dir / O.FILE).stat().st_mtime_ns
        O._save(full, self.dir / O.FILE)                # stesso contenuto: il file non si tocca
        self.assertEqual((self.dir / O.FILE).stat().st_mtime_ns, mt)
        # dato di ieri già in cache: nessuna chiamata
        http2 = fake_http(m)
        O.load(self.dir, http=http2, today=self.today, study=None)
        self.assertEqual(http2.calls, [])

    def test_senza_rete_usa_cache_e_storia_dello_studio(self):
        m = serie(end="2026-11-20")
        study = self.dir / "studio.csv"
        pd.DataFrame({"date": m.index.strftime("%Y-%m-%d"), "mvrv": m.to_numpy()}).to_csv(study, index=False)
        O._save(m, self.dir / O.FILE)
        full, note = O.load(self.dir, http=down, today=self.today, study=study)
        self.assertEqual(len(full), len(m))             # cache (5 anni) + storia dello studio per il resto
        self.assertIn("20/11/2026", note)
        r = O.build(self.dir, side="short", http=down, today=self.today, study=study, old_prices=None)
        self.assertEqual(r["date"], "2026-11-20")
        self.assertIn("CoinMetrics non risponde", r["source_note"])

    def test_senza_rete_e_senza_cache_solleva(self):
        with self.assertRaises(ConnectionError):
            O.load(self.dir, http=down, today=self.today, study=None)

    def test_build_compatto(self):
        r = O.build(self.dir, side="long", http=fake_http(serie()), today=self.today, study=None, old_prices=None)
        self.assertIn(r["zone"], ("cap", "norm", "eup"))
        self.assertLessEqual(len(r["series"]["v"]), O.CHART_DAYS)
        self.assertEqual(len(r["series"]["d"]), len(r["series"]["lo"]))
        self.assertTrue(0 <= r["pctile"] <= 100)
        self.assertEqual(r["frase"], O.frase("long", r["zone"]))
        self.assertLess(len(json.dumps(r)), 60000)


class TestFrase(unittest.TestCase):
    def test_quattro_casi_e_neutri(self):
        sc = O.frase("short", "cap")
        self.assertIn("capitolazione", sc)
        self.assertIn("rimbalzo", sc)
        self.assertIn("lezione 125", sc)
        self.assertIn("regole di W3.2", sc)
        le = O.frase("long", "eup")
        self.assertIn("euforia", le)
        self.assertIn("inizio dei rally", le)
        self.assertIn("dannoso", le)
        lc, se = O.frase("long", "cap"), O.frase("short", "eup")
        self.assertIn("capitolazione", lc)
        self.assertIn("W3.2", lc)
        self.assertIn("euforia", se)
        self.assertIn("W3.2", se)
        self.assertEqual(len({sc, le, lc, se}), 4)
        for side in ("long", "short", None):
            self.assertIn("normale", O.frase(side, "norm"))
        self.assertLess(len(O.frase("short", "norm")), len(sc))

    def test_verso_della_posizione(self):
        self.assertEqual(O.side_of({"status": "aperto", "side": "short"}), "short")
        self.assertEqual(O.side_of({"status": "uscita", "side": "long"}), "long")
        self.assertIsNone(O.side_of({"status": "flat", "side": "long"}))
        self.assertIsNone(O.side_of(None))


class TestScheda(unittest.TestCase):
    def test_scheda_nel_template(self):
        self.assertIn('<div class="oc" id="ocBox" hidden></div>', T)   # nella card della posizione di BTC
        self.assertIn('id="ocSec" hidden', T)                         # da flat: card compatta in fondo a Posizioni
        self.assertIn("function renderOnchain", T)
        self.assertIn("R.onchain", T)
        self.assertIn(":root[data-theme=\"dark\"]", T)
        i = T.index('id="v-posizioni"')
        self.assertLess(i, T.index('id="ocSec"'), T.index('id="v-opzioni"'))

    def test_pagina_con_i_dati(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        r = O.build(Path(tmp.name), side="short", http=fake_http(serie()), today=pd.Timestamp("2026-11-25"), study=None,
                    old_prices=None)
        out = render({"date": "2026-11-24", "onchain": r}, out=Path(tmp.name) / "index.html", standalone=False)
        html = out.read_text()
        self.assertIn('"onchain"', html)
        self.assertIn(O.NOTE, html)


if __name__ == "__main__":
    unittest.main()
