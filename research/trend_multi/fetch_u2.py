"""trend_multi · dati U2 (ADDENDUM.md, commit 4b8f2fc): ETF-serie e future delle materie prime; azioni dell'elenco di oggi
(OKX categoria 3 ∩ Bitget isRwa, solo instrumentType EQUITY su Yahoo). Salva data/u2/<nome>.csv.gz e data/u2/oggi_meta.csv."""
import json, sys, time
from pathlib import Path
import pandas as pd
import requests

D = Path(__file__).resolve().parent / "data" / "u2"
CUT = "2026-11-20"
UA = {"User-Agent": "research-client/1.0"}
COMM = {"UNG": "UNG", "CPER": "CPER", "PPLT": "PPLT", "GC_F": "GC=F", "SI_F": "SI=F", "BZ_F": "BZ=F", "NG_F": "NG=F",
        "HG_F": "HG=F", "PL_F": "PL=F"}


def yahoo(sym, k=0):
    host = "query1" if k % 2 == 0 else "query2"
    r = requests.get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}",
                     params=dict(period1=-2208988800, period2=1795300000, interval="1d", events="div,splits"), headers=UA, timeout=60)
    if r.status_code == 404:
        return None, {}
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").tz_localize("UTC").tz_convert(res["meta"]["exchangeTimezoneName"])
    df = pd.DataFrame({"close_raw": q["close"]}, index=idx.tz_localize(None).normalize())
    adj = res["indicators"].get("adjclose")
    df["adj"] = adj[0]["adjclose"] if adj else df["close_raw"]
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close_raw"])
    df = df[df.index <= CUT]; df.index.name = "date"
    return df[["adj", "close_raw"]].round(6), res["meta"]


def get(name, sym, need_equity=False):
    for k in range(6):
        try:
            df, meta = yahoo(sym, k)
            if df is None or len(df) == 0:
                return dict(name=name, sym=sym, stato="assente")
            info = dict(name=name, sym=sym, tipo=meta.get("instrumentType"), borsa=meta.get("exchangeName"),
                        nome=meta.get("longName") or meta.get("shortName"), da=str(df.index[0].date()), a=str(df.index[-1].date()), righe=len(df))
            if need_equity and meta.get("instrumentType") != "EQUITY":
                return dict(info, stato="non azione")
            df.to_csv(D / f"{name}.csv.gz")
            return dict(info, stato="ok")
        except Exception as e:  # noqa: BLE001
            time.sleep(8 + 8 * k)
    return dict(name=name, sym=sym, stato="errore")


if __name__ == "__main__":
    if "comm" in sys.argv:
        for n, s in COMM.items():
            if not (D / f"{n}.csv.gz").exists():
                print(get(n, s), flush=True); time.sleep(2)
    if "oggi" in sys.argv:
        o = json.load(open(D / "okx_swap.json"))["data"]; b = json.load(open(D / "bitget_usdt.json"))["data"]
        ok = {x["instId"].split("-")[0] for x in o if x.get("instCategory") == "3"}
        bg = {x["baseCoin"][:-5] if x["baseCoin"].endswith("STOCK") else x["baseCoin"] for x in b if x.get("isRwa") == "YES"}
        both = sorted(ok & bg)
        mp = D / "oggi_meta.csv"
        done = pd.read_csv(mp).to_dict("records") if mp.exists() else []
        seen = {r["name"] for r in done if r["stato"] != "errore"}
        done = [r for r in done if r["stato"] != "errore"]
        for t in both:
            if t in seen:
                continue
            done.append(get("S_" + t, "BRK-B" if t == "BRKB" else t, need_equity=True) | {"name": t})
            pd.DataFrame(done).to_csv(mp, index=False); time.sleep(1.5)
        print(pd.DataFrame(done)["stato"].value_counts())
