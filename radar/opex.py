"""Controllo "OPEX" (scadenze delle opzioni su BTC) accanto alla posizione aperta: CONTESTO descrittivo, non segnale. W3.2 non cambia.

Nasce dallo studio research/opex (26/11/2026): attorno alle scadenze mensili Deribit BTC non si muove più né meno dei venerdì
normali; la leggera tendenza al rialzo nella settimana dopo (mediana +1,7% contro −0,1%) è una misura su trenta, concentrata nel
2020–21. Il "massimo dolore" storico non è ricostruibile: da oggi si salva uno snapshot per verificare in futuro la "calamita".
Nessun avviso, nessun effetto su W3.2.

Fonti, in ordine: Deribit (public/get_book_summary_by_currency?currency=BTC&kind=option: open interest per contratto in BTC,
scadenza nel nome, prezzo indice); ripiego OKX (public/instruments + public/open-interest + market/index-tickers: opt-summary non
ha l'open interest); infine l'ultimo risultato salvato (data/opex/ultimo.json). Solo API pubbliche, nessuna chiave.

Ritmo: si scarica una volta al giorno (giorno UTC nuovo) e ogni 4 ore nelle ultime 48 ore prima della scadenza principale, o
quando la scadenza salvata è passata; negli altri giri orari si rilegge il file e si aggiornano solo giorni/ore alla scadenza.

Scadenza principale = la prossima mensile (ultimo venerdì del mese, 08:00 UTC; trimestrale a marzo, giugno, settembre,
dicembre); settimanale = il venerdì quotato più vicino diverso dalla principale.

Calcoli sulla scadenza principale: open interest per strike (call e put, in BTC), nozionale in scadenza (OI × prezzo, USD),
rapporto put/call sull'OI, massimo dolore (lo strike di regolamento che minimizza il valore intrinseco totale delle opzioni in
scadenza, cioè quanto incasserebbero i compratori), muri (strike con più OI call sopra il prezzo e più OI put sotto il prezzo),
distanza del prezzo dal massimo dolore, giorni/ore alla scadenza.

Calendario (report.opex.calendar, pagina Opzioni · "Scadenze maggiori"): i 6 venerdì più vicini, più le mensili/trimestrali e le
scadenze con nozionale ≥ 1 mld $ entro 120 giorni, più la prossima trimestrale. Per ognuna: nozionale, put/call, massimo dolore,
OI call/put (BTC), muri, iv_atm (mark_iv Deribit allo strike più vicino al future della scadenza, media call/put), movimento
atteso a una deviazione standard (iv_atm · √(giorni/365), ricalcolato a ogni giro) e skew (IV put ~10% sotto − IV call ~10%
sopra). Stessa chiamata Deribit (get_book_summary_by_currency ha mark_iv e underlying_price); con OKX i campi di volatilità sono null.

Snapshot: una riga compatta per ogni scaricamento in data/opex/snap.jsonl (al più una al giorno, più quelle ogni 4 ore negli
ultimi 2 giorni): servirà, dopo 12–18 scadenze, a verificare se il prezzo si avvicina al massimo dolore.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
DIR = "opex"
LAST_FILE = "ultimo.json"
SNAP_FILE = "snap.jsonl"
DERIBIT = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
OKX = "https://www.okx.com/api/v5/"
MONTHS = {m: i + 1 for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))}
FAST_HOURS = 48            # nelle ultime 48 ore prima della scadenza principale si riscarica ogni 4 ore
FAST_EVERY = 4
BAND = 0.20                # grafico a barre: strike entro ±20% dal prezzo
NEAR_PCT = 1.0             # massimo dolore entro ±1% dal prezzo = "vicino"
CAL_N = 6                  # scadenze nel calendario (venerdì più vicini), più mensili e grandi entro CAL_DAYS
CAL_DAYS = 120             # orizzonte di "Scadenze maggiori" (pagina Opzioni)
BIG_USD = 1e9              # scadenza "maggiore": nozionale ≥ 1 miliardo $
SKEW_OTM = 0.10            # skew = IV put ~10% sotto il future − IV call ~10% sopra
SKEW_TOL = 0.04
SRC_NAME = {"deribit": "Deribit (API pubblica)", "okx": "OKX (API pubblica, ripiego)"}
NOTE = "contesto, non cambia W3.2 (studio research/opex: nessun vantaggio dimostrabile attorno alle scadenze)"
# risultati dello studio (research/opex/risultati.txt, 26/11/2026): mediane, scadenze mensili contro gli altri venerdì
STUDY = {
    "n_m": 86, "n_q": 29, "n_o": 289, "since": "2019-09",
    "rows": [
        {"k": "|rendimento| 7 g prima", "m": 3.65, "q": 3.54, "o": 4.29},
        {"k": "Range 7 g prima", "m": 10.24, "q": 10.26, "o": 10.67},
        {"k": "Range del venerdì", "m": 4.20, "q": 4.15, "o": 4.10},
        {"k": "Rendimento 7 g dopo", "m": 1.72, "q": 0.87, "o": -0.11, "signed": True},
        {"k": "Range 7 g dopo", "m": 10.59, "q": 9.34, "o": 11.10},
    ],
    "up_m": 62, "up_q": 62, "up_o": 48, "p_post": 0.024,
}


# ------------------------------------------------------------------ calendario
def last_friday(y: int, m: int) -> datetime:
    """Ultimo venerdì del mese alle 08:00 UTC (scadenza mensile Deribit)."""
    nxt = datetime(y + (m == 12), m % 12 + 1, 1, 8, tzinfo=UTC)
    d = nxt - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - 4) % 7)


def next_monthly(now: datetime) -> datetime:
    """Prossima scadenza mensile dopo `now` (se quella del mese è già passata, quella del mese dopo)."""
    e = last_friday(now.year, now.month)
    if e <= now:
        e = last_friday(now.year + (now.month == 12), now.month % 12 + 1)
    return e


def is_quarterly(e: datetime) -> bool:
    return e.month in (3, 6, 9, 12) and e == last_friday(e.year, e.month)


def kind_of(e: datetime) -> str:
    if e == last_friday(e.year, e.month):
        return "trimestrale" if e.month in (3, 6, 9, 12) else "mensile"
    return "settimanale" if e.weekday() == 4 else "giornaliera"


def parse_deribit_name(name: str) -> tuple[datetime, float, str] | None:
    """"BTC-27NOV26-60000-C" → (scadenza 08:00 UTC, strike, "C"/"P")."""
    try:
        _, d, k, t = name.split("-")
        e = datetime(2000 + int(d[-2:]), MONTHS[d[-5:-2]], int(d[:-5]), 8, tzinfo=UTC)
        return e, float(k), t
    except (ValueError, KeyError):
        return None


# ------------------------------------------------------------------ fonti
def _f(x) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _get(url: str, params: dict | None = None) -> dict:
    """GET JSON con la sessione e i tentativi di radar.data (2 tentativi: il giro orario non deve aspettare minuti)."""
    from .data import _get as get_http
    r = get_http(url, params=params, retries=2)
    if r is None:
        raise RuntimeError(f"{url}: 404")
    return r.json()


def fetch_deribit(get=None) -> tuple[list[dict], float]:
    """(contratti [{exp, strike, type, oi, iv, und}], prezzo indice). OI in BTC (un contratto Deribit = 1 BTC); iv = mark_iv in %
    (None se assente o zero), und = underlying_price, cioè il future (o sintetico) di quella scadenza, None se assente."""
    j = (get or _get)(DERIBIT, {"currency": "BTC", "kind": "option"})
    res = j.get("result") if isinstance(j, dict) else None
    if not res:
        raise RuntimeError("Deribit: risposta senza contratti")
    out, px = [], 0.0
    for x in res:
        p = parse_deribit_name(str(x.get("instrument_name", "")))
        if not p:
            continue
        out.append({"exp": p[0], "strike": p[1], "type": p[2], "oi": _f(x.get("open_interest")),
                    "iv": _f(x.get("mark_iv")) or None, "und": _f(x.get("underlying_price")) or None})
        px = px or _f(x.get("estimated_delivery_price")) or _f(x.get("underlying_price"))
    if not out or px <= 0:
        raise RuntimeError("Deribit: contratti o prezzo mancanti")
    return out, px


def fetch_okx(get=None) -> tuple[list[dict], float]:
    """Ripiego OKX: strumenti (scadenza, strike, tipo) + open interest (oiCcy, in BTC) + prezzo indice BTC-USD. Niente volatilità:
    iv_atm, mov_atteso_pct e skew del calendario restano null."""
    g = get or _get

    def data(path, params):
        j = g(OKX + path, params)
        if not isinstance(j, dict) or j.get("code") != "0":
            raise RuntimeError(f"OKX {path}: risposta {j.get('code') if isinstance(j, dict) else j!r}")
        return j.get("data") or []
    inst = {x["instId"]: x for x in data("public/instruments", {"instType": "OPTION", "uly": "BTC-USD"})}
    ois = data("public/open-interest", {"instType": "OPTION", "uly": "BTC-USD"})
    idx = data("market/index-tickers", {"instId": "BTC-USD"})
    px = _f(idx[0].get("idxPx")) if idx else 0.0
    out = []
    for o in ois:
        x = inst.get(o.get("instId"))
        if not x:
            continue
        out.append({"exp": datetime.fromtimestamp(int(x["expTime"]) / 1000, UTC), "strike": _f(x.get("stk")),
                    "type": x.get("optType"), "oi": _f(o.get("oiCcy"))})
    if not out or px <= 0:
        raise RuntimeError("OKX: contratti o prezzo mancanti")
    return out, px


# ------------------------------------------------------------------ calcolo
def chain_of(contracts: list[dict], exp: datetime) -> dict[float, list[float]]:
    """{strike: [OI call, OI put]} per una scadenza."""
    ch: dict[float, list[float]] = {}
    for c in contracts:
        if c["exp"] == exp and c["strike"] > 0:
            v = ch.setdefault(c["strike"], [0.0, 0.0])
            v[0 if c["type"] == "C" else 1] += c["oi"]
    return dict(sorted(ch.items()))


def max_pain(ch: dict[float, list[float]]) -> tuple[float | None, float | None]:
    """(strike del massimo dolore, valore intrinseco totale in USD a quello strike). Candidati = gli strike quotati."""
    ks = [k for k, v in ch.items()]
    if not ks or sum(v[0] + v[1] for v in ch.values()) <= 0:
        return None, None
    best = None
    for s in ks:
        pain = sum(c * max(s - k, 0) + p * max(k - s, 0) for k, (c, p) in ch.items())
        if best is None or pain < best[1]:
            best = (s, pain)
    return best


def put_call(ch: dict[float, list[float]]) -> float | None:
    c = sum(v[0] for v in ch.values())
    p = sum(v[1] for v in ch.values())
    return round(p / c, 2) if c > 0 else None


def walls(ch: dict[float, list[float]], px: float) -> tuple[float | None, float | None]:
    """(muro call = strike con più OI call sopra il prezzo, muro put = strike con più OI put sotto il prezzo)."""
    up = [(v[0], k) for k, v in ch.items() if k >= px and v[0] > 0]
    dn = [(v[1], k) for k, v in ch.items() if k <= px and v[1] > 0]
    return (max(up)[1] if up else None), (max(dn)[1] if dn else None)


def summarize(ch: dict[float, list[float]], px: float) -> dict:
    mp, pain = max_pain(ch)
    cw, pw = walls(ch, px)
    oc, op = sum(v[0] for v in ch.values()), sum(v[1] for v in ch.values())
    return {"max_pain": mp, "pain_usd": None if pain is None else round(pain), "put_call": put_call(ch),
            "oi_call": round(oc, 1), "oi_put": round(op, 1), "notional": round((oc + op) * px),
            "call_wall": cw, "put_wall": pw,
            "dist_pct": None if mp is None else round((mp / px - 1) * 100, 2)}


def pick(contracts: list[dict], now: datetime) -> tuple[datetime, datetime | None]:
    """(scadenza principale, settimanale più vicina). Principale = prossima mensile quotata con OI; se manca, la mensile dopo."""
    exps = sorted({c["exp"] for c in contracts if c["exp"] > now})
    if not exps:
        raise RuntimeError("nessuna scadenza futura")
    main = next_monthly(now)
    for _ in range(3):
        if main in exps:
            break
        main = next_monthly(main)
    else:
        raise RuntimeError("scadenza mensile non quotata")
    wk = next((e for e in exps if e.weekday() == 4 and e != main), None)
    return main, wk


def mov_pct(iv: float | None, days: float) -> float | None:
    """Movimento atteso a una deviazione standard (≈ 68%) in %: iv/100 · √(giorni/365) · 100."""
    if iv is None or days <= 0:
        return None
    return round(iv * math.sqrt(days / 365), 1)


def vol_of(contracts: list[dict], exp: datetime) -> dict:
    """Volatilità di una scadenza dai mark_iv di Deribit: iv_atm (media call/put allo strike più vicino al future di quella
    scadenza), skew (IV della put ~10% sotto il future − IV della call ~10% sopra, in punti), fut. Tutto None senza mark_iv (OKX)."""
    rows = [c for c in contracts if c["exp"] == exp and c["strike"] > 0]
    unds = sorted(c["und"] for c in rows if c.get("und"))
    out = {"iv_atm": None, "skew": None, "fut": None}
    ivs = {(c["strike"], c["type"]): c["iv"] for c in rows if c.get("iv")}
    if not unds or not ivs:
        return out
    f = unds[len(unds) // 2]
    out["fut"] = round(f, 2)
    ks = sorted({k for k, _ in ivs})
    atm = min(ks, key=lambda k: abs(k - f))
    a = [ivs[(atm, t)] for t in ("C", "P") if (atm, t) in ivs]
    out["iv_atm"] = round(sum(a) / len(a), 1)
    kp = [k for k, t in ivs if t == "P"]
    kc = [k for k, t in ivs if t == "C"]
    if kp and kc:
        p = min(kp, key=lambda k: abs(k - f * (1 - SKEW_OTM)))
        c = min(kc, key=lambda k: abs(k - f * (1 + SKEW_OTM)))
        # solo se gli strike trovati sono davvero ~10% fuori (entro 4 punti), altrimenti la misura non è confrontabile
        if abs(p / f - (1 - SKEW_OTM)) <= SKEW_TOL and abs(c / f - (1 + SKEW_OTM)) <= SKEW_TOL:
            out["skew"] = round(ivs[(p, "P")] - ivs[(c, "C")], 1)
    return out


def cal_entry(contracts: list[dict], e: datetime, px: float, now: datetime) -> dict | None:
    """Una riga del calendario: nozionale, put/call, massimo dolore, OI call/put, muri, volatilità e movimento atteso."""
    sc = chain_of(contracts, e)
    s = summarize(sc, px)
    if s["oi_call"] + s["oi_put"] <= 0:
        return None
    v = vol_of(contracts, e)
    days = (e - now).total_seconds() / 86400
    return {"exp": e.isoformat(), "kind": kind_of(e), "notional": s["notional"], "put_call": s["put_call"],
            "max_pain": s["max_pain"], "oi_call": s["oi_call"], "oi_put": s["oi_put"], "call_wall": s["call_wall"],
            "put_wall": s["put_wall"], "iv_atm": v["iv_atm"], "mov_atteso_pct": mov_pct(v["iv_atm"], days), "skew": v["skew"],
            "fut": v["fut"]}


def compute(contracts: list[dict], px: float, now: datetime, src: str) -> dict:
    """Risultato completo (senza i campi che dipendono dall'ora del giro, aggiunti da finish())."""
    main, wk = pick(contracts, now)
    ch = chain_of(contracts, main)
    s = summarize(ch, px)
    lo, hi = px * (1 - BAND), px * (1 + BAND)
    bars = [[k, round(v[0], 1), round(v[1], 1)] for k, v in ch.items() if lo <= k <= hi and (v[0] + v[1]) > 0]
    weekly = None
    if wk is not None:
        sw = summarize(chain_of(contracts, wk), px)
        weekly = {"exp": wk.isoformat(), "kind": kind_of(wk), "notional": sw["notional"], "max_pain": sw["max_pain"],
                  "put_call": sw["put_call"]}
    cal = []
    exps = sorted({c["exp"] for c in contracts if c["exp"] > now})
    for e in exps:
        if e.weekday() != 4 and e != main:
            continue
        x = cal_entry(contracts, e, px, now)
        if x is None:
            continue
        cal.append(x)
        if len(cal) >= CAL_N:
            break
    # oltre le prime CAL_N: le mensili/trimestrali e le scadenze grandi (≥ 1 mld $) entro CAL_DAYS giorni (per "Scadenze maggiori")
    seen = {c["exp"] for c in cal}
    for e in exps:
        if e.isoformat() in seen or (e - now) > timedelta(days=CAL_DAYS):
            continue
        x = cal_entry(contracts, e, px, now)
        if x is not None and (x["kind"] in ("mensile", "trimestrale") or x["notional"] >= BIG_USD):
            cal.append(x)
            seen.add(x["exp"])
    # prossima trimestrale nel calendario anche se oltre
    if not any(c["kind"] == "trimestrale" for c in cal):
        q = next((e for e in exps if is_quarterly(e)), None)
        x = cal_entry(contracts, q, px, now) if q is not None else None
        if x is not None:
            cal.append(x)
    cal.sort(key=lambda c: c["exp"])
    total = sum(c["oi"] for c in contracts if c["exp"] > now)
    return dict(s, exp=main.isoformat(), kind=kind_of(main), quarterly=is_quarterly(main), price=round(px, 2),
                ts=now.isoformat(timespec="seconds"), src=src, bars=bars, weekly=weekly, calendar=cal,
                share=round(100 * (s["oi_call"] + s["oi_put"]) / total, 1) if total > 0 else None)


# ------------------------------------------------------------------ frase
def _n0(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


WD = ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica")


def frase(side: str | None, r: dict, now: datetime) -> str:
    """UNA frase per la posizione aperta di BTC (side long/short, None = flat). Sempre "solo contesto"."""
    mp, d = r.get("max_pain"), r.get("dist_pct")
    if mp is None or d is None:
        return "Massimo dolore non calcolabile — solo contesto"
    e = datetime.fromisoformat(r["exp"])
    h = (e - now).total_seconds() / 3600
    quando = f"fino a {WD[e.weekday()]}" if h <= 7 * 24 else f"fino al {e:%d/%m}"
    if abs(d) <= NEAR_PCT:
        base = f"Massimo dolore {_n0(mp)} $: vicino al prezzo, possibile prezzo fermo {quando}"
        tail = ""
    else:
        up = d > 0
        verso = "l'alto" if up else "il basso"
        base = f"Massimo dolore {_n0(mp)} $: {'sopra' if up else 'sotto'} il prezzo, possibile spinta verso {verso} {quando}"
        art = {"long": ("del long", "il long"), "short": ("dello short", "lo short")}.get(side)
        tail = "" if not art else (f" (a favore {art[0]})" if up == (side == "long") else f" (contro {art[1]})")
    if h > 7 * 24:
        base += ", effetto di solito debole a più di una settimana"
    return f"{base}{tail} — solo contesto"


def status_line(r: dict, now: datetime) -> str:
    """"Scadenza venerdì 27/11 · tra 1 g" (sotto le 24 ore: "tra 20 h")."""
    e = datetime.fromisoformat(r["exp"])
    h = max(0.0, (e - now).total_seconds() / 3600)
    t = f"tra {max(1, round(h))} h" if h < 24 else f"tra {int(h // 24)} g"
    return f"Scadenza {WD[e.weekday()]} {e:%d/%m} · {t}"


# ------------------------------------------------------------------ file
def _read_last(d: Path) -> dict | None:
    p = d / LAST_FILE
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:  # noqa: BLE001
        print(f"[opex] {p.name} non leggibile ({e!r})")
        return None


def _snap(r: dict) -> dict:
    w = r.get("weekly") or {}
    return {"ts": r["ts"], "src": r["src"], "price": r["price"], "exp": r["exp"], "kind": r["kind"], "max_pain": r["max_pain"],
            "call_wall": r["call_wall"], "put_wall": r["put_wall"], "put_call": r["put_call"], "notional": r["notional"],
            "oi_call": r["oi_call"], "oi_put": r["oi_put"], "w_exp": w.get("exp"), "w_max_pain": w.get("max_pain")}


def _save(d: Path, r: dict) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / LAST_FILE).write_text(json.dumps(r, separators=(",", ":")) + "\n")
    with (d / SNAP_FILE).open("a") as fh:
        fh.write(json.dumps(_snap(r), separators=(",", ":")) + "\n")


def due(last: dict | None, now: datetime) -> bool:
    """Serve scaricare? Mai fatto, giorno UTC nuovo, scadenza salvata passata, o ultime 48 ore e dato vecchio di 4 ore."""
    if not last:
        return True
    try:
        ts, e = datetime.fromisoformat(last["ts"]), datetime.fromisoformat(last["exp"])
    except (KeyError, ValueError):
        return True
    if ts.date() != now.date() or e <= now:
        return True
    if any("iv_atm" not in c for c in last.get("calendar") or []):   # file di prima del calendario esteso (27/11/2026): riscarica
        return True
    return (e - now) <= timedelta(hours=FAST_HOURS) and (now - ts) >= timedelta(hours=FAST_EVERY) - timedelta(minutes=5)


def finish(r: dict, side: str | None, now: datetime, note: str | None) -> dict:
    """Aggiunge i campi che dipendono dall'ora del giro e dalla posizione."""
    e = datetime.fromisoformat(r["exp"])
    h = (e - now).total_seconds() / 3600
    out = dict(r)
    out.update({"hours": round(h, 1), "days": round(h / 24, 2), "status": status_line(r, now), "side": side,
                "frase": frase(side, r, now), "note": NOTE, "src_name": SRC_NAME.get(r.get("src"), r.get("src")),
                "source_note": note, "study": STUDY})
    out["calendar"] = [dict(c, mov_atteso_pct=mov_pct(c.get("iv_atm"), (datetime.fromisoformat(c["exp"]) - now).total_seconds() / 86400))
                       if c.get("iv_atm") is not None else c for c in (out.get("calendar") or [])]
    if out.get("weekly"):
        out["weekly"] = dict(out["weekly"], hours=round((datetime.fromisoformat(out["weekly"]["exp"]) - now).total_seconds() / 3600, 1))
    return out


def build(data_dir: Path, side: str | None = None, get=None, now: datetime | None = None) -> dict:
    """report["opex"]: scadenza principale (OI per strike, nozionale, put/call, massimo dolore, muri, distanza), settimanale,
    calendario, studio, frase per la posizione. Rete giù = ultimo risultato con la nota; senza file = errore (_soft nel giro)."""
    now = now or datetime.now(UTC)
    d = Path(data_dir) / DIR
    last = _read_last(d)
    if not due(last, now):
        return finish(last, side, now, None)
    errs = []
    for src, fn in (("deribit", fetch_deribit), ("okx", fetch_okx)):
        try:
            contracts, px = fn(get)
            r = compute(contracts, px, now, src)
            _save(d, r)
            return finish(r, side, now, None if src == "deribit" else "Deribit non risponde: dati OKX (solo la parte di OKX del mercato)")
        except Exception as e:  # noqa: BLE001
            errs.append(f"{src} {type(e).__name__}")
    if not last:
        raise RuntimeError("opex non disponibile: " + ", ".join(errs))
    ts = datetime.fromisoformat(last["ts"])
    note = f"Fonti non raggiungibili ({', '.join(errs)}): ultimo dato del {ts:%d/%m %H:%M} UTC"
    if datetime.fromisoformat(last["exp"]) <= now:
        note += "; la scadenza salvata è già passata"
    return finish(last, side, now, note)


def side_of(weekly: dict | None) -> str | None:
    """Verso della posizione aperta di W3.2 su BTC (None se flat o in attesa d'ingresso)."""
    from .onchain import side_of as so
    return so(weekly)
