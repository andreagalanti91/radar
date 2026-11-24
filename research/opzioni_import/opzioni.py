"""Opzioni su BTC con i segnali di W3.2: scelta del contratto, quantita', registro "sulla carta" e sezione per la dashboard.

Modulo autonomo (solo libreria standard), pensato per essere copiato in radar/ (per esempio radar/opzioni.py).

Regole della strategia (identiche allo studio OPZIONI_W32.md, non vanno ottimizzate):
1. segnale = quello di W3.2, senza modifiche;
2. long -> si compra una call; short -> si compra una put;
3. scadenza = il venerdi' piu' vicino a 30 giorni fra quelli quotati (fra GG_MIN e GG_MAX);
4. prezzo d'esercizio = il piu' vicino al prezzo di BTC;
5. spesa = QUOTA del capitale di W3.2 (premio + commissioni); il resto resta fermo;
6. uscita = quando W3.2 esce si vende l'opzione; se scade prima si incassa il valore e si resta fuori fino al prossimo segnale;
7. mai rinnovare l'opzione scaduta, mai aumentare la quota dopo una perdita, mai vendere opzioni.

Il modulo NON invia ordini e non usa chiavi: legge solo i prezzi pubblici di OKX e tiene un registro "sulla carta".

Ingressi:
- w3: il dizionario di radar.weekly.evaluate() (servono: status, side, signal_date, entry, entry_px, price, capital);
- catena: lista di contratti come la restituisce scarica_catena() (o carica_catena() da un file salvato);
- registro: lista delle operazioni su carta (file JSON, per esempio data/opzioni_carta.json).
Uscita di build(): dizionario pronto per la dashboard (stesso schema di esempio_sezione.json in questa cartella).
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import urllib.request
from datetime import datetime, timedelta, timezone

QUOTA = 0.05                    # quota del capitale di W3.2 spesa in premio a ogni segnale
GG_OBIETTIVO, GG_MIN, GG_MAX = 30, 20, 50
CONTRATTO_BTC = 0.01            # un contratto OKX = 0,01 BTC
FEE, FEE_CAP, FEE_ESERCIZIO = 0.0003, 0.07, 0.0002      # listino OKX SEE: 0,03% del controvalore, tetto 7% del premio; esercizio 0,02%
FAMIGLIA = "linear"             # opzioni lineari (premio e incasso in dollari): le sole offerte da OKX nel SEE
OKX = "https://www.okx.com/api/v5/"
UTC = timezone.utc


# ------------------------------------------------------------------ prezzi
def _get(path: str) -> list:
    with urllib.request.urlopen(urllib.request.Request(OKX + path, headers={"User-Agent": "radar"}), timeout=30) as r:
        d = json.load(r)
    return d.get("data", []) if d.get("code") == "0" else []


def _f(x) -> float | None:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def scarica_catena(get=_get) -> list[dict]:
    """Catena completa delle opzioni su BTC di OKX (lineari e inverse). Tre chiamate pubbliche, nessuna chiave."""
    inst = {x["instId"]: x for x in get("public/instruments?instType=OPTION&uly=BTC-USD")}
    tick = {x["instId"]: x for x in get("market/tickers?instType=OPTION&uly=BTC-USD")}
    summ = {x["instId"]: x for x in get("public/opt-summary?uly=BTC-USD")}
    out = []
    for i, x in inst.items():
        t, s = tick.get(i, {}), summ.get(i, {})
        out.append({"id": i, "tipo": x["optType"], "strike": _f(x["stk"]), "famiglia": x.get("ctType", ""),
                    "scadenza": datetime.fromtimestamp(int(x["expTime"]) / 1000, UTC).isoformat(),
                    "denaro": _f(t.get("bidPx")), "lettera": _f(t.get("askPx")), "ultimo": _f(t.get("last")),
                    "vol": _f(s.get("markVol")), "delta": _f(s.get("delta")), "termine": _f(s.get("fwdPx"))})
    return out


def carica_catena(path: str) -> list[dict]:
    """Legge una catena salvata: il CSV di backtest/fetch_okx_options.py (colonne OKX) oppure un JSON di scarica_catena()."""
    if path.endswith(".json"):
        return json.load(open(path))
    op = gzip.open if path.endswith(".gz") else open
    out = []
    with op(path, "rt") as fh:
        for x in csv.DictReader(fh):
            out.append({"id": x["instId"], "tipo": x["optType"], "strike": _f(x["stk"]), "famiglia": x.get("ctType", ""),
                        "scadenza": x["scadenza"].replace(" ", "T") + "+00:00", "denaro": _f(x.get("bidPx")), "lettera": _f(x.get("askPx")),
                        "ultimo": _f(x.get("last")), "vol": _f(x.get("markVol")), "delta": _f(x.get("delta")), "termine": _f(x.get("fwdPx"))})
    return out


def _usd(c: dict, campo: str) -> float | None:
    """Prezzo in dollari per 1 BTC di sottostante: le lineari quotano gia' in dollari, le inverse in BTC."""
    v = c.get(campo)
    if v is None or v <= 0:
        return None
    return v if c["famiglia"] == "linear" else v * (c.get("termine") or 0)


