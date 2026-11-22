"""Invio alert su Telegram (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID). Messaggi della strategia v2."""
from __future__ import annotations

import os

import pandas as pd
import requests


def _usd(x: float) -> str:
    return f"${x:,.0f}".replace(",", ".")


def _when(ts: str) -> str:
    """'2026-11-02 08:00:00' -> '02/11 08:00 UTC'."""
    t = pd.Timestamp(ts)
    return t.strftime("%d/%m %H:%M UTC")


def _side(side: str) -> str:
    return "🟢 LONG" if side == "long" else "🔴 SHORT"


def _plan_lines(v: dict) -> list[str]:
    """Piano completo di un ingresso v2: livelli, size in dollari, leva, stop, TP, tempo."""
    p, L = v["plan"], v["side"] == "long"
    return [
        f"<b>Ingresso 40%</b> a mercato ~{_usd(p['entry'])}: {_usd(p['t1_usd'])} di posizione = {p['t1_btc']:.4f} BTC",
        f"<b>Limit 60%</b> a {_usd(p['limit'])} (−0,5 ATR, "
        + (f"valido fino al {_when(v['limit_expiry'])}" if v.get("limit_expiry") else "già eseguito")
        + f"): {_usd(p['t2_usd'])} = {p['t2_btc']:.4f} BTC",
        f"<b>Stop</b> {_usd(p['stop'])} (1 ATR dall'ingresso) per entrambe le parti",
        f"<b>Take profit</b> unico +1R dal medio: {_usd(p.get('tp', p['tp_first']))} con il solo 40%, "
        f"{_usd(p['tp_full'])} se si riempie anche il limit",
        f"<b>Uscita a tempo</b> entro il {_when(v['time_exit'])} (14 giorni)",
        "",
        f"<b>Su {_usd(p['capital'])}</b>: rischio {p['risk']:.2f}% = perdita allo stop ~{_usd(p['loss_usd'])} a DCA completa · "
        f"guadagno al TP ~{_usd(p['gain_usd'])}",
        f"<b>Leva</b> {p['lev']:.2f}x (posizione totale {_usd(p['notional'])}, margine isolato) · "
        f"delta taker {v.get('dt', 0):+.3f} ({'spot+perp' if v.get('perp') else 'solo spot'})"
        + (" · long sotto la SMA 40 settimane: size × 0,6" if L and v.get("below_sma40w") else ""),
    ]


