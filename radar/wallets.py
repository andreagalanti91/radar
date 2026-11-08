"""Wallet osservati (esattamente 3) e alert Telegram su di loro (Hyperliquid): posizioni e ordini, confronto fra due fotografie.

Lista osservata: data/wallets_watch.json (posti 1–3). La cambia solo l'utente, via Telegram (/sostituisci, /conferma, gestiti
qui da command() e chiamati da radar/journal.py durante il giro orario); radar/scout.py propone i candidati ma non sostituisce.
Gira ogni 5 minuti (.github/workflows/wallets.yml). Un wallet appena entrato nella lista viene solo fotografato al primo giro,
senza alert. Per ogni wallet legge posizioni e ordini aperti su tutti i DEX di
Hyperliquid (principale + HIP-3) e li confronta con la fotografia precedente (data/wallets_state.json, conservata nella
cache di GitHub Actions). Alert su:
- posizione nuova, chiusa o girata; variazione di size di almeno il 25% e di RADAR_WALLET_MIN dollari (default 50k);
- ordini nuovi (limit, take profit, stop) da almeno RADAR_WALLET_ORDER_MIN dollari (default 100k): sono le "prossime mosse".
Il Principale fa migliaia di operazioni al giorno: per questo non si notifica ogni fill ma solo i cambi di posizione.
Primo avvio (nessuno stato salvato): registra e non invia nulla.
"""
from __future__ import annotations

import html
import json
import math
import os
import re
import time
from pathlib import Path

import requests

from . import telegram

API = "https://api.hyperliquid.xyz/info"
STATE = Path(__file__).resolve().parents[1] / "data" / "wallets_state.json"
WATCH = STATE.with_name("wallets_watch.json")   # i 3 wallet osservati e i candidati (file nel repository)
# lista iniziale (se il file manca): Principale e Simile 1 scelti dall'utente, il terzo posto è da approvare
WALLETS = [
    ("0xd4c1f7e8d876c4749228d515473d36f919583d1d", "Principale"),
    ("0x99967871e6c4f9a5185abc57edede9e9540191f6", "Simile 1"),
    ("0x807a2e2e469df84b299da5f90f15dda4380daca1", "Simile 2"),
]
N_SLOTS = 3
_ADDR = re.compile(r"^0x[0-9a-f]{40}$")


def default_watch() -> dict:
    return {"version": 1, "updated": None, "candidates": [], "dismissed": {}, "history": [], "review": None,
            "slots": [{"slot": i + 1, "address": a, "name": n, "status": "confermato" if i < 2 else "provvisorio"} for i, (a, n) in enumerate(WALLETS)]}


def load_watch(path: Path | None = None) -> dict:
    path = path or WATCH
    try:
        w = json.loads(path.read_text()) if path.exists() else None
    except Exception as e:  # noqa: BLE001
        print(f"[wallet] lista osservata non letta: {e!r}")
        w = None
    w = w or default_watch()
    for k, v in default_watch().items():
        w.setdefault(k, v)
    slots = {int(x["slot"]): x for x in w.get("slots", []) if _ADDR.match(str(x.get("address", "")).lower())}
    w["slots"] = [slots.get(i) or default_watch()["slots"][i - 1] for i in range(1, N_SLOTS + 1)]   # sempre 3 posti
    return w


def save_watch(w: dict, path: Path | None = None) -> None:
    path = path or WATCH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(w, indent=1, default=str))


def watched(path: Path | None = None) -> list[tuple[str, str]]:
    """Solo i 3 wallet della lista osservata, nell'ordine dei posti."""
    return [(x["address"].lower(), x["name"]) for x in load_watch(path)["slots"]]


MIN_POS = float(os.environ.get("RADAR_WALLET_MIN", "50000"))
MIN_ORD = float(os.environ.get("RADAR_WALLET_ORDER_MIN", "100000"))
CHANGE = 0.25
PAGE = "https://andreagalanti91.github.io/radar/#wallet"


_W: list[tuple[float, int]] = []   # (istante, peso) delle richieste dell'ultimo minuto
BUDGET = 1000                      # Hyperliquid: ~1200 di peso al minuto per IP; 6 wallet × 11 DEX superano il limite senza freno


def _throttle(w: int) -> None:
    while True:
        now = time.time()
        _W[:] = [x for x in _W if now - x[0] < 60]
        if sum(x[1] for x in _W) + w <= BUDGET:
            _W.append((now, w))
            return
        time.sleep(1)


def _post(body: dict):
    _throttle(2 if body.get("type") in ("clearinghouseState", "spotClearinghouseState", "allMids") else 20)
    for k in range(3):
        r = requests.post(API, json=body, timeout=20)
        if r.status_code == 429:
            time.sleep(2 + 3 * k)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Hyperliquid: troppe richieste")


