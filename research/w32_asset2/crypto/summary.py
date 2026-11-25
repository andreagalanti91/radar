"""w32_asset2/crypto: tabelle in markdown per DATI.md (solo conteggi, nessun rendimento). Stampa su stdout."""
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent; D = HERE / "data"
c = pd.read_csv(D / "counts.csv"); y = pd.read_csv(D / "counts_anno.csv"); s = pd.read_csv(D / "survivorship.csv")
q = pd.read_csv(D / "qc.csv"); src = pd.read_csv(D / "sources.csv").set_index("ticker")
b = lambda v: "sì" if v == True else "no"

def tab(df):
    print("| " + " | ".join(df.columns) + " |"); print("|" + "---|" * len(df.columns))
    for r in df.itertuples(index=False): print("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |")

def nucleus(col, n, label):
    print(f"\n### {label}")
    x = c[c[col] <= n].sort_values(col)
    rows = []
    for r in x.itertuples():
        yy = y[y.ticker == r.ticker]
        rows.append(dict(rank=int(getattr(r, col)), moneta=r.ticker if r.simbolo == r.ticker else f"{r.ticker} ({r.simbolo_2020 if col == 'rank_2020' else r.simbolo})",
                         classe=r.classe, dati=f"{r.dati_da or ''}→{r.dati_a or ''}" if isinstance(r.dati_da, str) else "",
                         perp_da=r.perp_da if isinstance(r.perp_da, str) else "", completa_da=r.completa_da if isinstance(r.completa_da, str) else "",
                         anni_c=r.anni_completa if r.anni_completa else "", ingr_L_S=f"{int(r.ingressi_long)}/{int(r.ingressi_short)}" if pd.notna(r.ingressi) else "",
                         sovr_BTC=f"{r.sovr_btc_stesso_lato_pct:.0f}/{r.sovr_btc_opposto_pct:.0f}/{r.btc_flat_pct:.0f}" if pd.notna(r.sovr_btc_stesso_lato_pct) else "",
                         bitget=b(r.bitget_perp), okx=b(r.okx_perp), cat=r.categoria if r.categoria != "crypto" else ""))
    tab(pd.DataFrame(rows))

if __name__ == "__main__":
    inc = c[c.classe != "esclusa"]
    for lab, m in (("oggi", c.rank_oggi.notna()), ("2020", c.rank_2020.notna()), ("unione", c.ticker.notna())):
        x = c[m]; print(lab, "totale", len(x), "escluse", (x.classe == "esclusa").sum(), "incluse", (x.classe != "esclusa").sum(),
                        dict(x[x.classe != "esclusa"].classe.value_counts()),
                        "perp Bitget", int(x[x.classe != "esclusa"].bitget_perp.fillna(False).sum()), "perp OKX", int(x[x.classe != "esclusa"].okx_perp.fillna(False).sum()),
                        "valutabili con perp Bitget o OKX", int(((x.classe == "valutabile") & (x.bitget_perp.fillna(False) | x.okx_perp.fillna(False))).sum()))
    print("\nesclusioni per categoria (unione):", dict(c[c.classe == "esclusa"].categoria.str.split(",").str[0].value_counts()))
    print("esclusioni oggi:", dict(c[(c.classe == "esclusa") & c.rank_oggi.notna()].categoria.str.split(",").str[0].value_counts()))
    print("esclusioni 2020:", dict(c[(c.classe == "esclusa") & c.rank_2020.notna()].categoria.str.split(",").str[0].value_counts()))
    nucleus("rank_oggi", 20, "Top 20 di oggi")
    nucleus("rank_2020", 20, "Top 20 al 29/12/2019")
    v = c[c.classe == "valutabile"].sort_values("completa_da")
    print("\n### Valutabili"); tab(v[["ticker", "rank_oggi", "rank_2020", "completa_da", "anni_completa", "ingressi", "ingressi_long", "ingressi_short",
                                    "sovr_btc_stesso_lato_pct", "sovr_btc_opposto_pct", "btc_flat_pct", "bitget_perp", "okx_perp"]])
    print("\n### Brevi"); tab(c[c.classe == "breve"].sort_values("completa_da")[["ticker", "rank_oggi", "rank_2020", "perp_da", "completa_da", "anni_completa", "ingressi", "bitget_perp", "okx_perp"]])
    print("\n### Solo prezzo"); tab(c[c.classe == "solo prezzo"][["ticker", "rank_oggi", "rank_2020", "dati_da", "dati_a", "bitget_perp", "okx_perp"]])
    print("\n### Senza dati"); x = c[c.classe == "senza dati"]
    print("oggi:", " ".join(f"{r.ticker}({int(r.rank_oggi)})" for r in x[x.rank_oggi.notna()].sort_values("rank_oggi").itertuples()))
    print("solo 2020:", " ".join(f"{r.simbolo_2020}({int(r.rank_2020)})" for r in x[x.rank_oggi.isna()].sort_values("rank_2020").itertuples()))
    print("\n### Ingressi per anno (somma valutabili | brevi), lato L/S")
    for cl in ("valutabile", "breve"):
        t = y[y.ticker.isin(c[c.classe == cl].ticker)].groupby("anno")[["ingressi_long", "ingressi_short", "sett_cond_long", "sett_cond_short"]].sum()
        print(cl); print(t.to_string())
    print("\n### SOL e TAO per anno"); print(y[y.ticker.isin(["BTC", "ETH", "SOL", "TAO"])].to_string(index=False))
    print("\n### Sopravvivenza 2020"); print(s[s.escluso.isna()].stato.str.replace(r" \(.*\)", "", regex=True).value_counts().to_string())
    print("in top 200 oggi:", int((s[s.escluso.isna()].rank_oggi <= 200).sum()))
    d = s[s.stato.str.startswith("delistata", na=False)]; print("delistate:", "; ".join(f"{r.simbolo_2020}({r.rank_2020}) {r.binance_da}→{r.binance_fino}" for r in d.itertuples()))
    print("\nQC:", "ferme", int(q.ferma.fillna(False).sum()), "| vol0 tolti", int(q.giorni_vol0_tolti.fillna(0).sum()), "su", int((q.giorni_vol0_tolti.fillna(0) > 0).sum()), "serie",
          "| salti x3", q[q.salti_x3 > 0][["ticker", "serie"]].values.tolist(), "| spot/perp>5%", q[q.spot_perp_giorni_gt5pct > 5][["ticker", "spot_perp_giorni_gt5pct"]].values.tolist())
    print("SOL fonti:", src.loc["SOL"].to_dict()); print("TAO fonti:", src.loc["TAO"].to_dict())
