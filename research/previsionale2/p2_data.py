"""Previsionale 2 · dataset (PREREG §1–3): regimi di mercato e variabili di politica economica con i ritardi di disponibilità.
Riusa research/previsionale/fc_data.py (non lo riscrive). policy(idx) e regimes(close) sono pure e riusabili dal tool.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "previsionale"))
sys.path.insert(0, str(ROOT))
from fc_data import dataset, labels  # noqa: E402,F401

DATA = HERE / "data"
LAG = {"DFF": 2, "WALCL": 2, "WTREGEN": 2, "RRPONTSYD": 1, "DGS10": 1, "DGS2": 1, "DFII10": 1, "VIXCLS": 1, "DTWEXBGS": 8}
STABLE = ["pf", "sf", "rsi", "vol"]
POL = ["pol", "nl13", "dry", "curva", "usd", "vix", "fomc", "cpi"]
REG = ["U", "D", "A"]
INTER = ["pfU", "pfD"]
SETS = {"R": REG + STABLE + INTER, "P": POL, "RP": REG + STABLE + INTER + POL, "PF": ["pf"], "PFP": ["pf"] + POL}


def raw(name: str) -> pd.Series:
    d = pd.read_csv(DATA / f"{name}.csv", index_col=0, parse_dates=True)[name]
    return pd.to_numeric(d, errors="coerce").dropna()


def avail(name: str, idx: pd.DatetimeIndex) -> pd.Series:
    """Serie giornaliera su idx: il valore osservato il giorno d è utilizzabile dalla chiusura del giorno d + LAG (poi portato avanti)."""
    s = raw(name)
    s.index = s.index + pd.Timedelta(days=LAG[name])
    full = pd.date_range(min(s.index[0], idx[0]), idx[-1])
    return s.reindex(full).ffill().reindex(idx)


def cpi_yoy(idx: pd.DatetimeIndex) -> pd.DataFrame:
    """CPI annuo (non destagionalizzato) del mese m, utilizzabile dal giorno 25 del mese m+1. Colonne: yoy, cpi (segno)."""
    c = raw("CPIAUCNS")
    c = c.reindex(pd.date_range(c.index[0], c.index[-1], freq="MS"))          # mesi mancanti = NaN (10/2025)
    yoy = (c / c.shift(12) - 1).mul(100).round(1).dropna()
    sg = np.sign((yoy - yoy.shift(1)).round(1)).dropna()                        # confronto con l'ultimo mese pubblicato prima
    out = pd.DataFrame({"yoy": yoy, "cpi": sg}).dropna()
    out.index = out.index + pd.offsets.MonthBegin(1) + pd.Timedelta(days=24)
    full = pd.date_range(out.index[0], max(idx[-1], out.index[-1]))
    return out.reindex(full).ffill().reindex(idx)


def fomc_dates() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.read_csv(DATA / "fomc_dates.csv", parse_dates=["date"])["date"])


def policy(idx: pd.DatetimeIndex) -> pd.DataFrame:
    """Le 8 variabili di politica economica alla chiusura di t (PREREG §3) + serie di servizio per la parte descrittiva."""
    p = pd.DataFrame(index=idx)
    dff = avail("DFF", idx)
    p["dff"] = dff
    p["pol"] = dff - dff.shift(126)
    walcl = avail("WALCL", idx)
    nl = walcl - avail("WTREGEN", idx) - avail("RRPONTSYD", idx).fillna(0) * 1000
    p["walcl"], p["nl"] = walcl, nl
    p["nl13"] = (nl / nl.shift(91) - 1) * 100
    p["walcl13"] = (walcl / walcl.shift(91) - 1) * 100
    ry = avail("DFII10", idx)
    p["ry"] = ry
    p["dry"] = ry - ry.shift(63)
    p["curva"] = avail("DGS10", idx) - avail("DGS2", idx)
    usd = avail("DTWEXBGS", idx)
    p["usd"] = (usd / usd.shift(63) - 1) * 100
    p["vixlvl"] = avail("VIXCLS", idx)
    p["vix"] = np.log(p["vixlvl"])
    fd = fomc_dates().to_numpy()
    nxt = np.searchsorted(fd, idx.to_numpy(), side="right")                     # prima riunione con data > t
    days = np.array([(fd[i] - t).astype("timedelta64[D]").astype(int) if i < len(fd) else 999 for i, t in zip(nxt, idx.to_numpy())])
    p["fomc_days"] = days
    p["fomc"] = (days <= 7).astype(float)
    c = cpi_yoy(idx)
    p["cpi_yoy"], p["cpi"] = c["yoy"], c["cpi"]
    return p


def regimes(close: pd.Series) -> pd.DataFrame:
    """T: U/D/M su SMA200 e sua pendenza a 30 giorni; V: A/B su vol30 contro la mediana dei 365 giorni precedenti."""
    sma = close.rolling(200).mean()
    up = (close > sma) & (sma > sma.shift(30))
    dn = (close < sma) & (sma < sma.shift(30))
    T = pd.Series(np.where(up, "U", np.where(dn, "D", "M")), index=close.index).where(sma.shift(30).notna())
    v = np.log(close).diff().rolling(30).std()
    med = v.shift(1).rolling(365).median()
    V = pd.Series(np.where(v > med, "A", "B"), index=close.index).where(med.notna())
    return pd.DataFrame({"T": T, "V": V, "vol30": v, "sma200": sma})


def build(x: pd.DataFrame | None = None) -> pd.DataFrame:
    """Dataset completo: variabili del primo ciclo + regimi + politica + colonne dei modelli."""
    x = dataset() if x is None else x
    r = regimes(x["close"])
    p = policy(x.index)
    d = pd.concat([x, r, p], axis=1)
    d["U"] = (d["T"] == "U").astype(float).where(d["T"].notna())
    d["D"] = (d["T"] == "D").astype(float).where(d["T"].notna())
    d["A"] = (d["V"] == "A").astype(float).where(d["V"].notna())
    d["pfU"], d["pfD"] = d["pf"] * d["U"], d["pf"] * d["D"]
    return d


if __name__ == "__main__":
    d = build()
    print(d.index[0].date(), d.index[-1].date(), len(d))
    cols = REG + STABLE + INTER + POL
    print(pd.DataFrame({"dal": d[cols].apply(lambda s: s.first_valid_index()), "n": d[cols].notna().sum()}).to_string())
    print(d.loc["2015":, POL].describe().round(2).to_string())
    print(d.loc["2015":, "T"].value_counts().to_dict(), d.loc["2015":, "V"].value_counts().to_dict())
    print(d[["dff", "pol", "nl13", "ry", "dry", "curva", "usd", "vixlvl", "fomc_days", "cpi_yoy", "cpi", "T", "V"]].tail(3).to_string())
