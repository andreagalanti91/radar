"""W3.2 asset ciclo 2 · azioni · arricchisce universe.csv (valuta, borsa, dati da/a, Bitget, OKX, da quando, conteggi) e scrive
tabelle.txt per DATI.md. Ordine: universe.py -> build_universe.py -> fetch.py -> quality.py -> exchanges.py -> count.py -> finalize.py.
Nessun rendimento."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
D = HERE / "data"

if __name__ == "__main__":
    u = pd.read_csv(HERE / "universe.csv")
    base = [c for c in ["yahoo", "yahoo_us", "us_ticker", "exch_alias", "slug", "name", "cmc_symbol", "country", "rank_today", "rank_2020",
                        "mcap_today", "mcap_2019"] if c in u.columns]
    u = u[base]
    meta = pd.read_csv(D / "meta.csv").set_index("yahoo")
    m = pd.read_csv(D / "exchanges" / "match.csv").fillna("").set_index("yahoo")
    c = pd.read_csv(HERE / "counts.csv")
    c = c[c.line == "primaria"].pivot_table(index="yahoo", columns="variant", values="entries", aggfunc="first")
    u["currency"] = u["yahoo"].map(meta["currency"])
    u["exchange"] = u["yahoo"].map(meta["full_exchange"])
    u["data_from"] = u["yahoo"].map(meta["first"])
    u["data_to"] = u["yahoo"].map(meta["last"])
    u["years"] = ((pd.to_datetime(u["data_to"]) - pd.to_datetime(u["data_from"])).dt.days / 365.25).round(2)
    for k in ("bitget_perp", "bitget_since", "okx_perp", "okx_since", "okx_token", "okx_token_since"):
        u[k] = u["yahoo"].map(m[k]).fillna("")
    u["bitget"] = (u["bitget_perp"] != "").map({True: "si", False: "no"})
    u["okx"] = (u["okx_perp"] != "").map({True: "si", False: "no"})
    since = pd.concat([pd.to_datetime(u["bitget_since"].replace("", None)), pd.to_datetime(u["okx_since"].replace("", None))], axis=1).min(axis=1)
    u["perp_since"] = since.dt.strftime("%Y-%m-%d").fillna("")
    for v in ("prezzo", "cmf20", "cmf_w4", "obv_slope20", "obv_chg20", "ad_slope20"):
        u[f"n_{v}"] = u["yahoo"].map(c[v]) if v in c.columns else None
    u.to_csv(HERE / "universe.csv", index=False)

    L = []
    top = u[u.rank_today <= 100]
    t20 = u[u.rank_2020 <= 100]
    L.append(f"Universo: {len(u)} titoli; top 100 oggi {len(top)}, top 100 a fine 2019 {len(t20)}, in entrambe {len(top.merge(t20, on='yahoo'))}")
    usciti = t20[t20.rank_today > 100].sort_values("rank_2020")
    L.append(f"Usciti dalla top 100 (fine 2019 -> oggi): {len(usciti)}")
    L += [f"  {r.rank_2020:>3.0f} -> {r.rank_today:>3.0f}  {r.name} ({r.yahoo})" for r in usciti.itertuples()]
    entrati = top[~(top.rank_2020 <= 100)].sort_values("rank_today")
    L.append(f"Entrati nella top 100 dopo il 2019: {len(entrati)}")
    L += [f"  {r.rank_today:>3.0f} (2019: {'non quotata' if r.rank_2020 != r.rank_2020 else int(r.rank_2020)})  {r.name} ({r.yahoo})" for r in entrati.itertuples()]
    for lab, s in (("oggi", top), ("fine 2019", t20)):
        L.append(f"Operabili {lab}: Bitget perp {int((s.bitget == 'si').sum())}, OKX perp {int((s.okx == 'si').sum())}, "
                 f"almeno uno {int(((s.bitget == 'si') | (s.okx == 'si')).sum())} su {len(s)}")
    L.append("Paesi top 100 oggi: " + ", ".join(f"{k} {v}" for k, v in top.country.value_counts().items()))
    L.append("Paesi top 100 fine 2019: " + ", ".join(f"{k} {v}" for k, v in t20.country.fillna("n.d.").value_counts().items()))
    (HERE / "tabelle.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))
