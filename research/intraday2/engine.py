"""Shared intraday backtest engine (research/intraday2).

Plug-in contract
----------------
A strategy produces, per asset, a signal frame aligned with the bars index (bar OPEN time, UTC):
    side      +1 long / -1 short / 0 none, decided at the bar CLOSE  -> entry at NEXT bar open
    stop      optional absolute stop price for that entry (NaN -> use Exits.stop_pct / stop_atr)
    stop_pct  optional per-entry stop distance as fraction of entry price (overrides Exits)
    max_bars  optional per-entry time exit in bars (overrides Exits.time_bars)
    exit      optional bool: close any open position at the next bar open (explicit exit signal)
A plain Series is accepted as `side`.

Typical use
-----------
    from engine import load_bars, Exits, Sizing, Costs, backtest, metrics, report
    bars = {a: load_bars(a, "4h") for a in ASSETS}
    sig  = {a: my_signals(bars[a]) for a in ASSETS}
    res  = backtest(bars, sig, Exits(stop_atr=2, tp=[(1.5, .5), (3, .5)], tp_unit="R"),
                    Sizing(mode="risk", risk_pct=0.01, leverage=3), Costs(), start="2021-01-01")
    print(report(res))

Model (all deliberately conservative)
-------------------------------------
* Entry at next bar open (+slippage, +taker fee). One position per asset; signals while in a position are ignored.
* Intrabar order: gap at open through the stop -> fill at open; stop touched -> stop (ALWAYS before any TP in the
  same bar); then TPs in order (fill at max(level, open)). If a TP moves the stop to breakeven and the same bar's
  low also reaches the BE level, the remainder is stopped at BE in that bar (be_same_bar=True).
* Trailing stop is updated at bar close from the highest high / lowest low since entry and is active from the next bar.
* Time exit / signal exit / reversal exit fill at the next bar open.
* Funding: rate of each funding event (bars.funding, at bar-open time) x position notional at that bar's open,
  longs pay positive rates. Charged if the position is open at the event time.
* Liquidation (isolated margin at Sizing.leverage, maintenance mmr): long liq = E*(1-1/L+mmr). If the adverse
  extreme reaches it before the trade's own exit, the remaining position is lost at the liq price (margin gone).
* Sizing uses REALISED equity (closed PnL) at entry time; equity curve is marked to market at every bar close.
"""
from __future__ import annotations

import itertools
import math
import os
import time
from dataclasses import dataclass, field, replace
from typing import Callable

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ASSETS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
IS_END = "2024-01-01"  # in-sample 2021-2023, out-of-sample 2024 -> now


# ----------------------------------------------------------------------------------------------- data
def load_bars(asset: str, tf: str = "1h", metrics: bool = True, data_dir: str = DATA) -> pd.DataFrame:
    """Bars indexed by bar-open UTC time. Columns: open high low close volume quote_volume trades taker_buy_volume
    taker_buy_quote filled funding (sum of funding rates whose event time falls in the bar; 0 otherwise)
    [+ oi oi_value top_acc_ls top_pos_ls glob_acc_ls taker_ls, value known at the bar CLOSE, NaN before 2021-12]."""
    df = pd.read_csv(os.path.join(data_dir, f"{asset}_1h.csv.gz"))
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.set_index("ts").sort_index()
    f = pd.read_csv(os.path.join(data_dir, f"{asset}_funding.csv.gz"))
    f["ts"] = pd.to_datetime(f["ts"], utc=True)
    fr = f.groupby(f["ts"].dt.floor("h"))["rate"].sum()
    df["funding"] = fr.reindex(df.index).fillna(0.0)
    if metrics:
        p = os.path.join(data_dir, f"{asset}_metrics_1h.csv.gz")
        if os.path.exists(p):
            m = pd.read_csv(p)
            m["ts"] = pd.to_datetime(m["ts"], utc=True)
            df = df.join(m.set_index("ts"), how="left")
    if tf == "1h":
        return df
    return resample(df, tf)


