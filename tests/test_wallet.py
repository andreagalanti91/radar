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
        self.assertIn('const PAGE_OF = Object.assign({ wallet: "wallet" }', T)
        self.assertIn("window.PAGES.wallet = {", PAGE)

    def test_vecchio_wallet_hyperliquid_non_raggiungibile(self):
        old = (ROOT / "radar" / "pages" / "hyperliquid.html").read_text()
        self.assertIn('id="v-hyperliquid"', old)
        self.assertIn("window.PAGES.hyperliquid = {", old)
        self.assertNotIn('id="v-wallet"', old)
        self.assertNotIn("hyperliquid", re.search(r"const VIEWS = \[([^\]]*)\]", T).group(1))
        self.assertNotIn('href="#hyperliquid"', T)

    def test_supabase_da_cdn_versione_esatta(self):
        m = re.search(r'const SB_SRC = "https://cdn\.jsdelivr\.net/npm/@supabase/supabase-js@(\d+)\.(\d+)\.(\d+)/dist/umd/supabase\.js"', PAGE)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "2")
        self.assertGreaterEqual(int(m.group(2)), 40)            # chiavi sb_publishable_ supportate
        self.assertRegex(PAGE, r'const SB_SRI = "sha384-[A-Za-z0-9+/=]{64}"')
        self.assertIn("const CFG = /*__SUPABASE__*/null;", PAGE)
        self.assertNotIn("signUp", PAGE)                        # nessuna registrazione dalla pagina
        self.assertNotIn("Telegram", PAGE)

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
            self.assertIn("Deriva", pg.inner_text("#waCmp"))
            sw, cw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            self.assertLessEqual(sw, cw, f"{w}px")
            pg.locator(".waPos [data-a=add]").first.click()                                    # modulo nuova tranche
            pg.wait_for_selector("#sheet[open] .waForm input[name=prezzo]")
            pg.fill("#sheet .waForm input[name=prezzo]", "0")
            pg.click("#sheet .waForm button[type=submit]")
            self.assertIn("Prezzo", pg.inner_text("#sheet .waForm .err"))                     # validazione
            pg.fill("#sheet .waForm input[name=prezzo]", "61.000")
            pg.fill("#sheet .waForm input[name=quantita]", "0,05")
            pg.click("#sheet .waForm button[type=submit]")
            pg.wait_for_function("!document.getElementById('sheet').open")
            pg.wait_for_function("document.querySelector('.waPos').innerText.includes('3 tranche')")
            self.assertEqual(self.errs, [])
            pg.close()


if __name__ == "__main__":
    unittest.main()
