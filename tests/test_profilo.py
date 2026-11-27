"""Accesso al tool e pagina Profilo (27/11/2026): schermata di accesso globale (AUTH_GATE nel template, protezione "di facciata"),
saltata con ?demo=1 in locale e spenta senza Supabase; profilo in sidebar e avatar sul telefono; pagina Profilo con le sue sezioni
(Account, Il mio capitale, Bot Telegram, Preferenze, Dati, Info); CSV del Wallet da dati finti; barra in basso a scorrimento.
Niente rete esterna: la libreria Supabase nel browser è sostituita da un finto client (window.supabase prima del caricamento)."""
import functools
import http.server
import re
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from radar import dashboard

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
PROF = (ROOT / "radar" / "pages" / "profilo.html").read_text()
REPORT = {"date": "2026-11-26", "price": 60000.0, "updated_4h": "2026-11-27 12:00:00"}
FINTO = {"url": "https://finto.supabase.co", "anon": "sb_publishable_finto"}
# finto supabase-js: nessuna sessione salvata, accesso sempre riuscito, reset registrato in window.__reset
STUB = """window.__reset = null; window.supabase = { createClient: () => { const subs = [];
  const auth = {
    onAuthStateChange(f) { subs.push(f); return { data: { subscription: { unsubscribe() {} } } }; },
    async getSession() { return { data: { session: window.__sess || null } }; },
    async signInWithPassword({ email }) { const u = { email, user_metadata: {} }; window.__sess = { user: u }; subs.forEach(f => f("SIGNED_IN", window.__sess)); return { data: { user: u }, error: null }; },
    async resetPasswordForEmail(email, o) { window.__reset = { email, redirectTo: o && o.redirectTo }; return { error: null }; },
    async signOut() { window.__sess = null; subs.forEach(f => f("SIGNED_OUT", null)); return { error: null }; },
    async updateUser(x) { return { data: { user: window.__sess.user }, error: null }; } };
  return { auth, from() { return { select() { return { order: async () => ({ data: [], error: null }) }; } }; } }; } };"""


