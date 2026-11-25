"""PROPOSTA (solo anteprima, non collegata al bot): nuovi testi Telegram di RadarSignal.

Stesse informazioni operative dei messaggi di oggi, riordinate: riga 1 = cosa fare (è l'anteprima della notifica),
3–6 righe di numeri, dettagli in un blockquote espandibile, link alla dashboard. HTML ammesso da Telegram soltanto.
Le funzioni prendono gli stessi argomenti di quelle attuali (radar/weekly.py, radar/telegram.py, radar/cli.py, guard,
coherence) così che l'implementazione sia una sostituzione dei corpi, senza toccare logica ed eventi.
"""
from __future__ import annotations

import pandas as pd

DASH = "https://andreagalanti91.github.io/radar/"
ICON = {"long": "🟢", "short": "🔴"}
REASON_PLAIN = {"trail": "uscita automatica", "stop": "stop iniziale",
                "ema": "chiusura settimanale oltre la media a 21 settimane", "dist": "distribuzione (funding e flusso dei futures)"}


# ---------------------------------------------------------------- formati di base

def usd(x: float) -> str:
    return f"${x:,.0f}".replace(",", ".")


def susd(x: float) -> str:
    """Dollari con segno: +$2.250 / −$4.745."""
    return ("+" if x >= 0 else "−") + usd(abs(x))


def pc(x: float, d: int = 2) -> str:
    return f"{x:+.{d}f}%".replace(".", ",").replace("-", "−")


