"""dati_nuovi · scarico delle fonti nuove gratuite (FASE 1). Solo API/archivi pubblici, User-Agent onesto, pause fra le richieste.
Ogni fonte va in una sua cartella sotto data/ (dati scaricati = non fidati: solo CSV/JSON letti con pandas/json).

Fonti:
  cot/      CFTC Traders in Financial Futures (futures only, Socrata publicreporting.cftc.gov, dataset gpe5-46if):
            Bitcoin CME 133741, Micro Bitcoin 133742, Ether CME 146021, Micro Ether 146022.
  basis/    Deribit: future trimestrali scaduti e in corso (BTC/ETH) + perpetual, candele 1D (public/get_tradingview_chart_data);
            Binance coin-M trimestrali da data.binance.vision (controllo).
  funding/  Deribit perpetual (public/get_funding_rate_history, orario), Hyperliquid (fundingHistory), OKX e Bitget (solo il
            periodo che le API pubbliche restituiscono). Binance è già nei dati del repo.
  miner/    blockchain.com charts API: hash-rate, difficulty, miners-revenue, transaction-fees-usd.
  mvrv/     CoinMetrics community API: CapMVRVCur di ETH (BTC è già in research/utxo_pl/mvrv.csv).
Uso: python -I research/dati_nuovi/fetch.py [cot|basis|funding|miner|mvrv|all]
"""
from __future__ import annotations

import io
import json
import sys
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
D = HERE / "data"
UA = {"User-Agent": "radar-research/1.0 (personal non-commercial research script; python-requests)"}
S = requests.Session()
S.headers.update(UA)


def get(url, params=None, js=True, tries=4, pause=0.25, **kw):
    for k in range(tries):
        try:
            r = S.get(url, params=params, timeout=60, **kw)
            if r.status_code == 429:
                time.sleep(5 * (k + 1)); continue
            r.raise_for_status()
            time.sleep(pause)
            return r.json() if js else r.content
        except Exception as e:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 * (k + 1))


def ms(d):
    return int(pd.Timestamp(d, tz="UTC").timestamp() * 1000)


# ------------------------------------------------------------------ CFTC COT (TFF futures only)
def cot():
    out = D / "cot"; out.mkdir(parents=True, exist_ok=True)
    codes = {"133741": "BTC_CME", "133742": "BTC_MICRO", "146021": "ETH_CME", "146022": "ETH_MICRO"}
    url = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
    for c, name in codes.items():
        rows, off = [], 0
        while True:
            js = get(url, {"$where": f"cftc_contract_market_code='{c}'", "$order": "report_date_as_yyyy_mm_dd",
                           "$limit": 5000, "$offset": off})
            rows += js
            if len(js) < 5000:
                break
            off += 5000
        df = pd.DataFrame(rows)
        df.to_csv(out / f"{name}.csv", index=False)
        print("COT", name, len(df), df["report_date_as_yyyy_mm_dd"].min()[:10] if len(df) else "-",
              df["report_date_as_yyyy_mm_dd"].max()[:10] if len(df) else "-")


# ------------------------------------------------------------------ base dei future
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def last_friday(y, m):
    d = date(y, m + 1, 1) - timedelta(days=1) if m < 12 else date(y, 12, 31)
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


def deribit_chart(inst, a, b):
    try:
        js = get("https://www.deribit.com/api/v2/public/get_tradingview_chart_data",
                 {"instrument_name": inst, "start_timestamp": ms(a), "end_timestamp": ms(b), "resolution": "1D"}, tries=2)
    except Exception:  # noqa: BLE001  (strumento inesistente: 400)
        return None
    r = js.get("result") or {}
    if r.get("status") != "ok" or not r.get("ticks"):
        return None
    return pd.DataFrame({"t": pd.to_datetime(r["ticks"], unit="ms", utc=True).tz_localize(None), "open": r["open"],
                         "high": r["high"], "low": r["low"], "close": r["close"], "volume": r["volume"]})


