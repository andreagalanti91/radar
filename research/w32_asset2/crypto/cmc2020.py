"""Classifica al 01/01/2020: istantanee settimanali di CoinMarketCap (pagine /historical/20191229/ e /historical/20200105/),
lette dall'archivio pubblico Common Crawl (non dal sito CMC). CoinGecko pubblico non dà storico oltre 365 giorni.
Salva l'HTML grezzo in data/raw/cmc_<data>.html.gz e la tabella in data/raw/cmc_<data>.csv (rank, nome, simbolo, mcap)."""
import gzip, json, re, sys
from pathlib import Path
import cc
RAW = Path(__file__).resolve().parent / "data" / "raw"
CRAWLS = ["CC-MAIN-2021-04", "CC-MAIN-2021-17", "CC-MAIN-2021-49", "CC-MAIN-2022-49"]

def grab(day):
    p = RAW / f"cmc_{day}.html.gz"
    if p.exists(): return gzip.decompress(p.read_bytes())
    for c in CRAWLS:
        for rec in cc.cdx(c, f"com,coinmarketcap)/historical/{day}"):
            if rec.get("status") != "200": continue
            body = cc.warc(rec)
            if b"__NEXT_DATA__" in body or b"cmc-table" in body:
                p.write_bytes(gzip.compress(body)); (RAW / f"cmc_{day}.source.json").write_text(json.dumps(rec | {"crawl": c}, indent=1))
                return body
    return None

if __name__ == "__main__":
    for d in sys.argv[1:] or ["20191229", "20200105"]:
        b = grab(d); print(d, None if b is None else len(b))
