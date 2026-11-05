"""Short W2 · motore di ricerca (solo lettura del repo, nessuna modifica a radar/).

Dati:
- "repo": radar.features.build_features(load_all()) — identico a radar/weekly.py (spot Binance dal 2019-09, perp/funding dal 2020,
  metrics OI/LS dal 2021-12, F&G dal 2018).
- "long": prezzi Bitstamp 2014-01 → 2017-08-16 + Binance spot 2017-08-17 → 2019-08 (data/ di questa cartella) + repo dal 2019-09;
  flusso = pf14z dove esiste, prima CVD spot z (sf14z, proxy), funding 0 prima del 2020.
Motore: copia generalizzata di radar/weekly.simulate (stessa equity giornaliera mark-to-market, stessi ordini degli eventi).
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from radar.data import load_all  # noqa: E402
from radar.features import build_features, _z  # noqa: E402
from radar import weekly as W  # noqa: E402

SLIP = 0.001
FEE_SHORT = 0.001          # richiesta: 0,1%/lato per i nuovi short
P0 = dict(sma=40, ema_t=20, ema_x=21, atr=14, macd=(8, 21, 5), stop=2.5, trail=2.5)


# ----------------------------------------------------------------------------------------------------------- dati
def load_repo() -> pd.DataFrame:
    f = build_features(load_all())
    return f[f["close"].notna()]


def load_long(repo: pd.DataFrame) -> pd.DataFrame:
    bs = pd.read_csv(HERE / "data/bitstamp_1d_2014_2017.csv", index_col=0, parse_dates=True)
    bn = pd.read_csv(HERE / "data/binance_spot_1d_2017_2019.csv", index_col=0, parse_dates=True)
    cols = ["open", "high", "low", "close"]
    pre = pd.concat([bs[cols], bn[cols]])
    d = pd.concat([pre, repo[cols][repo.index >= "2019-09-01"]])
    d = d[~d.index.duplicated(keep="last")].sort_index()
    # CVD spot z su tutta la storia Binance (2017-08 →): proxy del flusso prima di pf14z
    sp = pd.concat([bn[["volume", "taker_buy_volume"]], repo[["spot_vol"]].rename(columns={"spot_vol": "volume"})
                    .assign(taker_buy_volume=(repo["spot_delta"] + repo["spot_vol"]) / 2)[repo.index >= "2019-09-01"]])
    sp = sp[~sp.index.duplicated(keep="last")].reindex(d.index)
    delta = 2 * sp["taker_buy_volume"] - sp["volume"]
    sf = _z(delta.rolling(14).sum() / sp["volume"].rolling(14).sum(), 180)
    d["pf14z"] = repo["pf14z"].reindex(d.index).fillna(sf)
    for c in ("funding", "funding_z", "ls_z"):
        d[c] = repo[c].reindex(d.index)
    return d


# ----------------------------------------------------------------------------------------------------------- settimanale
def weekly_bars(f: pd.DataFrame, p: dict = P0) -> pd.DataFrame:
    w = f[["open", "high", "low", "close"]].resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    w["flow"] = f["pf14z"].resample("W-SUN").last()
    w["fund7"] = f["funding"].fillna(0).rolling(7).mean().resample("W-SUN").last()
    w["fz"] = f["funding_z"].resample("W-SUN").last() if "funding_z" in f else np.nan
    w["lsz"] = f["ls_z"].resample("W-SUN").last() if "ls_z" in f else np.nan
    c = w["close"]
    w["sma"] = c.rolling(p["sma"]).mean()
    w["ema20"] = c.ewm(span=p["ema_t"], adjust=False).mean()
    w["ema21"] = c.ewm(span=p["ema_x"], adjust=False).mean()
    tr = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
    w["atr"] = tr.ewm(alpha=1 / p["atr"], adjust=False).mean()
    mf, ms, mg = p["macd"]
    m = c.ewm(span=mf, adjust=False).mean() - c.ewm(span=ms, adjust=False).mean()
    w["macd"], w["sig"] = m, m.ewm(span=mg, adjust=False).mean()
    # segnali long W2 (identici a radar/weekly.py; il MACD di F1 resta 8/21/5 anche quando varia quello degli short)
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    above = (c > w["sma"]).astype(int)
    age = above.groupby((above == 0).cumsum()).cumsum()
    m5 = c.ewm(span=8, adjust=False).mean() - c.ewm(span=21, adjust=False).mean()
    s5 = m5.ewm(span=5, adjust=False).mean()
    f1 = (age < 16) | ((m5 > s5) & (m5 > 0))
    w["L"] = (up & (c > w["ema21"]) & (w["flow"] > 0) & f1).fillna(False)
    w["dist_long"] = ((w["fund7"] > W.FUND_HOT) & (w["flow"] < 0)).fillna(False)
    w["dist_short"] = ((w["fund7"] < W.FUND_COLD) & (w["flow"] > 0)).fillna(False)
    # regimi short
    w["dn_w2"] = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    w["dn"] = (c < w["sma"]) & (w["ema20"] < w["ema20"].shift(1))
    w["mbear"] = (w["macd"] < w["sig"]) & (w["macd"] < 0)
    w["crowd"] = (w["fz"] > 0) | (w["lsz"] > 0)
    return w[w.index <= f.index[-1]]


def short_rules(w: pd.DataFrame) -> dict:
    """Ingressi short settimanali delle regole preregistrate (S6 è giornaliera, vedi daily_s6)."""
    c = w["close"]
    S = {}
    S["S0"] = (w["dn_w2"] & (c < w["ema21"]) & (w["flow"] < 0))
    S["S1"] = (w["dn"] & (c < w["ema21"]))
    S["S2"] = S["S1"] & w["mbear"]
    S["S3"] = S["S2"] & (w["flow"] < 0) & w["crowd"]
    lvl = np.minimum(w["ema21"], w["sma"]) - 0.25 * w["atr"]
    S["S4"] = ((c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["high"] >= lvl) & (c < w["ema21"]) & (c < w["open"]))
    xdn = (w["macd"] < w["sig"]) & (w["macd"].shift() >= w["sig"].shift())
    S["S5"] = xdn & (w["macd"] > 0) & (c > 1.25 * w["sma"]) & (w["fz"] > 1)
    S["S7"] = S["S2"]
    return {k: v.fillna(False) for k, v in S.items()}


def daily_s6(f: pd.DataFrame, w: pd.DataFrame) -> pd.Series:
    """S6: condizioni S2 (regime + MACD) dell'ultima settimana CHIUSA; ingresso alla chiusura giornaliera < minimo 7g e < EMA21w."""
    arm = (w["dn"] & w["mbear"]).astype(float)
    # la settimana che chiude la domenica d vale dai giorni d+1 … d+7
    a = arm.reindex(f.index, method="ffill").shift(1).fillna(0).astype(bool)
    e21 = w["ema21"].reindex(f.index, method="ffill").shift(1)
    lo7 = f["low"].rolling(7).min().shift(1)
    return (a & (f["close"] < lo7) & (f["close"] < e21)).fillna(False)


