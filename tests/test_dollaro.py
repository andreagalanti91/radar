"""Controllo "Dollaro" (radar/dollaro.py, scheda in Posizioni): calcoli (EMA, RSI, livelli, stato), divergenza con la STESSA
definizione di research/dxy_divergenza/check.py, frasi per verso × stato, fonti e ripiego senza rete, scheda nella pagina.
Niente rete (risposte finte)."""
import json
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from radar import dollaro as D
from radar.dashboard import render

ROOT = Path(__file__).resolve().parents[1]
T = (ROOT / "radar" / "dashboard_template.html").read_text()
STUDY_DIR = ROOT / "research" / "dxy_divergenza"
TODAY = pd.Timestamp("2026-11-26")


def serie(n=520, end="2026-11-25", seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=end, periods=n)
    return pd.Series(100 + np.cumsum(rng.normal(0, .35, n)), index=idx, name="close")


def yahoo_json(s, today_bar=True):
    """Risposta del chart API di Yahoo: timestamp all'apertura della seduta a New York (00:00 EST = 05:00 UTC)."""
    idx = list(s.index) + ([TODAY] if today_bar else [])
    vals = list(s.to_numpy()) + ([999.0] if today_bar else [])
    ts = [int((d + pd.Timedelta(hours=5)).timestamp()) for d in idx]
    return json.dumps({"chart": {"result": [{"meta": {"gmtoffset": -18000}, "timestamp": ts,
                                             "indicators": {"quote": [{"close": vals}]}}]}})


def fred_csv(s):
    return "observation_date,DTWEXBGS\n" + "".join(f"{d:%Y-%m-%d},{v:.4f}\n" for d, v in s.items())


def http_of(yahoo=None, fred=None):
    calls = []

    def http(url, params):
        calls.append((url, dict(params)))
        if "yahoo" in url:
            if yahoo is None:
                raise ConnectionError("Yahoo giù")
            return yahoo
        if fred is None:
            raise ConnectionError("FRED giù")
        return fred
    http.calls = calls
    return http


def check_events(dxy):
    """Ciclo di research/dxy_divergenza/check.py copiato alla lettera (eventi di divergenza ribassista)."""
    def rsi(s, n=14):
        d = s.diff(); up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()  # noqa: E702,E501
        return 100 - 100 / (1 + up / dn)
    r = rsi(dxy); ev = []; last = None  # noqa: E702
    for i in range(60, len(dxy)):
        w = dxy.iloc[i-60:i]; rw = r.iloc[i-60:i]  # noqa: E702
        if dxy.iloc[i] > w.max() and rw.max() > 65 and r.iloc[i] < rw.max() - 2:
            d = dxy.index[i]
            if last is None or (d - last).days > 30: ev.append(d); last = d  # noqa: E701,E702
    return ev


def fake(close, e20, e50, lo30, hi30, state, bear=None, bull=None):
    return {"close": close, "ema20": e20, "ema50": e50, "lo30": lo30, "hi30": hi30, "state": state,
            "break_dn": close < e20 and close < lo30, "break_up": close > e20 and close > hi30, "bear": bear, "bull": bull}


ACT = {"active": True, "confirmed": None}
OLD = {"active": False, "confirmed": "2026-09-15"}


