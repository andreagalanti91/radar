"""Scarica un campione giornaliero di scambi di opzioni BTC da Deribit (API pubblica) e il DVOL.

Uso:
    python3 scarica.py scambi 2018-01-01 2026-11-23 [--thread 3]
    python3 scarica.py dvol

Campionamento (per non scaricare tutto il volume): per ogni giorno UTC al massimo 3 richieste da 1000 scambi,
in ordine crescente di tempo, che partono dalle 00:00, dalle 08:00 e dalle 16:00 UTC (o dal punto in cui era arrivata
la pagina precedente, se oltre). Nei giorni poco liquidi (2018-2020) la prima pagina copre spesso l'intera giornata.
Cache riprendibile: cache/AAAA/AAAA-MM-GG.csv.gz (una riga di commento iniziale con i metadati del campione).
Solo API pubblica, richieste in serie per thread, pausa e ritentativi su 429/5xx, User-Agent generico.
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
CACHE = os.path.join(QUI, "cache")
URL = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time"
H = {"User-Agent": "research-client"}
FINESTRE_H = (0, 8, 16)
CAMPI = ("timestamp", "instrument_name", "price", "mark_price", "iv", "index_price", "amount")
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
            return r.json()["result"]
        except (requests.RequestException, ValueError, KeyError):
            time.sleep(attesa)
            attesa = min(attesa * 2, 60)
    raise RuntimeError(f"richiesta fallita dopo {tentativi} tentativi: {params}")


def percorso(giorno):
    return os.path.join(CACHE, giorno[:4], giorno + ".csv.gz")


def scarica_giorno(giorno):
    p = percorso(giorno)
    if os.path.exists(p):
        return giorno, "cache"
    t0 = int(dt.datetime.fromisoformat(giorno).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    fine = t0 + 86_400_000 - 1
    cursore, righe, visti, pagine, continuo, intero = t0, [], set(), 0, True, False
    for h in FINESTRE_H:
        inizio = max(cursore, t0 + h * 3_600_000)
        if inizio > fine:
            intero = continuo
            break
        if inizio > cursore:
            continuo = False  # salto: tra la pagina precedente e questa finestra ci sono scambi non presi
        res = _get(URL, dict(currency="BTC", kind="option", start_timestamp=inizio, end_timestamp=fine,
                             count=1000, sorting="asc"))
        pagine += 1
        tr = res.get("trades", [])
        for t in tr:
            if t["trade_id"] in visti:
                continue
            visti.add(t["trade_id"])
            righe.append([t.get(c) for c in CAMPI])
        if tr:
            cursore = tr[-1]["timestamp"] + 1
        if not res.get("has_more"):
            intero = continuo
            break
    buf = io.StringIO()
    meta = {"pagine": pagine, "scambi": len(righe), "intero_giorno": bool(intero)}
    buf.write("#" + json.dumps(meta) + "\n")
    w = csv.writer(buf)
    w.writerow(CAMPI)
    w.writerows(righe)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with gzip.open(tmp, "wt") as f:
        f.write(buf.getvalue())
    os.replace(tmp, p)
    return giorno, f"{pagine}p {len(righe)}s"


def scambi(da, a, thread=3):
    d0, d1 = dt.date.fromisoformat(da), dt.date.fromisoformat(a)
    giorni = [(d0 + dt.timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]
    giorni = [g for g in giorni if not os.path.exists(percorso(g))]
    print(f"da scaricare: {len(giorni)} giorni", flush=True)
    fatti = 0
    with ThreadPoolExecutor(thread) as ex:
        for g, esito in ex.map(_sicuro, giorni):
            fatti += 1
            if fatti % 25 == 0 or esito.startswith("ERRORE"):
                print(f"{fatti}/{len(giorni)} {g} {esito}", flush=True)
    print("fine", flush=True)


def _sicuro(g):
    try:
        return scarica_giorno(g)
    except Exception as e:  # una giornata rotta non ferma il download; si riprova al prossimo lancio
        return g, f"ERRORE {e}"


def dvol():
    url = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
    fine = int(time.time() * 1000)
    inizio = int(dt.datetime(2021, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    dati = {}
    while True:
        res = _get(url, dict(currency="BTC", resolution="1D", start_timestamp=inizio, end_timestamp=fine))
        for ts, o, hi, lo, c in res["data"]:
            dati[ts] = (o, hi, lo, c)
        cont = res.get("continuation")
        if not cont or not res["data"] or cont <= inizio:
            break
        fine = cont
        time.sleep(0.5)
    with open(os.path.join(QUI, "dvol.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close"])
        for ts in sorted(dati):
            d = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).date().isoformat()
            w.writerow([d, *dati[ts]])
    print(f"dvol: {len(dati)} giorni")


if __name__ == "__main__":
    if sys.argv[1] == "dvol":
        dvol()
    else:
        th = int(sys.argv[sys.argv.index("--thread") + 1]) if "--thread" in sys.argv else 3
        scambi(sys.argv[2], sys.argv[3], th)
