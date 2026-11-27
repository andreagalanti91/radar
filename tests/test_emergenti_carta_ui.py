"""Scanner · "Short emergenti sulla carta" (#scEmc, report.emergenti_carta di radar/emergenti_carta.py; registro V3 dal
30/11/2026, research/emergenti/PREREG-AVANTI-V3.md): stato, budget di carta, DD, chiuse/WR, posizioni aperte e chiuse, soglie di
rivalutazione, nota "solo carta". Senza R.emergenti_carta (o con un oggetto vuoto): "Il registro parte domenica 30/11"."""
import functools
import http.server
import json
import tempfile
import threading
import unittest
from pathlib import Path

from tests.test_scanner_posizioni import REPORT

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()

EC = {"inizio": "2026-11-30", "budget": 10000, "aggiornato": "2026-12-21", "valore": 10342.5, "dd": -4.8, "n_chiuse": 2, "wr": 50.0,
      "stato": "in raccolta", "lista": {"anno": 2026, "fonte": "CoinGecko", "n": 100},
      "soglie": {"min_chiuse": 20, "wr_min": 50, "dd_min": -25, "perdita_max": -10},
      "posizioni": [{"t": "ZRO", "ing": "2026-12-01", "px_in": 1.842, "ult": 1.611, "mv": 12.5, "trail": 2.304, "quota": 2000, "pnl": 11.92, "pnl_usd": 238.4},
                    {"t": "KAITO", "ing": "2026-12-08", "px_in": 0.9123, "ult": 0.9551, "mv": -4.7, "trail": 1.187, "quota": 2000, "pnl": -5.06, "pnl_usd": -101.2}],
      "chiuse": [{"t": "IP", "ing": "2026-12-01", "usc": "2026-12-08", "px_in": 3.12, "px_out": 3.61, "motivo": "stop mobile", "pnl": -16.58, "pnl_usd": -331.6},
                 {"t": "JTO", "ing": "2026-12-01", "usc": "2026-12-15", "px_in": 1.55, "px_out": 1.21, "motivo": "EMA 21", "pnl": 21.27, "pnl_usd": 425.3}]}


class Markup(unittest.TestCase):
    def test_posizione_e_testi(self):
        v = T[T.index('<div class="view" id="v-scanner"'):T.index("<!-- ============ GRAFICO")]
        self.assertLess(v.index('id="scPos"'), v.index('id="scEmc"'))
        self.assertLess(v.index('id="scEmc"'), v.index('id="scBet"'))
        js = T[T.index("// ---- Short emergenti sulla carta"):T.index("// ---- Scommesse sulla carta")]
        for w in ("Short emergenti sulla carta", "Il registro parte domenica", "Soglie di rivalutazione", "Solo carta, nessun ordine",
                  "studio non operabile (lezione 131)", "PREREG-AVANTI-V3.md"):
            self.assertIn(w, js)


class NelBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("playwright non installato")
        from radar.dashboard import render
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        iniziale = {"inizio": "2099-11-29", "budget": 10000.0, "settimana": None, "aggiornato": None, "posizioni": [], "chiuse": [],
                    "esclusi": [], "in_attesa": [], "valore": 10000.0, "rendimento": 0.0, "dd": 0.0, "n_chiuse": 0, "wr": None,
                    "stato": "in raccolta", "soglie": EC["soglie"], "lista": {"anno": 2099, "fonte": None, "n": 0}}   # _vuoto() di emergenti_carta
        partito = dict(iniziale, inizio="2020-11-01", settimana="2020-11-08", aggiornato="2020-11-09")   # data passata: registro già partito
        for nome, ec in (("pieno", EC), ("assente", None), ("vuoto", {}), ("iniziale", iniziale), ("partito", partito),
                         ("rivalutare", dict(EC, stato="rivalutare", n_chiuse=20, posizioni=[], esito="condizioni non tutte vere: il registro si chiude (decide l'utente)"))):
            rep = json.loads(json.dumps(REPORT))
            if ec is not None:
                rep["emergenti_carta"] = ec
            (d / nome).mkdir()
            render(rep, d / nome / "index.html")

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

    def apri(self, nome, w=400):
        pg = self.b.new_page(viewport={"width": w, "height": 900})
        self.errs = []
        pg.on("pageerror", lambda e: self.errs.append(str(e)))
        pg.route("**/*", lambda r: r.continue_() if "127.0.0.1" in r.request.url else r.abort())
        pg.goto(f"http://127.0.0.1:{self.srv.server_port}/{nome}/index.html?demo=1#scanner", wait_until="networkidle")
        pg.wait_for_selector("#scEmc .card", timeout=5000)
        return pg

    def fine(self, pg):
        self.assertEqual(self.errs, [])
        sw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        self.assertEqual(sw[0], sw[1])
        pg.close()

    def test_registro_pieno(self):
        for w in (360, 1280):
            pg = self.apri("pieno", w)
            t = pg.inner_text("#scEmc")
            self.assertIn("in raccolta dal 30/11", t)
            self.assertIn("$10.343", t)                   # valore del budget di carta
            self.assertIn("+3,4% su $10.000", t)
            self.assertIn("−4,8%", t)                     # DD
            self.assertIn("2 · 50%", t)                   # chiuse · WR
            self.assertIn("2 / 5", t)                     # aperte su massimo 5
            self.assertEqual(pg.eval_on_selector_all("#scEmc .emcL:not(details .emcL) .row b", "els => els.map(e => e.textContent)"), ["ZRO", "KAITO"])
            self.assertIn("+$238,40", t)                  # pnl_usd
            self.assertIn("+11,9% sulla quota", t)        # pnl in %
            self.assertIn("Chiuse (2)", t)
            pg.evaluate("document.querySelectorAll('#scEmc details').forEach(d => d.open = true)")
            t = pg.inner_text("#scEmc")
            self.assertLess(t.index("JTO"), t.index("IP"))   # chiuse dalla più recente
            for s in ("almeno 20 operazioni chiuse", "WR ≥ 50%", "rendimento del budget positivo", "DD giornaliero del budget ≥ −25%",
                      "senza perdita oltre −10%", "Solo carta, nessun ordine", "studio non operabile (lezione 131)"):
                self.assertIn(s, t)
            self.assertNotIn("Il registro parte", t)
            self.fine(pg)

    def test_registro_assente_o_vuoto(self):
        for nome in ("assente", "vuoto"):
            pg = self.apri(nome)
            t = pg.inner_text("#scEmc")
            self.assertIn("Il registro parte domenica 30/11", t)
            self.assertIn("Solo carta, nessun ordine", t)
            self.assertEqual(pg.eval_on_selector_all("#scEmc .tiles", "els => els.length"), 0)
            self.fine(pg)

    def test_registro_iniziale_e_partito_senza_segnali(self):
        pg = self.apri("iniziale")                     # forma di _vuoto() prima dell'inizio: nessuna tessera
        t = pg.inner_text("#scEmc")
        self.assertIn("Il registro parte domenica 29/11", t)
        self.assertEqual(pg.eval_on_selector_all("#scEmc .tiles", "els => els.length"), 0)
        self.fine(pg)
        pg = self.apri("partito")                      # partito, ancora nessun segnale: tessere e nota
        t = pg.inner_text("#scEmc")
        self.assertIn("$10.000", t)
        self.assertIn("DD\n0%", t)
        self.assertIn("0 / 5", t)
        self.assertIn("Nessun segnale short sulle emergenti finora", t)
        self.assertNotIn("Il registro parte", t)
        self.fine(pg)

    def test_da_rivalutare(self):
        pg = self.apri("rivalutare")
        t = pg.inner_text("#scEmc")
        self.assertIn("da rivalutare", t)
        self.assertIn("20 operazioni chiuse: soglie da rivalutare", t)
        self.assertIn("il registro si chiude (decide l'utente)", t)
        self.assertNotIn("in raccolta", t)
        self.fine(pg)


if __name__ == "__main__":
    unittest.main()
