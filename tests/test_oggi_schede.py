"""Vista Oggi, variante V2 "una domanda per scheda" (scelta dell'utente 26/11/2026): ordine delle sei schede, "Dettagli ›" in ognuna
verso il dettaglio esistente, frasi-risposta per short aperto, long aperto, nessuna posizione, uscita imminente e dati mancanti
(eseguite con node sulle funzioni vere del modello), numeri uguali a quelli di Posizioni (radar/weekly.exits_block)."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from radar import weekly

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
NODE = shutil.which("node")


def cut(a: str, b: str) -> str:
    return T[T.index(a):T.index(b)]


def oggi() -> str:
    i = T.index('<div class="view" id="v-oggi">')
    return T[i:T.index('<div class="view"', i + 10)]


# posizioni del report pubblicato del 26/11/2026 (chiusura del 25/11): BTC short da 65.286, ETH short da 2.125
BTC = dict(side="short", entry_px=65285.7, price=60458.01, best=58951.51, trail=75763.76, atr_w=6999.27, ema21=74273.45,
           expo=0.972, capital=30000.0, pnl_pct=7.23, fund7=0.00011, flow=-1.01)
ETH = dict(side="short", entry_px=2125.33, price=1692.65, best=1623.09, trail=2310.6, atr_w=278.85, ema21=2209.08,
           expo=0.813, capital=30000.0, pnl_pct=16.57, fund7=0.00006, flow=-0.73)


def pos(d: dict, status="aperto", entry="2026-11-16", **kw) -> dict:
    d = d | kw
    return {"status": status, "side": d["side"], "entry": entry, "week": "2026-11-22", "entry_px": d["entry_px"], "price": d["price"],
            "capital": d["capital"], "pnl_pct": d["pnl_pct"], "trail": d["trail"], "reason": kw.get("reason"),
            "uscite": weekly.exits_block(**{k: d[k] for k in BTC})}


QUESTIONS = ["Come vanno le posizioni?", "Quando escono?", "Dove può andare BTC in 30 giorni?", "Cosa dice la pre-analisi?",
             "Il mercato è con noi?", "Cosa succede oggi?"]


class Struttura(unittest.TestCase):
    def test_ordine_delle_domande(self):
        o = oggi()
        h = re.findall(r'<h2 class="qH" id="\w+">([^<]+)</h2>', o)
        self.assertEqual(h, QUESTIONS)
        self.assertEqual(o.count('<section class="card q"'), 6)

    def test_dettagli_in_ogni_scheda(self):
        secs = oggi().split('<section class="card q"')[1:]
        dest = ['href="#posizioni"', 'id="qExitM"', 'href="#grafico"', 'id="qPreM"', 'id="qMpM"', 'href="#notizie"']
        for s, d in zip(secs, dest):
            m = re.search(r'<(a|button)[^>]*class="qMore"[^>]*>Dettagli<svg', s)
            self.assertTrue(m, s[:120])
            self.assertIn(d, m.group(0))
        # i pulsanti aprono i pannelli già esistenti (nessuna informazione tolta)
        self.assertIn('openSheet("Quando escono", body)', T)
        self.assertIn("qxHtml(X.uscite, px)", cut('$("qExitM").onclick', "openSheet(\"Quando escono\""))
        self.assertIn("window.wkDlgOpen(X, b.dataset.a", T)
        self.assertIn('$("qPreM").onclick = () => { openSheet("Dettagli pre-analisi"', T)
        self.assertIn("${drBox}${cond}${sig}${ctx}${macroBox}${ctxD}${hist}${flow}${liq}", T)
        self.assertIn('$("qMpM").onclick = () => openSheet("Mercato power · perché ogni semaforo", body)', T)

    def test_tocchi_testi_e_colori(self):
        css = cut("/* ---------- Oggi · schede-domanda (V2)", "@media (prefers-reduced-motion:reduce){.view{animation:none}")
        self.assertGreater(len(css), 3000)
        self.assertIn("min-height:44px", re.search(r"\.qMore\{[^}]*\}", css).group(0))
        for px in re.findall(r"font:[^;]*?([\d.]+)rem", css) + re.findall(r"font-size:([\d.]+)rem", css):
            self.assertGreaterEqual(float(px) * 16, 13, px)                       # testi ≥ 13 px
        self.assertNotIn("--label3", css)                                         # testi secondari in --label2 (contrasto AA)
        # Mercato power: blu/arancio/grigio con simbolo; verde e rosso restano per profitto e perdita
        self.assertIn(".st-favore{color:#fff;background:var(--tint)}", css)
        self.assertIn(".mpDot.favore{background:var(--tint)} .mpDot.contro{background:var(--orange)}", T)

    def test_pre_analisi_spostata_in_oggi(self):
        self.assertNotIn('id="pvCard"', oggi())
        p = cut('<div class="view" id="v-posizioni"', '<div class="view" id="v-opzioni"')
        self.assertIn('id="pvCard"', p)                                           # in Posizioni resta un rimando
        self.assertIn('el.innerHTML = `<button type="button" class="wkMore" id="pvGo">', T)
        self.assertIn('$("qPre").scrollIntoView', T)

    def test_parole_al_posto_delle_sigle(self):
        o = cut("// ---- Oggi · schede-domanda (V2)", "(function renderPosLine() {")
        for w in ("EMA", "Trailing", "trailing", "W3.2", "OPEX", "σ"):
            self.assertNotIn(w, re.sub(r"//[^\n]*", "", o), w)
        self.assertIn('opex: "Scadenza opzioni", vix: "Paura sulle borse"', T)
        self.assertIn('replace(/\\bFOMC\\b/g, "Fed")', T)


@unittest.skipUnless(NODE, "node non disponibile")
class Frasi(unittest.TestCase):
    """Le funzioni delle schede, eseguite con node sui dati di ogni caso (stessi helper di formato della pagina)."""
    JS = "\n".join(["const window = {};", cut("const nfIT = window.nfIT", "const nfS = "), cut("const usd = ", "const css = "),
                    next(l for l in T.splitlines() if l.startswith("const artD = window.artD")),
                    cut("function qxAt(U, x) {", "(function renderWeekly() {"),
                    cut("// ---- Oggi · schede-domanda (V2). Funzioni comuni", "(function renderPosLine() {")])

    def run_case(self, R: dict, px: float, band=None, mp=None) -> dict:
        js = f"const R = {json.dumps(R)}; const REF = {{ px: {px} }};\n" + self.JS + f"""
