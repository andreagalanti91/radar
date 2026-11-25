"""Registro "scommesse" sulla carta (research/w32_asset2/REGISTRO-SCOMMESSE.md, regole fissate il 25/11/2026, da non cambiare).

- Quali ingressi: ogni ingresso NUOVO dello scanner (W3.2 con i parametri di BTC, radar/scanner.py) con segnale dalla domenica
  29/11/2026, su monete operabili su Bitget o OKX, solo se nello stesso verso in cui W3.2 è posizionata su BTC quella domenica
  (cancello di Q4: in posizione o vi entra quel giorno). BTC, ETH e TRX esclusi. Le posizioni aperte prima del 29/11 non entrano.
- Importo: 100 $ fissi a 1x (long a pronti, short sul perp). Ingresso all'apertura del lunedì dopo la domenica del segnale;
  uscita quando W3.2 esce su quella moneta (trailing, EMA 21, distribuzione), all'apertura del giorno indicato dalla regola
  (per stop e trailing il livello dello stop, o l'apertura se peggiore, come radar.weekly.simulate).
- Costi: 0,10% per lato; funding reale sugli short dove disponibile (giorni senza funding dichiarati nella nota).
- Moneta senza dati da oltre 7 giorni (uscita dall'archivio): chiusura all'ultimo prezzo disponibile, con la nota.
- Riferimento "senza filtro di BTC": la stessa regola su tutti gli ingressi nuovi, calcolata a parte (stesse righe, campo btc).

Aggiornamento: le operazioni nuove entrano quando lo scanner calcola la settimana (lunedì dopo la chiusura della domenica); il
valore delle aperte si aggiorna una volta al giorno (giorno chiuso nuovo), scaricando solo i giorni mancanti delle monete aperte
dalla cache dello scanner (poche richieste per moneta). Nessun capitale, nessun ordine, nessun avviso.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import scanner as SC
from . import weekly as W

INIZIO = "2026-11-29"            # prima domenica di segnale che conta
IMPORTO = 100.0
COSTO = 0.001                    # per lato
ESCLUSE = {"BTC", "ETH", "TRX"}
NOTA = "sulla carta: nessun capitale, nessun ordine"
FILE = "scommesse_carta.json"
FERMA_GIORNI = 7
VALUTAZIONI = [("2027-05-31", "6 mesi"), ("2027-11-30", "12 mesi")]
MIN_CHIUSE = 20
RIF_STUDIO = {"stesso": {"fin": 12386, "dd": -39, "in_perdita": 32}, "tutte": {"fin": 10381, "dd": -56, "in_perdita": 49},
              "nota": "78 altcoin dal 06/2020, 10.000 $ per moneta, Q4 contro Q1"}
REGOLE = [
    "Ogni ingresso nuovo dello scanner dalla settimana che chiude domenica 29/11/2026, su monete operabili su Bitget o OKX, solo se "
    "nello stesso verso di W3.2 su BTC quella domenica. Esclusi BTC ed ETH (capitale proprio) e TRX (registro proprio).",
    "100 $ fissi per ingresso, leva 1x (long a pronti, short sul perp), nessun aumento dopo una perdita.",
    "Ingresso all'apertura del lunedì dopo il segnale; uscita quando W3.2 esce su quella moneta, all'apertura del giorno indicato "
    "dalla regola (stop e trailing: livello dello stop).",
    "Costi 0,10% per lato e funding reale sugli short; se il funding manca lo si dichiara. Moneta senza dati: chiusura all'ultimo "
    "prezzo disponibile, con la nota.",
    "Valutazione a 6 e 12 mesi; con meno di 20 operazioni chiuse il registro non basta per giudicare. Passare a soldi veri resta "
    "una decisione dell'utente."]
CAMPI_MONETA = ("ticker", "spot", "spot_okx", "perp", "div", "fonte", "da", "okx", "bitget")


def _vuoto() -> dict:
    return {"inizio": INIZIO, "importo": IMPORTO, "operazioni": [], "dati_fino": None, "aggiornato": None}


# ------------------------------------------------------------------ ammissione
def ammissione(r: dict) -> tuple[bool, bool, str]:
    """(entra nel registro come ingresso nuovo, passa il filtro di BTC, motivo se non entra). `r` = riga dello scanner."""
    if r.get("lato") not in ("long", "short") or not r.get("sig"):
        return False, False, "nessun ingresso"
    if r["sig"] < INIZIO:
        return False, False, "segnale prima del 29/11/2026"
    if r["t"] in ESCLUSE:
        return False, False, "esclusa (capitale o registro proprio)"
    if not (r.get("bg") or r.get("ok")):
        return False, False, "non operabile su Bitget né OKX"
    return True, r.get("g") == r["lato"], ""


def aggiungi(reg: dict, scanner: dict | None, universo: dict[str, dict]) -> int:
    """Righe nuove dal risultato dello scanner (anche di una settimana saltata: chiave moneta|verso|segnale). Ritorna quante."""
    if not scanner or not scanner.get("righe"):
        return 0
    ops = reg.setdefault("operazioni", [])
    viste = {o["k"] for o in ops}
    n = 0
    for r in scanner["righe"]:
        ok, filtro, _ = ammissione(r)
        if not ok:
            continue
        k = f"{r['t']}|{r['lato']}|{r['sig']}"
        if k in viste:
            continue
        c = universo.get(r["t"]) or {}
        ops.append({"k": k, "t": r["t"], "v": r["lato"], "sig": r["sig"],
                    "ing": str(date.fromisoformat(r["sig"]) + timedelta(days=1)),
                    "btc": "stesso" if filtro else (r.get("g") or "flat"), "filtro": filtro, "stato": "attesa",
                    "c": {k2: c.get(k2) for k2 in CAMPI_MONETA if c.get(k2) is not None} or None})
        viste.add(k)
        n += 1
    return n


# ------------------------------------------------------------------ valutazione di un'operazione
def _px_uscita(f: pd.DataFrame, t: dict) -> float:
    sg, o = (1 if t["side"] == "long" else -1), float(f.loc[pd.Timestamp(t["exit"]), "open"])
    if t.get("reason") in ("stop", "trail"):
        o = min(o, t["stop"]) if sg > 0 else max(o, t["stop"])
    return o


def risultato(v: str, px_in: float, px_out: float, f: pd.DataFrame | None, ing: str, fine: str | None) -> dict:
    """100 $ a 1x: rendimento lordo, 0,10% per lato (sul valore in entrata e in uscita), funding sugli short (incassato se
    positivo) sui giorni da ingresso a uscita esclusa, sul valore del giorno prima. Restituisce $ e % e i giorni senza funding."""
    sg = 1 if v == "long" else -1
    rel = px_out / px_in
    lordo = sg * (rel - 1)
    costi = COSTO * (1 + rel)
    fund, nd = 0.0, 0
    if v == "short" and f is not None and len(f):
        a, b = pd.Timestamp(ing), pd.Timestamp(fine) if fine else f.index[-1] + pd.Timedelta(days=1)
        g = f[(f.index >= a) & (f.index < b)]
        if len(g):
            val = (f["close"].shift(1).reindex(g.index).fillna(px_in) / px_in).values
            fu = g["funding"].values if "funding" in g else np.full(len(g), np.nan)
            nd = int(np.isnan(fu).sum())
            fund = float(np.nansum(fu * val))
    r = lordo - costi + fund
    return {"pnl_usd": round(IMPORTO * r, 2), "pnl_pct": round(r * 100, 2), "costi_usd": round(IMPORTO * costi, 2),
            "funding_usd": round(IMPORTO * fund, 2), "funding_nd": nd}


def valuta(o: dict, f: pd.DataFrame | None, oggi: date) -> dict:
    """Aggiorna un'operazione non chiusa con le feature giornaliere della moneta (radar.scanner.feats)."""
    o = dict(o)
    if f is None or not len(f):
        o["nota"] = "dati della moneta non disponibili in questo giro"
        return o
    ing = pd.Timestamp(o["ing"])
    if o.get("px_in") is None:
        if ing not in f.index:
            o["stato"] = "attesa"
            if f.index[-1] >= ing:          # dati oltre il lunedì ma senza quel giorno: improbabile, lo si dice
                o["nota"] = "apertura del lunedì non trovata nei dati"
            return o
        o["px_in"] = SC._r(float(f.loc[ing, "open"]), 8)
        o["stato"] = "aperta"
    px_in = float(o["px_in"])
    # W3.2 sulla moneta, come lo scanner: la stessa operazione (verso e segnale) chiusa o ancora aperta
    w = W.weekly_bars(f)
    okw = w[w["sma"].notna() & w["flow"].notna()]
    tr = None
    if len(okw):
        with np.errstate(divide="ignore", invalid="ignore"):
            sim = W.simulate(f, start=str((okw.index[0] + pd.Timedelta(days=1)).date()))
        tr = next((t for t in SC._trades(sim) if t["side"] == o["v"] and t["signal"] == o["sig"]), None)
    last = f.index[-1]
    if tr is not None and tr.get("exit"):
        px_out = _px_uscita(f, tr)
        o.update(stato="chiusa", usc=tr["exit"], px_out=SC._r(px_out, 8), motivo=W.REASONS.get(tr["reason"], tr["reason"]))
        o.pop("ult", None)
        o.update(risultato(o["v"], px_in, px_out, f, o["ing"], tr["exit"]))
    elif pd.Timestamp(oggi) - last > pd.Timedelta(days=FERMA_GIORNI):
        px_out = float(f["close"].iloc[-1])
        o.update(stato="chiusa", usc=str((last + pd.Timedelta(days=1)).date()), px_out=SC._r(px_out, 8),
                 motivo="dati fermi", nota=f"dati della moneta fermi al {last.date():%d/%m/%Y}: chiusa all'ultimo prezzo disponibile")
        o.pop("ult", None)
        o.update(risultato(o["v"], px_in, px_out, f, o["ing"], o["usc"]))
    else:
        ult = float(f["close"].iloc[-1])
        o.update(stato="aperta", ult=SC._r(ult, 8), motivo="posizione aperta")
        if tr is None:
            o["nota"] = f"W3.2 non mostra più questa operazione nel calcolo del {oggi:%d/%m/%Y} (dati riscritti): da controllare"
        else:
            o.pop("nota", None)
            o["trail"] = SC._r(tr.get("trail"), 8)
        o.update(risultato(o["v"], px_in, ult, f, o["ing"], None))
    if o.get("funding_nd") and o["v"] == "short":
        o["nota_funding"] = f"funding mancante per {o['funding_nd']} giorni (non conteggiato)"
    return o


