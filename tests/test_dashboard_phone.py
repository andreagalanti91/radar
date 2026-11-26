"""Pre-analisi su telefono (radar/dashboard_template.html, radar/preview.py): card più corta a 400 px senza perdere informazioni
(chiusura multi-asset richiudibile, etichette non tagliate), funding senza "−0,0%". Niente rete."""
import re
import unittest
from pathlib import Path

from radar import preview

T = (Path(__file__).resolve().parents[1] / "radar" / "dashboard_template.html").read_text()


class TestFundingTesto(unittest.TestCase):
    def test_funding_piccolo_senza_meno_zero(self):
        self.assertEqual(preview._fund_txt(0.000098), "0,0098%/giorno · 3,6%/anno")
        self.assertEqual(preview._fund_txt(-0.0000013), "−0,0001%/giorno · −0,05%/anno")   # era "−0,0%/anno"
        self.assertEqual(preview._fund_txt(-0.0003), "−0,0300%/giorno · −10,9%/anno")
        self.assertEqual(preview._fund_txt(-1e-9), "0,0000%/giorno · 0,00%/anno")           # zero senza segno
        self.assertEqual(preview._fund_txt(0.0), "0,0000%/giorno · 0,00%/anno")


class TestPreanalisiTelefono(unittest.TestCase):
    def test_chiusura_multi_asset_richiudibile(self):
        # tabella degli asset in un <details> chiuso, solo nel pannello Dettagli pre-analisi; regime nel titolo
        self.assertIn('<details class="pvMac"><summary>', T)
        m = re.search(r'<details class="pvMac".*?</details>', T, re.S)
        self.assertIsNotNone(m)
        box = m.group(0)
        self.assertIn("<summary", box)
        self.assertIn("MC.regime.label", box[:box.index("</summary>")])      # il regime si legge anche da chiusa
        self.assertNotIn("MC.flags", box)                                    # gli avvisi restano sempre in vista, fuori
        self.assertIn("const macFlags = MC && (MC.flags", T)
        self.assertIn("${macFlags}", T)                                      # avvisi nella card
        self.assertIn("${ctx}${macroBox}", T)                                # tabella solo nel pannello

    def test_etichette_non_tagliate(self):
        css = re.search(r"\.pvMac \.mr>b\{[^}]*\}", T).group(0)
        self.assertNotIn("ellipsis", css)                                    # "Treasury 10 anni" era tagliato a 400 px
        self.assertNotIn("nowrap", css)

    def test_riga_decisione_corta_con_posizione(self):
        # con la posizione aperta "oggi short aperto" ripete il blocco sopra: su telefono resta solo la data della decisione
        self.assertIn('class="pvWhenX"', T)
        self.assertRegex(T, r"@media \(max-width:700px\)\{[^\n]*\.pvWhenX\{display:none\}")
        self.assertRegex(T, r"@media \(max-width:700px\)\{[^\n]*\.pvPos \.x\{display:none\}")


class TestTestiW31(unittest.TestCase):
    """Sezione "Limiti" di Come funziona: numeri presi dal report, mai scritti fissi nel modello (restavano indietro)."""
    def test_limiti_senza_numeri_del_25(self):
        for old in ("circa 78.000 $", "drawdown giornaliero −21%", "−25/−30%", "scendere del 30%"):
            self.assertNotIn(old, T)
        self.assertIn('id="wkLim"', T)
        # testo calcolato dallo storico del report (trade, vincenti, 10.000 $, drawdown): non può più restare indietro
        m = re.search(r'\$\("wkLim"\)\.innerHTML = `([^`]*)`', T)
        self.assertIsNotNone(m)
        # operazioni chiuse contate a parte dalla posizione aperta (rapporto ufficiale W3.2, 25/11/2026)
        for k in ("C.n", "C.wins", "C.open", "H.final_10k_1x", "M.max_dd_pct"):
            self.assertIn(k, m.group(1))

    def test_chiuse_separate_dalla_aperta(self):
        """history.m1 conta l'aperta come chiusa: la pagina usa chiuseW (H.trades senza reason "open") e CAGR/DD."""
        self.assertIn('const chiuseW = H =>', T)
        self.assertIn('t.reason !== "open"', T)
        self.assertIn('["Win rate (chiuse)", nfS(C.wr) + "%"]', T)
        self.assertIn('["Rend. annuo / DD", nfS(cagrDD(H, M, R.date))]', T)
        self.assertNotIn('["Rend./DD", nfS(M.mar)]', T)


