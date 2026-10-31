"""Registro dei trade reali via Telegram: l'utente scrive al bot cosa ha eseguito (Bybit/OKX), il workflow orario
legge i messaggi nuovi (getUpdates), salva in data/journal.json e risponde con una conferma breve.

Comandi: /entrato <prezzo> [quantità_btc] [v2|w2] [long|short] · /limit <prezzo> [quantità_btc] · /uscito <prezzo> [motivo]
         /exchange bybit|okx · /registro · /aiuto
Si accettano solo i messaggi della chat TELEGRAM_CHAT_ID (gli altri si ignorano senza risposta). Offset di getUpdates in
data/state.json (chiave "tg_offset"). Il confronto col segnale (prezzo, slippage %, ritardo in ore) si completa con
link(report) dopo il calcolo del segnale: i giri di ricerca usano lo slippage reale misurato (RESEARCH.md).
"""
from __future__ import annotations

import json
import os
import re

import pandas as pd
import requests

from .data import DATA_DIR

JOURNAL_FILE = DATA_DIR / "journal.json"
STATE_FILE = DATA_DIR / "state.json"
EXCHANGE = "bybit/okx"
W_V2 = (0.4, 0.6)   # pesi delle due tranche di v2 se la quantità non è indicata

HELP = ("<b>RADAR SIGNAL BTC · Registro dei trade reali</b>\n"
        "/entrato 67500 [0,015] [v2|w2] [long|short] · ingresso eseguito (prezzo, quantità BTC)\n"
        "/limit 66900 [0,022] · 2ª tranche (limit 60%) eseguita\n"
        "/uscito 69100 [motivo] · uscita (es. tp, stop, tempo, manuale)\n"
        "/exchange bybit|okx · exchange dei trade (predefinito bybit/okx)\n"
        "/registro · ultimi trade reali e confronto con il segnale\n"
        "Strategia e lato si deducono dal segnale attivo se non li scrivi. Virgola o punto vanno bene.\n"
        "Il bot legge i messaggi a ogni giro orario: la risposta arriva entro un'ora.")


# ---------------------------------------------------------------- file