class TestDivergenza(unittest.TestCase):
    def test_stessa_definizione_dello_studio_sui_dati_veri(self):
        d = pd.read_csv(STUDY_DIR / "dollaro_fred.csv")
        d.columns = ["date", "v"]
        d = d[pd.to_numeric(d.v, errors="coerce").notna()]
        s = pd.Series(d.v.astype(float).values, index=pd.to_datetime(d.date))
        mine = [e["date"] for e in D.divergences(s, D.rsi(s), "bear")]
        self.assertEqual(mine, check_events(s))
        self.assertEqual(len([x for x in mine if x >= pd.Timestamp("2006")]), 50)     # risultati.txt: 50 eventi dal 2006
        txt = (STUDY_DIR / "risultati.txt").read_text()
        last = re.search(r"ultimi eventi: \[(.*)\]", txt).group(1).replace("'", "").split(", ")
        self.assertEqual([x.strftime("%Y-%m-%d") for x in mine[-6:]], last)

    def test_stessa_definizione_su_serie_sintetiche(self):
        for seed in range(5):
            s = serie(seed=seed)
            self.assertEqual([e["date"] for e in D.divergences(s, D.rsi(s), "bear")], check_events(s))

    def test_rialzista_e_lo_specchio(self):
        s = serie(seed=7)
        neg = 200 - s                                      # serie capovolta: i minimi diventano massimi
        bull = [e["date"] for e in D.divergences(s, D.rsi(s), "bull")]
        self.assertEqual(bull, check_events(neg))
        ev = D.divergences(s, D.rsi(s), "bull")
        for e in ev:
            self.assertLess(e["ref_rsi"], 35)
            self.assertGreater(e["rsi"], e["ref_rsi"] + 2)
            self.assertLess(e["date"] - e["ref_date"], pd.Timedelta(days=100))

    def test_riferimento_e_il_massimo_rsi_della_finestra(self):
        s = serie(seed=1)
        r = D.rsi(s)
        for e in D.divergences(s, r, "bear"):
            i = s.index.get_loc(e["date"])
            self.assertEqual(e["ref_date"], r.iloc[i - 60:i].idxmax())
            self.assertGreater(e["close"], s.iloc[i - 60:i].max())


class TestCalcolo(unittest.TestCase):
    def test_ema_rsi_livelli_variazione(self):
        s = serie()
        a = D.analyze(s)
        self.assertAlmostEqual(a["ema20"], s.ewm(span=20, adjust=False).mean().iloc[-1], places=3)
        self.assertAlmostEqual(a["ema50"], s.ewm(span=50, adjust=False).mean().iloc[-1], places=3)
        w = s[(s.index < s.index[-1]) & (s.index >= s.index[-1] - pd.Timedelta(days=30))]
        self.assertAlmostEqual(a["lo30"], w.min(), places=3)
        self.assertAlmostEqual(a["hi30"], w.max(), places=3)
        self.assertAlmostEqual(a["ch20"], (s.iloc[-1] / s.iloc[-21] - 1) * 100, places=2)
        self.assertTrue(0 <= a["rsi"] <= 100)
        self.assertEqual(a["above20"], s.iloc[-1] > a["ema20"])

    def test_stati(self):
        idx = pd.bdate_range(end="2026-11-25", periods=300)
        up = pd.Series(np.linspace(90, 110, 300), index=idx)               # salita regolare: sopra le medie
        self.assertEqual(D.analyze(up)["state"], "forte")
        dn = pd.Series(np.linspace(110, 90, 300), index=idx)
        self.assertEqual(D.analyze(dn)["state"], "debole")
        self.assertTrue(D.analyze(dn)["break_dn"])
        # divergenza ribassista recente non confermata → "in indebolimento"
        s = serie(seed=0)
        for seed in range(60):
            s = serie(seed=seed)
            a = D.analyze(s)
            if a["bear"] and a["bear"]["active"]:
                break
        else:
            self.skipTest("nessuna serie sintetica con divergenza attiva")
        if not (a["close"] < a["ema20"] and a["close"] < a["ema50"]) and not a["break_dn"]:
            self.assertEqual(a["state"], "indeb")
            self.assertEqual(a["state_name"], "Dollaro in indebolimento (divergenza, da confermare)")

    def test_conferma_della_divergenza(self):
        s = serie(seed=2)
        a = D.analyze(s)
        for k in ("bear", "bull"):
            v = a[k]
            if v and v["confirmed"]:
                self.assertGreaterEqual(v["confirmed"], v["date"])
                self.assertFalse(v["active"])


