"""Opzioni su BTC con i segnali di W3.2: scelta del contratto, quantita', registro "sulla carta" e sezione per la dashboard.

Modulo dell'utente (research/opzioni_import/opzioni.py) portato in Radar il 24/11/2026 con modifiche minime: rete con le
convenzioni di Radar (radar.data._get), quota da RADAR_OPZIONI_QUOTA (tetto 10%), registro e archivio giornaliero su disco,
prezzo di regolamento da OKX, prezzo indicativo dal contratto inverso, e giro() che lega tutto e degrada senza rompere il giro.

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
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

QUOTA = 0.05                    # quota del capitale di W3.2 spesa in premio a ogni segnale
GG_OBIETTIVO, GG_MIN, GG_MAX = 30, 20, 50
CONTRATTO_BTC = 0.01            # un contratto OKX = 0,01 BTC
FEE, FEE_CAP, FEE_ESERCIZIO = 0.0003, 0.07, 0.0002      # listino OKX SEE: 0,03% del controvalore, tetto 7% del premio; esercizio 0,02%
FAMIGLIA = "linear"             # opzioni lineari (premio e incasso in dollari): le sole offerte da OKX nel SEE
QUOTA_MAX = 0.10               # tetto della quota (PROMPT dell'utente: "mai sopra il 10%")
OKX = "https://www.okx.com/api/v5/"
UTC = timezone.utc
STORICO_FILE = Path(__file__).with_name("opzioni_storico.json")   # le 23 operazioni del backtest con i prezzi veri di Deribit
ARCHIVIO_BANDA, ARCHIVIO_GG_MIN = 0.20, 7                         # archivio: contratti entro ±20% dal prezzo e con almeno 7 giorni


def quota_env(default: float = QUOTA) -> float:
    """Quota del capitale da RADAR_OPZIONI_QUOTA (frazione, es. 0.05 o 0.0667), mai sopra QUOTA_MAX; valore assente o non valido → 5%."""
    try:
        q = float(os.environ.get("RADAR_OPZIONI_QUOTA", "") or default)
    except ValueError:
        return default
    if not math.isfinite(q) or q <= 0:
        return default
    return min(q, QUOTA_MAX)


# ------------------------------------------------------------------ prezzi
def _get(path: str) -> list:
    """API pubblica OKX con la sessione e i tentativi di radar.data (2 tentativi: il giro orario non deve aspettare minuti)."""
    from .data import _get as get_http
    r = get_http(OKX + path, retries=2)
    d = r.json() if r is not None else {}
    if d.get("code") != "0":
        raise RuntimeError(f"OKX {path.split('?')[0]}: risposta {d.get('code')!r} {str(d.get('msg', ''))[:80]}")
    return d.get("data", [])


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


def regolamento_okx(scadenza_iso: str, get=_get) -> float | None:
    """Prezzo di regolamento di OKX alla scadenza (public/delivery-exercise-history): None se non ancora pubblicato."""
    ts = int(datetime.fromisoformat(scadenza_iso).timestamp() * 1000)
    for x in get("public/delivery-exercise-history?instType=OPTION&uly=BTC-USD&limit=100"):
        if abs(int(x.get("ts", 0)) - ts) <= 3_600_000:
            px = next((_f(d.get("px")) for d in x.get("details", []) if _f(d.get("px"))), None)
            if px:
                return px
    return None


def _gemello(catena: list[dict], ident: str) -> dict | None:
    """Il contratto inverso con lo stesso prezzo d'esercizio e scadenza (BTC-USD_UM-… → BTC-USD-…)."""
    return next((c for c in catena if c["id"] == ident.replace("BTC-USD_UM-", "BTC-USD-")), None) if "_UM-" in ident else None


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
                      "Spesa: " + f"{quota * 100:.3g}".replace(".", ",") + "% del capitale di W3.2", "Si vende quando W3.2 esce; se scade prima, si resta fuori",
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
        indicativo = False
        if den is None and _gemello(catena, aperta["id"]):     # lineare senza denaro: prezzo del gemello inverso in dollari
            den = _usd(_gemello(catena, aperta["id"]), "denaro")
            indicativo = den is not None
        gg = (datetime.fromisoformat(aperta["scadenza_iso"]) - adesso).total_seconds() / 86400
        val = aperta["btc"] * den if den is not None else None
        pos = aperta | {"giorni": round(gg, 1), "prezzo_ora": den, "prezzo_indicativo": indicativo, "valore": round(val, 2) if val is not None else None,
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


# ------------------------------------------------------------------ giro orario di Radar (radar/cli.py)
CSV_COLONNE = ["instId", "stk", "optType", "ctType", "last", "bidPx", "askPx", "markVol", "delta", "fwdPx", "scadenza"]


def _riga_csv(c: dict) -> dict:
    v = lambda x: "" if x is None else x
    return {"instId": c["id"], "stk": v(c["strike"]), "optType": c["tipo"], "ctType": c["famiglia"], "last": v(c.get("ultimo")),
            "bidPx": v(c.get("denaro")), "askPx": v(c.get("lettera")), "markVol": v(c.get("vol")), "delta": v(c.get("delta")),
            "fwdPx": v(c.get("termine")), "scadenza": _exp(c).astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")}


def archivia(catena: list[dict], cartella: Path, adesso: datetime, prezzo: float) -> Path | None:
    """Una volta al giorno: data/opzioni/catena_AAAA-MM-GG.csv.gz con i contratti entro ±20% dal prezzo e con almeno 7 giorni
    (lineari e inverse; colonne leggibili da carica_catena). OKX non conserva lo storico dei contratti scaduti."""
    out = Path(cartella) / f"catena_{adesso.strftime('%Y-%m-%d')}.csv.gz"
    if out.exists() or not catena or not prezzo:
        return None
    righe = [c for c in catena if c.get("strike") and abs(c["strike"] / prezzo - 1) <= ARCHIVIO_BANDA
             and (_exp(c) - adesso).total_seconds() / 86400 >= ARCHIVIO_GG_MIN]
    if not righe:
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    with gzip.open(tmp, "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLONNE)
        w.writeheader()
        w.writerows(_riga_csv(c) for c in sorted(righe, key=lambda c: (c["scadenza"], c["strike"], c["id"])))
    tmp.replace(out)
    return out


def ultima_archiviata(cartella: Path) -> tuple[list[dict], str | None]:
    """L'ultima catena salvata (per mostrare l'ultimo dato quando OKX non risponde): (catena, data) oppure ([], None)."""
    files = sorted(Path(cartella).glob("catena_*.csv.gz"))
    for f in reversed(files):
        try:
            return carica_catena(str(f)), f.name[7:17]
        except Exception:  # noqa: BLE001
            continue
    return [], None


def carica_registro(path: Path) -> list[dict]:
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return []


def salva_registro(path: Path, registro: list[dict]) -> bool:
    """Scrive il registro solo se cambia. True se scritto."""
    path = Path(path)
    if path.exists() and carica_registro(path) == registro:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(registro, ensure_ascii=False, indent=1) + "\n")
    tmp.replace(path)
    return True


def carica_storico() -> list[dict]:
    try:
        return json.loads(STORICO_FILE.read_text())
    except Exception:  # noqa: BLE001
        return []


def giro(w3: dict, data_dir: Path, adesso: datetime | None = None, get=_get, quota: float | None = None) -> dict:
    """Un giro orario: catena da OKX (3 chiamate pubbliche), archivio del giorno, registro su carta, sezione per la dashboard.
    Se OKX non risponde il registro NON si tocca (niente acquisti a prezzi vecchi) e la sezione mostra l'ultima catena archiviata
    con l'avviso; senza alcuna catena la sezione resta in piedi (proposte vuote). W3.2 non viene mai modificato: legge solo `w3`."""
    adesso = adesso or datetime.now(UTC)
    quota = quota_env() if quota is None else quota
    data_dir = Path(data_dir)
    reg_file, cartella = data_dir / "opzioni_carta.json", data_dir / "opzioni"
    registro = carica_registro(reg_file)
    dati = {"fonte": "OKX", "aggiornati": adesso.isoformat(timespec="minutes"), "ritardo": False, "nota": None}
    try:
        catena = scarica_catena(get)
        if not any(c["famiglia"] == FAMIGLIA and _usd(c, "lettera") for c in catena):
            raise RuntimeError("catena senza quotazioni")   # altrimenti un ingresso di W3.2 nascerebbe "non registrato" per sempre
    except Exception as e:  # noqa: BLE001
        catena, giorno = ultima_archiviata(cartella)
        dati.update(ritardo=True, aggiornati=giorno, errore=f"{type(e).__name__}: {str(e)[:120]}",
                    nota=(f"OKX non raggiungibile: prezzi dell'ultima catena salvata ({giorno}); registro non aggiornato in questo giro."
                          if giorno else "OKX non raggiungibile e nessuna catena salvata: prezzi non disponibili in questo giro."))
        print(f"[radar] opzioni: catena OKX non scaricata ({e!r}), uso l'ultima salvata: {giorno}")
    else:
        termini = sorted(c["termine"] for c in catena if c.get("termine"))
        prezzo = termini[len(termini) // 2] if termini else float(w3.get("price") or 0)   # prezzo a termine di adesso (mediana)
        try:
            archivia(catena, cartella, adesso, prezzo)
        except Exception as e:  # noqa: BLE001
            print(f"[radar] opzioni: archivio della catena non salvato ({e!r})")

        aperta = next((r for r in registro if r.get("stato") == "aperta"), None)
        scad = datetime.fromisoformat(aperta["scadenza_iso"]) if aperta else None
        s_px = None
        if scad and adesso >= scad:
            try:
                s_px = regolamento_okx(aperta["scadenza_iso"], get)
            except Exception as e:  # noqa: BLE001
                print(f"[radar] opzioni: prezzo di regolamento non letto ({e!r})")
        if scad and adesso >= scad and s_px is None and adesso - scad < timedelta(hours=24):
            print("[radar] opzioni: opzione scaduta, regolamento OKX non ancora pubblicato: registro al prossimo giro")
        else:   # dopo 24 ore senza regolamento vale la regola dell'originale: prezzo di W3.2
            registro = aggiorna_registro(registro, w3, catena, adesso, quota=quota, regolamento=lambda iso: s_px)
            salva_registro(reg_file, registro)
    out = build(w3, catena, registro, adesso, quota=quota, storico=carica_storico())
    out["dati"] = dati
    return out
