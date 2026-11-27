"""emergenti · universo (nessun prezzo qui, nessun rendimento).

Fonti: CoinGecko top 500 di oggi (cg_fetch.py, API pubblica /coins/markets) e istantanee CoinMarketCap top 200 a inizio anno
(snapshots.py, lette da Common Crawl). Esclusioni come w32_asset2 (categorie CoinGecko: stablecoin, wrapped/bridged, liquid
staking, oro/materie prime, RWA-fondi, azioni tokenizzate; per le istantanee CMC: tag e nomi, più l'abbinamento all'id CoinGecko).
Abbinamento al ticker canonico di oggi: rinomine e catene di w32_asset2/crypto/universe.py (MAP20, CHAIN, REUSED) più quelle
aggiunte qui (ALIAS). Disponibilità: archivio Binance (listing S3 di ops_fetch.py), perp OKX e Bitget dalle liste pubbliche.
Scrive data/universe_raw.csv (una riga per ticker canonico, rank per ogni classifica)."""
import json, re, sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent; RAW = HERE / "data" / "raw"; OPS = RAW / "ops"; CG = RAW / "cg"
W32 = HERE.parent / "w32_asset2" / "crypto"
sys.path.insert(0, str(W32))
import universe as U32  # noqa: E402  (solo costanti: MAP20, CHAIN, REUSED, TICK, TICK_ID, EXCL_CAT, NOT_EXCL, EXCL_MANUAL)

# rinomine aggiuntive (simbolo della classifica storica -> ticker canonico di oggi), valide fino alla data indicata (None = sempre)
ALIAS = {"MATIC": ("POL", None), "FTM": ("S", None), "EOS": ("A", None), "RNDR": ("RENDER", None), "MIOTA": ("IOTA", None),
         "NANO": ("XNO", None), "XZC": ("FIRO", None), "GNT": ("GLM", None), "STRAT": ("STRAX", None), "TOMO": ("VIC", None),
         "NPXS": ("PUNDIX", None), "KLAY": ("KAIA", None), "MC": ("BEAMX", "2023-11-01"),
         "LUNA": ("LUNC", "2022-05-13"),          # prima del crollo LUNA = Terra classic; dal 31/05/2022 LUNA = Terra 2.0
         "BTT": ("BTTC", "2022-02-11"), "BCHABC": ("BCH", None), "LOKI": ("OXEN", None)}
CHAIN = dict(U32.CHAIN)
CHAIN.update({"KAIA": [("KLAY", 1, None), ("KAIA", 1, None)]})
EXCL_CAT = dict(U32.EXCL_CAT)
# tag/nomi CMC che indicano monete da escludere nelle istantanee storiche
CMC_TAG_EXCL = {"stablecoin": "stablecoin", "asset-backed-stablecoin": "stablecoin", "fiat-stablecoin": "stablecoin",
                "algorithmic-stablecoin": "stablecoin", "tokenized-gold": "oro/materie prime", "wrapped-tokens": "wrapped",
                "tokenized-stock": "rwa/azione tokenizzata", "tokenized-treasury-bills": "rwa/fondo", "liquid-staking-derivatives": "staked"}
NAME_EXCL = [(re.compile(r"\b(wrapped|bridged)\b", re.I), "wrapped"), (re.compile(r"\b(staked|restaked)\b", re.I), "staked"),
             (re.compile(r"\b(tether gold|pax gold|xaut|paxg)\b", re.I), "oro/materie prime"),
             (re.compile(r"\b(usd|eur)\b.*\b(coin|stable)|\bdai\b|^usd", re.I), "stablecoin")]
SYM_EXCL = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "PAX", "GUSD", "HUSD", "USDD", "FRAX", "LUSD", "USDN", "UST", "USTC",
            "FDUSD", "PYUSD", "USDE", "USDS", "EURS", "EURT", "SAI", "USDK", "USDJ", "XAUT", "PAXG", "WBTC", "WETH", "STETH",
            "WBETH", "CBETH", "RETH", "WEETH", "WSTETH", "BTCB", "HBTC", "RENBTC", "TBTC", "CUSDC", "CDAI", "CETH", "USDX", "SUSD",
            "ALUSD", "MIM", "OUSD", "VAI", "XSGD", "EURC", "USD0", "USDB", "USDY", "BUIDL", "KBC", "CIX100", "FEI", "TRIBE_USD"}

