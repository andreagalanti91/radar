"""Pagina leggera (26/11/2026, C1) e legenda del Grafico su telefono (C2).

index.html porta solo i dati di Oggi e Posizioni; i dati pesanti delle pagine secondarie (Grafico, Scanner, Movimenti, Notizie)
sono file JSON accanto a index.html scaricati alla prima apertura (window.lazyData / lazyView), ciò che la pagina non usa va in
resto.json. Unendo i file alla pagina si ritrova il report completo: nessun dato perso."""
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from radar.dashboard import LAZY_FILES, render, split

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
PAGES = "".join(f.read_text() for f in sorted((ROOT / "radar" / "pages").glob("*.html")))
SOGLIA_INDEX = 800_000   # byte; misura col report pubblicato del 26/11/2026: 1.463.028 prima, 652.781 dopo (template e pagine ~510 KB); 27/11: +~30 KB di codice (accesso al tool e pagina Profilo), nessun dato in più


def report() -> dict:
    """Report sintetico con le stesse chiavi pesanti del report vero (dimensioni simili)."""
    n = 2600
    dates = [f"2019-{1 + i // 300:02d}-{1 + i % 28:02d}" for i in range(n)]
    hist = {"start": "2021-01-01", "trades": [{"entry": "2021-03-08", "exit": "2021-05-17", "side": "long", "pnl_pct": 74.5, "reason": "dist"}],
            "m1": {"n": 1, "years": {"2021": 74.5}}, "eq_dates": dates[:2155], "eq1": [1 + i / 1000 for i in range(2155)], "eq2": [1 + i / 500 for i in range(2155)],
            "final_10k_1x": 84100.0}
    chart = {k: [60000.0 + i for i in range(316)] for k in ("o", "h", "l", "c", "ema21", "sma40", "macd", "sig")}
    chart["d"] = dates[:316]
    wk = {"status": "aperto", "side": "short", "entry_px": 65285.7, "history": hist, "chart": chart, "sma40": 70000.0}
    news = [{"title": f"n{i}", "date": "2026-11-26T06:00:00Z", "group": "noi" if i % 2 else "altro", "level": "medio", "link": "x"} for i in range(80)]
    return {
        "date": "2026-11-25", "price": 60514.0,
        "equity": {"1x": [[d, 1.0] for d in dates], "btc": [[d, 2.0] for d in dates]},
        "trades": {"futures": [{"t": d, "px": 60000.0, "q": 0.1} for d in dates[:900]]},
        "series": {"date": dates, "close": [60000.0] * n, "sma200": [50000.0] * n},
        "scout": {"watch": [{"w": "0x" + "a" * 40, "n": i} for i in range(300)]},
        "orderbook": {"bids": [[60000 - i, 1.0] for i in range(300)]},
        "weekly": wk, "weekly_eth": dict(wk, entry_px=3000.0),
        "livelli": {"data": "2026-11-25", "prezzo": 60514.0, "livelli": [{"tipo": "supporto", "prezzo": 57800.0, "cosa": "minimo", "prob": 66}],
                    "serie": {"t0": "2019-09-01", "n": n, **{k: [10000 + i for i in range(n)] for k in ("o", "h", "l", "c", "v")}}},
        "scanner": {"settimana": "2026-11-22", "righe": [{"t": f"C{i}", "n": f"Coin {i}", "q": {"q1": {"wr": 50.0}}} for i in range(144)]},
        "trx_carta": {"nota": "sulla carta: nessun capitale, nessun ordine"}, "scommesse": {"righe": []},
        "news": news, "calendar": [{"name": "CPI", "date": "2026-11-27T13:30:00Z", "impact": "alto"}], "banks": [{"title": "FOMC", "date": "2026-12-09", "time": "20:00"}],
        "cone": {"i80": [52874.0, 75533.0]}, "context": {"rows": [{"label": "Mercato", "text": "ribasso"}]},
    }


def merge(a, b):   # stessa regola di lzMerge nel template
    for k, x in b.items():
        if isinstance(x, dict) and isinstance(a.get(k), dict):
            merge(a[k], x)
        else:
            a[k] = x
    return a