const strip = s => s.replace(/<[^>]+>/g, "");
const O = ASSETS_Q().filter(a => isOpenX(a[2]) && a[2].uscite && a[2].uscite.calc);
console.log(JSON.stringify({{ pos: strip(qPosHtml().match(/<p class="qA">(.*?)<\\/p>/)[1]), pos_html: strip(qPosHtml()),
  exit: strip(qExitAns()), blocks: O.map(([t, , X, p]) => strip(qExitBlock(t, X, p, 360))),
  pre: strip(qPreAns({px}, "29/11", {json.dumps(band)})), mp: strip(qMpAns({json.dumps((mp or {}).get("side"))}, {json.dumps((mp or {}).get("c"))})) }}));"""
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "x.js"
            p.write_text(js)
            out = subprocess.run([NODE, str(p)], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_short_aperti_report_del_26_11(self):
        R = {"weekly": pos(BTC), "weekly_eth": pos(ETH, entry="2026-11-09")}
        o = self.run_case(R, BTC["price"], mp={"side": "short", "c": {"favore": 1, "neutro": 3, "contro": 2}})
        # 30.000 $ × 7,23% = 2.169 $ (BTC) + 4.971 $ (ETH) = 7.140 $ su 60.000 $: gli stessi numeri del report e di Posizioni
        self.assertEqual(o["pos"], "Bene: +$7.140 in tutto (+11,9%).")
        self.assertIn("Bitcoin · shortdal 16/11, ingresso $65.286+$2.169+7,2%", o["pos_html"])
        self.assertIn("Ethereum · shortdal 09/11, ingresso $2.125+$4.971+16,6%", o["pos_html"])
        self.assertEqual(o["exit"], "Non prima di domenica 29/11, a meno che BTC salga del 25% e tocchi lo stop mobile.")
        u = R["weekly"]["uscite"]
        self.assertEqual((round(u["ema21"]["usd"]), round(u["trail"]["usd"])), (-4051, -4718))
        b = o["blocks"][0]
        for s in ("esce in perdita sopra$74.273domenica · −$4.051", "esce in profittodistribuzioneoggi no · varrebbe +$2.12",
                  "Stop mobile a $75.764 (−$4.718), controllato ogni ora.", "Sotto ~$47.800 lo stop passa in utile.", "sotto 47.800", "uscite in perdita"):
            self.assertIn(s, b)
        e = round(R["weekly_eth"]["uscite"]["ema21"]["usd"])
        self.assertIn(f"esce in perdita sopra$2.209domenica · −${abs(e)}", o["blocks"][1])
        self.assertIn("Stop mobile a $2.311 (−$2.160)", o["blocks"][1])
        self.assertEqual(o["pre"], "Domenica 29/11 restano aperte: nessuna uscita è vicina.")
        self.assertEqual(o["mp"], "Non del tutto: 1 segnale a favore, 2 contro, 3 neutri.")

    def test_long_aperto(self):
        L = dict(BTC, side="long", entry_px=55000.0, price=60458.01, best=61000.0, trail=50000.0, ema21=56500.0, pnl_pct=9.5, flow=0.8)
        R = {"weekly": pos(L), "weekly_eth": {"status": "flat", "side": None, "week": "2026-11-22"}}
        o = self.run_case(R, L["price"], mp={"side": "long", "c": {"favore": 2, "neutro": 3, "contro": 1}})
        self.assertEqual(o["pos"], "Bene: +$2.850 sulla posizione aperta (+9,5%).")
        self.assertIn("Ethereum · nessuna posizioneprossima decisione domenica 29/11", o["pos_html"])
        self.assertEqual(o["exit"], "Non prima di domenica 29/11, a meno che BTC scenda del 17% e tocchi lo stop mobile.")
        self.assertIn("esce in perdita a$50.000stop mobile", o["blocks"][0])
        self.assertIn("esce in profitto sotto$56.500domenica", o["blocks"][0])          # la media a 21 settimane è sopra l'ingresso
        self.assertEqual(o["pre"], "Domenica 29/11 resta aperta: nessuna uscita è vicina.")
        self.assertEqual(o["mp"], "Per lo più sì: 2 segnali a favore, 1 contro, 3 neutri.")

    def test_nessuna_posizione(self):
        f = {"status": "flat", "side": None, "week": "2026-11-22"}
        R = {"weekly": dict(f), "weekly_eth": dict(f)}
        o = self.run_case(R, 60458.0, band={"outcome": "none"}, mp={"side": None, "c": {"favore": 0, "neutro": 6, "contro": 0}})
        self.assertEqual(o["pos"], "Nessuna posizione aperta: si aspetta il prossimo segnale.")
        self.assertEqual(o["exit"], "Nessuna posizione aperta, niente da chiudere. La prossima decisione è domenica 29/11.")
        self.assertEqual(o["blocks"], [])
        self.assertEqual(o["pre"], "Domenica 29/11 nessun ingresso: con i dati di oggi le condizioni non ci sono.")
        self.assertEqual(o["mp"], "Nessuna posizione aperta: i semafori dicono solo com'è il mercato.")
        o = self.run_case(R, 57000.0, band={"outcome": "short"})
        self.assertEqual(o["pre"], "Se domenica 29/11 chiude come oggi, scatta un segnale short: ingresso lunedì.")
        R["weekly"] = dict(f, status="segnale", side="short")
        self.assertEqual(self.run_case(R, 57000.0)["pos"], "Nessuna posizione aperta: lunedì BTC entra short.")

    def test_uscita_imminente(self):
        # BTC chiude sopra la media a 21 settimane: se domenica resta così esce; ETH ha già il segnale di uscita (esce lunedì)
        R = {"weekly": pos(BTC, ema21=60000.0), "weekly_eth": pos(ETH, status="uscita", entry="2026-11-09", reason="ema")}
        o = self.run_case(R, 60458.01)
        self.assertEqual(o["exit"], "ETH esce lunedì 23/11 all'apertura, per la chiusura oltre la media a 21 settimane. "
                                    "Se domenica 29/11 chiude come oggi, BTC esce in profitto: è sopra $60.000.")
        self.assertEqual(o["pre"], "ETH esce lunedì 23/11: l'uscita è già decisa. Se domenica 29/11 chiude come oggi, BTC esce.")
        self.assertIn("esce lunedì 23/11", o["pos_html"])
        # vicina ma non ancora oltre: la frase lo dice con la distanza
        o = self.run_case({"weekly": pos(BTC, ema21=62000.0)}, 60458.01)
        self.assertEqual(o["pre"], "Domenica 29/11 resta aperta, ma BTC è a 3% dalla soglia di uscita.")
        # distribuzione attiva alla chiusura della domenica
        R = {"weekly": pos(BTC)}
        R["weekly"]["uscite"]["dist"]["attiva"] = True
        o = self.run_case(R, 60458.01)
        self.assertEqual(o["exit"], "Se domenica 29/11 resta così, BTC esce in profitto per distribuzione.")
        self.assertIn("attiva: decide domenica", o["blocks"][0])

    def test_dati_mancanti(self):
        o = self.run_case({}, 60458.0)
        self.assertEqual(o["pos"], "Dati delle posizioni non disponibili in questo momento.")
        self.assertEqual(o["exit"], "Dati delle uscite non disponibili in questo momento.")
        self.assertEqual(o["pre"], "Pre-analisi non disponibile in questo momento.")
        self.assertEqual(o["mp"], "Dati del mercato non disponibili in questo momento.")
        R = {"weekly": dict(pos(BTC), uscite=None)}
        o = self.run_case(R, 60458.0)
        self.assertEqual(o["exit"], "Uscite non disponibili per BTC: vedi i Dettagli.")
        self.assertEqual(o["pos"], "Bene: +$2.169 sulla posizione aperta (+7,2%).")      # risultato dal report (pnl_pct)

    def test_frasi_senza_consigli(self):
        src = cut("// ---- Oggi · schede-domanda (V2). Funzioni comuni", "(function renderPosLine() {")
        for w in ("compra", "vendi", "conviene", "dovresti", "consiglio", "andrà", "arriverà"):
            self.assertNotIn(w, src.lower())


if __name__ == "__main__":
    unittest.main()