def _exp(c: dict) -> datetime:
    return datetime.fromisoformat(c["scadenza"])


def black(F: float, K: float, tau: float, vol: float, cp: int) -> float:
    """Formula di Black sul prezzo a termine, senza sconto. cp = +1 call, -1 put. Serve solo come controllo e per i contratti senza quotazione."""
    if tau <= 0 or vol <= 0:
        return max(0.0, cp * (F - K))
    v = vol * math.sqrt(tau)
    d1 = (math.log(F / K) + 0.5 * v * v) / v
    N = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
    call = F * N(d1) - K * N(d1 - v)
    return call if cp > 0 else call - F + K


# ------------------------------------------------------------------ scelta e quantita'
def scegli(catena: list[dict], verso: str, prezzo: float, adesso: datetime, famiglia: str = FAMIGLIA) -> dict | None:
    """Il contratto della regola: call (long) o put (short), scadenza piu' vicina a 30 giorni fra GG_MIN e GG_MAX,
    prezzo d'esercizio piu' vicino al prezzo, con denaro e lettera presenti. None se non c'e' nulla di quotato."""
    tipo = "C" if verso == "long" else "P"
    ok = [c for c in catena if c["tipo"] == tipo and c["famiglia"] == famiglia and c["strike"] and _usd(c, "denaro") and _usd(c, "lettera")
          and GG_MIN <= (_exp(c) - adesso).total_seconds() / 86400 <= GG_MAX]
    if not ok:
        return None
    exp = min({c["scadenza"] for c in ok}, key=lambda e: abs((datetime.fromisoformat(e) - adesso).total_seconds() / 86400 - GG_OBIETTIVO))
    return min((c for c in ok if c["scadenza"] == exp), key=lambda c: abs(c["strike"] / prezzo - 1))


def dimensiona(c: dict, capitale: float, quota: float = QUOTA) -> dict:
    """Quanti contratti comprare con `quota` del capitale, spesa, perdita massima, pareggio a scadenza."""
    cp = 1 if c["tipo"] == "C" else -1
    lettera, denaro, F, K = _usd(c, "lettera"), _usd(c, "denaro"), c.get("termine") or c["strike"], c["strike"]
    fee = min(FEE * F, FEE_CAP * lettera)
    n = int(capitale * quota / ((lettera + fee) * CONTRATTO_BTC))
    btc = n * CONTRATTO_BTC
    spesa = btc * (lettera + fee)
    return {"contratti": n, "btc": round(btc, 2), "controvalore": round(btc * F), "spesa": round(spesa, 2), "quota": quota,
            "costo_contratto": round((lettera + fee) * CONTRATTO_BTC, 2), "commissioni": round(btc * fee, 2),
            "perdita_massima": round(spesa, 2), "perdita_massima_pct": round(spesa / capitale * 100, 2) if capitale else None,
            "pareggio": round(K + cp * (lettera + fee)), "pareggio_pct": round(((K + cp * (lettera + fee)) / F - 1) * 100, 1),
            "differenziale_pct": round((lettera - denaro) / ((lettera + denaro) / 2) * 100, 1)}


