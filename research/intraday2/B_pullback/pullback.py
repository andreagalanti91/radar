"""Famiglia B · pullback nel trend 1h (BTC, ETH, SOL). Regole in PREREG.md.

Uso:  python3 research/intraday2/B_pullback/pullback.py is      # fase 1: solo 2021-23, scelta
      python3 research/intraday2/B_pullback/pullback.py oos     # fase 2: giudizio 2024->oggi + robustezza
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from engine import (Exits, Sizing, Costs, load_all, backtest, metrics, placebo, neighbours, atr,  # noqa
                    resample, IS_END)

START = "2021-01-01"
EXITS = Exits(stop_atr=1.5, tp=[(1.5, 0.5), (3.0, 0.5)], tp_unit="R", be_after_tp1=True, time_bars=48,
              reverse_exit=False, reverse_entry=False)
SIZING = Sizing(mode="risk", risk_pct=0.01, leverage=2, allocation="shared", max_exposure=5.0)
COSTS = Costs()
COOLDOWN = 24

VARIANTS = {
    "B1": ("ema_retest", {"ema": 20, "adx": 20, "wick": 0.4}),
    "B2": ("ema_retest", {"ema": 50, "adx": 20, "wick": 0.4}),
    "B3": ("rsi2", {"rsi_lvl": 10, "adx": 20}),
    "B4": ("rsi14_hook", {"lo": 32, "hi": 40, "adx": 20}),
    "B5": ("vwap", {"n_above": 3}),
    "B6": ("bo_retest", {"don": 20, "window": 24}),
    "B7": ("ema_retest", {"ema": 20, "adx": 25, "wick": 0.4, "strict": True}),
    "B8": ("rsi2", {"rsi_lvl": 10, "adx": 25, "strict": True}),
}


# ------------------------------------------------------------------ helpers (no look-ahead)
def to_1h(s: pd.Series, tf: str, idx1h: pd.DatetimeIndex) -> pd.Series:
    """HTF series (indexed by HTF bar open) -> value known at the CLOSE of each 1h bar."""
    known = s.copy()
    known.index = s.index + pd.Timedelta(tf)          # time the HTF value becomes known
    close1h = idx1h + pd.Timedelta("1h")              # close time of each 1h bar
    out = known.reindex(known.index.union(close1h)).ffill().reindex(close1h)
    out.index = idx1h
    return out


def ema(s, n):
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def rsi(c, n):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def adx(df, n=14):
    h, l, c = df.high, df.low, df.close
    upm, dnm = h.diff(), -l.diff()
    pdm = np.where((upm > dnm) & (upm > 0), upm, 0.0)
    ndm = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    a = lambda x: pd.Series(x, index=df.index).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()  # noqa
    atr_ = a(tr)
    pdi, ndi = 100 * a(pdm) / atr_, 100 * a(ndm) / atr_
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def context(b: pd.DataFrame) -> dict:
    """Shared features, cached per asset."""
    idx = b.index
    h4, d1 = resample(b, "4h"), resample(b, "1D")
    c4 = h4.close
    e20, e50, e200 = ema(c4, 20), ema(c4, 50), ema(c4, 200)
    up4 = (e20 > e50) & (e50 > e200) & (e50 > e50.shift(6))
    dn4 = (e20 < e50) & (e50 < e200) & (e50 < e50.shift(6))
    de50 = ema(d1.close, 50)
    upd, dnd = d1.close > de50, d1.close < de50
    f = lambda s, tf: to_1h(s.astype(float), tf, idx)  # noqa
    ctx = {
        "Tup": (f(up4, "4h") == 1) & (f(upd, "1D") == 1),
        "Tdn": (f(dn4, "4h") == 1) & (f(dnd, "1D") == 1),
        "Dup": f(upd, "1D") == 1, "Ddn": f(dnd, "1D") == 1,
        "adx4": f(adx(h4), "4h"),
        "ema4": {20: f(e20, "4h"), 50: f(e50, "4h")},
        "h4": h4,
    }
    a1 = atr(b, 14)
    atrp = a1 / b.close
    ctx["atr1"] = a1
    ctx["atrp_lo"] = atrp.rolling(2160, min_periods=500).quantile(0.2)
    ctx["atrp_hi"] = atrp.rolling(2160, min_periods=500).quantile(0.8)
    ctx["atrp"] = atrp
    ctx["hour"] = pd.Series(idx.hour, index=idx)
    return ctx


_CTX = {}


def ctx_of(b):
    k = (id(b), len(b))
    if k not in _CTX:
        _CTX[k] = context(b)
    return _CTX[k]


def strict_mask(b, cx):
    hr = cx["hour"]
    return (cx["atrp"] >= cx["atrp_lo"]) & (cx["atrp"] <= cx["atrp_hi"]) & (hr >= 7) & (hr <= 21)


def cooldown(side: pd.Series, n=COOLDOWN) -> pd.Series:
    v = side.to_numpy().astype(int).copy()
    last = -10 ** 9
    for i in np.flatnonzero(v):
        if i - last < n:
            v[i] = 0
        else:
            last = i
    return pd.Series(v, index=side.index)


# ------------------------------------------------------------------ signals
def signals(b: pd.DataFrame, kind: str, ema=20, adx=20, wick=0.4, strict=False, rsi_lvl=10, lo=32, hi=40,
            n_above=3, don=20, window=24, **_) -> pd.DataFrame:
    cx = ctx_of(b)
    o, h, l, c = b.open, b.high, b.low, b.close
    rng = (h - l).replace(0, np.nan)
    adx_ok = cx["adx4"] > adx
    if kind == "ema_retest":
        e = cx["ema4"][ema] if ema in cx["ema4"] else to_1h(globals()["ema"](cx["h4"].close, ema), "4h", b.index)
        lw = (np.minimum(o, c) - l) / rng
        uw = (h - np.maximum(o, c)) / rng
        L = cx["Tup"] & adx_ok & (l <= e) & (c > e) & (c > o) & (lw >= wick)
        S = cx["Tdn"] & adx_ok & (h >= e) & (c < e) & (c < o) & (uw >= wick)
    elif kind == "rsi2":
        r = rsi(c, 2)
        e50 = cx["ema4"][50]
        L = cx["Tup"] & adx_ok & (r < rsi_lvl) & (c > e50)
        S = cx["Tdn"] & adx_ok & (r > 100 - rsi_lvl) & (c < e50)
    elif kind == "rsi14_hook":
        r = rsi(c, 14)
        L = cx["Tup"] & adx_ok & (r > hi) & (r.shift() <= hi) & (r.rolling(6).min() < lo)
        S = cx["Tdn"] & adx_ok & (r < 100 - hi) & (r.shift() >= 100 - hi) & (r.rolling(6).max() > 100 - lo)
    elif kind == "vwap":
        tp = (h + l + c) / 3
        v = b.volume.fillna(0)
        day = b.index.floor("D")
        vw = (tp * v).groupby(day).cumsum() / v.groupby(day).cumsum().replace(0, np.nan)
        above = (c > vw).astype(int).shift().rolling(n_above).sum() == n_above
        below = (c < vw).astype(int).shift().rolling(n_above).sum() == n_above
        hr = cx["hour"]
        sess = (hr >= 12) & (hr <= 20)
        newday = b.index.hour < n_above  # previous closes must belong to the same session
        L = cx["Tup"] & sess & ~newday & above & (l <= vw) & (c > vw) & (c > o)
        S = cx["Tdn"] & sess & ~newday & below & (h >= vw) & (c < vw) & (c < o)
    elif kind == "bo_retest":
        h4 = cx["h4"]
        dh, dl = h4.high.rolling(don).max().shift(), h4.low.rolling(don).min().shift()
        bu = (h4.close > dh)
        bd = (h4.close < dl)
        fu = to_1h(bu.astype(float), "4h", b.index) == 1   # last closed 4h bar broke out
        fd = to_1h(bd.astype(float), "4h", b.index) == 1
        lvl_u = to_1h(dh, "4h", b.index).where(fu)
        lvl_d = to_1h(dl, "4h", b.index).where(fd)
        # level of the first breakout bar, carried for `window` 1h bars after it becomes known
        lu = lvl_u.where(lvl_u.notna() & lvl_u.shift().isna()).ffill(limit=window - 1)
        ld = lvl_d.where(lvl_d.notna() & lvl_d.shift().isna()).ffill(limit=window - 1)
        a1 = cx["atr1"]
        L = cx["Dup"] & lu.shift().notna() & lu.notna() & (l <= lu + 0.25 * a1) & (c > lu)
        S = cx["Ddn"] & ld.shift().notna() & ld.notna() & (h >= ld - 0.25 * a1) & (c < ld)
    else:
        raise ValueError(kind)
    if strict:
        m = strict_mask(b, cx)
        L, S = L & m, S & m
    side = L.fillna(False).astype(int) - S.fillna(False).astype(int)
    return pd.DataFrame({"side": cooldown(side)})


def run(bars, vid, start=START, end=None, **over):
    kind, p = VARIANTS[vid]
    p = {**p, **over}
    sig = {a: signals(b, kind, **p) for a, b in bars.items()}
    return backtest(bars, sig, EXITS, SIZING, COSTS, start, end)


def row(res):
    m = metrics(res)
    t = res.trades
    return {k: m.get(k) for k in ("final", "ret_pct", "max_dd", "trades", "trades_per_month", "win_rate", "pf",
                                    "exp_R", "mar")} | {"longs": int((t.side == 1).sum()) if len(t) else 0}


def per_asset(res):
    t = res.trades
    return t.groupby("asset")["pnl"].sum().round(0).to_dict() if len(t) else {}


def buy_hold(bars, start, end=None):
    eq = []
    for a, b in bars.items():
        c = b.close.loc[pd.Timestamp(start, tz="UTC"):]
        if end is not None:
            c = c.loc[:pd.Timestamp(end, tz="UTC") - pd.Timedelta("1h")]
        eq.append(c / c.iloc[0] * 10_000 / 3)
    e = pd.concat(eq, axis=1).ffill().sum(axis=1).resample("1D").last()
    dd = (e / e.cummax() - 1).min() * 100
    return {"final": round(e.iloc[-1]), "ret_pct": round((e.iloc[-1] / 1e4 - 1) * 100, 1), "max_dd": round(dd, 1)}


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    phase = sys.argv[1] if len(sys.argv) > 1 else "is"
    bars = load_all("1h")
    if phase == "is":
        rows = []
        for vid in VARIANTS:
            r = run(bars, vid, START, IS_END)
            rows.append({"id": vid, **row(r), "assets": per_asset(r)})
        df = pd.DataFrame(rows)
        print(df.to_string(index=False))
        ok = df[(df.trades_per_month.between(2, 12)) & (df.pf >= 1.2) & (df.exp_R > 0)]
        if len(ok):
            best = ok.sort_values(["exp_R", "mar"], ascending=False)
            top = best.iloc[0]
            tie = best[best.exp_R >= top.exp_R - 0.02]
            choice = tie.sort_values("mar", ascending=False).iloc[0]["id"]
        else:
            choice = None
        print("SCELTA (IS):", choice)
        df.to_csv(os.path.join(HERE, "is_results.csv"), index=False)
        json.dump({"choice": choice}, open(os.path.join(HERE, "choice.json"), "w"))
    if phase == "oos":
        nplac = int(sys.argv[2]) if len(sys.argv) > 2 else 500
        rows, extra = [], {}
        for vid in VARIANTS:
            ri, ro, ra = (run(bars, vid, START, IS_END), run(bars, vid, IS_END), run(bars, vid, START))
            mi, mo, ma = row(ri), row(ro), row(ra)
            t = ro.trades
            no_best = float(t.pnl.sum() - t.pnl.max()) if len(t) else np.nan
            pl = placebo(ro, bars, EXITS, SIZING, COSTS, n=nplac, seed=1)
            kind, p = VARIANTS[vid]
            num = {k: v for k, v in p.items() if not isinstance(v, bool)}
            nb = neighbours(lambda q: run(bars, vid, IS_END, **q), num)
            rows.append({"id": vid, "ALL_final": ma["final"], "ALL_ret": ma["ret_pct"], "ALL_dd": ma["max_dd"],
                         "ALL_tpm": ma["trades_per_month"], "ALL_wr": ma["win_rate"], "ALL_pf": ma["pf"],
                         "ALL_expR": ma["exp_R"], "ALL_mar": ma["mar"],
                         "IS_ret": mi["ret_pct"], "IS_pf": mi["pf"], "IS_expR": mi["exp_R"],
                         "OOS_ret": mo["ret_pct"], "OOS_dd": mo["max_dd"], "OOS_tpm": mo["trades_per_month"],
                         "OOS_wr": mo["win_rate"], "OOS_pf": mo["pf"], "OOS_expR": mo["exp_R"],
                         "OOS_assets_pos": sum(v > 0 for v in per_asset(ro).values()),
                         "OOS_no_best": round(no_best, 0), "plac_pctl": pl["pctl"].get("ret_pct"),
                         "nb_median_ret": round(float(nb.ret_pct.iloc[1:].median()), 1)})
            print(rows[-1], flush=True)
        df = pd.DataFrame(rows)
        df.to_csv(os.path.join(HERE, "oos_results.csv"), index=False)
        print(df.to_string(index=False))
        print("B&H ALL", buy_hold(bars, START), "IS", buy_hold(bars, START, IS_END), "OOS", buy_hold(bars, IS_END))
        best = json.load(open(os.path.join(HERE, "choice.json")))["choice"] or "B5"
        run(bars, best, START).trades.to_csv(os.path.join(HERE, f"trades_{best}.csv"), index=False)