# ------------------------------------------------------------------ riepilogo
def riepilogo(ops: list[dict]) -> dict:
    vive = [o for o in ops if o.get("stato") in ("aperta", "chiusa")]
    ch = [o for o in vive if o["stato"] == "chiusa"]
    tot = round(sum(o.get("pnl_usd") or 0 for o in vive), 2)
    inv = IMPORTO * len(vive)
    peg = min(vive, key=lambda o: o.get("pnl_usd") or 0) if vive else None
    return {"n": len(ops), "investito": inv, "risultato_usd": tot, "risultato_pct": round(tot / inv * 100, 2) if inv else None,
            "aperte": sum(o["stato"] == "aperta" for o in vive), "chiuse": len(ch), "attesa": sum(o.get("stato") == "attesa" for o in ops),
            "in_guadagno_pct": round(sum((o.get("pnl_usd") or 0) > 0 for o in ch) / len(ch) * 100) if ch else None,
            "peggiore": ({"t": peg["t"], "usd": peg.get("pnl_usd"), "pct": peg.get("pnl_pct")} if peg and (peg.get("pnl_usd") or 0) < 0 else None)}


def build(reg: dict, now: datetime, dati: dict | None = None) -> dict:
    oggi = pd.Timestamp(now).date()
    ops = reg.get("operazioni", [])
    return {"nota": NOTA, "inizio": reg.get("inizio", INIZIO), "importo": IMPORTO, "operazioni": [o for o in ops if o.get("filtro")],
            "filtro": riepilogo([o for o in ops if o.get("filtro")]), "senza_filtro": riepilogo(ops),
            "min_chiuse": MIN_CHIUSE, "rif_studio": RIF_STUDIO, "regole": REGOLE, "dati_fino": reg.get("dati_fino"),
            "aggiornato": reg.get("aggiornato"),
            "valutazioni": [{"data": d, "cosa": k, "giorni": (date.fromisoformat(d) - oggi).days} for d, k in VALUTAZIONI],
            "dati": dati or {"ritardo": False, "nota": None}}