def num(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def sig(x: float) -> str:
    return f"{x:+.2f}σ".replace(".", ",").replace("-", "−")


def dm(day) -> str:
    try:
        return pd.Timestamp(day).strftime("%d/%m")
    except Exception:  # noqa: BLE001
        return "—"


GG = ("lun", "mar", "mer", "gio", "ven", "sab", "dom")


def gdm(day) -> str:
    """'2026-11-16' -> 'lun 16/11'."""
    try:
        t = pd.Timestamp(day)
        return f"{GG[t.dayofweek]} {t.strftime('%d/%m')}"
    except Exception:  # noqa: BLE001
        return "—"


def head(icon: str, asset: str | None, text: str) -> str:
    return f"{icon} <b>{asset + ' · ' if asset else ''}{text}</b>"


def details(*lines: str) -> str:
    """Dettagli secondari: blockquote espandibile (Telegram lo mostra chiuso su ~3 righe, si apre con un tocco)."""
    body = "\n".join(x for x in lines if x)
    return f"<blockquote expandable>{body}</blockquote>" if body else ""


def foot() -> str:
    return f'<a href="{DASH}">Apri la dashboard</a>'


def msg(*parts: str) -> str:
    return "\n".join(p for p in parts if p is not None and p != "")


def money(cap: float, pct: float) -> str:
    """'+7,50% (+$2.250)' sul capitale dell'asset."""
    return f"<b>{pc(pct)}</b> ({susd(cap * pct / 100)})"


def _side_up(side: str) -> str:
    return (side or "").upper()


def art(side: str, prep: str = "") -> str:
    """Articolo davanti a LONG/SHORT: 'il LONG', 'lo SHORT', 'dal LONG', 'dallo SHORT'."""
    a = "lo" if side == "short" else "il"
    if prep == "da":
        a = "dallo" if side == "short" else "dal"
    return f"{a} {_side_up(side)}"


def reason(r: str, side: str) -> str:
    if r == "ema":
        return f"settimana chiusa {'sotto' if side == 'long' else 'sopra'} la media a 21 settimane"
    return REASON_PLAIN.get(r, r)


def _exit_rules(side: str, trail_dist: float | None, ema21: float | None) -> str:
    L = side == "long"
    return ("<b>Come si esce</b> (alla prima delle tre): "
            + (f"uscita automatica a {usd(trail_dist)} dalla miglior chiusura giornaliera, si sposta solo a tuo favore "
               "e ti avviso a ogni passo; " if trail_dist else "uscita automatica (si sposta solo a tuo favore); ")
            + f"chiusura settimanale {'sotto' if L else 'sopra'} la media a 21 settimane"
            + (f" ({usd(ema21)})" if ema21 else "") + "; "
            + "distribuzione (funding medio 7 giorni "
            + ("&gt; 0,09%/giorno con flusso dei futures negativo)." if L else "&lt; −0,03%/giorno con flusso dei futures positivo)."))


def _mkt(market: str, expo: float, cap: float | None = None) -> str:
    base = (f"spot, esposizione {num(expo)}x, niente leva né funding" if market == "spot"
            else f"perp, margine isolato, esposizione {num(expo)}x del capitale")
    return f"<b>Mercato</b>: {base}" + (f" del capitale ({usd(cap)})" if cap else "") + "."


def _if_hit(w: dict, label: str = "Se scatta", icon: bool = True) -> str | None:
    """Esito se scatta ora l'uscita automatica (w["uscite"]["trail"], già calcolato per la dashboard)."""
    t = ((w.get("uscite") or {}).get("trail")) or {}
    if t.get("usd") is None:
        return None
    ic = ("🎯 " if t["usd"] > 0 else "🛑 ") if icon else ""
    return f"{ic}{label}: <b>{pc(t['pct_cap'])}</b> ({susd(t['usd'])})"


# ---------------------------------------------------------------- eventi W3.2 (sostituisce weekly.format_event)

W3_NOTE = {"BTC": "Operazioni rare (13 dal 2021, circa 2 l'anno) e lunghe · calo massimo storico −21% · al massimo il 25% "
                  "del capitale a rischio allo stop iniziale.",
           "ETH": "Operazioni rare (15 dal 2021, circa 2–3 l'anno) · calo massimo storico −27,5% · 60% dei trade in "
                  "profitto · al massimo il 25% della quota ETH a rischio allo stop iniziale."}


def format_event(ev: dict) -> str:
    t, w = ev["type"], ev["w"]
    a = w.get("asset") or "BTC"
    side = ev.get("side") or w.get("side") or ev.get("trade", {}).get("side", "")
    S, ic = _side_up(side), ICON.get(side, "⚪")
    L = side == "long"

    if t == "w_signal" and w["status"] == "segnale":
        p = w["plan"]
        sp = p["stop_pct"] if L else p["stop_pct"]
        return msg(
            head(ic, a, f"Nuovo {S}: entra lunedì all'apertura"),
            "",
            f"Entrata: ~<b>{usd(p['entry_est'])}</b> a mercato, {gdm(pd.Timestamp(w['signal_date']) + pd.Timedelta(days=1))}",
            f"Importo: {usd(p['notional'])} = {num(p.get('qty', p.get('btc')), 4)} {a} su {usd(p['capital'])}",
            f"🛑 Uscita in perdita: {usd(p['stop'])} (circa −{usd(p['loss_usd'])})",
            "🎯 Profitto: l'uscita segue il prezzo",
            "Lunedì ti confermo il prezzo eseguito.",
            details(f"<b>Stop iniziale</b> {usd(p['stop'])} = {'−' if L else '+'}{num(sp, 1)}% dal prezzo; perdita stimata allo stop "
                    f"~{usd(p['loss_usd'])} (costi inclusi).",
                    f"<b>Perché</b>: chiusura settimanale del {dm(w['signal_date'])} a {usd(w['price'])}, tendenza "
                    f"{'rialzista' if L else 'ribassista'}, flusso dei futures {sig(w['flow'])}.",
                    _mkt(p["market"], p["expo"]),
                    _exit_rules(side, p.get("trail_dist"), p.get("ema21")),
                    "Uscita automatica = 2,5 volte la volatilità media settimanale (ATR) dalla miglior chiusura.",
                    W3_NOTE.get(a, W3_NOTE["BTC"])),
            foot())

    if t == "w_signal":   # posizione aperta mai annunciata (giri saltati)
        return msg(
            head(ic, a, f"{S} già aperto dal {dm(w['entry'])} (segnale in ritardo)"),
            f"Entrata {gdm(w['entry'])} a <b>{usd(w['entry_px'])}</b> · ora {usd(w['price'])}",
            f"Risultato: {money(w['capital'], w['pnl_pct'])}",
            f"🛑 Uscita automatica: <b>{usd(w['trail'])}</b>",
            f"Media a 21 settimane: {usd(w['ema21'])}",
            details(f"Segnale del {dm(w['signal_date'])}: i giri precedenti non l'avevano comunicato. "
                    "Se entri ora, entri a un prezzo diverso.",
                    _mkt(w["market"], w["expo"]), _exit_rules(side, None, None)),
            foot())

    if t == "w_entry":
        x = ev["trade"]
        if w.get("status") in ("aperto", "uscita") and w.get("signal_date") == x["signal"]:
            return msg(
                head(ic, a, f"{S} aperto a {usd(x['entry_px'])}"),
                f"Entrata {gdm(x['entry'])} all'apertura (segnale del {dm(x['signal'])})",
                f"Importo: {usd(w['notional'])} = {num(w.get('qty', w.get('btc')), 4)} {a} su {usd(w['capital'])}",
                f"Prezzo ora: {usd(w['price'])} · {money(w['capital'], w['pnl_pct'])}",
                f"🛑 Uscita automatica: <b>{usd(w['trail'])}</b>",
                details(f"Stop iniziale {usd(w['stop0'])}. {_mkt(x['market'], x['expo'])}"),
                foot())
        win = (x.get("pnl_pct") or 0) > 0
        return msg(
            head("🎯" if win else "🛑", a, f"{S} aperto e già chiuso: {pc(x['pnl_pct'])}"),
            f"Entrata {gdm(x['entry'])} a {usd(x['entry_px'])} (segnale del {dm(x['signal'])})",
            f"Uscita {gdm(x['exit'])} a {usd(x['exit_px'])} · {reason(x['reason'], side)}",
            foot())

    if t == "w_info":
        return msg(
            head(ic, a, f"{S} in corso dal {dm(w['entry'])}: non è un segnale nuovo"),
            f"Da oggi il radar segue anche {a}.",
            f"Entrata {gdm(w['entry'])} a <b>{usd(w['entry_px'])}</b> · ora {usd(w['price'])}",
            f"Risultato: {money(w['capital'], w['pnl_pct'])} · {pc(w['move_pct'])} sul prezzo",
            f"Importo: {usd(w['notional'])} = {num(w.get('qty', w.get('btc')), 4)} {a} su {usd(w['capital'])}",
            f"🛑 Uscita automatica: <b>{usd(w['trail'])}</b>",
            f"Media a 21 settimane: {usd(w['ema21'])}",
            details("Se decidi di seguirla ora, entri a un prezzo diverso.", _mkt(w["market"], w["expo"]),
                    _exit_rules(side, None, None)),
            foot())

    if t == "w_trail":
        moved = "alzata" if L else "abbassata"
        return msg(
            head("🔔", a, f"Uscita automatica {moved} a {usd(w['trail'])}"),
            f"Era {usd(ev['old'])} · si sposta solo a tuo favore",
            f"{S} da {usd(w['entry_px'])} · ora {usd(w['price'])} · {money(w['capital'], w['pnl_pct'])}",
            _if_hit(w),
            foot())

    if t == "w_dist":
        from radar.weekly import next_decision
        sun = gdm(next_decision(w["date"]))
        return msg(
            head("⏳", a, f"Possibile uscita {art(side, 'da')}: decide domenica"),
            "Se la settimana chiudesse oggi si uscirebbe lunedì per distribuzione.",
            f"Funding medio 7g {pc(w['fund7'] * 100, 4)}/giorno · flusso futures {sig(w['flow'])}",
            f"<b>Nessuna azione ora</b>: decide la chiusura di {sun} (UTC).",
            f"🛑 Uscita automatica: {usd(w['trail'])}",
            details("Distribuzione = funding e flusso dei futures contrari alla posizione: "
                    + ("funding medio 7g sopra 0,09%/giorno con flusso negativo." if L
                       else "funding medio 7g sotto −0,03%/giorno con flusso positivo.")),
            foot())

    if t == "w_restore":
        x = ev.get("last")
        pos = None
        if w.get("status") in ("aperto", "uscita"):
            pos = (f"{ICON.get(w['side'], '⚪')} {_side_up(w['side'])} dal {dm(w['entry'])} a {usd(w['entry_px'])} · "
                   f"{money(w['capital'], w['pnl_pct'])}")
        return msg(
            head("⚠️", a, "Avvisi ripristinati: nessuna azione"),
            "Lo stato degli avvisi mancava: ricostruito dalla simulazione.",
            pos or f"Situazione: {_state_plain(w)}",
            f"🛑 Uscita automatica: {usd(w['trail'])} · media 21 sett. {usd(w['ema21'])}" if pos else None,
            details((f"Ultima chiusa: {x['side']} dal {dm(x['entry'])} a {usd(x['entry_px'])}, uscita {dm(x['exit'])} a "
                     f"{usd(x['exit_px'])} ({reason(x['reason'], x['side'])}), {pc(x['pnl_pct'])} sul capitale."
                     if x else ""),
                    f"Dati fino al {dm(w['date'])}. Ingressi e uscite degli ultimi 7 giorni seguono in messaggi separati."),
            foot())

    if t == "w_exit_next":
        est = w["pnl_pct"]
        return msg(
            head("🎯" if est > 0 else "🛑", a, f"Chiudi {art(side)} lunedì all'apertura"),
            f"Motivo: {reason(w['reason'], side)} ({gdm(w['exit_date'])})",
            f"Entrata {dm(w['entry'])} a {usd(w['entry_px'])} · ora {usd(w['price'])}",
            f"Risultato stimato: {money(w['capital'], est)}",
            "Lunedì ti confermo prezzo eseguito e risultato.",
            foot())

    if t == "w_exit":
        x = ev["trade"]
        win = x["pnl_pct"] > 0
        cap = w.get("capital") or 0
        after = ("Ora nessuna posizione: si attende il prossimo segnale." if w.get("status") == "nessuno" else None)
        return msg(
            head("🎯" if win else "🛑", a, f"{S} chiuso in {'profitto' if win else 'perdita'}: {pc(x['pnl_pct'])}"),
            f"Uscita {gdm(x['exit'])} a <b>{usd(x['exit_px'])}</b> · {reason(x['reason'], side)}",
            f"Entrata {gdm(x['entry'])} a {usd(x['entry_px'])} · {pc(x['move_pct'])} sul prezzo",
            f"Risultato: {money(cap, x['pnl_pct'])} del capitale" if cap else f"Risultato: <b>{pc(x['pnl_pct'])}</b> del capitale",
            after,
            foot())

    if t == "w_retract":
        if ev["kind"] == "signal":
            return msg(
                head("⚪", a, f"Segnale {S} annullato: non entrare"),
                f"Il segnale del {dm(ev['key'])} non è più valido dopo l'aggiornamento dei dati:",
                f"<i>{ev['why']}</i>",
                "<b>Se sei già entrato, valuta di chiudere.</b>",
                f"Stato attuale: {_state_plain(w)}.",
                foot())
        return msg(
            head(ic, a, f"Uscita annullata: tieni {art(side)}"),
            "L'uscita annunciata per lunedì non è più valida:",
            f"<i>{ev['why']}</i>",
            (f"🛑 Uscita automatica: {usd(w['trail'])} · media 21 sett. {usd(w['ema21'])}" if w.get("trail") else None),
            foot())
    return str(ev)


def _state_plain(w: dict | None) -> str:
    if not w:
        return "non calcolato"
    s = w.get("status")
    if s == "aperto":
        return f"{w['side']} aperto, uscita automatica {usd(w['trail'])}"
    if s == "uscita":
        return f"{w['side']}, chiusura lunedì all'apertura"
    if s == "segnale":
        return f"segnale {w['side']}, entrata lunedì all'apertura"
    return "nessuna posizione"


def format_intraday(events: list[dict], w: dict | None = None) -> str:
    """Stop toccato nell'ora (weekly.format_intraday). `w` = stato W3.2 per l'esito in dollari (facoltativo)."""
    e = events[0]
    a = e.get("asset") or "BTC"
    S = _side_up(e["side"])
    why = ""
    if e.get("which") == "comunicato":
        why = f"Livello = ultimo comunicato (quello del modello è {usd(e['model'])})."
    elif e.get("told") is not None and e.get("which") == "modello":
        why = f"Livello = quello del modello (l'ultimo comunicato era {usd(e['told'])})."
    return msg(
        head("🛑", a, f"Stop toccato: chiudi {art(e['side'])}"),
        f"Livello <b>{usd(e['level'])}</b> · prezzo ora {usd(e['last'])} ({e['time']})",
        (_if_hit(w, "Risultato a questo livello", icon=False) if w else None),
        details("Lo stop scatta al tocco. L'uscita ufficiale si registra alla chiusura giornaliera.", why),
        foot())


# ---------------------------------------------------------------- riepilogo "Oggi" (sostituisce telegram.today_brief)

def _asset_block(w: dict, pb: dict | None = None, ema_thr: float | None = None) -> list[str]:
    a = w.get("asset") or "BTC"
    st = w.get("status")
    if st in ("aperto", "uscita"):
        cap = (pb or {}).get("capital_usd") or w.get("capital") or 0
        pct = (pb or {}).get("pnl_pct", w.get("pnl_pct"))
        L = w["side"] == "long"
        out = [f"{ICON[w['side']]} <b>{a} {w['side']}</b> · {money(cap, pct)}",
               f"da {usd(w['entry_px'])} ({dm(w['entry'])}) · ora {usd(w['price'])}"]
        if st == "uscita":
            out.append("<b>Chiusura lunedì all'apertura</b>")
        else:
            out.append(f"uscita {usd(w['trail'])}"
                       + (f" · o domenica {'sotto' if L else 'sopra'} {usd(ema_thr)}" if ema_thr else ""))
        return out
    if st == "segnale":
        return [f"{ICON[w['side']]} <b>{a}</b>: nuovo {w['side']}, entrata lunedì all'apertura"]
    return [f"⚪ <b>{a}</b>: nessuna posizione · {usd(w['price'])}"]


def _todo(ws: list[dict]) -> str:
    acts = []
    for w in ws:
        a = w.get("asset") or "BTC"
        if w.get("status") == "segnale":
            acts.append(f"entra {w['side']} su {a} lunedì")
        elif w.get("status") == "uscita":
            acts.append(f"chiudi {a} lunedì")
    if acts:
        return "; ".join(acts)
    held = [f"{w.get('asset') or 'BTC'}" for w in ws if w.get("status") == "aperto"]
    sides = {w.get("side") for w in ws if w.get("status") == "aperto"}
    if held:
        return "nessuna azione"
    return "fuori dal mercato, nessuna azione"


def today_brief(report: dict, day: str | None = None, health: str | None = None) -> str:
    """`health` (facoltativo) = riga di salute del sistema: con questa il messaggio di salute separato non serve più."""
    report = report or {}
    pv, wk = report.get("preview") or {}, report.get("weekly") or {}
    eth = report.get("weekly_eth")
    ws = [x for x in (wk, eth) if x]
    pb = pv.get("position_block")
    lines = [head("📋", None, f"Oggi {dm(day)} · {_todo(ws)}")]
    if wk:
        lines += _asset_block(wk, pb, (pb or {}).get("exit_ema21_threshold"))
        if wk.get("status") == "nessuno":
            sc = pv.get("scenarios") or []
            from importlib import import_module
            band = import_module("radar.telegram")._signal_band
            sh, lg = band(sc, "short"), band(sc, "long")
            if sh or lg:
                lines.append(f"Dom {dm(pv.get('week_close_utc'))}: " + " · ".join(
                    x for x in ((f"short se chiude {sh}" if sh else None), (f"long se chiude {lg}" if lg else None)) if x))
            else:
                lines.append(f"Dom {dm(pv.get('week_close_utc'))}: nessuna chiusura dà un segnale con il flusso attuale")
    if eth:
        lines += _asset_block(eth)
    # contesto: le stesse righe di oggi (telegram._ctx_lines e macro.telegram_lines), in un blockquote espandibile
    from importlib import import_module
    tg = import_module("radar.telegram")
    ctx = tg._ctx_lines(pv.get("today"))
    try:
        mk = import_module("radar.macro").telegram_lines(report.get("macro"))
    except Exception:  # noqa: BLE001
        mk = []
    sr = (pv.get("today") or {}).get("sr") or []
    lv = " · ".join(f"{z['name']} {usd(z['lo'])}" for z in sr if z.get("name") in ("R1", "S1") and z.get("lo") is not None)
    data_day = wk.get("date")
    lines.append(details(*(ctx + mk + ([f"Livelli: {lv}"] if lv else []) +
                           [f"Prezzi alla chiusura del {dm(data_day)}. Contesto, non segnale: decide W3.2."])))
    lines.append(health)
    lines.append(foot())
    return msg(*lines)


# ---------------------------------------------------------------- salute e avvisi tecnici

def format_heartbeat(cur, data_until, last_run, problems, today, others=None, next_dec: str | None = None) -> str:
    state = [f"{ICON.get(cur.get('side'), '⚪') if cur and cur.get('status') != 'nessuno' else '⚪'} BTC "
             + (cur.get('side') if cur and cur.get('status') != 'nessuno' else 'fuori')] if cur else ["BTC non calcolato"]
    for a, c in (others or {}).items():
        state.append(f"{ICON.get(c.get('side'), '⚪') if c and c.get('status') != 'nessuno' else '⚪'} {a} "
                     + (c.get('side') if c and c.get('status') != 'nessuno' else 'fuori'))
    tail = f"Dati fino al {dm(data_until)} · ultimo giro {last_run}"
    if not problems:
        return msg(head("✅", None, "Radar attivo · tutto ok"), tail,
                   " · ".join(state) + (f" · prossima decisione {gdm(next_dec)}" if next_dec else ""))
    return msg(head("⚠️", None, f"Radar · {len(problems)} problem{'a' if len(problems) == 1 else 'i'} tecnic{'o' if len(problems) == 1 else 'i'}"),
               *[f"• {p}" for p in problems], tail,
               " · ".join(state) + (f" · prossima decisione {gdm(next_dec)}" if next_dec else ""))


def format_alarm(g: dict, asset: str = "BTC") -> str:
    return msg(head("⚠️", asset, "Soglia d'allarme: rivedi la strategia"),
               *[f"• {x}" for x in g["why"]],
               "Consigliato: revisione e rischio dimezzato (decidi tu).",
               details(f"Storico dal vivo dal {dm(g['since'])}. Nessuna azione automatica: segnali e posizione non cambiano."),
               foot())


def format_coherence(lines: list[str], asset: str = "BTC") -> str:
    return msg(head("⚠️", asset, "Dati da verificare prima della prossima decisione"),
               *[f"• {x}" for x in lines],
               "Nessuna azione automatica.")


def _src(k: str) -> str:
    return ("ETH " + k[4:]) if k.startswith("eth_") else k


def format_source(crit: dict, data_until: str | None) -> str:
    return msg(head("⚠️", None, "Problema tecnico: fonte dati non disponibile"),
               *[f"• {_src(k)}: {v}" for k, v in crit.items()],
               (f"Segnali calcolati sui dati fino al {dm(data_until)}: decisioni possibili in ritardo." if data_until else None))


def format_source_stop(err: str) -> str:
    return msg(head("⚠️", None, "Problema tecnico: giro interrotto"),
               f"Dati di W3.2 assenti ({err}): nessun segnale calcolato in questo giro.")


def format_stale(stale: dict, hours: int, data_until: str | None) -> str:
    return msg(head("⚠️", None, f"Problema tecnico: dati fermi da oltre {hours} ore"),
               *[f"• {_src(k)}: ultimo giorno {dm(v)}" for k, v in stale.items()],
               (f"Segnali calcolati sui dati fino al {dm(data_until)}: decisioni possibili in ritardo." if data_until else None))


def format_w3_error(err: str, asset: str = "BTC") -> str:
    return msg(head("⚠️", asset, "Segnale non calcolato in questo giro"), f"<code>{err}</code>",
               "Il prossimo giro riprova; posizione e livelli comunicati restano validi.")


def wf_push(run_url: str) -> str:
    return msg(head("⚠️", None, "Radar · salvataggio dei dati non riuscito"),
               "5 tentativi falliti: stato in cache, ripristinato al prossimo giro.", f'<a href="{run_url}">Dettagli del giro</a>')


def wf_tests(run_url: str) -> str:
    return msg(head("⚠️", None, "Radar · test falliti"), "Gli avvisi sono partiti comunque.",
               f'<a href="{run_url}">Dettagli del giro</a>')


def wf_failed(job: str, run_url: str) -> str:
    return msg(head("⚠️", None, f"Radar · giro non completato ({job})"),
               f'<a href="{run_url}">Dettagli del giro</a>')


def test_msg() -> str:
    return head("✅", None, "Radar · connessione riuscita")


def health_line(data_until: str, problems: list[str], next_dec: str | None) -> str:
    """Riga di salute da accodare al riepilogo (alternativa al messaggio separato)."""
    if problems:
        return f"⚠️ {len(problems)} problemi tecnici: " + "; ".join(problems)
    return f"✅ Sistema ok · dati fino al {dm(data_until)}" + (f" · decisione {gdm(next_dec)}" if next_dec else "")
