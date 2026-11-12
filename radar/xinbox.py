"""Posta in arrivo dei post di un trader seguito (oggi Chento, @ChentoTrades) inoltrati dall'utente al bot Telegram.

Nessuna lettura automatica di X (regole d'uso): l'utente condivide il post o lo screenshot al bot, il giro orario
(journal.poll) passa qui i messaggi non-comando della sua chat. Si salvano testo, link, immagini e ora in data/xinbox/;
dai testi si leggono lato e livelli; il comando /trade permette di inserire a mano i livelli letti da uno screenshot.
A ogni giro evaluate_all() verifica ogni operazione sulle candele orarie reali (data/spot_1h.csv): eseguita o no,
TP1 / target / stop, R ottenuto. Le candele orarie non dicono l'ordine dentro l'ora: se stop e target cadono nella
stessa candela si conta lo stop (prudente).

Formato /trade: /trade long 73200 stop 72100 tp 77600 target 87350 [quando 2026-11-08 14:59] [nota libera]
(quando = ora italiana del post; se manca vale l'ora del messaggio). /trader mostra il riepilogo.
"""
from __future__ import annotations

import json
import os
import re

import pandas as pd
import requests

from .data import DATA_DIR

DIR = DATA_DIR / "xinbox"
POSTS = DIR / "posts.json"
TRADER = "ChentoTrades"
FILL_DAYS = 7      # un ordine limit non eseguito entro 7 giorni si considera scaduto
HOLD_DAYS = 30     # dopo 30 giorni un trade senza esito si chiude al prezzo corrente

_NUM = r"(\d{2,3}(?:[.,]\d{3})+|\d{4,6}(?:[.,]\d+)?|\d{2,3}(?:[.,]\d+)?\s?k)"


def _read() -> list:
    try:
        return json.loads(POSTS.read_text())
    except Exception:  # noqa: BLE001
        return []


def _write(posts: list) -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    POSTS.write_text(json.dumps(posts, indent=1, ensure_ascii=False, default=str))


def _px(s: str) -> float | None:
    """'73.200' '73,200' '73200' '73.2k' '73200.5' -> 73200.0 (solo prezzi plausibili di BTC)."""
    s = s.strip().lower().replace(" ", "")
    try:
        if s.endswith("k"):
            v = float(s[:-1].replace(",", ".")) * 1000
        elif re.fullmatch(r"\d{2,3}([.,]\d{3})+", s):
            v = float(re.sub(r"[.,]", "", s))
        else:
            v = float(s.replace(",", "."))
    except ValueError:
        return None
    return v if 10_000 <= v <= 1_000_000 else None


def parse_levels(text: str) -> dict:
    """Lato e livelli da un testo libero (inglese o italiano). Restituisce solo ciò che trova."""
    t = (text or "").lower()
    out: dict = {}
    if re.search(r"\b(long|buy|compr|bid)", t):
        out["side"] = "long"
    if re.search(r"\b(short|sell|vend)", t):
        out["side"] = "short" if "side" not in out else out["side"]
    keys = {"entry": r"(?:entry|ingresso|limit|entrata|at|@)", "stop": r"(?:stop|sl|invalidation|invalidazione)",
            "tp1": r"(?:tp1|tp|take profit|primo target)", "target": r"(?:target|tp2|obiettivo)"}
    for k, kw in keys.items():
        m = re.search(kw + r"\s*[:=]?\s*\$?" + _NUM, t)
        if m and (v := _px(m.group(1))):
            out[k] = v
    if "entry" not in out:   # "long 73200" / "short 80.5k": il primo prezzo dopo il lato è l'ingresso
        m = re.search(r"\b(?:long|short|buy|sell)\s*\$?" + _NUM, t)
        if m and (v := _px(m.group(1))):
            out["entry"] = v
    return out


def _download_photo(api, file_id: str, name: str) -> str | None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    res = api("getFile", file_id=file_id)
    path = (res.get("result") or {}).get("file_path")
    if not res.get("ok") or not path:
        return None
    r = requests.get(f"https://api.telegram.org/file/bot{token}/{path}", timeout=30)
    if not r.ok:
        return None
    DIR.mkdir(parents=True, exist_ok=True)
    out = DIR / f"{name}{os.path.splitext(path)[1] or '.jpg'}"
    out.write_bytes(r.content)
    return out.name


