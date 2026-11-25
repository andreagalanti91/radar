"""W3.2 asset ciclo 2 · azioni · download prezzi giornalieri (Yahoo chart API pubblica, come research/multi_asset/fetch.py).

Per ogni ticker di universe.csv (colonna yahoo, più yahoo_us se il perp si riferisce all'ADR USA) salva data/px/<TICKER>.csv.gz:
  date, open, high, low, close      OHLC rettificati per frazionamenti E dividendi (fattore adjclose/close, come multi_asset)
  close_raw                          chiusura rettificata SOLO per frazionamenti (è il "close" di Yahoo; stesso nome di multi_asset)
  open_raw, high_raw, low_raw        idem per apertura, massimo, minimo
  close_unadj                        chiusura davvero non rettificata (close_raw × frazionamenti successivi, dagli eventi Yahoo)
  volume                             volume giornaliero (Yahoo lo rettifica per i frazionamenti)
Prezzi in valuta locale (meta.csv: valuta, borsa, fuso); cambi USD giornalieri in data/fx/<VALUTA>.csv.gz (USD per unità).
Dal 2019-01-01 all'ultima seduta disponibile; pausa 0,6 s fra le richieste; User-Agent generico onesto.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
D = HERE / "data"
UA = {"User-Agent": "research-client/1.0"}
P1 = 1546300800          # 2019-01-01 UTC
P2 = int(time.time()) + 86400


def yahoo(sym: str) -> tuple[pd.DataFrame, dict]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}"
    for k in range(3):
        try:
            r = requests.get(url, params=dict(period1=P1, period2=P2, interval="1d", events="div,splits"), headers=UA, timeout=60)
            if r.status_code == 404:
                raise ValueError("404 ticker sconosciuto")
            r.raise_for_status()
            break
        except requests.RequestException:
            if k == 2:
                raise
            time.sleep(5 * (k + 1))
    res = r.json()["chart"]["result"][0]
    meta = res["meta"]
    if not res.get("timestamp"):
        raise ValueError("nessun dato")
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").tz_localize("UTC").tz_convert(meta["exchangeTimezoneName"])
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")}, index=idx.tz_localize(None).normalize())
    adj = res["indicators"].get("adjclose")
    df["adjclose"] = adj[0]["adjclose"] if adj else df["close"]
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close"])
    for k in ("open", "high", "low"):
        df[k] = df[k].fillna(df["close"])
    fac = df["adjclose"] / df["close"]
    out = df[["open", "high", "low", "close"]].mul(fac, axis=0)
    out["open_raw"], out["high_raw"], out["low_raw"], out["close_raw"] = df["open"], df["high"], df["low"], df["close"]
    # frazionamenti: il close di Yahoo è già diviso per i frazionamenti successivi; li rimettiamo per il vero non rettificato
    spl = res.get("events", {}).get("splits", {})
    mult = pd.Series(1.0, index=df.index)
    for e in spl.values():
        d = pd.to_datetime(e["date"], unit="s").tz_localize("UTC").tz_convert(meta["exchangeTimezoneName"]).tz_localize(None).normalize()
        ratio = float(e["numerator"]) / float(e["denominator"])
        if ratio > 0:
            mult[mult.index < d] *= ratio
    out["close_unadj"] = df["close"] * mult
    out["volume"] = df["volume"]
    out.index.name = "date"
    info = dict(currency=meta.get("currency"), exchange=meta.get("exchangeName"), full_exchange=meta.get("fullExchangeName"),
                tz=meta.get("exchangeTimezoneName"), instrument=meta.get("instrumentType"), long_name=meta.get("longName"),
                n_splits=len(spl), n_div=len(res.get("events", {}).get("dividends", {})))
    return out, info


def fx(cur: str) -> pd.DataFrame:
    """USD per unità di valuta locale. Yahoo: 'EURUSD=X' (USD per EUR); per GBp/ZAc/ILA si divide per 100."""
    base = {"GBp": "GBP", "ZAc": "ZAR", "ILA": "ILS"}.get(cur, cur)
    df, _ = yahoo(f"{base}USD=X")
    s = df[["close_raw"]].rename(columns={"close_raw": "usd_per_unit"})
    if cur in ("GBp", "ZAc", "ILA"):
        s = s / 100.0
    return s


if __name__ == "__main__":
    uni = pd.read_csv(HERE / "universe.csv")
    (D / "px").mkdir(parents=True, exist_ok=True)
    (D / "fx").mkdir(parents=True, exist_ok=True)
    syms = [s for s in pd.concat([uni["yahoo"], uni.get("yahoo_us", pd.Series(dtype=str))]).dropna().unique() if s]
    only = set(sys.argv[1:])
    rows = []
    old = pd.read_csv(D / "meta.csv").set_index("yahoo") if (D / "meta.csv").exists() else None
    for s in syms:
        if only and s not in only:
            if old is not None and s in old.index:
                rows.append(dict(yahoo=s, **old.loc[s].to_dict()))
            continue
        try:
            df, info = yahoo(s)
            df.to_csv(D / "px" / f"{s}.csv.gz")
            rows.append(dict(yahoo=s, first=str(df.index[0].date()), last=str(df.index[-1].date()), rows=len(df),
                             zero_vol=int((df["volume"].fillna(0) == 0).sum()), **info))
            print(f"{s:12s} {df.index[0].date()} -> {df.index[-1].date()} {len(df):5d} {info['currency']} {info['exchange']}")
        except Exception as e:  # noqa: BLE001
            rows.append(dict(yahoo=s, error=str(e)[:120]))
            print(s, "ERRORE", e)
        time.sleep(0.6)
    meta = pd.DataFrame(rows)
    meta["downloaded"] = pd.Timestamp.now("UTC").strftime("%Y-%m-%d")
    meta.to_csv(D / "meta.csv", index=False)
    for cur in sorted(c for c in meta["currency"].dropna().unique() if c != "USD"):
        try:
            fx(cur).to_csv(D / "fx" / f"{cur}.csv.gz")
            print("fx", cur, "ok")
        except Exception as e:  # noqa: BLE001
            print("fx", cur, "ERRORE", e)
        time.sleep(0.6)
