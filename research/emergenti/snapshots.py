"""emergenti · classifiche storiche (contro il bias di sopravvivenza): istantanee di CoinMarketCap /historical/<data>/ lette
dall'archivio pubblico Common Crawl (data.commoncrawl.org, indice CDX con richieste Range; NON dal sito CMC), con il modulo
research/w32_asset2/crypto/cc.py. CoinGecko pubblico non dà classifiche oltre 365 giorni. Per ogni inizio d'anno si usa la prima
istantanea disponibile più vicina al 1° gennaio (elenco SNAP, trovato con le ricerche nell'indice del 27/11/2026).
Salva data/raw/cmc/cmc_<data>.html.gz, .source.json e data/snapshots.csv (data, rank, simbolo, slug, nome, mcap)."""
import gzip, json, re, sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent; RAW = HERE / "data" / "raw" / "cmc"; RAW.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE.parents[0] / "w32_asset2" / "crypto"))
import cc  # noqa: E402
W32 = HERE.parents[0] / "w32_asset2" / "crypto" / "data" / "raw"
# anno di riferimento -> (istantanea, raccolta Common Crawl)
SNAP = {2020: ("20191229", None),                  # già in w32_asset2 (CC-MAIN-2021-04)
        2021: ("20201227", "CC-MAIN-2021-04"),
        2022: ("20220102", "CC-MAIN-2022-49"), 2023: ("20230101", "CC-MAIN-2023-50"),
        2024: ("20231231", "CC-MAIN-2024-42"), 2025: ("20241228", "CC-MAIN-2026-43"), 2026: ("20251116", "CC-MAIN-2026-08")}
EXTRA = json.loads((HERE / "snapshots_extra.json").read_text()) if (HERE / "snapshots_extra.json").exists() else {}
for k, v in EXTRA.items(): SNAP[int(k)] = tuple(v)

def grab(day, coll):
    p = RAW / f"cmc_{day}.html.gz"
    if p.exists(): return gzip.decompress(p.read_bytes())
    w = W32 / f"cmc_{day}.html.gz"
    if w.exists(): return gzip.decompress(w.read_bytes())
    for rec in cc.cdx(coll, f"com,coinmarketcap)/historical/{day}"):
        if rec.get("status") != "200": continue
        body = cc.warc(rec)
        if b"__NEXT_DATA__" in body:
            p.write_bytes(gzip.compress(body)); (RAW / f"cmc_{day}.source.json").write_text(json.dumps(rec | {"crawl": coll}, indent=1))
            return body
    return None

def parse(b):
    s = b.decode("utf-8", "replace")
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', s, re.S)
    j = json.loads(m.group(1))
    st = j["props"].get("initialState") or j["props"].get("pageProps", {}).get("initialState")
    if isinstance(st, str): st = json.loads(st)
    return st["cryptocurrency"]["listingHistorical"]["data"]

if __name__ == "__main__":
    rows = []
    for y, (day, coll) in sorted(SNAP.items()):
        b = grab(day, coll)
        if b is None: print(y, day, "non trovata"); continue
        d = parse(b)
        for x in d:
            q = x.get("quote", {}).get("USD", {}) or {}
            rows.append(dict(anno=y, data=day, rank=x.get("cmc_rank") or x.get("cmcRank"), simbolo=x["symbol"], slug=x["slug"], nome=x["name"],
                             mcap_mn=round((q.get("market_cap") or q.get("marketCap") or 0) / 1e6, 1), prezzo=q.get("price"), data_aggiunta=(x.get("date_added") or x.get("dateAdded") or "")[:10], tags=",".join(x.get("tags") or [])[:300]))
        print(y, day, len(d), "righe, rank max", max((x.get("cmc_rank") or x.get("cmcRank") or 0) for x in d), flush=True)
    pd.DataFrame(rows).to_csv(HERE / "data" / "snapshots.csv", index=False)
