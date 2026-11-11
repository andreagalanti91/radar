"""Nuova strategia settimanale/mensile su BTC: mattoni (struttura S/R, canale, VWAP, bilancio dei volumi) e motore giornaliero.
Vedi PREREG.md. Nessuna dipendenza da radar/ (solo i dati)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ta_settimanale"))
FEE, SLIP, RCAP = 0.001, 0.001, 0.25
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def load() -> pd.DataFrame:
    import lib
    _, fl = lib.load()
    return fl[["open", "high", "low", "close", "volume"]].dropna(subset=["close"])


def bars(f: pd.DataFrame, rule: str = "W-SUN") -> pd.DataFrame:
    w = f.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    return w[w.index <= f.index[-1]].dropna(subset=["close"])


def vol_balance(w: pd.DataFrame, n: int) -> pd.Series:
    up = w["volume"].where(w["close"] > w["close"].shift(), 0.0).rolling(n).sum()
    dn = w["volume"].where(w["close"] <= w["close"].shift(), 0.0).rolling(n).sum()
    return up / dn.replace(0, np.nan)


def st_struct(w: pd.DataFrame, k: int = 3, vb: pd.Series | None = None):
    """S: long alla chiusura sopra l'ultimo massimo swing confermato, uscita sotto l'ultimo minimo swing confermato."""
    h, l, c = w["high"].to_numpy(), w["low"].to_numpy(), w["close"].to_numpy()
    n = len(w); res = sup = np.nan; state = 0
    st, stop = np.zeros(n), np.full(n, np.nan)
    b = vb.to_numpy() if vb is not None else None
    for t in range(n):
        j = t - k                                   # il pivot in j è confermato alla chiusura di t
        if j >= k:
            if h[j] == h[j - k:j + k + 1].max(): res = h[j]
            if l[j] == l[j - k:j + k + 1].min(): sup = l[j]
        if state and not np.isnan(sup) and c[t] < sup: state = 0
        elif not state and not np.isnan(res) and c[t] > res and (np.isnan(sup) or c[t] > sup) and (b is None or b[t] > 1): state = 1
        st[t], stop[t] = state, sup
    return pd.Series(st, w.index), pd.Series(stop, w.index)


def st_chan(w: pd.DataFrame, n_in: int = 20, n_out: int = 10, vb: pd.Series | None = None):
    c = w["close"]; hi = w["high"].rolling(n_in).max().shift(); lo = w["low"].rolling(n_out).min().shift()
    st, state = [], 0
    for t in range(len(w)):
        if state and c.iloc[t] < lo.iloc[t]: state = 0
        elif not state and c.iloc[t] > hi.iloc[t] and (vb is None or vb.iloc[t] > 1): state = 1
        st.append(state)
    return pd.Series(st, w.index, dtype=float), lo


def st_vwap(w: pd.DataFrame, n: int = 26, vb: pd.Series | None = None, vb_out: float | None = None):
    tp = (w["high"] + w["low"] + w["close"]) / 3
    vw = (tp * w["volume"]).rolling(n).sum() / w["volume"].rolling(n).sum()
    c = w["close"]; st, state = [], 0
    for t in range(len(w)):
        if state and (c.iloc[t] < vw.iloc[t] or (vb_out is not None and vb.iloc[t] < vb_out)): state = 0
        elif not state and c.iloc[t] > vw.iloc[t] and vw.iloc[t] > vw.iloc[t - 1] and (vb_out is None or vb.iloc[t] >= 1): state = 1
        st.append(state)
    return pd.Series(st, w.index, dtype=float), vw


def to_daily(f: pd.DataFrame, s: pd.Series) -> pd.Series:
    """Valore deciso alla chiusura della barra (etichetta = ultimo giorno) → valido dai giorni successivi."""
    return s.reindex(f.index).ffill()


def sim(f: pd.DataFrame, tgt: pd.Series, stop: pd.Series | None = None, start="2021-01-01", end=None, capital=10000.0, rcap=RCAP, anchor=6, trail_k=None, atr=None):
    """tgt/stop: serie giornaliere note alla chiusura del giorno; esecuzione all'apertura del giorno dopo."""
    f = f.loc[:end] if end else f
    idx = f.index; O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    T = tgt.reindex(idx).fillna(0).to_numpy(); S = (stop.reindex(idx).to_numpy() if stop is not None else np.full(len(idx), np.nan))
    t0 = idx.searchsorted(pd.Timestamp(start)); cash, qty, expo, cur_stop, blocked = 1.0, 0.0, 0.0, np.nan, False
    eq = np.full(len(idx), np.nan); trades = []; tr = None
    A = atr.reindex(idx).ffill().to_numpy() if atr is not None else None; best = np.nan; relvl = np.nan
    def trade_to(i, px, want):                      # porta l'esposizione a `want` (frazione dell'equity) al prezzo px
        nonlocal cash, qty, expo, tr
        e = cash + qty * px; dq = want * e / px - qty
        if abs(dq) * px < 1e-9 * e: return
        cash -= dq * px + abs(dq) * px * (FEE + SLIP); qty += dq; expo = want
        if want > 0 and tr is None: tr = {"entry": str(idx[i].date()), "entry_px": round(px, 2), "eq0": e}
        if want == 0 and tr is not None:
            tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), pnl=(cash / tr["eq0"] - 1)); trades.append(tr); tr = None
    for i in range(max(t0, 1), len(idx)):
        want = T[i - 1]; s = S[i - 1]
        if want == 0: blocked = False
        elif blocked and idx[i - 1].dayofweek == anchor and C[i - 1] > (relvl if not np.isnan(relvl) else (s if not np.isnan(s) else np.inf)): blocked = False; relvl = np.nan   # rientro: chiusura sopra lo stop (o nuovo massimo dopo un trailing)
        if blocked: want = 0.0
        if want > 0 and expo == 0:                  # ingresso: tetto di rischio sulla distanza dello stop
            d = (O[i] - s) / O[i] if not np.isnan(s) and s < O[i] else np.nan
            cap = min(1.0, rcap / d) if rcap and not np.isnan(d) and d > 0 else 1.0
            trade_to(i, O[i], want * cap); cur_stop = s; cap_now = cap; best = O[i]
        elif expo > 0:
            if want == 0: trade_to(i, O[i], 0.0); cur_stop = np.nan
            else:
                if not np.isnan(s): cur_stop = s if np.isnan(cur_stop) else max(cur_stop, s)
                if abs(want * cap_now - expo) > 0.05: trade_to(i, O[i], want * cap_now)
        hit = None
        if expo > 0 and trail_k and A is not None and not np.isnan(A[i - 1]):
            tl = best - trail_k * A[i - 1]
            if L[i] <= tl and (np.isnan(cur_stop) or tl >= cur_stop): hit = ("trail", tl)
        if expo > 0 and hit is None and not np.isnan(cur_stop) and L[i] <= cur_stop: hit = ("stop", cur_stop)
        if hit:
            trade_to(i, min(O[i], hit[1]), 0.0); cur_stop = np.nan; blocked = True
            relvl = best if hit[0] == "trail" else np.nan     # dopo un trailing si rientra solo su un nuovo massimo di chiusura
        elif expo > 0: best = max(best, C[i])
        eq[i] = cash + qty * C[i]
    e = pd.Series(eq[t0:], idx[t0:]).ffill().fillna(1.0) * capital
    if tr is not None: trades.append(dict(tr, exit=None, exit_px=None, pnl=(eq[-1] / tr["eq0"] - 1), open=True))
    return {"equity": e, "trades": trades}