def basis():
    out = D / "basis"; out.mkdir(parents=True, exist_ok=True)
    today = pd.Timestamp.now("UTC").tz_localize(None).normalize()
    for cur in ("BTC", "ETH"):
        if (out / f"deribit_{cur}_perp.csv").exists():
            continue
        frames = []
        for y in range(2017, 2028):
            for m in (3, 6, 9, 12):
                ex = last_friday(y, m)
                if pd.Timestamp(ex) - pd.Timedelta(days=200) > today:
                    continue
                inst = f"{cur}-{ex.day}{MON[m - 1]}{str(y)[2:]}"
                a = pd.Timestamp(ex) - pd.Timedelta(days=200)
                df = deribit_chart(inst, a, min(pd.Timestamp(ex) + pd.Timedelta(days=1), today))
                if df is None:
                    print("  nessun dato", inst); continue
                df["inst"], df["expiry"] = inst, str(ex)
                frames.append(df)
        fut = pd.concat(frames, ignore_index=True)
        fut.to_csv(out / f"deribit_{cur}_quarterly.csv", index=False)
        # perpetual (riferimento "spot" della stessa borsa), a blocchi di un anno
        pp = []
        for y in range(2018, today.year + 1):
            df = deribit_chart(f"{cur}-PERPETUAL", f"{y}-01-01", min(pd.Timestamp(f"{y + 1}-01-01"), today))
            if df is not None:
                pp.append(df)
        perp = pd.concat(pp, ignore_index=True).drop_duplicates("t")
        perp.to_csv(out / f"deribit_{cur}_perp.csv", index=False)
        print("BASE", cur, "trimestrali", fut["inst"].nunique(), fut["t"].min().date(), fut["t"].max().date(),
              "| perp", perp["t"].min().date(), perp["t"].max().date())
    # Binance coin-M trimestrali (controllo): elenco da S3 e file mensili 1d
    for cur in ("BTC", "ETH"):
        lst = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision",
                  {"prefix": f"data/futures/cm/monthly/klines/", "delimiter": "/"}, js=False).decode()
        syms = sorted(set(x.split("</Prefix>")[0].split("/")[-2] for x in lst.split("<Prefix>")[1:] if f"/{cur}USD_2" in x.split("</Prefix>")[0]))
        rows = []
        for s in syms:
            yy, mm, dd = 2000 + int(s[-6:-4]), int(s[-4:-2]), int(s[-2:])
            ex = pd.Timestamp(yy, mm, dd)
            for k in range(7, -1, -1):
                mth = (ex - pd.DateOffset(months=k)).strftime("%Y-%m")
                if pd.Timestamp(mth + "-01") > today:
                    continue
                u = f"https://data.binance.vision/data/futures/cm/monthly/klines/{s}/1d/{s}-1d-{mth}.zip"
                try:
                    zb = get(u, js=False, tries=2)
                except Exception:  # noqa: BLE001
                    continue
                with zipfile.ZipFile(io.BytesIO(zb)) as z:
                    raw = z.read(z.namelist()[0]).decode()
                lines = [l for l in raw.splitlines() if l and l[0].isdigit()]
                for l in lines:
                    p = l.split(",")
                    rows.append({"t": pd.to_datetime(int(p[0]), unit="ms"), "close": float(p[4]), "inst": s, "expiry": str(ex.date())})
        if rows:
            b = pd.DataFrame(rows).drop_duplicates(["t", "inst"])
            b.to_csv(out / f"binance_cm_{cur}_quarterly.csv", index=False)
            print("BINANCE CM", cur, b["inst"].nunique(), b["t"].min().date(), b["t"].max().date())