def format_event(ev: dict, report: dict | None = None) -> str:
    t = ev["type"]
    if t == "signal":
        v = ev["v2"]
        L = v["side"] == "long"
        lines = [f"<b>RADAR SIGNAL BTC · NUOVO SEGNALE {_side(v['side'])}</b> · in attesa di conferma 4h",
                 f"Setup: <b>{v['setup']}</b> · {v.get('setup_label', '')}",
                 f"Perché: {v.get('why', '')}"]
        if v["status"] == "conferma":
            p = v["plan"]
            lines += ["",
                      f"<b>Ingresso solo se una candela 4h chiude {'sopra' if L else 'sotto'} {_usd(v['trigger'])}</b> "
                      f"(soglia attuale: {'massimo' if L else 'minimo'} delle 2 candele 4h precedenti, si aggiorna a ogni barra) "
                      f"entro il {_when(v['deadline'])}. Altrimenti il segnale scade.",
                      "",
                      "Piano indicativo se la conferma arriva alla soglia:",
                      f"  40% ~{_usd(p['entry'])} · 60% limit {_usd(p['limit'])} · stop {_usd(p['stop'])} · TP {_usd(p['tp_full'])}",
                      f"  rischio {p['risk_lo']:.1f}–{p['risk_hi']:.1f}% del capitale (dipende dal delta taker della barra di conferma), "
                      f"leva {p['lev_lo']:.1f}–{p['lev_hi']:.1f}x",
                      "Riceverai il piano completo in dollari alla conferma."]
        return "\n".join(lines)
    if t == "entry":
        v = ev["v2"]
        if "plan" not in v:   # ingresso e uscita tra due controlli: solo il riepilogo
            return (f"<b>RADAR SIGNAL BTC · INGRESSO CONFERMATO {_side(v['side'])}</b>\n"
                    f"Ingresso {_usd(v['entry'])} alle {_when(v['entry_time'])} · stop {_usd(v['stop'])} · TP {_usd(v['tp'])}")
        when = "ora, all'apertura 4h delle " + _when(v["entry_time"]) if v["status"] == "ingresso" else _when(v["entry_time"])
        return "\n".join([f"<b>RADAR SIGNAL BTC · INGRESSO CONFERMATO {_side(v['side'])}</b> (futures)",
                          f"Segnale {v['signal_date']} · setup {v['setup']} · candela 4h chiusa "
                          f"{'sopra' if v['side'] == 'long' else 'sotto'} la soglia · ingresso {when}", ""]
                         + _plan_lines(v))
    if t == "dca_fill":
        v = ev["v2"]
        p = v["plan"]
        return (f"<b>RADAR SIGNAL BTC · Limit DCA eseguito</b> ({v['side']})\n"
                f"60% a {_usd(p['limit'])} · prezzo medio {_usd(v['avg'])} · stop {_usd(v['stop'])} · "
                f"nuovo TP {_usd(v['tp'])} (+1R dal medio)")
    if t in ("tp", "stop", "time"):
        tr = ev["trade"]
        head = {"tp": "Take profit raggiunto ✅", "stop": "Stop loss ❌", "time": "Uscita a tempo (14 giorni)"}[t]
        if t == "time":
            head += " ✅" if tr["pnl_pct"] > 0 else " ❌"
        return (f"<b>RADAR SIGNAL BTC · {head}</b> ({tr['side']}, segnale {tr['signal_date']})\n"
                f"Uscita {_usd(tr['exit_px'])} · medio {_usd(tr['avg'])} · DCA {tr['fills']}/2 · leva {tr['N']:.2f}x\n"
                f"Risultato {tr['pnl_pct']:+.2f}% sul capitale ({tr['pnl_pct_invested']:+.2f}% sul prezzo)")
    if t == "expired":
        v = ev["v2"]
        return (f"<b>RADAR SIGNAL BTC · Segnale scaduto</b> ({v['side']}, {v['signal_date']})\n"
                f"Nessuna chiusura 4h oltre la soglia entro 72 ore: nessun ingresso.")
    return str(ev)


def _status_line(v: dict) -> str:
    if v["status"] == "conferma":
        return (f"Segnale {v['side']} del {v['signal_date']} in attesa di conferma: chiusura 4h "
                f"{'sopra' if v['side'] == 'long' else 'sotto'} {_usd(v['trigger'])} entro il {_when(v['deadline'])}")
    if v["status"] == "ingresso":
        return f"Ingresso {v['side']} confermato: a mercato ~{_usd(v['plan']['entry'])}, stop {_usd(v['plan']['stop'])}"
    if v["status"] == "aperto":
        p = v["plan"]
        return (f"Trade {v['side']} aperto dal {_when(v['entry_time'])} · ingresso {_usd(v['entry'])} · DCA {v['fills']}/2 · "
                f"stop {_usd(v['stop'])} · TP {_usd(v['tp'])} · leva {p['lev']:.2f}x · {v['pnl_pct_invested']:+.2f}% sul prezzo"
                + ("" if v["filled"][1] else f" · limit {_usd(p['limit'])} attivo"))
    return "Nessun segnale v2 attivo"


def _weekly_line(w: dict) -> str:
    if w["status"] in ("aperto", "uscita"):
        return (f"{w['side']} dal {w['entry']} a {_usd(w['entry_px'])} ({w['market']}) · {w['move_pct']:+.2f}% · "
                f"trailing {_usd(w['trail'])}" + (" · uscita all'apertura di lunedì" if w["status"] == "uscita" else ""))
    if w["status"] == "segnale":
        return f"segnale {w['side']} alla chiusura del {w['signal_date']}, ingresso all'apertura di lunedì"
    return f"nessuna posizione · regime settimanale {w['regime']}"