def _read(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def load() -> dict:
    j = _read(JOURNAL_FILE, {})
    j.setdefault("exchange", EXCHANGE)
    j.setdefault("trades", [])
    j.setdefault("ref", {})
    return j


def save(j: dict) -> None:
    JOURNAL_FILE.write_text(json.dumps(j, indent=1, default=str))


# ---------------------------------------------------------------- parsing

def num(s: str, price: bool = True) -> float | None:
    """'67.500' / '67,500' / '67500,5' / '67.500,5' -> float. Con un solo separatore seguito da 3 cifre, per i prezzi
    è il separatore delle migliaia (67.500 = 67500); per le quantità è sempre il decimale (0,015)."""
    s = s.strip().replace("$", "").replace("'", "").replace(" ", "")
    if not re.fullmatch(r"\d[\d.,]*", s):
        return None
    if "." in s and "," in s:   # l'ultimo separatore è il decimale
        dec = "." if s.rfind(".") > s.rfind(",") else ","
        s = s.replace("," if dec == "." else ".", "").replace(dec, ".")
    elif s.count(".") + s.count(",") > 1:   # 1.234.567: solo migliaia
        s = s.replace(".", "").replace(",", "")
    elif "." in s or "," in s:
        a, b = re.split(r"[.,]", s)
        s = a + b if (price and len(b) == 3 and a != "0") else a + "." + b
    try:
        return float(s)
    except ValueError:
        return None


def parse(text: str) -> tuple[str, dict]:
    """Testo del messaggio -> (comando, argomenti)."""
    parts = text.strip().split()
    if not parts or not parts[0].startswith("/"):
        return "", {}
    cmd = parts[0][1:].split("@")[0].lower()
    args = {"nums": [], "strategy": None, "side": None, "words": []}
    for p in parts[1:]:
        w = p.lower()
        if w in ("v2", "w2"):
            args["strategy"] = w
        elif w in ("long", "short"):
            args["side"] = w
        elif w in ("btc", "x"):
            continue
        elif num(w) is not None and len(args["nums"]) < 2:
            args["nums"].append(w)
        else:
            args["words"].append(p)
    raw = args.pop("nums")
    args["price"] = num(raw[0]) if raw else None
    args["qty"] = num(raw[1], price=False) if len(raw) > 1 else None
    return cmd, args


# ---------------------------------------------------------------- calcoli

def _usd(x: float | None) -> str:
    return "–" if x is None else f"${x:,.0f}".replace(",", ".")


def _avg(t: dict) -> float:
    e = t["entries"]
    if all(x.get("qty") for x in e):
        w = [x["qty"] for x in e]
    elif t["strategy"] == "v2" and len(e) == 2:
        w = list(W_V2)
    else:
        w = [1.0] * len(e)
    return sum(x["price"] * k for x, k in zip(e, w)) / sum(w)


def _hours(a: str | None, b: str | None) -> float | None:
    if not a or not b:
        return None
    return round((pd.Timestamp(a) - pd.Timestamp(b)).total_seconds() / 3600, 1)


def _slip(real: float, sig: float | None, side: str, entry: bool) -> float | None:
    """Slippage in % rispetto al segnale: positivo = peggio del segnale (long: comprato più caro / venduto più basso)."""
    if not sig:
        return None
    s = (real - sig) / sig * 100 * (1 if side == "long" else -1) * (1 if entry else -1)
    return round(s, 3)


def compare(t: dict) -> dict:
    """Ricalcola medio, risultato % sul prezzo e confronto col segnale (slippage % e ritardo in ore)."""
    sig = t.get("signal") or {}
    t["avg"] = round(_avg(t), 2)
    e0 = t["entries"][0]
    c = {"slip_entry_pct": _slip(e0["price"], sig.get("entry"), t["side"], True),
         "delay_entry_h": _hours(e0["time"], sig.get("entry_time"))}
    lim = next((x for x in t["entries"][1:] if x.get("kind") == "limit"), None)
    if lim and sig.get("limit"):
        c["slip_limit_pct"] = _slip(lim["price"], sig["limit"], t["side"], True)
    if t.get("exit"):
        x = t["exit"]
        t["result_pct"] = round((x["price"] / t["avg"] - 1) * 100 * (1 if t["side"] == "long" else -1), 2)
        c["slip_exit_pct"] = _slip(x["price"], sig.get("exit"), t["side"], False)
        c["delay_exit_h"] = _hours(x["time"], sig.get("exit_time"))
        if sig.get("result_pct") is not None:
            c["result_vs_signal_pct"] = round(t["result_pct"] - sig["result_pct"], 2)
    t["compare"] = c
    return t


def averages(j: dict) -> dict:
    """Slippage e ritardo medi sui trade reali (None se non ci sono dati)."""
    def m(k):
        v = [t["compare"][k] for t in j["trades"] if t.get("compare", {}).get(k) is not None]
        return round(sum(v) / len(v), 3) if v else None
    slips = [t["compare"][k] for t in j["trades"] for k in ("slip_entry_pct", "slip_limit_pct", "slip_exit_pct")
             if t.get("compare", {}).get(k) is not None]
    return {"n": len(j["trades"]), "closed": sum(1 for t in j["trades"] if t.get("exit")),
            "slip_pct": round(sum(slips) / len(slips), 3) if slips else None,
            "slip_entry_pct": m("slip_entry_pct"), "slip_exit_pct": m("slip_exit_pct"),
            "delay_entry_h": m("delay_entry_h"), "delay_exit_h": m("delay_exit_h")}


# ---------------------------------------------------------------- segnale attivo

def _active(state: dict) -> dict:
    """Segnali attivi da data/state.json: {'v2': (lato, data segnale), 'w2': (...)}."""
    out = {}
    v = state.get("v2") or {}
    if v.get("status") in ("conferma", "ingresso", "aperto") and v.get("side"):
        out["v2"] = (v["side"], v.get("signal_date"))
    w = state.get("weekly") or {}
    if w.get("status") in ("segnale", "aperto", "uscita") and w.get("side"):
        out["w2"] = (w["side"], w.get("signal_date"))
    return out


def _open(j: dict, strategy: str | None) -> list[dict]:
    return [t for t in j["trades"] if not t.get("exit") and (strategy is None or t["strategy"] == strategy)]


def _pct(x: float | None, d: int = 2) -> str:
    return "–" if x is None else f"{x:+.{d}f}%".replace(".", ",")


def _h(x: float | None) -> str:
    return "–" if x is None else f"{x:.1f}".replace(".", ",")


def _cmp_text(t: dict) -> str:
    c, sig = t.get("compare", {}), t.get("signal") or {}
    if c.get("slip_exit_pct") is not None or c.get("delay_exit_h") is not None:
        return (f"Segnale uscita {_usd(sig.get('exit'))} · slippage {_pct(c.get('slip_exit_pct'), 3)} · "
                f"ritardo {_h(c.get('delay_exit_h'))} h")
    if c.get("slip_entry_pct") is not None:
        return (f"Segnale ingresso {_usd(sig.get('entry'))} · slippage {_pct(c['slip_entry_pct'], 3)} · "
                f"ritardo {_h(c.get('delay_entry_h'))} h")
    return "Confronto col segnale al prossimo giro orario."


# ---------------------------------------------------------------- comandi

def handle(text: str, when: str, j: dict, state: dict) -> str:
    """Esegue un comando sul registro j (modificato sul posto) e restituisce la risposta."""
    cmd, a = parse(text)
    if cmd in ("aiuto", "help", "start"):
        return HELP
    if cmd == "exchange":
        ex = next((w.lower() for w in a["words"] if w.lower() in ("bybit", "okx")), None)
        if not ex:
            return "Scrivi /exchange bybit oppure /exchange okx."
        j["exchange"] = ex
        for t in _open(j, None):
            t["exchange"] = ex
        return f"Exchange impostato: {ex} (trade aperti e prossimi)."
    if cmd == "registro":
        return summary(j)
    if cmd == "entrato":
        if not a["price"]:
            return "Manca il prezzo: /entrato 67500 [0,015] [v2|w2] [long|short]"
        act = _active(state)
        strat = a["strategy"]
        if not strat:
            if len(act) == 1:
                strat = next(iter(act))
            else:
                return ("Due segnali attivi (v2 e w2): " if act else "Nessun segnale attivo: ") + \
                       "specifica la strategia, es. /entrato " + f"{a['price']:.0f} v2 long"
        side = a["side"] or (act.get(strat) or (None,))[0]
        if not side:
            return f"Nessun segnale {strat} attivo: specifica il lato, es. /entrato {a['price']:.0f} {strat} long"
        sd = act[strat][1] if strat in act and act[strat][0] == side else None
        ref = j["ref"].get(strat) or {}
        sig = {k: ref.get(k) for k in ("entry", "entry_time", "limit")} if ref.get("signal_date") == sd and sd else {}
        n = sum(1 for t in j["trades"] if t["id"].startswith(when[:10])) + 1
        t = {"id": f"{when[:10]}-{n}", "strategy": strat, "side": side, "exchange": j["exchange"], "signal_date": sd,
             "entries": [{"price": a["price"], "qty": a["qty"], "time": when, "kind": "ingresso"}], "exit": None,
             "result_pct": None, "signal": sig, "note": " ".join(a["words"]) or None}
        j["trades"].append(compare(t))
        q = f" · {a['qty']:g} BTC".replace(".", ",") if a["qty"] else ""
        return (f"✅ Registrato ingresso {side} {strat.upper()} a {_usd(a['price'])}{q} ({t['exchange']}) · id {t['id']}\n"
                + _cmp_text(t))
    if cmd in ("limit", "uscito"):
        if not a["price"]:
            return f"Manca il prezzo: /{cmd} 67500" + (" [motivo]" if cmd == "uscito" else " [quantità_btc]")
        op = _open(j, a["strategy"])
        if not op:
            return "Nessun trade reale aperto: registra prima l'ingresso con /entrato."
        if len(op) > 1:
            return f"Più trade aperti ({', '.join(t['strategy'] for t in op)}): specifica la strategia, es. /{cmd} {a['price']:.0f} v2"
        t = op[0]
        if cmd == "limit":
            t["entries"].append({"price": a["price"], "qty": a["qty"], "time": when, "kind": "limit"})
            compare(t)
            return (f"✅ Limit eseguito a {_usd(a['price'])} · medio {_usd(t['avg'])} ({t['strategy'].upper()} {t['side']})"
                    + (f"\nSegnale limit {_usd(t['signal']['limit'])} · slippage {_pct(t['compare']['slip_limit_pct'], 3)}"
                       if t["compare"].get("slip_limit_pct") is not None else ""))
        t["exit"] = {"price": a["price"], "time": when, "reason": " ".join(a["words"]) or None}
        compare(t)
        return (f"✅ Uscita {t['strategy'].upper()} {t['side']} a {_usd(a['price'])} · medio {_usd(t['avg'])} · "
                f"risultato {_pct(t['result_pct'])} sul prezzo\n" + _cmp_text(t))
    return "Comando non riconosciuto. Scrivi /aiuto per l'elenco."


def summary(j: dict, n: int = 5) -> str:
    if not j["trades"]:
        return "Registro vuoto: nessun trade reale. Scrivi /aiuto per i comandi."
    lines = ["<b>RADAR SIGNAL BTC · Registro dei trade reali</b>"]
    for t in j["trades"][-n:][::-1]:
        c = t.get("compare", {})
        st = (f"uscita {_usd(t['exit']['price'])} · {_pct(t['result_pct'])}" if t.get("exit") else "aperto")
        lines.append(f"{t['id']} · {t['strategy'].upper()} {t['side']} · medio {_usd(t['avg'])} · {st} · "
                     f"slippage ingresso {_pct(c.get('slip_entry_pct'), 3)}, ritardo {_h(c.get('delay_entry_h'))} h")
    m = averages(j)
    lines.append(f"Medie su {m['n']} trade ({m['closed']} chiusi): slippage {_pct(m['slip_pct'], 3)} · ritardo ingresso "
                 f"{_h(m['delay_entry_h'])} h (slippage positivo = peggio del segnale)")
    return "\n".join(lines)


# ---------------------------------------------------------------- Telegram

def _api(method: str, **kw) -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=kw, timeout=20)
    return r.json() if r.ok else {"ok": False, "description": r.text}


