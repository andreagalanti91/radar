"""w32_asset2/crypto: fonti di riserva (API pubbliche, senza chiave).
- OKX /market/history-candles 1Dutc (spot X-USDT e perp X-USDT-SWAP): solo prezzo e volume, NESSUN taker buy (il flusso perp
  non si ricostruisce: versione "solo prezzo"); per le monete senza alcun dato Binance.
- OKX /public/funding-rate-history: funding dei mesi non ancora nell'archivio mensile Binance (l'API dà ~3 mesi).
- Bitget /spot/market/history-candles 1Dutc: TAO spot prima della quotazione Binance (Bitget TAOUSDT dal 30/03/2023).
Grezzi in data/raw/okx/ e data/raw/bitget/. Uso: python3 okx.py candles|funding|tao"""
import json, sys, time
from pathlib import Path
import pandas as pd, requests
HERE = Path(__file__).resolve().parent; RAW = HERE / "data" / "raw"
OK = RAW / "okx"; BG = RAW / "bitget"; OK.mkdir(parents=True, exist_ok=True); BG.mkdir(parents=True, exist_ok=True)
S = requests.Session(); S.headers["User-Agent"] = "radar-research-script/1.0 (python-requests; academic backtest)"

def getj(url, params):
    for a in range(5):
        try:
            r = S.get(url, params=params, timeout=30)
            if r.status_code == 200: return r.json()
            if r.status_code == 429: time.sleep(5)
        except (requests.RequestException, ValueError): pass
        time.sleep(1 + 3 * a)
    return None

def okx_candles(inst):
    p = OK / f"{inst}_candles.csv.gz"
    if p.exists(): return pd.read_csv(p, index_col=0, parse_dates=True)
    rows, after = [], ""
    while True:
        j = getj("https://www.okx.com/api/v5/market/history-candles", dict(instId=inst, bar="1Dutc", limit=100, after=after))
        d = (j or {}).get("data") or []
        if not d: break
        rows += d; after = d[-1][0]; time.sleep(0.25)
        if len(d) < 100: break
    if not rows: return None
    x = pd.DataFrame(rows).iloc[:, :9]; x.columns = ["t", "open", "high", "low", "close", "vol", "volCcy", "volQuote", "confirm"]
    x = x[x.confirm == "1"]                                    # solo candele chiuse
    x["date"] = pd.to_datetime(pd.to_numeric(x.t), unit="ms").dt.normalize()
    vol = x["vol"] if inst.count("-") == 1 else x["volCcy"]    # spot: vol in moneta; swap: volCcy in moneta
    x = x.assign(volume=pd.to_numeric(vol), tbv=float("nan")).set_index("date")[["open", "high", "low", "close", "volume", "tbv"]].astype(float).sort_index()
    x = x[~x.index.duplicated(keep="last")]; x.to_csv(p, compression="gzip"); return x

def okx_funding(inst):
    p = OK / f"{inst}_funding.csv.gz"
    if p.exists(): return pd.read_csv(p, index_col=0, parse_dates=True)
    rows, after = [], ""
    while True:
        j = getj("https://www.okx.com/api/v5/public/funding-rate-history", dict(instId=inst, limit=100, after=after))
        d = (j or {}).get("data") or []
        if not d: break
        rows += d; after = d[-1]["fundingTime"]; time.sleep(0.25)
        if len(d) < 100: break
    if not rows: return None
    x = pd.DataFrame(rows); x["date"] = pd.to_datetime(pd.to_numeric(x.fundingTime), unit="ms").dt.normalize()
    x["r"] = pd.to_numeric(x["realizedRate"].replace("", None)).fillna(pd.to_numeric(x["fundingRate"]))
    x = x.groupby("date")["r"].sum().rename("funding").to_frame(); x.to_csv(p, compression="gzip"); return x

def bitget_spot(sym, start_ms):
    p = BG / f"{sym}_spot.csv.gz"
    if p.exists(): return pd.read_csv(p, index_col=0, parse_dates=True)
    rows, end = [], int(time.time() * 1000)
    while end > start_ms:
        j = getj("https://api.bitget.com/api/v2/spot/market/history-candles", dict(symbol=sym, granularity="1Dutc", endTime=end, limit=200))
        d = (j or {}).get("data") or []
        if not d: break
        rows += d; end = min(int(r[0]) for r in d) - 1; time.sleep(0.3)
    x = pd.DataFrame(rows).iloc[:, :6]; x.columns = ["t", "open", "high", "low", "close", "volume"]
    x["date"] = pd.to_datetime(pd.to_numeric(x.t), unit="ms").dt.normalize()
    x = x.assign(tbv=float("nan")).set_index("date")[["open", "high", "low", "close", "volume", "tbv"]].astype(float).sort_index()
    x = x[~x.index.duplicated(keep="last")]; x.to_csv(p, compression="gzip"); return x

def lists():
    sw = {x["instId"] for x in json.load(open(RAW / "ops" / "okx_swap.json"))["data"]}
    sp = {x["instId"] for x in json.load(open(RAW / "ops" / "okx_spot.json"))["data"]}
    return sp, sw

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "candles"
    u = pd.read_csv(HERE / "data" / "universe_raw.csv"); u = u[u.escluso.isna()]
    sp, sw = lists()
    if what == "candles":       # monete senza alcun dato Binance
        import universe as U
        for r in u[(u.bn_spot != True) & u.bn_perp.isna() & ~u.ticker.isin(list(U.REUSED))].itertuples():
            for inst in (f"{r.ticker}-USDT", f"{r.ticker}-USDT-SWAP"):
                if inst in sp or inst in sw:
                    x = okx_candles(inst); print(r.ticker, inst, None if x is None else (len(x), str(x.index[0].date()), str(x.index[-1].date())), flush=True)
    elif what == "funding":     # tutti i perp OKX delle monete incluse (per il mese non ancora archiviato da Binance)
        for r in u.itertuples():
            inst = f"{r.ticker}-USDT-SWAP"
            if inst in sw:
                x = okx_funding(inst); print(r.ticker, None if x is None else (len(x), str(x.index[0].date()), str(x.index[-1].date())), flush=True)
    elif what == "tao":
        x = bitget_spot("TAOUSDT", 1680134400000); print("TAO bitget spot", len(x), x.index[0].date(), x.index[-1].date())
