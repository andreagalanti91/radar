"""Alert Telegram sui wallet della sentinella (Hyperliquid): posizioni e ordini, confronto fra due fotografie.

Gira ogni 5 minuti (.github/workflows/wallets.yml). Wallet: i 3 fissi della sentinella + le 3 balene scelte ogni giorno da
radar/scout.py (data/wallet_picks.json, salvato nel repository dal workflow orario). Un wallet appena entrato fra le scelte
viene solo fotografato al primo giro, senza alert. Per ogni wallet legge posizioni e ordini aperti su tutti i DEX di
Hyperliquid (principale + HIP-3) e li confronta con la fotografia precedente (data/wallets_state.json, conservata nella
cache di GitHub Actions). Alert su:
- posizione nuova, chiusa o girata; variazione di size di almeno il 25% e di RADAR_WALLET_MIN dollari (default 50k);
- ordini nuovi (limit, take profit, stop) da almeno RADAR_WALLET_ORDER_MIN dollari (default 100k): sono le "prossime mosse".
Il Principale fa migliaia di operazioni al giorno: per questo non si notifica ogni fill ma solo i cambi di posizione.
Primo avvio (nessuno stato salvato): registra e non invia nulla.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from . import telegram

API = "https://api.hyperliquid.xyz/info"
STATE = Path(__file__).resolve().parents[1] / "data" / "wallets_state.json"
WALLETS = [
    ("0xd4c1f7e8d876c4749228d515473d36f919583d1d", "Principale"),
    ("0x99967871e6c4f9a5185abc57edede9e9540191f6", "Simile 1"),
    ("0x807a2e2e469df84b299da5f90f15dda4380daca1", "Simile 2"),
]
PICKS = STATE.with_name("wallet_picks.json")   # le 3 balene scelte ogni giorno da radar/scout.py (file nel repository)


def watched() -> list[tuple[str, str]]:
    """Sentinella (fissa) + le 3 balene del giorno, se il file delle scelte c'è (il workflow orario lo salva in data/)."""
    out = list(WALLETS)
    try:
        picks = json.loads(PICKS.read_text()).get("picks", []) if PICKS.exists() else []
    except Exception as e:  # noqa: BLE001
        print(f"[wallet] scelte del giorno non lette: {e!r}")
        picks = []
    have = {a for a, _ in out}
    for p in picks:
        a = str(p.get("address", "")).lower()
        if a.startswith("0x") and a not in have:
            out.append((a, f"{p.get('name') or a[:8]} · selezione giornaliera"))
            have.add(a)
    return out


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