def poll() -> int:
    """Legge i messaggi nuovi del bot, esegue i comandi della chat TELEGRAM_CHAT_ID e risponde. Restituisce il numero di
    comandi eseguiti. Senza token/chat non fa nulla."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return 0
    state = _read(STATE_FILE, {})
    res = _api("getUpdates", offset=state.get("tg_offset", 0), timeout=2, allowed_updates=["message"])
    if not res.get("ok"):
        print(f"[journal] getUpdates non riuscito: {res.get('description')}")
        return 0
    ups = res.get("result", [])
    if not ups:
        return 0
    j, done = load(), 0
    for u in ups:
        m = u.get("message") or {}
        if str((m.get("chat") or {}).get("id")) != str(chat) or not m.get("text", "").startswith("/"):
            continue   # altre chat e testo libero: ignorati, nessuna risposta
        when = str(pd.Timestamp(m.get("date", 0), unit="s"))
        try:
            reply = handle(m["text"], when, j, state)
        except Exception as e:  # noqa: BLE001  un comando malformato non deve bloccare l'offset
            reply = f"Comando non registrato ({type(e).__name__}). Scrivi /aiuto per il formato."
        _api("sendMessage", chat_id=chat, text=reply, parse_mode="HTML", reply_to_message_id=m.get("message_id"))
        done += 1
    if done:
        save(j)
    state = _read(STATE_FILE, {})   # rilettura: lo stato potrebbe essere cambiato
    state["tg_offset"] = max(u["update_id"] for u in ups) + 1
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
    return done


# ---------------------------------------------------------------- confronto col segnale

def link(report: dict) -> None:
    """Dopo il calcolo del segnale: salva il riferimento attuale (v2 e w2) e completa il confronto dei trade reali con
    i prezzi e gli orari del segnale (ingresso, limit, uscita, risultato)."""
    j = load()
    ref = {}
    v = report.get("v2") or {}
    if v.get("status") in ("conferma", "ingresso", "aperto"):
        p = v.get("plan") or {}
        ref["v2"] = {"signal_date": v.get("signal_date"), "side": v.get("side"),
                     "entry": v.get("entry") or v.get("entry_est") or p.get("entry"), "entry_time": v.get("entry_time"),
                     "limit": (v.get("levels") or [None, p.get("limit")])[1]}
    w = report.get("weekly") or {}
    if w.get("status") in ("aperto", "uscita"):
        ref["w2"] = {"signal_date": w.get("signal_date"), "side": w.get("side"), "entry": w.get("entry_px"),
                     "entry_time": w.get("entry"), "limit": None}
    j["ref"] = ref
    v2 = {t["signal_date"]: t for t in (report.get("trades") or {}).get("futures", [])}
    w2 = {t["signal"]: t for t in ((w.get("history") or {}).get("trades") or [])}
    for t in j["trades"]:
        sd, s = t.get("signal_date"), dict(t.get("signal") or {})
        if not sd:
            continue
        if t["strategy"] == "v2" and sd in v2:
            x = v2[sd]
            s.update(entry=x.get("entry"), entry_time=x.get("entry_time"), limit=(x.get("levels") or [None, None])[1])
            if x.get("exit") != "open":
                s.update(exit=x.get("exit_px"), exit_time=x.get("exit_time") or x.get("exit_date"), exit_kind=x.get("exit"),
                         result_pct=x.get("pnl_pct_invested"))
        elif t["strategy"] == "w2" and sd in w2:
            x = w2[sd]
            s.update(entry=x.get("entry_px"), entry_time=x.get("entry"))
            if x.get("reason") != "open" and x.get("exit_px"):
                s.update(exit=x["exit_px"], exit_time=x.get("exit"), exit_kind=x.get("reason"), result_pct=x.get("move_pct"))
        elif sd == (ref.get(t["strategy"]) or {}).get("signal_date"):
            s.update({k: ref[t["strategy"]][k] for k in ("entry", "entry_time", "limit")})
        t["signal"] = s
        compare(t)
    save(j)
