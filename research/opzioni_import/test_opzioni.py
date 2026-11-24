"""Test del modulo opzioni.py sulla catena vera di OKX del 24/11/2026 (catena_2026-11-24.csv.gz)."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import opzioni as O

UTC = timezone.utc
QUI = Path(__file__).parent
CAT = O.carica_catena(str(QUI / "catena_2026-11-24.csv.gz"))
ORA = datetime(2026, 11, 24, 17, 40, tzinfo=UTC)
W3 = {"status": "aperto", "side": "short", "signal_date": "2026-11-22", "entry": "2026-11-24", "entry_px": 61271.0, "price": 60144.0, "capital": 45000.0}


def test_scelta_del_contratto():
    c = O.scegli(CAT, "short", 60144.0, ORA)
    assert c["id"] == "BTC-USD_UM-261225-60000-P"            # put, venerdi' piu' vicino a 30 giorni, strike piu' vicino al prezzo
    assert O.scegli(CAT, "long", 60144.0, ORA)["id"] == "BTC-USD_UM-261225-60000-C"
    assert O.scegli([], "long", 60144.0, ORA) is None


def test_quantita_e_perdita_massima():
    c = O.scegli(CAT, "short", 60144.0, ORA)
    d = O.dimensiona(c, 45000.0)
    assert d["contratti"] == 66 and abs(d["spesa"] - 2236) < 2  # 5% di 45.000 $ = 2.250 $: mai sopra il budget
    assert d["spesa"] <= 45000.0 * O.QUOTA and d["perdita_massima"] == d["spesa"]
    s = {x["mossa_pct"]: x for x in O.scenari(c, d, 45000.0)}
    assert s[0]["risultato"] < 0 and s[10]["risultato"] == -round(d["spesa"])   # BTC sale: si perde solo il premio
    assert s[-20]["risultato"] > 0


def test_registro_ingresso_recente_e_tardivo():
    reg = O.aggiorna_registro([], W3, CAT, ORA)
    assert reg[0]["stato"] == "aperta" and reg[0]["prezzo_in"] == 3370.0 and reg[0]["contratti"] == 66   # comprata alla lettera
    assert O.aggiorna_registro(reg, W3, CAT, ORA) == reg                                                 # idempotente
    vecchio = W3 | {"signal_date": "2026-11-08", "entry": "2026-11-09"}
    assert O.aggiorna_registro([], vecchio, CAT, ORA)[0]["stato"] == "non registrata"                     # niente prezzi inventati


def test_registro_uscita_di_w32_vende_al_denaro():
    reg = O.aggiorna_registro([], W3, CAT, ORA)
    reg = O.aggiorna_registro(reg, {"status": "nessuno", "price": 60144.0, "capital": 45000.0}, CAT, ORA + timedelta(days=7))
    r = reg[0]
    assert r["stato"] == "venduta" and r["prezzo_out"] == 3340.0 and r["risultato"] < 0    # denaro < lettera: stesso giorno = piccola perdita


def test_registro_scadenza_e_nessun_rinnovo():
    reg = O.aggiorna_registro([], W3, CAT, ORA)
    dopo = datetime(2026, 12, 25, 9, 0, tzinfo=UTC)
    reg = O.aggiorna_registro(reg, W3 | {"price": 52000.0}, CAT, dopo, regolamento=lambda iso: 52000.0)
    r = reg[0]
    assert r["stato"] == "scaduta" and abs(r["incasso"] - 0.66 * (8000 - 0.0002 * 52000)) < 1 and len(reg) == 1
    b = O.build(W3 | {"price": 52000.0}, CAT, reg, dopo)
    assert b["azione"] == "fuori"                                                          # W3.2 ancora aperta: non si rinnova


def test_build_stati():
    assert O.build({"status": "nessuno", "price": 60144.0, "capital": 45000.0}, CAT, [], ORA)["azione"] == "attesa"
    seg = O.build({"status": "segnale", "side": "long", "signal_date": "2026-11-22", "price": 60144.0, "capital": 45000.0}, CAT, [], ORA)
    assert seg["azione"] == "compra" and seg["proposta"]["contratto"]["tipo"] == "call"
    reg = O.aggiorna_registro([], W3, CAT, ORA)
    assert O.build(W3, CAT, reg, ORA)["azione"] == "tieni"
    assert O.build(W3 | {"status": "uscita"}, CAT, reg, ORA)["azione"] == "vendi"
