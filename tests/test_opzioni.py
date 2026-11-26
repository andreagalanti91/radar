"""Opzioni su BTC "sulla carta" con i segnali di W3.2 (radar/opzioni.py). I 6 test dell'utente (research/opzioni_import/test_opzioni.py)
sulla catena vera di OKX del 24/11/2026, più: errore di rete di OKX (la sezione degrada, il giro e W3.2 restano intatti), tetto della
quota, archivio giornaliero, registro iniziale con il capitale vero, pagina e menu della dashboard. Niente rete."""
import copy
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from radar import opzioni as O

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[1]
CATENA = ROOT / "data" / "opzioni" / "catena_2026-11-24.csv.gz"
CAT = O.carica_catena(str(CATENA))
ORA = datetime(2026, 11, 24, 17, 40, tzinfo=UTC)
W3 = {"status": "aperto", "side": "short", "signal_date": "2026-11-22", "entry": "2026-11-24", "entry_px": 61271.0, "price": 60144.0, "capital": 45000.0}


class TestOpzioniUtente(unittest.TestCase):
    """I 6 test dell'utente, invariati nei numeri (capitale d'esempio 45.000 $)."""

    def test_scelta_del_contratto(self):
        c = O.scegli(CAT, "short", 60144.0, ORA)
        self.assertEqual(c["id"], "BTC-USD_UM-261225-60000-P")       # put, venerdì più vicino a 30 giorni, strike più vicino al prezzo
        self.assertEqual(O.scegli(CAT, "long", 60144.0, ORA)["id"], "BTC-USD_UM-261225-60000-C")
        self.assertIsNone(O.scegli([], "long", 60144.0, ORA))

    def test_quantita_e_perdita_massima(self):
        c = O.scegli(CAT, "short", 60144.0, ORA)
        d = O.dimensiona(c, 45000.0)
        self.assertEqual(d["contratti"], 66)
        self.assertLess(abs(d["spesa"] - 2236), 2)                    # 5% di 45.000 $ = 2.250 $: mai sopra il budget
        self.assertLessEqual(d["spesa"], 45000.0 * O.QUOTA)
        self.assertEqual(d["perdita_massima"], d["spesa"])
        s = {x["mossa_pct"]: x for x in O.scenari(c, d, 45000.0)}
        self.assertLess(s[0]["risultato"], 0)
        self.assertEqual(s[10]["risultato"], -round(d["spesa"]))     # BTC sale: si perde solo il premio
        self.assertGreater(s[-20]["risultato"], 0)

    def test_registro_ingresso_recente_e_tardivo(self):
        reg = O.aggiorna_registro([], W3, CAT, ORA)
        self.assertEqual((reg[0]["stato"], reg[0]["prezzo_in"], reg[0]["contratti"]), ("aperta", 3370.0, 66))   # comprata alla lettera
        self.assertEqual(O.aggiorna_registro(reg, W3, CAT, ORA), reg)                                            # idempotente
        vecchio = W3 | {"signal_date": "2026-11-08", "entry": "2026-11-09"}
        self.assertEqual(O.aggiorna_registro([], vecchio, CAT, ORA)[0]["stato"], "non registrata")              # niente prezzi inventati

    def test_registro_uscita_di_w32_vende_al_denaro(self):
        reg = O.aggiorna_registro([], W3, CAT, ORA)
        reg = O.aggiorna_registro(reg, {"status": "nessuno", "price": 60144.0, "capital": 45000.0}, CAT, ORA + timedelta(days=7))
        r = reg[0]
        self.assertEqual((r["stato"], r["prezzo_out"]), ("venduta", 3340.0))
        self.assertLess(r["risultato"], 0)                             # denaro < lettera: stesso giorno = piccola perdita

    def test_registro_scadenza_e_nessun_rinnovo(self):
        reg = O.aggiorna_registro([], W3, CAT, ORA)
        dopo = datetime(2026, 12, 25, 9, 0, tzinfo=UTC)
        reg = O.aggiorna_registro(reg, W3 | {"price": 52000.0}, CAT, dopo, regolamento=lambda iso: 52000.0)
        r = reg[0]
        self.assertEqual(r["stato"], "scaduta")
        self.assertLess(abs(r["incasso"] - 0.66 * (8000 - 0.0002 * 52000)), 1)
        self.assertEqual(len(reg), 1)
        self.assertEqual(O.build(W3 | {"price": 52000.0}, CAT, reg, dopo)["azione"], "fuori")   # W3.2 ancora aperta: non si rinnova

    def test_build_stati(self):
        self.assertEqual(O.build({"status": "nessuno", "price": 60144.0, "capital": 45000.0}, CAT, [], ORA)["azione"], "attesa")
        seg = O.build({"status": "segnale", "side": "long", "signal_date": "2026-11-22", "price": 60144.0, "capital": 45000.0}, CAT, [], ORA)
        self.assertEqual((seg["azione"], seg["proposta"]["contratto"]["tipo"]), ("compra", "call"))
        reg = O.aggiorna_registro([], W3, CAT, ORA)
        self.assertEqual(O.build(W3, CAT, reg, ORA)["azione"], "tieni")
        self.assertEqual(O.build(W3 | {"status": "uscita"}, CAT, reg, ORA)["azione"], "vendi")


