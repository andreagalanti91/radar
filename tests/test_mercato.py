"""Mercato power (radar/mercato.py): regole dei sei semafori per long e short, nessun punteggio unico, registro giornaliero
data/mercato_power.csv (una riga al giorno per asset), aggancio nel giro orario. Niente rete."""
import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from radar import mercato as M

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 26, 18, tzinfo=timezone.utc)


def weekly(side="short", status="aperto", flow=-1.0, fund7=0.0001, attiva=False, price=60000.0):
    return {"status": status, "side": side, "flow": flow, "fund7": fund7, "price": price, "dist_now": attiva,
            "uscite": {"dist": {"fund7": fund7, "flow": flow, "attiva": attiva}}}


def report(side="short", zone="cap", dstate="indeb", mp_dist=15.9, hours=14.0, vix=26.4, fomc="2026-12-09", **w):
    return {"weekly": weekly(side, **w), "weekly_eth": weekly(side, flow=-0.7, price=1700.0),
            "onchain": {"mvrv": 1.14, "zone": zone, "zone_name": {"cap": "Capitolazione", "eup": "Euforia", "norm": "Normale"}[zone], "breve": "x"},
            "dollaro": {"close": 103.67, "state": dstate, "src": "yahoo", "frase": "y"},
            "opex": {"max_pain": 70000.0, "dist_pct": mp_dist, "hours": hours, "status": "Scadenza venerdì 27/11 · tra 14 h", "frase": "z — solo contesto"},
            "macro": {"assets": [{"key": "vix", "close": vix, "d20_pct": 8.8, "date": "2026-11-24"}]},
            "banks": [{"bank": "Fed", "date": fomc}], "context": {"fed": {"rate": {"direction": "in rialzo"}, "cpi": {"direction": "in salita"}}}}


def stati(r, asset="BTC"):
    return {i["key"]: i["stato"] for i in M.build(r, now=NOW)["assets"][asset]["items"]}


class Regole(unittest.TestCase):
    def test_caso_del_report_pubblicato(self):
        s = stati(report())
        self.assertEqual(s, {"onchain": "contro", "dollaro": "neutro", "opex": "contro", "vix": "neutro", "fed": "neutro", "flusso": "favore"})
        b = M.build(report(), now=NOW)["assets"]["BTC"]
        self.assertEqual(b["riga"], "1 a favore · 3 neutri · 2 contro")

    def test_ciclo_onchain(self):
        self.assertEqual(stati(report("short", zone="cap"))["onchain"], "contro")
        self.assertEqual(stati(report("long", zone="cap", flow=1.0))["onchain"], "favore")
        self.assertEqual(stati(report("short", zone="eup"))["onchain"], "favore")
        self.assertEqual(stati(report("long", zone="eup", flow=1.0))["onchain"], "contro")
        self.assertEqual(stati(report("short", zone="norm"))["onchain"], "neutro")

    def test_dollaro(self):
        self.assertEqual(stati(report("short", dstate="forte"))["dollaro"], "favore")
        self.assertEqual(stati(report("long", dstate="forte", flow=1.0))["dollaro"], "contro")
        self.assertEqual(stati(report("short", dstate="debole"))["dollaro"], "contro")
        self.assertEqual(stati(report("long", dstate="debole", flow=1.0))["dollaro"], "favore")
        self.assertEqual(stati(report("long", dstate="indeb", flow=1.0))["dollaro"], "neutro")

    def test_opex_solo_vicina_e_lontana_dal_prezzo(self):
        self.assertEqual(stati(report("long", flow=1.0))["opex"], "favore")                 # massimo dolore sopra il prezzo
        self.assertEqual(stati(report("short", mp_dist=-8.0))["opex"], "favore")            # sotto: a favore dello short
        self.assertEqual(stati(report("short", mp_dist=2.0))["opex"], "neutro")             # entro il 3%
        self.assertEqual(stati(report("short", hours=10 * 24))["opex"], "neutro")           # oltre 7 giorni

    def test_vix(self):
        self.assertEqual(stati(report("short", vix=34))["vix"], "favore")
        self.assertEqual(stati(report("long", vix=34, flow=1.0))["vix"], "contro")
        self.assertEqual(stati(report("short", vix=13))["vix"], "contro")
        self.assertEqual(stati(report("long", vix=13, flow=1.0))["vix"], "favore")
        self.assertEqual(stati(report("long", vix=20, flow=1.0))["vix"], "neutro")

    def test_fed_contro_a_ridosso_per_entrambi(self):
        self.assertEqual(stati(report("short", fomc="2026-11-28"))["fed"], "contro")
        self.assertEqual(stati(report("long", fomc="2026-11-28", flow=1.0))["fed"], "contro")
        self.assertEqual(stati(report("long", fomc="2026-12-20", flow=1.0))["fed"], "neutro")

    def test_flusso_e_distribuzione(self):
        self.assertEqual(stati(report("short", flow=-1.0))["flusso"], "favore")
        self.assertEqual(stati(report("short", flow=0.5))["flusso"], "neutro")
        self.assertEqual(stati(report("short", flow=0.5, attiva=True))["flusso"], "contro")
        self.assertEqual(stati(report("long", flow=1.2))["flusso"], "favore")
        self.assertEqual(stati(report("long", flow=-0.4))["flusso"], "neutro")
        it = next(i for i in M.build(report(), now=NOW)["assets"]["BTC"]["items"] if i["key"] == "flusso")
        self.assertTrue(it["w3"])                                                            # l'unico che W3.2 usa

    def test_flat_tutti_neutri(self):
        x = M.build(report(status="flat"), now=NOW)["assets"]["BTC"]
        self.assertIsNone(x["lato"])
        self.assertTrue(all(i["stato"] == "neutro" for i in x["items"]))
        self.assertIn("nessuna posizione aperta", x["riga"])

    def test_dati_mancanti_non_rompono(self):
        r = report()
        for k in ("onchain", "dollaro", "opex", "macro", "banks", "context"):
            r.pop(k)
        x = M.build(r, now=NOW)["assets"]["BTC"]
        self.assertEqual([i["key"] for i in x["items"]], ["flusso"])
        self.assertEqual(M.build({}, now=NOW)["assets"], {})


