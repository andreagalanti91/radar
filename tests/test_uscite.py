"""Quando esce una posizione W3.2 in perdita e in profitto (radar/weekly.exits_block, report.weekly[_eth].uscite): soglie
e esiti per short e long con valori noti, simmetria, nessun cambio ai segnali; riquadro "Quando esce" e frase in Oggi nella
dashboard; pannello "Perché è aperta e quando si chiude" con le condizioni e la distribuzione del lato giusto (bug 24/11:
mostrava le regole del long per lo short BTC)."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from radar import weekly
from radar.data import DATA_DIR

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
NODE = shutil.which("node")

# posizione BTC short del 16/11/2026 (report del 23/11): ingresso 65.286, miglior chiusura 58.952, ATR sett. ~6.999
BTC = dict(side="short", entry_px=65285.7, price=61270.93, best=58951.51, trail=75763.76, atr_w=6999.274, ema21=74273.45,
           expo=0.972, capital=30000.0, pnl_pct=5.94, fund7=5.7e-6, flow=-1.41)


def blk(**kw):
    return weekly.exits_block(**(BTC | kw))


class TestSoglie(unittest.TestCase):
    def test_short_btc(self):
        u = blk()
        self.assertAlmostEqual(u["trail"]["soglia"], 65285.7 - 2.5 * 6999.274, delta=0.01)   # ≈ 47.788
        self.assertAlmostEqual(u["trail"]["soglia"], 47788, delta=1)
        self.assertAlmostEqual(u["trail"]["soglia_dist_pct"], (47787.5 / 61270.93 - 1) * 100, delta=0.01)
        self.assertFalse(u["trail"]["soglia_ok"])
        self.assertEqual(u["trail"]["check"], "ogni ora")
        # trailing ed EMA 21 sopra l'ingresso: uscite in perdita; distribuzione al prezzo attuale (sotto l'ingresso) in profitto
        self.assertEqual((u["trail"]["esito"], u["ema21"]["esito"], u["dist"]["esito"]), ("perdita", "perdita", "profitto"))
        self.assertLess(u["trail"]["usd"], 0)
        self.assertAlmostEqual(u["trail"]["pct_price"], -(75763.76 / 65285.7 - 1) * 100, delta=0.01)
        # sul capitale: movimento × esposizione, meno slippage e commissione d'uscita (perp)
        self.assertAlmostEqual(u["trail"]["pct_cap"], -15.81, delta=0.02)
        self.assertAlmostEqual(u["trail"]["usd"], 30000 * u["trail"]["pct_cap"] / 100, delta=1)
        # EMA 21 deve scendere del 12,1% per passare sotto l'ingresso; a prezzo fermo ~13 settimane (α = 2/22)
        self.assertAlmostEqual(u["ema21"]["soglia_dist_pct"], -12.1, delta=0.01)
        self.assertEqual(u["ema21"]["settimane"], 13)
        # distribuzione short: funding 7g < −0,03% e flusso > 0
        self.assertEqual((u["dist"]["fund_soglia"], u["dist"]["fund_ok"], u["dist"]["flow_ok"], u["dist"]["attiva"]),
                         (-0.0003, False, False, False))
        self.assertTrue(blk(fund7=-0.0004, flow=0.2)["dist"]["attiva"])
        # a prezzo invariato l'esito della distribuzione è il P&L attuale meno i costi d'uscita
        self.assertAlmostEqual(u["dist"]["pct_cap"], 5.94 - 0.972 * 61270.93 * 1.001 / 65285.7 * (0.001 + 0.0005) * 100, delta=0.02)

    def test_long_simmetrico(self):
        u = weekly.exits_block("long", 100.0, 110.0, 120.0, 95.0, 10.0, 105.0, 1.0, 10000.0, 10.0, 0.001, -0.5)
        self.assertEqual(u["trail"]["soglia"], 125.0)                   # ingresso + 2,5 ATR
        self.assertEqual((u["trail"]["esito"], u["ema21"]["esito"], u["dist"]["esito"]), ("perdita", "profitto", "profitto"))
        self.assertTrue(u["ema21"]["soglia_ok"])
        self.assertIsNone(u["ema21"]["settimane"])
        self.assertTrue(u["dist"]["attiva"])                            # long: funding > 0,09% e flusso < 0
        self.assertEqual(u["calc"]["fee"], weekly.FEE_SPOT)
        # specchio dello short: stessi valori in percentuale
        s = weekly.exits_block("short", 100.0, 90.0, 80.0, 105.0, 10.0, 95.0, 1.0, 10000.0, 10.0, -0.001, 0.5)
        self.assertEqual(s["trail"]["soglia"], 75.0)
        self.assertEqual((s["trail"]["esito"], s["ema21"]["esito"], s["dist"]["esito"]), ("perdita", "profitto", "profitto"))
        self.assertTrue(s["dist"]["attiva"])

    def test_esito_ai_due_lati_dell_ingresso(self):
        for side, sg in (("short", -1), ("long", 1)):
            near = weekly.exits_block(side, 100.0, 100.0, 100.0, 100.0, 10.0, 100.0, 1.0, 10000.0, 0.0, 0.0, 0.0)
            for d, esito in ((2.0, "profitto"), (-2.0, "perdita")):
                u = weekly.exits_block(side, 100.0, 100.0, 100.0, 100 + sg * d, 10.0, 100 + sg * d, 1.0, 10000.0, 0.0, 0.0, 0.0)
                self.assertEqual((u["trail"]["esito"], u["ema21"]["esito"]), (esito, esito), (side, d))
                self.assertEqual(u["trail"]["soglia_ok"], esito == "profitto")
            # all'ingresso esatto i costi d'uscita fanno perdere un poco
            self.assertEqual(near["trail"]["esito"], "perdita")
            self.assertLess(near["trail"]["usd"], 0)
            self.assertGreater(near["trail"]["usd"], -40)

    def test_settimane_solo_se_semplice(self):
        self.assertIsNone(blk(price=66000.0)["ema21"]["settimane"])     # prezzo oltre l'ingresso: nessuna stima
        self.assertIsNone(blk(ema21=64000.0)["ema21"]["settimane"])     # EMA già dal lato del profitto


@unittest.skipUnless(all((DATA_DIR / f"{n}.csv").exists() for n in ("spot", "perp", "funding", "metrics", "fng")), "dati mancanti")
class TestSegnaliInvariati(unittest.TestCase):
    def test_numeri_storici(self):
        from radar.data import load_all
        from radar.features import build_features
        g = build_features(load_all())
        g = g[g.index <= "2026-11-15"]
        r = weekly.simulate(g)
        self.assertAlmostEqual(float(r["equity"].iloc[-1]), 78474, delta=5)
        self.assertEqual(weekly.metrics(r)["n"], 13)
        e = weekly.evaluate(g, capital=30000.0)
        self.assertEqual(e["history"]["final_10k_1x"], round(float(r["equity"].iloc[-1]), 0))
        if e["status"] in ("aperto", "uscita"):
            u = e["uscite"]
            self.assertEqual(u["trail"]["level"], e["trail"])
            self.assertEqual(u["entry_px"], e["entry_px"])
            self.assertEqual(u["calc"]["pnl_pct"], e["pnl_pct"])
        self.assertIn("sma40_dn", e)


class TestTemplate(unittest.TestCase):
    def test_riquadro_quando_esce(self):
        self.assertIn("Quando esce", T)
        self.assertIn("In perdita se…", T)
        self.assertIn("In profitto se…", T)
        self.assertIn("${qxHtml(W.uscite, px)}", T)                       # card BTC (prezzo live)
        self.assertIn("${qxHtml(E.uscite, E.price)}", T)                  # card ETH
        self.assertIn("qxLine(W.uscite, r.px)", T)                        # frase in Oggi
        self.assertIn('id="wkQxD"', T)                                    # anche nel pannello

    def test_pannello_short_senza_regole_long(self):
        # prima: intestazione fissa "Condizioni d'ingresso long" e distribuzione del long anche per lo short
        self.assertNotIn("Distribuzione<small>funding 7g sopra 0,09% e flusso negativo</small>", T)
        self.assertIn('id="wkCondH"', T)
        self.assertIn("Condizioni d'ingresso ${sd}", T)
        self.assertIn('funding 7g ${xs > 0 ? "sopra 0,09%" : "sotto −0,03%"} e flusso ${xs > 0 ? "negativo" : "positivo"}', T)
        self.assertIn('${L ? "sale con il prezzo e non scende mai" : "scende con il prezzo e non sale mai"}', T)


def block(start: str, end: str) -> str:
    return T[T.index(start):T.index(end)]


STUB = """const nfIT = (x, d = 0) => Number(x).toFixed(d); const usd = x => "$" + Math.round(x);
const pct = (x, d = 1) => (x > 0 ? "+" : "") + Number(x).toFixed(d) + "%"; const sgn = x => (x > 0 ? "+" : "") + Number(x).toFixed(2);
const pc1 = x => pct(x, 1);
const chk = (ok, k, d, v) => JSON.stringify({ ok, k }) + "\\n";
"""


@unittest.skipUnless(NODE, "node non disponibile")
class TestJs(unittest.TestCase):
    def run_js(self, js: str):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "x.js"
            p.write_text(js)
            out = subprocess.run([NODE, str(p)], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_frase_oggi_e_gruppi(self):
        u = blk()
        js = STUB + block("function qxAt(U, x) {", "(function renderWeekly() {") + \
            f"const U = {json.dumps(u)}; const P = qxParts(U, U.price);\n" \
            "console.log(JSON.stringify({ line: qxLine(U, U.price), loss: P.loss.map(r => r[0]), gain: P.gain.map(r => r[0]), html: qxHtml(U, U.price) }));"
        o = self.run_js(js)
        line = re.sub("<[^>]+>", "", o["line"])
        self.assertEqual(line, "esce in perdita sopra $74273 (chiusura settimanale) o a $75764 (trailing) · "
                               "in profitto con chiusura sotto ~$47800 o per distribuzione")
        self.assertEqual(o["loss"], ["Trailing a $75764", "Chiusura sett. sopra $74273"])
        self.assertEqual(o["gain"], ["Chiusura sotto ~$47800", "EMA 21 sotto $65286", "Distribuzione"])
        self.assertIn("~13 sett. a prezzo fermo", o["html"])

    def test_condizioni_short_nel_pannello(self):
        X = {"chart": {"c": [61270.0], "sma40": [80000, 79900, 79800, 79700, 79500]}, "sma40": 79500.0, "ema21": 74273.0,
             "ema20_up": False, "flow": -1.41, "sma40_dn": True, "sma40_4w": 80000.0, "f1_ok": True, "trend_age": 0,
             "old_trend": 16, "macd": 0, "macd_sig": 0}
        fn = block("  function condsHtml(X, sd) {", "  // uscite da sorvegliare")
        o = self.run_js(STUB + fn + f"const X = {json.dumps(X)};\n"
                        "const p = s => condsHtml(X, s).trim().split('\\n').map(JSON.parse);\n"
                        "console.log(JSON.stringify({ s: p('short'), l: p('long') }));")
        self.assertEqual([c["k"] for c in o["s"]], ["Trend: sotto la SMA 40 settimane", "SMA 40 in calo su 4 settimane",
                                                     "EMA 20 settimanale in calo", "Chiusura sotto la EMA 21", "Flusso dei perp negativo"])
        self.assertTrue(all(c["ok"] for c in o["s"]))                     # lo short del 16/11 ha tutte le condizioni verdi
        self.assertNotIn("Filtro MACD 8/21/5", [c["k"] for c in o["s"]])  # niente MACD per gli short
        self.assertIn("Filtro MACD 8/21/5", [c["k"] for c in o["l"]])
        self.assertFalse(any(c["ok"] for c in o["l"][:4]))


if __name__ == "__main__":
    unittest.main()
