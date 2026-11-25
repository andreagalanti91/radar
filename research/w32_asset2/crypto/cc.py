"""Common Crawl (archivio pubblico, data.commoncrawl.org, senza login): cerca una URL nell'indice CDX di una raccolta tramite
ricerca binaria su cluster.idx con richieste a intervalli (Range) e scarica il record WARC della pagina archiviata.
Serve a ricostruire la classifica crypto al 01/01/2020 (CoinGecko pubblico limita lo storico a 365 giorni)."""
import gzip, io, json, sys, time
import requests
BASE = "https://data.commoncrawl.org"
S = requests.Session(); S.headers["User-Agent"] = "radar-research-script/1.0 (python-requests; academic backtest)"

def rng(url, a, b):
    for k in range(5):
        try:
            r = S.get(url, headers={"Range": f"bytes={a}-{b}"}, timeout=90)
            if r.status_code in (200, 206): return r.content
        except requests.RequestException: pass
        time.sleep(3 + 5 * k)
    raise RuntimeError(f"range {url} {a}-{b}")

def size(url):
    for k in range(6):
        try:
            r = S.head(url, timeout=60)
            if r.status_code == 200: return int(r.headers["content-length"])
        except requests.RequestException: pass
        time.sleep(5 + 10 * k)                 # 503 "slow down" di Common Crawl: pausa e riprova
    raise RuntimeError(f"head {url}")

def _line_at(url, off, n):
    blk = rng(url, off, min(off + 4095, n - 1))
    if off: blk = blk.split(b"\n", 1)[1] if b"\n" in blk else b""
    return blk.split(b"\n", 1)[0].decode(errors="replace")

def cluster_lines(coll, key):
    """righe di cluster.idx che possono contenere `key` (SURT): l'ultima con chiave <= key e la successiva."""
    url = f"{BASE}/cc-index/collections/{coll}/indexes/cluster.idx"; n = size(url); lo, hi = 0, n
    while hi - lo > 8192:
        mid = (lo + hi) // 2; ln = _line_at(url, mid, n)
        if ln.split("\t")[0] <= key: lo = mid
        else: hi = mid
    blk = rng(url, lo, min(lo + 16383, n - 1)).decode(errors="replace").split("\n")
    if lo: blk = blk[1:]
    ok = [l for l in blk if l.count("\t") >= 3]
    best = [i for i, l in enumerate(ok) if l.split("\t")[0] <= key]
    i = best[-1] if best else 0
    return ok[i:i + 2]

def cdx(coll, key):
    out = []
    for l in cluster_lines(coll, key):
        _, f, off, ln = l.split("\t")[:4]
        raw = rng(f"{BASE}/cc-index/collections/{coll}/indexes/{f}", int(off), int(off) + int(ln) - 1)
        for row in gzip.decompress(raw).decode(errors="replace").split("\n"):
            if row.startswith(key): out.append(json.loads(row.split(" ", 2)[2]) | {"surt": row.split(" ")[0], "ts": row.split(" ")[1]})
    return out

def warc(rec):
    raw = rng(f"{BASE}/{rec['filename']}", int(rec["offset"]), int(rec["offset"]) + int(rec["length"]) - 1)
    body = gzip.decompress(raw)
    parts = body.split(b"\r\n\r\n", 2)        # intestazione WARC, intestazione HTTP, corpo
    return parts[2] if len(parts) == 3 else b""

if __name__ == "__main__":
    for r in cdx(sys.argv[1], sys.argv[2]): print(r["ts"], r["surt"], r.get("status"), r["url"])
