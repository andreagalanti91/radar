"""Mappa unica dei livelli (radar/livelli.py): riproduce lo studio (oggi.json), livelli rotti esclusi, nessun dato futuro,
unione con il cono (probabilità di tocco, trailing W3.2), file Coinglass facoltativo, card in Oggi e "Livelli vicini" in Grafico."""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from radar import cone, livelli as L

ROOT = Path(__file__).resolve().parents[1]
IMP = ROOT / "research/livelli_import"
LIQ_L = [(54145, 0.7487), (53312, 0.7117), (51368, 1.18), (50535, 0.9971)]
LIQ_S = [(76915, 0.7208), (91076, 0.8396), (92742, 0.9299), (93853, 0.8866)]
WEEKLY = {"status": "aperto", "side": "short", "trail": 75763.76, "stop0": 82163.3, "entry_px": 65285.7}


def daily() -> pd.DataFrame:
    return pd.read_csv(IMP / "btc_giornaliero.csv", parse_dates=[0], index_col=0)


class Studio(unittest.TestCase):
    """(a) stessi livelli e zone di oggi.json sul giornaliero dello studio."""
    @classmethod
    def setUpClass(cls):
        cls.o = L.build(daily(), liq_long=LIQ_L, liq_short=LIQ_S, liq_fonte="Coinglass 24/11/2026 09:01", storici=L.STORICI)
        cls.ref = json.loads((IMP / "oggi.json").read_text())

    def test_supporti_resistenze(self):
        sr = lambda o, t: sorted(round(x["prezzo"]) for x in o["livelli"] if x["tipo"] == t)
        self.assertEqual(sr(self.o, "supporto"), [38555, 49000, 55130, 57800])
        self.assertEqual(sr(self.o, "resistenza"), [87396, 97924])
        prov = [x for x in self.o["livelli"] if x.get("provvisorio")]
        self.assertEqual([round(x["prezzo"]) for x in prov], [55130])
        self.assertIn("non ancora confermato", prov[0]["cosa"])

    def test_identico_a_oggi_json(self):
        key = lambda o: [(round(x["prezzo"], 2), x["tipo"], x["cosa"]) for x in o["livelli"]]
        self.assertEqual(key(self.o), key(self.ref))
        self.assertAlmostEqual(self.o["atr"], self.ref["atr"], places=6)
        self.assertAlmostEqual(self.o["prezzo"], self.ref["prezzo"], places=2)

    def test_zone(self):
        z = lambda o: [(round(q["da"], 2), round(q["a"], 2), q["n"], q["ruolo"], q["tipi"], q["liq"]) for q in o["zone"]]
        self.assertEqual(z(self.o), z(self.ref))

    def test_storico_non_resistenza(self):
        st = [x for x in self.o["livelli"] if x["prezzo"] == 69000]
        self.assertEqual([x["tipo"] for x in st], ["storico"])
        self.assertIn("non una resistenza attiva", st[0]["cosa"])

    def test_costanti(self):
        self.assertEqual((L.K, L.LIFE, L.GAP), (5, 365 * 3, 0.032))
        self.assertEqual(L.CICLO_MIN, ("2022-06-01", "2023-03-01"))


class SenzaFuturo(unittest.TestCase):
    """(b) un livello rotto in chiusura non è attivo; (c) i livelli noti a una data non cambiano aggiungendo dati futuri."""
    def test_rotto_in_chiusura_escluso(self):
        d = daily()
        sup = next(s for s in L.attivi(d) if s["tipo"] == "supporto" and round(s["prezzo"]) == 57800)
        d2 = d.copy()
        extra = pd.DataFrame({"open": [57000.0], "high": [58000.0], "low": [56000.0], "close": [sup["prezzo"] - 1]},
                             index=[d.index[-1] + pd.Timedelta(days=1)])
        d2 = pd.concat([d2, extra])
        self.assertNotIn(57800, [round(s["prezzo"]) for s in L.attivi(d2) if s["tipo"] == "supporto"])
        self.assertNotIn(57800.19, [round(x["prezzo"], 2) for x in L.build(d2)["livelli"] if x["tipo"] == "supporto"])
        # solo un minimo sotto il livello (senza chiusura sotto) non lo rompe
        extra.loc[:, "close"] = sup["prezzo"] + 100
        self.assertIn(57800, [round(s["prezzo"]) for s in L.attivi(pd.concat([d, extra])) if s["tipo"] == "supporto"])

    def test_troncamento(self):
        d = daily()
        full = {(s["tipo"], s["prezzo"], s["formato"], s["confermato"]) for s in L.swings(d)}
        for cut in ("2019-06-30", "2021-11-17", "2023-01-04", "2024-08-07", "2025-10-08", "2026-07-01"):
            t = pd.Timestamp(cut)
            part = L.swings(d.loc[:t])
            known = {(s["tipo"], s["prezzo"], s["formato"], s["confermato"]) for s in part if s["confermato"] <= t}
            self.assertEqual(known, {x for x in full if x[3] <= t}, cut)
            self.assertTrue(all(s["confermato"] > s["formato"] for s in part))
            # attivi a quella data = swing noti, non scaduti, mai chiusi oltre il livello fino a quella data (solo dati ≤ t)
            exp = sorted((s[0], s[1]) for s in full if s[3] <= t and s[3] + pd.Timedelta(days=L.LIFE) >= t and not (
                (d.loc[s[3]:t, "close"] < s[1]).any() if s[0] == "supporto" else (d.loc[s[3]:t, "close"] > s[1]).any()))
            self.assertEqual(sorted((s["tipo"], s["prezzo"]) for s in L.attivi(d.loc[:t])), exp, cut)


