"""Avviso VIX su Telegram (richiesto dall'utente il 25/11/2026, stato/STATO-vix.md): condizione di mercato, non un segnale di W3.2.

- Controllo ogni 4 ore: il primo giro orario dentro ciascuna fascia 00, 04, 08, 12, 16, 20 UTC; negli altri giri non fa nulla.
  Marcatore della fascia in st["vix"]["ultimo_check"].
- Fonte: Yahoo chart API ^VIX (ultimo prezzo e chiusure giornaliere); ripiego FRED VIXCLS (solo chiusure). Rete caduta su
  entrambe: eccezione (la cattura cli._soft), nessun messaggio, nessun cambio di stato.
- Zone: "alta" sopra 30, "bassa" sotto 15, "neutra" in mezzo. Isteresi: avviso Buy quando il valore supera 30 ed è
  "armato_alto" (si riarma sotto 25); avviso Sell quando scende sotto 15 ed è "armato_basso" (si riarma sopra 17).
- Primo avvio (st["vix"] assente): un messaggio con la condizione attuale; armato solo il lato in cui il VIX non si trova già.
- Lo stato nuovo (zona, armamenti, marcatore) si scrive solo se l'invio è confermato (message_id o True), come guard.update:
  un invio fallito si ripropone al giro orario successivo.
- Dati storici citati: research/vix_alert/README.md (controllo descrittivo, nessuna regola di W3.2 cambia).
"""
from __future__ import annotations

import io
from datetime import datetime, timezone

import pandas as pd
import requests

from .telegram import details, esc, head, msg, num, pc

YAHOO = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX", "https://query2.finance.yahoo.com/v8/finance/chart/%5EVIX")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv"
UA = {"User-Agent": "Mozilla/5.0 (compatible; radar)"}
TIMEOUT = 20
HIGH, LOW = 30.0, 15.0              # soglie dell'avviso
REARM_HIGH, REARM_LOW = 25.0, 17.0  # riarmo: sotto 25 per il Buy, sopra 17 per il Sell
STEP_H = 4                          # controllo ogni 4 ore
KEY = "vix"
NOTE = "Condizione di mercato, non un segnale di W3.2."
LABEL = {"alta": "paura alta", "neutra": "normale", "bassa": "tranquillo"}


# ------------------------------------------------------------------ fonti (rete)
def _yahoo() -> dict:
    last = None
    for url in YAHOO:
        try:
            r = requests.get(url, params={"range": "1y", "interval": "1d"}, headers=UA, timeout=TIMEOUT)
            r.raise_for_status()
            res = r.json()["chart"]["result"][0]
            break
        except Exception as e:  # noqa: BLE001
            last = e
    else:
        raise last
    meta = res["meta"]
    off = int(meta.get("gmtoffset") or 0)
    closes = pd.Series(res["indicators"]["quote"][0]["close"],
                       index=[pd.Timestamp(int(t) + off, unit="s").normalize() for t in res["timestamp"]])
    closes = pd.to_numeric(closes, errors="coerce").dropna()
    closes = closes[~closes.index.duplicated(keep="last")].sort_index()
    value = float(meta["regularMarketPrice"])
    t = pd.Timestamp(int(meta["regularMarketTime"]), unit="s")
    day = pd.Timestamp(int(meta["regularMarketTime"]) + off, unit="s").normalize()
    closes = closes[closes.index < day]          # chiusure concluse; la barra del giorno è il prezzo attuale
    if not value > 0:
        raise ValueError("Yahoo ^VIX: prezzo assente")
    return {"value": value, "time": t, "day": day, "closes": closes.round(2),
            "prev": float(closes.iloc[-1]) if len(closes) else None, "source": "Yahoo ^VIX", "live": True}


def _fred() -> dict:
    start = (pd.Timestamp(datetime.now(timezone.utc).date()) - pd.Timedelta(days=370)).date()
    r = requests.get(FRED, params={"id": "VIXCLS", "cosd": str(start)}, timeout=TIMEOUT)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    if "VIXCLS" not in d.columns:
        raise ValueError("FRED VIXCLS: risposta senza la colonna attesa")
    s = pd.to_numeric(d.set_index(d.columns[0])["VIXCLS"], errors="coerce").dropna()
    s.index = pd.to_datetime(s.index).normalize()
    s = s[s > 0].sort_index()
    if len(s) == 0:
        raise ValueError("FRED VIXCLS: nessun dato")
    return {"value": float(s.iloc[-1]), "time": s.index[-1], "day": s.index[-1], "closes": s.iloc[:-1],
            "prev": float(s.iloc[-2]) if len(s) > 1 else None, "source": "FRED VIXCLS", "live": False}