def snapshot(addr: str, dexes: list[str]) -> dict:
    """{"pos": {coin: {"szi", "ntl", "entry"}}, "ord": {oid: {...}}} su tutti i DEX."""
    pos, ords = {}, {}
    for dex in dexes:
        cs = _post({"type": "clearinghouseState", "user": addr, **({"dex": dex} if dex else {})})
        for ap in cs.get("assetPositions", []):
            p = ap["position"]
            szi = float(p["szi"])
            if szi:
                pos[p["coin"]] = {"szi": szi, "ntl": abs(float(p["positionValue"])), "entry": float(p.get("entryPx") or 0)}
        for o in _post({"type": "frontendOpenOrders", "user": addr, **({"dex": dex} if dex else {})}):
            px = float(o.get("triggerPx") or 0) if o.get("isTrigger") else float(o["limitPx"])
            px = px or float(o["limitPx"])
            sz = float(o.get("origSz") or o["sz"]) or float(o["sz"])
            ords[str(o["oid"])] = {"coin": o["coin"], "side": "buy" if o["side"] == "B" else "sell", "px": px, "ntl": sz * px,
                                   "type": o.get("orderType", "Limit"), "ro": bool(o.get("reduceOnly")), "tpsl": o.get("isPositionTpsl", False)}
    return {"pos": pos, "ord": ords}


def _usd(x: float) -> str:
    return f"${x / 1e6:.2f}M".replace(".", ",") if abs(x) >= 1e6 else f"${x / 1e3:.0f}k"


def _px(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".") if x >= 100 else f"{x:.4g}".replace(".", ",")


def diff(name: str, old: dict, new: dict) -> list[str]:
    """Righe di alert per un wallet: cambi di posizione e ordini nuovi sopra soglia."""
    out = []
    op, np_ = old.get("pos", {}), new.get("pos", {})
    for c in sorted(set(op) | set(np_)):
        a, b = op.get(c), np_.get(c)
        side = lambda s: "LONG" if s > 0 else "SHORT"   # noqa: E731
        if a is None and b and b["ntl"] >= MIN_POS:
            out.append(f"🆕 Apre <b>{side(b['szi'])} {c}</b> {_usd(b['ntl'])} a {_px(b['entry'])}")
        elif b is None and a and a["ntl"] >= MIN_POS:
            out.append(f"✅ Chiude <b>{side(a['szi'])} {c}</b> (era {_usd(a['ntl'])})")
        elif a and b and (a["szi"] > 0) != (b["szi"] > 0) and max(a["ntl"], b["ntl"]) >= MIN_POS:
            out.append(f"🔄 Gira <b>{c}</b>: da {side(a['szi'])} {_usd(a['ntl'])} a <b>{side(b['szi'])}</b> {_usd(b['ntl'])}")
        elif a and b:
            d = abs(b["szi"]) - abs(a["szi"])
            dn = abs(d) * (b["ntl"] / abs(b["szi"]))
            if abs(d) >= CHANGE * abs(a["szi"]) and dn >= MIN_POS:
                out.append(f"{'➕ Aumenta' if d > 0 else '➖ Riduce'} <b>{side(b['szi'])} {c}</b> di {_usd(dn)} → {_usd(b['ntl'])}")
    no = [o for k, o in new.get("ord", {}).items() if k not in old.get("ord", {}) and o["ntl"] >= MIN_ORD]
    for o in sorted(no, key=lambda o: -o["ntl"])[:6]:
        kind = "TP/SL" if o["tpsl"] or "Take" in o["type"] or "Stop" in o["type"] else ("riduce" if o["ro"] else o["type"].lower())
        out.append(f"📌 Nuovo ordine {'acquisto' if o['side'] == 'buy' else 'vendita'} <b>{o['coin']}</b> {_usd(o['ntl'])} a {_px(o['px'])} ({kind})")
    if len(no) > 6:
        out.append(f"… e altri {len(no) - 6} ordini nuovi sopra {_usd(MIN_ORD)}")
    return [f"<b>{name}</b>"] + out if out else []


# ------------------------------------------------------------------ candidati e approvazione (Telegram)
def _pc(x, d=0, sign=True) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "–"
    v = f"{x * 100:{'+' if sign else ''}.{d}f}%".replace(".", ",")
    return v.replace("-", "−")


def _m(x) -> str:
    return "–" if x is None else _usd(x)


def _act(m: dict) -> str:
    f = m.get("fills_day")
    lv = m.get("lev")
    a = "–" if f is None else (f"{f:,.0f}".replace(",", ".") if f >= 10 else f"{f:.1f}".replace(".", ",")) + "/g"
    return a + ("" if lv is None else f" · {lv:.1f}x".replace(".", ","))


