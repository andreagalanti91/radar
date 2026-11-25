"""w32_asset2/crypto: bias di sopravvivenza. Per ogni moneta della top 200 al 29/12/2019 (CMC via Common Crawl): rank oggi
(CoinGecko top 250 del 25/11/2026), stato su Binance dall'archivio (ultimo mese spot/perp: delistata se < 2026-10), e se i
dati esistono ancora nell'archivio pubblico. Scrive data/survivorship.csv."""
import json
from pathlib import Path
import pandas as pd
import bv_list
HERE = Path(__file__).resolve().parent; D = HERE / "data"; RAW = D / "raw"

if __name__ == "__main__":
    u = pd.read_csv(D / "universe_raw.csv"); u = u[u.rank_2020.notna()].sort_values("rank_2020")
    cg = {x["symbol"].upper(): (x["market_cap_rank"], x["name"].lower()) for x in json.load(open(RAW / "cg_top.json"))}
    rk = lambda t, n: cg[t][0] if t in cg and cg[t][1] == n.lower() else None     # stesso simbolo E stesso nome (BEAM 2020 != BEAM oggi)
    rows = []
    for r in u.itertuples():
        row = dict(rank_2020=int(r.rank_2020), simbolo_2020=r.symbol_2020, nome=r.name, ticker_oggi=r.ticker,
                   rank_oggi=r.rank_oggi if pd.notna(r.rank_oggi) else rk(r.ticker, r.name), escluso=r.escluso if isinstance(r.escluso, str) else "")
        if not row["escluso"]:
            ch = json.loads(r.chain); sp = [c["spot"] for c in ch if c["spot"]]; pp = [c["perp"] for c in ch if c["perp"]]
            ms = [m for s in sp for m in bv_list.months("spot", s)]; mp = [m for s in pp for m in bv_list.months("um", s)]
            last = max(ms + mp) if ms or mp else ""
            row.update(binance_spot=",".join(sp), binance_perp=",".join(pp), binance_da=min(ms + mp) if ms or mp else "", binance_fino=last,
                       nota=ch[0].get("nota", ""),
                       stato=("mai su Binance (USDT)" if not last else "quotata su Binance" if last >= "2026-10" else f"delistata da Binance ({last})"))
            if row["stato"] == "quotata su Binance" and pd.isna(row["rank_oggi"]): row["stato"] += ", fuori dalla top 250"
        rows.append(row)
    df = pd.DataFrame(rows); df.to_csv(D / "survivorship.csv", index=False)
    inc = df[df.escluso == ""]
    print("2020 incluse", len(inc), "| ancora in top 200 oggi", int((inc.rank_oggi <= 200).sum()))
    print(inc.stato.str.replace(r" \(.*\)", "", regex=True).value_counts().to_string())