# token di governance/protocollo finiti in categorie o tag di esclusione (non replicano un sottostante): restano dentro
KEEP = {"LDO": "governance di Lido (non è stETH)", "JTO": "governance di Jito", "LISTA": "governance di Lista DAO",
        "ANKR": "token di protocollo", "FXS": "governance di Frax", "RPL": "token di Rocket Pool (non è rETH)",
        "TRIBE": "governance di Fei", "STAKE": "token di staking di xDai, non stabile", "BTG": "Bitcoin Gold (fork, non oro)",
        "SPX": "SPX6900 nativo (come w32_asset2)"}

def bn_lists():
    rd = lambda k: set((OPS / f"bv_{k}.txt").read_text().split())   # noqa: E731
    return rd("spot") | rd("spot_daily"), rd("um") | rd("um_daily"), rd("umfund")

def binance(t, spot, um):
    ch = CHAIN.get(t, [(t, 1, None)]); out = []
    if t in U32.REUSED: return [dict(base=t, fac=1, until=None, spot=None, perp=None, nota=U32.REUSED[t])]
    for base, fac, until in ch:
        sp = f"{base}USDT" if f"{base}USDT" in spot else None
        pp = next((p for p in (f"{base}USDT", f"1000{base}USDT", f"1M{base}USDT", f"1000000{base}USDT") if p in um), None)
        if base == "LUNA": pp = "LUNAUSDT" if "LUNAUSDT" in um else None
        out.append(dict(base=base, fac=fac, until=until, spot=sp, perp=pp))
    return out

def ops_lists():
    bg = json.load(open(OPS / "bitget_usdt_futures.json"))["data"]; ok = json.load(open(OPS / "okx_swap.json"))["data"]
    bgp = {}
    for x in bg:
        if x["quoteCoin"] == "USDT" and x.get("symbolType") == "perpetual": bgp.setdefault(x["baseCoin"].upper(), x)
    okp = {x["instFamily"].split("-")[0].upper(): x for x in ok if x.get("settleCcy") == "USDT" and x["instId"].endswith("-USDT-SWAP")}
    return bgp, okp

def find(d, t):
    for k in (t, f"1000{t}", f"1M{t}", f"1000000{t}", f"10000{t}"):
        if k in d: return k, d[k]
    return None, None

def ms(x):
    try: return str(pd.to_datetime(int(x), unit="ms").date()) if x and int(x) > 0 else ""
    except (ValueError, TypeError): return ""

def cg_excl():
    cat = {}
    for c, lab in EXCL_CAT.items():
        for p in (CG / f"cat_{c}.json", W32 / "data" / "raw" / f"cg_{c}.json"):
            if p.exists():
                d = json.load(open(p))
                if isinstance(d, list):
                    for x in d: cat.setdefault(x["id"], set()).add(lab)
    return cat

def canon(sym, day):
    a = ALIAS.get(sym)
    if a and (a[1] is None or day < a[1].replace("-", "")): return a[0]
    return sym

