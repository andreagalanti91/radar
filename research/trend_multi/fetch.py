"""trend_multi · dati: chiusure giornaliere rettificate (split e dividendi) da Yahoo chart API pubblica, come multi_asset/fetch.py.
Salva data/<TICKER>.csv.gz (date, adj, close_raw). Taglio 20/11/2026. Eseguito DOPO il commit del PREREG."""
import time
from pathlib import Path
import pandas as pd
import requests

D = Path(__file__).resolve().parent / "data"
CUT = "2026-11-20"
UA = {"User-Agent": "research-client/1.0"}
UNIVERSE = "SPY QQQ IWM EFA VGK EEM EWJ IEF TLT LQD HYG GLD SLV DBC USO UUP FXE FXY VNQ".split()
EXTRA = {"SHY": "SHY", "IRX": "^IRX"}


def yahoo(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}"
    r = requests.get(url, params=dict(period1=-2208988800, period2=1795300000, interval="1d", events="div,splits"),
                     headers=UA, timeout=60)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").tz_localize("UTC").tz_convert(res["meta"]["exchangeTimezoneName"])
    df = pd.DataFrame({"close_raw": q["close"]}, index=idx.tz_localize(None).normalize())
    adj = res["indicators"].get("adjclose")
    df["adj"] = adj[0]["adjclose"] if adj else df["close_raw"]
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close_raw"])
    df = df[df.index <= CUT]
    df.index.name = "date"
    return df[["adj", "close_raw"]].round(6)


if __name__ == "__main__":
    for name, sym in {**{u: u for u in UNIVERSE}, **EXTRA}.items():
        if (D / f"{name}.csv.gz").exists():
            continue
        for k in range(6):
            try:
                df = yahoo(sym)
                df.to_csv(D / f"{name}.csv.gz")
                print(f"{name:5s} {df.index[0].date()} -> {df.index[-1].date()} {len(df):6d} righe")
                break
            except Exception as e:  # noqa: BLE001
                print(name, "ERRORE", type(e).__name__, str(e)[:100]); time.sleep(10 + 10 * k)
        time.sleep(3)
