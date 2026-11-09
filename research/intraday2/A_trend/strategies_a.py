"""Famiglia A · trend e rotture 4h: segnali delle 8 varianti preregistrate (PREREG.md)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import atr, Exits, Sizing  # noqa

EXITS = Exits(stop_atr=1.5, tp=[(1.5, .5), (3, .5)], tp_unit="R", be_after_tp1=True, time_bars=12,
              reverse_exit=False, reverse_entry=False)
SIZING = Sizing(mode="risk", risk_pct=0.01, leverage=2, allocation="equal", max_exposure=3)


def daily_regime(b, ema_d=50):
    """+1/-1/0 from CLOSED daily bars, aligned to 4h bars whose close is after the day close."""
    d = b["close"].resample("1D").last().dropna()
    e = d.ewm(span=ema_d, adjust=False, min_periods=ema_d).mean()
    reg = pd.Series(0, index=d.index)
    reg[(d > e) & (e > e.shift(5))] = 1
    reg[(d < e) & (e < e.shift(5))] = -1
    # 4h bar opening at t closes at t+4h; last completed day = (t+4h).normalize() - 1 day
    key = (b.index + pd.Timedelta(hours=4)).normalize() - pd.Timedelta(days=1)
    return pd.Series(reg.reindex(key).fillna(0).to_numpy(), index=b.index).astype(int)


def adx(b, n=14):
    h, l, c = b["high"], b["low"], b["close"]
    up, dn = h.diff(), -l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=b.index)
    ndm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=b.index)
    a = atr(b, n)
    pdi = 100 * pdm.ewm(alpha=1 / n, adjust=False).mean() / a
    ndi = 100 * ndm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi)
    return dx.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def rel_vol(b, n=20):
    v = b["volume"]
    return v / v.rolling(n, min_periods=n).mean().shift(1)


def donchian_break(b, N):
    hh = b["high"].rolling(N).max().shift(1)
    ll = b["low"].rolling(N).min().shift(1)
    c = b["close"]
    up = (c > hh) & ~(c.shift() > hh.shift())
    dn = (c < ll) & ~(c.shift() < ll.shift())
    return up, dn, hh, ll


def _out(up, dn):
    side = up.fillna(False).astype(int) - dn.fillna(False).astype(int)
    return pd.DataFrame({"side": side})


def ichi(b, tk=9, kj=26, sb=52, ema_d=None, **_):
    h, l, c = b["high"], b["low"], b["close"]
    ten = (h.rolling(tk).max() + l.rolling(tk).min()) / 2
    kij = (h.rolling(kj).max() + l.rolling(kj).min()) / 2
    sa = ((ten + kij) / 2).shift(kj)
    sbb = ((h.rolling(sb).max() + l.rolling(sb).min()) / 2).shift(kj)
    top, bot = np.maximum(sa, sbb), np.minimum(sa, sbb)
    up = (ten > kij) & (ten.shift() <= kij.shift()) & (c > top)
    dn = (ten < kij) & (ten.shift() >= kij.shift()) & (c < bot)
    if ema_d:
        r = daily_regime(b, ema_d); up &= r == 1; dn &= r == -1
    return _out(up, dn)


def don(b, N=55, v=1.5, ema_d=None, adx_min=None, **_):
    up, dn, _, _ = donchian_break(b, N)
    rv = rel_vol(b)
    up &= rv >= v; dn &= rv >= v
    if ema_d:
        r = daily_regime(b, ema_d); up &= r == 1; dn &= r == -1
    if adx_min:
        ax = adx(b); up &= ax >= adx_min; dn &= ax >= adx_min
    return _out(up, dn)


def sqz(b, bb=20, look=180, pct=15, N=20, ema_d=None, **_):
    c = b["close"]
    w = 4 * c.rolling(bb).std() / c.rolling(bb).mean()
    rank = w.rolling(look, min_periods=look).rank(pct=True) * 100
    comp = (rank <= pct).astype(float).rolling(6, min_periods=1).max() > 0
    up, dn, _, _ = donchian_break(b, N)
    up &= comp; dn &= comp
    if ema_d:
        r = daily_regime(b, ema_d); up &= r == 1; dn &= r == -1
    return _out(up, dn)


def retest(b, N=55, ema_d=50, w=6, tol=0.25, **_):
    up, dn, hh, ll = donchian_break(b, N)
    r = daily_regime(b, ema_d)
    up &= r == 1; dn &= r == -1
    a = atr(b).to_numpy(); hi, lo, c = b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy()
    side = np.zeros(len(b), int)
    w = int(round(w))
    for sgn, ev, lvl in ((1, up.to_numpy(), hh.to_numpy()), (-1, dn.to_numpy(), ll.to_numpy())):
        for i in np.flatnonzero(ev):
            L = lvl[i]
            for j in range(i + 1, min(i + 1 + w, len(b))):
                if sgn * (c[j] - L) <= 0:      # closed back through the level: setup cancelled
                    break
                touch = lo[j] <= L + tol * a[j] if sgn == 1 else hi[j] >= L - tol * a[j]
                if touch:
                    side[j] = sgn
                    break
    return pd.DataFrame({"side": side}, index=b.index)


VARIANTS = {
    "A1 ICHI": (ichi, {"tk": 9, "kj": 26, "sb": 52}),
    "A2 DON": (don, {"N": 55, "v": 1.5}),
    "A3 DON_REG": (don, {"N": 55, "v": 1.5, "ema_d": 50}),
    "A4 SQZ": (sqz, {"bb": 20, "look": 180, "pct": 15, "N": 20}),
    "A5 SQZ_REG": (sqz, {"bb": 20, "look": 180, "pct": 15, "N": 20, "ema_d": 50}),
    "A6 DON_ADX": (don, {"N": 55, "v": 1.5, "ema_d": 50, "adx_min": 20}),
    "A7 RETEST": (retest, {"N": 55, "ema_d": 50, "w": 6, "tol": 0.25}),
    "A8 ICHI_REG": (ichi, {"tk": 9, "kj": 26, "sb": 52, "ema_d": 50}),
}