if __name__ == "__main__":
    spot, um, umf = bn_lists(); bgp, okp = ops_lists(); cat = cg_excl(); rows = {}
    top = json.load(open(CG / "top500.json"))
    for x in top[:500]:
        sym = x["symbol"].upper(); t = U32.TICK_ID.get(x["id"], U32.TICK.get(sym, sym))
        ex = U32.EXCL_MANUAL.get(x["id"]) or ("" if x["id"] in U32.NOT_EXCL else ",".join(sorted(cat.get(x["id"], set()))))
        if not ex and sym in SYM_EXCL: ex = "stablecoin/wrapped (simbolo)"
        if not ex: ex = next((lab for rx, lab in NAME_EXCL if rx.search(f"{x['name']}")), "")
        if t in rows: t = f"{t}#{x['id']}"           # simbolo doppio nella top 500: il secondo resta separato (senza dati Binance)
        rows[t] = dict(ticker=t, simbolo=sym, id_cg=x["id"], nome=x["name"], rank_oggi=x["market_cap_rank"],
                       mcap_oggi_mn=round((x["market_cap"] or 0) / 1e6, 1), prezzo_oggi=x["current_price"], escluso=ex)
    snap = pd.read_csv(HERE / "data" / "snapshots.csv")
    cg_by_slug = {x["id"]: x for x in top}
    for (y, day), g in snap.groupby(["anno", "data"]):
        for x in g.itertuples():
            day = str(day); t = canon(x.simbolo, day)
            tags = set(str(x.tags).split(",")) if isinstance(x.tags, str) else set()
            ex = next((lab for k, lab in CMC_TAG_EXCL.items() if k in tags), "")
            if not ex and str(x.simbolo).upper() in SYM_EXCL: ex = "stablecoin/wrapped (simbolo)"
            if not ex and x.slug in cat: ex = ",".join(sorted(cat[x.slug]))
            if not ex: ex = next((lab for rx, lab in NAME_EXCL if rx.search(str(x.nome))), "")
            r = rows.get(t)
            if r is not None and r.get("id_cg") and x.slug != r["id_cg"] and r.get("nome", "").lower() != str(x.nome).lower():
                r.setdefault("nota", ""); r["nota"] = (r["nota"] + f" | {y}: CMC {x.slug} ({x.nome}) con lo stesso ticker").strip(" |")
            if r is None:
                r = rows[t] = dict(ticker=t, simbolo=x.simbolo, id_cg=None, nome=x.nome, rank_oggi=None, mcap_oggi_mn=None,
                                   prezzo_oggi=None, escluso=ex)
            r[f"rank_{y}"] = int(x.rank); r[f"mcap_{y}_mn"] = x.mcap_mn; r[f"prezzo_cmc_{y}"] = None
            r[f"slug_{y}"] = x.slug; r.setdefault("data_aggiunta_cmc", x.data_aggiunta if isinstance(x.data_aggiunta, str) else "")
            if ex and not r["escluso"]: r["escluso"] = ex
    for t, r in rows.items():
        if t in KEEP and r["escluso"]: r["nota_esclusione"] = f"non escluso ({r['escluso']}): {KEEP[t]}"; r["escluso"] = ""
    out = []
    for t, r in rows.items():
        base = t.split("#")[0]
        ch = binance(base, spot, um) if "#" not in t else [dict(base=base, fac=1, until=None, spot=None, perp=None, nota="simbolo doppio")]
        r["chain"] = json.dumps(ch); r["bn_spot"] = next((c["spot"] for c in ch[::-1] if c["spot"]), None)
        r["bn_perp"] = next((c["perp"] for c in ch[::-1] if c["perp"]), None)
        kb, b = find(bgp, base); ko, o = find(okp, base)
        r.update(bitget_perp=bool(b) and b.get("symbolStatus") == "normal", bitget_perp_simbolo=b["symbol"] if b else "",
                 bitget_perp_da=ms(b.get("launchTime") or b.get("openTime")) if b else "",
                 okx_perp=bool(o) and o.get("state") == "live", okx_perp_simbolo=o["instId"] if o else "",
                 okx_perp_da=ms(o.get("listTime")) if o else "")
        out.append(r)
    df = pd.DataFrame(out); df.to_csv(HERE / "data" / "universe_raw.csv", index=False)
    inc = df[df.escluso.fillna("") == ""]
    print("righe", len(df), "| incluse", len(inc), "| escluse", (df.escluso.fillna("") != "").sum())
    print("oggi 1-500 incluse", inc.rank_oggi.notna().sum(), "| con perp Binance", inc.bn_perp.notna().sum(),
          "| perp Bitget", int(inc.bitget_perp.sum()), "| perp OKX", int(inc.okx_perp.sum()))
    for c in [c for c in df.columns if re.fullmatch(r"rank_\d{4}", c)]:
        print(c, "incluse", inc[c].notna().sum(), "rank 101-200 incluse", ((inc[c] > 100) & (inc[c] <= 200)).sum())
