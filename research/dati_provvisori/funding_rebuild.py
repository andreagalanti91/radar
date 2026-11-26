"""Funding Binance ricostruito dall'indice di premio pubblico (premiumIndexKlines 1m di data.binance.vision).

Formula pubblica di Binance (USDT-M, intervallo 8h): P = media dei premi del periodo pesata 1, 2, …, n;
F = P + clamp(I − P, −0,05%, +0,05%) con I = 0,01% per 8h; tetto ±0,3% (mai raggiunto da BTC nel periodo).
Il pagamento delle 00:00/08:00/16:00 UTC usa i premi delle 8 ore precedenti; "date" = giorno del pagamento (come
data.fetch_funding: groupby della data di calc_time).

funding_8h(prem) → Serie dei tassi per ora di pagamento; daily(f8) → somma per giorno.
Uso diretto: python3 -I funding_rebuild.py RAW REPO → confronto con l'archivio mensile (funding_rebuild_check.csv).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

I_RATE, CLAMP, CAP = 0.0001, 0.0005, 0.003


def load_premium(raw: Path) -> pd.Series:
    p = raw / "premium_1m.parquet"
    df = pd.read_parquet(p) if p.exists() else pd.read_csv(raw / "premium_1m.csv.gz", parse_dates=["t"])
    return df.set_index("t")["close"].astype(float)


def binance_formula(p: np.ndarray | pd.Series) -> np.ndarray | pd.Series:
    """Tasso di un periodo dal premio medio P (stessa formula usata anche sul tasso OKX nella correzione F2)."""
    return np.clip(p + np.clip(I_RATE - p, -CLAMP, CLAMP), -CAP, CAP)


def funding_8h(prem: pd.Series, min_share: float = 0.9) -> pd.Series:
    """Tasso Binance per ogni pagamento (indice = ora del pagamento). Periodi con meno del 90% dei minuti: NaN."""
    t = prem.index
    # minuto [t, t+1m) appartiene al pagamento successivo: ceil a 8h di (t + 1 minuto)
    pay = (t + pd.Timedelta(minutes=1)).ceil("8h")
    df = pd.DataFrame({"p": prem.values, "pay": pay})
    df["k"] = df.groupby("pay").cumcount() + 1          # peso 1..n in ordine di tempo
    g = df.assign(pw=df["p"] * df["k"]).groupby("pay")
    n = g.size()
    pavg = g["pw"].sum() / g["k"].sum()
    out = binance_formula(pavg)
    return out.where(n >= min_share * 480)


def daily(f8: pd.Series) -> pd.Series:
    return f8.groupby(f8.index.normalize()).sum(min_count=3)


if __name__ == "__main__":
    raw, repo = Path(sys.argv[1]), Path(sys.argv[2])
    out = Path(__file__).resolve().parent
    f8 = funding_8h(load_premium(raw))
    f8.rename("rate").to_csv(raw / "binance_funding_rebuilt_8h.csv")
    d = daily(f8).rename("rebuilt")
    act = pd.read_csv(repo / "funding.csv", index_col=0, parse_dates=True)
    act = act[act["source"] == "binance"]["funding"]
    j = pd.concat([act.rename("binance"), d], axis=1).dropna()
    j["err"] = j["rebuilt"] - j["binance"]
    j["fund7_b"] = j["binance"].rolling(7).mean()
    j["fund7_r"] = j["rebuilt"].rolling(7).mean()
    j["err7"] = j["fund7_r"] - j["fund7_b"]
    j.to_csv(out / "funding_rebuild_check.csv")
    for k in ("err", "err7"):
        a = j[k].abs().dropna()
        print(k, "n", len(a), "mediana", f"{a.median():.2e}", "p95", f"{a.quantile(.95):.2e}", "max", f"{a.max():.2e}",
              "esatti(<1e-7)", f"{(a < 1e-7).mean():.1%}")
    print("per anno |err7| p95:", j["err7"].abs().groupby(j.index.year).quantile(.95).map("{:.1e}".format).to_dict())
