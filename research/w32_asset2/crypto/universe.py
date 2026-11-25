"""w32_asset2/crypto: universo = prime 200 CoinGecko di oggi (/coins/markets, data/raw/cg_top.json) e prime 200 al 01/01/2020
(istantanea CoinMarketCap /historical/20191229/ letta da Common Crawl, controllo con quella del 05/01/2020; cmc2020.py).
Esclusi: stablecoin, wrapped/bridged, liquid staking/restaking, oro e materie prime tokenizzate, RWA/fondi/azioni tokenizzate.
Per ogni moneta: catena di ticker Binance (rinomine e ridenominazioni) e disponibilità nell'archivio data.binance.vision
(listing S3, anche simboli delistati); niente prezzi qui. Scrive data/universe_raw.csv."""
import gzip, json, re
from pathlib import Path
import pandas as pd
import bv_list
HERE = Path(__file__).resolve().parent; RAW = HERE / "data" / "raw"

# categorie CoinGecko escluse (file data/raw/cg_<categoria>.json, /coins/markets?category=...)
EXCL_CAT = {"stablecoins": "stablecoin", "yield-bearing-stablecoins": "stablecoin", "wrapped-tokens": "wrapped",
            "bridged-tokens": "bridged", "liquid-staking-tokens": "staked", "liquid-restaking-tokens": "staked",
            "tokenized-btc": "wrapped", "tokenized-gold": "oro/materie prime", "tokenized-silver": "oro/materie prime",
            "tokenized-commodities": "oro/materie prime", "tokenized-treasuries": "rwa/fondo", "tokenized-money-market-fund-mmfs": "rwa/fondo",
            "tokenized-private-credit": "rwa/fondo", "tokenized-credit": "rwa/fondo", "tokenized-stock": "rwa/azione tokenizzata",
            "tokenized-exchange-traded-funds-etfs": "rwa/fondo", "tokenized-products": "rwa/fondo"}
NOT_EXCL = {"spx6900"}            # SPX6900: token nativo Ethereum, CoinGecko lo mette anche fra i bridged per le copie su altre reti
EXCL_MANUAL = {"midas-fasanara-global-open": "rwa/fondo"}   # fondo tokenizzato a valore ~1 (ATH/ATL 1,011/1,000), non categorizzato
TICK = {"GRAM": "TON", "BTT": "BTTC"}                      # simbolo CoinGecko -> ticker Binance di oggi
TICK_ID = {"beam-2": "BEAMX"}                              # Beam (gaming, ex Merit Circle) = BEAMX su Binance; BEAM del 2020 è un'altra moneta

# 2020 (simboli CMC del 29/12/2019) -> ticker canonico di oggi; esclusioni 2020
MAP20 = {"MIOTA": "IOTA", "BSV": "BSV", "NANO": "XNO", "XZC": "FIRO", "GNT": "GLM", "STRAT": "STRAX", "TOMO": "VIC",
         "NPXS": "PUNDIX", "FTM": "S", "MATIC": "POL", "BTT": "BTTC", "LUNA": "LUNC", "EOS": "A", "LOKI": "OXEN"}
EXCL20 = {"USDT": "stablecoin", "USDC": "stablecoin", "PAX": "stablecoin", "TUSD": "stablecoin", "SAI": "stablecoin",
          "EURS": "stablecoin", "USDK": "stablecoin", "KBC": "oro/materie prime", "CIX100": "rwa/fondo"}

# catena di serie Binance per ticker canonico: (base Binance, divisore del prezzo per esprimerlo nell'unità di oggi, fino al)
# l'elemento successivo prevale dal suo primo giorno; "fino al" taglia ticker poi riusati per un'altra moneta.
CHAIN = {"POL": [("MATIC", 1, None), ("POL", 1, None)], "RENDER": [("RNDR", 1, None), ("RENDER", 1, None)],
         "S": [("FTM", 1, None), ("S", 1, None)], "XNO": [("NANO", 1, None), ("XNO", 1, None)],
         "FIRO": [("XZC", 1, None), ("FIRO", 1, None)], "GLM": [("GNT", 1, None), ("GLM", 1, None)],
         "STRAX": [("STRAT", 1, None), ("STRAX", 1, None)], "VIC": [("TOMO", 1, None), ("VIC", 1, None)],
         "PUNDIX": [("NPXS", 1 / 1000, None), ("PUNDIX", 1, None)],          # 1 PUNDIX = 1000 NPXS
         "BTTC": [("BTT", 1000, "2022-02-11"), ("BTTC", 1, None)],             # 1 BTT vecchio = 1000 BTTC
         "LUNC": [("LUNA", 1, "2022-05-13"), ("LUNC", 1, None)],              # LUNAUSDT dal 31/05/2022 = Terra 2.0 (altra moneta)
         "A": [("EOS", 1, None), ("A", 1, None)],                             # EOS -> Vaulta (A), 1:1
         "LIT": [("LIT", 1, None)],
         "BCH": [("BCHABC", 1, None), ("BCH", 1, None)],                    # BCHABCUSDT (11/2018-11/2019) = BCH prima della rinomina
         "RAY": [("RAY", 1, None), ("RAYSOL", 1, None)]}                      # perp Raydium riquotato come RAYSOLUSDT
REUSED = {"LA": "LAUSDT su Binance = Lagrange (dal 2025), non LATOKEN del 2020",
          "NET": "NETUSDT su Binance dal 2026-08 = altra moneta, non NEXT del 2020",
          "BZ": "BZUSDT su Binance dal 2026-04 = altra moneta, non Bit-Z Token del 2020"}   # ticker riusato: nessun dato Binance
