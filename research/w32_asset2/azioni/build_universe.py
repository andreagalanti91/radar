"""W3.2 asset ciclo 2 · azioni · costruisce universe.csv dalle classifiche di CompaniesMarketcap (universe.py).

- rank_today: posizione nella classifica di oggi (companiesmarketcap.com, solo società quotate; ETF e fondi non sono nella
  classifica delle società). rank_2020: posizione per capitalizzazione a fine 2019 (tabella "end of year" delle pagine società)
  fra i candidati (prime 500 di oggi + EXTRA di universe.py), escluse le società senza valore 2019 (non quotate allora).
- yahoo: linea principale di quotazione (borsa locale; per gli ADR/OTC della classifica si usa la linea primaria, YAHOO_PRIMARY);
  yahoo_us: linea USA (ADR o quotazione diretta) quando esiste, perché i perp su azioni di Bitget/OKX seguono quella.
- us_ticker / exch_alias: codici usati per cercare lo strumento su Bitget/OKX (exchanges.py).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
D = HERE / "data"

# simbolo della classifica (ADR/OTC) -> linea primaria su Yahoo
YAHOO_PRIMARY = {
    "GOOG": "GOOGL", "TSM": "2330.TW", "TCEHY": "0700.HK", "NVS": "NOVN.SW", "AZN": "AZN.L", "HSBC": "HSBA.L",
    "SHEL": "SHEL.L", "RY": "RY.TO", "TM": "7203.T", "SAP": "SAP.DE", "MUFG": "8306.T", "ASML": "ASML.AS", "TD": "TD.TO",
    "TTE": "TTE.PA", "NVO": "NOVO-B.CO", "BHP": "BHP.AX", "SONY": "6758.T", "BUD": "ABI.BR", "SAN": "SAN.MC",
    "UL": "ULVR.L", "SNY": "SAN.PA", "GSK": "GSK.L", "BP": "BP.L", "BTI": "BATS.L", "DEO": "DGE.L", "RIO": "RIO.L",
    "TOELY": "8035.T", "NTES": "9999.HK", "PBR": "PETR4.SA", "VALE": "VALE3.SA", "ITUB": "ITUB4.SA", "ABEV": "ABEV3.SA",
    "INFY": "INFY.NS", "HDB": "HDFCBANK.NS", "IBN": "ICICIBANK.NS", "SMFG": "8316.T", "MFG": "8411.T", "SFTBY": "9984.T",
    "NTTYY": "9432.T", "BNS": "BNS.TO", "ENB": "ENB.TO", "CNI": "CNR.TO", "CP": "CP.TO", "SHOP": "SHOP.TO", "BMO": "BMO.TO",
    "LVMUY": "MC.PA", "LRLCY": "OR.PA", "NSRGY": "NESN.SW", "SIEGY": "SIE.DE", "ALIZY": "ALV.DE",
    "DTEGY": "DTE.DE", "BABA": "BABA", "JD": "JD", "PDD": "PDD", "BIDU": "BIDU", "SE": "SE", "CHL": "0941.HK",
    "PTR": "0857.HK", "SNP": "0386.HK", "LFC": "2628.HK", "IDCBY": "1398.HK", "CICHY": "0939.HK", "ACGBY": "1288.HK",
    "BACHY": "3988.HK", "PNGAY": "2318.HK", "MPNGY": "3690.HK", "XIACF": "1810.HK", "BYDDY": "1211.HK", "TOYOF": "7203.T",
    "ARM": "ARM", "LIN": "LIN", "SPOT": "SPOT", "ACN": "ACN", "MDT": "MDT", "CB": "CB", "ETN": "ETN", "SCCO": "SCCO",
    "UBS": "UBSG.SW", "ABBNY": "ABBN.SW", "ZURVY": "ZURN.SW", "CFRUY": "CFR.SW", "HESAY": "RMS.PA", "AIR.PA": "AIR.PA",
    "SAFRY": "SAF.PA", "EADSY": "AIR.PA", "IBDRY": "IBE.MC", "ITX.MC": "ITX.MC", "SBGSY": "SU.PA", "ELV": "ELV",
}
# per i titoli non USA con una linea USA quotata in borsa (ADR NYSE/Nasdaq o diretta; esclusi OTC) a cui si riferiscono i perp
US_LINE = {
    "2330.TW": "TSM", "0700.HK": "", "NOVN.SW": "NVS", "AZN.L": "AZN", "HSBA.L": "HSBC", "SHEL.L": "SHEL", "RY.TO": "RY",
    "7203.T": "TM", "SAP.DE": "SAP", "8306.T": "MUFG", "ASML.AS": "ASML", "TD.TO": "TD", "TTE.PA": "TTE", "NOVO-B.CO": "NVO",
    "BHP.AX": "BHP", "6758.T": "SONY", "ABI.BR": "BUD", "SAN.MC": "SAN", "ULVR.L": "UL", "SAN.PA": "SNY", "GSK.L": "GSK",
    "BP.L": "BP", "BATS.L": "BTI", "DGE.L": "DEO", "RIO.L": "RIO", "9999.HK": "NTES", "PETR4.SA": "PBR", "VALE3.SA": "VALE",
    "ITUB4.SA": "ITUB", "ABEV3.SA": "ABEV", "INFY.NS": "INFY", "HDFCBANK.NS": "HDB", "ICICIBANK.NS": "IBN", "8316.T": "SMFG",
    "8411.T": "MFG", "BNS.TO": "BNS", "ENB.TO": "ENB", "CNR.TO": "CNI", "CP.TO": "CP", "SHOP.TO": "SHOP", "BMO.TO": "BMO",
    "UBSG.SW": "UBS", "0941.HK": "", "9988.HK": "BABA", "RO.SW": "RHHBY", "1211.HK": "", "1810.HK": "",   # OTC o delistati: nessuna linea USA
    "TCS.NS": "", "RELIANCE.NS": "", "0005.HK": "HSBC",
}
# codice base dello strumento su Bitget/OKX per i titoli non USA (o con codice diverso dal ticker), separati da |
EXCH_ALIAS = {
    "samsung": "SAMSUNG", "sk-hynix": "SKHYNIX", "tencent": "TENCENT|TENCENTHKD", "tsmc": "TSM|TWTSM", "toyota": "TOYOTA|TM",
    "sony": "SONY|JPSONY", "xiaomi": "XIAOMI|XIAOMIHKD", "meituan": "MEITUAN", "mitsubishi-ufj-financial": "MUFG|JPMUFG",
    "softbank": "SOFTBANK", "reliance-industries": "RELIANCE", "tata-consultancy-services": "TCS", "hdfc-bank": "HDFCBANK",
    "icici-bank": "ICICIBANK", "infosys": "INFY", "state-bank-of-india": "SBIN", "bharti-airtel": "BHARTIARTL",
    "hindustan-unilever": "HINDUNILVR", "itc": "ITC", "larsen-toubro": "LT", "hyundai": "HYUNDAI", "kia": "KIA",
    "lg-energy-solution": "LGENERGY", "samsung-biologics": "SSBIOLOGICS", "kb-financial-group": "KBFG", "naver": "NAVER",
    "murata-manufacturing": "MURATA", "fast-retailing": "FASTRETAILING", "tokyo-electron": "TOKYOEL", "advantest": "ADVANTEST",
    "kioxia": "KIOXIA", "smic": "SMIC", "netease": "NETEASE|NTES", "kuaishou": "KUAISHOU", "pop-mart": "POPMART", "byd": "BYD",
    "lenovo": "LENOVOHKD", "cxmt": "CXMT", "zhongji-innolight": "ZHONGJI", "gigadevice": "GIGADEVICE|GIGADEV",
    "mediatek": "MEDIATEK", "hon-hai-precision": "HONHAI", "foxconn": "HONHAI", "delta-electronics": "TWDELTA",
    "berkshire-hathaway": "BRKB", "alphabet-google": "GOOGL|GOOG", "spacex": "SPCX", "anthropic": "ANT|ANTHROPIC",
    "novo-nordisk": "NVO", "alibaba": "BABA", "saudi-aramco": "", "keyence": "", "nintendo": "",
}
# codici di Bitget/OKX che sono materie prime, indici o ETF e non vanno mai attribuiti a un'azione omonima
NOT_STOCK = {"CL", "BZ", "NG", "XAU", "XAG", "XPT", "XPD", "XCU", "COPPER", "NATGAS", "PAXG", "XAUT", "H100", "B200"}


def main() -> pd.DataFrame:
    t = pd.read_csv(D / "cmc_today.csv")
    y = pd.read_csv(D / "cmc_2019.csv")
    t = t.merge(y[["slug", "mcap_2019"]], on="slug", how="left")
    extra = y[~y.slug.isin(t.slug)].copy()
    extra["name"] = extra["page_title"].str.replace(r"^Market capitalization of ", "", regex=True).str.replace(r" \(.*\)$", "", regex=True)
    extra["cmc_symbol"] = y.loc[extra.index, "page_title"].str.extract(r"\(([^)]*)\)$")[0]
    allc = pd.concat([t, extra[["slug", "name", "cmc_symbol", "mcap_2019"]]], ignore_index=True)
    r19 = allc.dropna(subset=["mcap_2019"]).sort_values("mcap_2019", ascending=False)
    r19["rank_2020"] = range(1, len(r19) + 1)
    allc = allc.merge(r19[["slug", "rank_2020"]], on="slug", how="left")
    u = allc[(allc.rank_today <= 100) | (allc.rank_2020 <= 100)].copy()
    u["yahoo"] = u["cmc_symbol"].map(lambda s: YAHOO_PRIMARY.get(s, s))
    u["yahoo_us"] = u["yahoo"].map(lambda s: US_LINE.get(s, ""))
    u["us_ticker"] = [us if us else (s if ("." not in s and not s[:1].isdigit()) else "") for s, us in zip(u["yahoo"], u["yahoo_us"])]
    u["exch_alias"] = u["slug"].map(lambda s: EXCH_ALIAS.get(s, ""))
    u["name"] = u["name"].astype(str).str.split().str.join(" ")
    u = u.sort_values(["rank_today", "rank_2020"], na_position="last")
    return u


if __name__ == "__main__":
    u = main()
    print(len(u), "titoli:", (u.rank_today <= 100).sum(), "top 100 oggi,", (u.rank_2020 <= 100).sum(), "top 100 a fine 2019,",
          ((u.rank_today <= 100) & (u.rank_2020 <= 100)).sum(), "in entrambe")
    cols = ["yahoo", "yahoo_us", "us_ticker", "exch_alias", "slug", "name", "cmc_symbol", "country", "rank_today", "rank_2020",
            "mcap_today", "mcap_2019"]
    u[cols].to_csv(HERE / "universe.csv", index=False)
