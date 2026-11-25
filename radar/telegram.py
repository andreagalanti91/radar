"""Telegram di RadarSignal: formato comune dei messaggi (HTML ammesso da Telegram), riepilogo giornaliero "Oggi" e invio
(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).

Formato (approvato il 25/11/2026, stato/telegram-preview/PROPOSTA.md): riga 1 = cosa fare, in grassetto con un'icona di stato
(è l'anteprima della notifica); 3–6 righe "etichetta: valore"; dettagli in un <blockquote expandable>; link alla dashboard in
fondo ai messaggi di trading. Tag usati: b, i, code, a, blockquote expandable. I valori testuali dinamici passano da esc().
"""
from __future__ import annotations

import html
import os

import pandas as pd
import requests

DASH = "https://andreagalanti91.github.io/radar/"
ICON = {"long": "🟢", "short": "🔴"}
GG = ("lun", "mar", "mer", "gio", "ven", "sab", "dom")


# ---------------------------------------------------------------- formato comune

def esc(x) -> str:
    """Testo dinamico dentro un messaggio HTML di Telegram: escape di <, > e &."""
    return html.escape(str(x), quote=False)


def usd(x: float) -> str:
    return f"${x:,.0f}".replace(",", ".")


_usd = usd


def susd(x: float) -> str:
    """Dollari con segno vero: +$2.250 / −$4.745."""
    return ("+" if x >= 0 else "−") + usd(abs(x))


def pc(x: float, d: int = 2) -> str:
    return f"{x:+.{d}f}%".replace(".", ",").replace("-", "−")


def _pc(x: float, d: int = 1) -> str:
    return pc(x, d)