# (etichetta, funzione) delle righe del confronto: le stesse metriche dello scout (radar/scout.py)
ROWS = [("Punteggio", lambda m, sc: "–" if sc is None else f"{sc:.0f}"),
        ("Rend. 1 anno", lambda m, sc: _pc(m.get("ret_1y"))),
        ("Max drawdown", lambda m, sc: _pc(m.get("dd"), sign=False)),
        ("R² crescita", lambda m, sc: "–" if m.get("r2") is None else f"{m['r2']:.2f}".replace(".", ",")),
        ("Periodi +", lambda m, sc: _pc(m.get("pos"), sign=False)),
        ("Funding/PnL", lambda m, sc: _pc(m.get("fund_pnl"), 1, sign=False)),
        ("Valore", lambda m, sc: _m(m.get("value"))),
        ("Ultimi 30g", lambda m, sc: _pc(m.get("ret_30d"), 1)),
        ("Attività, leva", lambda m, sc: _act(m))]


def compare_text(c: dict) -> str:
    """Confronto affiancato candidato / wallet che sostituirebbe, in <pre> (Telegram, HTML)."""
    a, b = c.get("metrics") or {}, c.get("vs_metrics") or {}
    w = 14
    head = f"{'':{w}} {'candidato':>11} {c.get('vs_name', 'attuale')[:11]:>11}"
    lines = [head] + [f"{lab:{w}} {fn(a, c.get('score')):>11} {fn(b, c.get('vs_score')):>11}" for lab, fn in ROWS]
    return "<pre>" + html.escape("\n".join(lines)) + "</pre>"


def candidate_text(c: dict, new: bool = True) -> str:
    adr = c["address"]
    return "\n".join([
        f"<b>{'RADAR · WALLET · nuovo candidato' if new else 'Candidato'}: {html.escape(c.get('name') or c['id'])}</b> (id {c['id']}) "
        f"per il posto {c['slot']}, al posto di <b>{html.escape(c.get('vs_name', ''))}</b>",
        f"<code>{adr}</code>" + (f" · {html.escape(c['display'])}" if c.get("display") else ""),
        f"Perché: {html.escape(c.get('reason', ''))}",
        compare_text(c),
        f"Approva: <code>/sostituisci {c['slot']} {c['id']}</code> · scarta: <code>/scarta {c['id']}</code> · elenco: /candidati",
        f"<a href=\"https://hyperdash.com/address/{adr}\">Hyperdash</a> · <a href=\"{PAGE}\">pagina Wallet</a>"])


def _find(w: dict, key: str) -> tuple[dict | None, str]:
    """Candidato (o alternativa del posto in revisione) per id, prefisso o indirizzo."""
    k = key.lower().removeprefix("#")
    pool = [("cand", c) for c in w.get("candidates", [])] + [("review", o) for o in ((w.get("review") or {}).get("options") or [])]
    hit = [(t, c) for t, c in pool if c.get("id", "").lower() == k or c["address"].lower() == k or (len(k) >= 4 and c["address"].lower().startswith(k if k.startswith("0x") else "0x" + k))]
    return (hit[0][1], hit[0][0]) if hit else (None, "")


def _slot_line(x: dict) -> str:
    st = " · <i>provvisorio, da approvare</i>" if x.get("status") == "provvisorio" else ""
    sc = f" · punti {x['score']:.0f}" if isinstance(x.get("score"), (int, float)) else ""
    return f"{x['slot']}. <b>{html.escape(x['name'])}</b> <code>{x['address'][:6]}…{x['address'][-4:]}</code>{sc}{st}"


HELP_W = ("<b>Wallet osservati</b>\n/osservati · i 3 wallet seguiti\n/candidati · candidati dello scout con il confronto\n"
          "/sostituisci 3 8bae [nome] · mette il candidato 8bae al posto 3\n/conferma 3 · conferma un posto provvisorio\n/scarta 8bae · scarta un candidato per 30 giorni")
COMMANDS = ("osservati", "candidati", "sostituisci", "conferma", "scarta")


