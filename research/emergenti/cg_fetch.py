"""emergenti · classifica di oggi: CoinGecko API pubblica senza chiave (https://api.coingecko.com/api/v3/coins/markets,
vs_currency=usd, order=market_cap_desc, per_page=250, pagine 1-2 = prime 500) e liste delle categorie da escludere (stesse
categorie di w32_asset2/crypto/universe.py, pagine 1-3 per coprire le monete fino al rank ~500). Pausa 8 s fra le richieste
(limite pubblico ~10-30/min). Salva in data/raw/cg/ (fuori da git). Uso: python3 cg_fetch.py"""
import json, time
from pathlib import Path
import requests
HERE = Path(__file__).resolve().parent; OUT = HERE / "data" / "raw" / "cg"; OUT.mkdir(parents=True, exist_ok=True)
URL = "https://api.coingecko.com/api/v3/coins/markets"
S = requests.Session(); S.headers["User-Agent"] = "radar-research-script/1.0 (python-requests; academic backtest)"
CATS = ["stablecoins", "yield-bearing-stablecoins", "wrapped-tokens", "bridged-tokens", "liquid-staking-tokens",
        "liquid-restaking-tokens", "tokenized-btc", "tokenized-gold", "tokenized-silver", "tokenized-commodities",
        "tokenized-treasuries", "tokenized-money-market-fund-mmfs", "tokenized-private-credit", "tokenized-credit",
        "tokenized-stock", "tokenized-exchange-traded-funds-etfs", "tokenized-products", "real-world-assets-rwa"]

def get(params):
    for a in range(6):
        r = S.get(URL, params=params, timeout=60)
        if r.status_code == 200: return r.json()
        time.sleep(30 + 30 * a)                     # 429: pausa lunga
    raise SystemExit(f"CoinGecko non risponde: {params} {r.status_code}")

def save(name, params, pages):
    p = OUT / f"{name}.json"
    if p.exists(): return json.load(open(p))
    out = []
    for pg in range(1, pages + 1):
        x = get(dict(params, page=pg)); time.sleep(8); out += x
        if len(x) < 250: break
    p.write_text(json.dumps(out)); print(name, len(out), flush=True); return out

if __name__ == "__main__":
    base = dict(vs_currency="usd", order="market_cap_desc", per_page=250, sparkline="false")
    top = save("top500", base, 2)
    (OUT / "top500.meta.json").write_text(json.dumps({"scaricato_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()), "url": URL, "params": base}))
    for c in CATS: save(f"cat_{c}", dict(base, category=c), 3)