class Markup(unittest.TestCase):
    def test_gate_nel_template(self):
        self.assertIn("const AUTH_GATE = true;", T)
        self.assertIn('protezione "di facciata"', T)                              # dichiarato nel codice
        self.assertIn("const ON = AUTH_GATE && CONF && !DEMO;", T)               # senza Supabase o in demo locale: spento
        self.assertIn('const DEMO = /[?&]demo=1(&|$)/.test(location.search) && LOCAL;', T)
        self.assertIn('<div class="authGate" id="authGate" hidden></div>', T)
        self.assertLess(T.index('id="authGate"'), T.index("<!--__PAGES__-->"))   # RadarAuth pronto prima delle pagine
        self.assertIn("resetPasswordForEmail(email, { redirectTo:", T)
        self.assertIn("updateUser({ password: pw })", T)
        self.assertIn("Password dimenticata?", T)
        self.assertNotIn("signUp", T + PROF)
        self.assertIn(".authLock .shell,.authLock .tabbar{visibility:hidden}", T)

    def test_schermata_accesso_essenziale(self):
        show = re.search(r"function show\(msg\) \{(.*?)\n  \}", T, re.S).group(1)
        self.assertIn("<h1>Accedi a RadarSignal</h1>", show)
        self.assertNotIn("Nessuna registrazione", T)                              # niente descrizione sotto il titolo
        self.assertNotIn("agFoot", T)                                             # niente frase finale in fondo
        self.assertIn('id="agForm" novalidate>${logo}', show)                     # logo dentro la card
        bg = re.search(r"const BG = `(<svg class=\"agBg\".*?</svg>)`;", T, re.S).group(1)
        self.assertLess(len(bg.encode()), 15000)                                  # sfondo leggero, SVG inline
        self.assertNotRegex(bg, r"https?:|<image|href=")                          # nessuna immagine esterna
        self.assertIn("@media (prefers-reduced-motion:reduce){.agWait .spin,.agBgM{animation:none}}", T)
        self.assertIn("color-scheme:dark;", T)                                    # ingresso sempre scuro, anche col tema chiaro

    def test_profilo_in_sidebar_e_avatar_telefono(self):
        side = re.search(r'<aside class="side">(.*?)</aside>', T, re.S).group(1)
        self.assertIn('<a class="me" href="#profilo" data-v="profilo"', side)
        self.assertNotIn('class="promo"', T)                                     # la card "Alert su Telegram" è passata nel Profilo
        mbar = re.search(r'<header class="mbar">(.*?)</header>', T, re.S).group(1)
        self.assertIn('<a class="reload meBtn" href="#profilo" data-v="profilo" title="Profilo" aria-label="Profilo e impostazioni" data-me-ini>', mbar)
        self.assertLess(mbar.index("toggleTheme()"), mbar.index("meBtn"))
        tab = re.search(r'<nav class="tabbar" aria-label="Sezioni">(.*?)</nav>', T, re.S).group(1)
        self.assertNotIn("profilo", tab)
        self.assertIn("@media (min-width:900px){#v-profilo .prHead{display:none}}", PROF)   # desktop: niente profilo sotto il prezzo

    def test_pagina_profilo(self):
        self.assertIn('<div class="view" id="v-profilo" hidden>', PROF)
        self.assertIn("window.PAGES.profilo = {", PROF)
        for h in ("Account", "Il mio capitale", "Bot Telegram", "Preferenze", "Dati", "Info"):
            self.assertRegex(PROF, rf'<h2 class="sh" id="pr\w+H">{h}')
        self.assertIn("https://t.me/${BOT}", PROF)
        self.assertIn('const BOT = "CryptoRadarGalaBot";', PROF)
        self.assertIn("lista proposta", PROF)
        for c in ("/entrato", "/aggiungi", "/uscito", "/registro"):
            self.assertIn(f'["{c}"', PROF)
        self.assertNotIn("sendMessage", PROF)                                      # nessun avviso Telegram da qui
        self.assertIn("Strumento di analisi, non consulenza finanziaria", PROF)
        self.assertIn('href="#metodo"', PROF)
        self.assertIn('ls.set("radarStart"', PROF)
        self.assertIn("try { return localStorage.getItem(k); } catch (_) { return null; }", PROF)
        self.assertIn("<b>Aliquota sulle plusvalenze %</b>", PROF)                     # in "Il mio capitale", salvata in user_metadata.aliquota
        self.assertIn("window.WalletAPI.setAliquota(v)", PROF)
        self.assertIn("Stima, non consulenza fiscale.", PROF)

    def test_versione_iniettata(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(dashboard, "build_info", return_value={"commit": "abc1234"}):
            html = dashboard.render(REPORT, Path(t) / "index.html").read_text()
        self.assertIn('window.RADAR_BUILD = {"commit": "abc1234"};', html)
        self.assertNotIn("/*__BUILD__*/", html)


class NelBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("playwright non installato")
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        with mock.patch.object(dashboard, "supabase_config", return_value=FINTO):
            dashboard.render(REPORT, d / "on" / "index.html")
        with mock.patch.object(dashboard, "supabase_config", return_value=None):
            dashboard.render(REPORT, d / "off" / "index.html")

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

    def pagina(self, path, w=400, stub=True, init=""):
        ctx = self.b.new_context(viewport={"width": w, "height": 860})
        if stub:
            ctx.add_init_script(STUB)
        if init:
            ctx.add_init_script(init)
        pg = ctx.new_page()
        self.errs = []
        pg.on("pageerror", lambda e: self.errs.append(str(e)))
        pg.route("**/*", lambda r: r.continue_() if "127.0.0.1" in r.request.url else r.abort())
        pg.goto(f"http://127.0.0.1:{self.srv.server_port}/{path}")
        return ctx, pg

    def test_gate_presente_senza_sessione(self):
        ctx, pg = self.pagina("on/index.html#oggi")
        pg.wait_for_selector("#agForm", timeout=5000)
        self.assertTrue(pg.is_visible("#authGate"))
        self.assertEqual(pg.evaluate("getComputedStyle(document.querySelector('.shell')).visibility"), "hidden")
        self.assertEqual(pg.evaluate("getComputedStyle(document.querySelector('.tabbar')).visibility"), "hidden")
        self.assertEqual(pg.locator("#agForm input").count(), 2)                   # solo email e password
        self.assertEqual(pg.inner_text("#agForm h1"), "Accedi a RadarSignal")
        self.assertTrue(pg.is_visible("#authGate svg.agBg"))
        self.assertEqual(pg.evaluate("Math.round(document.querySelector('#agForm input').getBoundingClientRect().height)"), 56)
        self.assertEqual(pg.evaluate("getComputedStyle(document.querySelector('.agCard')).borderRadius"), "24px")   # 28px oltre 440px
        sw, cw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        self.assertLessEqual(sw, cw)
        self.assertIn("Password dimenticata?", pg.inner_text("#authGate"))
        self.assertNotIn("Registrati", pg.inner_text("#authGate"))
        pg.click("#agReset")                                                      # senza email: chiede l'email
        self.assertIn("Scrivi la tua email", pg.inner_text("#agErr"))
        pg.fill("#agForm input[name=email]", "mario.rossi@example.com")
        pg.click("#agReset")
        pg.wait_for_function("window.__reset")
        self.assertEqual(pg.evaluate("window.__reset.email"), "mario.rossi@example.com")
        self.assertTrue(pg.evaluate("window.__reset.redirectTo.endsWith('/on/index.html')"))
        self.assertIn("arriva un'email", pg.inner_text("#agOk"))
        pg.fill("#agForm input[name=pw]", "segreta")
        pg.click("#agForm .agBtn")
        pg.wait_for_function("document.getElementById('authGate').hidden")
        self.assertEqual(pg.evaluate("getComputedStyle(document.querySelector('.shell')).visibility"), "visible")
        pg.wait_for_function("document.querySelector('.mbar .meBtn').textContent.trim() === 'MR'", timeout=3000)   # avatar con le iniziali
        self.assertEqual(pg.inner_text(".side .me [data-me-mail]"), "mario.rossi@example.com")
        self.assertTrue(pg.evaluate("window.RadarAuth.gate"))
        pg.evaluate("window.RadarAuth.signOut()")                                 # uscita: torna la schermata di accesso
        pg.wait_for_selector("#agForm", timeout=5000)
        self.assertEqual(self.errs, [])
        ctx.close()

    def test_gate_saltato_in_demo_e_senza_supabase(self):
        for path in ("on/index.html?demo=1#oggi", "off/index.html#oggi"):
            ctx, pg = self.pagina(path)
            pg.wait_for_timeout(300)
            self.assertTrue(pg.is_hidden("#authGate"), path)
            self.assertFalse(pg.evaluate("window.RadarAuth.gate"), path)
            self.assertTrue(pg.is_visible("#v-oggi"), path)
            self.assertEqual(self.errs, [], path)
            ctx.close()

    def test_profilo_sezioni_e_csv(self):
        for w in (360, 1280):
            ctx, pg = self.pagina("on/index.html?demo=1#profilo", w)
            pg.wait_for_selector("#prCsv:not([disabled])", timeout=5000)
            heads = pg.locator("#v-profilo h2.sh").all_inner_texts()
            self.assertEqual([h.split("\n")[0].strip() for h in heads], ["Account", "Il mio capitale", "Bot Telegram", "Preferenze", "Dati", "Info"])
            self.assertIn("demo@radar.local", pg.inner_text("#prAccB"))
            self.assertIn("Cambia password", pg.inner_text("#prAccB"))
            self.assertIn("$10.000", pg.inner_text("#prCapB"))
            self.assertIn("33%", pg.inner_text("#prAliqV"))                                # predefinita: Italia dal 2026
            self.assertIn("predefinita", pg.inner_text("#prCapB"))
            self.assertIn("@CryptoRadarGalaBot", pg.inner_text("#prBotB"))
            self.assertEqual(pg.locator("#prBotB .prSt").count(), 19)
            self.assertEqual(pg.get_attribute("#prBotB a.waCta", "href"), "https://t.me/CryptoRadarGalaBot")
            self.assertIn("26 novembre 2026", pg.inner_text("#prDatiB"))
            self.assertEqual(pg.get_attribute('.side a.me', "aria-current"), "page")
            self.assertEqual(pg.is_visible("#v-profilo .prHead"), w < 900, f"{w}px")   # intestazione con avatar solo su telefono
            sw, cw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            self.assertLessEqual(sw, cw, f"{w}px")
            with pg.expect_download() as dl:
                pg.click("#prCsv")
            txt = Path(dl.value.path()).read_bytes().decode("utf-8-sig")
            self.assertTrue(txt.startswith("posizione;moneta;lato;mercato;leva;"))
            self.assertEqual(len(txt.strip().split("\r\n")), 1 + 6)                # 4 posizioni demo, 6 movimenti
            self.assertEqual(self.errs, [])
            ctx.close()

    def test_aliquota_dal_profilo_al_wallet(self):
        ctx, pg = self.pagina("on/index.html?demo=1#profilo")
        pg.wait_for_selector("#prAliqE", timeout=5000)
        pg.click("#prAliqE")
        pg.wait_for_selector("#sheet[open] input[name=al]")
        self.assertGreaterEqual(pg.locator("#sheet button[type=submit]").bounding_box()["height"], 44)
        pg.fill("#sheet input[name=al]", "150")
        pg.click("#sheet button[type=submit]")
        self.assertIn("tra 0 e 100", pg.inner_text("#sheet .err"))                       # validazione
        pg.fill("#sheet input[name=al]", "26,5")
        pg.click("#sheet button[type=submit]")
        pg.wait_for_function("!document.getElementById('sheet').open")
        self.assertEqual(pg.inner_text("#prAliqV"), "26,5%")
        self.assertNotIn("predefinita", pg.inner_text("#prCapB"))
        self.assertEqual(pg.evaluate("window.WalletAPI.aliquota().then(a => a.value)"), 26.5)
        pg.evaluate("location.hash = '#wallet'")                                          # il Wallet usa l'aliquota del profilo
        pg.wait_for_selector("#waHero .waTax", timeout=5000)
        self.assertIn("aliquota 26,5% dal Profilo", pg.inner_text("#waHero"))
        self.assertIn("aliquota 26,5%", pg.inner_text("#waTaxY"))
        pg.evaluate("window.WalletAPI.setAliquota(null)")                                 # vuoto: torna la predefinita
        pg.wait_for_function("document.getElementById('waHero').innerText.includes('aliquota 33% (Italia)')")
        self.assertEqual(self.errs, [])
        ctx.close()

    def test_csv_da_dati_finti(self):
        ctx, pg = self.pagina("off/index.html#oggi")
        pg.wait_for_function("window.WalletCalc")
        csv = pg.evaluate("""() => window.WalletCalc.toCSV(
          [{ id: "p1", asset: "BTC", lato: "short", mercato: "perp", leva: 3, exchange: "Bitget", strategia: "W3.2", segnale_data: "2026-11-15", stato: "aperta", note: 'nota; con "virgolette"', created_at: "2026-11-16T10:00:00Z" },
           { id: "p2", asset: "PIEVERSE", lato: "long", mercato: "perp", leva: 5, exchange: "OKX", strategia: "fuori segnale", segnale_data: null, stato: "aperta", note: null, created_at: "2026-11-24T09:00:00Z" }],
          [{ id: "m2", posizione_id: "p1", tipo: "aggiunta", data: "2026-11-20T15:45:00Z", prezzo: 62800, quantita: 0.1, margine: null, commissioni: 3.8, funding: 2.4, note: null },
           { id: "m1", posizione_id: "p1", tipo: "ingresso", data: "2026-11-16T10:20:00Z", prezzo: 65420.5, quantita: 0.15, margine: 3271, commissioni: 5.9, funding: 0, note: "prima" }])""")
        self.assertTrue(csv.startswith("﻿posizione;moneta;"))
        rows = csv[1:].strip().split("\r\n")
        self.assertEqual(len(rows), 4)                                             # intestazione + 2 movimenti + posizione senza movimenti
        self.assertEqual(rows[1], 'p1;BTC;short;perp;3;Bitget;W3.2;2026-11-15;aperta;ingresso;2026-11-16T10:20:00Z;65420,5;0,15;3271;5,9;0;prima;"nota; con ""virgolette"""')
        self.assertTrue(rows[2].startswith("p1;BTC;short;perp;3;Bitget;W3.2;2026-11-15;aperta;aggiunta;2026-11-20T15:45:00Z;62800;0,1;;3,8;2,4;"))
        self.assertEqual(rows[3], "p2;PIEVERSE;long;perp;5;OKX;fuori segnale;;aperta;;;;;;;;;")
        self.assertEqual(self.errs, [])
        ctx.close()

    def test_pagina_iniziale_salvata(self):
        ctx, pg = self.pagina("off/index.html", init="try{localStorage.setItem('radarStart','posizioni')}catch(e){}")
        pg.wait_for_timeout(300)
        self.assertEqual(pg.evaluate("location.hash"), "#posizioni")
        self.assertTrue(pg.is_hidden("#v-oggi"))
        ctx.close()
        ctx, pg = self.pagina("off/index.html#notizie", init="try{localStorage.setItem('radarStart','wallet')}catch(e){}")
        pg.wait_for_timeout(300)
        self.assertEqual(pg.evaluate("location.hash"), "#notizie")               # l'indirizzo esplicito vince
        ctx.close()

    def test_barra_in_basso_scorre_solo_lei(self):
        for w in (360, 400):
            ctx, pg = self.pagina("off/index.html?demo=1#notizie", w)
            pg.wait_for_timeout(400)
            sw, cw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            self.assertLessEqual(sw, cw, f"{w}px")                                # la pagina non scorre in orizzontale
            r = pg.evaluate("""() => { const t = document.querySelector('.tabbar .tbs'), a = t.querySelector('a[aria-current="page"]');
              const tb = t.getBoundingClientRect(), ab = a.getBoundingClientRect();
              return { sw: t.scrollWidth, cw: t.clientWidth, x: t.scrollLeft, cls: t.className, inView: ab.left >= tb.left - 1 && ab.right <= tb.right + 1,
                       labels: [...t.querySelectorAll('a')].filter(x => !x.hidden).map(x => [x.textContent.trim(), x.offsetWidth, x.offsetHeight, x.scrollWidth <= x.clientWidth]) }; }""")
            self.assertGreater(r["sw"], r["cw"])                                   # c'è altro da scorrere
            self.assertTrue(r["inView"])                                           # voce attiva (Notizie, l'ultima) portata in vista
            self.assertGreater(r["x"], 0)
            self.assertIn("fl", r["cls"])                                          # sfumatura sul bordo sinistro
            self.assertEqual([x[0] for x in r["labels"]], ["Oggi", "Posizioni", "Wallet", "Opzioni", "Scanner", "Grafico", "Movimenti", "Notizie"])
            for name, wd, ht, fits in r["labels"]:
                self.assertGreaterEqual(wd, 64, name)
                self.assertGreaterEqual(ht, 44, name)
                self.assertTrue(fits, name)                                        # etichetta intera, non tagliata
            self.assertEqual(self.errs, [])
            ctx.close()


if __name__ == "__main__":
    unittest.main()
