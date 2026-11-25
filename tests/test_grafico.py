"""Motore unico dei livelli (report["livelli"]) per Oggi, Grafico, Pre-analisi e Telegram; calcolo live in JS identico a
radar/cone.py (eseguito con node); menu a 5 voci con Liquidazioni spenta (LIQ_ON); Grafico solo BTC con volumi, senza MACD,
con interruttori e tabella completa."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from radar import cone, livelli as L, preview, telegram

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar/dashboard_template.html").read_text()
WEEKLY = {"status": "aperto", "side": "short", "trail": 75763.76, "stop0": 82163.3, "entry_px": 65285.7}
LIQMAP = {"price": 61300, "ts": "2026-11-24 08:02:00",
          "below": [{"price": 59168.0, "usd": 5.7e7, "sig": True}, {"price": 58040.0, "usd": 2e7, "sig": True}, {"price": 60061.0, "usd": 7e6, "sig": False}],
          "above": [{"price": 64894.0, "usd": 5.5e7, "sig": True}, {"price": 62707.0, "usd": 1.8e7, "sig": True}],
          "onchain": {"mid": 60400, "ts": "2026-11-24T08:02", "below": [{"price": 58211.0, "usd": 3.9e7}], "above": [{"price": 63892.0, "usd": 1.5e7}]}}
NODE = shutil.which("node")


def daily() -> pd.DataFrame:
    return pd.read_csv(ROOT / "research/livelli_import/btc_giornaliero.csv", parse_dates=[0], index_col=0)


def block(start: str, end: str) -> str:
    return T[T.index(start):T.index(end)]


LVX_JS = block("// <calc>", "// Oggi · \"Livelli e probabilità a 30 giorni\" = FORBICE")
STUB = """const nfIT = (x, d = 0) => Number(x).toFixed(d); const usd = x => "$" + Math.round(x); const escS = t => String(t);
const artD = (p, s) => p + " " + s; const pct = (x, d = 1) => Number(x).toFixed(d) + "%";
"""


def run_node(js: str):
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "x.js"
        p.write_text(js)
        out = subprocess.run([NODE, str(p)], capture_output=True, text=True, timeout=60)
    if out.returncode:
        raise AssertionError(out.stderr)
    return json.loads(out.stdout)


class Fixture:
    o = None

    @classmethod
    def get(cls):
        if cls.o is None:
            cls.o = L.compute(daily(), {"weekly": WEEKLY, "liqmap": LIQMAP}, None, n_paths=2000)
        return cls.o


class CalcoloLive(unittest.TestCase):
    """Le probabilità ricalcolate sul prezzo live nel browser coincidono con quelle di radar/cone.py per lo stesso prezzo."""
    def test_griglia_vicina_al_calcolo_esatto(self):
        h = cone.history(daily())
        g = cone.touch_grid(h, n_paths=3000)
        lv = [50000, 55000, 58000, 60000, 64000, 70000, 80000]
        ex = cone.touch_probs(h, lv, n_paths=3000)
        for x, e in zip(lv, ex):
            self.assertLess(abs(cone.grid_touch_prob(g, g["prezzo"], x) - e), 0.006, x)
        i80 = cone.compute(h, n_paths=3000)["i80"]
        self.assertAlmostEqual(cone.grid_interval(g, g["prezzo"], 0.8)[0], i80[0], delta=1)

    def test_livelli_usa_la_griglia(self):
        o = Fixture.get()
        for x in o["livelli"]:
            self.assertEqual(x["prob"], round(cone.grid_touch_prob(o["tocco"], o["prezzo"], x["prezzo"]) * 100), x)
        self.assertEqual(o["tocco"]["orizzonte"], cone.H)
        self.assertEqual(len(o["tocco"]["mx"]), cone.GRID_N)
        for k in ("sigma", "drift", "metodo", "fine"):
            self.assertIn(k, o["tocco"])

    @unittest.skipUnless(NODE, "node non disponibile")
    def test_js_uguale_a_python(self):
        g = Fixture.get()["tocco"]
        prices = [52000.5, 58123.0, 61271.08, 63999.9, 70500.0]
        levels = [38555.0, 49000.0, 55130.0, 57800.19, 59168.0, 62707.0, 64894.0, 69000.0, 75763.76, 87395.67, 97924.49]
        js = LVX_JS[:LVX_JS.index("const LVX = ")] + f"""
