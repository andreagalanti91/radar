"""Multi-asset · fase 1: scarica i dati giornalieri (fonti gratuite e pubbliche), salva CSV in data/.
- Yahoo chart API pubblica (query1.finance.yahoo.com/v8/finance/chart): OHLC giornaliero dal primo dato; per azioni ed ETF
  OHLC rettificati per split E dividendi con il fattore adjclose/close (Yahoo dà OHLC già rettificati per split).
- VIX: CBOE (cdn.cboe.com, storico ufficiale dal 1990) come fonte principale; FRED VIXCLS come controllo.
Taglio: ultima chiusura di venerdì 2026-11-20 (ultima candela settimanale W-FRI completa).
Stooq: connessione rifiutata da questo container (non usato).
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import pandas as pd
import requests

D = Path(__file__).resolve().parent / "data"
CUT = "2026-11-20"
UA = {"User-Agent": "research-client/1.0"}
MAIN = {"SPX": "^GSPC", "SPXTR": "^SP500TR", "GOLD": "GC=F", "SILVER": "SI=F", "GLD": "GLD", "SLV": "SLV",
        "NVDA": "NVDA", "AAPL": "AAPL", "MSFT": "MSFT", "GOOGL": "GOOGL", "AMZN": "AMZN", "META": "META",
        "AVGO": "AVGO", "TSLA": "TSLA", "BRK-B": "BRK-B", "LLY": "LLY", "VIX_YH": "^VIX"}
# componenti del Dow Jones al 01/01/2000 con storia continua su Yahoo (esclusi: EK, GM e AT&T storici, Alcoa, DuPont storica)
DOW2000 = "AXP BA CAT C KO XOM GE HPQ HD HON IBM INTC IP JNJ JPM MCD MRK MMM MO PG WMT DIS RTX T".split()


def yahoo(sym: str) -> pd.DataFrame:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}"
    r = requests.get(url, params=dict(period1=-2208988800, period2=1795300000, interval="1d", events="div,splits"),
                     headers=UA, timeout=60)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").tz_localize("UTC").tz_convert(res["meta"]["exchangeTimezoneName"])
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")}, index=idx.tz_localize(None).normalize())
    adj = res["indicators"].get("adjclose")
    df["adjclose"] = adj[0]["adjclose"] if adj else df["close"]
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close"])
    df = df[df.index <= CUT]
    fac = df["adjclose"] / df["close"]
    for k in ("open", "high", "low"):
        df[k] = df[k].fillna(df["close"])
    out = df[["open", "high", "low", "close"]].mul(fac, axis=0)
    out["close_raw"], out["volume"] = df["close"], df["volume"]
    out.index.name = "date"
    return out


def vix() -> None:
    r = requests.get("https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv", headers=UA, timeout=60)
    v = pd.read_csv(io.StringIO(r.text))
    v.columns = [c.lower() for c in v.columns]
    v["date"] = pd.to_datetime(v["date"], format="%m/%d/%Y")
    v.set_index("date").loc[:CUT].to_csv(D / "VIX.csv.gz")
    for _ in range(3):   # FRED: solo controllo, connessione instabile da questo container
        try:
            r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params=dict(id="VIXCLS"), headers=UA, timeout=60)
            pd.read_csv(io.StringIO(r.text)).to_csv(D / "VIX_fred.csv.gz", index=False)
            return
        except requests.RequestException as e:
            print("FRED non raggiungibile:", type(e).__name__)
            time.sleep(3)


if __name__ == "__main__":
    vix()
    which = sys.argv[1:] or ["main", "dow"]
    jobs = ([(n, s, D) for n, s in MAIN.items()] if "main" in which else []) + \
           ([(s, s, D / "dow2000") for s in DOW2000] if "dow" in which else [])
    for name, sym, folder in jobs:
        try:
            df = yahoo(sym)
            df.to_csv(folder / f"{name}.csv.gz")
            print(f"{name:8s} {sym:9s} {df.index[0].date()} -> {df.index[-1].date()} {len(df):6d} righe")
        except Exception as e:  # noqa: BLE001
            print(name, sym, "ERRORE", e)
        time.sleep(0.5)
