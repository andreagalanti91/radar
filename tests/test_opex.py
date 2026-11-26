"""Controllo "OPEX" (radar/opex.py, scheda in Posizioni): calendario delle scadenze, massimo dolore, put/call e muri su catena
sintetica, scelta della scadenza, ripiego Deribit → OKX → ultimo file, ritmo degli scaricamenti, snapshot, scheda nella pagina.
Rete sempre finta."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from radar import opex as O
from radar.dashboard import render

ROOT = Path(__file__).resolve().parent.parent
T = (ROOT / "radar" / "dashboard_template.html").read_text()
UTC = timezone.utc
NOW = datetime(2026, 11, 26, 17, 0, tzinfo=UTC)


def c(exp, k, t, oi):
    return {"exp": exp, "strike": float(k), "type": t, "oi": float(oi)}


def deribit_json(rows, px=60000.0):
    """rows: [(nome Deribit, oi)]"""
    return {"result": [{"instrument_name": n, "open_interest": oi, "estimated_delivery_price": px, "underlying_price": px}
                       for n, oi in rows]}


ROWS = [("BTC-27NOV26-55000-P", 300), ("BTC-27NOV26-58000-P", 500), ("BTC-27NOV26-60000-C", 100), ("BTC-27NOV26-60000-P", 100),
        ("BTC-27NOV26-62000-C", 200), ("BTC-27NOV26-65000-C", 400), ("BTC-4DEC26-60000-C", 50), ("BTC-4DEC26-58000-P", 80),
        ("BTC-28NOV26-60000-C", 10), ("BTC-25DEC26-70000-C", 900), ("BTC-25DEC26-50000-P", 700)]


def okx_get(px=60000.0):
    def ms(d):
        return str(int(d.timestamp() * 1000))
    e1, e2 = datetime(2026, 11, 27, 8, tzinfo=UTC), datetime(2026, 12, 4, 8, tzinfo=UTC)
    inst = [{"instId": "A", "stk": "58000", "optType": "P", "expTime": ms(e1)}, {"instId": "B", "stk": "62000", "optType": "C", "expTime": ms(e1)},
            {"instId": "C", "stk": "60000", "optType": "C", "expTime": ms(e2)}]
    oi = [{"instId": "A", "oiCcy": "40"}, {"instId": "B", "oiCcy": "20"}, {"instId": "C", "oiCcy": "5"}]

    def get(url, params=None):
        if "deribit" in url:
            raise ConnectionError("giù")
        if "instruments" in url:
            return {"code": "0", "data": inst}
        if "open-interest" in url:
            return {"code": "0", "data": oi}
        if "index-tickers" in url:
            return {"code": "0", "data": [{"idxPx": str(px)}]}
        raise AssertionError(url)
    return get


def down(url, params=None):
    raise ConnectionError("rete giù")


class TestCalendario(unittest.TestCase):
    def test_ultimo_venerdi_e_trimestrali(self):
        self.assertEqual(O.last_friday(2026, 11), datetime(2026, 11, 27, 8, tzinfo=UTC))
        self.assertEqual(O.last_friday(2026, 12), datetime(2026, 12, 25, 8, tzinfo=UTC))
        self.assertEqual(O.last_friday(2027, 1), datetime(2027, 1, 29, 8, tzinfo=UTC))
        self.assertEqual(O.last_friday(2026, 7), datetime(2026, 7, 31, 8, tzinfo=UTC))   # il 31 è venerdì
        self.assertTrue(O.is_quarterly(datetime(2026, 12, 25, 8, tzinfo=UTC)))
        self.assertFalse(O.is_quarterly(datetime(2026, 11, 27, 8, tzinfo=UTC)))
        self.assertFalse(O.is_quarterly(datetime(2026, 12, 18, 8, tzinfo=UTC)))          # venerdì di dicembre, non l'ultimo
        self.assertEqual(O.kind_of(datetime(2026, 12, 4, 8, tzinfo=UTC)), "settimanale")
        self.assertEqual(O.kind_of(datetime(2026, 11, 28, 8, tzinfo=UTC)), "giornaliera")

    def test_prossima_mensile(self):
        self.assertEqual(O.next_monthly(NOW), datetime(2026, 11, 27, 8, tzinfo=UTC))
        self.assertEqual(O.next_monthly(datetime(2026, 11, 27, 8, tzinfo=UTC)), datetime(2026, 12, 25, 8, tzinfo=UTC))   # alle 08:00 è passata
        self.assertEqual(O.next_monthly(datetime(2026, 12, 26, tzinfo=UTC)), datetime(2027, 1, 29, 8, tzinfo=UTC))

    def test_nome_deribit(self):
        self.assertEqual(O.parse_deribit_name("BTC-4DEC26-58000-P"), (datetime(2026, 12, 4, 8, tzinfo=UTC), 58000.0, "P"))
        self.assertEqual(O.parse_deribit_name("BTC-27NOV26-60000-C")[0], datetime(2026, 11, 27, 8, tzinfo=UTC))
        self.assertIsNone(O.parse_deribit_name("BTC-PERPETUAL"))

    def test_scelta_principale_e_settimanale(self):
        contracts, _ = O.fetch_deribit(lambda u, p=None: deribit_json(ROWS))
        main, wk = O.pick(contracts, NOW)
        self.assertEqual(main, datetime(2026, 11, 27, 8, tzinfo=UTC))
        self.assertEqual(wk, datetime(2026, 12, 4, 8, tzinfo=UTC))                       # il sabato 28 (giornaliera) non conta
        main, wk = O.pick(contracts, datetime(2026, 11, 27, 9, tzinfo=UTC))             # dopo la scadenza: la trimestrale di dicembre
        self.assertEqual(main, datetime(2026, 12, 25, 8, tzinfo=UTC))
        self.assertEqual(wk, datetime(2026, 12, 4, 8, tzinfo=UTC))


class TestCalcolo(unittest.TestCase):
    E = datetime(2026, 11, 27, 8, tzinfo=UTC)

    def chain(self):
        e = self.E
        return O.chain_of([c(e, 55000, "P", 300), c(e, 58000, "P", 500), c(e, 60000, "C", 100), c(e, 60000, "P", 100),
                           c(e, 62000, "C", 200), c(e, 65000, "C", 400), c(e + timedelta(days=7), 60000, "C", 999)], e)

    def test_massimo_dolore_a_mano(self):
        ch = self.chain()
        self.assertEqual(list(ch), [55000.0, 58000.0, 60000.0, 62000.0, 65000.0])        # solo la scadenza scelta
        def pain(s):
            return sum(cc * max(s - k, 0) + p * max(k - s, 0) for k, (cc, p) in ch.items())
        exp = min(ch, key=pain)
        mp, v = O.max_pain(ch)
        self.assertEqual(mp, exp)
        self.assertEqual(mp, 60000.0)
        self.assertEqual(v, pain(60000.0))   # 300·5000 + 500·2000 = 2,5 milioni

    def test_massimo_dolore_sposta_con_le_put(self):
        e = self.E
        ch = O.chain_of([c(e, 50000, "P", 10), c(e, 60000, "P", 1000), c(e, 70000, "C", 10)], e)
        self.assertEqual(O.max_pain(ch)[0], 60000.0)
        self.assertEqual(O.max_pain({}), (None, None))

    def test_put_call_muri_riepilogo(self):
        ch = self.chain()
        self.assertEqual(O.put_call(ch), round(900 / 700, 2))
        self.assertEqual(O.walls(ch, 61000), (65000.0, 58000.0))
        s = O.summarize(ch, 61000)
        self.assertEqual(s["notional"], round(1600 * 61000))
        self.assertAlmostEqual(s["dist_pct"], round((60000 / 61000 - 1) * 100, 2))
        self.assertIsNone(O.put_call({1.0: [0.0, 5.0]}))

    def test_frase(self):
        r = {"max_pain": 62000.0, "dist_pct": 3.3, "exp": self.E.isoformat()}
        f = O.frase("long", r, NOW)
        self.assertEqual(f, "Massimo dolore 62.000 $: sopra il prezzo, possibile spinta verso l'alto fino a venerdì (a favore del long) — solo contesto")
        self.assertIn("(contro lo short)", O.frase("short", r, NOW))
        self.assertIn("vicino al prezzo", O.frase(None, dict(r, dist_pct=0.4), NOW))
        self.assertIn("verso il basso", O.frase(None, dict(r, dist_pct=-4), NOW))
        self.assertIn("più di una settimana", O.frase(None, r, NOW - timedelta(days=10)))
        self.assertEqual(O.status_line(r, NOW), "Scadenza venerdì 27/11 · tra 15 h")
        self.assertEqual(O.status_line(r, NOW - timedelta(days=2)), "Scadenza venerdì 27/11 · tra 2 g")


class TestFontiERitmo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_deribit_e_snapshot(self):
        r = O.build(self.dir, side="short", get=lambda u, p=None: deribit_json(ROWS), now=NOW)
        self.assertEqual((r["src"], r["exp"], r["kind"], r["quarterly"]), ("deribit", "2026-11-27T08:00:00+00:00", "mensile", False))
        self.assertEqual(r["max_pain"], 60000.0)
        self.assertEqual((r["call_wall"], r["put_wall"]), (65000.0, 58000.0))
        self.assertEqual(r["weekly"]["exp"], "2026-12-04T08:00:00+00:00")
        self.assertTrue(any(x["kind"] == "trimestrale" for x in r["calendar"]))
        self.assertEqual(r["hours"], 15.0)
        self.assertIsNone(r["source_note"])
        self.assertEqual(r["note"], O.NOTE)
        lines = (self.dir / "opex" / "snap.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["max_pain"], 60000.0)
        self.assertLess(len(json.dumps(r)), 8000)
        # un'ora dopo: niente rete, si aggiornano solo le ore
        r2 = O.build(self.dir, side="short", get=down, now=NOW + timedelta(hours=1))
        self.assertEqual(r2["hours"], 14.0)
        self.assertIsNone(r2["source_note"])
        self.assertEqual(len((self.dir / "opex" / "snap.jsonl").read_text().splitlines()), 1)

    def test_ritmo(self):
        last = {"ts": NOW.isoformat(), "exp": "2026-11-29T08:00:00+00:00"}
        self.assertFalse(O.due(last, NOW + timedelta(hours=5)))                       # lontano dalla scadenza: una volta al giorno
        self.assertTrue(O.due(last, NOW + timedelta(hours=8)))                        # giorno UTC nuovo
        self.assertTrue(O.due(None, NOW))
        last = {"ts": NOW.isoformat(), "exp": "2026-11-27T08:00:00+00:00"}           # ultime 48 ore: ogni 4 ore
        self.assertFalse(O.due(last, NOW + timedelta(hours=2)))
        self.assertTrue(O.due(last, NOW + timedelta(hours=4)))
        self.assertTrue(O.due({"ts": NOW.isoformat(), "exp": NOW.isoformat()}, NOW + timedelta(minutes=1)))   # scadenza passata

    def test_ripiego_okx(self):
        r = O.build(self.dir, side=None, get=okx_get(), now=NOW)
        self.assertEqual(r["src"], "okx")
        self.assertIn("OKX", r["source_note"])
        self.assertEqual(r["put_call"], 2.0)
        self.assertEqual(r["notional"], 60 * 60000)

    def test_ultimo_file_e_senza_nulla(self):
        with self.assertRaises(RuntimeError):
            O.build(self.dir, get=down, now=NOW)
        from radar.cli import _soft
        self.assertIsNone(_soft("scadenze delle opzioni (OPEX)", lambda: O.build(self.dir, get=down, now=NOW)))
        O.build(self.dir, get=lambda u, p=None: deribit_json(ROWS), now=NOW)
        r = O.build(self.dir, get=down, now=NOW + timedelta(days=1))                  # giorno nuovo, rete giù: ultimo file
        self.assertIn("ultimo dato del 26/11 17:00 UTC", r["source_note"])
        self.assertEqual(r["max_pain"], 60000.0)
        r = O.build(self.dir, get=down, now=NOW + timedelta(days=2))
        self.assertIn("già passata", r["source_note"])


class TestScheda(unittest.TestCase):
    def test_nel_giro_e_nel_template(self):
        cli = (ROOT / "radar" / "cli.py").read_text()
        self.assertIn('_soft("scadenze delle opzioni (OPEX)", lambda: mod("opex").build(DATA_DIR', cli)
        self.assertIn('"opex", "onchain", "dollaro"):', cli)
        self.assertIn('<div class="oc" id="dxBox" hidden></div><div class="oc" id="oxBox" hidden></div>', T)
        self.assertLess(T.index('id="dxSec"'), T.index('id="oxSec"'))
        self.assertLess(T.index('id="oxSec"'), T.index('id="v-opzioni"'))
        js = T[T.index("function renderOpex"):T.index("function renderPosLine")]
        for x in ('class="ocTap" id="oxOpen" aria-haspopup="dialog"', "OPEX · solo contesto", "Dettagli ›", 'class="oxTh"',
                  'class="mp"', 'class="dot"', "oxChartP", "O.frase", "O.note"):
            self.assertIn(x, js)
        for t in ("Dove siamo", "Open interest per strike", "Prossime scadenze", "Scadenze passate (studio)",
                  "Cosa significa per la posizione", "Fonte"):
            self.assertIn(f'sec("{t}"', js)

    def test_dati_nella_pagina(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        r = O.build(Path(tmp.name), side="short", get=lambda u, p=None: deribit_json(ROWS), now=NOW)
        out = render({"date": "2026-11-26", "opex": r}, out=Path(tmp.name) / "index.html", standalone=False)
        html = out.read_text()
        R = json.JSONDecoder().raw_decode(html, html.index("const R = ") + len("const R = "))[0]
        self.assertEqual(R["opex"]["max_pain"], 60000.0)
        self.assertIn(O.NOTE, html)

    def test_apre_nel_browser_senza_overflow(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright non installato")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        r = O.build(Path(tmp.name), side="short", get=lambda u, p=None: deribit_json(ROWS), now=NOW)
        cut = lambda a, b: T[T.index(a):T.index(b)]  # noqa: E731
        style = cut("<style>", "</style>") + "</style>"
        sheet = next(l for l in T.splitlines() if '<dialog class="dlg" id="sheet"' in l)
        js = "\n".join([
            "const $ = id => document.getElementById(id);",
            cut("// Pannello generico: openSheet", "// telefono: sposta blocchi"),
            cut("const nfIT = window.nfIT", "const nfS = "), cut("const pct = ", "const css = "),
            next(l for l in T.splitlines() if l.startswith("const escS = ")),
            "const R = " + json.dumps({"opex": r, "weekly": {"status": "flat"}}) + ";",
            cut("(function renderOpex()", "// ---- Oggi: riga di stato delle posizioni")])
        page = Path(tmp.name) / "ox.html"
        page.write_text(f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                        f'{style}</head><body><div class="section" id="oxSec" hidden><div class="card ocCard" id="oxCard"></div></div>'
                        f'{sheet}<script>{js}</script></body></html>')
        try:
            p = sync_playwright().start()
            b = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            self.skipTest(f"chromium non disponibile: {e}")
        self.addCleanup(p.stop)
        self.addCleanup(b.close)
        for wd in (360, 400):
            pg = b.new_page(viewport={"width": wd, "height": 800})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(page.as_uri())
            pg.wait_for_selector("#oxOpen", state="visible", timeout=5000)
            self.assertGreaterEqual(pg.query_selector("#oxOpen").bounding_box()["height"], 44)
            q = lambda s: pg.evaluate(f"document.querySelectorAll('#oxOpen {s}').length")  # noqa: E731
            self.assertEqual((q(".oxTh .dot"), q(".oxTh .mp"), q(".oxTh .wl")), (1, 1, 2))
            pg.click("#oxOpen")
            self.assertTrue(pg.evaluate("document.getElementById('sheet').open"))
            pg.wait_for_timeout(100)
            self.assertGreater(pg.evaluate("document.querySelectorAll('#sheet #oxChartP rect').length"), 4)
            self.assertFalse(pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
            self.assertEqual(errs, [])
            pg.close()


if __name__ == "__main__":
    unittest.main()
