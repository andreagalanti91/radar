"""Variante B "Cruscotto a tessere" (radar/dashboard_template.html, 26/11/2026): tessere con "Dettagli ›" che aprono il pannello
(dal basso su telefono, a destra su desktop), ordine di Oggi, pre-analisi in Oggi, Mercato power in Oggi e Posizioni, colori
(verde/rosso solo profitto/perdita e semafori, lato neutro, candele grigie), pagine spente ancora spente. Niente rete."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()


def view(v):
    i = T.index(f'<div class="view" id="v-{v}"')
    j = T.find('<div class="view" id="v-', i + 10)
    return T[i:j if j > 0 else None]


class Tessere(unittest.TestCase):
    def test_tessera_con_dettagli(self):
        # una funzione sola disegna le tessere: "Dettagli ›" in fondo, pulsante con data-det, apre il pannello generico
        self.assertIn("const tileB = window.tileB = o =>", T)
        self.assertIn('class="dtl${o.c ? " c" : ""}" data-det="${o.det}" aria-haspopup="dialog"', T)
        self.assertIn('.dtl::after{content:"›"', T)
        self.assertIn("const f = DET[b.dataset.det]; if (f) { e.preventDefault(); f(b); }", T)
        self.assertRegex(T, r"\.dtl\{[^}]*min-height:40px")                          # tocco ≥ 40 px

    def test_ogni_dettagli_ha_il_suo_pannello(self):
        js = T[T.index("<script>\nconst R = "):]
        dets = set(re.findall(r'det: "(\w+)"(?!\s*\+)', js)) - {""}   # chiavi fisse (quelle composte, "gx" + gruppo, hanno il loro DET[...] nel ciclo)
        for d in dets:
            self.assertRegex(js, rf'DET(\.{d}\b|\["{d}"\])', d)
        self.assertGreaterEqual(len(dets), 15)

    def test_pannello_dal_basso_e_a_destra(self):
        self.assertRegex(T, r"@media \(max-width:700px\)\{\s*dialog\.dlg\{width:100%;max-width:100%;margin:auto 0 0")
        m = re.search(r"@media \(min-width:701px\)\{\s*dialog\.dlg\{([^}]*)\}", T)
        self.assertIsNotNone(m)
        for x in ("right:0", "left:auto", "height:100dvh"):
            self.assertIn(x, m.group(1))

    def test_etichette_leggibili(self):
        for sel in (r"\.t \.k\{font:500 13px", r"\.t \.sm\{font-size:13px", r"\.pt \.tg\{font-size:12px", r"\.xb \.lb\{[^}]*font:600 12\.5px"):
            self.assertRegex(T, sel)


class Oggi(unittest.TestCase):
    def test_ordine_e_contenuto(self):
        o = view("oggi")
        ordine = ['id="ogTop"', 'id="ogPos"', 'id="ogCone"', 'id="ogPre"', 'id="ogPw"', 'id="ogCtx"', 'id="ogNews"']
        self.assertEqual([o.index(i) for i in ordine], sorted(o.index(i) for i in ordine))

    def test_preanalisi_in_oggi(self):
        self.assertIn('const PV = R.preview, el = $("ogPre");', T)
        self.assertNotIn('id="pvCard"', T)
        self.assertIn('DET.pre = () => { openSheet("Pre-analisi della chiusura di domenica"', T)
        self.assertIn("Con i dati di oggi: <b>${es}</b>", T)

    def test_posizioni_con_barra_di_uscita_in_dollari(self):
        js = T[T.index("// ---- Oggi e Posizioni · posizioni aperte"):T.index("// ---- Mercato power (report.mercato")]
        for x in ("function pbarB(", "function xbarB(", "susd(o.usd)", "utile bloccato", "Distribuzione a fine settimana",
                  "in perdita se esce ora", "verde = lontana · grigio = non ancora", "wkDlgOpen(W, tag, live)"):
            self.assertIn(x, js)
        # P&L con la stessa formula del server (calc di exits_block)
        self.assertIn("c.pnl_pct + c.sg * c.expo * (px - c.px0) / U.entry_px * 100", js)


class MercatoPower(unittest.TestCase):
    def test_in_oggi_e_posizioni(self):
        js = T[T.index("// ---- Mercato power (report.mercato"):T.index("// ---- Opzioni (pagina a sé)")]
        self.assertIn("R.mercato && R.mercato.assets", js)
        self.assertIn('$("ogPw").innerHTML', js)
        self.assertIn('$("posPw").innerHTML', js)
        self.assertIn('it.key !== "flusso"', js)                                      # in Posizioni il flusso è già nella distribuzione
        self.assertIn("contesto · decide W3.2", js)
        self.assertIn("Regola del semaforo", js)
        self.assertIn("USATO DA W3.2", js)
        for b in ("ocOpen", "dxOpen", "oxOpen"):                                      # schede complete raggiungibili dai Dettagli
            self.assertIn(f'B("{b}"', js)
        codice = "\n".join(l for l in js.splitlines() if not l.lstrip().startswith("//"))
        self.assertNotRegex(codice, r"(?i)punteggio|score")                          # nessun punteggio unico nella pagina

    def test_schede_vecchie_conservate(self):
        p = view("posizioni")
        self.assertIn('<div id="ctxHold" hidden>', p)
        for x in ('id="ocBox"', 'id="dxBox"', 'id="oxBox"'):
            self.assertIn(x, p)


class Colori(unittest.TestCase):
    def test_lato_neutro_candele_grigie(self):
        self.assertIn('const sideC = s => s === "long" || s === "short" ? `<span class="side-c">', T)
        self.assertIn(".side-c{display:inline-flex;align-items:center;gap:3px;font:600 12px/1 var(--font);color:var(--label2)", T)
        self.assertIn('upColor: "rgba(0,0,0,0)", downColor: gry', T)
        self.assertIn(".scTag.long,.scTag.short{--c:var(--label2)}", T)

    def test_tema_chiaro_e_scuro(self):
        self.assertIn(':root{--neu:#d5d9e0;', T)
        self.assertIn(':root[data-theme="dark"]{--neu:#3a3f4a;', T)


class PagineSpente(unittest.TestCase):
    def test_restano_spente(self):
        for f in ("const BOOK_ON = false;", "const LIQ_ON = false;", "const OPZIONI_ON = false;"):
            self.assertIn(f, T)
        self.assertIn('wallet: "oggi"', T)
        nav = T[T.index('<nav aria-label="Sezioni">'):T.index("</nav>")]
        self.assertEqual(re.findall(r'data-v="(\w+)"', nav), ["oggi", "posizioni", "scanner", "grafico", "movimenti", "notizie"])


if __name__ == "__main__":
    unittest.main()
