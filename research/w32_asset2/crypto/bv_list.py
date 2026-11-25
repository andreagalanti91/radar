"""Elenco dei simboli presenti nell'archivio pubblico data.binance.vision (listing S3, anche simboli delistati) e dei mesi
disponibili per un simbolo. Salva data/raw/bv_<mercato>.txt."""
import re, sys, time
from pathlib import Path
import requests
RAW = Path(__file__).resolve().parent / "data" / "raw"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
S = requests.Session(); S.headers["User-Agent"] = "radar-research-script/1.0 (python-requests; academic backtest)"
PFX = {"spot": "data/spot/monthly/klines/", "um": "data/futures/um/monthly/klines/", "umfund": "data/futures/um/monthly/fundingRate/"}

def ls(prefix, delim="/"):
    out, marker = [], ""
    while True:
        for k in range(5):
            try:
                r = S.get(S3, params={"prefix": prefix, "delimiter": delim, "marker": marker}, timeout=60)
                if r.status_code == 200: break
            except requests.RequestException: pass
            time.sleep(3 + 5 * k)
        t = r.text
        keys = re.findall(r"<Prefix>([^<]+)</Prefix>", t)[1:] if delim else []
        keys += re.findall(r"<Key>([^<]+)</Key>", t)
        out += keys
        if "<IsTruncated>true</IsTruncated>" not in t or not keys: return out
        marker = re.findall(r"<NextMarker>([^<]+)</NextMarker>", t)
        marker = marker[0] if marker else keys[-1]
        time.sleep(0.2)

def symbols(mkt):
    p = RAW / f"bv_{mkt}.txt"
    if p.exists(): return p.read_text().split()
    s = sorted({k[len(PFX[mkt]):].strip("/") for k in ls(PFX[mkt])}); p.write_text("\n".join(s)); return s

def months(mkt, sym):
    pre = PFX[mkt] + sym + ("/1d/" if mkt != "umfund" else "/")
    return sorted(re.findall(r"(\d{4}-\d{2})\.zip$", k)[0] for k in ls(pre, "") if k.endswith(".zip"))

if __name__ == "__main__":
    for m in sys.argv[1:] or ["spot", "um", "umfund"]: print(m, len(symbols(m)))