def ingest(m: dict, api) -> str:
    """Salva un messaggio inoltrato (link X, testo, screenshot) e restituisce la risposta per l'utente."""
    when = pd.Timestamp(m.get("date", 0), unit="s")
    text = m.get("text") or m.get("caption") or ""
    links = re.findall(r"https?://(?:x|twitter)\.com/\S+", text)
    name = f"{when:%Y%m%d_%H%M%S}_{m.get('message_id')}"
    photo = None
    if m.get("photo"):
        photo = _download_photo(api, m["photo"][-1]["file_id"], name)
    lv = parse_levels(text)
    posts = _read()
    rec = {"id": name, "received_utc": str(when), "post_utc": str(when), "text": text, "links": links, "image": photo,
           "source": "inoltro", **lv}
    posts.append(rec)
    evaluate_all(posts)
    _write(posts)
    got = ", ".join(f"{k} {v:,.0f}".replace(",", ".") for k, v in lv.items() if k != "side")
    head = f"<b>Post salvato</b> ({name})" + (f" · {lv['side'].upper()}" if lv.get("side") else "")
    if lv.get("entry") and lv.get("stop"):
        return head + f"\nLivelli letti: {got}. L'esito si verifica sui prezzi a ogni giro."
    tail = ("Immagine salvata: i livelli del grafico li leggo nell'analisi, oppure scrivili tu con\n"
            "/trade long 73200 stop 72100 tp 77600 target 87350 quando 2026-11-08 14:59") if photo else \
           "Per verificarne l'esito servono almeno ingresso e stop: /trade long 73200 stop 72100 tp 77600"
    return head + (f"\nLetti: {got}." if got else "") + "\n" + tail


def command(text: str, when_utc: str) -> str | None:
    """/trade e /trader; None se il comando non è di questo modulo."""
    cmd = text.split()[0].lower().split("@")[0] if text.strip() else ""
    if cmd == "/trader":
        return summary(_read())
    if cmd != "/trade":
        return None
    body = text[len(text.split()[0]):]
    lv = parse_levels(body)
    q = re.search(r"quando\s+(\d{4}-\d{2}-\d{2}(?:[ t]\d{1,2}:\d{2})?)", body.lower())
    post = (pd.Timestamp(q.group(1)).tz_localize("Europe/Rome").tz_convert("UTC").tz_localize(None)
            if q else pd.Timestamp(when_utc))
    if not (lv.get("side") and lv.get("entry") and lv.get("stop")):
        return "Formato: /trade long 73200 stop 72100 tp 77600 target 87350 [quando 2026-11-08 14:59]"
    posts = _read()
    rec = {"id": f"{post:%Y%m%d_%H%M%S}_manuale", "received_utc": when_utc, "post_utc": str(post), "text": body.strip(),
           "links": [], "image": None, "source": "manuale", **lv}
    posts.append(rec)
    evaluate_all(posts)
    _write(posts)
    o = rec.get("outcome") or {}
    return (f"<b>Trade registrato</b> · {lv['side'].upper()} {lv['entry']:,.0f} stop {lv['stop']:,.0f}".replace(",", ".")
            + f"\nEsito ad oggi: {o.get('status', 'in verifica')}" + (f" · {o['r']:+.2f}R" if o.get("r") is not None else ""))


# ---------------------------------------------------------------- verifica sui prezzi

def _candles() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "spot_1h.csv", parse_dates=["t"])
    return df.set_index("t").sort_index()