def daily_brief(report: dict) -> str:
    c = {k: (0.0 if v is None else v) for k, v in report["components"].items()}
    active = [x["setup"] for x in report.get("checklist", []) if x["active"]]
    T = report["stats"]["periods"]["Totale"]
    return (f"<b>RADAR SIGNAL BTC · {report['date']}</b>\nPrezzo {_usd(report['price'])} · score flusso {report['score']:+.2f} "
            f"(soglia ±{report['threshold']}) · regime {report['regime']}\n"
            f"Setup attivi: {', '.join(active) if active else 'nessuno'}\n"
            f"<b>v2</b>: {_status_line(report['v2'])}\n"
            + (f"<b>Settimanale W3</b>: {_weekly_line(report['weekly'])}\n" if report.get("weekly") else "")
            + (f"Regione 7g · acquisto {_usd(report['zone']['buy'][0])}–{_usd(report['zone']['buy'][1])} "
               f"(toccata {report['zone']['stats']['buy_zone_touch_%']:.0f}% delle volte) · vendita "
               f"{_usd(report['zone']['sell'][0])}–{_usd(report['zone']['sell'][1])}\n" if report.get("zone") else "")
            + f"CVD perp z {c['perp_flow_z']:+.2f} · L/S retail z {c['retail_ls_z']:+.2f} · "
            f"funding {c['funding7_annual_pct']:.1f}%/anno · F&amp;G {c['fng']:.0f}\n"
            f"Storico v2 dal 2022-03: {T['trades']} trade · WR {T['win_rate']}% · {T['total_return_%']:+.1f}% · "
            f"DD giornaliero {T['max_dd_%']}% (rischio base {report['params']['risk'] * 100:.2f}%)")


def _pc(x: float, d: int = 1) -> str:
    return f"{x:+.{d}f}%".replace(".", ",").replace("-", "−")


def _dm(day: str | None) -> str:
    try:
        return pd.Timestamp(day).strftime("%d/%m")
    except Exception:  # noqa: BLE001
        return "—"


def _signal_band(sc: list[dict], side: str) -> str | None:
    """Fasce di chiusura settimanale che darebbero il segnale `side` (scenari della pre-analisi), in parole."""
    out = []
    for b in sc or []:
        if b.get("outcome") != side:
            continue
        lo, hi = b.get("lo"), b.get("hi")
        out.append(f"sotto {_usd(hi)}" if lo is None and hi is not None else f"sopra {_usd(lo)}" if hi is None and lo is not None
                   else f"fra {_usd(lo)} e {_usd(hi)}" if lo is not None else "a qualsiasi prezzo")
    return " o ".join(out) if out else None


def _w3_lines(pv: dict, wk: dict | None) -> list[str]:
    """Due righe su W3: posizione e PnL; stop/trailing e soglia d'uscita (in posizione) o soglia del segnale (flat)."""
    pb = pv.get("position_block")
    sun = _dm(pv.get("week_close_utc"))
    if pb:
        side = pb["side"].upper()
        if pb.get("entry_px") is None:
            l1 = f"<b>W3</b>: {side} in apertura il {_dm(pb['entry_date'])} (ingresso all'apertura del lunedì)"
        else:
            l1 = (f"<b>W3</b>: {side} dal {_dm(pb['entry_date'])} a {_usd(pb['entry_px'])} · {_pc(pb['pnl_pct'], 2)} "
                  f"({'+' if pb['pnl_usd'] >= 0 else '−'}{_usd(abs(pb['pnl_usd']))} su {_usd(pb['capital_usd'])})")
        l2 = (f"Stop/trailing {_usd(pb['stop'])} ({_pc(pb['stop_dist_pct'])}) · uscita se la settimana chiude "
              f"{'sotto' if pb['side'] == 'long' else 'sopra'} {_usd(pb['exit_ema21_threshold'])} (dom {sun})")
        if "ATTIVA" in (pb.get("dist_rule") or ""):
            l2 += " · distribuzione attiva"
        return [l1, l2]
    if wk and wk.get("status") == "uscita":
        return [f"<b>W3</b>: uscita {wk.get('side', '')} all'apertura di lunedì ({wk.get('reason', '')})",
                "Da lunedì nessuna posizione: si attende il prossimo segnale"]
    sc = pv.get("scenarios") or []
    sh, lg = _signal_band(sc, "short"), _signal_band(sc, "long")
    if sh or lg:
        l2 = "Segnale alla chiusura di dom " + sun + ": " + " · ".join(
            x for x in ((f"short se chiude {sh}" if sh else None), (f"long se chiude {lg}" if lg else None)) if x)
    else:
        l2 = f"Nessuna chiusura di dom {sun} dà un segnale con il flusso attuale"
    return ["<b>W3</b>: nessuna posizione", l2]