const G = {json.dumps(g)}, P = {json.dumps(prices)}, LV = {json.dumps(levels)};
console.log(JSON.stringify({{ t: P.map(p => LV.map(l => lvTouch(G, p, l))), i: P.map(p => [lvInterval(G, p, 0.8), lvInterval(G, p, 0.5)]) }}));"""
        out = run_node(js)
        for i, p in enumerate(prices):
            for j, lv in enumerate(levels):
                py = cone.grid_touch_prob(g, p, lv)
                self.assertAlmostEqual(out["t"][i][j], py, places=9, msg=(p, lv))
                self.assertEqual(round(out["t"][i][j] * 100), round(py * 100))
            for k, m in enumerate((0.8, 0.5)):
                for a, b in zip(out["i"][i][k], cone.grid_interval(g, p, m)):
                    self.assertAlmostEqual(a, b, places=6)


@unittest.skipUnless(NODE, "node non disponibile")
class MotoreUnico(unittest.TestCase):
    """Oggi (forbice) e Grafico (linee e tabella) leggono le stesse righe di report["livelli"]: liquidazioni identiche."""
    def _lvx(self, px: float, live: bool):
        o = Fixture.get()
        js = STUB + f"const R = {{ livelli: {json.dumps(o)}, price: {o['prezzo']} }}; const REF = {{ px: {px}, live: {str(live).lower()}, lab: 'chiusura' }};\n" \
            + "const window = { REF };\n" + LVX_JS + """
