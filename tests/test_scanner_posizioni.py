"""Scanner · "Monete in posizione" (#scPos, variante 1 a righe scelta dall'utente il 27/11/2026; anteprima in
stato/ux-varianti/scanner): riepilogo long/short con risultato medio dall'ingresso, righe espandibili con il perché del verso
(semafori), avviso "segnale non verificato" per le monete senza storia sufficiente, filtro e ordinamento. Lo scanner pubblica in
cond anche fund7 e dist (stesse formule di weekly_bars) così il semaforo Funding/distribuzione non resta grigio."""
import functools
import http.server
import json
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

from radar import scanner as SC
from radar import weekly as W

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()


def cond(regime, flow=0.5, fund7=0.0001, dist=None, px=1, ema=1):
    c = {"px_sma": px, "ema20": px, "sma_dn": px < 0, "ema21": ema, "flow": flow, "f1": True, "macd": False, "eta": 3,
         "regime": regime, "c_long": False, "c_short": False, "dsma": 12.0 * px}
    if fund7 is not None:
        c["fund7"] = fund7
        c["dist"] = dist or {"long": False, "short": False}
    return c


def riga(t, lato, rk, mv=None, cl="valutabile", **kw):
    r = {"t": t, "n": t.title(), "cl": cl, "rk": rk, "bg": True, "ok": True, "q": None, "lato": lato, "evento": None,
         "btc": "stesso", "ult": 2.0}
    if mv is not None:
        r.update(ing="2026-11-02", sig="2026-11-01", sett=3, px_in=1.8, trail=1.5 if lato == "long" else 2.6, mv=mv,
                 du=25.0 if lato == "long" else 30.0)
    r.update(kw)
    return r


RIGHE = [
    riga("BTC", "short", 1, mv=6.0, btc=None, cond=cond("short", flow=-0.4, px=-1, ema=-1)),
    riga("AAA", "long", 10, mv=10.0, cond=cond("long")),
    riga("BBB", "long", 20, mv=20.0, cl="breve", cond=cond("long", flow=-0.3, fund7=None)),
    riga("CCC", "short", 5, mv=-5.0, btc="opposto", cond=cond("short", flow=-0.2, fund7=-0.0005, px=-1, ema=-1)),
    riga("NEW", "short", 30, evento="ingresso", sig="2026-11-22", sett=0, cond=cond("short", flow=-0.6, px=-1, ema=-1)),
    riga("FLT", "flat", 3, cond=cond("neutro")),
]
REPORT = {"date": "2026-11-25", "price": 1.0,
          "scanner": {"settimana": "2026-11-22", "calcolato": "2026-11-24T06:00", "n": len(RIGHE), "righe": RIGHE,
                      "conteggi": {"long": 2, "short": 3, "flat": 1, "nd": 0}, "nuovi": ["NEW"], "uscite": [], "btc": "short",
                      "finestra_giorni": 1000, "dati": {}}}


class Markup(unittest.TestCase):
    def test_blocco_e_codice(self):
        v = T[T.index('<div class="view" id="v-scanner"'):T.index("<!-- ============ GRAFICO")]
        self.assertIn('<div id="scPos"></div>', v)
        self.assertLess(v.index('id="scIng"'), v.index('id="scPos"'))
        self.assertLess(v.index('id="scPos"'), v.index('id="scBet"'))
        js = T[T.index("// ---- Monete in posizione"):T.index("// ---- Scommesse sulla carta")]
        self.assertNotIn("VAR", js)                       # solo la variante 1: niente ramo delle tessere
        self.assertNotIn("pzGrid", T)
        self.assertNotRegex(T, r"pzTile\b")              # (pzTiles = tessere del riepilogo, restano)
        for w in ("Long aperti", "Short aperti", "Non verificati", "non un segnale provato sulle altcoin",
                  "segnale non verificato: storia insufficiente", "Funding medio 7 giorni", "Mostra tutte"):
            self.assertIn(w, js)


class Condizioni(unittest.TestCase):
    def test_fund7_e_dist_come_weekly_bars(self):
        from tests.test_scanner import serie
        df = serie(drift=-1.0, seed=3, p0=50.0)                       # flusso perp negativo
        f = SC.feats(df, df, pd.DataFrame({"funding": 0.002}, index=df.index))   # funding caldo: distribuzione dei long
        w = W.weekly_bars(f)
        c = SC.condizioni(w)
        self.assertEqual(c["fund7"], round(float(w["fund7"].iloc[-1]), 6))
        self.assertEqual(c["dist"], {"long": bool(w["dist_long"].iloc[-1]), "short": bool(w["dist_short"].iloc[-1])})
        self.assertTrue(c["dist"]["long"])
        self.assertFalse(c["dist"]["short"])
        json.dumps(c)                                                 # tipi pubblicabili (niente numpy.bool_)
        st = SC.stato_moneta(f, date(2026, 11, 22))
        self.assertIn("fund7", st["cond"])
        self.assertIn("dist", st["cond"])

    def test_fund7_assente(self):
        from tests.test_scanner import serie
        df = serie(seed=2)
        w = W.weekly_bars(SC.feats(df, df, pd.DataFrame({"funding": 0.0001}, index=df.index)))
        w.loc[w.index[-1], "fund7"] = float("nan")
        c = SC.condizioni(w)
        self.assertIsNone(c["fund7"])
        self.assertEqual(c["dist"], {"long": False, "short": False})


class NelBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("playwright non installato")
        from radar.dashboard import render
        cls.tmp = tempfile.TemporaryDirectory()
        render(REPORT, Path(cls.tmp.name) / "index.html")

        class Q(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a):
                pass
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Q, directory=cls.tmp.name))
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        try:
            cls.p = sync_playwright().start()
            cls.b = cls.p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            cls.srv.shutdown()
            cls.srv.server_close()
            raise unittest.SkipTest(f"chromium non disponibile: {e}")

    @classmethod
    def tearDownClass(cls):
        cls.b.close()
        cls.p.stop()
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.tmp.cleanup()

    def pagina(self, w):
        pg = self.b.new_page(viewport={"width": w, "height": 900})
        self.errs = []
        pg.on("pageerror", lambda e: self.errs.append(str(e)))
        pg.route("**/*", lambda r: r.continue_() if "127.0.0.1" in r.request.url else r.abort())
        pg.goto(f"http://127.0.0.1:{self.srv.server_port}/index.html#scanner", wait_until="networkidle")
        pg.wait_for_selector("#scPos .pzRow", timeout=5000)
        return pg

    def righe(self, pg):
        return pg.eval_on_selector_all("#scPos .pzRow", "els => els.map(e => e.dataset.t)")

    def test_riepilogo_semafori_avviso(self):
        pg = self.pagina(400)
        tiles = pg.inner_text("#scPos .pzTiles")
        self.assertIn("Long aperti\n2", tiles)
        self.assertIn("+15,0%", tiles)                                # media dei long aperti (10 e 20)
        self.assertIn("Short aperti\n2", tiles)                       # BTC e CCC aperti, NEW nuovo
        self.assertIn("+1 nuovi", tiles)
        self.assertIn("+0,5%", tiles)                                 # media degli short aperti (6 e −5)
        self.assertNotIn("FLT", self.righe(pg))                       # solo monete in posizione
        # moneta con storia breve: punto arancio nella riga e avviso nella riga aperta
        self.assertEqual(pg.eval_on_selector_all("#scPos .pzRow .pzDot", "els => els.map(e => e.closest('.pzRow').dataset.t)"), ["BBB"])
        pg.evaluate("document.querySelector('#scPos .pzRow[data-t=BBB]').open = true")
        bbb = pg.inner_text("#scPos .pzRow[data-t=BBB] .pzOpen")
        self.assertIn("segnale non verificato: storia insufficiente", bbb)
        sem = pg.eval_on_selector_all("#scPos .pzRow[data-t=BBB] .pzSem li", "els => els.map(e => e.className)")
        self.assertEqual(sem, ["ok", "ok", "wa", "nd", "ok"])         # flusso contrario = arancio, funding assente = grigio
        self.assertNotIn("non verificato", pg.inner_text("#scPos .pzRow[data-t=AAA] .pzOpen"))
        # funding presente: semaforo acceso, testo del funding medio
        sem = pg.eval_on_selector_all("#scPos .pzRow[data-t=CCC] .pzSem li", "els => els.map(e => e.className)")
        self.assertEqual(sem[3], "ok")
        self.assertIn("Funding medio 7 giorni −0,050% al giorno", pg.text_content("#scPos .pzRow[data-t=CCC] .pzSem"))
        self.assertEqual(self.errs, [])
        sw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        self.assertEqual(sw[0], sw[1])
        pg.close()

    def test_distribuzione_rossa(self):
        rep = json.loads(json.dumps(REPORT))
        rep["scanner"]["righe"][1]["cond"]["dist"] = {"long": True, "short": False}
        from radar.dashboard import render
        with tempfile.TemporaryDirectory() as t:
            html = render(rep, Path(t) / "i.html").read_text()
            sc = json.loads((Path(t) / "scanner.json").read_text())
        self.assertIn('"scanner": "scanner.json?v=', html)
        self.assertEqual(sc["scanner"]["righe"][1]["cond"]["dist"], {"long": True, "short": False})
        js = T[T.index("// ---- Monete in posizione"):T.index("// ---- Scommesse sulla carta")]
        self.assertIn('const dist = c.dist ? !!c.dist[r.lato]', js)   # usa il campo dello scanner quando c'è
        self.assertIn('c: dist ? "no" : "ok"', js)

    def test_filtro_e_ordinamento(self):
        pg = self.pagina(1280)
        self.assertEqual(self.righe(pg), ["BBB", "AAA", "BTC", "CCC", "NEW"])   # risultato decrescente, nuovi in fondo
        pg.click("#pzF button[data-v=long]")
        self.assertEqual(self.righe(pg), ["BBB", "AAA"])
        pg.click("#pzF button[data-v=short]")
        self.assertEqual(self.righe(pg), ["BTC", "CCC", "NEW"])
        pg.click("#pzO button[data-v=cap]")
        self.assertEqual(self.righe(pg), ["BTC", "CCC", "NEW"])
        pg.click("#pzF button[data-v=tutte]")
        self.assertEqual(self.righe(pg), ["BTC", "CCC", "AAA", "BBB", "NEW"])   # per capitalizzazione
        self.assertEqual(pg.get_attribute("#pzO button[data-v=cap]", "aria-pressed"), "true")
        self.assertEqual(self.errs, [])
        pg.close()


if __name__ == "__main__":
    unittest.main()
