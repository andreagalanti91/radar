"""Opzioni e direzione · fase 1 · scaricamento dati (solo API pubbliche Deribit, nessun risultato qui).

Uso (dentro research/opzioni_direzione/):
    python3 scarica.py dvol BTC 1D|3600       -> dati/dvol_BTC_1D.csv / dati/dvol_BTC_3600.csv
    python3 scarica.py dvol ETH 1D|3600
    python3 scarica.py domeniche BTC|ETH [--thread 2]   -> dati/domeniche/<CUR>/AAAA-MM-GG.csv.gz (giornata INTERA)
    python3 scarica.py book BTC|ETH           -> dati/book_<CUR>_<AAAA-MM-GG>.csv.gz (istantanea attuale con open interest)

Domeniche: TUTTI gli scambi di opzioni della domenica UTC (00:00-23:59:59), dal 2021-01-03 al 2026-11-22, con il lato
dell'aggressore (direction). Paginazione per tempo con deduplica su trade_id (nessuno scambio perso a parità di millisecondo).
Cache riprendibile, richieste in serie per thread, attesa e ritentativi su 429/5xx, User-Agent generico.
"""
import csv
import datetime as dt
import gzip
import io
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.path.join(QUI, "dati")
H = {"User-Agent": "research-client"}
STORICO = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time"
CAMPI = ("timestamp", "trade_id", "instrument_name", "price", "mark_price", "iv", "index_price", "amount", "direction")
PRIMA, ULTIMA = dt.date(2021, 1, 3), dt.date(2026, 11, 22)
_sess = threading.local()


def _get(url, params, tentativi=8):
    s = getattr(_sess, "s", None)
    if s is None:
        s = _sess.s = requests.Session()
    attesa = 2.0
    for _ in range(tentativi):
        try:
            r = s.get(url, params=params, headers=H, timeout=40)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(attesa)
                attesa = min(attesa * 2, 60)
                continue
            r.raise_for_status()
            time.sleep(0.15)  # ritmo prudente
            return r.json()["result"]
        except (requests.RequestException, ValueError, KeyError):
            time.sleep(attesa)
            attesa = min(attesa * 2, 60)
    raise RuntimeError(f"richiesta fallita: {params}")


def dvol(cur, res):
    url = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
    fine = int(time.time() * 1000)
    inizio = int(dt.datetime(2021, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    dati = {}
    while True:
        r = _get(url, dict(currency=cur, resolution=res, start_timestamp=inizio, end_timestamp=fine))
        for ts, o, hi, lo, c in r["data"]:
            dati[ts] = (o, hi, lo, c)
        cont = r.get("continuation")
        if not cont or not r["data"] or cont <= inizio:
            break
        fine = cont
    p = os.path.join(DATI, f"dvol_{cur}_{res}.csv")
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "open", "high", "low", "close"])
        for ts in sorted(dati):
            w.writerow([dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), *dati[ts]])
    print(f"dvol {cur} {res}: {len(dati)} punti")


def _percorso(cur, giorno):
    return os.path.join(DATI, "domeniche", cur, giorno + ".csv.gz")


def giornata(cur, giorno):
    p = _percorso(cur, giorno)
    if os.path.exists(p):
        return giorno, "cache"
    t0 = int(dt.datetime.fromisoformat(giorno).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    fine = t0 + 86_400_000 - 1
    cur_ts, righe, visti, pagine = t0, [], set(), 0
    while True:
        r = _get(STORICO, dict(currency=cur, kind="option", start_timestamp=cur_ts, end_timestamp=fine,
                               count=1000, sorting="asc"))
        pagine += 1
        tr = r.get("trades", [])
        nuovi = 0
        for t in tr:
            if t["trade_id"] in visti:
                continue
            visti.add(t["trade_id"])
            nuovi += 1
            righe.append([t.get(c) for c in CAMPI])
        if not tr or not r.get("has_more"):
            break
        ultimo = tr[-1]["timestamp"]
        cur_ts = ultimo if nuovi and ultimo > cur_ts else cur_ts + 1
        if pagine > 400:
            raise RuntimeError("troppe pagine")
    buf = io.StringIO()
    buf.write("#" + json.dumps({"pagine": pagine, "scambi": len(righe), "intero_giorno": True}) + "\n")
    w = csv.writer(buf)
    w.writerow(CAMPI)
    w.writerows(righe)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p + ".tmp", "wt") as f:
        f.write(buf.getvalue())
    os.replace(p + ".tmp", p)
    return giorno, f"{pagine}p {len(righe)}s"


def domeniche(cur, thread=2):
    g, giorni = PRIMA, []
    while g <= ULTIMA:
        if not os.path.exists(_percorso(cur, g.isoformat())):
            giorni.append(g.isoformat())
        g += dt.timedelta(days=7)
    print(f"{cur}: da scaricare {len(giorni)} domeniche", flush=True)

    def sicuro(x):
        try:
            return giornata(cur, x)
        except Exception as e:
            return x, f"ERRORE {e}"

    with ThreadPoolExecutor(thread) as ex:
        for i, (x, esito) in enumerate(ex.map(sicuro, giorni), 1):
            if i % 20 == 0 or esito.startswith("ERRORE"):
                print(f"{cur} {i}/{len(giorni)} {x} {esito}", flush=True)
    print("fine", flush=True)


def book(cur):
    r = _get("https://www.deribit.com/api/v2/public/get_book_summary_by_currency", dict(currency=cur, kind="option"))
    oggi = dt.datetime.now(dt.timezone.utc)
    p = os.path.join(DATI, f"book_{cur}_{oggi.date().isoformat()}.csv.gz")
    campi = ("instrument_name", "open_interest", "volume", "mark_price", "mark_iv", "underlying_price",
             "estimated_delivery_price", "creation_timestamp")
    with gzip.open(p, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(campi)
        for x in r:
            w.writerow([x.get(c) for c in campi])
    print(f"book {cur}: {len(r)} contratti -> {p}")


if __name__ == "__main__":
    os.makedirs(DATI, exist_ok=True)
    a = sys.argv
    if a[1] == "dvol":
        dvol(a[2], a[3])
    elif a[1] == "domeniche":
        domeniche(a[2], int(a[a.index("--thread") + 1]) if "--thread" in a else 2)
    elif a[1] == "book":
        book(a[2])
