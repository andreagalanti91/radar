"""Robustezza W2 + MACD: usa radar.weekly cosi' com'e' (costanti sostituite solo in memoria, radar/ non viene toccato)."""
from __future__ import annotations
import sys, warnings
from contextlib import contextmanager
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/short_w2"))
from radar import weekly as W  # noqa: E402
import short_lab as S  # noqa: E402  (solo per i caricatori dei dati lunghi)

_ORIG_WB = W.weekly_bars
BASE = dict(sma=40, ema_t=20, ema_x=21, trail=2.5, stop=2.5, macd=(8, 21, 5), old=16, flow="std", thr=0.0, f1=True)


def load():
    repo = S.load_repo()
    return repo, S.load_long(repo)


@contextmanager
def params(**kw):
    p = {**BASE, **kw}
    saved = {k: getattr(W, k) for k in ("SMA", "EMA_T", "EMA_X", "TRAIL_K", "STOP_K", "MACD_P", "OLD_TREND", "weekly_bars")}
    W.SMA, W.EMA_T, W.EMA_X, W.TRAIL_K, W.STOP_K = p["sma"], p["ema_t"], p["ema_x"], p["trail"], p["stop"]
    W.MACD_P, W.OLD_TREND = tuple(p["macd"]), (p["old"] if p["f1"] else 10 ** 9)

    def wb(f):
        w = _ORIG_WB(f)
        if p["flow"] == "std" and p["thr"] == 0.0:
            return w
        c = w["close"]
        up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
        dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
        if p["flow"] == "none":          # senza filtro di flusso (ingressi); la distribuzione resta com'e'
            w["long"] = (up & (c > w["ema21"]) & w["f1_ok"]).fillna(False)
            w["short"] = (dn & (c < w["ema21"])).fillna(False)
        else:                            # soglia diversa solo sui long
            w["long"] = (up & (c > w["ema21"]) & (w["flow"] > p["thr"]) & w["f1_ok"]).fillna(False)
        return w
    W.weekly_bars = wb
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(W, k, v)


def run(f, start="2021-01-01", end=None, **kw):
    if end:
        f = f[f.index <= end]
    with params(**kw):
        return W.simulate(f, start=start)


def all_trades(r):
    return r["trades"] + ([dict(r["open"], pnl=r["open"]["pnl_close"], exit="open", reason="open")] if r["open"] else [])


def stats(e: pd.Series, trades=None) -> dict:
    e = e.dropna(); e = e / e.iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    tot = e.iloc[-1] - 1; dd = (e / e.cummax() - 1).min()
    cagr = e.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 else np.nan
    out = dict(finale=round(10000 * e.iloc[-1]), rend=round(tot * 100, 1), cagr=round(cagr * 100, 1), dd=round(dd * 100, 1),
               mar=round(tot / abs(dd), 2) if dd < 0 else np.nan, calmar=round(cagr / abs(dd), 2) if dd < 0 else np.nan)
    if trades is not None:
        pn = np.array([t["pnl"] for t in trades])
        out.update(n=len(pn), wr=round((pn > 0).mean() * 100, 1) if len(pn) else np.nan,
                   peggiore=round(pn.min() * 100, 1) if len(pn) else np.nan)
    return out


def bh(f, start, end=None):
    c = f["close"][f.index >= start]
    if end:
        c = c[c.index <= end]
    return c