class NessunPunteggio(unittest.TestCase):
    def test_solo_conteggio(self):
        m = M.build(report(), now=NOW)
        txt = json.dumps(m, ensure_ascii=False).lower()
        for bad in ("score", "punteggio\":", "totale", "media"):
            self.assertNotIn(bad, txt)
        b = m["assets"]["BTC"]
        self.assertEqual(set(b["conteggio"]), {"favore", "neutro", "contro"})
        self.assertEqual(sum(b["conteggio"].values()), len(b["items"]))
        self.assertIn("decide W3.2", m["nota"])
        for k, _, regola in M.SEMAFORI:                                                    # regole scritte, una per semaforo
            self.assertTrue(len(regola) > 40, k)

    def test_w32_non_legge_il_modulo(self):
        for f in ("weekly.py", "guard.py", "limiti.py", "alerts.py"):
            p = ROOT / "radar" / f
            if p.exists():
                self.assertNotRegex(p.read_text(), r"from \.mercato|import mercato|\"mercato\"\)|report\[.mercato.\]", f)


class Registro(unittest.TestCase):
    def test_una_riga_al_giorno_per_asset(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            M.build(report(), d, now=NOW)
            M.build(report(vix=34), d, now=NOW.replace(hour=20))                              # stesso giorno: sostituisce
            M.build(report(), d, now=datetime(2026, 11, 27, 9, tzinfo=timezone.utc))
            rows = list(csv.DictReader((d / M.LOG_FILE).open()))
        self.assertEqual([(r["data"], r["asset"]) for r in rows], [("2026-11-26", "BTC"), ("2026-11-26", "ETH"), ("2026-11-27", "BTC"), ("2026-11-27", "ETH")])
        self.assertEqual(rows[0]["vix"], "favore")                                           # l'ultima del giorno
        self.assertEqual(rows[0]["lato"], "short")
        self.assertEqual(rows[0]["prezzo"], "60000.0")
        self.assertEqual((rows[2]["favore"], rows[2]["neutri"], rows[2]["contro"]), ("1", "3", "2"))
        self.assertEqual(list(rows[0]), M.COLS)


class Giro(unittest.TestCase):
    def test_aggancio_in_cli(self):
        cli = (ROOT / "radar" / "cli.py").read_text()
        self.assertIn('report["mercato"] = _soft("mercato power", lambda: mod("mercato").build(report, DATA_DIR))', cli)
        self.assertLess(cli.index('report["opex"] = _soft('), cli.index('report["mercato"] = _soft('))   # dopo i dati che legge
        self.assertIn('"mercato", "opex", "onchain", "dollaro"):', cli)                                  # tolto dal report se manca


if __name__ == "__main__":
    unittest.main()
