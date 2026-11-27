"""Pagina Opzioni riattivata (27/11/2026) e sezione "Scadenze maggiori": calendario OPEX esteso (radar/opex.py: OI call/put, muri,
iv_atm, movimento atteso, skew dai mark_iv di Deribit; null col ripiego OKX), sezione nella pagina, riga Opzioni in Oggi.
Rete sempre finta."""
from __future__ import annotations

import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from radar import opex as O
try:
    from test_opex import okx_get           # discover -s tests
except ImportError:
    from tests.test_opex import okx_get

ROOT = Path(__file__).resolve().parent.parent
T = (ROOT / "radar" / "dashboard_template.html").read_text()
UTC = timezone.utc
NOW = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)   # dopo la scadenza delle 08:00 del 27/11
DEC = datetime(2026, 12, 25, 8, tzinfo=UTC)
FUT = 60000.0


def book():
    """Libro finto Deribit: 25DEC26 trimestrale con future 60.000 e mark_iv; settimanali con poco OI; 29JAN27 mensile grande
    (oltre i 6 venerdì più vicini) e 26FEB27 piccolo."""
    r = []

    def add(name, oi, iv, und):
        r.append({"instrument_name": name, "open_interest": oi, "mark_iv": iv, "underlying_price": und,
                  "estimated_delivery_price": 59800.0})
    # 25 dicembre: ATM 60.000 (call 48, put 50 → 49), put 54.000 (−10%) IV 58, call 66.000 (+10%) IV 46 → skew 12
    for k, (oc, op, ivc, ivp) in {54000: (100, 9000, 52, 58), 60000: (5000, 4000, 48, 50), 66000: (8000, 200, 46, 49),
                                  80000: (12000, 0, 55, 60)}.items():
        add(f"BTC-25DEC26-{k}-C", oc, ivc, FUT)
        add(f"BTC-25DEC26-{k}-P", op, ivp, FUT)
    for d in ("4DEC26", "11DEC26", "18DEC26", "1JAN27", "8JAN27", "15JAN27"):
        add(f"BTC-{d}-60000-C", 10, 45, FUT)
        add(f"BTC-{d}-60000-P", 10, 47, FUT)
    add("BTC-29JAN27-60000-C", 20000, 50, 60500.0)
    add("BTC-29JAN27-60000-P", 15000, 52, 60500.0)
    add("BTC-26FEB27-60000-C", 5, 50, 61000.0)
    add("BTC-30APR27-60000-C", 50000, 50, 62000.0)   # oltre 120 giorni: non entra (non è la prossima trimestrale)
    return {"result": r}


def get_book(u, p=None):
    return book()