def fetch() -> dict:
    """Ultimo valore del VIX: Yahoo, poi FRED. Entrambe cadute: eccezione."""
    try:
        return _yahoo()
    except Exception as e:  # noqa: BLE001
        print(f"[vix] Yahoo non disponibile ({e!r}): ripiego FRED VIXCLS")
    return _fred()


# ------------------------------------------------------------------ logica
def zone(v: float) -> str:
    return "alta" if v > HIGH else "bassa" if v < LOW else "neutra"


def slot(now) -> str:
    """Fascia di 4 ore del giro: '2026-11-25T16'."""
    t = pd.Timestamp(now)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    return f"{t.date()}T{t.hour // STEP_H * STEP_H:02d}"


def since(q: dict) -> dict:
    """Ultimo attraversamento noto dalle chiusure recenti (più il valore attuale): data d'ingresso nella zona attuale e
    ultimo giorno visto nelle altre zone."""
    s = pd.concat([q["closes"], pd.Series([q["value"]], index=[q["day"]])])
    s = s[~s.index.duplicated(keep="last")].sort_index()
    z = s.map(zone)
    cur = z.iloc[-1]
    out = [i for i, x in z.items() if x != cur]
    start = s.index[0]
    entered = None if not out else z.index[z.index > out[-1]][0]
    prev_ep = None
    if out:   # episodio precedente nella stessa zona (es. VIX sopra 30 anche il 20/11)
        before = z[z.index < out[-1]]
        same = before[before == cur]
        prev_ep = (same.index[-1], float(s[same.index[-1]])) if len(same) else None
    last = {k: (z[z == k].index[-1] if (z == k).any() else None) for k in ("alta", "bassa")}
    return {"zone": cur, "entered": entered, "start": start, "prev_episode": prev_ep, "last": last}


def _pt(x: float) -> str:
    return f"{x:+.2f}".replace(".", ",").replace("-", "−")


def _dm(t) -> str:
    return pd.Timestamp(t).strftime("%d/%m")


def _value_line(q: dict) -> str:
    when = f"alle {pd.Timestamp(q['time']).strftime('%H:%M')} UTC" if q.get("live") else f"chiusura del {_dm(q['day'])}"
    line = f"VIX <b>{num(q['value'])}</b> {when}"
    if q.get("prev"):
        d = q["value"] - q["prev"]
        line += f" · oggi {_pt(d)} punti ({pc(d / q['prev'] * 100, 1)})" if q.get("live") else \
            f" · {_pt(d)} punti sulla chiusura precedente"
    return line


def _since_line(q: dict) -> str:
    s = since(q)
    z = s["zone"]
    where = {"alta": f"Sopra {HIGH:.0f}", "bassa": f"Sotto {LOW:.0f}", "neutra": f"Tra {LOW:.0f} e {HIGH:.0f}"}[z]
    if s["entered"] is None:
        txt = f"{where} almeno dal {_dm(s['start'])}"
    elif pd.Timestamp(s["entered"]) == pd.Timestamp(q["day"]):
        txt = f"{where} da oggi ({_dm(s['entered'])})"
    else:
        txt = f"{where} dal {_dm(s['entered'])}"
    if z != "neutra" and s["prev_episode"]:
        d, v = s["prev_episode"]
        txt += f"; episodio precedente il {_dm(d)} ({num(v)})"
    if z == "neutra":
        seen = [f"sopra {HIGH:.0f} il {_dm(s['last']['alta'])}" if s["last"]["alta"] is not None else None,
                f"sotto {LOW:.0f} il {_dm(s['last']['bassa'])}" if s["last"]["bassa"] is not None else None]
        seen = [x for x in seen if x]
        if seen:
            txt += "; ultima chiusura " + ", ".join(seen)
    return txt


def _src(q: dict) -> str:
    return f"Fonte: {esc(q['source'])} · controllo ogni {STEP_H} ore · dati storici: research/vix_alert"


def format_buy(q: dict) -> str:
    return msg(head("🟢", None, f"VIX sopra {HIGH:.0f} · segnale Buy (paura alta)"),
               _value_line(q),
               "Storico S&amp;P 500: +5,5% mediano a 90 giorni (giorno qualsiasi +3,1%); su BTC misto.",
               NOTE,
               details(_since_line(q) + f". Prossimo avviso Buy dopo un ritorno sotto {REARM_HIGH:.0f}.",
                       "Dal 1990 43 eventi: S&amp;P 500 +2,5% mediano a 30 giorni (giorno qualsiasi +1,2%). BTC dal 2019 "
                       "(13 eventi): +4,0% a 30 giorni (contro +1,5%), +4,3% a 90 (contro +6,2%).",
                       _src(q)))


