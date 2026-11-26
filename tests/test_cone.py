"""Card "Fra 30 giorni" (radar/cone.py): valori noti, seme stabile, registro idempotente, dicitura fissa, nessuna frase di direzione."""
import json
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from radar import cone

ROOT = Path(__file__).resolve().parents[1]
NOTE = ("Probabilità calcolate dalla volatilità attuale, non dalla direzione: il tool non sa prevedere se BTC salirà o scenderà "
        "(lezioni 112–113). Affidabilità storica: intervallo 80% centrato nel 78% dei casi.")


def ohlc(n=900, seed=1, vol=0.03, end="2026-11-21", symmetric=False):
    rng = np.random.default_rng(seed)
    r = rng.standard_t(4, n) * vol / np.sqrt(2)
    if symmetric:                       # storia speculare: ogni rendimento compare con i due segni
        r = np.concatenate([r[: n // 2], -r[: n // 2]])
    c = 50_000 * np.exp(np.cumsum(r - r.mean()))
    o = np.r_[c[0], c[:-1]]
    w = 0 if symmetric else np.abs(rng.normal(0, vol / 3, len(c)))
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * np.exp(w), "low": np.minimum(o, c) * np.exp(-w), "close": c},
                        index=pd.date_range(end=end, periods=len(c)))


WEEKLY = {"status": "aperto", "side": "short", "trail": 75763.76, "stop0": 82163.3, "flow": -1.53}
LEVELS = {"supports": [{"price": 61185.0}, {"price": 56410.0}, {"price": 47995.0}],
          "resistances": [{"price": 61900.0}, {"price": 67197.0}, {"price": 74552.0}]}


class Calcolo(unittest.TestCase):
    def test_volatilita_nulla_intervallo_degenere(self):
        f = pd.DataFrame({"high": 60_000.0, "low": 60_000.0, "close": 60_000.0}, index=pd.date_range("2024-01-01", periods=500))
        c = cone.compute(f)
        self.assertEqual(c["i80"], [60_000.0, 60_000.0])
        self.assertEqual(c["i50"], [60_000.0, 60_000.0])
        self.assertEqual(c["vol30_pct"], 0.0)
        self.assertTrue(all(o["prob"] == 0 for o in c["levels"]))      # nessun livello raggiungibile senza volatilità

    def test_tocco_monotono_nella_distanza(self):
        p = cone.prepare(ohlc())
        end, mx, mn = cone.simulate(p["zr"], p["zu"], p["zd"], p["sigma"], p["drift"])
        up = [cone.touch_prob(mx, mn, 100, 100 * (1 + x)) for x in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5)]
        dn = [cone.touch_prob(mx, mn, 100, 100 * (1 - x)) for x in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5)]
        for seq in (up, dn):
            self.assertTrue(all(a >= b for a, b in zip(seq, seq[1:])), seq)
            self.assertGreater(seq[0], seq[-1])
        self.assertEqual(cone.touch_prob(mx, mn, 100, 100), 1.0)

    def test_intervalli_annidati_e_prezzo_dentro(self):
        c = cone.compute(ohlc())
        self.assertLess(c["i80"][0], c["i50"][0])
        self.assertLess(c["i50"][0], c["i50"][1])
        self.assertLess(c["i50"][1], c["i80"][1])
        self.assertTrue(c["i80"][0] < c["price"] < c["i80"][1])

    def test_simmetria_senza_deriva(self):
        p = cone.prepare(ohlc(n=2000, symmetric=True))
        end, mx, mn = cone.simulate(p["zr"], p["zu"], p["zd"], p["sigma"], drift=0.0, n_paths=40_000)
        lo, hi = cone.interval(end, 100.0, 0.8)
        self.assertAlmostEqual(np.log(hi / 100), -np.log(lo / 100), delta=0.012)        # intervallo simmetrico in logaritmo
        for x in (0.1, 0.2):
            su, giu = cone.touch_prob(mx, mn, 100, 100 * np.exp(x)), cone.touch_prob(mx, mn, 100, 100 * np.exp(-x))
            self.assertAlmostEqual(su, giu, delta=0.02)

    def test_volatilita_piu_alta_cono_piu_largo(self):
        a, b = cone.compute(ohlc(vol=0.02)), cone.compute(ohlc(vol=0.04))
        self.assertGreater(b["i80"][1] / b["i80"][0], a["i80"][1] / a["i80"][0])

    def test_seme_stabile(self):
        f = ohlc()
        a, b = cone.compute(f, WEEKLY, LEVELS), cone.compute(f, WEEKLY, LEVELS)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        p = cone.prepare(f)
        x, y = cone.simulate(p["zr"], p["zu"], p["zd"], p["sigma"]), cone.simulate(p["zr"], p["zu"], p["zd"], p["sigma"])
        self.assertTrue(all(np.array_equal(i, j) for i, j in zip(x, y)))
        self.assertEqual(cone.SEED, 20261123)

    def test_storia_corta_errore_esplicito(self):
        with self.assertRaises(ValueError):
            cone.prepare(ohlc(n=200))

    def test_stesso_metodo_dello_studio(self):
        """Dati congelati dello studio: il modulo riproduce gli intervalli del metodo scelto (b) entro il rumore del campionamento."""
        d = pd.read_csv(ROOT / "research/p2_nuovi/data/f_long.csv.gz", index_col=0, parse_dates=True)
        P = pd.read_csv(ROOT / "research/cono30/previsioni.csv.gz", index_col=0, parse_dates=True)
        for day in ("2020-03-01", "2024-06-01", "2026-10-16"):
            c = cone.compute(d.loc[:day])
            self.assertAlmostEqual(c["i80"][0] / P.loc[day, "b_q10"], 1, delta=0.02)
            self.assertAlmostEqual(c["i80"][1] / P.loc[day, "b_q90"], 1, delta=0.02)