def _get_da(catena):
    """Finta API OKX che restituisce la catena salvata nelle tre forme di scarica_catena."""
    def get(path):
        if path.startswith("public/instruments"):
            return [{"instId": c["id"], "optType": c["tipo"], "stk": str(c["strike"]), "ctType": c["famiglia"],
                     "expTime": str(int(datetime.fromisoformat(c["scadenza"]).timestamp() * 1000))} for c in catena]
        if path.startswith("market/tickers"):
            return [{"instId": c["id"], "bidPx": c["denaro"] or "", "askPx": c["lettera"] or "", "last": c["ultimo"] or ""} for c in catena]
        if path.startswith("public/opt-summary"):
            return [{"instId": c["id"], "markVol": c["vol"], "delta": c["delta"], "fwdPx": c["termine"]} for c in catena]
        if path.startswith("public/delivery-exercise-history"):
            return []
        raise AssertionError(path)
    return get


def _rete_giu(path):
    raise ConnectionError("OKX non raggiungibile")


W3_OGGI = {"status": "aperto", "side": "short", "signal_date": "2026-11-15", "entry": "2026-11-16", "entry_px": 65285.7, "price": 60144.0, "capital": 30000.0}


class TestGiro(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "opzioni").mkdir()
        (self.d / "opzioni_carta.json").write_text((ROOT / "data" / "opzioni_carta.json").read_text())

    def test_errore_di_rete_degrada_e_non_tocca_registro_ne_w32(self):
        prima = (self.d / "opzioni_carta.json").read_bytes()
        w3 = copy.deepcopy(W3_OGGI)
        # nessuna catena salvata: la sezione resta in piedi senza prezzi
        out = O.giro(w3, self.d, ORA, get=_rete_giu, quota=0.05)
        self.assertEqual(out["azione"], "tieni")
        self.assertTrue(out["dati"]["ritardo"])
        self.assertIn("OKX non raggiungibile", out["dati"]["nota"])
        self.assertIsNone(out["posizione"]["prezzo_ora"])
        self.assertEqual((self.d / "opzioni_carta.json").read_bytes(), prima)          # registro intatto
        self.assertEqual(w3, W3_OGGI)                                                   # W3.2 non modificato
        # con un'ultima catena archiviata: ultimo dato, con l'avviso
        (self.d / "opzioni" / CATENA.name).write_bytes(CATENA.read_bytes())
        out = O.giro(w3, self.d, ORA + timedelta(hours=1), get=_rete_giu, quota=0.05)
        self.assertEqual(out["dati"]["aggiornati"], "2026-11-24")
        self.assertEqual(out["posizione"]["prezzo_ora"], 5700.0)
        # segnale nuovo con OKX giù: nessuna riga "non registrata" scritta per sempre
        nuovo = {"status": "aperto", "side": "long", "signal_date": "2026-11-22", "entry": "2026-11-24", "entry_px": 61000.0, "price": 60144.0, "capital": 30000.0}
        O.giro(nuovo, self.d, ORA, get=_rete_giu, quota=0.05)
        self.assertEqual((self.d / "opzioni_carta.json").read_bytes(), prima)

    def test_errore_di_okx_non_ferma_il_giro(self):
        # aggancio in radar/cli.py: _soft registra l'errore e il report prosegue senza la chiave (nessuna eccezione)
        from radar.cli import _soft
        with mock.patch.object(O, "build", side_effect=RuntimeError("guasto")):
            self.assertIsNone(_soft("opzioni su carta", lambda: O.giro(W3_OGGI, self.d, ORA, get=_rete_giu)))
        src = (ROOT / "radar" / "cli.py").read_text()
        self.assertIn('report["opzioni"] = _soft("opzioni su carta", lambda: mod("opzioni").giro(wcur, DATA_DIR)) if wcur else None', src)
        self.assertLess(src.index("wcur = weekly.evaluate(f)"), src.index('report["opzioni"]'))   # dopo W3.2 e i suoi avvisi

    def test_api_okx_con_errore_solleva(self):
        # risposta OKX con codice d'errore: eccezione (non una catena vuota che farebbe nascere righe "non registrate")
        resp = mock.Mock(); resp.json.return_value = {"code": "50011", "msg": "Too Many Requests", "data": []}
        with mock.patch("radar.data._get", return_value=resp):
            with self.assertRaises(RuntimeError):
                O._get("public/opt-summary?uly=BTC-USD")

    def test_giro_con_okx_ok_archivia_e_registra(self):
        out = O.giro(W3_OGGI, self.d, ORA, get=_get_da(CAT), quota=0.05)
        self.assertEqual(out["azione"], "tieni")
        self.assertFalse(out["dati"]["ritardo"])
        p = out["posizione"]
        self.assertEqual((p["id"], p["contratti"], p["spesa"], p["prezzo_ora"]), ("BTC-USD_UM-261211-65000-P", 53, 1480.94, 5700.0))
        self.assertEqual(len(out["storico"]), 23)
        arch = self.d / "opzioni" / "catena_2026-11-24.csv.gz"
        self.assertTrue(arch.exists())
        a = O.carica_catena(str(arch))
        self.assertTrue(0 < len(a) < len(CAT))                                              # solo ±20% e ≥ 7 giorni
        self.assertTrue(all(abs(c["strike"] / 60000 - 1) <= 0.21 for c in a))
        self.assertTrue(all((datetime.fromisoformat(c["scadenza"]) - ORA).days >= 7 for c in a))
        self.assertEqual(O.scegli(a, "short", 60144.0, ORA)["id"], "BTC-USD_UM-261225-60000-P")   # l'archivio si rilegge
        m = arch.stat().st_mtime
        O.giro(W3_OGGI, self.d, ORA + timedelta(hours=1), get=_get_da(CAT), quota=0.05)
        self.assertEqual(arch.stat().st_mtime, m)                                            # una volta al giorno

    def test_registro_scritto_solo_se_cambia(self):
        f = self.d / "opzioni_carta.json"
        self.assertFalse(O.salva_registro(f, json.loads(f.read_text())))
        self.assertTrue(O.salva_registro(f, []))

    def test_prezzo_indicativo_dal_contratto_inverso(self):
        reg = json.loads((self.d / "opzioni_carta.json").read_text())
        senza = [c | {"denaro": None} if c["id"] == "BTC-USD_UM-261211-65000-P" else c for c in CAT]
        p = O.build(W3_OGGI, senza, reg, ORA)["posizione"]
        self.assertTrue(p["prezzo_indicativo"])
        self.assertAlmostEqual(p["prezzo_ora"], 0.095 * 60050.72048733233, places=2)

    def test_scadenza_attende_il_regolamento_okx(self):
        dopo = datetime(2026, 12, 11, 9, 0, tzinfo=UTC)
        O.giro(W3_OGGI, self.d, dopo, get=_get_da(CAT), quota=0.05)                           # regolamento non pubblicato: si aspetta
        self.assertEqual(json.loads((self.d / "opzioni_carta.json").read_text())[0]["stato"], "aperta")
        ts = str(int(datetime(2026, 12, 11, 8, tzinfo=UTC).timestamp() * 1000))
        base = _get_da(CAT)
        get = lambda p: [{"ts": ts, "details": [{"insId": "x", "px": "58000"}]}] if "delivery" in p else base(p)
        out = O.giro(W3_OGGI, self.d, dopo, get=get, quota=0.05)
        r = json.loads((self.d / "opzioni_carta.json").read_text())[0]
        self.assertEqual((r["stato"], r["prezzo_btc_out"]), ("scaduta", 58000.0))
        self.assertAlmostEqual(r["incasso"], 0.53 * (7000 - 0.0002 * 58000), places=1)
        self.assertEqual(out["azione"], "fuori")                                                # non si rinnova


