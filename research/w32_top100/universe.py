"""w32_top100: universo = top 100 CoinGecko (/coins/markets, 22/11/2026) meno stablecoin, oro tokenizzato, fondi/RWA a valore
stabile e token wrapped/staked; per ognuno verifica (solo disponibilità, nessun prezzo) spot <SYM>USDT e perp USDT-M su Binance."""
import json, time
from pathlib import Path
import pandas as pd, requests
HERE = Path(__file__).resolve().parent; RAW = HERE / "data" / "raw"
S = requests.Session()
EXCL_CAT = ["stablecoins", "wrapped-tokens", "liquid-staking-tokens", "liquid-restaking-tokens", "tokenized-gold", "bridged-tokens"]
# fondi tokenizzati / RWA a valore quasi costante (non categorizzati come stablecoin da CoinGecko): esclusi come le stablecoin
EXCL_RWA = {"figure-heloc", "ondo-us-dollar-yield", "spiko-amundi-overnight-swap-fund-eur", "hashnote-usyc",
            "blackrock-usd-institutional-digital-liquidity-fund", "superstate-short-duration-us-government-securities-fund-ustb",
            "janus-henderson-anemoy-aaa-clo-fund"}
TICK = {"GRAM": "TON"}                                   # ticker Binance diverso da CoinGecko
RENAME = {"POL": "MATIC", "RENDER": "RNDR"}              # cambi di ticker 1:1 su Binance: storia precedente dal vecchio ticker
ARC = "https://data.binance.vision/data/futures/um/monthly/klines"

def spot_ok(p):
    r = S.get("https://data-api.binance.vision/api/v3/klines", params=dict(symbol=p, interval="1d", limit=1, startTime=1500000000000), timeout=30)
    return r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0

def perp_sym(t):
    for p in (f"{t}USDT", f"1000{t}USDT", f"1M{t}USDT"):
        for m in ("2026-10", "2026-09"):
            if S.head(f"{ARC}/{p}/1d/{p}-1d-{m}.zip", timeout=30).status_code == 200: return p
    return None

if __name__ == "__main__":
    top = json.load(open(RAW / "cg_top.json"))[:100]
    cat = {}
    for c in EXCL_CAT:
        for x in json.load(open(RAW / f"cg_{c}.json")): cat.setdefault(x["id"], []).append(c)
    rows = []
    for x in top:
        sym = x["symbol"].upper(); t = TICK.get(sym, sym)
        ex = ",".join(cat.get(x["id"], [])) or ("rwa/fondo" if x["id"] in EXCL_RWA else "")
        row = dict(rank=x["market_cap_rank"], id=x["id"], symbol=sym, ticker=t, mcap_bn=round(x["market_cap"] / 1e9, 2), escluso=ex)
        if not ex:
            row["spot"] = spot_ok(f"{t}USDT") or (t in RENAME and spot_ok(f"{RENAME[t]}USDT")); row["perp"] = perp_sym(t); time.sleep(0.3)
        rows.append(row); print(row, flush=True)
    pd.DataFrame(rows).to_csv(HERE / "universe.csv", index=False)
