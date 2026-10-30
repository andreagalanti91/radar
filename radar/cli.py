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
from .strategy import Params  # noqa: E402


def daily() -> None:
    report = evaluate(build_features(update_all()))
    events = diff_events(report)
    for ev in events:
        telegram.send(telegram.format_event(ev, report))
    if os.environ.get("RADAR_DAILY_BRIEF", "1") == "1":
        telegram.send(telegram.daily_brief(report))
    save_state(report)
    out = render(report)
    print(f"[radar] {report['date']} score {report['score']:+.2f} · eventi: {[e['type'] for e in events]} · dashboard: {out}")


def backtest() -> None:
    f = build_features(load_all())
    p = Params()
    for mk in ("futures", "spot"):
        t = run(f, p, mk, BACKTEST_START)
        print(f"\n== {mk}\n{summary(t)}")
        print(t.drop(columns=[c for c in ("pending_entries", "next_tps") if c in t]).to_string())


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if cmd == "daily":
        daily()
    elif cmd == "backtest":
        backtest()
    elif cmd == "test-telegram":
        ok = telegram.send("<b>RADAR BTC</b> · test connessione riuscito ✅")
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
