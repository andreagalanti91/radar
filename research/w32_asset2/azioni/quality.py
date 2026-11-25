"""W3.2 asset ciclo 2 · azioni · controlli di qualità sui dati scaricati (nessun rendimento di strategia).

Per ogni linea Yahoo: sedute, buchi di calendario > 7 giorni, sedute con volume 0, salti giornalieri |Δ| > 25% sulla chiusura
rettificata (possibili errori o eventi veri: da guardare, non si correggono), OHLC incoerenti (H < max(O,C) o L > min(O,C)),
coerenza del prezzo con la classifica: ultima chiusura in USD (cambio Yahoo) / prezzo USD della classifica CompaniesMarketcap
(≈ 1 se stessa linea; diverso da 1 per ADR con rapporto di conversione o classi diverse). Uscita: quality.csv.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D = HERE / "data"


def fx_last(cur: str) -> float:
    if cur == "USD":
        return 1.0
    p = D / "fx" / f"{cur}.csv.gz"
    return float(pd.read_csv(p, index_col=0)["usd_per_unit"].dropna().iloc[-1]) if p.exists() else np.nan


if __name__ == "__main__":
    uni = pd.read_csv(HERE / "universe.csv")
    cmc = pd.read_csv(D / "cmc_today.csv").set_index("slug")
    raw = pd.read_csv(D / "raw" / "cmc_today_top500.csv") if (D / "raw" / "cmc_today_top500.csv").exists() else None
    meta = pd.read_csv(D / "meta.csv").set_index("yahoo")
    rows = []
    for _, u in uni.iterrows():
        for col in ("yahoo", "yahoo_us"):
            s = u[col]
            if not isinstance(s, str) or not (D / "px" / f"{s}.csv.gz").exists():
                continue
            f = pd.read_csv(D / "px" / f"{s}.csv.gz", index_col=0, parse_dates=True)
            gaps = f.index.to_series().diff().dt.days
            r = f["close"].pct_change()
            bad = ((f["high_raw"] < f[["open_raw", "close_raw"]].max(axis=1) - 1e-9) | (f["low_raw"] > f[["open_raw", "close_raw"]].min(axis=1) + 1e-9)).sum()
            cur = meta.loc[s, "currency"]
            px_usd = f["close_raw"].iloc[-1] * fx_last(cur)
            cmc_px = np.nan
            if raw is not None:
                m = raw[raw["Name"].str.strip() == str(u["name"]).strip()]
                cmc_px = float(m["price (USD)"].iloc[0]) if len(m) else np.nan
            rows.append(dict(yahoo=s, line="primaria" if col == "yahoo" else "USA", slug=u["slug"], currency=cur, first=str(f.index[0].date()),
                             last=str(f.index[-1].date()), sessions=len(f), gaps_gt7d=int((gaps > 7).sum()), zero_vol=int((f["volume"].fillna(0) == 0).sum()),
                             jumps_gt25=int((r.abs() > 0.25).sum()), max_jump=round(float(r.abs().max()), 3), ohlc_bad=int(bad),
                             last_usd=round(px_usd, 4), cmc_usd=cmc_px, ratio=round(px_usd / cmc_px, 3) if cmc_px == cmc_px and cmc_px else np.nan))
    q = pd.DataFrame(rows)
    q.to_csv(HERE / "quality.csv", index=False)
    print(q[(q.jumps_gt25 > 0) | (q.ohlc_bad > 0) | (q.gaps_gt7d > 0) | ((q.ratio - 1).abs() > 0.1)].to_string())