# ----------------------------------------------------------------------------------------------------------- motore
def short_cfg(rule: str, p: dict = P0, size: str = "R25", fee: float = FEE_SHORT) -> dict:
    cfg = dict(rule=rule, stop=p["stop"], trail=p["trail"], exit="ema", maxw=None, size=size, fee=fee, dist=False)
    if rule == "S0":
        cfg.update(dist=True)
    if rule == "S5":
        cfg.update(stop=1.5, exit="macd_up", maxw=8)
    if rule == "S7":
        cfg.update(exit="sma")
    return cfg


def simulate(f: pd.DataFrame, w: pd.DataFrame, short_entry: pd.Series | None, scfg: dict | None, longs: bool = True,
             start: str = "2021-01-01", end: str | None = None, daily_short: pd.Series | None = None,
             w2_short_fees: bool = False, entry_override: pd.Series | None = None) -> dict:
    """Un conto, una posizione alla volta. Long = W2 (spot 1x, F1, EMA21, distribuzione, trailing). Short = regola scelta.
    w2_short_fees=True: short con commissione perp 0,05% come in radar/weekly.py (solo per replicare W2)."""
    if end:
        f = f[f.index <= pd.Timestamp(end)]
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    wset = set(w.index)
    sent = short_entry if entry_override is None else entry_override
    dsh = daily_short.to_numpy(bool) if daily_short is not None else None
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq, inmkt = [], np.full(len(idx), np.nan), np.zeros(len(idx), bool)
    sstop = scfg["stop"] if scfg else 2.5
    strail = scfg["trail"] if scfg else 2.5

    def close_all(px, i, reason):
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        cash = max(cash, 0.0)
        tr.update(exit=str(idx[i].date()), exit_px=px, reason=reason, pnl=cash / tr["eq0"] - 1, move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    def expo_short(close, atr):
        if scfg["size"] == "1x":
            return 1.0
        return min(1.0, W.R_SHORT / (W.STOP_K * atr / close))

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side and cash > 0:
                side, ref_close, ref_atr = pend[1], pend[2], pend[3]
                if side > 0:
                    lt, frate, fperp, k = 1.0, W.FEE_SPOT, 0.0, W.STOP_K
                else:
                    lt = expo_short(ref_close, ref_atr)
                    frate, fperp, k = (W.FEE_PERP if w2_short_fees else scfg["fee"]), 1.0, sstop
                px = O[i] * (1 + SLIP * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[4].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=px, expo=round(lt, 3), eq0=cash + abs(q) * px * frate, weeks=0,
                          stop0=float(ref_close - side * k * ref_atr), best=O[i], curatr=float(ref_atr),
                          liq=px * (1 + 1 / lt) if side < 0 else 0.0)
            pend = None
        if side:
            tk = W.TRAIL_K if side > 0 else strail
            tl = tr["best"] - side * tk * tr["curatr"]
            stop = max(tr["stop0"], tl) if side > 0 else min(tr["stop0"], tl)
            if side < 0 and H[i] >= tr["liq"] and tr["liq"] < stop:
                close_all(max(O[i], tr["liq"]), i, "liq")
            elif (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        inmkt[i] = bool(side)
        # decisioni
        if day.dayofweek == 6 and day in wset:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
                tr["weeks"] += 1
                d = None
                if side > 0:
                    if wk["close"] < wk["ema21"]:
                        d = "ema"
                    elif wk["dist_long"]:
                        d = "dist"
                else:
                    ex = scfg["exit"]
                    if ex == "ema" and wk["close"] > wk["ema21"]:
                        d = "ema"
                    elif ex == "sma" and wk["close"] > wk["sma"]:
                        d = "sma"
                    elif ex == "macd_up" and wk["macd"] > wk["sig"]:
                        d = "macd"
                    elif scfg["dist"] and wk["dist_short"]:
                        d = "dist"
                    elif scfg["maxw"] and tr["weeks"] >= scfg["maxw"]:
                        d = "time"
                pend = ("exit", d) if d else None
            else:
                if longs and wk["L"]:
                    pend = ("enter", 1, float(wk["close"]), float(wk["atr"]), day)
                elif sent is not None and bool(sent.get(day, False)):
                    pend = ("enter", -1, float(wk["close"]), float(wk["atr"]), day)
                elif dsh is not None and dsh[i]:
                    pend = ("enter", -1, float(C[i]), float(wk["atr"]), day)
                else:
                    pend = None
        elif dsh is not None and not side and pend is None and dsh[i]:
            wl = w[w.index < day]
            if len(wl):
                pend = ("enter", -1, float(C[i]), float(wl["atr"].iloc[-1]), day)
    if side:   # posizione aperta chiusa all'ultima chiusura (come radar/weekly.metrics)
        i = len(idx) - 1
        t = dict(tr)
        t.update(exit=None, exit_px=C[i], reason="open",
                 pnl=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1, move=(C[i] / tr["entry_px"] - 1) * side)
        trades.append(t)
    e = pd.Series(eq[t0:], idx[t0:])
    return {"trades": trades, "eq": e, "inmkt": pd.Series(inmkt[t0:], idx[t0:])}


def metrics(r: dict, side: str | None = None, cap: float = 10000.0) -> dict:
    e = r["eq"] / r["eq"].iloc[0]
    T = [t for t in r["trades"] if side is None or t["side"] == side]
    pn = np.array([t["pnl"] for t in T]) if T else np.zeros(0)
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    tot = float(e.iloc[-1] - 1)
    dd = float((e / e.cummax() - 1).min())
    cagr = (1 + tot) ** (1 / yrs) - 1 if tot > -1 else -1
    best = float(pn.max()) if len(pn) else 0.0
    return dict(final=round(cap * (1 + tot)), ret=round(tot * 100, 1), dd=round(dd * 100, 1), n=len(T),
                wr=round(float((pn > 0).mean() * 100)) if len(pn) else None,
                avg_w=round(float(pn[pn > 0].mean() * 100), 1) if (pn > 0).any() else None,
                avg_l=round(float(pn[pn <= 0].mean() * 100), 1) if (pn <= 0).any() else None,
                mar=round(cagr / abs(dd), 2) if dd < 0 else None, cagr=round(cagr * 100, 1),
                tim=round(float(r["inmkt"].mean() * 100)),
                sum_pnl=round(float((np.prod(1 + pn) - 1) * 100), 1) if len(pn) else 0.0,
                no_best=round(float((np.prod(1 + pn) / (1 + best) - 1) * 100), 1) if len(pn) else 0.0)
