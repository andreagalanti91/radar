"""TA settimanale/mensile · dati, indicatori e motori (solo lettura del repo; niente modifiche a radar/)."""
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
sys.path.insert(0, str(ROOT / "research/short_w2"))
from radar import weekly as W  # noqa: E402
from short_lab import load_long, load_repo  # noqa: E402

FEE_SPOT, FEE_PERP, SLIP = W.FEE_SPOT, W.FEE_PERP, W.SLIP


# ------------------------------------------------------------------------------------------------ dati
def load():
    """f = dati del tool (2019-09→, identici a radar/weekly.py); fl = storia lunga 2011-09→ con flusso proxy e volume."""
    f = load_repo()
    fl = load_long(f)
    old = pd.read_csv(HERE / "data/bitstamp_1d_2011_2013.csv", index_col=0, parse_dates=True)
    fl = pd.concat([old[["open", "high", "low", "close"]], fl]).sort_index()
    fl = fl[~fl.index.duplicated(keep="last")]
    sw = ROOT / "research/short_w2/data"
    bs = pd.read_csv(sw / "bitstamp_1d_2014_2017.csv", index_col=0, parse_dates=True)["volume"]
    bn = pd.read_csv(sw / "binance_spot_1d_2017_2019.csv", index_col=0, parse_dates=True)["volume"]
    vol = pd.concat([old["volume"], bs, bn[bn.index < "2019-09-01"], f["spot_vol"]])
    fl["volume"] = vol[~vol.index.duplicated(keep="last")].reindex(fl.index)
    return f, fl


def macd(c: pd.Series, p=(12, 26, 9)):
    m = c.ewm(span=p[0], adjust=False).mean() - c.ewm(span=p[1], adjust=False).mean()
    return m, m.ewm(span=p[2], adjust=False).mean()


def rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def indicators(fl: pd.DataFrame) -> pd.DataFrame:
    """Tabella settimanale (indice = domenica) con tutti gli indicatori, calcolati sulla storia lunga, senza futuro."""
    c = fl["close"]
    d = pd.DataFrame(index=fl.index)
    d["close"] = c
    for n in (150, 200, 250):
        d[f"sma{n}"] = c.rolling(n).mean()
        d[f"ema{n}"] = c.ewm(span=n, adjust=False).mean().where(np.arange(len(c)) >= n)
    d["sma50"] = c.rolling(50).mean()
    for k in (14, 28, 56):
        d[f"slope{k}"] = d["sma200"] / d["sma200"].shift(k) - 1
        d[f"eslope{k}"] = d["ema200"] / d["ema200"].shift(k) - 1
    d["mayer"] = c / d["sma200"]
    d["gc"] = d["sma50"] > d["sma200"]
    # mensile: ultimo mese solare chiuso (etichetta = ultimo giorno del mese → disponibile solo da quel giorno)
    mc = c.resample("ME").last()
    mc = mc[mc.index <= c.index[-1]]
    mo = pd.DataFrame(index=mc.index)
    mo["m_close"] = mc
    for n in (8, 10, 12):
        mo[f"m_sma{n}"] = mc.rolling(n).mean()
    for tag, p in (("", (12, 26, 9)), ("f", (8, 21, 5))):
        m, s = macd(mc, p)
        mo[f"m_hist{tag}"] = (m - s).where(np.arange(len(mc)) >= p[1])
    mo["m_rsi"] = rsi(mc).where(np.arange(len(mc)) >= 15)
    d = d.join(mo.reindex(d.index).ffill())
    w = d.resample("W-SUN").last()
    wc = c.resample("W-SUN").last()
    w["wclose"] = wc
    for tag, p in (("", (12, 26, 9)), ("f", (8, 21, 5))):
        m, s = macd(wc, p)
        ok = np.arange(len(wc)) >= p[1] + p[2]
        w[f"macd{tag}"], w[f"sig{tag}"] = m.where(ok), s.where(ok)
    w["sma200w"] = wc.rolling(200).mean()
    v = fl["volume"].resample("W-SUN").sum(min_count=7)
    w["vol"] = v
    for n in (10, 20, 30):
        w[f"vr{n}"] = v / v.shift(1).rolling(n).mean()
    return w[w.index <= fl.index[-1]], d, mo


