"""Wallet reale (radar/pages/wallet.html, supabase/schema.sql, radar/dashboard.py supabase_config): voce di menu, vista senza
configurazione, calcoli in window.WalletCalc (prezzo medio DCA, P/L, liquidazione stimata, leva massima, deriva rispetto a W3.2,
calo massimo), anteprima demo, schema con RLS su entrambe le tabelle, nessuna chiave segreta nel repository. Niente rete esterna."""
import base64
import functools
import http.server
import json
import os
import re
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from radar import dashboard

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
PAGE = (ROOT / "radar" / "pages" / "wallet.html").read_text()
SQL = (ROOT / "supabase" / "schema.sql").read_text()

WEEKLY = {"price": 60000.0, "status": "aperto", "side": "short", "signal_date": "2026-11-15", "entry": "2026-11-16", "entry_px": 65000.0,
          "trail": 75000.0, "history": {"start": "2021-01-01", "trades": [
              {"signal": "2026-08-23", "entry": "2026-08-24", "side": "long", "entry_px": 77000.0, "exit": "2026-11-09", "exit_px": 74000.0, "reason": "ema"},
              {"signal": "2026-11-15", "entry": "2026-11-16", "side": "short", "entry_px": 65000.0, "exit": None, "exit_px": None, "reason": "open"}]}}
REPORT = {"date": "2026-11-26", "price": 60000.0}   # report minimo per la pagina; i dati W3.2 si aggiungono a R nel browser (MODELLO)
MODELLO = {"weekly": WEEKLY,
          "weekly_eth": dict(WEEKLY, price=1700.0, signal_date="2026-11-08", entry="2026-11-09", entry_px=2125.0, trail=2310.0,
                             history={"start": "2021-01-01", "trades": [{"signal": "2026-11-08", "entry": "2026-11-09", "side": "short", "entry_px": 2125.0,
                                                                          "exit": None, "exit_px": None, "reason": "open"}]})}


def dashboard_nf2(x: float) -> str:
    """Numero all'italiana con 2 decimali, come nfIT: 1234.5 -> "1.234,50"."""
    return f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _jwt(role: str) -> str:
    enc = lambda o: base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")
    return f"{enc({'alg': 'HS256'})}.{enc({'role': role, 'iss': 'supabase'})}.firma"


class Markup(unittest.TestCase):
    def test_voce_di_menu_wallet(self):
        for nav in (r'<nav aria-label="Sezioni">(.*?)</nav>', r'<nav class="tabbar" aria-label="Sezioni">(.*?)</nav>'):
            box = re.search(nav, T, re.S).group(1)
            self.assertIn('<a href="#wallet" data-v="wallet"><svg><use href="#i-wal"/></svg>Wallet</a>', box)
        self.assertIn('<div class="view" id="v-wallet" hidden>', PAGE)
        self.assertIn('"wallet"', re.search(r"const VIEWS = \[([^\]]*)\]", T).group(1))
        self.assertIn('const PAGE_OF = Object.assign({ wallet: "wallet", profilo: "profilo" }', T)
        self.assertIn("window.PAGES.wallet = {", PAGE)
        self.assertNotIn("const R = ", PAGE)                    # i test leggono il report dalla prima "const R = " della pagina

    def test_vecchio_wallet_hyperliquid_non_raggiungibile(self):
        old = (ROOT / "radar" / "pages" / "hyperliquid.html").read_text()
        self.assertIn('id="v-hyperliquid"', old)
        self.assertIn("window.PAGES.hyperliquid = {", old)
        self.assertNotIn('id="v-wallet"', old)
        self.assertNotIn("hyperliquid", re.search(r"const VIEWS = \[([^\]]*)\]", T).group(1))
        self.assertNotIn('href="#hyperliquid"', T)

    def test_supabase_da_cdn_versione_esatta(self):   # dal 27/11/2026 il caricamento e il client unico sono nel template (window.RadarAuth)
        m = re.search(r'const SB_SRC = "https://cdn\.jsdelivr\.net/npm/@supabase/supabase-js@(\d+)\.(\d+)\.(\d+)/dist/umd/supabase\.js"', T)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "2")
        self.assertGreaterEqual(int(m.group(2)), 40)            # chiavi sb_publishable_ supportate
        self.assertRegex(T, r'const SB_SRI = "sha384-[A-Za-z0-9+/=]{64}"')
        self.assertIn("const CFG = /*__SUPABASE__*/null;", PAGE)
        self.assertNotIn("SB_SRC", PAGE)                        # una sola istanza: il Wallet usa window.RadarAuth.client()
        self.assertNotIn("createClient", PAGE)
        self.assertIn("window.RadarAuth.client()", PAGE)
        self.assertEqual(T.count("createClient(CFG.url"), 1)
        for src in (PAGE, T):
            self.assertNotIn("signUp", src)                     # nessuna registrazione dalla pagina
        self.assertNotIn("Telegram", PAGE)

    def test_confronto_accordion_chiuso(self):
        sec = re.search(r'<details class="section waAcc" id="waCmpSec">(.*?)</details>', PAGE, re.S)
        self.assertIsNotNone(sec)                               # <details> senza "open": chiuso di default
        self.assertIn('<summary class="card"><span class="waAccT"><b>Confronto con la strategia</b><small id="waCmpSum">', sec.group(1))
        self.assertIn("Deriva totale", PAGE)
        self.assertIn("driftSum(cmps)", PAGE)

    def test_pulsanti_con_icona_e_aria_label(self):
        for icon, label in (("plus", "Apri posizione"), ("out", "Esci dall'account")):
            self.assertRegex(PAGE, rf'<button type="button" class="waCta [a-z ]+" id="wa\w+" aria-label="{label}"><svg class="waI" aria-hidden="true"><use href="#i-{icon}"/></svg>')
        # etichette d'azione dal 27/11/2026: Aumenta (era Tranche), Riduci o chiudi, Storico (era Movimenti), Modifica, Elimina
        for icon, label, aria in (("plus", "Aumenta", "Aumenta la posizione"), ("minus", "Riduci o chiudi", "Riduci o chiudi la posizione"), ("list", "Storico", "Storico della posizione"),
                                  ("edit", "Modifica", "Modifica movimento"), ("trash", "Elimina", "Elimina movimento")):
            self.assertRegex(PAGE, rf'cta\("[a-z ]+", [^)]*"{icon}", "{label}", "[^"]*", "{aria}"\)')
            self.assertIn(f'<symbol id="i-{icon}"', T)
        self.assertIn('class="waCta ${kind}" ${attrs} aria-label="${esc(aria || label)}"><svg class="waI" aria-hidden="true">', PAGE)
        for vecchia in ('"Tranche"', '"Movimenti"', "Aggiungi tranche", "Nuova posizione", "Riduci / chiudi"):
            self.assertNotIn(vecchia, PAGE)
        self.assertIn("window.openSheet(`Storico · ${pos.asset}`, box)", PAGE)
        css = re.search(r"\.waCta\{[^}]*\}", PAGE).group(0)
        self.assertIn("min-height:var(--h)", css)
        self.assertIn("--h:44px", css)                          # area di tocco di almeno 44 px
        for st in (".waCta:focus-visible{", ".waCta:disabled", ".waCta.pri:hover", ".waCta.pri{", ".waCta.sec{", ".waCta.ter{", ".waCta.del{"):
            self.assertIn(st, PAGE)

    def test_demo_solo_in_locale(self):
        self.assertIn('/[?&]demo=1(&|$)/.test(location.search) && (location.protocol === "file:" || /^(localhost|127\\.0\\.0\\.1|\\[::1\\])$/.test(location.hostname))', PAGE)


