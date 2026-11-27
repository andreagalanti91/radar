"""emergenti · operabilità dell'utente dalle liste pubbliche degli strumenti (oggi):
Bitget /api/v2/mix/market/contracts?productType=USDT-FUTURES (perp USDT; launchTime/openTime) e /api/v2/spot/public/symbols;
OKX /api/v5/public/instruments?instType=SWAP e SPOT (listTime). Elenco dei simboli dell'archivio Binance (listing S3 pubblico di
data.binance.vision: spot, perp USDT-M, funding; anche i delistati). Salva in data/raw/ops/ (fuori da git)."""
import json, re, time
from pathlib import Path
import requests
HERE = Path(__file__).resolve().parent; OUT = HERE / "data" / "raw" / "ops"; OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session(); S.headers["User-Agent"] = "radar-research-script/1.0 (python-requests; academic backtest)"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
PFX = {"spot": "data/spot/monthly/klines/", "um": "data/futures/um/monthly/klines/", "umfund": "data/futures/um/monthly/fundingRate/",
       "um_daily": "data/futures/um/daily/klines/", "spot_daily": "data/spot/daily/klines/"}
LISTS = {"bitget_usdt_futures": ("https://api.bitget.com/api/v2/mix/market/contracts", {"productType": "USDT-FUTURES"}),
         "bitget_spot": ("https://api.bitget.com/api/v2/spot/public/symbols", {}),
         "okx_swap": ("https://www.okx.com/api/v5/public/instruments", {"instType": "SWAP"}),
         "okx_spot": ("https://www.okx.com/api/v5/public/instruments", {"instType": "SPOT"})}

def ls(prefix):
    out, marker = [], ""
    while True:
        r = S.get(S3, params={"prefix": prefix, "delimiter": "/", "marker": marker}, timeout=60); t = r.text
        keys = re.findall(r"<Prefix>([^<]+)</Prefix>", t)[1:]
        out += keys
        if "<IsTruncated>true</IsTruncated>" not in t or not keys: return out
        nm = re.findall(r"<NextMarker>([^<]+)</NextMarker>", t); marker = nm[0] if nm else keys[-1]; time.sleep(0.2)

if __name__ == "__main__":
    for k, (u, p) in LISTS.items():
        d = S.get(u, params=p, timeout=60).json(); (OUT / f"{k}.json").write_text(json.dumps(d)); print(k, len(d.get("data", [])), flush=True)
        time.sleep(0.5)
    for k, p in PFX.items():
        s = sorted({x[len(p):].strip("/") for x in ls(p)}); (OUT / f"bv_{k}.txt").write_text("\n".join(s)); print(k, len(s), flush=True)
    (OUT / "meta.json").write_text(json.dumps({"scaricato_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime())}))