class TestQuotaECapitale(unittest.TestCase):
    def test_tetto_della_quota(self):
        for v, q in (("", 0.05), ("0.05", 0.05), ("0.0667", 0.0667), ("0.10", 0.10), ("0.25", 0.10), ("5", 0.10),
                     ("-0.1", 0.05), ("0", 0.05), ("abc", 0.05), ("nan", 0.05)):
            with mock.patch.dict(os.environ, {"RADAR_OPZIONI_QUOTA": v}):
                self.assertEqual(O.quota_env(), q, v)
        c = O.scegli(CAT, "short", 60144.0, ORA)
        self.assertLessEqual(O.dimensiona(c, 30000.0, O.QUOTA)["spesa"], 1500)
        with mock.patch.dict(os.environ, {"RADAR_OPZIONI_QUOTA": "0.5"}):
            self.assertLessEqual(O.dimensiona(c, 30000.0, O.quota_env())["spesa"], 3000)      # mai oltre il 10% di 30.000 $

    def test_capitale_vero_di_w32(self):
        from radar import weekly
        self.assertEqual(weekly.asset_capital("BTC", 30000.0, 1.0), 30000.0)
        reg = json.loads((ROOT / "data" / "opzioni_carta.json").read_text())
        self.assertEqual(len(reg), 1)
        r = reg[0]
        self.assertEqual((r["chiave"], r["id"], r["capitale"], r["quota"], r["contratti"], r["spesa"]),
                         ("2026-11-15|short", "BTC-USD_UM-261211-65000-P", 30000.0, 0.05, 53, 1480.94))
        self.assertIn("ricostruita", r["nota"])
        self.assertLessEqual(r["spesa"], 1500)
        c = O.scegli(CAT, "long", 60144.0, ORA)
        self.assertEqual(O.dimensiona(c, 30000.0, 0.05)["contratti"], 42)

    def test_workflow(self):
        s = (ROOT / ".github" / "workflows" / "daily.yml").read_text()
        self.assertIn("RADAR_OPZIONI_QUOTA: ${{ vars.RADAR_OPZIONI_QUOTA || '0.05' }}", s)
        self.assertIn("git add data/", s)                                                   # registro e archivio salvati con il resto
        ign = (ROOT / ".gitignore").read_text()
        self.assertNotIn("opzioni", ign)


