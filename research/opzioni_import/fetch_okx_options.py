"""Scarica da OKX (API pubblica) le opzioni su BTC: fotografia della catena di oggi e storico giornaliero dei contratti ancora vivi.

OKX non espone lo storico dei contratti gia' scaduti: per avere prezzi veri nel tempo bisogna lanciare questo script ogni giorno
e accumulare le fotografie. Lo storico delle candele copre solo i contratti quotati oggi, dalla loro data di quotazione.

Uscite in data/opzioni/okx/:
  catena_AAAA-MM-GG.csv.gz   una riga per contratto: denaro, lettera, ultimo, volatilita' (denaro/lettera/mark), delta, prezzo a termine
  candele_1Dutc.csv.gz       candele giornaliere (UTC) di tutti i contratti vivi, prezzo in BTC
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "opzioni" / "okx"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://www.okx.com/api/v5/"


def get(path: str, tries: int = 4) -> list:
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + path, headers={"User-Agent": "research-client"}), timeout=30) as r:
                d = json.load(r)
            if d.get("code") == "0":
                return d["data"]
            if d.get("code") == "50011":                      # troppe richieste
                time.sleep(1.5 * (k + 1))
                continue
            return []
        except Exception:
            time.sleep(1.5 * (k + 1))
    return []


def chain() -> pd.DataFrame:
    inst = pd.DataFrame(get("public/instruments?instType=OPTION&uly=BTC-USD"))[["instId", "stk", "optType", "expTime", "listTime", "ctMult", "settleCcy", "ctType"]]
    tick = pd.DataFrame(get("market/tickers?instType=OPTION&uly=BTC-USD"))[["instId", "last", "bidPx", "askPx", "bidSz", "askSz", "vol24h"]]
    summ = pd.DataFrame(get("public/opt-summary?uly=BTC-USD"))[["instId", "bidVol", "askVol", "markVol", "volLv", "delta", "fwdPx", "ts"]]
    # due famiglie: BTC-USD (inverse, premio e regolamento in BTC) e BTC-USD_UM (lineari, premio e regolamento in USD: le sole offerte nel SEE)
    d = inst.merge(tick, on="instId", how="left").merge(summ, on="instId", how="left")
    d["scadenza"] = pd.to_datetime(d.expTime.astype("int64"), unit="ms")
    d["quotata"] = pd.to_datetime(d.listTime.astype("int64"), unit="ms")
    return d.drop(columns=["expTime", "listTime"])


def candles(ids: list) -> pd.DataFrame:
    rows = []
    for n, i in enumerate(ids):
        after = ""
        while True:
            x = get(f"market/history-candles?instId={i}&bar=1Dutc&limit=100" + (f"&after={after}" if after else ""))
            rows += [(i, int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in x]
            if len(x) < 100:
                break
            after = x[-1][0]
        time.sleep(0.11)
        if n % 200 == 0:
            print(n, "/", len(ids), len(rows), flush=True)
    c = pd.DataFrame(rows, columns=["instId", "ts", "open", "high", "low", "close", "contratti"])
    c["data"] = pd.to_datetime(c.ts, unit="ms")
    return c.drop(columns="ts").sort_values(["instId", "data"])


if __name__ == "__main__":
    ch = chain()
    day = pd.Timestamp.now("UTC").strftime("%Y-%m-%d")
    ch.to_csv(OUT / f"catena_{day}.csv.gz", index=False)
    print("catena:", len(ch), "contratti,", ch.scadenza.nunique(), "scadenze")
    if "--candele" in sys.argv:
        ids = ch[ch.scadenza - ch.quotata > pd.Timedelta(days=6)].instId.drop_duplicates().tolist()      # i contratti giornalieri hanno pochi giorni di storia
        c = candles(ids)
        c.to_csv(OUT / "candele_1Dutc.csv.gz", index=False)
        print("candele:", len(c), "righe,", c.instId.nunique(), "contratti, dal", c.data.min().date())
