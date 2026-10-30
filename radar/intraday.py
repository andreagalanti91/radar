"""Controllo in tempo reale (orario) degli ordini del piano: limit DCA, stop e target.

Il modello lavora su candele giornaliere, ma gli ordini vengono toccati durante la giornata.
Ogni ora si scaricano le candele orarie dall'ultima chiusura giornaliera e si controlla se un livello
del piano attivo è stato raggiunto. Gli alert sono un avviso operativo; lo stato ufficiale del trade
viene confermato alla chiusura giornaliera dal motore di backtest.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests

KLINES = "https://data-api.binance.vision/api/v3/klines"


def hourly_since(day: str, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Candele orarie dalla mezzanotte UTC successiva al giorno `day` (ultima chiusura nota)."""
    start = int((pd.Timestamp(day) + pd.Timedelta(days=1)).tz_localize("UTC").timestamp() * 1000)
    try:
        r = requests.get(KLINES, params={"symbol": symbol, "interval": "1h", "startTime": start, "limit": 1000}, timeout=20)
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


def _levels(report: dict) -> list[dict]:
    """Livelli da sorvegliare: nuovo segnale di oggi oppure trade aperto."""
    out = []
    sig, ot = report.get("signal"), report.get("open_trade", {}).get("futures")
    if sig:
        sg = 1 if sig["side"] == "long" else -1
        for k, e in enumerate(sig["entries"][1:], start=2):
            out.append({"kind": "entry", "price": e["price"], "sg": sg, "label": f"limit DCA {k} ({int(e['weight']*100)}%)"})
        out.append({"kind": "stop", "price": sig["stop"], "sg": sg, "label": "stop loss"})
        for k, t in enumerate(sig["take_profits"], start=1):
            out.append({"kind": "tp", "price": t["price"], "sg": sg, "label": f"take profit {k}"})
    elif ot:
        sg = 1 if ot["side"] == "long" else -1
        for k, v in enumerate(ot.get("pending_entries", []), start=1):
            out.append({"kind": "entry", "price": v, "sg": sg, "label": "limit DCA in attesa"})
        out.append({"kind": "stop", "price": ot["stop"], "sg": sg, "label": "stop attuale"})
        for k, v in enumerate(ot.get("next_tps", []), start=ot.get("tp_hit", 0) + 1):
            out.append({"kind": "tp", "price": v, "sg": sg, "label": f"take profit {k}"})
    return out


def check(report: dict, already: list[str]) -> tuple[list[dict], list[str]]:
    """Ritorna (eventi nuovi, chiavi aggiornate). `already` evita alert doppi."""
    lv = _levels(report)
    if not lv:
        return [], already
    h = hourly_since(report["date"])
    if h.empty:
        return [], already
    lo, hi = float(h["low"].min()), float(h["high"].max())
    events, keys = [], list(already)
    for x in lv:
        below = x["kind"] in ("entry", "stop") and x["sg"] == 1 or x["kind"] == "tp" and x["sg"] == -1
        hit = lo <= x["price"] if below else hi >= x["price"]
        key = f"{report['date']}:{x['kind']}:{x['price']}"
        if hit and key not in keys:
            keys.append(key)
            events.append({**x, "last": float(h["close"].iloc[-1]),
                           "time": datetime.now(timezone.utc).strftime("%H:%M UTC")})
    return events, keys[-50:]


def format_events(events: list[dict]) -> str:
    icon = {"entry": "🟢", "tp": "✅", "stop": "🛑"}
    lines = ["<b>RADAR SIGNAL BTC · Ordine toccato (tempo reale)</b>"]
    for e in events:
        lines.append(f"{icon[e['kind']]} {e['label']} a ${e['price']:,.0f}".replace(",", "."))
    lines.append(f"Prezzo ora ${events[0]['last']:,.0f} · {events[0]['time']}".replace(",", "."))
    lines.append("Lo stato ufficiale del trade si conferma alla chiusura giornaliera.")
    return "\n".join(lines)