class Schema(unittest.TestCase):
    def test_tabelle_e_rls(self):
        for t in ("wallet_posizioni", "wallet_movimenti"):
            self.assertIn(f"create table if not exists public.{t}", SQL)
            self.assertIn(f"alter table public.{t} enable row level security;", SQL)
            for op in ("select", "insert", "update", "delete"):
                pol = re.search(rf"create policy {t}_{op} on public\.{t} for {op} to authenticated ([^;]*);", SQL)
                self.assertIsNotNone(pol, f"{t} {op}")
                self.assertIn("user_id = auth.uid()", pol.group(1))
                self.assertIn(f"drop policy if exists {t}_{op} on public.{t};", SQL)   # script rieseguibile
        self.assertEqual(SQL.count("user_id       uuid not null default auth.uid() references auth.users (id) on delete cascade"), 2)
        self.assertIn("references public.wallet_posizioni (id) on delete cascade", SQL)
        for k in ("'spot', 'perp', 'opzione'", "'long', 'short'", "'Bitget', 'OKX', 'altro'", "'aperta', 'chiusa'", "'W3.2', 'scanner', 'fuori segnale'",
                  "'ingresso', 'aggiunta', 'riduzione', 'chiusura'", "commissioni   numeric not null default 0", "funding       numeric not null default 0"):
            self.assertIn(k, SQL)
        self.assertEqual(SQL.count("execute function public.wallet_set_updated_at()"), 2)
        self.assertNotRegex(SQL.lower(), r"\bdrop table\b")

    def test_nessuna_chiave_segreta_nel_repo(self):
        files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True).stdout.split()
        jwt = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.(eyJ[A-Za-z0-9_-]{8,})\.[A-Za-z0-9_-]+")
        for f in files:
            p = ROOT / f
            if not p.is_file() or p.suffix in (".png", ".jpg", ".gz", ".parquet", ".zip", ".ico", ".woff2") or p.stat().st_size > 5_000_000:
                continue
            txt = p.read_text(errors="ignore")
            self.assertIsNone(re.search(r"sb_secret_[A-Za-z0-9_-]{10,}", txt), f)
            for m in jwt.finditer(txt):
                body = m.group(1)
                role = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)) or b"{}").get("role")
                self.assertNotEqual(role, "service_role", f)
        cfg = json.loads((ROOT / "radar" / "wallet_config.json").read_text())
        self.assertTrue(cfg["url"].startswith("https://") and cfg["url"].endswith(".supabase.co"))
        self.assertTrue(cfg["anon"].startswith("sb_publishable_"))


