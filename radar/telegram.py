"""Invio alert su Telegram (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)."""
from __future__ import annotations

import os

import requests


def _usd(x: float) -> str:
    return f"${x:,.0f}".replace(",", ".")


def format_event(ev: dict, report: dict) -> str:
    t = ev["type"]
    if t == "signal":
        p = ev["plan"]
        side = "🟢 LONG" if p["side"] == "long" else "🔴 SHORT"
        mk = "spot + futures" if p["side"] == "long" else "solo futures"
        lines = [f"<b>RADAR BTC · NUOVO SEGNALE {side}</b> ({mk})",
                 f"Setup: <b>{p['setup']}</b> · {p['setup_label']}",
                 f"Chiusura {p['date']}: {_usd(p['price'])} · score flusso {p['score']:+.2f}", "",
                 "<b>Entrata DCA</b>"]
        lines += [f"  {int(e['weight']*100)}% @ {_usd(e['price'])}" + (" (open domani)" if i == 0 else " (limit, 7 gg)")
                  for i, e in enumerate(p["entries"])]
        lines += [f"  Prezzo medio se completa: {_usd(p['avg_entry_if_full'])}",
                  f"<b>Stop</b>: {_usd(p['stop'])} (rischio ~{p['risk_pct_full']}% sul medio)", "",
                  "<b>Uscita DCA</b> (sul medio a DCA completa; il bot ricalcola i target a ogni tranche)"]
        lines += [f"  {int(tp['weight']*100)}% @ {_usd(tp['price'])}" for tp in p["take_profits"]]
        lines += [f"  {int(p['trail_weight']*100)}% in trailing a {p['trail_atr']} ATR · max {p['max_hold_days']} gg",
                  "Dopo il TP1 lo stop va a pareggio.", "",
                  f"<b>Leva</b> futures consigliata {p['leverage']:g}x: perdita massima ~{p['risk_pct_capital_at_leverage']}% "
                  f"del capitale allocato se tutte le tranche si riempiono e scatta lo stop. Usa margine isolato."]
        return "\n".join(lines)
    tr, market = ev["trade"], ev["market"]
    if t == "dca_fill":
        return (f"<b>RADAR BTC · DCA eseguito</b> ({market})\nTranche riempite: {tr['tranches']}/3 · "
                f"prezzo medio {_usd(tr['avg_entry'])} · stop {_usd(tr['stop'])}")
    if t == "tp_hit":
        nxt = ", ".join(_usd(x) for x in tr.get("next_tps", [])) or "trailing"
        return (f"<b>RADAR BTC · Take profit {tr['tp_hit']} raggiunto</b> ({market})\n"
                f"Stop ora a {_usd(tr['stop'])} · prossimi target: {nxt} · residuo {tr['remaining']*100:.0f}%")
    if t == "closed":
        emoji = "✅" if tr["pnl_pct_capital"] > 0 else "❌"
        return (f"<b>RADAR BTC · Trade chiuso {emoji}</b> ({market}, {tr['side']})\n"
                f"Uscita: {tr['exit']} · {tr['days']} gg · PnL {tr['pnl_pct_invested']:+.2f}% sull'investito")
    return str(ev)


def daily_brief(report: dict) -> str:
    c = {k: (0.0 if v is None else v) for k, v in report["components"].items()}
    ot = report["open_trade"]["futures"]
    pos = (f"Trade {ot['side']} aperto dal {ot['signal_date']} · medio {_usd(ot['avg_entry'])} · stop {_usd(ot['stop'])}"
           if ot else "Nessun trade aperto")
    active = [x["setup"] for x in report.get("checklist", []) if x["active"]]
    return (f"<b>RADAR BTC · {report['date']}</b>\nPrezzo {_usd(report['price'])} · score flusso {report['score']:+.2f} "
            f"(soglia ±{report['threshold']}) · regime {report['regime']}\n"
            f"Setup attivi: {', '.join(active) if active else 'nessuno'}\n"
            f"CVD perp z {c['perp_flow_z']:+.2f} · L/S retail z {c['retail_ls_z']:+.2f} · "
            f"funding {c['funding7_annual_pct']:.1f}%/anno · F&amp;G {c['fng']:.0f}\n{pos}")


def send(text: str) -> bool:
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("[telegram] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID non impostati, messaggio non inviato:\n" + text)
        return False
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
                      timeout=20)
    if not r.ok:
        print(f"[telegram] errore {r.status_code}: {r.text}")
    return r.ok