# ------------------------------------------------------------------ giro
def _universo(cache: Path) -> dict[str, dict]:
    try:
        return {m["ticker"]: m for m in SC.universo_precedente(cache)["monete"]}
    except Exception:  # noqa: BLE001
        return {}


def giro(scanner: dict | None, data_dir: Path, now: datetime | None = None, net: SC.Rete | None = None,
         cache: Path = SC.CACHE_DIR, seed_dir: Path | None = SC.SEED_DIR, universo: dict[str, dict] | None = None) -> dict:
    """Un giro orario: aggiunge gli ingressi nuovi della settimana calcolata dallo scanner e, a giorno chiuso nuovo, rivaluta le
    operazioni non chiuse. Senza operazioni aperte non fa richieste. Errori di rete: ultimo registro con l'avviso."""
    now = now or datetime.now(timezone.utc)
    data_dir = Path(data_dir)
    path = data_dir / FILE
    reg = SC._load(path) or _vuoto()
    oggi = pd.Timestamp(now).date()
    ieri = str(oggi - timedelta(days=1))
    nuove = aggiungi(reg, scanner, universo if universo is not None else _universo(cache))
    vive = [o for o in reg["operazioni"] if o.get("stato") != "chiusa"]
    if not nuove and path.exists() and (not vive or (reg.get("dati_fino") or "") >= ieri):
        return build(reg, now)          # niente di nuovo: nessuna richiesta, file intatto
    dati, errori = {"ritardo": False, "nota": None}, []
    if vive:
        net = net or SC.Rete()
        da = oggi - timedelta(days=SC.WINDOW_DAYS)
        fino = []
        for i, o in enumerate(reg["operazioni"]):
            if o.get("stato") == "chiusa":
                continue
            c = o.get("c")
            if not c or not c.get("perp"):
                reg["operazioni"][i] = dict(o, nota="moneta senza fonte dati: non valutabile")
                continue
            try:
                s = SC.aggiorna_moneta(net, c, cache, oggi, da, seed_dir)
            except SC.ReteNonDisponibile as e:
                s = dict(SC.cache_moneta(c, cache, da, seed_dir), errore=f"rete: {str(e)[:60]}")
            if s["errore"]:
                errori.append(o["t"])
            f = SC.feats(s["spot"], s["perp"], s["funding"])
            if f is not None and len(f):
                f = f[f.index.date < oggi]
                fino.append(str(f.index[-1].date()))
            reg["operazioni"][i] = valuta(o, f, oggi)
        reg["dati_fino"] = min(fino) if fino else reg.get("dati_fino")
        if errori:
            dati = {"ritardo": True, "nota": f"Dati non aggiornati per {', '.join(errori)}: valori sull'ultima cache."}
    else:
        reg["dati_fino"] = ieri
    reg["aggiornato"] = pd.Timestamp(now).isoformat(timespec="minutes")
    data_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg, ensure_ascii=False, separators=(",", ":"), default=str))
    r = riepilogo([o for o in reg["operazioni"] if o.get("filtro")])
    print(f"[radar] scommesse sulla carta: {r['aperte']} aperte, {r['chiuse']} chiuse, {r['attesa']} in attesa, risultato {r['risultato_usd']} $"
          + (f" · {nuove} nuove" if nuove else ""))
    return build(reg, now, dati)
