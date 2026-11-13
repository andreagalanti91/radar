"""Uso:
  python -m radar.cli daily        aggiorna dati, calcola segnale, invia alert, genera dashboard
  python -m radar.cli backtest     stampa le statistiche del backtest
  python -m radar.cli test-telegram  invia un messaggio di prova
"""
from __future__ import annotations

import os
import sys
import warnings

warnings.filterwarnings("ignore")

from . import telegram  # noqa: E402
from .backtest import run, summary  # noqa: E402
from .dashboard import render  # noqa: E402
from .data import CRITICAL, STALE_HOURS, load_all, stale_sources, update_all  # noqa: E402
from .features import build_features  # noqa: E402
from .live import BACKTEST_START, diff_events, evaluate, save_state  # noqa: E402
from .news import fetch_calendar, fetch_central_banks, fetch_news  # noqa: E402
from . import intraday  # noqa: E402
from . import paper  # noqa: E402
from . import lab  # noqa: E402
from . import weekly  # noqa: E402
from . import journal  # noqa: E402
import pandas as pd  # noqa: E402
from .liquidations import collect as collect_liquidations  # noqa: E402
import json  # noqa: E402
from .live import STATE_FILE  # noqa: E402
from .strategy import Params  # noqa: E402


def _now() -> pd.Timestamp:
    return pd.Timestamp.utcnow().tz_localize(None)


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        print(f"[radar] state.json non leggibile ({e!r}): si riparte da uno stato vuoto")
        return {}


def _save_state(st: dict) -> None:
    STATE_FILE.write_text(json.dumps(st, indent=2, default=str))


def weekly_alerts(cur: dict, st: dict, send=None, h=None) -> list[dict]:
    """Eventi W3 + controllo orario dello stop. Ogni evento si marca in st["weekly"] SOLO se send() conferma
    (message_id o True); i falliti si ripropongono al giro dopo. Il controllo orario guarda il più protettivo tra
    lo stop del modello e l'ultimo comunicato. Restituisce gli eventi inviati."""
    send = send or telegram.send
    sent, st["weekly"] = weekly.send_events(cur, st.get("weekly"), send)
    keys = st.get("weekly_intraday_keys", [])
    hev, new_keys = weekly.check_intraday(cur, keys, h, told=weekly.told_level(st["weekly"], cur))
    if hev:
        if send(weekly.format_intraday(hev)):
            st["weekly_intraday_keys"] = new_keys
        else:
            print("[radar] allerta stop W3 non confermata da Telegram: si riprova al prossimo giro")
    return sent


def source_alerts(errors: dict, stale: dict, st: dict, now: pd.Timestamp, data_until: str | None, send=None) -> None:
    """Avvisi sulle fonti (al massimo uno al giorno per tipo, marcati solo se inviati): fonte W3 non scaricata
    (si valuta sull'ultima cache) e dati fermi da oltre 36 ore."""
    send = send or telegram.send
    today = str(now.date())
    crit = {k: v for k, v in errors.items() if k in CRITICAL}
    note = f"W3 valutato sui dati fino al {data_until}: decisioni possibili in ritardo." if data_until else ""
    if crit and st.get("source_alert") != today:
        if send("<b>RADAR SIGNAL BTC · Fonte non disponibile</b>\n"
                + "\n".join(f"fonte {k} non disponibile ({v})" for k, v in crit.items()) + f"\n{note}"):
            st["source_alert"] = today
    if stale and st.get("stale_alert") != today:
        if send(f"<b>RADAR SIGNAL BTC · Dati vecchi</b>\nFonti ferme da oltre {STALE_HOURS} ore: "
                + ", ".join(f"{k} (ultimo giorno {v})" for k, v in stale.items()) + f".\n{note}"):
            st["stale_alert"] = today


def heartbeat_due(st: dict, now: pd.Timestamp) -> bool:
    """Un messaggio di salute al giorno (UTC), al primo giro dopo le 07:00 UTC."""
    return os.environ.get("RADAR_HEARTBEAT", "1") == "1" and now.hour >= 7 and st.get("heartbeat") != str(now.date())


def heartbeat(cur: dict | None, st: dict, now: pd.Timestamp, data_until: str, problems: list[str], send=None) -> bool:
    send = send or telegram.send
    if not heartbeat_due(st, now):
        return False
    if send(weekly.format_heartbeat(cur, data_until, now.strftime("%d/%m %H:%M UTC"), problems, str(now.date()))):
        st["heartbeat"] = str(now.date())
        return True
    return False