class TestFrase(unittest.TestCase):
    def test_short(self):
        self.assertEqual(D.frase("short", fake(105, 103, 101, 102, 106, "forte")), "Dollaro forte: vento a favore dello short")
        f = D.frase("short", fake(104, 103, 101, 102.5, 106, "indeb", bear=ACT))
        self.assertEqual(f, "Divergenza ribassista sul dollaro: da confermare sotto 102,50")
        self.assertEqual(D.frase("short", fake(101, 103, 102, 102, 106, "debole", bear=OLD)),
                         "Dollaro in calo: vento contrario allo short, prudenza")
        self.assertEqual(D.frase("short", fake(102.5, 103, 104, 102, 106, "debole")), "Dollaro debole: vento contrario allo short")

    def test_long_specchio(self):
        self.assertEqual(D.frase("long", fake(101, 103, 104, 102, 106, "debole")), "Dollaro debole: vento a favore del long")
        self.assertEqual(D.frase("long", fake(107, 103, 101, 102, 106, "forte")), "Dollaro in rialzo: vento contrario al long, prudenza")
        self.assertEqual(D.frase("long", fake(105, 103, 101, 102, 106, "forte")), "Dollaro forte: vento contrario al long")
        self.assertEqual(D.frase("long", fake(104, 103, 101, 102.5, 106, "indeb", bear=ACT)),
                         "Divergenza ribassista sul dollaro: da confermare sotto 102,50")
        self.assertEqual(D.frase("long", fake(95, 97, 99, 96, 100, "debole", bull=ACT)),
                         "Divergenza rialzista sul dollaro: da confermare sopra 100,00")

    def test_flat_e_nota(self):
        self.assertIn("nessuna posizione", D.frase(None, fake(105, 103, 101, 102, 106, "forte")))
        c = D.frase_completa("short", fake(105, 103, 101, 102, 106, "forte"))
        self.assertIn("contesto, non cambia W3.2 (studio research/dxy_divergenza: nessun vantaggio dimostrabile)", c)
        frasi = {D.frase(sd, fake(*x)) for sd in ("long", "short") for x in
                 ((105, 103, 101, 102, 106, "forte"), (101, 103, 104, 102, 106, "debole"))}
        self.assertEqual(len(frasi), 4)
        for f in frasi:
            self.assertLessEqual(len(f), 70)

    def test_studio_come_i_risultati(self):
        txt = (STUDY_DIR / "risultati.txt").read_text().splitlines()
        for row, line in zip(D.STUDY["rows"], txt):
            self.assertTrue(line.startswith(f"{row['k']}: {row['n']} eventi"), line)
            for h, (m, g, q, gq) in row["h"].items():
                exp = f"{h}g mediana {m:+.1f}% (giù {g}%) · qualsiasi {q:+.1f}% (giù {gq}%)"
                self.assertIn(exp.replace("-0.0", "+0.0"), line.replace("-0.0", "+0.0"))
        self.assertIn(f"dal 2019-09: {D.STUDY['corr_all']:+.2f}; ultime 52 settimane: {D.STUDY['corr_52w']:+.2f}", txt[3])


