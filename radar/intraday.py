"""Controllo in tempo reale (orario) dei livelli v2: soglia di conferma, limit DCA, stop e take profit.

Il motore v2 lavora su candele 4h (conferma e gestione del trade). Ogni ora si scaricano le candele orarie dal momento
rilevante (giorno dopo il segnale se si attende la conferma, ingresso se il trade è aperto) e si controlla se un livello
è stato toccato. Gli alert sono un avviso operativo; lo stato ufficiale (conferma, limit, TP, stop) lo dà il motore v2
sulle candele 4h chiuse, a ogni giro orario.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests

KLINES = "https://data-api.binance.vision/api/v3/klines"


def hourly_since(start, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Candele orarie (UTC) da `start` (timestamp o giorno)."""
    t = pd.Timestamp(start)
    t = t.tz_localize("UTC") if t.tzinfo is None else t
    try:
        r = requests.get(KLINES, params={"symbol": symbol, "interval": "1h", "startTime": int(t.timestamp() * 1000),
                                         "limit": 1000}, timeout=20)
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        print(f"[intraday] {type(e).__name__}")
        return pd.DataFrame()
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows).iloc[:, :5]
    d.columns = ["t", "open", "high", "low", "close"]
    d["t"] = pd.to_datetime(d["t"], unit="ms", utc=True)
    return d.set_index("t").astype(float)


def _levels(report: dict) -> tuple[list[dict], str | None]:
    """(livelli da sorvegliare, inizio della finestra oraria) dallo stato v2."""
    v = report.get("v2") or {}
    st = v.get("status")
    if st not in ("conferma", "ingresso", "aperto"):
        return [], None
    sg = 1 if v["side"] == "long" else -1
    if st == "conferma":
        since = str(pd.Timestamp(v["signal_date"]) + pd.Timedelta(days=1))
        return [{"kind": "confirm", "price": v["trigger"], "sg": sg,
                 "label": f"soglia di conferma 4h ({'sopra' if sg == 1 else 'sotto'})"}], since
    p = v["plan"]
    out = []
    if st == "ingresso" or not v["filled"][1]:
        out.append({"kind": "entry", "price": p["limit"], "sg": sg, "label": "limit DCA 60%"})
    out.append({"kind": "stop", "price": v.get("stop", p["stop"]), "sg": sg, "label": "stop loss"})
    out.append({"kind": "tp", "price": v.get("tp", p["tp_first"]), "sg": sg, "label": "take profit +1R"})
    return out, v["entry_time"]


def check(report: dict, already: list[str], h: pd.DataFrame | None = None) -> tuple[list[dict], list[str]]:
    """Ritorna (eventi nuovi, chiavi aggiornate). `already` evita alert doppi; `h` = candele orarie (test)."""
    lv, since = _levels(report)
    if not lv:
        return [], already
    h = hourly_since(since) if h is None else h
    if h.empty:
        return [], already
    lo, hi = float(h["low"].min()), float(h["high"].max())
    events, keys = [], list(already)
    sd = report["v2"]["signal_date"]
    for x in lv:
        below = x["kind"] in ("entry", "stop") and x["sg"] == 1 or x["kind"] in ("tp", "confirm") and x["sg"] == -1
        hit = lo <= x["price"] if below else hi >= x["price"]
        # una sola allerta per la soglia di conferma (si sposta a ogni barra 4h), per gli altri livelli una per prezzo
        key = f"{sd}:confirm" if x["kind"] == "confirm" else f"{sd}:{x['kind']}:{x['price']}"
        if hit and key not in keys:
            keys.append(key)
            events.append({**x, "last": float(h["close"].iloc[-1]),
                           "time": datetime.now(timezone.utc).strftime("%H:%M UTC")})
    return events, keys[-50:]


def format_events(events: list[dict]) -> str:
    icon = {"confirm": "⏳", "entry": "🟢", "tp": "✅", "stop": "🛑"}
    lines = ["<b>RADAR SIGNAL BTC · Livello toccato (tempo reale)</b>"]
    for e in events:
        lines.append(f"{icon[e['kind']]} {e['label']} a ${e['price']:,.0f}".replace(",", "."))
        if e["kind"] == "confirm":
            lines.append("L'ingresso scatta solo se la candela 4h CHIUDE oltre la soglia.")
    lines.append(f"Prezzo ora ${events[0]['last']:,.0f} · {events[0]['time']}".replace(",", "."))
    lines.append("Lo stato ufficiale si conferma sulle candele 4h chiuse (controllo ogni ora).")
    return "\n".join(lines)