class Livelli(unittest.TestCase):
    def test_livelli_scelti(self):
        lv = cone.pick_levels(60_215.77, WEEKLY, LEVELS)
        self.assertEqual([(o["label"], o["price"]) for o in lv],
                         [("Trailing W3.2", 75763.76), ("Numero tondo", 70000.0), ("Resistenza", 67197.0),
                          ("Supporto", 56410.0), ("Numero tondo", 50000.0)])       # 61.185 e 61.900 sono a meno del 3%: esclusi

    def test_senza_posizione_niente_trailing(self):
        lv = cone.pick_levels(60_215.77, {"status": "piatto", "trail": None}, None)
        self.assertEqual([o["price"] for o in lv], [70000.0, 50000.0])

    def test_numeri_tondi(self):
        self.assertEqual(cone.round_levels(61_000), [50_000, 70_000])
        self.assertEqual(cone.round_levels(98_000), [90_000, 110_000])
        self.assertEqual(cone.round_levels(30_000), [25_000, 35_000])

    def test_card_completa(self):
        c = cone.compute(ohlc(), WEEKLY, LEVELS)
        self.assertEqual(c["title"], "Fra 30 giorni")
        self.assertEqual(c["target"], "2026-12-21")
        self.assertLessEqual(len(c["levels"]), 5)
        for o in c["levels"]:
            self.assertTrue(0 <= o["prob"] <= 100)
            self.assertEqual(o["side"], "su" if o["price"] > c["price"] else "giu")

    def test_righe_descrittive(self):
        rows = cone.describe(WEEKLY, {"nearest_above": {"price": 62197.0, "dist_pct": 1.47}, "nearest_below": {"price": 60061.0, "dist_pct": -2.02}})
        self.assertEqual(rows[0], {"label": "Flusso perp", "text": "in vendita (−1,5)"})
        self.assertEqual(rows[1], {"label": "Liquidazioni", "text": "fascia stimata più vicina a 62.197 $ (+1,5%) · stima"})
        self.assertEqual(cone.describe(None, None), [])
        self.assertEqual(cone.describe({"flow": None}, {"nearest_above": None}), [])


