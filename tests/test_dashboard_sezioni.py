"""Struttura delle sezioni (radar/dashboard_template.html): menu a 6 voci nel markup (Scanner dal 25/11; Opzioni aggiunta dal JS con OPZIONI_ON, di nuovo attiva dal 27/11) uguale su telefono e desktop, Book e "Come funziona"
fuori dal menu, vecchi indirizzi reindirizzati, Liquidazioni pagina a sé, card di Oggi con le diciture obbligatorie. Niente rete."""
import re
import tempfile
import unittest
from pathlib import Path

from radar.dashboard import render

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
MENU = [("oggi", "Oggi"), ("posizioni", "Posizioni"), ("wallet", "Wallet"), ("scanner", "Scanner"), ("grafico", "Grafico"), ("movimenti", "Movimenti"), ("notizie", "Notizie")]   # Liquidazioni fuori dal menu dal 24/11 (LIQ_ON); Wallet (posizioni reali) dal 27/11/2026
CORTE = {"Liquidazioni": "Liquid."}   # etichette accorciate nella barra in basso del telefono


def _nav(src, pat):
    box = re.search(pat, src, re.S).group(1)
    return box, re.findall(r'<a href="#(\w+)" data-v="(\w+)"><svg><use href="#[\w-]+"/></svg>([^<]+)</a>', box)


class TestMenu(unittest.TestCase):
    def test_sei_voci_stesso_ordine(self):
        for pat, short in ((r'<aside class="side">.*?<nav aria-label="Sezioni">(.*?)</nav>', {}), (r'<nav class="tabbar" aria-label="Sezioni">(.*?)</nav>', CORTE)):
            box, links = _nav(T, pat)
            self.assertEqual([(h, t) for h, v, t in links], [(h, short.get(t, t)) for h, t in MENU])
            self.assertTrue(all(h == v for h, v, _ in links))
            self.assertEqual(box.count("<a "), 7)
            for w in ("Book", "Come funziona", "Storico", "#book", "#metodo", "Liquid", "#liquidazioni", "Opzioni", "#opzioni"):
                self.assertNotIn(w, box)
        self.assertNotIn("Navigazione", T)
        self.assertIn("grid-template-columns:repeat(7,1fr)", re.search(r"\.tabbar\{[^}]*\}", T).group(0))

    def test_ogni_voce_ha_la_sua_pagina_e_icona(self):
        pages = "".join(f.read_text() for f in (ROOT / "radar" / "pages").glob("*.html"))
        for v, _ in MENU + [("liquidazioni", ""), ("opzioni", "")]:
            self.assertIn(f'<div class="view" id="v-{v}"', T + pages)
        for ico in re.findall(r'<use href="#([\w-]+)"/>', T):
            self.assertIn(f'<symbol id="{ico}"', T)

    def test_vecchi_indirizzi(self):
        alias = re.search(r"const ALIAS = \{([^}]*)\}", T).group(1)
        for old, new in (("storico", "movimenti"), ("simulatore", "movimenti"), ("statistiche", "movimenti")):
            self.assertRegex(alias, rf'\b{old}: "{new}"')
        self.assertNotIn("wallet:", alias)   # dal 27/11/2026 #wallet è il Wallet reale (prima portava a Oggi)
        self.assertIn('book: BOOK_ON ? "book" : "oggi"', alias)
        self.assertIn('liquidazioni: LIQ_ON ? "liquidazioni" : "grafico"', alias)   # #liquidazioni porta a Grafico finché LIQ_ON = false
        self.assertIn('history.replaceState(null, "", "#" + ok)', T)            # l'indirizzo vecchio viene riscritto
        views = re.search(r"const VIEWS = \[([^\]]*)\]", T).group(1)
        self.assertEqual(re.findall(r'"(\w+)"', views), ["oggi", "posizioni", "wallet", "scanner", "grafico", "movimenti", "notizie", "metodo"])
        self.assertIn('.concat(OPZIONI_ON ? ["opzioni"] : [], LIQ_ON ? ["liquidazioni"] : [], BOOK_ON ? ["book"] : [])', T)
        self.assertIn('opzioni: OPZIONI_ON ? "opzioni" : "oggi"', alias)            # #opzioni porta a Oggi finché OPZIONI_ON = false

    def test_opzioni_attiva(self):   # nascosta dal 25/11, riattivata il 27/11/2026 su richiesta dell'utente
        self.assertIn("const OPZIONI_ON = true;", T)
        self.assertLess(T.index("const OPZIONI_ON = true;"), T.index("(function renderOpzioni()"))   # dichiarata prima dell'uso
        self.assertIn('const L = $("opLine"); if (!L || !OPZIONI_ON) return;', T)  # riga in Oggi solo con il flag
        self.assertIn('<div class="view" id="v-opzioni" hidden>', T)
        self.assertNotIn('href="#opzioni" data-v="opzioni"', T.split("<script")[0])   # voce aggiunta dal JS, prima di Scanner
        self.assertIn("if (OPZIONI_ON && viewEl(\"opzioni\"))", T)
        self.assertIn("/* 7 voci (Opzioni di nuovo nel menu dal 27/11, OPZIONI_ON)", T)

    def test_book_spento_ma_presente(self):
        self.assertIn("const BOOK_ON = false;", T)                              # una riga per riaccenderlo
        self.assertTrue((ROOT / "radar" / "pages" / "book.html").exists())
        self.assertNotIn('href="#book"', T.split("<script")[0])                 # nessun link nel markup
        # la pagina Book parte solo dal router, e solo se la sezione è tra quelle raggiungibili
        self.assertIn('const PAGE_OF = Object.assign({ wallet: "wallet" }, LIQ_ON ? { liquidazioni: "liquidazioni" } : {}, BOOK_ON ? { book: "book" } : {})', T)
        self.assertIn("const LIQ_ON = false;", T)
        self.assertIn("const pk = PAGE_OF[ok], PG = pk && (window.PAGES || {})[pk]", T)
        B = (ROOT / "radar" / "pages" / "book.html").read_text()
        reg = B[B.index("window.PAGES.book = {"):]
        self.assertIn("show() { if (!document.hidden) start();", reg)           # le connessioni partono da show(), mai al caricamento
        self.assertNotIn("start()", reg[reg.index("hide()"):])

    def test_come_funziona_solo_da_regole_complete(self):
        self.assertEqual(T.count('href="#metodo"'), 1)
        self.assertIn('<a class="more" href="#metodo" id="wkRules"', T)
        self.assertIn('<div class="view" id="v-metodo" hidden>', T)


