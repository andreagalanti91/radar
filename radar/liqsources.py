"""Liquidazioni reali di BTC da più exchange (solo API REST pubbliche e gratuite, raggiungibili da runner USA).

Ogni ora: scarica gli eventi recenti, normalizza (ts, exchange, id, side, price, btc, usd), controlla la qualità,
accoda a data/liq_events/YYYY-MM.csv senza doppioni (exchange+id) e scrive una riga per fonte in coverage.csv.
side = lato LIQUIDATO: "long" (vendita forzata) o "short" (acquisto forzato).
Fonti escluse (vedi research/liq_fonti/README.md): Binance fapi e Bybit (bloccati negli USA, solo websocket),
BitMEX (403 dal sandbox), Hyperliquid (i trade pubblici non marcano le liquidazioni), Bitget (nessun endpoint pubblico).
"""
from __future__ import annotations

import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from .data import DATA_DIR

EV_DIR = DATA_DIR / "liq_events"
COLS = ["ts", "exchange", "id", "side", "price", "btc", "usd"]
TIMEOUT = 15
MAX_PRICE_DEV = 0.05  # scarto massimo dal prezzo mediano del giro


def _get(url, params=None):
    r = requests.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _ev(ts_ms, exch, eid, side, price, btc):
    price, btc = float(price), abs(float(btc))
    return {"ts": int(ts_ms), "exchange": exch, "id": str(eid), "side": side,
            "price": price, "btc": round(btc, 8), "usd": round(btc * price, 2)}


# ---------- parser puri (testabili senza rete) ----------
def parse_okx(details):
    return [_ev(d["ts"], "okx", f'{d["ts"]}-{d["bkPx"]}-{d["sz"]}', d["posSide"], d["bkPx"], float(d["sz"]) * 0.01)
            for d in details if d.get("posSide") in ("long", "short")]


def parse_gate(rows, mult=0.0001):
    out = []
    for r in rows:
        size = float(r.get("size") or 0) or -float(r.get("order_size") or 0)
        if not size:
            continue
        px = r.get("fill_price") or r.get("order_price")
        out.append(_ev(int(r["time"]) * 1000, "gate", f'{r["time"]}-{px}-{r.get("size")}',
                       "long" if size > 0 else "short", px, size * mult))
    return out


def parse_deribit(trades):
    out = []
    for t in trades:
        liq = t.get("liquidation")
        if not liq:
            continue
        taker_sell = t["direction"] == "sell"
        # "T" = liquidato il taker (lato = direzione), "M" = liquidato il maker (lato opposto)
        sell = taker_sell if "T" in liq else not taker_sell
        out.append(_ev(t["timestamp"], "deribit", t["trade_id"], "long" if sell else "short",
                       t["price"], float(t["amount"]) / float(t["price"])))  # amount in USD sul perpetuo
    return out


def parse_kraken(history):
    out = []
    for h in history:
        if h.get("type") != "liquidation":
            continue
        ts = datetime.fromisoformat(h["time"][:26].rstrip("Z") + "+00:00").timestamp() * 1000
        out.append(_ev(ts, "kraken", h.get("uid") or h["trade_id"], "long" if h["side"] == "sell" else "short",
                       h["price"], h["size"]))
    return out


def parse_dydx(trades):
    out = []
    for t in trades:
        if t.get("type") != "LIQUIDATED":
            continue
        ts = datetime.fromisoformat(t["createdAt"].replace("Z", "+00:00")).timestamp() * 1000
        out.append(_ev(ts, "dydx", t["id"], "long" if t["side"] == "SELL" else "short", t["price"], t["size"]))
    return out


def parse_lighter(trades):
    out = []
    for t in trades:
        if "liquidation" not in str(t.get("type", "")):
            continue
        taker_buy = bool(t.get("is_maker_ask"))
        out.append(_ev(t["timestamp"], "lighter", t["trade_id"], "short" if taker_buy else "long", t["price"], t["size"]))
    return out


# ---------- fetch (rete) ----------
def fetch_okx(since_ms=0, pages=20):
    url, out, after = "https://www.okx.com/api/v5/public/liquidation-orders", [], None
    for _ in range(pages):
        p = {"instType": "SWAP", "uly": "BTC-USDT", "state": "filled", "limit": 100}
        if after:
            p["after"] = after
        det = (_get(url, p).get("data") or [{}])[0].get("details", [])
        if not det:
            break
        out += parse_okx(det)
        after = min(int(d["ts"]) for d in det)
        if after <= since_ms:
            break
    return out


def fetch_gate(hours=3):
    now, out = int(time.time()), []
    for h in range(hours):  # l'API accetta finestre di massimo 1 ora
        rows = _get("https://api.gateio.ws/api/v4/futures/usdt/liq_orders",
                    {"contract": "BTC_USDT", "from": now - 3600 * (h + 1) + 1, "to": now - 3600 * h, "limit": 1000})
        out += parse_gate(rows)
    return out


def fetch_deribit(hours=2, pages=30):
    end, start, out = int(time.time() * 1000), int(time.time() * 1000) - hours * 3600_000, []
    for _ in range(pages):
        r = _get("https://www.deribit.com/api/v2/public/get_last_trades_by_instrument_and_time",
                 {"instrument_name": "BTC-PERPETUAL", "start_timestamp": start, "end_timestamp": end,
                  "count": 1000, "sorting": "desc"})["result"]
        tr = r.get("trades", [])
        out += parse_deribit(tr)
        if not r.get("has_more") or not tr:
            break
        end = min(t["timestamp"] for t in tr) - 1
    return out


def fetch_kraken():
    return parse_kraken(_get("https://futures.kraken.com/derivatives/api/v3/history", {"symbol": "PF_XBTUSD"}).get("history", []))


