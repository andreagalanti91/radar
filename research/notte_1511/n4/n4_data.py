"""N4 · dati comuni: feature giornaliere (radar/features.py), regime W3, OI unito dal 2021, variabili discrete (PREREG.md).
Uso come modulo: from n4_data import build ; df, VARS = build(th=0.43, thd=0.5)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from radar.data import load_all  # noqa: E402
from radar.features import build_features, _z  # noqa: E402
from radar import weekly  # noqa: E402

H_CACHE = Path("/tmp/radar-work/liqfasce/work/h.pkl")
# OI 14/11 non ancora nell'archivio Binance: stima con la variazione OKX (rubik, tutti i contratti BTC) 13/11 → 14/11
OKX_OI = {"2026-11-13": 3458826730.1744, "2026-11-14": 3243896818.3761}


def raw():
    d = load_all()
    f = build_features(d)
    f = f[f["close"].notna()].copy()
    # OI in USD: 2021-01→2021-11 dalla cache oraria (ultimo valore del giorno), poi metrics.csv
    m = d["metrics"]["oi_usd"].where(d["metrics"]["oi_usd"] > 0)
    oi = m.copy()
    if H_CACHE.exists():
        h = pd.read_pickle(H_CACHE)["oi_usd"].resample("D").last()
        h.index = pd.DatetimeIndex(h.index).as_unit("ns")
        oi = pd.concat([h[h.index < m.index[0]], m])
    oi = oi[~oi.index.duplicated(keep="last")].sort_index()
    if "2026-11-14" not in oi.index.strftime("%Y-%m-%d") and pd.Timestamp("2026-11-13") in oi.index:
        oi.loc[pd.Timestamp("2026-11-14")] = oi.loc["2026-11-13"] * OKX_OI["2026-11-14"] / OKX_OI["2026-11-13"]
    f["oi_usd"] = oi.reindex(f.index)
    return f


def weekly_ctx(f: pd.DataFrame) -> pd.DataFrame:
    w = weekly.weekly_bars(f)
    c = w["close"]
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    w["reg"] = np.where(up, "L", np.where(dn, "S", "N"))
    w.loc[w["sma"].isna(), "reg"] = np.nan
    # ultima settimana CHIUSA al giorno t: la barra W-SUN che termina la domenica ≤ t
    ctx = w[["reg", "sma", "ema21"]].reindex(f.index, method="ffill")
    # la barra W-SUN etichettata domenica D copre lun..D: per i giorni lun..sab successivi vale la settimana chiusa D
    return ctx


def cut3(x: pd.Series, a: float, b: float, labels=("lo", "mid", "hi")) -> pd.Series:
    out = pd.Series(np.where(x < a, labels[0], np.where(x > b, labels[2], labels[1])), index=x.index, dtype=object)
    out[x.isna()] = np.nan
    return out


def build(th: float = 0.43, thd: float = 0.5, f: pd.DataFrame | None = None):
    f = raw() if f is None else f
    ctx = weekly_ctx(f)
    c = f["close"]
    df = pd.DataFrame(index=f.index)
    df["close"], df["high"], df["low"] = c, f["high"], f["low"]
    for h in (7, 14, 30):
        df[f"r{h}"] = c.shift(-h) / c - 1
    # informazione del giorno precedente per flussi/derivati (come live_flow)
    pf, sf = f["pf14z"].shift(1), f["sf14z"].shift(1)
    fz = f["funding_z"].shift(1)
    lo = np.log(f["oi_usd"])
    doi = lo.diff()
    oiz = _z(f["oi_usd"].pct_change(7, fill_method=None), 180).shift(1)
    sig = doi.rolling(180, min_periods=90).std()
    ret1 = c.pct_change()
    liq_day = pd.Series(np.where(doi <= -2 * sig, np.where(ret1 < 0, 1, -1), 0), index=f.index)
    liq_day[sig.isna()] = np.nan
    ll = (liq_day == 1).astype(int).rolling(3).max().shift(1)
    ls = (liq_day == -1).astype(int).rolling(3).max().shift(1)
    liq = pd.Series(np.where((ll == 1) & (ls == 0), "LL", np.where((ls == 1) & (ll == 0), "LS", "0")), index=f.index, dtype=object)
    liq[sig.shift(1).isna()] = np.nan
    df["REG"] = ctx["reg"]
    df["PFs"] = pd.Series(np.where(pf > 0, "pos", "neg"), index=f.index, dtype=object).where(pf.notna())
    df["PFt"] = cut3(pf, -th, th)
    df["SFs"] = pd.Series(np.where(sf > 0, "pos", "neg"), index=f.index, dtype=object).where(sf.notna())
    df["SFt"] = cut3(sf, -th, th)
    df["DIV"] = cut3(sf - pf, -thd, thd, ("perp", "pari", "spot"))
    df["FUND"] = cut3(fz, -th, th)
    df["OI"] = cut3(oiz, -th, th)
    df["LIQ"] = liq
    ds = c / ctx["sma"] - 1
    de = c / ctx["ema21"] - 1
    df["DSMA"] = cut3(ds, 0.0, 0.20, ("sotto", "0-20", "oltre20"))
    df["DEMA"] = cut3(de, -0.05, 0.05, ("sotto5", "pm5", "sopra5"))
    raw_cols = dict(pf14z=pf, sf14z=sf, div=sf - pf, funding_z=fz, oi_z=oiz, dsma=ds, dema=de, liq_day=liq_day)
    for k, v in raw_cols.items():
        df["x_" + k] = v
    return df, f


VARS = ["REG", "PFs", "PFt", "SFs", "SFt", "DIV", "FUND", "OI", "LIQ", "DSMA", "DEMA"]
BASE = {"PFs": "PF", "PFt": "PF", "SFs": "SF", "SFt": "SF"}

if __name__ == "__main__":
    df, f = build()
    print(df.tail(5).T)
    print(df.loc["2021":, VARS].notna().mean().round(3))