def resample(df: pd.DataFrame, tf: str = "4h") -> pd.DataFrame:
    """Aggregate 1h bars into tf bars (UTC-aligned, label = bar open). Incomplete last bar is dropped."""
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
           "quote_volume": "sum", "trades": "sum", "taker_buy_volume": "sum", "taker_buy_quote": "sum",
           "filled": "max", "funding": "sum"}
    for c in ("oi", "oi_value", "top_acc_ls", "top_pos_ls", "glob_acc_ls", "taker_ls"):
        if c in df.columns:
            agg[c] = "last"
    agg = {k: v for k, v in agg.items() if k in df.columns}
    g = df.resample(tf, label="left", closed="left")
    out = g.agg(agg)
    n = g["close"].count()
    full = int(pd.Timedelta(tf) / pd.Timedelta("1h"))
    out = out[n > 0]
    if len(out) and n.iloc[-1] < full:
        out = out.iloc[:-1]
    for c in ("volume", "quote_volume", "taker_buy_volume", "taker_buy_quote"):
        if c in out.columns:  # min_count semantics: all-NaN (OKX-filled) stays NaN
            out.loc[g[c].count().reindex(out.index) == 0, c] = np.nan
    return out


def load_all(tf: str = "1h", assets=ASSETS, metrics: bool = True) -> dict:
    return {a: load_bars(a, tf, metrics) for a in assets}


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Wilder ATR, known at bar close."""
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


# ----------------------------------------------------------------------------------------------- config
@dataclass
class Exits:
    """Exit spec. Distances: stop_pct (fraction of entry) or stop_atr (x ATR at signal bar); a per-entry 'stop'
    level in the signal overrides both. tp = [(distance, fraction), ...] in tp_unit 'pct' | 'R' | 'atr'.
    Fractions are of the INITIAL size; any remainder (sum<1) is a runner closed by stop/trail/time/signal."""
    stop_pct: float | None = None
    stop_atr: float | None = None
    tp: list = field(default_factory=list)
    tp_unit: str = "pct"
    be_after_tp1: bool = False
    be_offset: float = 0.0          # BE stop = entry*(1 + side*be_offset), e.g. 0.001 to cover costs
    be_same_bar: bool = True        # conservative: BE can be hit in the same bar as TP1
    trail_atr: float | None = None  # trail distance in ATR (current ATR at bar close)
    trail_pct: float | None = None  # trail distance as fraction of the extreme
    trail_after_tp1: bool = False   # start trailing only once TP1 is filled
    time_bars: int | None = None    # exit at open of bar entry+time_bars
    reverse_exit: bool = True       # opposite signal at close -> exit next open
    reverse_entry: bool = True      # ... and open the opposite position at that same open
    atr_len: int = 14


@dataclass
class Sizing:
    """mode 'fixed': notional = leverage x allocation.  mode 'risk': notional = risk_pct x equity / stop_distance%,
    capped at leverage x allocation. allocation 'equal' = equity/len(assets) per asset, 'shared' = whole equity.
    leverage is also the exchange (isolated) leverage used for the liquidation price."""
    mode: str = "fixed"
    leverage: float = 3.0
    risk_pct: float = 0.01
    allocation: str = "equal"
    max_exposure: float | None = None   # cap on sum(open notionals)/equity; new trades are scaled down to fit
    max_positions: int | None = None
    min_fill: float = 0.2               # skip a capped trade if < min_fill of its intended size remains
    compounding: bool = True            # False: size off initial capital
    capital: float = 10_000.0


@dataclass
class Costs:
    fee: float = 0.0005        # taker per side
    slip: float = 0.0002       # entries / TP / time / signal exits
    slip_stop: float = 0.0005  # stop, trailing, BE and liquidation exits
    funding: bool = True
    mmr: float = 0.005
    liquidation: bool = True


STOP_REASONS = {"stop", "be", "trail", "liq"}


# ----------------------------------------------------------------------------------------------- phase 1
def _signal_frame(sig, index) -> pd.DataFrame:
    if isinstance(sig, pd.Series):
        sig = sig.to_frame("side")
    s = sig.reindex(index)
    out = pd.DataFrame(index=index)
    out["side"] = s["side"].fillna(0).astype(int).clip(-1, 1) if "side" in s else 0
    for c in ("stop", "stop_pct", "max_bars"):
        out[c] = s[c].astype(float) if c in s else np.nan
    out["exit"] = s["exit"].fillna(False).astype(bool) if "exit" in s else False
    return out


def _simulate_asset(asset, bars, sig, ex: Exits, i0: int, i1: int):
    """Unit-size path simulation for one asset. Returns list of trade dicts with exit legs."""
    O = bars["open"].to_numpy(float); H = bars["high"].to_numpy(float)
    L = bars["low"].to_numpy(float); C = bars["close"].to_numpy(float)
    A = (bars["atr"] if "atr" in bars else atr(bars, ex.atr_len)).to_numpy(float)
    side = sig["side"].to_numpy(); stopv = sig["stop"].to_numpy(); stoppct = sig["stop_pct"].to_numpy()
    maxb = sig["max_bars"].to_numpy(); exitf = sig["exit"].to_numpy()
    n = len(O)
    ol, os_ = O.tolist(), (-O).tolist()
    hl, hs = H.tolist(), (-L).tolist()
    ll, ls = L.tolist(), (-H).tolist()
    Al = A.tolist()
    ex_long = (exitf | ((side == -1) & ex.reverse_exit)).tolist()
    ex_short = (exitf | ((side == 1) & ex.reverse_exit)).tolist()
    cand = np.flatnonzero(side[i0:i1] != 0) + i0
    tps = ex.tp
    trades, skipped = [], 0
    nxt = i0  # earliest signal index allowed
    ci = 0
    while ci < len(cand):
        i = int(cand[ci]); ci += 1
        if i < nxt:
            continue
        e = i + 1
        if e >= min(n, i1):
            break
        sd = int(side[i])
        Ep = O[e]
        # stop distance (positive price units)
        if not math.isnan(stopv[i]):
            dstop = sd * (Ep - stopv[i])
            if dstop <= 0:
                skipped += 1
                continue
        elif not math.isnan(stoppct[i]):
            dstop = stoppct[i] * Ep
        elif ex.stop_pct is not None:
            dstop = ex.stop_pct * Ep
        elif ex.stop_atr is not None and not math.isnan(A[i]):
            dstop = ex.stop_atr * A[i]
        elif ex.stop_atr is not None:
            skipped += 1
            continue
        else:
            dstop = math.inf
        unit = {"pct": Ep, "R": dstop, "atr": A[i]}[ex.tp_unit] if tps else 0.0
        if tps and (math.isnan(unit) or math.isinf(unit)):
            skipped += 1
            continue
        mb = int(maxb[i]) if not math.isnan(maxb[i]) else (ex.time_bars or 10**9)
        # long-space arrays
        if sd == 1:
            o_, h_, l_, xf = ol, hl, ll, ex_long
        else:
            o_, h_, l_, xf = os_, hs, ls, ex_short
        E = o_[e]
        aE = abs(E)
        stop = E - dstop
        tpl = [E + d * unit for d, _ in tps]
        fr = [f for _, f in tps]
        ntp = len(tpl)
        rem = 1.0
        k = 0
        hh = E
        trail_on = not ex.trail_after_tp1
        reason = "stop"
        legs = []
        b = e
        last = n - 1
        while True:
            o = o_[b]; h = h_[b]; lo = l_[b]
            if b > e:
                if b - e >= mb:
                    legs.append((b, o, rem, "time")); break
                if xf[b - 1]:
                    legs.append((b, o, rem, "signal")); break
                if o <= stop:
                    legs.append((b, o, rem, reason)); break
            if lo <= stop:
                legs.append((b, stop, rem, reason)); break
            moved = False
            while k < ntp and h >= tpl[k]:
                q = rem if (k == ntp - 1 and sum(fr) >= 0.9999) else min(fr[k], rem)
                legs.append((b, max(tpl[k], o), q, f"tp{k + 1}"))
                rem -= q
                k += 1
                if k == 1:
                    if ex.be_after_tp1:
                        be = E + ex.be_offset * aE
                        if be > stop:
                            stop = be; reason = "be"; moved = True
                    if ex.trail_after_tp1:
                        trail_on = True
            if rem <= 1e-9:
                break
            if moved and ex.be_same_bar and lo <= stop:
                legs.append((b, stop, rem, "be")); break
            if h > hh:
                hh = h
            if trail_on:
                if ex.trail_atr is not None:
                    t = hh - ex.trail_atr * Al[b]
                elif ex.trail_pct is not None:
                    t = hh - ex.trail_pct * abs(hh)
                else:
                    t = -math.inf
                if t > stop:
                    stop = t; reason = "trail"
            if b >= last or b >= i1 - 1:
                legs.append((b, C[b] if sd == 1 else -C[b], rem, "end")); break
            b += 1
        # back to real prices
        legs = [(lb, lp * sd, lq, lr) for lb, lp, lq, lr in legs]
        xb = legs[-1][0]
        trades.append({"asset": asset, "side": sd, "sig_i": i, "e": e, "entry_raw": Ep, "dstop": dstop,
                       "legs": legs, "x": xb})
        last_reason = legs[-1][3]
        if last_reason == "signal" and ex.reverse_entry and side[xb - 1] == -sd:
            nxt = xb - 1
        else:
            nxt = xb
        # rewind candidate pointer
        ci = int(np.searchsorted(cand, nxt))
    return trades, skipped


# ----------------------------------------------------------------------------------------------- phase 2
@dataclass
class Result:
    trades: pd.DataFrame       # one row per trade (all legs aggregated)
    legs: pd.DataFrame         # one row per partial fill
    equity: pd.Series          # bar-close MTM equity on the union index of the window
    daily: pd.Series           # daily (UTC) last MTM equity
    exposure: pd.Series        # gross open notional / equity at bar close
    capital: float
    start: pd.Timestamp
    end: pd.Timestamp
    info: dict


def _ts(x) -> pd.Timestamp:
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def _apply_liquidation(legs, e, sd, liq_px, L_, H_):
    """Truncate a leg list at the first bar where the adverse extreme reaches liq_px."""
    xb = legs[-1][0]
    path = L_[e:xb + 1] if sd == 1 else H_[e:xb + 1]
    hit = np.flatnonzero(path <= liq_px) if sd == 1 else np.flatnonzero(path >= liq_px)
    if not len(hit):
        return legs
    lb = e + int(hit[0])
    new = []
    for lg in legs:
        if lg[0] < lb:
            new.append(lg)
        elif lg[0] == lb and lg[3] in STOP_REASONS and sd * (lg[1] - liq_px) > 0:
            new.append(lg)  # own stop (not gapped beyond liq) fills before the liquidation price
        else:
            break
    done = sum(lg[2] for lg in new)
    if done < 1 - 1e-9:
        new.append((lb, liq_px, 1.0 - done, "liq"))
    return new


def backtest(bars: dict, signals: dict, exits: Exits = None, sizing: Sizing = None, costs: Costs = None,
             start=None, end=None) -> Result:
    """Run the portfolio backtest. bars/signals: {asset: DataFrame}. Entries only for signals in [start, end);
    positions still open at the last bar before `end` are closed at its close (reason 'end')."""
    ex = exits or Exits(); sz = sizing or Sizing(); co = costs or Costs()
    t0 = time.perf_counter()
    assets = list(bars)
    idx = bars[assets[0]].index
    for a in assets[1:]:
        idx = idx.union(bars[a].index)
    start = _ts(start) if start is not None else idx[0]
    end = _ts(end) if end is not None else idx[-1] + pd.Timedelta(seconds=1)
    gidx = idx[idx.searchsorted(start):idx.searchsorted(end)]
    raw, skipped, maps, arrays = [], {}, {}, {}
    for a in assets:
        b = bars[a]
        s = _signal_frame(signals[a], b.index)
        i0, i1 = int(b.index.searchsorted(start)), int(b.index.searchsorted(end))
        tr, sk = _simulate_asset(a, b, s, ex, i0, i1)
        raw += tr
        skipped[a] = sk
        maps[a] = gidx.searchsorted(b.index)
        arrays[a] = (b["open"].to_numpy(float), b["high"].to_numpy(float), b["low"].to_numpy(float),
                     b["close"].to_numpy(float),
                     b["funding"].fillna(0).to_numpy(float) if "funding" in b else np.zeros(len(b)))
    raw.sort(key=lambda t: (bars[t["asset"]].index[t["e"]], t["asset"]))

    cap0 = sz.capital
    realized = cap0
    pending = []   # realised cash events (time, amount) not yet booked into sizing equity
    openpos = []   # (final exit time, notional)
    rows = []
    n_assets = len(assets)
    dropped = 0
    for t in raw:
        a, sd, e = t["asset"], t["side"], t["e"]
        O_, H_, L_, C_, F_ = arrays[a]
        bidx = bars[a].index
        te = bidx[e]
        if pending:
            realized += sum(amt for tt, amt in pending if tt <= te)
            pending = [(tt, amt) for tt, amt in pending if tt > te]
        openpos = [p for p in openpos if p[0] > te]
        eq = realized if sz.compounding else cap0
        if realized <= 0:
            break
        alloc = eq / n_assets if sz.allocation == "equal" else eq
        Ef = t["entry_raw"] * (1 + sd * co.slip)
        cap_notional = sz.leverage * alloc
        if sz.mode == "risk":
            if not math.isfinite(t["dstop"]):
                raise ValueError("risk sizing needs a stop (Exits.stop_pct/stop_atr or signal 'stop')")
            stop_frac = t["dstop"] / t["entry_raw"] + co.slip + co.slip_stop + 2 * co.fee
            notional = min(sz.risk_pct * eq / stop_frac, cap_notional)
        else:
            notional = cap_notional
        intended = notional
        if sz.max_positions is not None and len(openpos) >= sz.max_positions:
            dropped += 1
            continue
        if sz.max_exposure is not None:
            notional = min(notional, max(sz.max_exposure * eq - sum(p[1] for p in openpos), 0.0))
        if notional <= 0 or notional < sz.min_fill * intended:
            dropped += 1
            continue
        qty = notional / Ef
        legs = t["legs"]
        liq_px = np.nan
        if co.liquidation:
            liq_px = t["entry_raw"] * (1 - sd * (1 / sz.leverage - co.mmr))
            legs = _apply_liquidation(legs, e, sd, liq_px, L_, H_)
        fee_in = notional * co.fee
        legout = []  # (time, bar, fill, frac, reason, gross, fee)
        for (lb, lp, lq, lr) in legs:
            q = qty * lq
            if lr == "liq":
                px, gross, fee = lp, -q * Ef / sz.leverage, 0.0   # isolated margin of the slice is lost
            else:
                px = lp * (1 - sd * (co.slip_stop if lr in STOP_REASONS else co.slip))
                gross = sd * q * (px - Ef)
                fee = q * px * co.fee
            legout.append((bidx[lb], lb, px, lq, lr, gross, fee))
        xb, xr = legs[-1][0], legs[-1][3]
        fund_bars = np.zeros(0, dtype=int); fund_amt = np.zeros(0)
        if co.funding:
            at_open = xr in ("time", "signal") or (xr in STOP_REASONS and xb > e and legs[-1][1] == O_[xb])
            bs = np.arange(e + 1, xb if at_open else xb + 1)
            if len(bs):
                held = np.ones(len(bs))
                for (lb, lp, lq, lr) in legs:
                    held[bs > lb] -= lq
                fund_amt = sd * qty * held * O_[bs] * F_[bs]
                fund_bars = bs
        fund = float(fund_amt.sum())
        fees = fee_in + sum(l[6] for l in legout)
        net = sum(l[5] - l[6] for l in legout) - fee_in - fund
        for l in legout:
            pending.append((l[0], l[5] - l[6]))
        pending.append((legout[-1][0], -fee_in - fund))
        openpos.append((legout[-1][0], notional))
        risk_usd = qty * t["dstop"] if math.isfinite(t["dstop"]) else np.nan
        rows.append({"asset": a, "side": sd, "signal_time": bidx[t["sig_i"]], "entry_time": te, "entry": Ef,
                     "stop0": t["entry_raw"] - sd * t["dstop"] if math.isfinite(t["dstop"]) else np.nan,
                     "exit_time": legout[-1][0],
                     "exit": float(np.average([l[2] for l in legout], weights=[l[3] for l in legout])),
                     "bars": xb - e, "qty": qty, "notional": notional, "lev": notional / eq,
                     "equity_at_entry": eq, "fees": fees, "funding": fund, "pnl": net, "pnl_pct": net / eq * 100,
                     "R": net / risk_usd if risk_usd > 0 else np.nan, "risk_usd": risk_usd,
                     "tp_hits": sum(1 for l in legout if l[4].startswith("tp")), "n_legs": len(legout),
                     "reason": "+".join(l[4] for l in legout), "final": legout[-1][4], "liq_px": liq_px,
                     "_legs": legout, "_e": e, "_fb": fund_bars, "_fa": fund_amt})
    equity, expo = _mtm(rows, arrays, maps, gidx, cap0, co)
    daily = equity.groupby(equity.index.floor("D")).last()
    legs_df = pd.DataFrame([{"asset": r["asset"], "entry_time": r["entry_time"], "time": l[0], "price": l[2],
                             "frac": l[3], "reason": l[4], "pnl": l[5] - l[6]} for r in rows for l in r["_legs"]])
    trades = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
    info = {"skipped_invalid_stop": skipped, "dropped_by_portfolio_caps": dropped, "candidates": len(raw),
            "runtime_s": round(time.perf_counter() - t0, 3), "exits": ex, "sizing": sz, "costs": co}
    st = gidx[0] if len(gidx) else start
    en = gidx[-1] if len(gidx) else end
    return Result(trades, legs_df, equity, daily, expo, cap0, st, en, info)


def _mtm(rows, arrays, maps, gidx, cap0, co):
    """Bar-close mark-to-market equity: cap0 + cumulative realised cash + open PnL at the close."""
    N = len(gidx)
    cash = np.zeros(N + 1)
    unreal = np.zeros(N + 1)
    gross = np.zeros(N + 1)
    for r in rows:
        C_ = arrays[r["asset"]][3]
        m = maps[r["asset"]]
        e, legs, sd, qty, Ef = r["_e"], r["_legs"], r["side"], r["qty"], r["entry"]
        xb = legs[-1][1]
        cash[m[e]] -= r["notional"] * co.fee
        if len(r["_fb"]):
            np.add.at(cash, m[r["_fb"]], -r["_fa"])
        bs = np.arange(e, xb + 1)
        held = np.ones(len(bs))
        for (tl, lb, px, lq, lr, g, fee) in legs:
            held[bs >= lb] -= lq
            cash[m[lb]] += g - fee
        held = np.clip(held, 0, None)
        np.add.at(unreal, m[bs], sd * qty * held * (C_[bs] - Ef))
        np.add.at(gross, m[bs], qty * held * C_[bs])
    eq = cap0 + np.cumsum(cash[:N]) + unreal[:N]
    equity = pd.Series(eq, index=gidx, name="equity")
    expo = pd.Series(gross[:N] / np.where(eq > 0, eq, np.nan), index=gidx, name="exposure")
    return equity, expo


# ----------------------------------------------------------------------------------------------- metrics
def _pf(p):
    w, l = p[p > 0].sum(), -p[p < 0].sum()
    return float(w / l) if l > 0 else (np.inf if w > 0 else np.nan)


def _trade_stats(t: pd.DataFrame) -> dict:
    if not len(t):
        return {"trades": 0}
    p = t["pnl"]
    return {"trades": len(t), "win_rate": round(float((p > 0).mean() * 100), 1), "pnl": round(float(p.sum()), 0),
            "avg_win": round(float(p[p > 0].mean()), 1) if (p > 0).any() else 0.0,
            "avg_loss": round(float(p[p < 0].mean()), 1) if (p < 0).any() else 0.0,
            "pf": round(_pf(p), 2), "exp_R": round(float(t["R"].mean()), 3) if t["R"].notna().any() else np.nan}


def metrics(res: Result) -> dict:
    """Headline metrics on daily MTM equity + trade statistics."""
    d, t, c0 = res.daily, res.trades, res.capital
    if not len(d):
        return {}
    final = float(d.iloc[-1])
    years = max((d.index[-1] - d.index[0]).days + 1, 1) / 365.25
    cagr = ((final / c0) ** (1 / years) - 1) * 100 if final > 0 else -100.0
    dd = float(((d / np.maximum.accumulate(np.r_[c0, d.to_numpy()])[1:]) - 1).min() * 100)
    months = years * 12
    out = {"final": round(final, 0), "ret_pct": round((final / c0 - 1) * 100, 1), "cagr": round(cagr, 1),
           "max_dd": round(dd, 1), "mar": round(cagr / abs(dd), 2) if dd < 0 else np.nan,
           "trades_per_month": round(len(t) / months, 2) if months else np.nan,
           "time_in_mkt": round(float((res.exposure.fillna(0) > 0).mean() * 100), 1),
           "fees": round(float(t["fees"].sum()), 0) if len(t) else 0, "funding": round(float(t["funding"].sum()), 0) if len(t) else 0,
           "liquidations": int(t["reason"].str.contains("liq").sum()) if len(t) else 0}
    out.update(_trade_stats(t))
    return out


def breakdown(res: Result) -> dict:
    """Per-year (return from daily equity + trade stats), per-asset and long/short tables."""
    d, t = res.daily, res.trades
    yrs = []
    prev = res.capital
    for y, s in d.groupby(d.index.year):
        tt = t[t["entry_time"].dt.year == y] if len(t) else t
        dd = float((s / np.maximum.accumulate(np.r_[prev, s.to_numpy()])[1:] - 1).min() * 100)
        yrs.append({"year": y, "ret_pct": round((s.iloc[-1] / prev - 1) * 100, 1), "max_dd": round(dd, 1),
                    **_trade_stats(tt)})
        prev = s.iloc[-1]
    by_asset = pd.DataFrame([{"asset": a, **_trade_stats(g)} for a, g in t.groupby("asset")]) if len(t) else pd.DataFrame()
    by_side = pd.DataFrame([{"side": "long" if s == 1 else "short", **_trade_stats(g)} for s, g in t.groupby("side")]) if len(t) else pd.DataFrame()
    by_exit = t.groupby("final")["pnl"].agg(["count", "sum"]).round(0) if len(t) else pd.DataFrame()
    return {"years": pd.DataFrame(yrs), "assets": by_asset, "sides": by_side, "exits": by_exit}


def report(res: Result, title: str = "") -> str:
    m = metrics(res)
    b = breakdown(res)
    lines = [f"== {title} {res.start:%Y-%m-%d} -> {res.end:%Y-%m-%d}  ({res.info['runtime_s']}s)",
             "  " + "  ".join(f"{k}={v}" for k, v in m.items())]
    for k in ("years", "assets", "sides"):
        if len(b[k]):
            lines.append(b[k].to_string(index=False))
    if len(b["exits"]):
        lines.append("exits: " + ", ".join(f"{i}={int(r['count'])}/{r['sum']:+.0f}$" for i, r in b["exits"].iterrows()))
    return "\n".join(lines)


# ----------------------------------------------------------------------------------------------- helpers
def run_strategy(signal_fn: Callable, params: dict, exits: Exits, sizing: Sizing = None, costs: Costs = None,
                 bars: dict = None, tf: str = "1h", start="2021-01-01", end=None) -> Result:
    """signal_fn(bars_df, **params) -> signal frame; bars default: load_all(tf). Warm-up uses data before start."""
    bars = bars or load_all(tf)
    sig = {a: signal_fn(b, **params) for a, b in bars.items()}
    return backtest(bars, sig, exits, sizing, costs, start, end)


def split(signal_fn, params, exits, sizing=None, costs=None, bars=None, tf="1h",
          start="2021-01-01", cut=IS_END, end=None) -> dict:
    """In-sample [start, cut) and out-of-sample [cut, end) as two independent runs with fresh capital,
    plus the full run. Returns {'IS': Result, 'OOS': Result, 'ALL': Result}."""
    bars = bars or load_all(tf)
    sig = {a: signal_fn(b, **params) for a, b in bars.items()}
    return {"IS": backtest(bars, sig, exits, sizing, costs, start, cut),
            "OOS": backtest(bars, sig, exits, sizing, costs, cut, end),
            "ALL": backtest(bars, sig, exits, sizing, costs, start, end)}


def placebo(res: Result, bars: dict, exits: Exits, sizing: Sizing = None, costs: Costs = None, n: int = 100,
            seed: int = 0, match_holding: bool | None = None, keys=("ret_pct", "max_dd", "pf", "mar", "exp_R")) -> dict:
    """Random-entry placebo: per asset the same number of entries (spread uniformly over the window), the same
    long/short mix, per-trade stop distances resampled from the real trades (stop_pct) and the same Exits.
    match_holding (default: True when the exits have no TP and no stop, i.e. signal-driven) also imposes holding
    times resampled from the real trades. Returns {'runs': DataFrame, 'pctl': {metric: percentile of the real
    result within the placebo distribution}}."""
    rng = np.random.default_rng(seed)
    t = res.trades
    real = metrics(res)
    if not len(t):
        return {"runs": pd.DataFrame(), "pctl": {}}
    ex = replace(exits, reverse_exit=False, reverse_entry=False)
    if match_holding is None:
        match_holding = exits.reverse_exit and not exits.tp and exits.trail_atr is None and exits.trail_pct is None
    stop_pct = ((t["entry"] - t["stop0"]).abs() / t["entry"]).dropna().to_numpy()
    hold = np.maximum(t["bars"].to_numpy(), 1)
    long_share = float((t["side"] == 1).mean())
    runs = []
    for k in range(n):
        sig = {}
        for a, b in bars.items():
            na = int((t["asset"] == a).sum())
            i0, i1 = b.index.searchsorted(res.start), b.index.searchsorted(res.end)
            fr = pd.DataFrame(index=b.index, data={"side": 0, "stop_pct": np.nan, "max_bars": np.nan})
            if na and i1 - i0 > 2:
                busy = min(float(np.mean(hold)) * na / (i1 - i0), 0.9)
                m = min(int(round(na / (1 - busy))), i1 - i0 - 1)
                pos = np.sort(rng.choice(np.arange(i0, i1 - 1), size=m, replace=False))
                fr.iloc[pos, 0] = np.where(rng.random(m) < long_share, 1, -1)
                if len(stop_pct):
                    fr.iloc[pos, 1] = rng.choice(stop_pct, m)
                if match_holding:
                    fr.iloc[pos, 2] = rng.choice(hold, m)
            sig[a] = fr
        r = backtest(bars, sig, ex, sizing, costs, res.start, res.end + pd.Timedelta(hours=1))
        runs.append({**{kk: metrics(r).get(kk, np.nan) for kk in keys}, "trades": len(r.trades)})
    runs = pd.DataFrame(runs)
    pct = {kk: round(float((runs[kk] < real.get(kk, np.nan)).mean() * 100), 1) for kk in keys if kk in real}
    return {"runs": runs, "pctl": pct, "real": {kk: real.get(kk) for kk in keys}}


def neighbours(run_fn: Callable[[dict], Result], base: dict, grid: dict | None = None,
               rel=(0.8, 0.9, 1.1, 1.2), mode: str = "oat") -> pd.DataFrame:
    """Robustness grid around chosen params. run_fn(params) -> Result. grid: {param: [values]}; if omitted,
    numeric params are scaled by `rel` (ints rounded). mode 'oat' = one-at-a-time, 'full' = cartesian product.
    Returns one row per param set with headline metrics; row 0 is the base."""
    if grid is None:
        grid = {}
        for k, v in base.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            vals = sorted({(int(round(v * r)) if isinstance(v, int) else round(v * r, 10)) for r in rel} - {v})
            grid[k] = vals
    sets = [dict(base)]
    if mode == "full":
        keys = list(grid)
        for combo in itertools.product(*[[base[k]] + list(grid[k]) for k in keys]):
            p = dict(base); p.update(zip(keys, combo))
            if p != base:
                sets.append(p)
    else:
        for k, vals in grid.items():
            for v in vals:
                p = dict(base); p[k] = v
                sets.append(p)
    out = []
    for p in sets:
        m = metrics(run_fn(p))
        out.append({**{k: p[k] for k in grid}, **{k: m.get(k) for k in
                    ("ret_pct", "cagr", "max_dd", "mar", "trades", "win_rate", "pf", "exp_R")}})
    df = pd.DataFrame(out)
    df.attrs["share_pf_gt_1"] = float((df["pf"] > 1).mean())
    return df