class FileSecondari(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rep = report()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "index.html"
        render(json.loads(json.dumps(cls.rep)), cls.out, standalone=True)
        cls.html = cls.out.read_text()
        cls.R = json.JSONDecoder().raw_decode(cls.html, cls.html.index("const R = ") + len("const R = "))[0]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def f(self, name):
        return json.loads((self.out.parent / name).read_text())

    def test_file_scritti(self):
        for name in list(LAZY_FILES.values()) + ["resto.json"]:
            self.assertTrue((self.out.parent / name).exists(), name)
        self.assertEqual(self.f("grafico.json")["livelli"]["serie"], self.rep["livelli"]["serie"])
        self.assertEqual(set(self.f("scanner.json")), {"scanner", "trx_carta", "scommesse"})
        self.assertEqual(set(self.f("movimenti.json")["weekly"]["history"]), {"eq_dates", "eq1"})
        n = self.f("news.json")
        self.assertEqual(len(n["news"]), 80)                       # news.json resta completo (la pagina lo ricarica ogni 10 minuti)
        self.assertEqual(set(n), {"news", "calendar", "banks"})

    def test_versione_nel_nome(self):   # impronta del contenuto: niente file vecchi in cache uniti a una pagina nuova
        for k, name in LAZY_FILES.items():
            body = (self.out.parent / name).read_bytes()
            self.assertEqual(self.R["_lazy"][k], f"{name}?v={hashlib.sha1(body).hexdigest()[:10]}")

    def test_pagina_senza_dati_pesanti(self):
        for k in ("equity", "trades", "series", "scout", "orderbook", "scanner", "trx_carta", "scommesse"):
            self.assertNotIn(k, self.R, k)
        self.assertNotIn("serie", self.R["livelli"])
        for key in ("weekly", "weekly_eth"):
            self.assertFalse({"eq_dates", "eq1", "eq2"} & set(self.R[key]["history"]))
            self.assertTrue(all(len(v) == 5 for v in self.R[key]["chart"].values()))
        self.assertLess(self.out.stat().st_size, SOGLIA_INDEX)
        self.assertLess(len(json.dumps(self.R)), 40_000)               # i dati rimasti nella pagina sono pochi

    def test_nessun_dato_perso(self):
        full = json.loads(json.dumps(self.R))
        for name in ["resto.json"] + list(LAZY_FILES.values()):
            merge(full, self.f(name))
        full.pop("_lazy"), full.pop("series_start")
        rep = json.loads(json.dumps(self.rep))
        self.assertEqual({k: full[k] for k in rep}, rep)   # render aggiunge solo le sue chiavi calcolate (limiti, journal)

    def test_letture_della_pagina_invariate(self):
        R, rep = self.R, self.rep
        self.assertEqual(R["series_start"], rep["series"]["date"][0])
        for key in ("weekly", "weekly_eth"):   # condsHtml: ultima chiusura e SMA 40 di 4 settimane fa
            c0, c1 = rep[key]["chart"], R[key]["chart"]
            self.assertEqual(c1["c"][-1], c0["c"][-1])
            self.assertEqual(c1["sma40"][len(c1["sma40"]) - 5], c0["sma40"][len(c0["sma40"]) - 5])
        self.assertEqual(R["news"], [n for n in rep["news"] if n["group"] == "noi"])   # Oggi usa solo le notizie "per noi"
        self.assertEqual((R["calendar"], R["banks"]), (rep["calendar"], rep["banks"]))
        self.assertEqual(R["livelli"]["livelli"], rep["livelli"]["livelli"])

    def test_report_senza_parti_secondarie(self):
        with tempfile.TemporaryDirectory() as t:
            html = render({"date": "2026-11-25", "price": 1.0}, Path(t) / "index.html").read_text()
            self.assertEqual(json.loads((Path(t) / "news.json").read_text())["news"], [])
        self.assertIn('"_lazy": {}', html)

    def test_split_non_modifica_il_report(self):
        rep = report()
        before = json.dumps(rep)
        split(rep)
        self.assertEqual(json.dumps(rep), before)


class CaricamentoPigro(unittest.TestCase):
    def test_caricatore(self):
        self.assertIn("window.lazyData = k =>", T)
        self.assertIn("fetch(R._lazy[k]", T)
        self.assertIn("window.lazyView = (k, boxIds, what, ready, onErr) =>", T)
        self.assertIn("non sono arrivati", T)        # messaggio chiaro con Riprova se il file non arriva
        self.assertIn("Riprova", T)
        self.assertIn("Caricamento ${what}…", T)

    def test_pagine_avviate_dal_router(self):
        r = T[T.index("function route() {"):T.index("window.addEventListener(\"hashchange\"")]
        for x in ('lazyView("grafico", "lzGraf"', 'lazyView("scanner", "lzScan"', "movData()", "newsData()"):
            self.assertIn(x, r)
        self.assertNotIn("(function renderChart()", T)     # non più eseguite al caricamento
        self.assertNotIn("(function renderScanner()", T)
        for box in ("lzGraf", "lzScan", "lzNews", "lzSim", "lzDet"):
            self.assertIn(f'id="{box}"', T)

    def test_simulatore_senza_numeri_di_riserva(self):
        sim = T[T.index("function simulate() {"):T.index("function goal(")]
        self.assertIn('if (lazyPending("movimenti")) return;', sim)

    def test_oggi_senza_file_secondari(self):
        """Oggi (riga posizioni, forbice dei livelli, contesto, notizie del giorno) legge solo dati incorporati."""
        blocchi = [T[T.index("(function renderPosLine()"):T.index("// ---- Opzioni (pagina a sé)")],
                   T[T.index("(function renderCone()"):T.index("// ---- Grafico (solo BTC)")],
                   T[T.index("(function renderContext()"):T.index("renderNews();\n")]]
        for b in blocchi:
            for x in ("lazyData", "lazyView", ".serie", "R.scanner", "eq_dates", "trx_carta"):
                self.assertNotIn(x, b)
        self.assertIn("NEWS.filter(isNoi", T[T.index("function renderToday()"):])

    def test_workflow_pubblica_la_cartella(self):   # i file nuovi stanno in site/ accanto a index.html: upload-pages-artifact li pubblica
        wf = (ROOT / ".github" / "workflows" / "daily.yml").read_text()
        up = wf[wf.index("actions/upload-pages-artifact@"):]
        self.assertRegex(up[:200], r"with:\s*\n\s*path: site\n")


class LegendaGrafico(unittest.TestCase):
    def test_pulsante_su_telefono(self):
        g = T[T.index("<!-- ============ GRAFICO"):T.index("<!-- ============ MOVIMENTI")]
        self.assertIn('class="lvLeg gxLeg mHide" id="gxLeg"', g)                       # da 701 px in su resta visibile
        self.assertRegex(g, r'<button type="button" class="gxLegBtn mOnly" id="gxLegBtn"[^>]*>.*Legenda</button>')
        self.assertIn('$("gxLegBtn").onclick = () => sheetNodes("Legenda del grafico", [$("gxLeg")]);', T)
        self.assertIn(".gxLeg.inSheet", T)


if __name__ == "__main__":
    unittest.main()
