"""Pagina Opzioni · "La nostra analisi" (research/opzioni_direzione, research/opzioni_scadenze, lezione 128): sezione dopo "Scadenze
maggiori" e prima dell'operatività su carta, quattro domande, riga "Oggi" collegata a report.opzioni (put/call di W3.2 o nessuna
opzione) e movimento atteso della prossima scadenza grande da report.opex.calendar. Eseguito con node sulla funzione vera."""
import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
NODE = shutil.which("node")
QUESTIONS = ["Le opzioni dicono dove va BTC?", "Il prezzo va verso il massimo dolore?", "A cosa servono allora?", "Quando comprare put o call?"]


def cut(a: str, b: str) -> str:
    return T[T.index(a):T.index(b)]


def iso(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).replace(hour=8, minute=0, second=0, microsecond=0).isoformat()


PUT = {"verso": "short", "tipo": "put", "strike": 65000.0, "scadenza": "2026-12-11", "stato": "aperta"}
CAL = [{"exp": iso(4), "notional": 3e8, "mov_atteso_pct": 5.0},                       # piccola: non conta
       {"exp": iso(7), "notional": 1.66e9, "mov_atteso_pct": 6.6, "max_pain": 63000.0},
       {"exp": iso(28), "notional": 1.01e10, "mov_atteso_pct": 13.2}]


class Struttura(unittest.TestCase):
    def test_sezione_fra_scadenze_e_carta(self):
        v = cut('<div class="view" id="v-opzioni"', '<div class="view" id="v-scanner"')
        self.assertLess(v.index('id="sxSec"'), v.index('id="anSec"'))
        self.assertLess(v.index('id="anSec"'), v.index('id="opSec"'))
        self.assertIn("La nostra analisi", v)
        self.assertIn("Studio preregistrato con revisione critica (lezione 128). Solo contesto: W3.2 non cambia. Non è consulenza.", v)

    def test_numeri_dello_studio(self):
        js = cut("(function renderAnalisi()", '// ---- Opzioni · "Scadenze maggiori"')
        for q in QUESTIONS:
            self.assertIn(q, js)
        for x in ("31–44%", "$70.000", "$61.600", "78%", "94%", "50/50", "72%", "20–50 giorni", "5%", "$29.856", "−9,8%", "$84.330",
                  "$2.000–19.000", "Dettagli", "1e9", "<= 120"):
            self.assertIn(x, js)
        sx = cut("(function renderScadenze()", "// ---- Scanner (pagina a sé)")
        self.assertIn("BIG = 1e9", sx)                       # stessa regola di "Scadenze maggiori" per la prossima scadenza grande
        self.assertIn("DAYS = 120", sx)
        self.assertNotIn("renderAnalisi", sx)                # la sezione Scadenze resta autonoma (test_opzioni_scadenze la isola)