def scenari(c: dict, dim: dict, capitale: float, mosse=(-0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30)) -> list[dict]:
    """Guadagno o perdita a scadenza per alcuni movimenti di BTC rispetto al prezzo a termine di oggi."""
    cp, K, F, btc, out = (1 if c["tipo"] == "C" else -1), c["strike"], c.get("termine") or c["strike"], dim["btc"], []
    for m in mosse:
        s = F * (1 + m)
        intr = max(0.0, cp * (s - K))
        val = btc * (intr - min(FEE_ESERCIZIO * s, FEE_CAP * intr))
        out.append({"mossa_pct": round(m * 100), "btc": round(s), "valore": round(val), "risultato": round(val - dim["spesa"]),
                    "sul_capitale_pct": round((val - dim["spesa"]) / capitale * 100, 1) if capitale else None})
    return out


def descrivi(c: dict, adesso: datetime) -> dict:
    """Il contratto in forma leggibile."""
    e = _exp(c)
    return {"id": c["id"], "tipo": "call" if c["tipo"] == "C" else "put", "strike": c["strike"], "scadenza": e.strftime("%Y-%m-%d"),
            "scadenza_ora_utc": e.strftime("%H:%M"), "giorni": round((e - adesso).total_seconds() / 86400, 1), "denaro": _usd(c, "denaro"),
            "lettera": _usd(c, "lettera"), "vol_pct": round(c["vol"] * 100) if c.get("vol") else None, "delta": c.get("delta"),
            "termine": c.get("termine"), "famiglia": c["famiglia"]}


# ------------------------------------------------------------------ registro su carta
def _chiave(w3: dict) -> str | None:
    """Identifica la posizione di W3.2: data del segnale e verso."""
    return f"{w3.get('signal_date')}|{w3.get('side')}" if w3.get("side") and w3.get("signal_date") else None


def _trova(catena: list[dict], ident: str) -> dict | None:
    return next((c for c in catena if c["id"] == ident), None)