def met(r: dict) -> dict:
    e = r["equity"]; yrs = (e.index[-1] - e.index[0]).days / 365.25; ret = e.iloc[-1] / e.iloc[0] - 1
    dd = float((e / e.cummax() - 1).min()); cagr = (1 + ret) ** (1 / yrs) - 1 if ret > -1 else -1
    t = r["trades"]; w = [x for x in t if x["pnl"] > 0]
    return {"finale": round(float(e.iloc[-1])), "rend_%": round(ret * 100, 1), "cagr_%": round(cagr * 100, 1), "dd_%": round(dd * 100, 1),
            "mar": round(cagr / abs(dd), 2) if dd else np.nan, "trade": len(t), "wr_%": round(100 * len(w) / len(t)) if t else None,
            "peggiore_%": round(100 * min((x["pnl"] for x in t), default=0), 1)}


def atr_w(f: pd.DataFrame, rule: str = "W-SUN", n: int = 14) -> pd.Series:
    w = bars(f, rule); c = w["close"]
    tr = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
    return to_daily(f, tr.ewm(alpha=1 / n, adjust=False).mean())


def variants(f: pd.DataFrame, rule: str = "W-SUN", k=3, n_in=20, n_out=10, n_vw=26, n_vb=13) -> dict:
    """Le 8 varianti del PREREG: {nome: (tgt giornaliero, stop giornaliero)}."""
    w = bars(f, rule); vb = vol_balance(w, n_vb)
    s1, sup = st_struct(w, k); s2, _ = st_struct(w, k, vb)
    d1, lo = st_chan(w, n_in, n_out); d2, _ = st_chan(w, n_in, n_out, vb)
    v1, vw = st_vwap(w, n_vw); v2, _ = st_vwap(w, n_vw, vb, 0.8)
    vote = (s1 + d1 + v1) / 3
    m = bars(f, "ME"); mvb = vol_balance(m, 6); m8, mvw = st_vwap(m, 10, mvb, 1.0)
    D = lambda s: to_daily(f, s)
    return {"N1 struttura S/R": (D(s1), D(sup)), "N2 struttura + volumi": (D(s2), D(sup)), "N3 canale 20/10": (D(d1), D(lo)),
            "N4 canale + volumi": (D(d2), D(lo)), "N5 VWAP 26 sett.": (D(v1), D(vw)), "N6 VWAP + bilancio volumi": (D(v2), D(vw)),
            "N7 voto S+D+V": (D(vote), D(lo)), "N8 mensile VWAP 10m + volumi": (D(m8), D(mvw))}


def bh(f, start, end=None, capital=10000.0):
    c = f["close"].loc[start:end]; e = c / c.iloc[0] * capital
    return {"equity": e, "trades": []}