def _ctx_lines(td: dict | None) -> list[str]:
    """2–3 righe di contesto dalla sezione Oggi della pre-analisi."""
    if not td:
        return []
    it = {x["key"]: x for x in td.get("items") or []}
    out = []
    fl = [f"{lab} {it[k]['value']} ({it[k]['read'].split(': ', 1)[-1].split(';')[0].removeprefix(lab + ' ')})"
          for k, lab in (("pf14z", "perp"), ("sf14z", "spot")) if k in it]
    if fl:
        out.append("Flussi: " + " · ".join(fl))
    dv = [f"{lab} {it[k]['value'].split(' · ')[-1]}" for k, lab in (("funding", "funding"), ("oi7", "OI 7g")) if k in it]
    if "liq24h" in it:
        dv.append(f"liquidazioni 24h {it['liq24h']['value'].replace(' · ', ' / ')}")
    if dv:
        out.append("Derivati: " + " · ".join(dv))
    an = td.get("analog")
    if an:
        out.append(f"Storico simile ({an['label'].split(',')[0]}, {an['n']} casi): {an['p7']:.0f}% di rialzo a 7 g, "
                   f"{an['p30']:.0f}% a 30 g · non significativo")
    return out[:3]


def today_brief(report: dict, day: str | None = None) -> str:
    """Riepilogo giornaliero "Oggi" (al massimo 8 righe, 11 con i mercati): prezzo, W3, 2–3 righe di contesto, riga
    "Mercati" e fino a 2 flag (report["macro"], radar/macro.py), nota. Mai eccezioni."""
    report = report or {}
    pv, wk = report.get("preview") or {}, report.get("weekly")
    head = "<b>RADAR SIGNAL BTC · Oggi</b>" + (f" · {_dm(day)}" if day else "")
    try:
        price = pv.get("price") or (wk or {}).get("price") or report.get("price")
        data_day = (wk or {}).get("date") or report.get("date")
        l_px = (f"Prezzo {_usd(price)}" if price else "Prezzo n.d.") + (f" (chiusura {_dm(data_day)})" if data_day else "")
        sr = (pv.get("today") or {}).get("sr") or []
        r1 = next((z for z in sr if z["name"] == "R1"), None)
        s1 = next((z for z in sr if z["name"] == "S1"), None)
        for z, tag in ((r1, "R1"), (s1, "S1")):
            if z and z.get("lo") is not None and z.get("hi") is not None:
                l_px += f" · {tag} {_usd(z['lo'])}–{_usd(z['hi'])}"
        if pv:
            w3 = _w3_lines(pv, wk)
        elif wk:
            try:
                w3 = [f"<b>W3</b>: {_weekly_line(wk)}"]
            except Exception:  # noqa: BLE001
                w3 = [f"<b>W3</b>: {wk.get('status', 'stato non disponibile')} {wk.get('side', '')}".rstrip()]
        else:
            w3 = ["<b>W3</b>: non calcolato in questo giro"]
        lines = [head, l_px] + w3 + _ctx_lines(pv.get("today"))
    except Exception as e:  # noqa: BLE001
        print(f"[telegram] riepilogo incompleto: {e!r}")
        lines = [head, "Dati del riepilogo incompleti in questo giro."]
    try:   # chiusura multi-asset (radar/macro.py): una riga "Mercati: …" e al massimo 2 flag da rivedere
        from .macro import telegram_lines
        mk = telegram_lines(report.get("macro"))
    except Exception as e:  # noqa: BLE001
        print(f"[telegram] riga mercati non composta: {e!r}")
        mk = []
    return "\n".join(lines[:7] + mk + ["Contesto, non segnale: decide W3."])


def send(text: str):
    """Invia un messaggio. Restituisce il message_id di Telegram (o True) se l'invio è confermato, False altrimenti:
    chi chiama marca l'evento come inviato SOLO con un valore vero. Mai eccezioni (rete, timeout): False."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("[telegram] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID non impostati, messaggio non inviato:\n" + text)
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
                          timeout=20)
    except requests.RequestException as e:   # il messaggio d'errore non contiene l'URL con il token
        print(f"[telegram] errore di rete: {type(e).__name__}")
        return False
    if not r.ok:
        print(f"[telegram] errore {r.status_code}: {r.text[:300]}")
        return False
    try:
        body = r.json()
    except ValueError:
        body = {}
    if body.get("ok") is False:
        print(f"[telegram] risposta non ok: {str(body)[:300]}")
        return False
    mid = (body.get("result") or {}).get("message_id")
    print(f"[telegram] ok id={mid}")
    return mid or True