@unittest.skipUnless(NODE, "node non installato")
class Oggi(unittest.TestCase):
    JS = "\n".join(["const window = {};", cut("const nfIT = window.nfIT", "const nfS = "), cut("const usd = ", "const css = "),
                    next(l for l in T.splitlines() if l.startswith("const escS = ")),
                    next(l for l in T.splitlines() if l.startswith("const isOpenX = ")),
                    cut("(function renderAnalisi()", '// ---- Opzioni · "Scadenze maggiori"')])

    def run_case(self, R: dict) -> str:
        js = (f"const R = {json.dumps(R)}; const box = {{ innerHTML: '' }}; const $ = id => id === 'anGrid' ? box : null;\n" + self.JS +
              "\nconsole.log(JSON.stringify(box.innerHTML));")
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "x.js"
            p.write_text(js)
            out = subprocess.run([NODE, str(p)], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_quattro_domande(self):
        h = self.run_case({})
        self.assertEqual(h.count('class="card q anC"'), 4)
        for q in QUESTIONS:
            self.assertIn(q, h)
        self.assertEqual(h.count("<summary>Dettagli</summary>"), 4)

    def test_put_aperta(self):
        h = self.run_case({"weekly": {"status": "aperto", "side": "short"}, "opzioni": {"azione": "tieni", "posizione": PUT},
                           "opex": {"calendar": CAL}})
        self.assertIn("<b>Oggi</b> · W3.2 short → put (quella su carta). Put $65.000, scadenza 11/12.", h)
        self.assertIn('<span class="chip on short">W3.2 short → put</span>', h)
        self.assertIn('<span class="chip">W3.2 long → call</span>', h)
        dm = datetime.fromisoformat(CAL[1]["exp"]).strftime("%d/%m")
        self.assertIn(f"il mercato prezza <b>±6,6%</b> entro il {dm} (prossima scadenza grande, 1,7 mld $)", h)

    def test_segnale_long_da_comprare(self):
        q = {"contratto": {"tipo": "call", "strike": 70000.0, "scadenza": "2027-01-08"}}
        h = self.run_case({"weekly": {"status": "aperto", "side": "long"}, "opzioni": {"azione": "compra", "proposta": q}})
        self.assertIn("W3.2 long → call da comprare (su carta). Call $70.000, scadenza 08/01.", h)
        self.assertIn('<span class="chip on long">W3.2 long → call</span>', h)

    def test_senza_segnale(self):
        for R in ({"weekly": {"status": "flat", "side": None}, "opzioni": {"azione": "attesa", "esempio": {}}}, {}):
            h = self.run_case(R)
            self.assertIn("<b>Oggi</b> · nessun segnale di W3.2: nessuna opzione.", h)
            self.assertNotIn("chip on", h)
            self.assertNotIn("prossima scadenza grande", h)          # niente calendario: niente riga

    def test_fuori_e_volatilita_mancante(self):
        cal = [dict(c, mov_atteso_pct=None) for c in CAL]          # ripiego OKX: volatilità null
        h = self.run_case({"weekly": {"status": "aperto", "side": "short"}, "opex": {"calendar": cal},
                           "opzioni": {"azione": "fuori", "proposta": {"contratto": {"tipo": "put", "strike": 60000.0, "scadenza": "2026-12-25"}}}})
        self.assertIn("W3.2 short, ma l'opzione di questa operazione non è aperta: nessuna opzione fino al prossimo segnale.", h)
        self.assertNotIn("da comprare", h)
        self.assertNotIn("chip on", h)
        self.assertIn("movimento atteso non disponibile in questo aggiornamento", h)

    def test_nel_browser_2x2(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright non installato")
        style = cut("<style>", "</style>") + "</style>"
        sec = cut('<div class="section" id="anSec">', '<div class="section" id="opSec">')
        R = {"weekly": {"status": "aperto", "side": "short"}, "opzioni": {"azione": "tieni", "posizione": PUT}, "opex": {"calendar": CAL}}
        js = "const $ = id => document.getElementById(id);\n" + self.JS.replace("const window = {};", "") .replace(
            "(function renderAnalisi()", f"const R = {json.dumps(R)};\n(function renderAnalisi()", 1)
        with tempfile.TemporaryDirectory() as t:
            page = Path(t) / "an.html"
            page.write_text(f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                            f'{style}</head><body><main style="padding:16px;max-width:1000px">{sec}</main><script>{js}</script></body></html>')
            try:
                p = sync_playwright().start()
                b = p.chromium.launch()
            except Exception as e:  # noqa: BLE001
                self.skipTest(f"chromium non disponibile: {e}")
            self.addCleanup(p.stop)
            self.addCleanup(b.close)
            for w in (360, 400, 1280):
                pg = b.new_page(viewport={"width": w, "height": 900})
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(page.as_uri())
                r = pg.evaluate("[...document.querySelectorAll('.anC')].map(c => { const r = c.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.height)]; })")
                self.assertEqual(len(r), 4)
                self.assertEqual(errs, [])
                self.assertFalse(pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
                if w == 1280:   # 2×2: stesse righe, stesse altezze per riga (nessun vuoto)
                    self.assertEqual((r[0][1], r[0][2]), (r[1][1], r[1][2]))
                    self.assertEqual((r[2][1], r[2][2]), (r[3][1], r[3][2]))
                    self.assertLess(r[0][0], r[1][0])
                else:           # telefono: una colonna
                    self.assertEqual(len({x[0] for x in r}), 1)
                pg.close()


if __name__ == "__main__":
    unittest.main()
