"""Layout desktop, variante A (scelta dell'utente il 27/11/2026; anteprima in stato/ux-varianti/desktop): da 1100 px griglia a 12
colonne con le schede di Oggi a tutta larghezza e il contenuto in colonne interne (posizioni BTC | ETH | Opzioni, uscite BTC | ETH);
la barra delle uscite misura la propria colonna (qc in renderPosLine). Sotto 1100 px nessuna regola nuova: telefono invariato."""
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
STYLE = T[T.index("<style>"):T.index("</style>")]


def block_a() -> str:
    i = STYLE.index("/* ---------- Layout desktop A")
    j = STYLE.index("@media (min-width:1100px){", i)
    depth, k = 0, STYLE.index("{", j)
    for k in range(k, len(STYLE)):
        depth += {"{": 1, "}": -1}.get(STYLE[k], 0)
        if depth == 0:
            break
    return STYLE[j:k + 1]


class Regole(unittest.TestCase):
    def test_media_query_1100(self):
        b = block_a()
        for r in (".qGrid{grid-template-columns:repeat(12,minmax(0,1fr));align-items:stretch}", ".qGrid>.q{grid-column:1/-1}",
                  "#qPos:has(>#opLine:not([hidden])){grid-template-columns:repeat(3,minmax(0,1fr))}", "#posLine{display:contents}",
                  "#qExitB{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:28px}",
                  "#wkHero{grid-template-columns:repeat(3,minmax(0,1fr))", "#scSec>#scIng{grid-column:2;grid-row:span 2}",
                  ".nwGrid>.nwGrp:last-child:nth-child(odd){grid-column:1/-1}", ".sxGrid>.sxC:last-child:nth-child(odd){grid-column:1/-1}",
                  ".qOp .opCt,.qOp .opSc{display:none} .qOp .opCt2{display:inline}"):
            self.assertIn(r, b)
        # nessuna regola della variante fuori dal blocco ≥ 1100 px (sotto, telefono e tablet restano come prima)
        fuori = STYLE.replace(b, "")
        self.assertNotIn("repeat(12,", fuori)
        self.assertNotIn("nwGrp:last-child:nth-child(odd)", fuori)
        self.assertNotIn("#posLine{display:contents}", fuori)
        self.assertIn(".qOp .opCt2{display:none;white-space:nowrap}", fuori)          # "· su carta" solo su desktop

    def test_etichette_opex_colonna_stretta(self):   # termometro OPEX nella card di BTC su tre colonne: etichette unite prima
        js = T[T.index("(function renderOpex() {"):T.index("// ---- pannello", T.index("(function renderOpex() {"))]
        self.assertIn('const TH = box && window.matchMedia && matchMedia("(min-width:1100px)").matches ? 50 : 34;', js)
        self.assertIn("Math.abs(xn - xm) < TH", js)
        self.assertIn('escS(st.slice(cut + 3)).replace(/(\\d) (?=\\S)/g, "$1&nbsp;")', js)   # "tra 27 g": numero e unità insieme

    def test_larghezza_barra_uscite(self):
        js = T[T.index("(function renderPosLine() {"):T.index("// ---- Opzioni (pagina a sé)")]
        self.assertIn('const qb = $("qExitB"), qc = getComputedStyle(qb).gridTemplateColumns.split(" ").length || 1;', js)
        self.assertIn("const W = Math.max(240, ((qb.clientWidth || 320) - 28 * (qc - 1)) / qc - 4);", js)
        self.assertNotIn('const W = Math.max(240, ($("qExitB").clientWidth || 320) - 4);', js)

    def test_nel_browser(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright non installato")
        i = T.index('<div class="view" id="v-oggi">')
        oggi = T[i:T.index('<div class="view"', i + 10)].replace(' hidden></a>', '></a>')
        row = '<div class="qP"><span class="ic"></span><div><b>{}</b><small>dal 16/11, ingresso $65.286</small></div><div class="rv"><b>+$1.653</b></div></div>'
        posl = '<p class="qA">Bene.</p>' + row.format("Bitcoin · short") + row.format("Ethereum · short")
        opl = ('<span class="ic"></span><div><b>Opzioni · <span class="opTag tieni">TIENI</span> <span class="opCt">su carta</span></b>'
               '<small>Put $65.000 · <span class="opSc">scadenza </span>11/12<span class="opCt2"> · su carta</span></small></div><div class="rv"><b>+$774</b></div>')
        js = ("const $ = id => document.getElementById(id);"
              f"$('posLine').innerHTML = {posl!r}; $('opLine').innerHTML = {opl!r};"
              "$('qExitB').innerHTML = '<p class=\"qA\">x</p><div class=\"qX\">BTC</div><div class=\"qX\">ETH</div>';"
              "const qb = $('qExitB'), qc = getComputedStyle(qb).gridTemplateColumns.split(' ').length || 1;"
              "window.__r = { qc, pos: getComputedStyle($('qPos')).gridTemplateColumns.split(' ').length,"
              " q: getComputedStyle(document.querySelector('.qGrid')).gridTemplateColumns.split(' ').length,"
              " opH: $('opLine').querySelector('div').getBoundingClientRect().height, sw: document.documentElement.scrollWidth };")
        with tempfile.TemporaryDirectory() as t:
            page = Path(t) / "a.html"
            page.write_text(f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                            f'{STYLE}</style></head><body><main style="padding:16px;max-width:984px">{oggi}</main><script>{js}</script></body></html>')
            try:
                p = sync_playwright().start()
                b = p.chromium.launch()
            except Exception as e:  # noqa: BLE001
                self.skipTest(f"chromium non disponibile: {e}")
            self.addCleanup(p.stop)
            self.addCleanup(b.close)
            res = {}
            for w in (400, 1099, 1280):
                pg = b.new_page(viewport={"width": w, "height": 900})
                pg.goto(page.as_uri())
                res[w] = pg.evaluate("window.__r")
                pg.close()
        self.assertEqual((res[400]["qc"], res[1099]["qc"]), (1, 1))         # telefono e tablet: barra a tutta larghezza
        self.assertEqual(res[1099]["q"], 2)                                  # 900–1099 px: due schede affiancate come prima
        self.assertEqual((res[1280]["q"], res[1280]["pos"], res[1280]["qc"]), (12, 3, 2))   # BTC | ETH | Opzioni; uscite BTC | ETH
        self.assertLess(res[1280]["opH"], 70)                                # testo della riga Opzioni su 3 righe, non 4
        for w in res:
            self.assertLessEqual(res[w]["sw"], w)


if __name__ == "__main__":
    unittest.main()