class ConCono(unittest.TestCase):
    """(d) probabilità per ogni livello, monotone nella distanza, coerenti con il cono; trailing W3.2 con posizione aperta."""
    @classmethod
    def setUpClass(cls):
        cls.d = daily()
        rep = {"weekly": WEEKLY, "liqmap": {
            "price": 61300, "ts": "2026-11-24 08:02:00",
            "below": [{"price": 59168.0, "usd": 5.7e7, "sig": True}, {"price": 60061.0, "usd": 7e6, "sig": False}],
            "above": [{"price": 64894.0, "usd": 5.5e7, "sig": True}],
            "onchain": {"mid": 60400, "ts": "2026-11-24T08:02", "below": [{"price": 58211.0, "usd": 3.9e7}], "above": [{"price": 62892.0, "usd": 1.5e7}]}}}
        cls.rep = rep
        cls.o = L.compute(cls.d, rep, None, n_paths=3000)

    def test_probabilita_ovunque(self):
        for x in self.o["livelli"]:
            self.assertIsInstance(x["prob"], int, x)
            self.assertTrue(0 <= x["prob"] <= 100)
        for z in self.o["zone"]:
            self.assertTrue(0 <= z["prob"] <= 100)

    def test_monotone(self):
        px = self.o["prezzo"]
        up = sorted((x for x in self.o["livelli"] if x["prezzo"] > px), key=lambda x: x["prezzo"])
        dn = sorted((x for x in self.o["livelli"] if x["prezzo"] < px), key=lambda x: -x["prezzo"])
        for side in (up, dn):
            p = [x["prob"] for x in side]
            self.assertEqual(p, sorted(p, reverse=True))
            self.assertGreater(p[0], p[-1])

    def test_stessi_cammini_del_cono(self):
        c = cone.compute(cone.history(self.d), WEEKLY, None, n_paths=3000)
        tr = next(o for o in c["levels"] if o["label"] == "Trailing W3.2")
        mine = next(x for x in self.o["livelli"] if x["tipo"] == "trailing")
        self.assertEqual(mine["prob"], tr["prob"])
        self.assertEqual(round(mine["prezzo"]), round(WEEKLY["trail"]))

    def test_trailing_solo_con_posizione(self):
        o = L.compute(self.d, {"weekly": {**WEEKLY, "status": "piatto"}}, None, n_paths=1000)
        self.assertFalse([x for x in o["livelli"] if x["tipo"] == "trailing"])
        self.assertFalse([x for x in self.o["zone"] if "trailing" in x["tipi"]])     # il trailing non entra nelle zone

    def test_fonti_liquidazioni(self):
        lq = [x for x in self.o["livelli"] if x["tipo"].startswith("liq_")]
        self.assertEqual({x["fonte"] for x in lq}, {L.FONTE_STIMA, L.FONTE_ONCHAIN})
        self.assertNotIn(60061, [round(x["prezzo"]) for x in lq])                    # solo cluster significativi della stima
        for x in lq:
            self.assertEqual(x["reale"], x["fonte"] == L.FONTE_ONCHAIN)
            self.assertIn("reali" if x["reale"] else "stimate", x["cosa"])
        self.assertEqual([f["fonte"] for f in self.o["fonti_liq"]], [L.FONTE_STIMA, L.FONTE_ONCHAIN])
        self.assertIn("tranne quelle on-chain", self.o["nota_liq"])

    def test_nota_fissa(self):
        r = pd.read_csv(IMP / "rotture.csv")
        s = r[r["tipo"] == "supporto"]
        self.assertEqual(len(s), 15)
        self.assertEqual(int(s["rientro5"].sum()), 6)
        self.assertEqual(round(-s["ext14"].median() * 100), 11)
        for t in ("contesto, non un segnale", "15 casi dal 2018", "circa l'11%", "6 casi su 15", "entro 5 giorni"):
            self.assertIn(t, self.o["nota"])

    def test_non_tocca_w32(self):
        src = (ROOT / "radar/weekly.py").read_text()
        self.assertNotRegex(src, r"from \.livelli|import livelli|\.livelli import")
        w = dict(WEEKLY)
        L.compute(self.d, {"weekly": w}, None, n_paths=500)
        self.assertEqual(w, WEEKLY)