# ------------------------------------------------------------------------------------------------ motore W2 con ganci
def sim_w2(f, w, start="2021-01-01", end=None, gate=None, xexit=None, capital=10000.0):
    """Copia di radar.weekly.simulate (1x) con due ganci: gate (Series bool settimanale: nuovo LONG ammesso) e
    xexit (Series bool settimanale: uscita forzata dal long, motivo 'extra'). Senza ganci = W2 identica."""
    f = f[f["close"].notna()]
    if end:
        f = f[f.index <= end]
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = FEE_PERP, 1.0
    trades, eq, pos = [], np.full(len(idx), np.nan), np.zeros(len(idx))
    G = None if gate is None else gate.reindex(w.index).fillna(True).astype(bool)
    X = None if xexit is None else xexit.reindex(w.index).fillna(False).astype(bool)

    def close_all(px, i, reason):
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1)
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = W.exposure(side, wk["close"], wk["atr"], 1.0)
                frate, fperp = (FEE_SPOT, 0.0) if side > 0 else (FEE_PERP, 1.0)
                px = O[i] * (1 + SLIP * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=round(px, 2), expo=round(lt, 3), eq0=cash + abs(q) * px * frate,
                          stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
            pend = None
        if side:
            tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
            stop = max(tr["stop0"], tl) if side > 0 else min(tr["stop0"], tl)
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        pos[i] = side
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            if side > 0 and d is None and X is not None and X.loc[day]:
                d = ("exit", "extra")
            if not side and d and d[1] == 1 and G is not None and not G.loc[day]:
                d = None
            pend = d + (wk, day) if d else None
    if side:   # posizione aperta: chiusa all'ultima chiusura (con commissione), come nelle metriche del tool
        i = len(idx) - 1
        e = eq[i] - abs(qty) * C[i] * frate
        trades.append(dict(tr, exit="open", exit_px=float(C[i]), reason="open", pnl=e / tr["eq0"] - 1))
        eq[i] = e
    return {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "pos": pd.Series(pos[t0:], idx[t0:])}


# ------------------------------------------------------------------------------------------------ motore a stato
def sim_state(fl, tgt, start="2021-01-01", end=None, capital=10000.0):
    """Regola a stato: tgt = Series (indice = giorno della decisione alla chiusura) con +1/0/−1; esecuzione all'apertura
    del giorno dopo. Long spot 1x; short perp 1x con funding reale. Nessuno stop."""
    f = fl[fl["close"].notna()]
    if end:
        f = f[f.index <= end]
    idx = f.index
    O, C = f["open"].to_numpy(float), f["close"].to_numpy(float)
    FU = f["funding"].fillna(0).to_numpy(float)
    T = tgt.reindex(idx).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, tr, pend = 1.0, 0.0, 0.0, 0, None, None
    trades, eq, pos = [], np.full(len(idx), np.nan), np.zeros(len(idx))
    for i in range(t0, len(idx)):
        if pend is not None and pend != side:
            if side:
                fr = FEE_SPOT if side > 0 else FEE_PERP
                px = O[i] * (1 - SLIP * side)
                cash += qty * px - cost - abs(qty) * px * fr
                tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), pnl=cash / tr["eq0"] - 1)
                trades.append(tr)
                qty = cost = 0.0
            side = int(pend)
            if side:
                fr = FEE_SPOT if side > 0 else FEE_PERP
                px = O[i] * (1 + SLIP * side)
                q = side * cash / px
                qty, cost = q, q * px
                e0 = cash
                cash -= abs(q) * px * fr
                tr = dict(entry=str(idx[i].date()), side="long" if side > 0 else "short", entry_px=round(px, 2), eq0=e0)
        pend = None
        if side < 0:
            cash -= qty * C[i] * FU[i]
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if eq[i] <= 0:   # short 1x liquidato (prezzo raddoppiato)
            eq[i:] = 0.0
            trades.append(dict(tr, exit=str(idx[i].date()), exit_px=C[i], pnl=-1.0))
            side = 0
            break
        pos[i] = side
        if not np.isnan(T[i]):
            pend = T[i]
    if side:
        i = len(idx) - 1
        fr = FEE_SPOT if side > 0 else FEE_PERP
        e = eq[i] - abs(qty) * C[i] * fr
        trades.append(dict(tr, exit="open", exit_px=float(C[i]), pnl=e / tr["eq0"] - 1))
        eq[i] = e
    return {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "pos": pd.Series(pos[t0:], idx[t0:])}


def bh(fl, start="2021-01-01", end=None, capital=10000.0):
    idx = fl.index[fl.index >= start]
    return sim_state(fl, pd.Series(1.0, index=fl.index), start=str(idx[0].date()), end=end, capital=capital)


# ------------------------------------------------------------------------------------------------ metriche
def met(r, a=None, b=None):
    """Metriche sull'equity giornaliera (eventuale fetta a→b della stessa corsa). MAR = rendimento totale / |DD|, come nel tool."""
    e = r["equity"].dropna()
    p = r["pos"].reindex(e.index)
    tr = r["trades"]
    if a or b:
        a_, b_ = pd.Timestamp(a or e.index[0]), pd.Timestamp(b or e.index[-1])
        base = e[e.index < a_]
        e0 = base.iloc[-1] if len(base) else None
        e = e[(e.index >= a_) & (e.index <= b_)]
        p = p.reindex(e.index)
        tr = [t for t in tr if a_ <= pd.Timestamp(t["entry"]) <= b_]
        e = e / (e0 if e0 else e.iloc[0]) * 10000.0
        start_val = 10000.0
    else:
        start_val = 10000.0
    pn = np.array([t["pnl"] for t in tr])
    ret = e.iloc[-1] / start_val - 1
    run = np.maximum.accumulate(np.r_[start_val, e.to_numpy()])[1:]
    dd = float((e.to_numpy() / run - 1).min())
    yrs = max((e.index[-1] - e.index[0]).days / 365.25, 1e-9)
    best = pn.max() if len(pn) else 0.0
    return dict(final=round(float(e.iloc[-1])), ret=round(ret * 100, 1), dd=round(dd * 100, 1), n=len(pn),
                wr=round(float((pn > 0).mean() * 100), 1) if len(pn) else np.nan,
                mar=round(ret / abs(dd), 2) if dd < 0 else np.nan,
                cagr=round(((1 + ret) ** (1 / yrs) - 1) * 100, 1) if ret > -1 else -100.0,
                tim=round(float((p != 0).mean() * 100)), worst=round(float(pn.min() * 100), 1) if len(pn) else np.nan,
                nobest=round(((1 + ret) / (1 + best) - 1) * 100, 1))


def changed(base, var):
    """Trade W2 senza corrispondenza esatta (ingresso, uscita) nella variante, e trade nuovi della variante."""
    kb = {(t["entry"], t["exit"], t["side"]) for t in base["trades"]}
    kv = {(t["entry"], t["exit"], t["side"]) for t in var["trades"]}
    return len(kb - kv), len(kv - kb)