class TestPagina(unittest.TestCase):
    T = (ROOT / "radar" / "dashboard_template.html").read_text()

    def test_pagina_e_riga_in_oggi(self):
        T = self.T
        self.assertIn('<div class="view" id="v-opzioni" hidden>', T)
        self.assertIn("Operatività sulla carta: nessun ordine viene inviato.", T)
        self.assertIn('<details class="opMore"><summary>Storico dal 2018 con i prezzi veri', T)   # chiuso di default
        self.assertIn("non rende più di W3.2", T)
        self.assertIn("si può perdere tutto il premio", T)
        for a in ("COMPRA", "TIENI", "VENDI", "FUORI", "ATTESA"):
            self.assertIn(f'"{a}"', T)
        i = T.index('<div class="view" id="v-oggi">')
        oggi = T[i:T.index('<div class="view"', i + 10)]
        self.assertLess(oggi.index('id="ogPos"'), oggi.index('id="opLine" href="#opzioni"'))   # variante B: sotto le tessere delle posizioni
        self.assertNotIn('id="opBody"', oggi)

    def test_render(self):
        from radar.dashboard import render
        reg = json.loads((ROOT / "data" / "opzioni_carta.json").read_text())
        op = O.build(W3_OGGI, CAT, reg, ORA, storico=O.carica_storico())
        html = render({"date": "2026-11-24", "price": 60144.0, "opzioni": op}, Path(tempfile.mkdtemp()) / "index.html", standalone=False).read_text()
        self.assertIn('"azione": "tieni"', html)
        self.assertIn("BTC-USD_UM-261211-65000-P", html)


if __name__ == "__main__":
    unittest.main()
