"""Dati orari dello studio "assorbimento dei market maker" (PREREG.md, sezione 2). Nessun look-ahead.

Uso: python research/mm_assorbimento/mm_data.py  → cache /tmp/radar-work/mm/feat.pkl
Fonti: h.pkl (perp 1h + OI, research/liq_squeeze/sq_data.py), data/taker_1h.csv, hmaps.pkl (mappe stimate), funding 8h
(research/intraday2/data, poi data/funding.csv / 3), W3 (radar/weekly.simulate) per regime e giorni flat.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

LQ = Path("/tmp/radar-work/liqsqueeze")
WORK = Path("/tmp/radar-work/mm"); WORK.mkdir(parents=True, exist_ok=True)
END = pd.Timestamp("2026-11-17 23:00")


def pct_prev(x: np.ndarray, n: int) -> np.ndarray:
    """Percentile (0–100) di x[i] rispetto agli n valori PRECEDENTI (barra esclusa): quota dei precedenti < x[i]."""
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    win = swv(x[:-1], n)                      # win[j] = x[j : j+n] → precedenti di i = j+n
    cur = x[n:]
    valid = ~np.isnan(win).any(axis=1) & ~np.isnan(cur)
    p = (win < cur[:, None]).mean(axis=1) * 100
    out[n:] = np.where(valid, p, np.nan)
    return out


def w3_context() -> tuple[pd.Series, pd.Series, dict]:
    """Regime settimanale W3 (noto dal lunedì 00 UTC) e giorni flat di W3 (nessuna posizione aperta nel giorno UTC)."""
    f = build_features(load_all()); f = f[f["close"].notna()]
    r = W.simulate(f)
    w = r["weekly"]
    reg = pd.Series("neutro", index=w.index)
    for i in range(5, len(w)):
        wk = w.iloc[i]
        if wk["close"] > wk["sma"] and wk["ema20"] > w["ema20"].iloc[i - 1]:
            reg.iloc[i] = "long"
        elif wk["close"] < wk["sma"] and wk["sma"] < w["sma"].iloc[i - 4] and wk["ema20"] < w["ema20"].iloc[i - 1]:
            reg.iloc[i] = "short"
    days = pd.date_range("2021-01-01", END.normalize(), freq="D")
    inpos = pd.Series(False, index=days)
    trs = r["trades"] + ([r["open"]] if r["open"] else [])
    for t in trs:
        a = pd.Timestamp(t["entry"])
        b = pd.Timestamp(t["exit"]) if t.get("exit") else days[-1] + pd.Timedelta(days=1)
        # uscite a mercato all'apertura (ema, dist) liberano il giorno d'uscita; stop/trailing intraday no
        last = b if t.get("reason") in ("stop", "trail") or not t.get("exit") else b - pd.Timedelta(days=1)
        inpos.loc[a:last] = True
    # regime valido nella settimana successiva alla domenica di chiusura
    reg_day = reg.copy(); reg_day.index = reg_day.index + pd.Timedelta(days=1)
    reg_day = reg_day.reindex(days, method="ffill").fillna("neutro")
    return reg_day, ~inpos, r


def build() -> dict:
    h = pd.read_pickle(LQ / "h.pkl")
    h = h[h.index <= END]
    full = pd.date_range(h.index[0], END, freq="h")
    miss = full.difference(h.index)
    h = h.reindex(full)
    c = h["close"].ffill()
    for k in ("open", "high", "low", "close"):        # ore mancanti (24 h, 28/10/2026): barra piatta, nessun segnale
        h[k] = h[k].fillna(c)
    tk = pd.read_csv(ROOT / "data/taker_1h.csv", parse_dates=["t"]).set_index("t").reindex(full)
    H = h.join(tk)
    H["vol"] = H["spot_vol"] + H["perp_vol"]
    ds, dp = 2 * H["spot_taker"] - H["spot_vol"], 2 * H["perp_taker"] - H["perp_vol"]
    H["dS"], H["dP"] = ds, dp
    H["D"] = (ds + dp) / H["vol"]
    oib = H["oi_usd"] / H["close"]
    H["dOI"] = oib.diff()
    H["rng"] = (H["high"] - H["low"]) / H["close"]
    H.loc[miss, ["vol", "D", "rng"]] = np.nan
    H["vol_pct"] = pct_prev(H["vol"].to_numpy(float), 720)
    H["rng_pct"] = pct_prev(H["rng"].to_numpy(float), 720)
    # candele 4h (00, 04, … UTC), assegnate all'ultima ora della barra (nota alla sua chiusura)
    g = H.groupby(H.index.floor("4h"))
    B4 = pd.DataFrame({"high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                       "spot_vol": g["spot_vol"].sum(min_count=4), "perp_vol": g["perp_vol"].sum(min_count=4),
                       "dS": g["dS"].sum(min_count=4), "dP": g["dP"].sum(min_count=4), "n": g["close"].count(),
                       "oib": oib.groupby(H.index.floor("4h")).last()})
    B4["vol"] = B4["spot_vol"] + B4["perp_vol"]
    B4["D"] = (B4["dS"] + B4["dP"]) / B4["vol"]
    B4["dOI"] = B4["oib"].diff()
    B4["rng"] = (B4["high"] - B4["low"]) / B4["close"]
    B4["vol_pct"] = pct_prev(B4["vol"].to_numpy(float), 180)
    B4["rng_pct"] = pct_prev(B4["rng"].to_numpy(float), 180)
    B4["zhi"] = B4["high"].rolling(3).max(); B4["zlo"] = B4["low"].rolling(3).min()
    B4.index = B4.index + pd.Timedelta(hours=3)
    B4 = B4[B4["n"] == 4]
    # ATR giornaliero a 14 giorni dei giorni UTC chiusi prima dell'ora
    gd = H.groupby(H.index.normalize())
    Dd = pd.DataFrame({"high": gd["high"].max(), "low": gd["low"].min(), "close": gd["close"].last()})
    tr = pd.concat([Dd["high"] - Dd["low"], (Dd["high"] - Dd["close"].shift()).abs(),
                    (Dd["low"] - Dd["close"].shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)
    H["atr_d"] = atr.reindex(H.index.normalize()).to_numpy()
    # funding a 8h
    fu = pd.read_csv(ROOT / "research/intraday2/data/BTCUSDT_funding.csv.gz")
    fu["t"] = pd.to_datetime(fu["ts"]).dt.tz_localize(None)
    fu = fu.set_index("t")["rate"]
    fd = pd.read_csv(ROOT / "data/funding.csv", parse_dates=["date"]).set_index("date")["funding"]
    FR = pd.Series(0.0, index=full)
    stamps = full[full.hour.isin([0, 8, 16])]
    v = fu.reindex(stamps)
    fill = (fd.reindex(stamps.normalize()).to_numpy() / 3)
    v = v.where(v.notna(), pd.Series(fill, index=stamps))
    FR.loc[stamps] = v.fillna(0).to_numpy()
    # mappe stimate
    M = pd.read_pickle(LQ / "hmaps.pkl")
    M = M[M.index <= END + pd.Timedelta(hours=1)]
    I = (M["S6"] - M["L6"]) / (M["S6"] + M["L6"])
    up = M["up"].apply(lambda cl: sorted([p for p, u, r in cl if r >= 0.30]))
    dn = M["dn"].apply(lambda cl: sorted([p for p, u, r in cl if r >= 0.30], reverse=True))
    reg_day, flat_day, w3 = w3_context()
    return {"H": H, "B4": B4, "FR": FR, "I": I, "up": up, "dn": dn, "reg_day": reg_day, "flat_day": flat_day,
            "w3": w3, "missing": miss}


def load(refresh: bool = False) -> dict:
    p = WORK / "feat.pkl"
    if p.exists() and not refresh:
        return pd.read_pickle(p)
    d = build()
    pd.to_pickle(d, p)
    return d


if __name__ == "__main__":
    d = load(refresh=True)
    H = d["H"]
    print(H.index[0], H.index[-1], len(H), "ore mancanti", len(d["missing"]))
    print("taker da", H["vol"].first_valid_index(), "pct da", H["vol_pct"].first_valid_index())
    print("mappe", d["I"].index[0], d["I"].index[-1], len(d["I"]))
    print("W3 flat giorni", int(d["flat_day"].sum()), "regime", d["reg_day"].value_counts().to_dict())