def num(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def sig(x: float) -> str:
    return f"{x:+.2f}σ".replace(".", ",").replace("-", "−")


def dm(day) -> str:
    """'2026-11-16' -> '16/11'."""
    try:
        return pd.Timestamp(day).strftime("%d/%m")
    except Exception:  # noqa: BLE001
        return "—"


_dm = dm


def gdm(day) -> str:
    """'2026-11-16' -> 'lun 16/11'."""
    try:
        t = pd.Timestamp(day)
        return f"{GG[t.dayofweek]} {t.strftime('%d/%m')}"
    except Exception:  # noqa: BLE001
        return "—"


def head(icon: str, asset: str | None, text: str) -> str:
    """Riga 1: '<icona> <b>ASSET · azione</b>'."""
    return f"{icon} <b>{asset + ' · ' if asset else ''}{text}</b>"


def details(*lines: str | None) -> str:
    """Dettagli secondari in una citazione espandibile (Telegram la mostra chiusa su ~3 righe)."""
    body = "\n".join(x for x in lines if x)
    return f"<blockquote expandable>{body}</blockquote>" if body else ""


def foot() -> str:
    return f'<a href="{DASH}">Apri la dashboard</a>'


def msg(*parts: str | None) -> str:
    return "\n".join(p for p in parts if p)


def money(pct: float, usd_: float) -> str:
    """'<b>+7,50%</b> (+$2.250)': % sul capitale dell'asset e dollari."""
    return f"<b>{pc(pct)}</b> ({susd(usd_)})"


def money_cap(cap: float, pct: float) -> str:
    return money(pct, (cap or 0) * pct / 100)


def side_up(side: str | None) -> str:
    return (side or "").upper()


def art(side: str | None, prep: str = "") -> str:
    """Articolo davanti a LONG/SHORT: 'il LONG', 'lo SHORT', 'dal LONG', 'dallo SHORT'."""
    a = ("dallo" if side == "short" else "dal") if prep == "da" else ("lo" if side == "short" else "il")
    return f"{a} {side_up(side)}"


def health_line(data_until: str | None, problems: list[str] | None, next_dec: str | None) -> str:
    """Riga di salute in fondo al riepilogo "Oggi" (il messaggio di salute separato parte solo con problemi)."""
    if problems:
        n = len(problems)
        return f"⚠️ {n} problem{'a' if n == 1 else 'i'} tecnic{'o' if n == 1 else 'i'}: " + esc("; ".join(problems))
    return ("✅ Sistema ok" + (f" · dati fino al {dm(data_until)}" if data_until else "")
            + (f" · decisione {gdm(next_dec)}" if next_dec else ""))


# ---------------------------------------------------------------- riepilogo giornaliero "Oggi"

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


def _levels_line(pv: dict) -> str | None:
    """R1 e S1 della mappa unica dei livelli (un prezzo se lo = hi, altrimenti la fascia)."""
    out = []
    for z in (pv.get("today") or {}).get("sr") or []:
        if z.get("name") in ("R1", "S1") and z.get("lo") is not None and z.get("hi") is not None:
            out.append(f"{z['name']} {usd(z['lo'])}" if z["lo"] == z["hi"] else f"{z['name']} {usd(z['lo'])}–{usd(z['hi'])}")
    return ("Livelli: " + " · ".join(out)) if out else None


def _btc_lines(pv: dict, wk: dict) -> tuple[list[str], str | None]:
    """Righe di BTC (posizione dalla pre-analisi, altrimenti dallo stato di W3.2) e stato per l'azione del giorno."""
    pb = pv.get("position_block")
    sun = pv.get("week_close_utc")
    st = wk.get("status")
    if pb and pb.get("entry_px") is not None:
        side = pb["side"]
        pnl = pb.get("pnl_usd")
        if pnl is None:
            pnl = (pb.get("capital_usd") or 0) * (pb.get("pnl_pct") or 0) / 100
        px = pb.get("price") or pv.get("price") or wk.get("price")
        out = [f"{ICON.get(side, '⚪')} <b>BTC {side}</b> · {money(pb['pnl_pct'], pnl)}",
               f"da {usd(pb['entry_px'])} ({dm(pb['entry_date'])})" + (f" · ora {usd(px)}" if px else "")]
        l3 = f"uscita {usd(pb['stop'])}"
        if pb.get("exit_ema21_threshold") is not None:
            l3 += f" · o domenica {'sotto' if side == 'long' else 'sopra'} {usd(pb['exit_ema21_threshold'])}"
        if "ATTIVA" in (pb.get("dist_rule") or ""):
            l3 += " · distribuzione attiva"
        return out + [l3], "aperto"
    if pb:   # segnale di domenica: ingresso all'apertura di lunedì, prezzo non ancora noto
        side = pb["side"]
        return [f"{ICON.get(side, '⚪')} <b>BTC</b>: nuovo {side}, entrata lunedì all'apertura",
                f"uscita in perdita {usd(pb['stop'])}"], "segnale"
    if st == "uscita":
        side = wk["side"]
        out = [f"{ICON.get(side, '⚪')} <b>BTC {side}</b> · {money_cap(wk.get('capital') or 0, wk['pnl_pct'])}",
               f"da {usd(wk['entry_px'])} ({dm(wk['entry'])}) · ora {usd(wk['price'])}",
               f"<b>Chiusura lunedì all'apertura</b> ({esc(_reason(wk.get('reason'), side))})"]
        return out, "uscita"
    if st == "aperto":
        side = wk["side"]
        return [f"{ICON.get(side, '⚪')} <b>BTC {side}</b> · {money_cap(wk.get('capital') or 0, wk['pnl_pct'])}",
                f"da {usd(wk['entry_px'])} ({dm(wk['entry'])}) · ora {usd(wk['price'])}",
                f"uscita {usd(wk['trail'])}"], "aperto"
    if st == "segnale":
        return [f"{ICON.get(wk['side'], '⚪')} <b>BTC</b>: nuovo {wk['side']}, entrata lunedì all'apertura"], "segnale"
    if not pv and not st:
        return ["⚪ <b>BTC</b>: segnale non calcolato in questo giro"], None
    px = pv.get("price") or wk.get("price")
    out = ["⚪ <b>BTC</b>: nessuna posizione" + (f" · {usd(px)}" if px else "")]
    if pv:
        sc = pv.get("scenarios") or []
        sh, lg = _signal_band(sc, "short"), _signal_band(sc, "long")
        if sh or lg:
            out.append(f"Dom {dm(sun)}: " + " · ".join(
                x for x in ((f"short se chiude {sh}" if sh else None), (f"long se chiude {lg}" if lg else None)) if x))
        else:
            out.append(f"Dom {dm(sun)}: nessuna chiusura dà un segnale con il flusso attuale")
    return out, "nessuno"


def _reason(r: str | None, side: str | None) -> str:
    if r == "ema":
        return f"settimana chiusa {'sotto' if side == 'long' else 'sopra'} la media a 21 settimane"
    return {"trail": "uscita automatica", "stop": "stop iniziale",
            "dist": "distribuzione (funding e flusso dei futures)"}.get(r, r or "")


def _asset_lines(w: dict) -> tuple[list[str], str | None]:
    """Righe di un asset di W3.2 diverso da BTC (oggi ETH), dal suo stato e sul suo capitale."""
    a = w.get("asset") or "ETH"
    st = w.get("status")
    if st in ("aperto", "uscita"):
        side = w["side"]
        out = [f"{ICON.get(side, '⚪')} <b>{a} {side}</b> · {money_cap(w.get('capital') or 0, w.get('pnl_pct') or 0)}",
               f"da {usd(w['entry_px'])} ({dm(w['entry'])}) · ora {usd(w['price'])}"]
        out.append("<b>Chiusura lunedì all'apertura</b>" if st == "uscita" else f"uscita {usd(w['trail'])}")
        return out, st
    if st == "segnale":
        return [f"{ICON.get(w['side'], '⚪')} <b>{a}</b>: nuovo {w['side']}, entrata lunedì all'apertura"], st
    return [f"⚪ <b>{a}</b>: nessuna posizione" + (f" · {usd(w['price'])}" if w.get("price") else "")], "nessuno"


def _todo(states: list[tuple[str, str | None, str | None]]) -> str:
    """Azione del giorno per la riga 1 del riepilogo: [(asset, stato, lato)]."""
    acts = [f"entra {sd} su {a} lunedì" if st == "segnale" else f"chiudi {a} lunedì"
            for a, st, sd in states if st in ("segnale", "uscita")]
    if acts:
        return "; ".join(acts)
    if any(st == "aperto" for _, st, _ in states):
        return "nessuna azione"
    return "fuori dal mercato, nessuna azione" if states and all(st == "nessuno" for _, st, _ in states) else "nessuna azione"


def today_brief(report: dict, day: str | None = None, health: str | None = None) -> str:
    """Riepilogo giornaliero "Oggi": riga 1 con l'azione del giorno, 2–3 righe per asset di W3.2 (BTC, poi ETH), contesto della
    pre-analisi e mercati (radar/macro.py) nei dettagli, riga di salute (`health`, telegram.health_line) e link. Mai eccezioni."""
    report = report or {}
    pv, wk = report.get("preview") or {}, report.get("weekly") or {}
    eth = report.get("weekly_eth")
    states: list = []
    try:
        lines, st = _btc_lines(pv, wk)
        side = (pv.get("position_block") or {}).get("side") or wk.get("side")
        states.append(("BTC", st, side))
    except Exception as e:  # noqa: BLE001
        print(f"[telegram] riepilogo incompleto: {e!r}")
        lines = ["Dati del riepilogo incompleti in questo giro."]
    if eth:
        try:   # altri asset di W3.2 (report["weekly_eth"]): subito dopo BTC
            el, est = _asset_lines(eth)
            lines += el
            states.append((eth.get("asset") or "ETH", est, eth.get("side")))
        except Exception as e:  # noqa: BLE001
            print(f"[telegram] righe ETH non composte: {e!r}")
    ctx: list[str] = []
    try:
        ctx = [esc(x) for x in _ctx_lines(pv.get("today"))]
    except Exception as e:  # noqa: BLE001
        print(f"[telegram] contesto non composto: {e!r}")
    try:   # chiusura multi-asset (radar/macro.py): una riga "Mercati: …" e al massimo 2 flag da rivedere
        from .macro import telegram_lines
        mk = [esc(x) for x in telegram_lines(report.get("macro"))]
    except Exception as e:  # noqa: BLE001
        print(f"[telegram] riga mercati non composta: {e!r}")
        mk = []
    try:
        lv = _levels_line(pv)
    except Exception:  # noqa: BLE001
        lv = None
    data_day = wk.get("date") or report.get("date")
    note = (f"Prezzi alla chiusura del {dm(data_day)}. " if data_day else "") + "Contesto, non segnale: decide W3.2."
    top = head("📋", None, f"Oggi {dm(day)} · {_todo(states)}" if day else f"Oggi · {_todo(states)}")
    return msg(top, *lines, details(*ctx, *mk, lv, note), health, foot())


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


# ---------------------------------------------------------------- avvisi tecnici del giro (radar/cli.py)

def format_run_stopped(err: str) -> str:
    """Nessuna fonte di W3.2 con dati né cache: il giro si ferma."""
    return msg(head("⚠️", None, "Problema tecnico: giro interrotto"),
               f"Dati di W3.2 assenti ({esc(err)}): nessun segnale calcolato in questo giro.")


def format_w3_error(err: str, asset: str = "BTC") -> str:
    return msg(head("⚠️", asset, "Segnale non calcolato in questo giro"), f"<code>{esc(err)}</code>",
               "Il prossimo giro riprova; posizione e livelli comunicati restano validi.")


def format_test() -> str:
    return head("✅", None, "Radar · connessione riuscita")


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
