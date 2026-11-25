"""w32_asset2/crypto: operabilità per l'utente dalle liste pubbliche degli strumenti (scaricate il 25/11/2026 in data/raw/ops/):
Bitget /api/v2/mix/market/contracts?productType=USDT-FUTURES (perp USDT-M; openTime = apertura dichiarata) e
/api/v2/spot/public/symbols; OKX /api/v5/public/instruments?instType=SWAP e SPOT (listTime). Scrive data/ops.csv.
Nota: openTime/listTime sono le date dichiarate dalla borsa (possono essere una riapertura, non la prima quotazione)."""
import json
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent; OPS = HERE / "data" / "raw" / "ops"

def ms(x):
    try: return str(pd.to_datetime(int(x), unit="ms").date()) if x and int(x) > 0 else ""
    except ValueError: return ""

def load():
    bg = json.load(open(OPS / "bitget_usdt_futures.json"))["data"]; bgs = json.load(open(OPS / "bitget_spot.json"))["data"]
    ok = json.load(open(OPS / "okx_swap.json"))["data"]; oks = json.load(open(OPS / "okx_spot.json"))["data"]
    bgp = {}
    for x in bg:
        if x["quoteCoin"] == "USDT" and x.get("symbolType") == "perpetual": bgp.setdefault(x["baseCoin"].upper(), x)
    bgsp = {x["baseCoin"].upper(): x for x in bgs if x["quoteCoin"] == "USDT"}
    okp = {x["instFamily"].split("-")[0].upper(): x for x in ok if x.get("settleCcy") == "USDT" and x["instId"].endswith("-USDT-SWAP")}
    oksp = {x["baseCcy"].upper(): x for x in oks if x["quoteCcy"] == "USDT"}
    return bgp, bgsp, okp, oksp

def find(d, t):
    for k in (t, f"1000{t}", f"1M{t}", f"1000000{t}", f"10000{t}"):
        if k in d: return k, d[k]
    return None, None

_L = None
def ops(t):
    global _L
    _L = _L or load(); bgp, bgsp, okp, oksp = _L
    kb, b = find(bgp, t); ko, o = find(okp, t); _, bs = find(bgsp, t); _, os_ = find(oksp, t)
    return dict(bitget_perp=bool(b) and b.get("symbolStatus") == "normal", bitget_perp_simbolo=b["symbol"] if b else "",
                bitget_perp_stato=b.get("symbolStatus", "") if b else "", bitget_perp_da=ms(b.get("openTime")) if b else "",
                bitget_spot=bool(bs) and bs.get("status") == "online", bitget_spot_da=ms(bs.get("openTime")) if bs else "",
                okx_perp=bool(o) and o.get("state") == "live", okx_perp_simbolo=o["instId"] if o else "", okx_perp_da=ms(o.get("listTime")) if o else "",
                okx_spot=bool(os_) and os_.get("state") == "live", okx_spot_da=ms(os_.get("listTime")) if os_ else "")

if __name__ == "__main__":
    u = pd.read_csv(HERE / "data" / "universe_raw.csv"); u = u[u.escluso.isna()]
    df = pd.DataFrame([dict(ticker=t, **ops(t)) for t in u.ticker]); df.to_csv(HERE / "data" / "ops.csv", index=False)
    print("perp Bitget", int(df.bitget_perp.sum()), "| perp OKX", int(df.okx_perp.sum()), "| almeno uno", int((df.bitget_perp | df.okx_perp).sum()), "di", len(df))
    print(df[df.ticker.isin(["SOL", "TAO", "BTC", "ETH"])].to_string())