class Coinglass(unittest.TestCase):
    """(e) file facoltativo: assente, valido, vecchio (ignorato e dichiarato), illeggibile."""
    NOW = pd.Timestamp("2026-11-24 10:00")

    def test_assente(self):
        with tempfile.TemporaryDirectory() as t:
            rows, st = L.coinglass(Path(t) / L.COINGLASS_FILE, self.NOW)
        self.assertEqual((rows, st["stato"]), ([], "assente"))

    def _file(self, t, data):
        p = Path(t) / L.COINGLASS_FILE
        p.write_text(json.dumps({"data": data, "long": [[51368, 1.18], [54145, 0.7487]], "short": [[76915, 0.7208]]}))
        return p

    def test_valido(self):
        with tempfile.TemporaryDirectory() as t:
            rows, st = L.coinglass(self._file(t, "2026-11-24 09:01"), self.NOW)
            o = L.liq_inputs({}, Path(t), self.NOW)
        self.assertEqual(st["stato"], "valido")
        self.assertEqual(len(rows), 3)
        self.assertEqual({r["fonte"] for r in rows}, {"Coinglass, 24/11/2026 09:01"})
        self.assertFalse(any(r["reale"] for r in rows))
        self.assertEqual(o[1][0]["fonte"], "Coinglass, 24/11/2026 09:01")
        b = L.build(daily(), liq=rows)
        self.assertIn("liquidazioni di long stimate: 1,18 miliardi $", [x["cosa"] for x in b["livelli"]])

    def test_vecchio_ignorato(self):
        with tempfile.TemporaryDirectory() as t:
            rows, st = L.coinglass(self._file(t, "2026-11-10 09:01"), self.NOW)
        self.assertEqual((rows, st["stato"], st["data"]), ([], "vecchio", "2026-11-10 09:01"))

    def test_illeggibile(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / L.COINGLASS_FILE
            p.write_text("{non json")
            rows, st = L.coinglass(p, self.NOW)
        self.assertEqual((rows, st["stato"]), ([], "illeggibile"))


class Dashboard(unittest.TestCase):
    """(f) una sola card in Oggi al posto di "Fra 30 giorni"; "Livelli vicini" in Grafico legge report.livelli."""
    T = (ROOT / "radar/dashboard_template.html").read_text()

    def test_card_unica(self):
        blk = self.T[self.T.index("(function renderCone()"):self.T.index("// Contesto (report.context")]
        self.assertNotIn("Fra 30 giorni", self.T)
        self.assertIn("Livelli e probabilità a ${H} giorni", blk)
        self.assertIn("R.livelli", blk)
        self.assertIn("C.note", blk)                                   # dicitura del cono, testuale
        self.assertIn("L.nota", blk)
        self.assertEqual(self.T.count('id="cnCard"'), 1)
        self.assertLess(self.T.index('id="cnCard"'), self.T.index('id="cxCard"'))
        self.assertIn("lvChart", blk)                                  # grafico dell'ultimo anno nei Dettagli
        self.assertIn("LightweightCharts.createChart", blk)
        self.assertNotIn("new Chart(", self.T)                         # niente Chart.js

    def test_livelli_vicini_nuova_fonte(self):
        self.assertIn("const NEWLV = R.livelli", self.T)
        self.assertIn("const LV = SRSRC;", self.T)
        sr = self.T[self.T.index("window.srLevels = px =>"):self.T.index("const REF_SUBS")]
        self.assertIn("NEWLV ?", sr)
        self.assertNotIn("R.levels", self.T.replace(": R.levels;", "", 2))   # report.levels solo come riserva in srLevels

    def test_render(self):
        from radar.dashboard import render
        o = L.build(daily(), liq_long=LIQ_L, liq_fonte="Coinglass, 24/11/2026 09:01")
        rep = {"date": o["data"], "price": o["prezzo"], "livelli": o}
        with tempfile.TemporaryDirectory() as t:
            html = render(rep, Path(t) / "index.html", standalone=False).read_text()
        self.assertIn('"livelli": {"data": "2026-11-23"', html)

    def test_cli_soft(self):
        src = (ROOT / "radar/cli.py").read_text()
        self.assertIn('report["livelli"] = _soft("mappa dei livelli", lambda: mod("livelli").compute(f, report, DATA_DIR))', src)
        self.assertLess(src.index('report["cone"] = _soft'), src.index('report["livelli"] = _soft'))


if __name__ == "__main__":
    unittest.main()