class Config(unittest.TestCase):
    def test_file_e_override(self):
        with mock.patch.dict(os.environ, {"RADAR_SUPABASE_URL": "", "RADAR_SUPABASE_ANON": ""}):
            c = dashboard.supabase_config()
            self.assertEqual(c["anon"], json.loads(dashboard.WALLET_CONFIG.read_text())["anon"])
        with mock.patch.dict(os.environ, {"RADAR_SUPABASE_URL": "https://x.supabase.co/", "RADAR_SUPABASE_ANON": _jwt("anon")}):
            self.assertEqual(dashboard.supabase_config()["url"], "https://x.supabase.co")
        for bad in (_jwt("service_role"), "sb_" + "secret_abcdefghijklmnop"):
            with mock.patch.dict(os.environ, {"RADAR_SUPABASE_URL": "https://x.supabase.co", "RADAR_SUPABASE_ANON": bad}):
                self.assertIsNone(dashboard.supabase_config())
        with tempfile.TemporaryDirectory() as t, mock.patch.object(dashboard, "WALLET_CONFIG", Path(t) / "nessuno.json"), \
                mock.patch.dict(os.environ, {"RADAR_SUPABASE_URL": "", "RADAR_SUPABASE_ANON": ""}):
            self.assertIsNone(dashboard.supabase_config())

    def test_iniettata_nella_pagina(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(dashboard, "supabase_config", return_value={"url": "https://x.supabase.co", "anon": "sb_publishable_x</script>"}):
            html = dashboard.render(REPORT, Path(t) / "index.html").read_text()
        self.assertIn('const CFG = {"url": "https://x.supabase.co", "anon": "sb_publishable_x<\\/script>"};', html)
        self.assertNotIn("/*__SUPABASE__*/", html)


class NelBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("playwright non installato")
        cls.tmp = tempfile.TemporaryDirectory()
        with mock.patch.object(dashboard, "supabase_config", return_value=None):
            dashboard.render(REPORT, Path(cls.tmp.name) / "index.html")

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

    def pagina(self, w=400, q=""):
        pg = self.b.new_page(viewport={"width": w, "height": 860})
        self.errs = []
        pg.on("pageerror", lambda e: self.errs.append(str(e)))
        pg.route("**/*", lambda r: r.continue_() if "127.0.0.1" in r.request.url else r.abort())
        pg.goto(f"http://127.0.0.1:{self.srv.server_port}/index.html{q}#wallet")
        return pg

    def test_senza_configurazione(self):
        pg = self.pagina()
        pg.wait_for_selector("#waGate h2", timeout=5000)
        self.assertEqual(pg.inner_text("#waGate h2"), "Wallet non ancora configurato")
        self.assertTrue(pg.is_hidden("#waApp"))
        self.assertEqual(pg.get_attribute('.tabbar a[data-v="wallet"]', "aria-current"), "page")
        self.assertEqual(self.errs, [])
        pg.close()

    def test_calcoli(self):
        pg = self.pagina()
        pg.wait_for_function("window.WalletCalc")
        r = pg.evaluate("""() => { const C = window.WalletCalc;
          const movs = [{ tipo: "ingresso", data: "2026-11-16T10:00:00Z", prezzo: 65000, quantita: 0.1, margine: 2000, commissioni: 3 },
                        { tipo: "aggiunta", data: "2026-11-20T10:00:00Z", prezzo: 62000, quantita: 0.2, margine: null, commissioni: 2, funding: 1 }];
          const st = C.posState(movs, "short", 3);
          const red = C.posState(movs.concat([{ tipo: "riduzione", data: "2026-11-22T10:00:00Z", prezzo: 60000, quantita: 0.15, commissioni: 1 }]), "short", 3);
          const cl = C.posState(movs.concat([{ tipo: "chiusura", data: "2026-11-25T10:00:00Z", prezzo: 61000, quantita: 0.3 }]), "short", 3);
          const pie = C.posState([{ tipo: "ingresso", data: "2026-11-24T09:00:00Z", prezzo: 2.8, quantita: 178.5714, margine: 100 }], "long", 5);
          const model = { signal: "2026-11-15", entry: "2026-11-16", side: "short", entry_px: 64000, exit: null, exit_px: null };
          return { avg: st.avg, qty: st.qty, margin: st.margin, realized: st.realized,
            pnl: C.pnl(st, 60000), redAvg: red.avg, redQty: red.qty, redMargin: red.margin, redGross: red.gross,
            clOpen: cl.open, clGross: cl.gross, clAvgOut: cl.avgOut,
            liqS: C.liqPrice(st.avg, st.qty, st.margin, "short", "perp"), liqL: C.liqPrice(pie.avg, pie.qty, pie.margin, "long", "perp"),
            liqSpot: C.liqPrice(100, 1, 100, "long", "spot"), pieQty: pie.qty,
            lev: [C.levMax(0.15), C.levMax(0.30), C.levMax(-0.10), C.levMax(1.5), C.levMax(null)], stopD: C.stopD(63000, 75000, "short"),
            cmp: C.compare(st, "short", model, 60000), cmpCl: C.compare(cl, "short", model, 60000),
            mf: [C.modelFor(%s, null, "2026-11-17", "short"), C.modelFor(%s, "2026-08-23", "2026-11-17", "short"), C.modelFor(%s, null, "2026-11-17", "long")],
            dd: C.ddMax([{ t: "2026-01-02", d: 500 }, { t: "2026-01-03", d: -1000 }, { t: "2026-01-01", d: 0 }], 10000, 200),
            dd0: C.ddMax([{ t: "2026-01-02", d: 500 }, { t: "2026-01-03", d: -1000 }], null, 0),
            num: ["2,80", "65.286", "65.286,5", "66.100", "0.125", "1.234.567", "65286.5", "abc", "", "−3,5"].map(C.parseNum),
            stats: C.stats([{ st: cl, pos: { strategia: "W3.2" } }, { st: pie, pos: { strategia: "fuori segnale" } }]) }; }""" % ((json.dumps(WEEKLY["history"]["trades"]),) * 3))
        self.assertAlmostEqual(r["avg"], (65000 * 0.1 + 62000 * 0.2) / 0.3, places=6)            # prezzo medio DCA
        self.assertAlmostEqual(r["qty"], 0.3)
        self.assertAlmostEqual(r["margin"], 2000 + 62000 * 0.2 / 3, places=6)                   # margine inserito + stimato dalla leva
        self.assertAlmostEqual(r["realized"], -6)                                              # commissioni e funding
        self.assertAlmostEqual(r["pnl"]["usd"], (r["avg"] - 60000) * 0.3, places=6)            # short: guadagna se scende
        self.assertAlmostEqual(r["pnl"]["pctMargin"], r["pnl"]["usd"] / r["margin"] * 100, places=6)
        self.assertAlmostEqual(r["pnl"]["movePct"], (1 - 60000 / r["avg"]) * 100, places=6)
        self.assertAlmostEqual(r["redAvg"], r["avg"], places=6)                                # la riduzione non cambia il prezzo medio
        self.assertAlmostEqual(r["redQty"], 0.15)
        self.assertAlmostEqual(r["redMargin"], r["margin"] / 2, places=6)
        self.assertAlmostEqual(r["redGross"], (r["avg"] - 60000) * 0.15, places=6)
        self.assertFalse(r["clOpen"])
        self.assertAlmostEqual(r["clGross"], (r["avg"] - 61000) * 0.3, places=6)
        self.assertAlmostEqual(r["clAvgOut"], 61000)
        self.assertAlmostEqual(r["liqS"], (r["avg"] + r["margin"] / 0.3) / 1.005, places=4)    # margine isolato, mantenimento 0,5%
        self.assertAlmostEqual(r["liqL"], (2.8 - 100 / 178.5714) / 0.995, places=4)             # PIEVERSE 5x da 2,80: circa 2,25
        self.assertAlmostEqual(r["liqL"], 2.251, places=2)
        self.assertIsNone(r["liqSpot"])
        self.assertEqual(r["lev"], [5.0, 2.5, 10, 0.6, None])                                  # come radar/scanner.py lev_max
        self.assertAlmostEqual(r["stopD"], 12000 / 63000)
        c = r["cmp"]                                                                           # deriva contro W3.2
        inv = r["avg"] * 0.3
        real = ((r["avg"] - 60000) * 0.3 - 6) / inv * 100
        self.assertAlmostEqual(c["realPct"], real, places=6)
        self.assertAlmostEqual(c["modelPct"], (1 - 60000 / 64000) * 100, places=6)
        self.assertAlmostEqual(c["drift"], real - (1 - 60000 / 64000) * 100, places=6)
        self.assertAlmostEqual(c["driftUsd"], c["drift"] / 100 * inv, places=4)
        self.assertAlmostEqual(c["dPx"], -(64000 - r["avg"]) / 64000 * 100, places=6)          # short entrato sotto il modello: peggio
        self.assertLess(c["dPx"], 0)
        self.assertEqual(c["dDays"], 0)
        self.assertTrue(c["sameSide"])
        self.assertFalse(c["mClosed"])
        self.assertAlmostEqual(r["cmpCl"]["modelPct"], (1 - 61000 / 64000) * 100, places=6)    # modello aperto: fino alla tua uscita
        self.assertEqual(r["mf"][0]["signal"], "2026-11-15")
        self.assertEqual(r["mf"][1]["signal"], "2026-08-23")                                   # data del segnale indicata
        self.assertIsNone(r["mf"][2])                                                          # nessun long attivo al 17/11
        self.assertAlmostEqual(r["dd"]["usd"], -1000)
        self.assertAlmostEqual(r["dd"]["pct"], -1000 / 10500 * 100, places=6)
        self.assertAlmostEqual(r["dd0"]["usd"], -1000)
        self.assertIsNone(r["dd0"]["pct"])
        self.assertEqual(r["num"], [2.8, 65286, 65286.5, 66100, 0.125, 1234567, 65286.5, None, None, -3.5])
        s = r["stats"]
        self.assertEqual((s["n"], s["wins"], s["nSig"], s["nOff"]), (2, 1, 1, 1))
        self.assertEqual(self.errs, [])
        pg.close()

    def test_calcoli_operazioni_e_tasse(self):
        pg = self.pagina()
        pg.wait_for_function("window.WalletCalc")
        r = pg.evaluate("""() => { const C = window.WalletCalc;
          const W = { status: "aperto", side: "short", signal_date: "2026-11-15", trail: 75000 };
          const st = C.posState([{ tipo: "ingresso", data: "2026-11-16T10:00:00Z", prezzo: 65000, quantita: 0.1, margine: 2000 }], "short", 3);
          return {
            sz: [C.size("margine", 1000, 3, 60000), C.size("quantita", 0.05, 3, 60000), C.size("valore", 3000, 3, 60000), C.size("margine", 1000, 1, 60000), C.size("margine", 0, 3, 60000)],
            fr: [C.feeRate("Bitget", "perp"), C.feeRate("OKX", "perp"), C.feeRate("altro", "perp"), C.feeRate("Bitget", "spot")], fee: C.fee(3000, 0.06),
            pre: [C.preStrategy("short", W, null), C.preStrategy("long", W, null), C.preStrategy("long", null, { lato: "long", sig: "2026-11-22" }),
                  C.preStrategy("short", null, { lato: "long", sig: "2026-11-22" }), C.preStrategy("short", null, null), C.preStrategy("short", { status: "flat" }, null)],
            plan: C.plan({ px: 60000, qty: 0.05, lev: 3, lato: "short", mercato: "perp", stop: 75000, capital: 10000, feeRate: 0.06 }),
            plan10: C.plan({ px: 60000, qty: 0.05, lev: 10, lato: "short", mercato: "perp", stop: 75000, capital: 10000, feeRate: 0.06 }),
            planSpot: C.plan({ px: 2, qty: 100, lev: 1, lato: "long", mercato: "spot", stop: null, levMax: 4, capital: null, feeRate: 0.1 }),
            add: C.addPreview(st, 60000, 0.1, 2000, "short", "perp"),
            red: C.reducePreview(st, 60000, C.qtyOfPct(st.qty, 50), 0.06), redAll: C.reducePreview(st, 60000, C.qtyOfPct(st.qty, 100), 0.06),
            pct: [C.qtyOfPct(0.3, 25), C.qtyOfPct(0.3, 100), C.qtyOfPct(0, 50)],
            rate: [C.taxRate(null, 2026), C.taxRate(null, 2025), C.taxRate(20, 2026), C.taxRate("", 2027), C.taxRate(0, 2026)],
            ty: C.taxYears([{ t: "2026-03-01T10:00:00Z", d: 3000 }, { t: "2026-06-01T10:00:00Z", d: -1200 }, { t: "2025-05-01T10:00:00Z", d: -500 },
                            { t: "2025-09-01T10:00:00Z", d: 200 }, { t: "2024-01-10T10:00:00Z", d: 1000 }], null),
            tyAl: C.taxYears([{ t: "2026-03-01T10:00:00Z", d: 3000 }], 20),
            tc: [C.taxIfClosed(1800, 1200, 33), C.taxIfClosed(-500, 200, 33), C.taxIfClosed(1000, -1500, 33)],
            em: [C.emergBudget(60, 50, 10000), C.emergBudget(60, 40, 10000), C.emergBudget(60, 50, null)] }; }""")
        for x in r["sz"][:3]:                                                                  # margine, quantità o valore: gli altri due dalla leva
            self.assertAlmostEqual(x["value"], 3000)
            self.assertAlmostEqual(x["margin"], 1000)
            self.assertAlmostEqual(x["qty"], 0.05)
        self.assertAlmostEqual(r["sz"][3]["value"], 1000)                                      # 1x: valore = margine
        self.assertIsNone(r["sz"][4])
        self.assertEqual(r["fr"], [0.06, 0.05, 0.06, 0.1])                                     # taker stimata
        self.assertAlmostEqual(r["fee"], 1.8)
        self.assertEqual([(x["strategia"], x["segnale"]) for x in r["pre"]], [("W3.2", "2026-11-15"), ("fuori segnale", None), ("scanner", "2026-11-22"),
                                                                              ("fuori segnale", None), ("fuori segnale", None), ("fuori segnale", None)])
        P = r["plan"]
        self.assertAlmostEqual(P["value"], 3000)
        self.assertAlmostEqual(P["margin"], 1000)
        self.assertAlmostEqual(P["liq"], (60000 + 1000 / 0.05) / 1.005, places=4)
        self.assertAlmostEqual(P["liqD"], ((60000 + 20000) / 1.005 / 60000 - 1) * 100, places=6)
        self.assertAlmostEqual(P["stopD"], 25)
        self.assertEqual(P["levMax"], 3.0)                                                     # 1 / (0,25 + 0,05) = 3,33 → 3
        self.assertFalse(P["levOver"])
        self.assertAlmostEqual(P["atStop"], -(15000 * 0.05) - 1.8 - 75000 * 0.05 * 0.0006, places=6)   # commissioni di entrata e uscita
        self.assertAlmostEqual(P["riskPct"], P["atStop"] / 10000 * 100, places=6)
        self.assertAlmostEqual(P["weight"], 10)
        self.assertAlmostEqual(P["expo"], 30)
        self.assertTrue(r["plan10"]["levOver"])                                                # leva oltre quella compatibile con lo stop
        self.assertTrue(r["plan10"]["liqFirst"])
        self.assertIsNone(r["planSpot"]["liq"])
        self.assertEqual(r["planSpot"]["levMax"], 4)                                           # senza stop: leva massima dello Scanner
        self.assertIsNone(r["planSpot"]["weight"])
        A = r["add"]                                                                           # Aumenta: nuovo prezzo medio e liquidazione
        self.assertAlmostEqual(A["avg"], 62500)
        self.assertAlmostEqual(A["qty"], 0.2)
        self.assertAlmostEqual(A["margin"], 4000)
        self.assertAlmostEqual(A["liq"], (62500 + 4000 / 0.2) / 1.005, places=4)
        self.assertAlmostEqual(A["liqNow"], (65000 + 2000 / 0.1) / 1.005, places=4)
        self.assertAlmostEqual(A["dAvg"], (62500 / 65000 - 1) * 100, places=6)
        D = r["red"]                                                                           # Riduci 50%: P/L realizzato stimato
        self.assertAlmostEqual(D["qty"], 0.05)
        self.assertAlmostEqual(D["gross"], 5000 * 0.05)
        self.assertAlmostEqual(D["fee"], 60000 * 0.05 * 0.0006)
        self.assertAlmostEqual(D["net"], 250 - 1.8)
        self.assertAlmostEqual(D["rest"], 0.05)
        self.assertAlmostEqual(D["marginRest"], 1000)
        self.assertFalse(D["full"])
        self.assertTrue(r["redAll"]["full"])
        self.assertEqual(r["redAll"]["rest"], 0)
        self.assertAlmostEqual(r["pct"][0], 0.075)
        self.assertEqual(r["pct"][1], 0.3)
        self.assertIsNone(r["pct"][2])
        self.assertEqual(r["rate"], [33, 26, 20, 33, 0])                                        # 33% dal 2026, 26% fino al 2025, aliquota del profilo
        y26, y25, y24 = r["ty"]                                                                # tasse per anno con compensazione
        self.assertEqual((y26["year"], y25["year"], y24["year"]), (2026, 2025, 2024))
        self.assertAlmostEqual(y26["net"], 1800)
        self.assertAlmostEqual(y26["tax"], 1800 * 0.33)                                        # le perdite dell'anno compensano i guadagni
        self.assertAlmostEqual(y26["after"], 1800 * 0.67)
        self.assertAlmostEqual(y26["monthly"], 1800 * 0.67 / 12)                               # netto al mese = netto annuo / 12
        self.assertAlmostEqual(y25["net"], -300)
        self.assertEqual(y25["tax"], 0)                                                        # saldo negativo: niente tasse, nessun riporto
        self.assertAlmostEqual(y25["monthly"], -25)
        self.assertAlmostEqual(y24["tax"], 260)                                                # 26% prima del 2026
        self.assertAlmostEqual(r["tyAl"][0]["tax"], 600)                                       # aliquota dal profilo
        self.assertAlmostEqual(r["tc"][0]["tax"], 990)                                         # se chiudessi oggi
        self.assertAlmostEqual(r["tc"][0]["extra"], 990 - 594)
        self.assertAlmostEqual(r["tc"][0]["monthly"], (3000 - 990) / 12)
        self.assertEqual(r["tc"][1]["tax"], 0)
        self.assertAlmostEqual(r["tc"][2]["extra"], -330)
        self.assertEqual([x["over"] for x in r["em"]], [True, False, False])                   # regola dell'1% sulle emergenti
        self.assertAlmostEqual(r["em"][0]["limit"], 100)
        self.assertEqual(self.errs, [])
        pg.close()

    def test_tasse_in_euro_cambi_bce(self):
        pg = self.pagina()
        pg.wait_for_function("window.WalletCalc && window.WalletFX")
        r = pg.evaluate("""async () => { const C = window.WalletCalc, FX = window.WalletFX;
          // cambi finti (euro per 1 $): venerdì 6/3, poi lunedì 9/3; weekend senza cambio
          const tab = { "2025-12-31": 0.80, "2026-03-02": 0.90, "2026-03-06": 0.92, "2026-03-09": 0.95, "2026-06-01": 0.85, "2026-11-27": 0.91 };
          const rateOf = d => { const x = C.fxAt(tab, d); return x ? x.rate : null; };
          const spot = C.eurEvents([   // spot long: due ingressi a date diverse, chiusura sabato 7/3 (cambio del venerdì)
            { tipo: "ingresso", data: "2026-03-02T10:00:00Z", prezzo: 1000, quantita: 1, commissioni: 0 },
            { tipo: "aggiunta", data: "2026-03-06T10:00:00Z", prezzo: 2000, quantita: 1, commissioni: 10 },
            { tipo: "riduzione", data: "2026-03-07T10:00:00Z", prezzo: 3000, quantita: 1, commissioni: 0 },
            { tipo: "chiusura", data: "2026-06-01T10:00:00Z", prezzo: 2500, quantita: 1, commissioni: 0 }], "long", "spot", rateOf);
          const perp = C.eurEvents([   // perp short: risultato in $ al cambio della chiusura, funding al cambio della sua data
            { tipo: "ingresso", data: "2026-03-02T10:00:00Z", prezzo: 60000, quantita: 0.1, commissioni: 0 },
            { tipo: "chiusura", data: "2026-03-09T10:00:00Z", prezzo: 50000, quantita: 0.1, commissioni: 0, funding: 20 }], "short", "perp", rateOf);
          const loss = C.eurEvents([{ tipo: "ingresso", data: "2026-03-02T10:00:00Z", prezzo: 100, quantita: 10 },
            { tipo: "chiusura", data: "2026-06-01T10:00:00Z", prezzo: 50, quantita: 10 }], "long", "spot", rateOf);
          const ty = C.taxYears(spot.ev.concat(perp.ev, loss.ev), null);
          const miss = C.eurEvents([{ tipo: "ingresso", data: "2020-01-02T10:00:00Z", prezzo: 1, quantita: 1 }], "long", "spot", rateOf);
          // caricamento: rete finta, cache in localStorage finta, ripiego sulla cache, nessun cambio
          const mkSt = () => { const m = {}; return { getItem: k => k in m ? m[k] : null, setItem: (k, v) => { m[k] = String(v); }, m }; };
          let calls = 0; const okF = async url => { calls++; return { ok: true, json: async () => ({ rates: { "2025-12-31": { EUR: 0.86 }, "2026-11-27": { EUR: 0.91 } }, url }) }; };
          const badF = async () => { calls++; throw new Error("rete"); };
          FX.mem = {}; const st1 = mkSt(); const live = await FX.load([2026], { fetch: okF, storage: st1 });
          const c1 = calls; const again = await FX.load([2026], { fetch: okF, storage: st1 }); const c2 = calls;
          FX.mem = {}; const old = mkSt(); old.setItem(FX.KEY + "2026", JSON.stringify({ rates: { "2026-11-20": 0.9 }, t: Date.now() - 864e5 }));
          const cache = await FX.load([2026], { fetch: badF, storage: old });
          FX.mem = {}; const none = await FX.load([2026], { fetch: badF, storage: mkSt() });
          FX.mem = {}; const part = await FX.load([2025, 2026], { fetch: url => String(url).includes("/2026-") ? okF(url) : badF(), storage: mkSt() });
          FX.mem = {};
          return { fxSat: C.fxAt(tab, "2026-03-07T10:00:00Z"), fxSun: C.fxAt(tab, "2026-03-08"), fxNone: C.fxAt(tab, "2025-01-01"), spot, perp, loss, ty, miss: miss.missing,
            live, stored: JSON.parse(st1.m[FX.KEY + "2026"]), c1, c2, again, cache, none, part }; }""")
        self.assertEqual(r["fxSat"], {"date": "2026-03-06", "rate": 0.92})                    # sabato: cambio del venerdì
        self.assertEqual(r["fxSun"]["date"], "2026-03-06")
        self.assertIsNone(r["fxNone"])
        ev = r["spot"]["ev"]
        avg_eur = (1000 * 0.90 + 2000 * 0.92) / 2                                             # costo medio in euro ponderato su due ingressi
        self.assertAlmostEqual(ev[1]["d"], -10 * 0.92)                                         # commissione al cambio della sua data
        self.assertAlmostEqual(ev[2]["d"], 3000 * 0.92 - avg_eur)                              # corrispettivo al cambio dell'uscita − costo medio in euro
        self.assertAlmostEqual(ev[3]["d"], 2500 * 0.85 - avg_eur)
        self.assertAlmostEqual(ev[2]["usd"], 3000 - 1500)
        self.assertFalse(r["spot"]["missing"])
        pe = r["perp"]["ev"]
        self.assertAlmostEqual(pe[1]["d"], (60000 - 50000) * 0.1 * 0.95 - 20 * 0.95)           # perp: risultato in $ al cambio della chiusura
        self.assertAlmostEqual(r["loss"]["ev"][1]["d"], 500 * 0.85 - 1000 * 0.90)
        y = r["ty"][0]
        gains = (3000 * 0.92 - avg_eur) + (2500 * 0.85 - avg_eur) + pe[1]["d"]
        losses = -10 * 0.92 + (500 * 0.85 - 1000 * 0.90)
        self.assertEqual(y["year"], 2026)
        self.assertAlmostEqual(y["gains"], gains)
        self.assertAlmostEqual(y["losses"], losses)                                            # compensazione in euro nell'anno
        self.assertAlmostEqual(y["tax"], (gains + losses) * 0.33)
        self.assertAlmostEqual(y["after"], (gains + losses) * 0.67)
        self.assertAlmostEqual(y["monthly"], (gains + losses) * 0.67 / 12)                     # netto / 12 in euro
        self.assertTrue(r["miss"])                                                             # movimento senza cambio: niente euro
        self.assertTrue(r["live"]["ok"])
        self.assertFalse(r["live"]["fallback"])
        self.assertEqual(r["live"]["last"], {"date": "2026-11-27", "rate": 0.91})
        self.assertIn("2026-11-27", r["stored"]["rates"])                                      # salvato in localStorage
        self.assertEqual((r["c1"], r["c2"]), (1, 1))                                           # seconda volta dalla cache: nessuna richiesta
        self.assertTrue(r["cache"]["ok"])                                                      # rete giù: ultimo cambio in cache, dichiarato
        self.assertTrue(r["cache"]["fallback"])
        self.assertEqual(r["cache"]["last"], {"date": "2026-11-20", "rate": 0.9})
        self.assertFalse(r["none"]["ok"])                                                      # nessun cambio
        self.assertIsNone(r["none"]["last"])
        self.assertFalse(r["part"]["ok"])                                                      # manca un anno: non si mostra in euro
        self.assertEqual(self.errs, [])
        pg.close()

    def test_riepilogo_tasse_in_euro_e_senza_cambio(self):
        rates = {"2025-12-31": {"EUR": 0.86}, "2026-08-25": {"EUR": 0.85}, "2026-11-03": {"EUR": 0.88}, "2026-11-27": {"EUR": 0.9}}
        for fx in (True, False):
            pg = self.b.new_page(viewport={"width": 400, "height": 860})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            def route(rq, _req=None, fx=fx):   # Playwright passa (route, request)
                u = rq.request.url
                if "127.0.0.1" in u:
                    return rq.continue_()
                if fx and u.startswith("https://api.frankfurter.dev/v1/2026-01-01..2026-12-31?from=USD&to=EUR"):
                    return rq.fulfill(status=200, content_type="application/json", headers={"access-control-allow-origin": "*"},
                                      body=json.dumps({"amount": 1, "base": "USD", "rates": rates}))
                return rq.abort()
            pg.route("**/*", route)
            pg.goto(f"http://127.0.0.1:{self.srv.server_port}/index.html?demo=1#wallet")
            pg.wait_for_selector("#waLogin", timeout=5000)
            pg.evaluate("() => { try { localStorage.clear(); } catch (_) {} window.WalletFX.mem = {}; }")
            pg.fill("#waLogin input[name=email]", "demo@radar.local")
            pg.click("#waLogin button[type=submit]")
            pg.wait_for_selector(".waTax", timeout=5000)
            if fx:
                pg.wait_for_selector("#waFx:has-text('Cambi BCE')", timeout=5000)
                t = pg.inner_text(".waTax")
                self.assertIn("in euro ai cambi BCE", t)
                self.assertRegex(t, r"profitto lordo 2026\s+−\u2060[\d.]+,\d\d\u00a0€")          # formato italiano in euro
                self.assertIn("netto al mese", t)
                self.assertIn("≈ −\u2060$", t)                                                  # controvalore in dollari
                self.assertIn("ultimo 27/11: 1\u00a0$\u00a0=\u00a00,9000\u00a0€", t)
                closed = (2255 * 2 * 0.88 - 2480 * 2 * 0.85) - (2.5 * 0.85 + 2.3 * 0.88)       # chiusa spot ETH: costo al cambio d'ingresso
                costs = (5.9 + 3.8 + 2.4 + 3.2 + 1.1 + 0.3) * 0.88                              # commissioni e funding delle aperte (novembre)
                self.assertIn("euro ai cambi di riferimento BCE", pg.inner_text("#waTaxN"))
                self.assertIn("saldo −\u2060" + dashboard_nf2(closed - costs) + "\u00a0€", pg.inner_text("#waTaxY"))
            else:
                pg.wait_for_selector("#waFxW", timeout=5000)
                self.assertIn("Cambio non disponibile", pg.inner_text("#waFxW"))
                self.assertRegex(pg.inner_text(".waTax"), r"profitto lordo 2026\s+−\u2060\$")
            self.assertIn("Stima, non consulenza fiscale", pg.inner_text("#waTaxN"))
            sw, cw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            self.assertLessEqual(sw, cw)
            self.assertEqual(errs, [])
            pg.close()

    def test_apri_posizione_a_passi(self):
        for w in (360, 1280):
            pg = self.pagina(w, "?demo=1")
            pg.wait_for_selector("#waLogin", timeout=5000)
            pg.evaluate("m => Object.assign(R, m)", MODELLO)
            pg.fill("#waLogin input[name=email]", "demo@radar.local")
            pg.click("#waLogin button[type=submit]")
            pg.wait_for_selector(".waPos", timeout=5000)
            self.assertEqual(pg.inner_text("#waNew"), "Apri posizione")
            pg.click("#waNew")
            pg.wait_for_selector("#sheet[open] .waSteps")
            self.assertEqual(pg.get_attribute("#sheet [data-st='1']", "aria-current"), "step")
            self.assertEqual(pg.get_attribute("#sheet [data-side=short]", "aria-pressed"), "true")   # W3.2 su BTC è short
            self.assertEqual(pg.get_attribute("#sheet [data-seg=strategia] [data-v='W3.2']", "aria-pressed"), "true")   # preselezionata
            self.assertEqual(pg.input_value("#sheet input[name=segnale_data]"), "2026-11-15")  # data del segnale compilata
            pg.click("#sheet [data-side=long]")                                                # lato opposto al segnale: fuori segnale
            self.assertEqual(pg.get_attribute("#sheet [data-seg=strategia] [data-v='fuori segnale']", "aria-pressed"), "true")
            self.assertEqual(pg.input_value("#sheet input[name=segnale_data]"), "")
            pg.click("#sheet [data-side=short]")
            pg.click("#sheet [data-coin=ETH]")
            self.assertEqual(pg.input_value("#sheet input[name=segnale_data]"), "2026-11-08")
            pg.click("#sheet [data-coin=BTC]")
            for b in pg.locator("#sheet .waChip, #sheet .waSide button, #sheet [data-step='1'] .seg button, #sheet .waBar .waCta").all():   # tocco ≥ 44 px
                self.assertGreaterEqual(b.bounding_box()["height"], 44)
            pg.click("#sheet [data-next]")
            pg.wait_for_selector("#sheet [data-step='2']:not([hidden])")
            self.assertEqual(pg.input_value("#sheet input[name=prezzo]"), "60000")            # prezzo attuale precompilato
            self.assertEqual(pg.inner_text("#sheet [data-back]"), "Indietro")
            pg.click("#sheet [data-next]")
            self.assertIn("importo", pg.inner_text("#sheet .err"))
            pg.fill("#sheet input[name=importo]", "1.000")
            pg.click("#sheet [data-lev='3']")
            self.assertIn("$3.000", pg.inner_text("#sheet [data-calc]"))                       # valore = margine × leva
            self.assertIn("$1,80", pg.inner_text("#sheet [data-feev]"))                        # 0,06% di 3.000
            pg.click("#sheet [data-next]")
            pg.wait_for_selector("#sheet [data-step='3']:not([hidden])")
            sumT = pg.inner_text("#sheet [data-sum]")
            for k in ("valore della posizione", "margine", "liquidazione stimata", "stop della strategia", "leva massima con lo stop", "rischio allo stop", "peso sul capitale", "commissione stimata"):
                self.assertIn(k, sumT)
            self.assertIn("trailing W3.2", sumT)
            self.assertIn("10,0%", sumT)                                                       # 1.000 su 10.000
            sw, cw = pg.evaluate("[document.getElementById('sheet').scrollWidth, document.getElementById('sheet').clientWidth]")
            self.assertLessEqual(sw, cw, f"{w}px")
            self.assertEqual(pg.inner_text("#sheet [data-next]"), "Apri posizione")
            pg.click("#sheet [data-next]")
            pg.wait_for_function("!document.getElementById('sheet').open")
            pg.wait_for_function("document.querySelectorAll('.waPos').length === 4")
            self.assertEqual(self.errs, [])
            pg.close()

    def test_demo_senza_scorrimento_orizzontale(self):
        for w in (360, 1280):
            pg = self.pagina(w, "?demo=1")
            pg.wait_for_selector("#waLogin", timeout=5000)
            pg.evaluate("m => Object.assign(R, m)", MODELLO)   # stato di W3.2 su BTC ed ETH per il confronto
            pg.fill("#waLogin input[name=email]", "demo@radar.local")
            pg.fill("#waLogin input[name=pw]", "x")
            pg.click("#waLogin button[type=submit]")
            pg.wait_for_selector(".waPos", timeout=5000)
            self.assertEqual(pg.locator(".waPos").count(), 3)
            self.assertEqual(pg.locator("#waClosed button.row").count(), 1)
            self.assertIn("fuori segnale", pg.inner_text("#waOpen"))
            self.assertIsNone(pg.get_attribute("#waCmpSec", "open"))                          # confronto chiuso di default
            self.assertRegex(pg.inner_text("#waCmpSum"), r"^Deriva totale [−+]?\u2060?\$[\d.,]+ · 4 posizioni$")
            self.assertTrue(pg.is_hidden("#waCmp"))
            pg.click("#waCmpSec > summary")
            self.assertTrue(pg.is_visible("#waCmp"))
            self.assertIn("Deriva", pg.inner_text("#waCmp"))
            for b in pg.locator(".waPos .waCta").all():                                    # icona, aria-label, tocco ≥ 44 px
                self.assertTrue(b.get_attribute("aria-label"))
                self.assertEqual(b.locator("svg use").count(), 1)
                self.assertGreaterEqual(b.bounding_box()["height"], 44)
            sw, cw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            self.assertLessEqual(sw, cw, f"{w}px")
            pg.locator(".waPos [data-a=add]").first.click()                                    # modulo Aumenta
            pg.wait_for_selector("#sheet[open] .waForm input[name=importo]")
            self.assertTrue(pg.input_value("#sheet input[name=prezzo]"))                       # prezzo attuale precompilato
            self.assertIn("Usa prezzo attuale", pg.inner_text("#sheet [data-src]"))
            self.assertEqual(pg.input_value("#sheet input[name=fee]"), "0,06")                 # taker Bitget perp, stima
            pg.fill("#sheet .waForm input[name=prezzo]", "0")
            pg.click("#sheet .waForm button[type=submit]")
            self.assertIn("Prezzo", pg.inner_text("#sheet .waForm .err"))                     # validazione
            pg.fill("#sheet .waForm input[name=prezzo]", "61.000")
            pg.click("#sheet [data-seg=by] [data-v=quantita]")
            pg.fill("#sheet .waForm input[name=importo]", "0,05")
            prev = pg.inner_text("#sheet [data-prev]")
            self.assertIn("nuovo prezzo medio", prev)                                          # anteprima prima di salvare
            self.assertIn("nuova liquidazione", prev)
            self.assertIn("$3.050", pg.inner_text("#sheet [data-calc]"))                       # valore = 0,05 × 61.000
            sw2, cw2 = pg.evaluate("[document.getElementById('sheet').scrollWidth, document.getElementById('sheet').clientWidth]")
            self.assertLessEqual(sw2, cw2, f"{w}px Aumenta")
            pg.click("#sheet .waForm button[type=submit]")
            pg.wait_for_function("!document.getElementById('sheet').open")
            pg.wait_for_function("document.querySelector('.waPos').innerText.includes('3 ingressi')")
            pg.locator(".waPos [data-a=red]").first.click()                                    # modulo Riduci o chiudi
            pg.wait_for_selector("#sheet[open] [data-pct]")
            pg.click("#sheet [data-pct='50']")
            prev = pg.inner_text("#sheet [data-prev]")
            self.assertIn("Riduzione del 50%", prev)
            self.assertIn("P/L realizzato stimato", prev)
            self.assertEqual(pg.inner_text("#sheet button[type=submit]"), "Riduci posizione")
            pg.click("#sheet [data-pct='100']")
            self.assertEqual(pg.inner_text("#sheet button[type=submit]"), "Chiudi posizione")
            self.assertIn("Chiusura totale", pg.inner_text("#sheet [data-prev]"))
            pg.click("#sheetX")
            self.assertIn("Tasse stimate", pg.inner_text("#waHero"))                           # tasse nel conto
            self.assertIn("netto al mese", pg.inner_text("#waHero"))
            self.assertIn("Se chiudessi oggi", pg.inner_text("#waHero"))
            self.assertIn("aliquota 33%", pg.inner_text("#waTaxY"))
            self.assertIn("compensano", pg.inner_text("#waTaxN"))
            self.assertEqual(self.errs, [])
            pg.close()


if __name__ == "__main__":
    unittest.main()
