"""Multi-asset · regole preregistrate (research/multi_asset/PREREG.md). Non modifica radar/.

- s1_*: W3.1 "solo prezzo" (regime SMA40/EMA20, ingresso EMA21, filtro MACD(8,21,5) nei trend >= 16 sett., stop e trailing
  2,5 ATR sett. a cricchetto, uscita alla chiusura sett. oltre la EMA21, rischio 10% allo stop iniziale; niente flusso, funding,
  distribuzione). Settimana W-FRI per azioni/ETF/indice (decisione all'ultima seduta della settimana, esecuzione all'apertura
  della seduta successiva); W-SUN per BTC (motore research/p2_nuovi/p2_engine.py, identico a W3.1).
- ema_vix: indicatore "EMA200D combined VIX" (research/ema200_vix/LOGICA.md); use_vix=False -> S2 (solo EMA).
In fase 1 si contano solo gli eventi; i rendimenti si calcolano in fase 2 dopo il commit del PREREG.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D = HERE / "data"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "p2_nuovi"))
from radar import weekly as W  # noqa: E402

MAIN = ["SPX", "GLD", "SLV", "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "AVGO", "TSLA", "BRK-B", "LLY"]
DOW = "AXP BA CAT C KO XOM GE HPQ HD HON IBM INTC IP JNJ JPM MCD MRK MMM MO PG WMT DIS RTX T".split()
CUT = "2026-11-20"
BTC_CUT = "2026-11-15"
FEE = 0.0005          # costo per lato azioni/ETF/indice (commissione + slippage), stress 0,0015
SHORT_COST = 0.03     # costo annuo dello short sul nozionale (stima)
PERIODS = {"A": ("2000-01-01", "2010-12-31"), "B": ("2011-01-01", "2020-12-31"), "C": ("2021-01-01", CUT)}
BTC_PERIODS = {"A": ("2021-01-01", "2022-12-31"), "B": ("2023-01-01", "2024-12-31"), "C": ("2025-01-01", BTC_CUT)}


def load(name: str) -> pd.DataFrame:
    p = D / f"{name}.csv.gz" if (D / f"{name}.csv.gz").exists() else D / "dow2000" / f"{name}.csv.gz"
    f = pd.read_csv(p, index_col=0, parse_dates=True)
    return f[f.index <= CUT]


def load_vix() -> pd.Series:
    return pd.read_csv(D / "VIX.csv.gz", index_col=0, parse_dates=True)["close"].loc[:CUT]


def load_btc() -> dict:
    from p2_data import load as p2load
    d = p2load()
    d["f"] = d["f"][d["f"].index <= BTC_CUT]
    return d


def test_start(f: pd.DataFrame, need_vix: bool = False) -> pd.Timestamp:
    """Primo giorno testabile: un anno di calendario dopo il primo dato (riscaldamento di SMA40/ATR/EMA200); per S3 non prima del 1991."""
    s = f.index[0] + pd.DateOffset(years=1)
    return max(s, pd.Timestamp("1991-01-01")) if need_vix else s


# ---------------------------------------------------------------- S1: W3.1 solo prezzo
def s1_weekly(f: pd.DataFrame, rule: str = "W-FRI") -> pd.DataFrame:
    w = f[["open", "high", "low", "close"]].resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    w = w.dropna(subset=["close"])
    w["day"] = f["close"].resample(rule).apply(lambda s: s.index[-1] if len(s) else pd.NaT).reindex(w.index)
    c = w["close"]
    w["sma"] = c.rolling(W.SMA).mean()
    w["ema20"] = c.ewm(span=W.EMA_T, adjust=False).mean()
    w["ema21"] = c.ewm(span=W.EMA_X, adjust=False).mean()
    tr = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
    w["atr"] = tr.ewm(alpha=1 / W.ATR_N, adjust=False).mean()
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    above = (c > w["sma"]).astype(int)
    w["trend_age"] = above.groupby((above == 0).cumsum()).cumsum()
    m = c.ewm(span=W.MACD_P[0], adjust=False).mean() - c.ewm(span=W.MACD_P[1], adjust=False).mean()
    w["macd"], w["macd_sig"] = m, m.ewm(span=W.MACD_P[2], adjust=False).mean()
    w["f1_ok"] = (w["trend_age"] < W.OLD_TREND) | ((w["macd"] > w["macd_sig"]) & (w["macd"] > 0))
    w["long"] = (up & (c > w["ema21"]) & w["f1_ok"]).fillna(False)
    w["short"] = (dn & (c < w["ema21"])).fillna(False)
    w["dist_long"] = False
    w["dist_short"] = False
    w["flow"], w["fund7"] = 0.0, 0.0
    return w[w["day"] <= f.index[-1]]


def s1_sim(f: pd.DataFrame, start, end=None, long_only: bool = False, k: float = W.STOP_K, risk: float = 0.10,
           fee: float = FEE, short_cost: float = SHORT_COST, capital: float = 10000.0, wb: pd.DataFrame | None = None) -> dict:
    """Motore giornaliero di S1 per azioni/ETF/indice (stessa sequenza degli eventi di radar.weekly.simulate)."""
    f = f[f["close"].notna()]
    if end is not None:
        f = f[f.index <= pd.Timestamp(end)]
    w = s1_weekly(f) if wb is None else wb[wb["day"] <= f.index[-1]]
    dec = pd.Series(w.index, index=pd.DatetimeIndex(w["day"]))          # giorno di decisione -> etichetta della settimana
    idx = f.index
    O, H, L, C = (f[c].to_numpy(float) for c in ("open", "high", "low", "close"))
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    trades, eq, ex = [], np.full(len(idx), np.nan), np.zeros(len(idx))

    def close_all(px, i, reason):
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * fee
        tr.update(exit=str(idx[i].date()), exit_px=px, reason=reason, pnl=cash / tr["eq0"] - 1, move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i], i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = min(1.0, risk / (k * wk["atr"] / wk["close"]))
                q = side * lt * cash / O[i]
                qty, cost = q, q * O[i]
                cash -= abs(q) * O[i] * fee
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=O[i], expo=lt, eq0=cash + abs(q) * O[i] * fee,
                          stop0=float(wk["close"] - side * k * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
                tr["stop"] = tr["stop0"]
            pend = None
        if side:
            tl = tr["best"] - side * k * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                close_all(min(O[i], stop) if side > 0 else max(O[i], stop), i, "stop" if stop == tr["stop0"] else "trail")
            else:
                if side < 0 and i > 0:
                    cash -= abs(qty) * C[i] * short_cost * (idx[i] - idx[i - 1]).days / 365.0
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        ex[i] = abs(qty * C[i]) / eq[i] if side else 0.0
        if day in dec.index:
            wk = w.loc[dec[day]]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            if d and d[0] == "enter" and d[1] < 0 and long_only:
                d = None
            pend = d + (wk, day) if d else None
    out = {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "expo": pd.Series(ex[t0:], idx[t0:]), "open": None}
    if side:
        out["open"] = dict(tr, pnl=(eq[-1] - abs(qty) * C[-1] * fee) / tr["eq0"] - 1)
    return out


def s1_btc(f: pd.DataFrame, start=W.START, end=None, long_only: bool = False, k: float = W.STOP_K) -> dict:
    """S1 su BTC: motore W3.1 (p2_engine, W-SUN, costi e funding reali) con segnali senza flusso e senza distribuzione."""
    import p2_engine as E
    ff = f[f["close"].notna()]
    if end is not None:
        ff = ff[ff.index <= end]
    w = W.weekly_bars(ff)
    s = s1_weekly(ff, "W-SUN")
    for c in ("long", "short", "dist_long", "dist_short"):
        w[c] = s[c].reindex(w.index).fillna(False).astype(bool)
    allow = (lambda side, day: side > 0) if long_only else None
    return E.simulate(ff, start=start, end=end, allow=allow, k=k, wb=w)


# ---------------------------------------------------------------- S2/S3: EMA200D (+ VIX)
def ema_vix(close: pd.Series, vol: pd.Series | None, start, end=None, ema: int = 200, thr: float = 34.0,
            horizon: int = 60, use_vix: bool = True, stop: float | None = None) -> list[dict]:
    """Eventi dell'indicatore alla CHIUSURA. close: chiusure giornaliere dell'asset; vol: VIX (o DVOL) giornaliero.
    Il crossover del VIX si valuta sulle sedute del VIX e agisce alla chiusura dell'asset dello stesso giorno (se l'asset
    non quota quel giorno, alla prima chiusura successiva). Priorità a parità di giorno: ingresso di trend."""
    close = close.dropna()
    e = close.ewm(span=ema, adjust=False).mean()
    xo = (close > e) & (close.shift() <= e.shift())
    xu = (close < e) & (close.shift() >= e.shift())
    vx = pd.Series(False, index=close.index)
    if use_vix and vol is not None:
        v = vol.dropna()
        vxo = (v > thr) & (v.shift() <= thr)
        days = v.index[vxo.to_numpy()]
        pos = close.index.searchsorted(days)
        pos = pos[pos < len(close)]
        vx.iloc[np.unique(pos)] = True
    end = pd.Timestamp(end) if end is not None else close.index[-1]
    sel = (close.index >= pd.Timestamp(start)) & (close.index <= end)
    idx, C, E_, XO, XU, VX = close.index[sel], close[sel].to_numpy(), e[sel].to_numpy(), xo[sel].to_numpy(), xu[sel].to_numpy(), vx[sel].to_numpy()
    trades, cur = [], None
    for i, day in enumerate(idx):
        if cur is None:
            if XO[i]:
                cur = dict(entry=day, entry_px=C[i], kind="trend", origin="trend")
            elif VX[i]:
                cur = dict(entry=day, entry_px=C[i], kind="vix", origin="vix")
            continue
        if cur["kind"] == "trend":
            if XU[i]:
                trades.append(dict(cur, exit=day, exit_px=C[i], reason="xunder")); cur = None
        else:
            if stop is not None and C[i] <= cur["entry_px"] * (1 - stop):
                trades.append(dict(cur, exit=day, exit_px=C[i], reason="stop")); cur = None
            elif day >= cur["entry"] + pd.Timedelta(days=horizon):
                if C[i] > E_[i]:
                    cur["kind"] = "trend"
                else:
                    trades.append(dict(cur, exit=day, exit_px=C[i], reason="horizon")); cur = None
    if cur is not None:
        trades.append(dict(cur, exit=None, exit_px=C[-1], reason="open"))
    return trades


def vix_crossings(vol: pd.Series, thr: float, start, end=None) -> int:
    v = vol.dropna()
    v = v[(v.index >= pd.Timestamp(start) - pd.Timedelta(days=7)) & (v.index <= (pd.Timestamp(end) if end else v.index[-1]))]
    x = (v > thr) & (v.shift() <= thr)
    return int(x[v.index >= pd.Timestamp(start)].sum())


def dvol_threshold(vix_thr: float, dvol: pd.Series, vix: pd.Series) -> tuple[float, float]:
    """Soglia DVOL equivalente: percentile di vix_thr nello storico VIX 1990–2020 → stesso quantile dello storico DVOL disponibile."""
    vv = vix.loc[:"2020-12-31"].dropna()
    q = float((vv < vix_thr).mean())
    return q, float(dvol.dropna().quantile(q))
