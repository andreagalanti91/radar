"""tradera_test · dati (23/11/2026). Fonti pubbliche, nessuna modifica a radar/.

- LMT giornaliero: Yahoo chart API pubblica (stessa funzione di research/multi_asset/fetch.py), OHLC NON rettificati per i
  dividendi (come il grafico di TradingView) + adjclose; salvato in data/LMT_raw.csv.gz.
- NVDA giornaliero: cache di research/multi_asset/data/NVDA.csv.gz (OHLC rettificati) riportata ai prezzi non rettificati
  per i dividendi con il fattore close_raw/close (Yahoo li dà già rettificati per gli split).
- BTCUSDT ed ETHUSDT giornalieri dal primo dato (08/2017): data-api.binance.vision (mirror pubblico dei dati di mercato
  Binance; api.binance.com risponde 451 da qui). Il 4h di BTC si legge da research/ema_sma/data.
- Azioni del Dow 2000 con perpetuo OKX/Bitget (universo U2 di research/trend_multi/ADDENDUM.md): cache di multi_asset.
Taglio: 2026-11-20 per le azioni (ultimo venerdì), 2026-11-22 per le crypto (ultima candela chiusa).
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
D = HERE / "data"
MA = HERE.parents[0] / "multi_asset" / "data"
UA = {"User-Agent": "research-client/1.0"}
U2 = "BA CAT C GE HD HPQ IBM INTC JNJ JPM KO MCD MO MRK MSFT PG RTX T WMT XOM".split()


def yahoo_raw(sym: str) -> pd.DataFrame:
    for k in range(6):
        host = "query1" if k % 2 == 0 else "query2"
        r = requests.get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{sym}",
                         params=dict(period1=-2208988800, period2=1795300000, interval="1d", events="div,splits"),
                         headers=UA, timeout=60)
        if r.status_code == 200:
            break
        time.sleep(10 + 10 * k)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").tz_localize("UTC").tz_convert(res["meta"]["exchangeTimezoneName"])
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")}, index=idx.tz_localize(None).normalize())
    df["adjclose"] = res["indicators"]["adjclose"][0]["adjclose"]
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close"])
    df.index.name = "date"
    return df[df.index <= "2026-11-20"]


def binance_1d(sym: str) -> pd.DataFrame:
    rows, start = [], 1500000000000
    while True:
        r = requests.get("https://data-api.binance.vision/api/v3/klines",
                         params=dict(symbol=sym, interval="1d", startTime=start, limit=1000), timeout=60)
        r.raise_for_status()
        x = r.json()
        if not x:
            break
        rows += x
        start = x[-1][0] + 86400000
        if len(x) < 1000:
            break
    df = pd.DataFrame([[pd.Timestamp(int(a[0]), unit="ms")] + [float(v) for v in a[1:6]] for a in rows],
                      columns=["date", "open", "high", "low", "close", "volume"]).set_index("date")
    return df[df.index <= "2026-11-22"]


def stock(name: str, raw: bool = False) -> pd.DataFrame:
    """Azione giornaliera: rettificata (backtest) o non rettificata per i dividendi (replica dei grafici)."""
    if name == "LMT":
        d = pd.read_csv(D / "LMT_raw.csv.gz", index_col=0, parse_dates=True)
        if raw:
            return d[["open", "high", "low", "close", "volume"]]
        f = d["adjclose"] / d["close"]
        return d[["open", "high", "low", "close"]].mul(f, axis=0).assign(volume=d["volume"])
    p = MA / ("dow2000" if name not in ("NVDA", "MSFT") else "") / f"{name}.csv.gz"
    d = pd.read_csv(p, index_col=0, parse_dates=True)
    if raw:
        f = d["close_raw"] / d["close"]
        return d[["open", "high", "low", "close"]].mul(f, axis=0).assign(volume=d["volume"])
    return d[["open", "high", "low", "close", "volume"]]


def crypto(sym: str, tf: str = "1d") -> pd.DataFrame:
    if tf == "4h":
        d = pd.read_csv(HERE.parents[0] / "ema_sma" / "data" / "BTCUSDT_4h.csv.gz", index_col=0, parse_dates=True)
        d.columns = ["open", "high", "low", "close", "volume"][:len(d.columns)]
        return d
    return pd.read_csv(D / f"{sym}_1d.csv.gz", index_col=0, parse_dates=True)


if __name__ == "__main__":
    if not (D / "LMT_raw.csv.gz").exists():
        yahoo_raw("LMT").to_csv(D / "LMT_raw.csv.gz")
    for s in ("BTCUSDT", "ETHUSDT"):
        df = binance_1d(s)
        df.to_csv(D / f"{s}_1d.csv.gz")
        print(s, df.index[0].date(), df.index[-1].date(), len(df))
    for n in ["LMT", "NVDA"] + U2:
        d = stock(n)
        print(f"{n:5s} {d.index[0].date()} -> {d.index[-1].date()} {len(d)}")