def fetch_dydx():
    return parse_dydx(_get("https://indexer.dydx.trade/v4/trades/perpetualMarket/BTC-USD", {"limit": 1000}).get("trades", []))


def fetch_lighter():
    return parse_lighter(_get("https://mainnet.zklighter.elliot.ai/api/v1/recentTrades",
                              {"market_id": 1, "limit": 100}).get("trades", []))


SOURCES = {"okx": fetch_okx, "gate": fetch_gate, "deribit": fetch_deribit,
           "kraken": fetch_kraken, "dydx": fetch_dydx, "lighter": fetch_lighter}


# ---------- qualità e archivio ----------
def check(events, now_ms=None):
    """Scarta eventi incoerenti: prezzo/size non positivi, nel futuro, prezzo lontano dalla mediana. Ritorna (buoni, note)."""
    now_ms = now_ms or int(time.time() * 1000)
    good = [e for e in events if e["price"] > 0 and e["btc"] > 0 and e["ts"] <= now_ms + 60_000 and e["side"] in ("long", "short")]
    notes = []
    if len(good) < len(events):
        notes.append(f"scartati {len(events) - len(good)} non validi")
    if good:
        px = sorted(e["price"] for e in good)[len(good) // 2]
        ok = [e for e in good if abs(e["price"] / px - 1) <= MAX_PRICE_DEV]
        if len(ok) < len(good):
            notes.append(f"scartati {len(good) - len(ok)} con prezzo >5% dalla mediana {px:.0f}")
        good = ok
    return good, notes


def load(months=2, ev_dir=None):
    ev_dir = Path(ev_dir or EV_DIR)
    out = []
    for p in sorted(ev_dir.glob("20??-??.csv"))[-months:]:
        with open(p, newline="") as f:
            for r in csv.DictReader(f):
                r["ts"], r["price"], r["btc"], r["usd"] = int(r["ts"]), float(r["price"]), float(r["btc"]), float(r["usd"])
                out.append(r)
    return out


def store(events, ev_dir=None):
    """Accoda per mese senza doppioni (exchange+id). Ritorna il numero di eventi nuovi per exchange."""
    ev_dir = Path(ev_dir or EV_DIR)
    ev_dir.mkdir(parents=True, exist_ok=True)
    by_month, added = {}, {}
    for e in events:
        m = datetime.fromtimestamp(e["ts"] / 1000, timezone.utc).strftime("%Y-%m")
        by_month.setdefault(m, []).append(e)
    for m, evs in by_month.items():
        p = ev_dir / f"{m}.csv"
        seen = set()
        if p.exists():
            with open(p, newline="") as f:
                seen = {(r["exchange"], r["id"]) for r in csv.DictReader(f)}
        new = []
        for e in sorted(evs, key=lambda e: e["ts"]):
            k = (e["exchange"], e["id"])
            if k not in seen:
                seen.add(k)
                new.append(e)
                added[e["exchange"]] = added.get(e["exchange"], 0) + 1
        if new:
            exists = p.exists()
            with open(p, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLS)
                if not exists:
                    w.writeheader()
                w.writerows(new)
    return added


def collect(ev_dir=None, sources=None) -> dict:
    ev_dir = Path(ev_dir or EV_DIR)
    sources = sources or SOURCES
    last = {}
    for e in load(1, ev_dir):
        last[e["exchange"]] = max(last.get(e["exchange"], 0), e["ts"])
    allev, status = [], {}
    for name, fn in sources.items():
        try:
            evs = fn(last.get("okx", 0)) if name == "okx" else fn()
            status[name] = ["ok", len(evs), ""]
            allev += evs
        except Exception as ex:  # una fonte rotta non ferma le altre
            status[name] = ["errore", 0, f"{type(ex).__name__}: {str(ex)[:80]}"]
    good, notes = check(allev)
    added = store(good, ev_dir)
    run = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cov = ev_dir / "coverage.csv"
    exists = cov.exists()
    with open(cov, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["run", "exchange", "stato", "scaricati", "nuovi", "nota"])
        for name, (st, n, note) in status.items():
            w.writerow([run, name, st, n, added.get(name, 0), note])
    msg = ", ".join(f"{k}:{v[0]}/{v[1]}+{added.get(k, 0)}" for k, v in status.items())
    print(f"[liq-fonti] {msg}" + (f" | {'; '.join(notes)}" if notes else ""))
    return {"status": status, "added": added, "notes": notes}


def summary(events=None, now_ms=None, big_usd=250_000, top=10, ev_dir=None) -> dict:
    """Totali per exchange (1h/24h, long vs short liquidati in $) e ultimi eventi grandi."""
    now_ms = now_ms or int(time.time() * 1000)
    events = load(2, ev_dir) if events is None else events
    per = {}
    for e in events:
        age = now_ms - e["ts"]
        if age < 0 or age > 86_400_000:
            continue
        d = per.setdefault(e["exchange"], {w: {"long_usd": 0.0, "short_usd": 0.0, "n": 0} for w in ("1h", "24h")})
        for w, lim in (("1h", 3_600_000), ("24h", 86_400_000)):
            if age <= lim:
                d[w][f'{e["side"]}_usd'] += e["usd"]
                d[w]["n"] += 1
    tot = {w: {k: sum(p[w][k] for p in per.values()) for k in ("long_usd", "short_usd", "n")} for w in ("1h", "24h")}
    big = sorted((e for e in events if 0 <= now_ms - e["ts"] <= 86_400_000 and e["usd"] >= big_usd),
                 key=lambda e: e["ts"], reverse=True)[:top]
    last = max((e["ts"] for e in events), default=None)
    return {"per_exchange": per, "total": tot, "big": big, "last_ts": last,
            "stale": last is None or now_ms - last > 6 * 3_600_000}