class TestFonti(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.s = serie()

    def test_yahoo_salva_due_anni_solo_barre_chiuse_e_non_riscrive(self):
        h = http_of(yahoo=yahoo_json(self.s))
        s, src, note = D.load(self.dir, http=h, today=TODAY)
        self.assertEqual((src, note), ("yahoo", None))
        self.assertEqual(s.index[-1], pd.Timestamp("2026-11-25"))      # la barra di oggi (999) è scartata
        self.assertNotIn(999.0, s.to_numpy())
        self.assertEqual(h.calls[0][1], {"range": "2y", "interval": "1d"})
        p = self.dir / D.FILE
        txt = p.read_text()
        self.assertEqual(txt.splitlines()[0], "date,close,src")
        d = pd.read_csv(p, parse_dates=["date"])
        self.assertLessEqual((d.date.iloc[-1] - d.date.iloc[0]).days, D.KEEP_DAYS)
        m = p.stat().st_mtime_ns
        self.assertFalse(D._save(s, "yahoo", p))
        self.assertEqual(p.stat().st_mtime_ns, m)
        # dato fresco: nessuna nuova richiesta
        h2 = http_of(yahoo=yahoo_json(self.s))
        D.load(self.dir, http=h2, today=TODAY)
        self.assertEqual(h2.calls, [])

    def test_query2_se_query1_fallisce(self):
        calls = []

        def h(url, params):
            calls.append(url)
            if "query1" in url:
                raise ConnectionError("429")
            return yahoo_json(self.s)
        s, src, _ = D.load(self.dir, http=h, today=TODAY)
        self.assertEqual(src, "yahoo")
        self.assertEqual(len(calls), 2)

    def test_senza_yahoo_ripiega_su_fred_e_lo_dichiara(self):
        f = self.s * 1.19
        s, src, note = D.load(self.dir, http=http_of(fred=fred_csv(f)), today=TODAY)
        self.assertEqual(src, "fred")
        self.assertIn("FRED DTWEXBGS", note)
        self.assertIn("settimana di ritardo", note)
        self.assertEqual(pd.read_csv(self.dir / D.FILE)["src"].iloc[-1], "fred")

    def test_fred_non_sovrascrive_il_dxy_salvato(self):
        old = self.s[self.s.index <= "2026-11-10"]
        D._save(old, "yahoo", self.dir / D.FILE)
        before = (self.dir / D.FILE).read_text()
        s, src, note = D.load(self.dir, http=http_of(fred=fred_csv(self.s * 1.19)), today=TODAY)
        self.assertEqual(src, "fred")
        self.assertEqual((self.dir / D.FILE).read_text(), before)

    def test_senza_rete_ultimo_file(self):
        D._save(self.s[self.s.index <= "2026-11-24"], "yahoo", self.dir / D.FILE)
        s, src, note = D.load(self.dir, http=http_of(), today=TODAY)
        self.assertEqual(src, "yahoo")
        self.assertIn("24/11/2026", note)
        D._save(self.s[self.s.index <= "2026-11-02"], "yahoo", self.dir / D.FILE)   # vecchio: prova FRED, poi il file
        s, src, note = D.load(self.dir, http=http_of(), today=TODAY)
        self.assertIn("ultimo dato salvato del 02/11/2026", note)
        r = D.build(self.dir, side="short", http=http_of(), today=TODAY)
        self.assertIn("02/11/2026", r["source_note"])

    def test_senza_rete_e_senza_file_solleva_e_il_giro_continua(self):
        with self.assertRaises(RuntimeError):
            D.load(self.dir, http=http_of(), today=TODAY)
        from radar.cli import _soft
        self.assertIsNone(_soft("dollaro (DXY)", lambda: D.build(self.dir, http=http_of(), today=TODAY)))

    def test_build_compatto(self):
        r = D.build(self.dir, side="short", http=http_of(yahoo=yahoo_json(self.s)), today=TODAY)
        self.assertIn(r["state"], ("forte", "indeb", "debole"))
        S = r["series"]
        self.assertTrue(len(S["d"]) == len(S["c"]) == len(S["e20"]) == len(S["e50"]) == len(S["rsi"]))
        self.assertLessEqual((pd.Timestamp(S["d"][-1]) - pd.Timestamp(S["d"][0])).days, D.CHART_DAYS)
        for m in S["bear"] + S["bull"]:
            self.assertLess(m["j"], m["i"])
        self.assertEqual(r["frase"], D.frase("short", r))
        self.assertEqual(r["note"], D.NOTE)
        self.assertLess(len(json.dumps(r)), 12000)
        self.assertFalse(any(k.startswith("_") for k in r))


class TestScheda(unittest.TestCase):
    def test_nel_giro_e_nel_template(self):
        cli = (ROOT / "radar" / "cli.py").read_text()
        self.assertIn('_soft("dollaro (DXY)", lambda: mod("dollaro").build(DATA_DIR', cli)
        self.assertIn('"onchain", "dollaro"):', cli)
        self.assertIn('<div class="oc" id="ocBox" hidden></div><div class="oc" id="dxBox" hidden></div>', T)
        self.assertLess(T.index('id="ocSec"'), T.index('id="dxSec"'))
        self.assertLess(T.index('id="dxSec"'), T.index('id="v-opzioni"'))
        js = T[T.index("function renderDollaro"):T.index("// ---- Oggi e Posizioni · posizioni aperte")]   # variante B: la riga di Oggi è diventata la tessera delle posizioni
        for x in ('class="ocTap" id="dxOpen" aria-haspopup="dialog"', "Dettagli ›", "dxChartP", "dxChartR", "D.frase", "D.note"):
            self.assertIn(x, js)
        for t in ("Dove siamo", "Ultimi 6 mesi", "Divergenza", "Livelli di conferma", "Dopo le divergenze passate (studio)",
                  "Dollaro e BTC", "Cosa significa per la posizione", "Fonte"):
            self.assertIn(f'sec("{t}"', js)
        # scheda chiusa come il Ciclo on-chain: termometro (fasce, soglie, tacca EMA20, punto), niente cifre fuori dal pannello
        for x in ('class="ocTh dxTh"', 'class="tick"', 'class="dot ${S}"', "calo confermato", "rialzo confermato", "${thermo}"):
            self.assertIn(x, js)
        self.assertNotIn("dxVal", T)

    def test_dati_nella_pagina(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        r = D.build(Path(tmp.name), side="short", http=http_of(yahoo=yahoo_json(serie())), today=TODAY)
        out = render({"date": "2026-11-25", "dollaro": r}, out=Path(tmp.name) / "index.html", standalone=False)
        html = out.read_text()
        R = json.JSONDecoder().raw_decode(html, html.index("const R = ") + len("const R = "))[0]
        self.assertEqual(R["dollaro"]["state"], r["state"])                 # Posizioni immediata: dati nella pagina
        self.assertIn(D.NOTE, html)

    def test_apre_nel_browser_senza_overflow(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright non installato")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        r = D.build(Path(tmp.name), side="short", http=http_of(yahoo=yahoo_json(serie(seed=5))), today=TODAY)
        cut = lambda a, b: T[T.index(a):T.index(b)]  # noqa: E731
        style = cut("<style>", "</style>") + "</style>"
        sheet = next(l for l in T.splitlines() if '<dialog class="dlg" id="sheet"' in l)
        js = "\n".join([
            "const $ = id => document.getElementById(id);",
            cut("// Pannello generico: openSheet", "// telefono: sposta blocchi"),
            cut("const nfIT = window.nfIT", "const nfS = "), cut("const pct = ", "const css = "),
            next(l for l in T.splitlines() if l.startswith("const escS = ")),
            "const R = " + json.dumps({"dollaro": r, "weekly": {"status": "flat"}}) + ";",
            cut("(function renderDollaro()", "// ---- Oggi e Posizioni · posizioni aperte")])
        page = Path(tmp.name) / "dx.html"
        page.write_text(f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                        f'{style}</head><body><div class="section" id="dxSec" hidden><div class="card ocCard" id="dxCard"></div></div>'
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
            pg.wait_for_selector("#dxOpen", state="visible", timeout=5000)
            pg.wait_for_timeout(50)
            self.assertGreaterEqual(pg.query_selector("#dxOpen").bounding_box()["height"], 44)
            q = lambda s: pg.evaluate(f"document.querySelectorAll('#dxOpen {s}').length")  # noqa: E731
            self.assertEqual((q(".dxTh .bar i"), q(".dxTh .thr:not(.ema)"), q(".dxTh .tick"), q(".dxTh .dot"), q(".dxTh .zn")), (3, 2, 1, 1, 3))
            self.assertEqual(q(".dxTh .zn.on"), 1)                                   # una sola fascia evidenziata
            txt = pg.evaluate("document.getElementById('dxOpen').innerText")
            self.assertNotIn("RSI", txt)                                              # cifre e data solo nel pannello
            self.assertNotIn("20 giorni", txt)
            box, dot = pg.query_selector("#dxOpen .dxTh").bounding_box(), pg.query_selector("#dxOpen .dxTh .dot").bounding_box()
            self.assertTrue(box["x"] <= dot["x"] and dot["x"] + dot["width"] <= box["x"] + box["width"] + 1)
            pg.click("#dxOpen")
            self.assertTrue(pg.evaluate("document.getElementById('sheet').open"))
            pg.wait_for_timeout(100)
            self.assertEqual(pg.evaluate("[...document.querySelectorAll('#sheetB .ocSec h3')].map(h => h.textContent)"),
                             ["Dove siamo", "Ultimi 6 mesi", "Divergenza", "Livelli di conferma", "Dopo le divergenze passate (studio)",
                              "Dollaro e BTC", "Cosa significa per la posizione", "Fonte"])
            self.assertEqual(pg.evaluate("document.querySelectorAll('#dxChartP svg path.dc').length"), 1)
            self.assertEqual(pg.evaluate("document.querySelectorAll('#dxChartR svg path.rsi').length"), 1)
            self.assertEqual(pg.evaluate("document.querySelectorAll('#sheetB .dxTb .c').length"), 9)
            self.assertLessEqual(pg.evaluate("document.documentElement.scrollWidth"), wd)
            self.assertLessEqual(pg.evaluate("document.getElementById('sheetB').scrollWidth"),
                                 pg.evaluate("document.getElementById('sheetB').clientWidth"))
            pg.keyboard.press("Escape")
            self.assertFalse(pg.evaluate("document.getElementById('sheet').open"))
            self.assertEqual(errs, [])
            pg.close()


if __name__ == "__main__":
    unittest.main()