class Calendario(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_fetch_conserva_iv_e_future(self):
        rows, px = O.fetch_deribit(get_book)
        self.assertEqual(px, 59800.0)
        x = next(c for c in rows if c["strike"] == 54000 and c["type"] == "P")
        self.assertEqual((x["iv"], x["und"], x["oi"]), (58.0, FUT, 9000.0))
        # compatibilità: risposta senza mark_iv/underlying_price → None, niente errori
        rows2, _ = O.fetch_deribit(lambda u, p=None: {"result": [{"instrument_name": "BTC-25DEC26-60000-C", "open_interest": 1,
                                                                  "estimated_delivery_price": 60000}]})
        self.assertEqual((rows2[0]["iv"], rows2[0]["und"]), (None, None))

    def test_volatilita_movimento_skew(self):
        rows, _ = O.fetch_deribit(get_book)
        v = O.vol_of(rows, DEC)
        self.assertEqual(v["iv_atm"], 49.0)                 # media call 48 e put 50 allo strike 60.000 (= future)
        self.assertEqual(v["skew"], 12.0)                   # put 54.000 (58) − call 66.000 (46)
        self.assertEqual(O.mov_pct(49.0, 28), round(49 * math.sqrt(28 / 365), 1))
        self.assertIsNone(O.mov_pct(None, 28))
        self.assertIsNone(O.mov_pct(49.0, 0))

    def test_calendario_esteso(self):
        r = O.build(self.dir, get=get_book, now=NOW)
        cal = {c["exp"][:10]: c for c in r["calendar"]}
        self.assertEqual(list(cal), sorted(cal))                                    # per data
        self.assertIn("2027-01-29", cal)                                            # mensile oltre i 6 venerdì, entro 120 g
        self.assertIn("2027-02-26", cal)                                            # mensile piccola: nel calendario, la pagina la filtra
        self.assertNotIn("2027-04-30", cal)                                         # oltre 120 giorni
        d = cal["2026-12-25"]
        self.assertEqual(d["kind"], "trimestrale")
        self.assertEqual((d["oi_call"], d["oi_put"]), (25100.0, 13200.0))
        self.assertEqual((d["call_wall"], d["put_wall"]), (80000.0, 54000.0))
        self.assertEqual((d["iv_atm"], d["skew"]), (49.0, 12.0))
        days = (DEC - NOW).total_seconds() / 86400
        self.assertEqual(d["mov_atteso_pct"], round(49 * math.sqrt(days / 365), 1))
        self.assertGreater(d["notional"], 1e9)
        for k in ("exp", "kind", "notional", "put_call", "max_pain"):                # campi di prima invariati
            self.assertIn(k, d)
        # giro dopo, dal file: il movimento atteso si ricalcola con i giorni che restano
        later = NOW + timedelta(hours=5)
        r2 = O.build(self.dir, get=lambda u, p=None: (_ for _ in ()).throw(ConnectionError()), now=later)
        d2 = next(c for c in r2["calendar"] if c["exp"].startswith("2026-12-25"))
        self.assertEqual(d2["mov_atteso_pct"], round(49 * math.sqrt((DEC - later).total_seconds() / 86400 / 365), 1))

    def test_ripiego_okx_volatilita_null(self):
        r = O.build(self.dir, get=okx_get(), now=datetime(2026, 11, 26, 17, tzinfo=UTC))
        self.assertEqual(r["src"], "okx")
        for c in r["calendar"]:
            self.assertIsNone(c["iv_atm"])
            self.assertIsNone(c["mov_atteso_pct"])
            self.assertIsNone(c["skew"])
            self.assertIn("oi_call", c)

    def test_file_vecchio_si_riscarica(self):
        last = {"ts": NOW.isoformat(), "exp": "2026-12-25T08:00:00+00:00", "calendar": [{"exp": "2026-12-25T08:00:00+00:00"}]}
        self.assertTrue(O.due(last, NOW + timedelta(hours=1)))
        last["calendar"][0]["iv_atm"] = 49.0
        self.assertFalse(O.due(last, NOW + timedelta(hours=1)))


class Pagina(unittest.TestCase):
    def test_opzioni_attiva(self):
        self.assertIn("const OPZIONI_ON = true;", T)
        self.assertIn("riattivata il 27/11/2026", T)
        v = T[T.index('<div class="view" id="v-opzioni"'):T.index('<div class="view" id="v-scanner"')]
        self.assertLess(v.index('id="sxSec"'), v.index('id="opSec"'))              # Scadenze maggiori in testa
        q = T[T.index('id="qPos"'):T.index("</section>", T.index('id="qPos"'))]
        self.assertLess(q.index('id="posLine"'), q.index('id="opLine" href="#opzioni"'))   # riga dentro "Come vanno le posizioni?"
        js = T[T.index("(function renderScadenze()"):T.index("// ---- Scanner (pagina a sé)")]
        for x in ("BIG = 1e9", "DAYS = 120", "mov_atteso_pct", "c.skew", "la più vicina", "non una calamita", "W3.2 non cambia",
                  "openOpexPanel"):
            self.assertIn(x, js)
        self.assertIn('$("oxOpen").onclick = window.openOpexPanel = ', T)

    def test_sezione_nel_browser(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright non installato")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        now = datetime.now(UTC).replace(microsecond=0)
        b0 = book()
        # sposta le scadenze in avanti rispetto a oggi: il filtro della pagina usa l'ora del browser
        r = O.build(Path(tmp.name), get=lambda u, p=None: b0, now=min(now, NOW))
        shift = max(timedelta(0), now - NOW) + timedelta(days=1)
        for c in r["calendar"]:
            c["exp"] = (datetime.fromisoformat(c["exp"]) + shift).isoformat()
        cut = lambda a, b: T[T.index(a):T.index(b)]  # noqa: E731
        style = cut("<style>", "</style>") + "</style>"
        sec = cut('<div class="section" id="sxSec" hidden>', '<div class="section" id="opSec">')
        js = "\n".join([
            "const $ = id => document.getElementById(id);",
            cut("const nfIT = window.nfIT", "const nfS = "), cut("const pct = ", "const css = "),
            next(l for l in T.splitlines() if l.startswith("const escS = ")),
            "const OPZIONI_ON = true; window.openOpexPanel = () => { window.__opened = 1; };",
            "const R = " + json.dumps({"opex": r}) + ";",
            cut("(function renderScadenze()", "// ---- Scanner (pagina a sé)")])
        page = Path(tmp.name) / "sx.html"
        page.write_text(f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                        f'{style}</head><body><main style="padding:16px">{sec}</main><script>{js}</script></body></html>')
        try:
            p = sync_playwright().start()
            b = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            self.skipTest(f"chromium non disponibile: {e}")
        self.addCleanup(p.stop)
        self.addCleanup(b.close)
        for wd in (360, 400, 1280):
            pg = b.new_page(viewport={"width": wd, "height": 800})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(page.as_uri())
            pg.wait_for_selector("#sxSec", state="visible", timeout=5000)
            n = pg.evaluate("document.querySelectorAll('#sxList .sxC').length")
            self.assertEqual(n, 2)                                                   # 25/12 e 29/01 (≥ 1 mld $)
            self.assertEqual(pg.evaluate("document.querySelectorAll('#sxList .sxC.on').length"), 1)
            txt = pg.inner_text("#sxList")
            self.assertIn("trimestrale", txt)
            self.assertIn("Il mercato prezza ±", txt)
            self.assertIn("protezione dal ribasso", txt)
            self.assertFalse(pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
            pg.click("#sxMore")
            self.assertEqual(pg.evaluate("window.__opened"), 1)
            self.assertEqual(errs, [])
            pg.close()


if __name__ == "__main__":
    unittest.main()