def command(text: str, today: str, path: Path | None = None) -> str | None:
    """Comandi Telegram della lista osservata. None se il comando non è di questo modulo (lo gestisce radar/journal.py)."""
    parts = text.strip().split()
    if not parts or not parts[0].startswith("/"):
        return None
    cmd = parts[0][1:].split("@")[0].lower()
    if cmd not in COMMANDS:
        return None
    w, args = load_watch(path), parts[1:]
    if cmd == "osservati":
        return "<b>Wallet osservati</b>\n" + "\n".join(_slot_line(x) for x in w["slots"]) + f"\n\nCandidati in attesa: {len(w['candidates'])} (/candidati)"
    if cmd == "candidati":
        cs = w["candidates"]
        rv = w.get("review") or {}
        out = [candidate_text(c, new=False) for c in cs]
        if rv.get("options"):
            out.append(f"<b>Posto {rv['slot']} provvisorio</b>: {html.escape(rv.get('note', ''))}\nConferma: <code>/conferma {rv['slot']}</code> · alternative: "
                       + ", ".join(f"{html.escape(o['name'])} <code>/sostituisci {rv['slot']} {o['id']}</code>" for o in rv["options"]))
        return "\n\n".join(out) if out else "Nessun candidato: i 3 wallet osservati restano i migliori secondo lo scout. /osservati per la lista."
    if cmd == "conferma":
        n = int(args[0]) if args and args[0].isdigit() else 0
        if not 1 <= n <= N_SLOTS:
            return "Scrivi /conferma 1, 2 o 3."
        x = w["slots"][n - 1]
        x["status"] = "confermato"
        x["since"] = x.get("since") or today
        if (w.get("review") or {}).get("slot") == n:
            w["review"] = None
        w["updated"] = today
        save_watch(w, path)
        return f"✅ Posto {n} confermato: {html.escape(x['name'])}."
    if cmd == "scarta":
        if not args:
            return "Scrivi /scarta seguito dall'id del candidato (es. /scarta 8bae)."
        c, _ = _find(w, args[0])
        if not c:
            return f"Nessun candidato «{html.escape(args[0])}». /candidati per l'elenco."
        w["dismissed"][c["address"]] = today
        w["candidates"] = [x for x in w["candidates"] if x["address"] != c["address"]]
        w["updated"] = today
        save_watch(w, path)
        return f"Candidato {c.get('id')} scartato: non verrà riproposto per 30 giorni."
    # sostituisci <posto> <id> [nome]
    if len(args) < 2 or not args[0].isdigit() or not 1 <= int(args[0]) <= N_SLOTS:
        return "Formato: /sostituisci &lt;posto 1-3&gt; &lt;id candidato&gt; [nome], es. /sostituisci 3 8bae. /candidati per l'elenco."
    n = int(args[0])
    c, kind = _find(w, args[1])
    if not c:
        return f"Nessun candidato «{html.escape(args[1])}». /candidati per l'elenco."
    if any(x["address"] == c["address"] for x in w["slots"]):
        return f"{html.escape(c['name'])} è già fra gli osservati."
    old = w["slots"][n - 1]
    name = " ".join(args[2:])[:24] or c.get("name") or f"Balena {c['id']}"
    w["slots"][n - 1] = {"slot": n, "address": c["address"], "name": name, "status": "confermato", "since": today,
                         "score": c.get("score"), "metrics": c.get("metrics"), "fails": c.get("fails", []), "checked": c.get("date")}
    w["history"].append({"date": today, "slot": n, "out": [old["address"], old["name"]], "in": [c["address"], name], "via": "telegram"})
    w["history"] = w["history"][-60:]
    # i candidati confrontati con il wallet uscito vanno rifatti: li ricalcola lo scout al prossimo giro
    w["candidates"] = [x for x in w["candidates"] if x["address"] != c["address"] and x.get("slot") != n]
    if (w.get("review") or {}).get("slot") == n:
        w["review"] = None
    w["updated"] = today
    save_watch(w, path)
    return (f"✅ Posto {n}: <b>{html.escape(name)}</b> <code>{c['address'][:6]}…{c['address'][-4:]}</code> al posto di {html.escape(old['name'])}.\n"
            f"Alert attivi dal prossimo controllo (il primo giro registra senza avvisare).\n" + "\n".join(_slot_line(x) for x in w["slots"]))


def run() -> None:
    dexes = [""] + [d["name"] for d in _post({"type": "perpDexs"}) if d]
    old = json.loads(STATE.read_text()) if STATE.exists() else None
    new, msgs = {}, []
    for addr, name in watched():
        try:
            new[addr] = snapshot(addr, dexes)
        except Exception as e:  # noqa: BLE001
            print(f"[wallet] {name}: {e!r}")
            if old and addr in old:
                new[addr] = old[addr]   # dato mancante: si tiene la fotografia precedente, niente falsi alert
            continue
        if old and addr in old:
            msgs += diff(name, old[addr], new[addr])
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(new))
    if old is None:
        print("[wallet] primo avvio: fotografia registrata, nessun alert")
        return
    if msgs and os.environ.get("RADAR_WALLET_ALERTS", "1") == "1":
        telegram.send("<b>SENTINELLA WALLET · Hyperliquid</b>\n" + "\n".join(msgs) + f"\n\n<a href=\"{PAGE}\">Apri la pagina Wallet</a>")
    print(f"[wallet] {len(msgs)} righe di alert")


if __name__ == "__main__":
    run()