const rs = LVX.rows();
const oggi = [LVX.nearest(rs, "liq_short", true, true), LVX.nearest(rs, "liq_short", true, false), LVX.nearest(rs, "liq_long", false, false), LVX.nearest(rs, "liq_long", false, true)].filter(Boolean);
const graf = rs.filter(o => /^liq_/.test(o.tipo));
console.log(JSON.stringify({ oggi: oggi.map(o => [o.tipo, o.prezzo, o.reale, o.prob, o.dist]), graf: graf.map(o => [o.tipo, o.prezzo, o.reale, o.prob, o.dist]), n: rs.length,
  i80: LVX.interval(0.8) }));"""
        return o, run_node(js)

    def test_liquidazioni_oggi_uguali_al_grafico(self):
        for px, live in ((None, False), (60000.0, True)):
            o, out = self._lvx(px or Fixture.get()["prezzo"], live)
            src = [(x["tipo"], x["prezzo"], x["reale"]) for x in o["livelli"] if x["tipo"].startswith("liq_")]
            self.assertEqual(sorted((a, b, c) for a, b, c, _, _ in out["graf"]), sorted(src))     # Grafico = tutte quelle della mappa
            graf = {(a, b, c): (p, d) for a, b, c, p, d in out["graf"]}
            for a, b, c, p, d in out["oggi"]:                                                  # Oggi = sottoinsieme, stessi numeri
                self.assertEqual(graf[(a, b, c)], (p, d))
            self.assertEqual({(a, c) for a, _, c, _, _ in out["oggi"]}, {("liq_short", True), ("liq_short", False), ("liq_long", True), ("liq_long", False)})
            self.assertEqual(out["n"], len(o["livelli"]))
            ref = px or o["prezzo"]
            for a, b, c, p, d in out["graf"]:
                self.assertAlmostEqual(d, b / ref - 1, places=9)
                self.assertEqual(p, round(cone.grid_touch_prob(o["tocco"], ref, b) * 100))

    def test_nessun_ricalcolo_dei_cluster_nel_browser(self):
        blk = block("// ---- Mappa unica dei livelli (report.livelli", "// Contesto (report.context")
        self.assertNotIn("R.liqmap", blk)
        self.assertNotIn("R.levels", blk)
        self.assertNotIn("liqImb5", T)
        self.assertNotIn("lq:clusters", T)
        self.assertIn("R.livelli", blk)


class Navigazione(unittest.TestCase):
    def test_menu_sei_voci(self):   # Scanner dal 25/11/2026; Opzioni nascosta dal 25/11/2026 (OPZIONI_ON)
        side = re.findall(r'data-v="(\w+)"', T[T.index('<nav aria-label="Sezioni">'):T.index("</nav>")])
        tab = re.findall(r'data-v="(\w+)"', T[T.index('<nav class="tabbar"'):T.index("</nav>", T.index('<nav class="tabbar"'))])
        self.assertEqual(side, ["oggi", "posizioni", "scanner", "grafico", "movimenti", "notizie"])
        self.assertEqual(tab, side)

    def test_liquidazioni_spenta_e_reindirizzata(self):
        self.assertIn("const LIQ_ON = false;", T)
        self.assertIn('liquidazioni: LIQ_ON ? "liquidazioni" : "grafico"', T)
        self.assertIn("LIQ_ON ? { liquidazioni: \"liquidazioni\" } : {}", T)            # senza flag la pagina non si avvia
        self.assertIn('LIQ_ON ? ["liquidazioni"] : []', T)
        self.assertNotIn('href="#liquidazioni"', T)

    def test_pagina_resta_nel_codice(self):
        from radar.dashboard import render
        with tempfile.TemporaryDirectory() as t:
            html = render({"date": "2026-11-23", "price": 61271.0}, Path(t) / "index.html", standalone=False).read_text()
        self.assertIn('id="v-liquidazioni"', html)
        self.assertIn("window.PAGES.liquidazioni", html)


class Grafico(unittest.TestCase):
    G = block("<!-- ============ GRAFICO", "<!-- ============ MOVIMENTI")
    J = block("// ---- Grafico (solo BTC)", "// Contesto (report.context")

    def test_niente_macd(self):
        for s in (self.G, self.J):
            self.assertNotRegex(s, r"(?i)macd")
        self.assertNotIn("wkMacd", T)

    def test_volumi_e_intervalli(self):
        self.assertIn('addHistogramSeries({ priceScaleId: "vol"', self.J)
        for v in ("4h", "1d", "1w", "1m"):
            self.assertIn(f'data-v="{v}"', self.G)
        self.assertIn("api.binance.com", self.J)
        self.assertIn("data-api.binance.vision", self.J)
        self.assertIn("api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600", self.J)
        self.assertIn("non disponibili", self.J)                                          # stato d'errore del 4h
        self.assertNotRegex(self.G + self.J, r"ETH|ETHUSDT|asset")                         # solo BTC

    def test_interruttori(self):
        for k in ("res", "sup", "lls", "llo", "lss", "lso", "med", "fib", "sto", "trl", "zon"):
            self.assertRegex(self.J, rf'\["{k}", ')
        self.assertIn('localStorage.getItem(KEY)', self.J)
        self.assertRegex(self.J, r"try \{ localStorage.setItem\(KEY")
        for x in ("subscribeCrosshairMove", "scrollToRealTime", "setMarkers", "gxFull", "removePriceLine"):
            self.assertIn(x, self.J)

    def test_tabella_e_diciture(self):
        self.assertIn('id="gxTbl"', self.G)
        self.assertIn("LVX.rows(px)", self.J)
        self.assertIn("L.nota_prob", self.J)
        self.assertIn("L.nota_liq", self.J)
        self.assertIn("contesto, non un segnale", self.J)
        for gone in ('id="lvCard"', 'id="srCard"', 'id="lqCard"', 'id="wkChart"'):
            self.assertNotIn(gone, T)

    def test_oggi_forbice(self):
        o = block("// Oggi · \"Livelli e probabilità a 30 giorni\" = FORBICE", "// ---- Grafico (solo BTC)")
        self.assertIn('href="#grafico">Apri nel Grafico', o)
        self.assertIn("volatilità, non dalla direzione", o)
        self.assertIn("liquidazioni stimate tranne quelle on-chain", o)
        self.assertNotIn("lvChart", T)
        self.assertNotIn("lvAll", o)

    def test_serie_nel_report(self):
        d = daily()
        d["spot_vol"] = 1000.0
        s = L.serie(d.iloc[-50:])
        self.assertEqual((s["t0"], s["n"], len(s["c"]), s["v"][-1]), (str(d.index[-50].date()), 50, 50, 1000))
        self.assertNotIn("d", s)
        o = Fixture.get()
        self.assertNotIn("candele", o)
        self.assertEqual(o["serie"]["n"], len(daily()))


class PreanalisiTelegram(unittest.TestCase):
    def test_sr_rows_dalla_mappa(self):
        o = Fixture.get()
        sr = preview.sr_rows(o, tab={"rows": []})
        r1 = next(z for z in sr if z["name"] == "R1")
        s1 = next(z for z in sr if z["name"] == "S1")
        res = min((x["prezzo"] for x in o["livelli"] if x["tipo"] == "resistenza" and x["prezzo"] > o["prezzo"]), key=lambda p: p - o["prezzo"])
        sup = max(x["prezzo"] for x in o["livelli"] if x["tipo"] == "supporto" and x["prezzo"] < o["prezzo"])
        self.assertEqual((r1["lo"], r1["hi"]), (round(res), round(res)))
        self.assertEqual(s1["lo"], round(sup))
        self.assertEqual(preview.sr_rows(None), [])
        self.assertEqual(preview.sr_rows({"supports": [], "resistances": []}), [])       # vecchio formato: ignorato

    def test_liquidazioni_preanalisi_uguali_a_oggi(self):
        o = Fixture.get()
        ln = preview.liq_near(o)
        px = o["prezzo"]
        for side, tipo, up in (("long", "liq_long", False), ("short", "liq_short", True)):
            for src, reale in (("stima", False), ("onchain", True)):
                exp = min((x for x in o["livelli"] if x["tipo"] == tipo and x["reale"] == reale and (x["prezzo"] > px) == up), key=lambda x: abs(x["prezzo"] - px))
                self.assertEqual(ln[side][src]["prezzo"], round(exp["prezzo"]))

    def test_telegram_r1_s1_un_prezzo(self):
        rep = {"price": 61271, "date": "2026-11-23",
               "preview": {"price": 61271, "today": {"sr": [{"name": "R1", "lo": 87396.0, "hi": 87396.0}, {"name": "S1", "lo": 57800.0, "hi": 57800.0}]}}}
        txt = telegram.today_brief(rep, "2026-11-24")
        self.assertIn("R1 $87.396 · S1 $57.800", txt)
        self.assertNotIn("$87.396–", txt)


if __name__ == "__main__":
    unittest.main()