class Testi(unittest.TestCase):
    def test_dicitura_fissa(self):
        self.assertEqual(cone.NOTE, NOTE)
        self.assertEqual(cone.compute(ohlc())["note"], NOTE)
        readme = (ROOT / "research/cono30/README.md").read_text()
        self.assertIn("78,2%", readme)                                    # il numero della dicitura è quello dello studio

    def test_nessuna_frase_di_direzione(self):
        f = ohlc()
        with tempfile.TemporaryDirectory() as t:
            c = cone.build(f, {"weekly": WEEKLY, "levels": LEVELS}, Path(t))
        txt = json.dumps(c, ensure_ascii=False).lower()
        for bad in ("andrà", "arriverà", "target", "obiettivo di prezzo"):
            self.assertNotIn(bad, txt.replace('"target":', ""))
        tpl = (ROOT / "radar/dashboard_template.html").read_text()
        blk = tpl[tpl.index("(function renderCone()"):tpl.index("// Contesto (report.context")]
        self.assertNotRegex(blk.lower(), r"andrà|arriverà|salirà a|scenderà a")
        self.assertIn('id="ogCone"', tpl)   # variante B: tessera "BTC fra 30 giorni" in Oggi

    def test_non_tocca_w32(self):
        src = (ROOT / "radar/weekly.py").read_text()
        self.assertNotIn("cone", src)
        w = dict(WEEKLY)
        cone.compute(ohlc(), w, LEVELS)
        self.assertEqual(w, WEEKLY)


class Registro(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name) / cone.LOG
        self.addCleanup(self.tmp.cleanup)

    def test_idempotente_senza_doppioni(self):
        f = ohlc()
        c = cone.compute(f)
        for _ in range(3):
            cone.update_log(self.p, c, f["close"])
        a = self.p.read_text()
        log = pd.read_csv(self.p)
        self.assertEqual(len(log), 1)
        self.assertEqual(list(log.columns), cone.LOG_COLS)
        cone.update_log(self.p, dict(c, price=1.0, i80=[1, 2]), f["close"])      # stessa data: resta la prima previsione
        self.assertEqual(self.p.read_text(), a)

    def test_esito_a_scadenza(self):
        f = ohlc()
        c = cone.compute(f.iloc[:-30])
        live = cone.update_log(self.p, c, f["close"].iloc[:-30])
        self.assertEqual(live["n"], 0)
        live = cone.update_log(self.p, cone.compute(f), f["close"])
        log = pd.read_csv(self.p)
        self.assertEqual(len(log), 2)
        r = log.iloc[0]
        self.assertAlmostEqual(r["close30"], round(float(f["close"].iloc[-1]), 2))
        self.assertEqual(r["in80"], int(r["lo80"] <= r["close30"] <= r["hi80"]))
        self.assertEqual(live["n"], 1)
        self.assertTrue(pd.isna(log.iloc[1]["close30"]))
        b = self.p.read_text()
        cone.update_log(self.p, cone.compute(f), f["close"])
        self.assertEqual(self.p.read_text(), b)

    def test_registro_rotto_non_blocca(self):
        self.p.write_text("non,un,registro\n1,2\n\x00")
        f = ohlc()
        c = cone.build(f, {}, Path(self.tmp.name))
        self.assertEqual(c["live"]["n"], 0)
        self.assertEqual(len(pd.read_csv(self.p)), 1)
        self.assertTrue(self.p.with_suffix(".csv.bad").exists())
        self.assertEqual(cone.update_log(self.p / "sotto" / "x.csv", c, f["close"]), {"n": 0, "in80": 0, "in50": 0})   # percorso non scrivibile

    def test_build_con_storia_fissa(self):
        h = cone.history(ohlc(n=400, end="2026-11-21"))
        self.assertEqual(str(h.index[0].date()), "2014-01-01")
        self.assertTrue(h.index.is_monotonic_increasing and h.index.is_unique)
        self.assertEqual(len(cone.history(ohlc(n=400), seed_file=Path("/non/esiste.csv"))), 400)


if __name__ == "__main__":
    unittest.main()