class TestStruttura(unittest.TestCase):
    def _view(self, v):
        i = T.index(f'<div class="view" id="v-{v}"')
        j = T.find('<div class="view" id="v-', i + 10)
        return T[i:j if j > 0 else None]

    def test_oggi(self):
        o = self._view("oggi")
        # schede-domanda (V2): posizioni · uscite · 30 giorni · pre-analisi · Mercato power · notizie (tests/test_oggi_schede.py)
        ids = ('id="posLine"', 'id="qExitB"', 'id="cnCard"', 'id="pvQ"', 'id="cxCard"', 'id="todayN"')
        for i in ids:
            self.assertIn(i, o)
        for a, b in zip(ids, ids[1:]):
            self.assertLess(o.index(a), o.index(b))
        for i in ('id="wkHero"', 'id="pvCard"', 'id="wkChart"', 'id="lvCard"'):
            self.assertNotIn(i, o)

    def test_posizioni_grafico_movimenti(self):
        p, g, m = self._view("posizioni"), self._view("grafico"), self._view("movimenti")
        for i in ('id="wkHero"', 'id="ethCard"', 'id="pvCard"', 'id="wkDlg"'):
            self.assertIn(i, p)
        for i in ('id="gxCard"', 'id="gxTf"', 'id="gxSw"', 'id="gxChart"', 'id="gxTbl"'):
            self.assertIn(i, g)
        self.assertLess(g.index('id="gxChart"'), g.index('id="gxTbl"'))                 # tabella completa sotto il grafico
        for i in ('id="wkMacd"', 'id="lvCard"', 'id="srCard"', 'id="lqCard"', "#liquidazioni"):
            self.assertNotIn(i, g)
        self.assertNotIn("v-liquidazioni", T)                                   # Liquidazioni resta nel suo file, pagina a sé
        for i in ('id="wkStatSec"', 'id="ethStatSec"', 'id="simPanel"', 'id="simTrades"'):
            self.assertIn(i, m)
        self.assertNotIn("v-storico", T)

    def test_card_di_oggi(self):
        # frase con l'intervallo, scala 80/50% con il prezzo, livelli ordinati per prezzo, tre tessere di contesto (senza Mercato power)
        for w in ('class="cnScale"', 'class="b80"', 'class="b50"', 'class="qL"', ".sort((a, b) => b[0].prezzo - a[0].prezzo)",
                  'class="cxTiles"', 'class="cxT"', "Dettagli ›"):
            self.assertIn(w, T)
        # le diciture arrivano dal report e restano in pagina, testuali
        self.assertIn('<p class="cxNote">${esc(C.note)}</p>', T)
        # con report.mercato la scheda diventa "Mercato power" (tests/test_mercato.py) e il Contesto passa nel suo pannello
        self.assertIn("if (!rows.length || MP) return;", T)
        self.assertIn('${ctxC ? sec("Contesto di mercato e politica economica", ctxPanel(ctxC)) : ""}', T)
        from radar import cone, context
        self.assertTrue(context.NOTE.startswith("Contesto, non segnale"))
        self.assertIn("Probabilità calcolate dalla volatilità attuale, non dalla direzione", Path(cone.__file__).read_text())

    def test_render(self):
        rep = {"date": "2026-11-22", "price": 61271.08,
               "cone": {"price": 61271.08, "i80": [52874.0, 75533.0], "i50": [57803.0, 69035.0], "note": "Probabilità calcolate dalla volatilità attuale, non dalla direzione: prova."},
               "context": {"rows": [{"label": "Mercato", "text": "ribasso"}], "note": "Contesto, non segnale: prova."}}
        html = render(rep, Path(tempfile.mkdtemp()) / "index.html", standalone=False).read_text()
        import json
        self.assertIn(json.dumps("Probabilità calcolate dalla volatilità attuale, non dalla direzione: prova."), html)
        self.assertIn(json.dumps("Contesto, non segnale: prova."), html)
        self.assertIn('<div class="view" id="v-liquidazioni" hidden>', html)    # la pagina delle liquidazioni resta iniettata
        self.assertIn('id="v-book"', html)                                      # il Book resta nel file, senza voce di menu
        self.assertEqual(html.count('href="#book"'), 0)


if __name__ == "__main__":
    unittest.main()