class TestSoloW32(unittest.TestCase):
    """Nell'interfaccia solo la strategia in uso (W3.2): niente versioni precedenti, laboratorio né conti su carta."""
    VIETATI = ("W3.1", "Storico v2", "Laboratorio", "Giornaliera v2", "Strategia v2", "labTab", "stratSeg", "only-v2", "paperSec")

    def _ui(self):
        root = Path(__file__).resolve().parents[1] / "radar"
        return [("dashboard_template.html", T)] + [(f.name, f.read_text()) for f in sorted((root / "pages").glob("*.html"))]

    def test_sorgenti_senza_versioni_vecchie(self):
        for name, src in self._ui():
            for w in self.VIETATI:
                self.assertNotIn(w, src, f"{w!r} in {name}")
            self.assertNotRegex(src, r"\bW2\b", name)
            self.assertNotRegex(src, r"\bW3\b(?!\.2)", name)          # sempre "W3.2"

    def test_html_generato(self):
        import tempfile
        from radar.dashboard import render
        rep = {"date": "2026-11-21", "price": 60000, "lab": {"candidates": [{"name": "W3.1 Laboratorio"}]}, "paper": {"x": "Storico v2"}}
        html = render(rep, Path(tempfile.mkdtemp()) / "index.html", standalone=False).read_text()
        for w in ("W3.1", "Storico v2", "Laboratorio"):
            self.assertNotIn(w, html)

    def test_tema_scelto_o_del_dispositivo(self):
        # scelta salvata (pulsante luna) prima di tutto, altrimenti il tema del dispositivo (decisione 22/11)
        self.assertIn('t = localStorage.getItem("radarTheme")', T)
        self.assertIn('matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"', T)
        self.assertIn(':root[data-theme="dark"]{', T)



class TestToolSemplice(unittest.TestCase):
    """Richiesta 22/11: "togliamo le informazioni non necessarie". Stesso stile, meno contenuto in primo piano."""
    def test_oggi_senza_ripetizioni(self):
        # la pre-analisi non ripete P&L, ingresso e trailing della card Posizione: resta solo la soglia d'uscita
        self.assertNotIn("Posizione W3.2: ${sd > 0", T)
        self.assertNotIn("Ingresso → ${r.live", T)
        self.assertIn("Esce se <span class=\"x\">la settimana </span>chiude", T)
        self.assertNotIn("pvCtxS\">${cLines", T)                             # flussi e funding solo nei Dettagli
        self.assertNotIn('class="wkPx"', T)                                  # il prezzo è già in testa alla pagina

    def test_livelli_una_scheda(self):
        # dal 24/11 "Livelli vicini", S/R e liquidazioni vicine confluiscono nella tabella completa sotto il grafico (motore unico)
        for gone in ('id="lvCard"', 'id="srCard"', 'id="lqCard"'):
            self.assertNotIn(gone, T)
        # variante B: sei tessere-interruttore (una per gruppo) con il loro elenco al posto della tabella e delle pillole scorrevoli;
        # su telefono una colonna, gli interruttori vanno a capo (flex-wrap): mai scorrimento orizzontale della pagina
        self.assertIn('<div class="gxG" id="gxTbl"></div>', T)
        self.assertIn(".swB{display:flex;flex-wrap:wrap", T)
        self.assertIn(".sheetOnly:not(.inSheet){display:none!important}", T)

    def test_notizie_corte(self):
        self.assertNotIn("n.summary", T)                                     # niente riassunti nel feed
        self.assertIn("g.slice(0, 3)", T)                                   # per tema le prime 3, il resto richiuso
        self.assertIn("Altre ${bkMore.length} riunioni", T)
        self.assertNotIn('id="newsWhy"', T)
        self.assertIn("meglio non aprire o spostare posizioni a ridosso dell'uscita", T)   # avviso di rischio resta

    def test_liquidazioni_senza_book(self):
        L = (Path(__file__).resolve().parents[1] / "radar" / "pages" / "liquidazioni.html").read_text()
        for w in ('id="obBookBox"', 'id="obEng"', 'id="lqMBook"', 'id="lqMEng"', "liveBook(", "renderEngine"):
            self.assertNotIn(w, L)
        self.assertIn("ev.slice(0, 6)", L)
        self.assertIn("W.slice(0, 6)", L)
        B = (Path(__file__).resolve().parents[1] / "radar" / "pages" / "book.html").read_text()
        self.assertIn("Indicatore descrittivo, non un segnale", B)            # dicitura del sentiment sempre in vista


if __name__ == "__main__":
    unittest.main()