def aggiorna_registro(registro: list[dict], w3: dict, catena: list[dict], adesso: datetime, capitale: float | None = None, quota: float = QUOTA,
                      regolamento=None, tardivo_giorni: float = 1.5) -> list[dict]:
    """Porta avanti il registro "sulla carta". Va chiamata a ogni giro; non fa nulla se non c'e' niente da registrare.
    - W3.2 apre una posizione (status "aperto") e nel registro manca: si registra l'acquisto alla LETTERA di adesso, solo se
      l'ingresso e' avvenuto da meno di `tardivo_giorni` (altrimenti la riga nasce come "non registrata": niente prezzi inventati);
    - l'opzione aperta arriva alla scadenza: si chiude al valore intrinseco (prezzo di regolamento da `regolamento(scadenza)`,
      se fornito, altrimenti il prezzo di W3.2) e resta fuori fino al prossimo segnale;
    - W3.2 chiude la posizione e l'opzione e' ancora aperta: si registra la vendita al DENARO di adesso.
    Ritorna il registro aggiornato (lista nuova: quella in ingresso non viene modificata)."""
    reg = [dict(r) for r in registro]
    capitale = float(w3.get("capital") or 0) if capitale is None else capitale
    key = _chiave(w3) if w3.get("status") in ("aperto", "uscita") else None
    aperta = next((r for r in reg if r.get("stato") == "aperta"), None)
    # 1) scadenza
    if aperta and adesso >= datetime.fromisoformat(aperta["scadenza_iso"]):
        s = (regolamento(aperta["scadenza_iso"]) if regolamento else None) or float(w3.get("price") or 0)
        cp = 1 if aperta["tipo"] == "call" else -1
        intr = max(0.0, cp * (s - aperta["strike"]))
        val = aperta["btc"] * (intr - min(FEE_ESERCIZIO * s, FEE_CAP * intr))
        aperta.update(stato="scaduta", chiusa=aperta["scadenza"], prezzo_btc_out=round(s, 2), incasso=round(val, 2),
                      risultato=round(val - aperta["spesa"], 2), risultato_pct=round((val - aperta["spesa"]) / aperta["capitale"] * 100, 2))
        aperta = None
    # 2) W3.2 e' uscita: vendita al denaro
    if aperta and aperta["chiave"] != key:
        c = _trova(catena, aperta["id"])
        den = _usd(c, "denaro") if c else None
        if den is not None:
            val = aperta["btc"] * max(0.0, den - min(FEE * (c.get("termine") or aperta["strike"]), FEE_CAP * den))
            aperta.update(stato="venduta", chiusa=adesso.strftime("%Y-%m-%d"), prezzo_out=round(den, 2), incasso=round(val, 2),
                          prezzo_btc_out=w3.get("price"), risultato=round(val - aperta["spesa"], 2),
                          risultato_pct=round((val - aperta["spesa"]) / aperta["capitale"] * 100, 2))
            aperta = None
    # 3) nuova posizione di W3.2
    if key and not any(r["chiave"] == key for r in reg):
        entra = datetime.fromisoformat(str(w3["entry"])).replace(tzinfo=UTC)
        base = {"chiave": key, "verso": w3["side"], "segnale": w3["signal_date"], "entra": str(w3["entry"]), "prezzo_btc_in": w3.get("entry_px"),
                "capitale": round(capitale, 2), "quota": quota}
        c = scegli(catena, w3["side"], float(w3.get("price") or w3["entry_px"]), adesso)
        if (adesso - entra).total_seconds() / 86400 > tardivo_giorni or c is None or capitale <= 0:
            reg.append(base | {"stato": "non registrata", "nota": "ingresso di W3.2 precedente all'avvio del registro" if c else "nessun contratto quotato"})
        else:
            d = dimensiona(c, capitale, quota)
            reg.append(base | {"stato": "aperta", "id": c["id"], "tipo": "call" if c["tipo"] == "C" else "put", "strike": c["strike"],
                               "scadenza": _exp(c).strftime("%Y-%m-%d"), "scadenza_iso": c["scadenza"], "registrata": adesso.isoformat(timespec="minutes"),
                               "prezzo_in": round(_usd(c, "lettera"), 2), "vol_in_pct": round(c["vol"] * 100) if c.get("vol") else None,
                               "contratti": d["contratti"], "btc": d["btc"], "spesa": d["spesa"]})
    return reg