def evaluate(rec: dict, c: pd.DataFrame) -> dict:
    """Esito di un'operazione con ingresso e stop: limit eseguito? poi stop, TP1 o target (il primo toccato)."""
    side, e, s = rec.get("side"), rec.get("entry"), rec.get("stop")
    if side not in ("long", "short") or not e or not s:
        return {"status": "livelli mancanti"}
    L = side == "long"
    risk = (e - s) if L else (s - e)
    if risk <= 0:
        return {"status": "stop incoerente"}
    t0 = pd.Timestamp(rec["post_utc"]).floor("h")
    after = c[c.index >= t0]
    if after.empty:
        return {"status": "in attesa di dati"}
    filled = None
    for t, row in after[after.index < t0 + pd.Timedelta(days=FILL_DAYS)].iterrows():
        if (row.low <= e <= row.high) or (L and row.high < e) or (not L and row.low > e):
            filled = t
            break
    if filled is None:
        done = after.index[-1] >= t0 + pd.Timedelta(days=FILL_DAYS)
        return {"status": "non eseguito" if done else "ordine in attesa"}
    tp1, tgt = rec.get("tp1"), rec.get("target")
    r1 = (((tp1 - e) if L else (e - tp1)) / risk) if tp1 else None
    took_tp1 = False   # dopo TP1: metà chiusa a TP1, stop della metà restante spostato all'ingresso
    for t, row in after[after.index >= filled].iterrows():
        stop_now = e if took_tp1 else s
        if (row.low <= stop_now) if L else (row.high >= stop_now):   # prudente: lo stop viene prima
            if took_tp1:
                return {"status": "TP1 poi stop a pareggio", "filled_utc": str(filled), "exit_utc": str(t),
                        "r": round(0.5 * r1, 2)}
            return {"status": "stop", "filled_utc": str(filled), "exit_utc": str(t), "r": -1.0}
        if t == filled:
            continue   # nella candela d'ingresso non si sa se il massimo viene prima o dopo: si contano solo gli stop
        if tgt and (row.high >= tgt if L else row.low <= tgt):
            g = ((tgt - e) if L else (e - tgt)) / risk
            r = 0.5 * r1 + 0.5 * g if (took_tp1 and r1 is not None) else g
            return {"status": "target", "filled_utc": str(filled), "exit_utc": str(t), "r": round(r, 2)}
        if tp1 and not took_tp1 and (row.high >= tp1 if L else row.low <= tp1):
            if not tgt:
                return {"status": "TP1", "filled_utc": str(filled), "exit_utc": str(t), "r": round(r1, 2)}
            took_tp1 = True
        if t >= filled + pd.Timedelta(days=HOLD_DAYS):
            px = row.close
            r = ((px - e) if L else (e - px)) / risk
            r = 0.5 * r1 + 0.5 * r if took_tp1 else r
            return {"status": "chiuso a tempo (30 giorni)", "filled_utc": str(filled), "exit_utc": str(t), "r": round(r, 2)}
    last = after.close.iloc[-1]
    return {"status": "aperto" + (" (TP1 preso, stop a pareggio)" if took_tp1 else ""), "filled_utc": str(filled),
            "r_now": round(((last - e) if L else (e - last)) / risk, 2)}


def evaluate_all(posts: list | None = None) -> list:
    """Ricalcola l'esito di ogni operazione; chiamata a ogni giro orario (cli.daily)."""
    save = posts is None
    posts = _read() if posts is None else posts
    if not posts:
        return posts
    c = _candles()
    for p in posts:
        if p.get("entry") and p.get("stop"):
            p["outcome"] = evaluate(p, c)
    if save:
        _write(posts)
    return posts


def summary(posts: list) -> str:
    tr = [p for p in posts if p.get("outcome")]
    closed = [p for p in tr if p["outcome"].get("r") is not None]
    rs = [p["outcome"]["r"] for p in closed]
    lines = [f"<b>Trader seguito · @{TRADER}</b>",
             f"Post salvati {len(posts)} · operazioni con livelli {len(tr)} · chiuse {len(closed)}"]
    if rs:
        win = sum(r > 0 for r in rs)
        lines.append(f"Vincenti {win}/{len(rs)} · somma {sum(rs):+.2f}R · media {sum(rs) / len(rs):+.2f}R per trade")
    nf = sum(p["outcome"]["status"] == "non eseguito" for p in tr)
    if nf:
        lines.append(f"Ordini non eseguiti: {nf}")
    for p in tr[-5:]:
        o = p["outcome"]
        lines.append(f"{p['post_utc'][:16]} · {p['side']} {p['entry']:,.0f} · {o['status']}".replace(",", ".")
                     + (f" {o['r']:+.2f}R" if o.get("r") is not None else ""))
    lines.append("Servono 20–30 operazioni, comprese le perdenti, per giudicare il metodo.")
    return "\n".join(lines)