BRIEF_WAIT_H = 6   # se alle 06:00 UTC i dati non arrivano ancora a ieri, il riepilogo parte comunque (con la data dei dati)


def brief_due(st: dict, now: pd.Timestamp, data_until: str | None) -> bool:
    """Riepilogo giornaliero: una volta al giorno (UTC), al primo giro dopo le 00:00 che ha i dati fino a ieri (candela
    giornaliera chiusa), oppure dalle BRIEF_WAIT_H UTC anche senza. Dipende dallo stato (st["daily_brief"]) e non dal cron:
    il cron delle 00:30 di daily.yml non partiva mai. RADAR_DAILY_BRIEF=0 lo spegne."""
    if os.environ.get("RADAR_DAILY_BRIEF", "1") != "1" or st.get("daily_brief") == str(now.date()):
        return False
    yesterday = str((now - pd.Timedelta(days=1)).date())
    return bool(data_until and data_until >= yesterday) or now.hour >= BRIEF_WAIT_H


def daily_brief(report: dict, st: dict, now: pd.Timestamp, data_until: str | None, send=None) -> bool:
    """Invia il riepilogo se dovuto; il marker del giorno si scrive solo se Telegram conferma (si riprova al giro dopo)."""
    send = send or telegram.send
    if not brief_due(st, now, data_until):
        return False
    if send(telegram.daily_brief(report)):
        st["daily_brief"] = str(now.date())
        return True
    print("[radar] riepilogo giornaliero non confermato da Telegram: si riprova al prossimo giro")
    return False


def _soft(label: str, fn, *a, **k):
    """Fonte o modulo non essenziale per W3: un errore si registra e non ferma il giro."""
    try:
        return fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] {label} non disponibile: {e!r}")
        return None


