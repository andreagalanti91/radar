"""Soglie d'allarme di W3.2 dal vivo (solo avviso: nessuna azione automatica, non cambia segnali né posizione).

Sullo storico dal vivo (dal primo trade reale W3 nel registro data/journal.json, altrimenti da weekly.LIVE_START):
- drawdown dell'equity della simulazione W3.2 (report["weekly"]["history"]: eq_dates/eq1, posizione aperta valutata
  alla chiusura giornaliera) dal suo massimo nel periodo;
- stop consecutivi: trade chiusi per trailing o stop iniziale IN PERDITA, contati dall'ultimo trade chiuso all'indietro.
Allarme se drawdown ≤ −15% o ≥ 2 stop consecutivi. Un solo avviso Telegram per evento (marker in data/state.json, chiave
"guard": scritto solo se Telegram conferma). Evento drawdown = massimo da cui si misura; evento stop = ultimo stop della serie.
"""
from __future__ import annotations

import pandas as pd

from . import weekly

DD_ALARM = -15.0          # % dal massimo dell'equity dal vivo
STOPS_ALARM = 2           # stop consecutivi in perdita
STOP_REASONS = ("stop", "trail")
TEXT = "Soglia d'allarme: revisione consigliata e rischio dimezzato (decisione dell'utente). Nessuna azione automatica."


def live_start(journal: dict | None) -> str:
    """Primo ingresso reale W3 nel registro (strategia w2/w3), altrimenti LIVE_START."""
    days = []
    for t in (journal or {}).get("trades", []):
        if t.get("strategy") in ("w2", "w3"):
            for e in t.get("entries") or []:
                if e.get("time"):
                    days.append(str(e["time"])[:10])
    return min(days) if days else weekly.LIVE_START


def compute(wcur: dict, start: str) -> dict:
    h = (wcur or {}).get("history") or {}
    dates, eq = h.get("eq_dates") or [], h.get("eq1") or []
    s = pd.Series(eq, index=pd.to_datetime(dates), dtype=float).dropna()
    s = s[s.index >= pd.Timestamp(start)]
    out = {"since": start, "thresholds": {"dd_pct": DD_ALARM, "stops_in_a_row": STOPS_ALARM}, "dd_pct": None,
           "dd_max_pct": None, "peak_date": None, "stops_in_a_row": 0, "last_stop": None, "alarm": False, "why": []}
    if len(s):
        peak = s.cummax()
        out["dd_pct"] = round(float((s.iloc[-1] / peak.iloc[-1] - 1) * 100), 2)
        out["dd_max_pct"] = round(float((s / peak - 1).min() * 100), 2)
        out["peak_date"] = str(s.idxmax().date())        # massimo da cui si misura il drawdown attuale
        out["eq_date"] = str(s.index[-1].date())
    else:
        print(f"[guard] nessun dato di equity dal {start}: drawdown non calcolato")
    closed = [t for t in h.get("trades", []) if t.get("reason") != "open" and t.get("exit") and t["exit"] >= start]
    n, last = 0, None
    for t in reversed(closed):
        if t.get("reason") in STOP_REASONS and (t.get("pnl_pct") or 0) < 0:
            n += 1
            last = last or t["signal"]
        else:
            break
    out["stops_in_a_row"], out["last_stop"] = n, last
    if out["dd_pct"] is not None and out["dd_pct"] <= DD_ALARM:
        out["why"].append(f"equity {out['dd_pct']:+.1f}% dal massimo del {out['peak_date']} (soglia {DD_ALARM:.0f}%)")
    if n >= STOPS_ALARM:
        out["why"].append(f"{n} stop consecutivi in perdita (ultimo: segnale del {last}; soglia {STOPS_ALARM})")
    out["alarm"] = bool(out["why"])
    return out


def events(g: dict) -> list[str]:
    ev = []
    if g["dd_pct"] is not None and g["dd_pct"] <= DD_ALARM:
        ev.append(f"dd:{g['peak_date']}")
    if g["stops_in_a_row"] >= STOPS_ALARM:
        ev.append(f"stops:{g['last_stop']}")
    return ev


def format_alarm(g: dict) -> str:
    return ("<b>RADAR SIGNAL BTC · Soglia d'allarme W3.2</b>\n" + "\n".join(g["why"])
            + f"\nStorico dal vivo dal {g['since']}.\n" + TEXT)


def update(wcur: dict | None, st: dict, journal: dict | None = None, send=None) -> dict | None:
    """Calcola lo stato e invia un avviso per ogni evento nuovo; marca st["guard"]["sent"] solo se send conferma."""
    if not wcur:
        return None
    if send is None:
        from .telegram import send
    g = compute(wcur, live_start(journal))
    gs = st.setdefault("guard", {})
    sent = list(gs.get("sent", []))
    new = [e for e in events(g) if e not in sent]
    if new:
        if send(format_alarm(g)):
            gs["sent"] = (sent + new)[-20:]
            print(f"[guard] avviso inviato: {new}")
        else:
            print("[guard] avviso non confermato da Telegram: si riprova al prossimo giro")
    gs["last"] = {k: g[k] for k in ("dd_pct", "stops_in_a_row", "alarm")}
    print(f"[guard] dal {g['since']}: drawdown {g['dd_pct']}% (peggiore {g['dd_max_pct']}%), stop consecutivi "
          f"{g['stops_in_a_row']}, allarme {'SÌ' if g['alarm'] else 'no'}")
    return g