def format_sell(q: dict) -> str:
    return msg(head("🔴", None, f"VIX sotto {LOW:.0f} · segnale Sell (mercato tranquillo)"),
               _value_line(q),
               "Storicamente dopo un VIX sotto 15 le azioni hanno continuato a salire (+6,2% mediano a 180 giorni): "
               "segnale debole.",
               NOTE,
               details(_since_line(q) + f". Prossimo avviso Sell dopo un ritorno sopra {REARM_LOW:.0f}.",
                       "Dal 1990 87 eventi: S&amp;P 500 +6,2% mediano a 180 giorni con il 76% di casi positivi (giorno "
                       "qualsiasi +5,6% e 74%). BTC −3,4% a 90 giorni (contro +6,2%), con pochi casi.",
                       _src(q)))


def format_first(q: dict) -> str:
    z = zone(q["value"])
    rearm = {"alta": f" Il prossimo avviso Buy arriva dopo un ritorno sotto {REARM_HIGH:.0f}.",
             "bassa": f" Il prossimo avviso Sell arriva dopo un ritorno sopra {REARM_LOW:.0f}.", "neutra": ""}[z]
    return msg(head("📊", None, f"VIX {num(q['value'])} · condizione di mercato: {LABEL[z]}"),
               _value_line(q),
               _since_line(q) + ".",
               f"Soglie: sopra {HIGH:.0f} paura alta (Buy), sotto {LOW:.0f} mercato tranquillo (Sell), in mezzo normale.",
               f"Ti avviso quando supera {HIGH:.0f} o scende sotto {LOW:.0f}, controllo ogni {STEP_H} ore.{rearm}",
               details("Storico S&amp;P 500 dopo un VIX sopra 30: +5,5% mediano a 90 giorni (giorno qualsiasi +3,1%); su "
                       "BTC misto. Dopo un VIX sotto 15 le azioni hanno continuato a salire (+6,2% mediano a 180 giorni): "
                       "segnale debole.", NOTE, _src(q)))


def giro(st: dict, now, fetch_fn=None) -> list[tuple[str, callable]]:
    """Controllo VIX del giro. Restituisce [(testo, conferma)]: chi invia chiama conferma() solo se l'invio riesce; senza
    messaggi lo stato si aggiorna subito (lista vuota). Fuori fascia o fascia già controllata: [] senza rete.
    Rete caduta: eccezione, stato invariato."""
    old = st.get(KEY)
    sl = slot(now)
    if old is not None and old.get("ultimo_check") == sl:
        return []
    q = (fetch_fn or fetch)()
    v = round(float(q["value"]), 2)
    z = zone(v)
    base = {"zona": z, "ultimo_check": sl, "valore": v, "fonte": q["source"],
            "ora": pd.Timestamp(q["time"]).isoformat() if q.get("live") else str(pd.Timestamp(q["day"]).date())}
    if old is None:
        new = {**base, "armato_alto": z != "alta", "armato_basso": z != "bassa"}
        out = [(format_first(q), "primo avvio")]
    else:
        aa, ab = bool(old.get("armato_alto", True)), bool(old.get("armato_basso", True))
        aa, ab = aa or v < REARM_HIGH, ab or v > REARM_LOW
        out = []
        if v > HIGH and aa:
            out.append((format_buy(q), "buy"))
            aa = False
        if v < LOW and ab:
            out.append((format_sell(q), "sell"))
            ab = False
        new = {**base, "armato_alto": aa, "armato_basso": ab}
        if old.get("ultimo_avviso"):
            new["ultimo_avviso"] = old["ultimo_avviso"]

    def commit(kind=None):
        if kind:
            new["ultimo_avviso"] = {"tipo": kind, "valore": v, "fascia": sl}
        st[KEY] = new

    if not out:
        commit()
        return []
    return [(t, (lambda k=k: commit(k))) for t, k in out]


def update(st: dict, now=None, send=None, fetch_fn=None) -> dict | None:
    """Aggancio per cli.daily (come guard.update): invia gli avvisi e scrive st["vix"] solo se Telegram conferma."""
    if send is None:
        from .telegram import send
    now = pd.Timestamp.now("UTC") if now is None else now
    msgs = giro(st, now, fetch_fn)
    for text, ok in msgs:
        if send(text):
            ok()
            print(f"[vix] avviso inviato ({st[KEY]['zona']}, {st[KEY]['valore']})")
        else:
            print("[vix] avviso non confermato da Telegram: si riprova al prossimo giro")
    if not msgs:
        v = st.get(KEY) or {}
        print(f"[vix] nessun avviso · fascia {v.get('ultimo_check')} · {v.get('valore')} ({v.get('zona')})")
    return st.get(KEY)