def daily() -> None:
    try:   # registro dei trade reali: comandi Telegram arrivati dall'ultimo giro (risposta entro un'ora)
        n = journal.poll()
        if n:
            print(f"[radar] registro reale: {n} comandi Telegram eseguiti")
    except Exception as e:  # noqa: BLE001
        print(f"[radar] registro reale non letto: {e!r}")
    errors: dict = {}
    try:
        d = update_all(errors=errors)
    except Exception as e:  # noqa: BLE001   fonte W3 senza dati né cache: niente da valutare
        telegram.send(f"<b>RADAR SIGNAL BTC · Fonte non disponibile</b>\n{type(e).__name__}: dati W3 assenti, giro interrotto.")
        raise
    f = build_features(d)
    now = _now()
    stale = stale_sources(d, now)
    data_until = min(str(d[k].index.max().date()) for k in CRITICAL)
    problems = [f"fonte {k} non disponibile" for k in errors] + [f"dati {k} vecchi" for k in stale]
    # ---- W3 per primo: valutazione e alert prima di tutto il resto (fonti accessorie, v2, dashboard)
    st = _load_state()
    wcur = None
    try:
        wcur = weekly.evaluate(f)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] settimanale W3 non calcolato: {e!r}")
        problems.append("W3 non calcolato")
        if st.get("w3_error_alert") != str(now.date()) and telegram.send(
                f"<b>RADAR SIGNAL BTC · W3 non calcolato</b>\n{type(e).__name__}: {str(e)[:200]}"):
            st["w3_error_alert"] = str(now.date())
    if wcur:
        try:
            sent = weekly_alerts(wcur, st)
            print(f"[radar] W3 {wcur['status']} · eventi inviati: {[e['type'] for e in sent]}")
        except Exception as e:  # noqa: BLE001
            print(f"[radar] eventi settimanali non inviati: {e!r}")
    _soft("avvisi sulle fonti", source_alerts, errors, stale, st, now, data_until)
    _soft("heartbeat", heartbeat, wcur, st, now, data_until, problems)
    _save_state(st)
    # ---- v2, moduli accessori e dashboard: ognuno isolato
    _soft("liquidazioni", collect_liquidations)
    try:
        report = evaluate(f)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] v2 non calcolato, dashboard non generata: {e!r}")
        st = _load_state()
        st["last_run"] = _now().isoformat(timespec="seconds")
        _save_state(st)
        return
    if wcur:
        report["weekly"] = wcur
    from importlib import import_module
    from .data import DATA_DIR

    def mod(name: str):   # import isolato: un modulo accessorio rotto non ferma il giro
        return import_module(f".{name}", __package__)
    report["levels"] = _soft("supporti e resistenze", lambda: mod("levels").compute(f))
    _soft("modulo su carta", paper.update, f)
    # mappa delle liquidazioni vicine e balene Hyperliquid (radar/liqmap.py)
    report["liqmap"] = _soft("mappa delle liquidazioni", lambda: mod("liqmap").update(report.get("levels"), DATA_DIR))
    _soft("trader seguito (esiti)", lambda: mod("xinbox").evaluate_all())
    report["liqsources"] = _soft("liquidazioni multi-exchange", lambda: mod("liqsources").summary())
    # ultima cascata di liquidazioni (24 ore) e prossime fasce dense: solo contesto (radar/liqcascade.py, lezione 92)
    report["cascade"] = _soft("cascata di liquidazioni", lambda: mod("liqcascade").update(report, DATA_DIR))
    # scout balene Hyperliquid: una volta al giorno (≥ 20 ore dall'ultimo giro) (radar/scout.py)
    try:   # come prima: None = scout non rifatto oggi; assente = errore (la dashboard legge l'ultimo file)
        report["scout"] = mod("scout").daily(DATA_DIR)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] scout balene non disponibile: {e!r}")
    # motore del book: foto, controlli, previsione 1h/4h (radar/orderbook.py)
    report["orderbook"] = _soft("book", lambda: mod("orderbook").update(DATA_DIR))
    report["news"] = _soft("notizie", fetch_news) or []
    report["calendar"] = _soft("calendario", fetch_calendar) or []
    report["banks"] = _soft("banche centrali", fetch_central_banks) or []   # prossime riunioni Fed (FOMC) e BCE
    for k in ("levels", "liqmap", "orderbook"):
        if report.get(k) is None:
            report.pop(k, None)
    # solo W3 (W2 + MACD robusta, dal 12/11/2026) (decisione dell'utente): alert di v2 spenti, RADAR_V2_ALERTS=1 per riaccenderli
    v2_on = os.environ.get("RADAR_V2_ALERTS", "0") == "1"
    events = diff_events(report)
    for ev in events if v2_on else []:
        telegram.send(telegram.format_event(ev, report))
    save_state(report)
    # controllo orario degli ordini (limit DCA, stop, target) sulle candele orarie di oggi
    st = _load_state()
    if v2_on:   # riepilogo giornaliero (testo di v2, come prima: spento con gli alert di v2)
        _soft("riepilogo giornaliero", daily_brief, report, st, _now(), data_until)
    try:
        ev, keys = intraday.check(report, st.get("intraday_keys", []))
        if not (ev and v2_on) or telegram.send(intraday.format_events(ev)):
            st["intraday_keys"] = keys
    except Exception as e:  # noqa: BLE001
        print(f"[radar] controllo orario v2 non eseguito: {e!r}")
    # fine del giro pesante: lo legge il controllo del workflow (daily.yml) per saltare un secondo giro entro 25 minuti
    st["last_run"] = _now().isoformat(timespec="seconds")
    _save_state(st)
    _soft("registro reale (collegamento al segnale)", journal.link, report)   # prezzi e orari di v2 e W3
    _soft("laboratorio", lab.build, report)
    out = render(report)
    print(f"[radar] {report['date']} score {report['score']:+.2f} · eventi v2: {[e['type'] for e in events]} · dashboard: {out}")


def backtest() -> None:
    f = build_features(load_all())
    p = Params()
    for mk in ("futures", "spot"):
        t = run(f, p, mk, BACKTEST_START)
        print(f"\n== {mk}\n{summary(t)}")
        print(t.drop(columns=[c for c in ("pending_entries", "next_tps", "mtm") if c in t]).to_string())


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if cmd == "daily":
        daily()
    elif cmd == "backtest":
        backtest()
    elif cmd == "test":
        import unittest
        r = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover("tests"))
        sys.exit(0 if r.wasSuccessful() else 1)
    elif cmd == "test-telegram":
        ok = telegram.send("<b>RADAR BTC</b> · test connessione riuscito ✅")
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
