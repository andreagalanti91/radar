"""Costruisce superficie.csv.gz e giorni.csv dal campione di scambi in cache/ (vedi scarica.py).

Uso: python3 costruisci.py

superficie.csv.gz — una riga per (data, scadenza, tipo, fascia) con almeno uno scambio valido nel campione del giorno:
    data        giorno UTC del campione (AAAA-MM-GG)
    scadenza    data di scadenza (le opzioni Deribit scadono alle 08:00 UTC)
    gg          giorni dalla 12:00 UTC di `data` alla scadenza (tempo di riferimento della superficie)
    indice      prezzo indice mediano del campione del giorno (USD)
    tipo        C / P
    fascia      fascia di moneyness ln(K/F) in %: 0 = [-2,5;+2,5], ±5 = (2,5;7,5], ±10 = (7,5;15], ±20 = (15;30], ±40 = (30;50]
    m           moneyness media ln(K/F) degli scambi della fascia (F = indice al momento dello scambio), pesata per quantità
    iv          volatilità implicita mediana pesata per quantità (frazione annua; da `iv` dello scambio Deribit)
    n           numero di scambi nella fascia
    btc         quantità scambiata (BTC)
giorni.csv — una riga per giorno scaricato: scambi nel campione, scambi validi, pagine, intero_giorno (il campione copre
tutta la giornata), indice mediano/min/max, ora del primo e dell'ultimo scambio.
Nessun valore è inventato: un giorno/scadenza/fascia senza scambi non compare.
"""
import datetime as dt
import glob
import json
import os
import gzip

import numpy as np
import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
BORDI = np.array([-0.5, -0.3, -0.15, -0.075, -0.025, 0.025, 0.075, 0.15, 0.3, 0.5])
ETICHETTE = np.array([-40, -20, -10, -5, 0, 5, 10, 20, 40])
MESI = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def scadenza_da_nome(nome):
    """'BTC-26JAN18-16000-C' -> (date(2018,1,26), 16000.0, 'C')."""
    _, s, k, t = nome.split("-")
    g, mese, anno = int(s[:-5]), MESI[s[-5:-2]], 2000 + int(s[-2:])
    return dt.date(anno, mese, g), float(k), t


def mediana_pesata(v, w):
    o = np.argsort(v)
    v, w = v[o], w[o]
    c = np.cumsum(w)
    return float(v[np.searchsorted(c, 0.5 * c[-1])])


def giorno(path):
    with gzip.open(path, "rt") as f:
        meta = json.loads(f.readline()[1:])
        df = pd.read_csv(f)
    d = os.path.basename(path)[:10]
    info = {"data": d, "scambi": len(df), "pagine": meta["pagine"], "intero_giorno": meta["intero_giorno"]}
    if df.empty:
        return info, None
    cache_nomi = {n: scadenza_da_nome(n) for n in df["instrument_name"].unique()}
    df["scad"] = df["instrument_name"].map(lambda n: cache_nomi[n][0])
    df["K"] = df["instrument_name"].map(lambda n: cache_nomi[n][1])
    df["tipo"] = df["instrument_name"].map(lambda n: cache_nomi[n][2])
    ok = (df["iv"] > 1) & (df["iv"] < 500) & (df["amount"] > 0) & (df["index_price"] > 0)
    scad_ts = pd.to_datetime(df["scad"].astype(str)).values.astype("datetime64[ms]").astype(np.int64) + 8 * 3_600_000
    ok &= scad_ts > df["timestamp"].values
    df = df[ok].copy()
    info["validi"] = len(df)
    if df.empty:
        return info, None
    df["m"] = np.log(df["K"] / df["index_price"])
    df = df[(df["m"] > BORDI[0]) & (df["m"] <= BORDI[-1])]
    df["fascia"] = ETICHETTE[np.clip(np.searchsorted(BORDI, df["m"].values, side="left") - 1, 0, len(ETICHETTE) - 1)]
    # la fascia 0 è chiusa a entrambi i lati: m == -0,025 va in 0
    df.loc[np.isclose(df["m"], -0.025), "fascia"] = 0
    indice = float(df["index_price"].median()) if len(df) else float("nan")
    ts = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    info.update(indice=round(indice, 2), indice_min=float(df["index_price"].min()), indice_max=float(df["index_price"].max()),
                primo=ts.min().strftime("%H:%M"), ultimo=ts.max().strftime("%H:%M"))
    rif = dt.datetime.fromisoformat(d) + dt.timedelta(hours=12)
    righe = []
    for (sc, tipo, fa), g in df.groupby(["scad", "tipo", "fascia"]):
        w = g["amount"].values.astype(float)
        gg = (dt.datetime.combine(sc, dt.time(8)) - rif).total_seconds() / 86400
        righe.append((d, sc.isoformat(), round(gg, 3), round(indice, 2), tipo, int(fa),
                      round(float(np.average(g["m"], weights=w)), 4),
                      round(mediana_pesata(g["iv"].values / 100, w), 4), len(g), round(float(w.sum()), 2)))
    return info, righe


def main():
    file = sorted(glob.glob(os.path.join(QUI, "cache", "*", "*.csv.gz")))
    infos, tutte = [], []
    for i, p in enumerate(file):
        try:
            info, righe = giorno(p)
        except Exception as e:  # file rotto: lo si segnala e si va avanti (si riscarica cancellandolo)
            print("ERRORE", p, e)
            continue
        infos.append(info)
        if righe:
            tutte.extend(righe)
        if i % 500 == 0:
            print(i, len(file), flush=True)
    sup = pd.DataFrame(tutte, columns=["data", "scadenza", "gg", "indice", "tipo", "fascia", "m", "iv", "n", "btc"])
    sup.to_csv(os.path.join(QUI, "superficie.csv.gz"), index=False, compression="gzip")
    pd.DataFrame(infos).to_csv(os.path.join(QUI, "giorni.csv"), index=False)
    print(f"superficie: {len(sup)} righe, {sup['data'].nunique()} giorni; giorni in cache: {len(infos)}")


if __name__ == "__main__":
    main()