# ------------------------------------------------------------------ sezione della dashboard
def build(w3: dict, catena: list[dict], registro: list[dict], adesso: datetime | None = None, capitale: float | None = None, quota: float = QUOTA,
          storico: list[dict] | None = None) -> dict:
    """Tutto quello che la sezione "Opzioni" deve mostrare. Non modifica il registro: chiamare prima aggiorna_registro()."""
    adesso = adesso or datetime.now(UTC)
    capitale = float(w3.get("capital") or 0) if capitale is None else capitale
    st, prezzo = w3.get("status", "nessuno"), float(w3.get("price") or 0)
    out = {"aggiornato": adesso.isoformat(timespec="minutes"), "w3": {"stato": st, "verso": w3.get("side"), "segnale": w3.get("signal_date"), "entra": w3.get("entry"),
                                                                    "prezzo_in": w3.get("entry_px"), "prezzo": prezzo},
           "capitale": round(capitale), "quota_pct": round(quota * 100, 1), "budget": round(capitale * quota), "registro": registro, "storico": storico or [],
           "regole": ["Segnale di W3.2, senza modifiche", "Long: call · short: put", "Scadenza: il venerdì più vicino a 30 giorni", "Prezzo d'esercizio: il più vicino al prezzo",
                      f"Spesa: {quota * 100:.0f}% del capitale di W3.2", "Si vende quando W3.2 esce; se scade prima, si resta fuori",
                      "Mai rinnovare, mai aumentare dopo una perdita, mai vendere opzioni"]}
    aperta = next((r for r in registro if r.get("stato") == "aperta"), None)
    key = _chiave(w3) if st in ("aperto", "uscita") else None
    riga = next((r for r in registro if r.get("chiave") == key), None) if key else None

    def proposta(verso: str) -> dict | None:
        c = scegli(catena, verso, prezzo, adesso)
        if c is None or capitale <= 0:
            return None
        d = dimensiona(c, capitale, quota)
        return {"contratto": descrivi(c, adesso), "quantita": d, "scenari": scenari(c, d, capitale)}

    if st == "segnale":
        p = proposta(w3["side"])
        out.update(azione="compra", titolo=f"Segnale {w3['side']}: comprare una {'call' if w3['side'] == 'long' else 'put'} all'apertura di lunedì",
                   testo="Prezzi indicativi di adesso: all'apertura vanno riletti. Ordine limite a metà fra denaro e lettera." if p else
                         "Nessun contratto quotato fra 20 e 50 giorni: controllare a mano sulla piattaforma.", proposta=p)
    elif st in ("aperto", "uscita") and aperta and aperta["chiave"] == key:
        c = _trova(catena, aperta["id"])
        den = _usd(c, "denaro") if c else None
        gg = (datetime.fromisoformat(aperta["scadenza_iso"]) - adesso).total_seconds() / 86400
        val = aperta["btc"] * den if den is not None else None
        pos = aperta | {"giorni": round(gg, 1), "prezzo_ora": den, "valore": round(val, 2) if val is not None else None,
                        "risultato": round(val - aperta["spesa"], 2) if val is not None else None,
                        "risultato_pct": round((val - aperta["spesa"]) / aperta["capitale"] * 100, 2) if val is not None else None,
                        "vol_ora_pct": round(c["vol"] * 100) if c and c.get("vol") else None}
        if st == "uscita":
            out.update(azione="vendi", titolo="W3.2 esce: vendere l'opzione all'apertura di lunedì", testo="Ordine limite a metà fra denaro e lettera.", posizione=pos)
        else:
            out.update(azione="tieni", titolo=f"Opzione aperta: tenere ({gg:.0f} giorni alla scadenza)",
                       testo="Si vende quando W3.2 esce. Se arriva alla scadenza l'incasso è automatico e non si rinnova.", posizione=pos)
    elif st in ("aperto", "uscita") and riga and riga.get("stato") in ("scaduta", "venduta"):
        out.update(azione="fuori", titolo="Opzione di questa operazione già chiusa: restare fuori fino al prossimo segnale",
                   testo="W3.2 è ancora in posizione, ma la regola non prevede di rinnovare l'opzione.", ultima=riga)
    elif st in ("aperto", "uscita"):
        p = proposta(w3["side"]) if st == "aperto" else None
        out.update(azione="fuori", titolo="W3.2 è già in posizione: nessuna opzione registrata per questa operazione",
                   testo="L'opzione si compra all'ingresso di W3.2, non dopo. Sotto, per riferimento, cosa costerebbe oggi.", proposta=p)
    else:
        esempio = {v: proposta(v) for v in ("long", "short")}
        out.update(azione="attesa", titolo="Nessun segnale di W3.2: nessuna opzione da comprare",
                   testo="Sotto, per riferimento, cosa si comprerebbe oggi se arrivasse un segnale.", esempio=esempio)
    return out


if __name__ == "__main__":
    import sys
    cat = carica_catena(sys.argv[1] if len(sys.argv) > 1 else "catena_2026-11-24.csv.gz")
    reg = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else []
    ora = datetime(2026, 11, 24, 17, 40, tzinfo=UTC)
    w3 = {"status": "aperto", "side": "short", "signal_date": "2026-11-15", "entry": "2026-11-16", "entry_px": 65286.0, "price": 60144.0, "capital": 45000.0}
    reg = aggiorna_registro(reg, w3, cat, ora)
    print(json.dumps(build(w3, cat, reg, ora), ensure_ascii=False, indent=1))