CUT_FROM = {"LIT": "2025-12-23",   # LITUSDT fino al 2025 = Litentry; Lighter dal 23/12/2025 (w32_top100)
            "SUN": "2021-06-18",   # ridenominazione SUN del 18/06/2021 (27,57 -> 0,033): si usa solo il token nuovo
            "PUMP": "2025-07-10"}  # PUMPUSDT perp prima del 10/07/2025 = altro contratto (0,047 -> 0,005 in un giorno)

def cg_categories():
    cat = {}
    for c, lab in EXCL_CAT.items():
        p = RAW / f"cg_{c}.json"
        d = json.load(open(p)) if p.exists() else []
        if not isinstance(d, list): raise SystemExit(f"categoria {c} non scaricata: {d}")
        for x in d: cat.setdefault(x["id"], []).append(lab)
    return cat

def cmc(day):
    b = gzip.decompress((RAW / f"cmc_{day}.html.gz").read_bytes()).decode("utf-8", "replace")
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', b, re.S)
    return json.loads(m.group(1))["props"]["initialState"]["cryptocurrency"]["listingHistorical"]["data"]

def cg2020():
    """controllo: home page CoinGecko del 24/01/2020 (Common Crawl CC-MAIN-2020-05), prime 100 per capitalizzazione."""
    p = next(RAW.glob("cg_home_2020*.html.gz"), None)
    if p is None: return []
    b = gzip.decompress(p.read_bytes()).decode("utf-8", "replace")
    return [x.upper() for x in re.findall(r'data-coin-symbol="([a-z0-9]+)" data-source="star_button" data-type="unfavorite"', b)]

def binance(t, spot, um):
    """per il ticker canonico: elementi della catena con spot/perp presenti nell'archivio."""
    ch = CHAIN.get(t, [(t, 1, None)]); out = []
    if t in REUSED: return [dict(base=t, fac=1, until=None, spot=None, perp=None, nota=REUSED[t])]
    for base, fac, until in ch:
        sp = f"{base}USDT" if f"{base}USDT" in spot else None
        pp = next((p for p in (f"{base}USDT", f"1000{base}USDT", f"1M{base}USDT", f"1000000{base}USDT") if p in um), None)
        if base == "LUNA": pp = "LUNAUSDT" if "LUNAUSDT" in um else None
        out.append(dict(base=base, fac=fac, until=until, spot=sp, perp=pp))
    return out

if __name__ == "__main__":
    spot, um = set(bv_list.symbols("spot")), set(bv_list.symbols("um"))
    cat = cg_categories(); rows = {}
    for x in json.load(open(RAW / "cg_top.json"))[:200]:
        sym = x["symbol"].upper(); t = TICK_ID.get(x["id"], TICK.get(sym, sym))
        ex = EXCL_MANUAL.get(x["id"]) or ("" if x["id"] in NOT_EXCL else ",".join(sorted(set(cat.get(x["id"], [])))))
        rows[t] = dict(ticker=t, symbol=sym, id_cg=x["id"], name=x["name"], rank_oggi=x["market_cap_rank"],
                       mcap_oggi_bn=round(x["market_cap"] / 1e9, 2), rank_2020=None, symbol_2020=None, slug_2020=None,
                       rank_20200105=None, mcap_2020_mn=None, escluso=ex)
    r05 = {x["slug"]: x["cmc_rank"] for x in cmc("20200105")}
    for x in cmc("20191229"):
        s = x["symbol"]; t = MAP20.get(s, s)
        if t in rows and rows[t]["rank_2020"] is None: r = rows[t]
        else: r = rows.setdefault(t, dict(ticker=t, symbol=s, id_cg=None, name=x["name"], rank_oggi=None, mcap_oggi_bn=None, escluso=EXCL20.get(s, "")))
        r.update(rank_2020=x["cmc_rank"], symbol_2020=s, slug_2020=x["slug"], rank_20200105=r05.get(x["slug"]),
                 mcap_2020_mn=round(x["quote"]["USD"]["market_cap"] / 1e6, 1))
        if not r["escluso"] and s in EXCL20: r["escluso"] = EXCL20[s]
    cg20 = cg2020(); miss = []
    for i, s in enumerate(cg20, 1):
        t = MAP20.get(s, s)
        if t in rows and rows[t].get("rank_2020") is not None: rows[t]["rank_cg_20200124"] = i
        else: miss.append(f"{i}:{s}")
    print("CoinGecko 24/01/2020: prime", len(cg20), "| fuori dalla top 200 CMC 29/12/2019:", " ".join(miss))
    out = []
    for t, r in rows.items():
        if not r["escluso"]:
            ch = binance(t, spot, um)
            r["chain"] = json.dumps(ch); r["bn_spot"] = any(c["spot"] for c in ch); r["bn_perp"] = next((c["perp"] for c in ch[::-1] if c["perp"]), None)
        out.append(r)
    df = pd.DataFrame(out); df.to_csv(HERE / "data" / "universe_raw.csv", index=False)
    inc = df[df.escluso.fillna("") == ""]
    print("righe", len(df), "oggi", df.rank_oggi.notna().sum(), "2020", df.rank_2020.notna().sum(), "in entrambe", (df.rank_oggi.notna() & df.rank_2020.notna()).sum())
    print("escluse oggi", (df.rank_oggi.notna() & (df.escluso.fillna("") != "")).sum(), "escluse 2020", (df.rank_2020.notna() & (df.escluso.fillna("") != "")).sum())
    print("incluse", len(inc), "con spot Binance", inc.bn_spot.sum(), "con perp Binance", inc.bn_perp.notna().sum())