# ------------------------------------------------------------------ funding multi-exchange
def funding():
    out = D / "funding"; out.mkdir(parents=True, exist_ok=True)
    today = pd.Timestamp.now("UTC").tz_localize(None).normalize()
    for cur in ("BTC", "ETH"):
        # Deribit: orario, finestre di 30 giorni
        rows, a = [], pd.Timestamp("2019-01-01")
        while a < today:
            b = min(a + pd.Timedelta(days=30), today)
            js = get("https://www.deribit.com/api/v2/public/get_funding_rate_history",
                     {"instrument_name": f"{cur}-PERPETUAL", "start_timestamp": ms(a), "end_timestamp": ms(b)})
            rows += js.get("result") or []
            a = b
        df = pd.DataFrame(rows).drop_duplicates("timestamp")
        df.to_csv(out / f"deribit_{cur}.csv", index=False)
        print("FUND deribit", cur, len(df), pd.to_datetime(df["timestamp"].min(), unit="ms").date() if len(df) else "-")
        # Hyperliquid: 500 righe a richiesta
        rows, st = [], ms("2023-01-01")
        while True:
            r = S.post("https://api.hyperliquid.xyz/info", json={"type": "fundingHistory", "coin": cur, "startTime": st}, timeout=60)
            r.raise_for_status(); js = r.json(); time.sleep(0.3)
            if not js:
                break
            rows += js
            nst = js[-1]["time"] + 1
            if nst <= st or len(js) < 2:
                break
            st = nst
        df = pd.DataFrame(rows).drop_duplicates("time")
        df.to_csv(out / f"hyperliquid_{cur}.csv", index=False)
        print("FUND hyperliquid", cur, len(df), pd.to_datetime(df["time"].min(), unit="ms").date() if len(df) else "-")
        # OKX: API pubblica (solo gli ultimi ~3 mesi)
        rows, after = [], None
        for _ in range(40):
            p = {"instId": f"{cur}-USDT-SWAP", "limit": 100}
            if after:
                p["after"] = after
            js = get("https://www.okx.com/api/v5/public/funding-rate-history", p).get("data") or []
            if not js:
                break
            rows += js; after = js[-1]["fundingTime"]
        df = pd.DataFrame(rows).drop_duplicates("fundingTime") if rows else pd.DataFrame()
        df.to_csv(out / f"okx_{cur}.csv", index=False)
        print("FUND okx", cur, len(df), pd.to_datetime(int(df["fundingTime"].astype("int64").min()), unit="ms").date() if len(df) else "-")
        # Bitget: API pubblica (pagine ≤ 100)
        rows = []
        for pg in range(1, 101):
            js = get("https://api.bitget.com/api/v2/mix/market/history-fund-rate",
                     {"symbol": f"{cur}USDT", "productType": "usdt-futures", "pageSize": 100, "pageNo": pg}).get("data") or []
            if not js:
                break
            rows += js
        df = pd.DataFrame(rows).drop_duplicates("fundingTime") if rows else pd.DataFrame()
        df.to_csv(out / f"bitget_{cur}.csv", index=False)
        print("FUND bitget", cur, len(df), pd.to_datetime(int(df["fundingTime"].astype("int64").min()), unit="ms").date() if len(df) else "-")


# ------------------------------------------------------------------ miner
def miner():
    out = D / "miner"; out.mkdir(parents=True, exist_ok=True)
    for ch in ("hash-rate", "difficulty", "miners-revenue", "transaction-fees-usd"):
        js = get(f"https://api.blockchain.info/charts/{ch}", {"timespan": "all", "format": "json", "sampled": "false"})
        df = pd.DataFrame(js["values"]); df["date"] = pd.to_datetime(df["x"], unit="s").dt.date
        df[["date", "y"]].rename(columns={"y": ch}).to_csv(out / f"{ch}.csv", index=False)
        print("MINER", ch, len(df), df["date"].min(), df["date"].max())


def mvrv():
    out = D / "mvrv"; out.mkdir(parents=True, exist_ok=True)
    rows, nxt = [], None
    p = {"assets": "eth", "metrics": "CapMVRVCur", "frequency": "1d", "start_time": "2016-01-01", "page_size": 10000}
    url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    while True:
        js = get(nxt or url, None if nxt else p)
        rows += js.get("data", [])
        nxt = js.get("next_page_url")
        if not nxt:
            break
    df = pd.DataFrame(rows)
    df["date"] = df["time"].str[:10]
    df[["date", "CapMVRVCur"]].rename(columns={"CapMVRVCur": "mvrv"}).to_csv(out / "eth_mvrv.csv", index=False)
    print("MVRV eth", len(df), df["date"].min(), df["date"].max())


def cmflows():
    """CoinMetrics community (gratuita, senza chiave, 10 richieste/6 s): flussi verso/da exchange e saldo sugli exchange.
    Metriche "flash": possono essere riviste dopo la pubblicazione (si salvano anche stato e ora di stato)."""
    out = D / "cmflows"; out.mkdir(parents=True, exist_ok=True)
    url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    for a in ("btc", "eth"):
        rows, nxt = [], None
        p = {"assets": a, "metrics": "FlowInExNtv,FlowOutExNtv,SplyExNtv,HashRate", "frequency": "1d",
             "start_time": "2016-01-01", "page_size": 10000, "paging_from": "start"}
        while True:
            js = get(nxt or url, None if nxt else p, pause=0.7)
            rows += js.get("data", [])
            nxt = js.get("next_page_url")
            if not nxt:
                break
        df = pd.DataFrame(rows); df["date"] = df["time"].str[:10]
        df.drop(columns=["time"]).to_csv(out / f"{a}_flows.csv", index=False)
        print("CMFLOWS", a, len(df), df["date"].min(), df["date"].max(), "| colonne:", ",".join(c for c in df.columns if "status" not in c))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in (("cot", cot), ("basis", basis), ("funding", funding), ("miner", miner), ("mvrv", mvrv), ("cmflows", cmflows)):
        if what in (k, "all"):
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                print("ERRORE", k, repr(e)[:300])
