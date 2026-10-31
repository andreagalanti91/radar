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
from .data import load_all, update_all  # noqa: E402
from .features import build_features  # noqa: E402
from .live import BACKTEST_START, diff_events, evaluate, save_state  # noqa: E402
from .news import fetch_calendar, fetch_news  # noqa: E402
from . import intraday  # noqa: E402
from . import paper  # noqa: E402
from . import lab  # noqa: E402
from . import weekly  # noqa: E402
import pandas as pd  # noqa: E402
from .liquidations import collect as collect_liquidations  # noqa: E402
import json  # noqa: E402
from .live import STATE_FILE  # noqa: E402
from .strategy import Params  # noqa: E402


def daily() -> None:
    d = update_all()
    f = build_features(d)
    report = evaluate(f)
    try:   # segnale settimanale W2: un errore qui non deve fermare v2
        report["weekly"] = weekly.evaluate(f)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] settimanale non calcolato: {e!r}")
    try:   # modulo su carta (H2 e v2): un errore qui non deve fermare alert e dashboard
        paper.update(f)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] modulo su carta non aggiornato: {e!r}")
    st0 = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    stale = [k for k in ("spot", "perp", "funding", "metrics") if (pd.Timestamp.utcnow().tz_localize(None) - d[k].index.max()).days > 2]
    if stale and st0.get("stale_alert") != str(pd.Timestamp.utcnow().date()):
        telegram.send(f"<b>RADAR SIGNAL BTC · Dati non aggiornati</b>\nFonti ferme da oltre 36 ore: {', '.join(stale)}. "
                      f"I segnali potrebbero essere in ritardo finché le fonti non tornano disponibili.")
        st0["stale_alert"] = str(pd.Timestamp.utcnow().date())
        STATE_FILE.write_text(json.dumps(st0, indent=2, default=str))
    collect_liquidations()
    report["news"], report["calendar"] = fetch_news(), fetch_calendar()
    events = diff_events(report)
    for ev in events:
        telegram.send(telegram.format_event(ev, report))
    if os.environ.get("RADAR_DAILY_BRIEF", "1") == "1":
        telegram.send(telegram.daily_brief(report))
    save_state(report)
    # controllo orario degli ordini (limit DCA, stop, target) sulle candele orarie di oggi
    st = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    ev, st["intraday_keys"] = intraday.check(report, st.get("intraday_keys", []))
    if ev:
        telegram.send(intraday.format_events(ev))
    if report.get("weekly"):
        try:   # eventi del settimanale (dedupe in state.json, chiave "weekly") e controllo orario del trailing
            wev, st["weekly"] = weekly.diff_events(report["weekly"], st.get("weekly"))
            for e in wev:
                telegram.send(weekly.format_event(e))
            hev, st["weekly_intraday_keys"] = weekly.check_intraday(report["weekly"], st.get("weekly_intraday_keys", []))
            if hev:
                telegram.send(weekly.format_intraday(hev))
        except Exception as e:  # noqa: BLE001
            print(f"[radar] eventi settimanali non inviati: {e!r}")
    STATE_FILE.write_text(json.dumps(st, indent=2, default=str))
    try:   # Laboratorio (v2 e candidati della ricerca): un errore qui non deve fermare la dashboard
        lab.build(report)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] laboratorio non aggiornato: {e!r}")
    out = render(report)
    print(f"[radar] {report['date']} score {report['score']:+.2f} · eventi: {[e['type'] for e in events]} · dashboard: {out}")


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
