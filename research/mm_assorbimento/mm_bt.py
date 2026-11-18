"""Motore e regole dello studio (PREREG.md sezioni 2–5): A1, A2, B1, B2, C1, C2, controlli K0/K1.

Una posizione alla volta, 1x, decisione alla chiusura dell'ora t, ingresso all'apertura di t+1, costi 0,08% + 0,05% per lato,
funding 8h reale, stop prima del target nella stessa ora, tempo massimo 48 ore.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

FEE, SLIP = 0.0008, 0.0005
IS0, OOS0 = pd.Timestamp("2022-02-01"), pd.Timestamp("2024-01-01")
K0_START = pd.Timestamp("2021-01-23")
WMIN, WCAP = 0.010, 0.035


@dataclass(frozen=True)
class Cfg:
    name: str
    kind: str                      # "A1h", "A4h", "B", "K1"
    vp: float = 80; rp: float = 30; th: float = 0.10; oi: bool = True      # assorbimento (famiglia A)
    win: int = 24                  # finestra di attivazione del setup A (ore)
    N: int = 24; k: float = 1.0; cap: float | None = WCAP                 # compressione (famiglia B)
    absf: bool = False             # filtro assorbimento (A1 principale) nel box
    mapthr: float | None = None    # filtro mappa: long se I ≥ thr, short se I ≤ −thr
    w3: bool = False               # famiglia C: verso del regime W3 e solo a W3 flat
    tmode: str = "liq"             # "liq" = fascia densa fra 1 e 3 W, altrimenti 2W; "2W" = sempre 2W
    tmax: int = 48
    start: pd.Timestamp = IS0


class Data:
    def __init__(self, d: dict):
        H = d["H"]
        self.idx = H.index
        self.n = len(H)
        self.O, self.Hh, self.L, self.C = (H[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        self.FR = d["FR"].reindex(H.index).fillna(0).to_numpy(float)
        self.atr = H["atr_d"].to_numpy(float)
        self.H = H
        self.B4 = d["B4"]
        self.I = d["I"].reindex(H.index).to_numpy(float)
        self.up = d["up"].reindex(H.index)
        self.dn = d["dn"].reindex(H.index)
        day = H.index.normalize()
        self.flat = d["flat_day"].reindex(day).fillna(False).to_numpy(bool)
        reg = d["reg_day"].reindex(day).fillna("neutro").to_numpy()
        self.reg = np.where(reg == "long", 1, np.where(reg == "short", -1, 0))
        self.hi12 = H["high"].rolling(12).max().to_numpy(float)
        self.lo12 = H["low"].rolling(12).min().to_numpy(float)
        self._box = {}
        self._abs = {}
        a = self.abs1h(80, 30, 0.10, True)                      # A1 principale per il filtro di B
        self.cum_L = np.concatenate([[0], np.cumsum(a == 1)])
        self.cum_S = np.concatenate([[0], np.cumsum(a == -1)])

    def _absorb(self, X: pd.DataFrame, vp, rp, th, oi) -> np.ndarray:
        D = X["D"].to_numpy(float)
        sg = np.sign(D)
        ok = ((X["vol_pct"].to_numpy(float) >= vp) & (X["rng_pct"].to_numpy(float) <= rp) & (np.abs(D) >= th)
              & (np.sign(X["dS"].to_numpy(float)) == sg) & (np.sign(X["dP"].to_numpy(float)) == sg))
        if oi:
            ok &= X["dOI"].to_numpy(float) > 0
        ok &= ~np.isnan(D)
        return np.where(ok, -sg, 0).astype(int)                 # verso del setup = opposto agli aggressori assorbiti

    def abs1h(self, vp, rp, th, oi) -> np.ndarray:
        key = ("1h", vp, rp, th, oi)
        if key not in self._abs:
            self._abs[key] = self._absorb(self.H, vp, rp, th, oi)
        return self._abs[key]

    def abs4h(self, vp, rp, th, oi):
        key = ("4h", vp, rp, th, oi)
        if key not in self._abs:
            B = self.B4
            s = self._absorb(B, vp, rp, th, oi)
            pos = self.idx.get_indexer(B.index)
            dr = np.zeros(self.n, int); zh = np.full(self.n, np.nan); zl = np.full(self.n, np.nan)
            m = pos >= 0
            dr[pos[m]] = s[m]; zh[pos[m]] = B["zhi"].to_numpy(float)[m]; zl[pos[m]] = B["zlo"].to_numpy(float)[m]
            self._abs[key] = (dr, zh, zl)
        return self._abs[key]

    def box(self, N):
        if N not in self._box:
            self._box[N] = (pd.Series(self.Hh).rolling(N).max().shift(1).to_numpy(float),
                            pd.Series(self.L).rolling(N).min().shift(1).to_numpy(float))
        return self._box[N]


@dataclass
class Result:
    cfg: Cfg
    trades: pd.DataFrame
    eq_h: np.ndarray = field(repr=False)


def target(dt: Data, T: int, side: int, ref: float, W: float, tmode: str) -> tuple[float, str]:
    if tmode == "liq":
        cl = dt.up.iloc[T] if side > 0 else dt.dn.iloc[T]
        if isinstance(cl, list):
            for p in cl:                                        # ordinate dalla più vicina nel verso del trade
                dist = (p - ref) * side
                if dist < W:
                    continue
                if dist <= 3 * W:
                    return p, "fascia"
                break
    return ref + side * 2 * W, "2W"


def run(dt: Data, c: Cfg, end: int | None = None) -> Result:
    n = dt.n if end is None else end
    O, Hh, L, C, FR = dt.O, dt.Hh, dt.L, dt.C, dt.FR
    t_start = dt.idx.searchsorted(c.start)
    if c.kind == "A1h":
        adir = dt.abs1h(c.vp, c.rp, c.th, c.oi); zh, zl = dt.hi12, dt.lo12
    elif c.kind == "A4h":
        adir, zh, zl = dt.abs4h(c.vp, c.rp, c.th, c.oi)
    else:
        bh, bl = dt.box(c.N)
    eq = 1.0
    eq_h = np.full(n, np.nan)
    trades = []
    pos = None
    setup = None                    # (dir, lo, hi, t0)
    last_entry = -10 ** 9
    t = t_start
    while t < n:
        if pos is not None:
            side, T, ef, stop, tgt = pos["side"], pos["T"], pos["ef"], pos["stop"], pos["tgt"]
            px, why, intrabar = None, None, False
            if t >= T + c.tmax:
                px, why = O[t], "tempo"
            elif c.w3 and not dt.flat[t]:
                px, why = O[t], "w3"
            elif (side > 0 and L[t] <= stop) or (side < 0 and Hh[t] >= stop):
                px = min(O[t], stop) if side > 0 else max(O[t], stop); why, intrabar = "stop", True
            elif (side > 0 and Hh[t] >= tgt) or (side < 0 and L[t] <= tgt):
                px = max(O[t], tgt) if side > 0 else min(O[t], tgt); why, intrabar = "target", True
            elif t == n - 1:
                px, why, intrabar = C[t], "fine", True
            if px is None:
                if t > T:
                    pos["fund"] += FR[t] * O[t] / ef
                eq_h[t] = pos["e0"] * (1 + side * (C[t] / ef - 1) - FEE - side * pos["fund"])
                t += 1
                continue
            if intrabar and t > T:
                pos["fund"] += FR[t] * O[t] / ef
            xf = px * (1 - side * SLIP)
            r = side * (xf / ef - 1) - FEE - FEE * xf / ef - side * pos["fund"]
            eq = pos["e0"] * (1 + r)
            trades.append(dict(signal=dt.idx[T - 1], entry=dt.idx[T], exit=dt.idx[t], side=side, ef=ef, xf=xf,
                               stop=stop, tgt=tgt, ttype=pos["ttype"], W=pos["W"], hours=t - T, reason=why, r=r))
            eq_h[t] = eq
            pos, setup = None, None
            t += 1
            continue
        eq_h[t] = eq
        sig = None
        if c.kind in ("A1h", "A4h"):
            if setup is not None and t > setup[3]:
                d0, lo, hi, t0 = setup
                if t > t0 + c.win:
                    setup = None
                elif (d0 < 0 and C[t] < lo) or (d0 > 0 and C[t] > hi):
                    sig, setup = (d0, lo, hi), None
                elif (d0 < 0 and C[t] > hi) or (d0 > 0 and C[t] < lo):
                    setup = None
            if sig is None and adir[t] != 0 and not np.isnan(zh[t]):
                setup = (int(adir[t]), zl[t], zh[t], t)
        else:
            hi, lo = bh[t], bl[t]
            if not np.isnan(hi) and t - c.N > last_entry:
                d0 = 1 if C[t] > hi else -1 if C[t] < lo else 0
                if d0:
                    W = hi - lo
                    ok = W / C[t] >= WMIN
                    if ok and c.kind == "B":
                        ok = W <= c.k * dt.atr[t] and W / C[t] <= c.cap
                    if ok and c.absf:
                        cum = dt.cum_L if d0 > 0 else dt.cum_S
                        ok = cum[t] - cum[t - c.N] > 0          # assorbimento nel box [t−N, t−1]
                    if ok:
                        sig = (d0, lo, hi)
        if sig is not None and t + 1 < n:
            d0, lo, hi = sig
            T = t + 1
            W = hi - lo
            ok = W / C[t] >= WMIN
            if ok and c.mapthr is not None:
                I = dt.I[T]
                ok = not np.isnan(I) and (I >= c.mapthr if d0 > 0 else I <= -c.mapthr)
            if ok and c.w3:
                ok = bool(dt.flat[T]) and dt.reg[T] == d0
            ref = O[T]
            stop = lo if d0 > 0 else hi
            if ok and (ref - stop) * d0 <= 0:
                ok = False                                      # apertura già oltre lo stop
            if ok:
                tgt, tt = target(dt, T, d0, ref, W, c.tmode)
                ef = ref * (1 + d0 * SLIP)
                pos = dict(side=d0, T=T, ef=ef, stop=stop, tgt=tgt, ttype=tt, W=W / ref, e0=eq, fund=0.0)
                last_entry = T
        t += 1
    tr = pd.DataFrame(trades)
    return Result(c, tr, eq_h)


def daily_equity(dt: Data, res: Result, capital=10000.0) -> pd.Series:
    """Equity giornaliera (chiusura UTC) da 10.000 $ al 01/01/2021; liquidità prima dell'avvio della regola."""
    e = pd.Series(res.eq_h, dt.idx).ffill().fillna(1.0)
    d = e.groupby(e.index.normalize()).last()
    return d * capital


def stats(tr: pd.DataFrame, eq: pd.Series | None = None) -> dict:
    if tr is None or len(tr) == 0:
        return dict(n=0, wr=np.nan, pf=np.nan, mean=np.nan, cap=10000.0, ret=0.0, dd=0.0, mar=np.nan)
    r = tr["r"].to_numpy()
    g, l_ = r[r > 0].sum(), -r[r < 0].sum()
    out = dict(n=len(r), wr=(r > 0).mean() * 100, pf=g / l_ if l_ > 0 else np.inf, mean=r.mean() * 100,
               nl=int((tr["side"] > 0).sum()), ns=int((tr["side"] < 0).sum()))
    if eq is not None:
        e = eq / eq.iloc[0]
        dd = float((e / e.cummax() - 1).min())
        ret = float(e.iloc[-1] - 1)
        out.update(cap=10000 * (1 + ret), ret=ret * 100, dd=dd * 100, mar=ret / abs(dd) if dd < 0 else np.nan)
    else:
        ret = float(np.prod(1 + r) - 1)
        out.update(cap=10000 * (1 + ret), ret=ret * 100)
    return out


def halves(tr: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(tr) == 0:
        return tr, tr
    return tr[tr["entry"] < OOS0], tr[tr["entry"] >= OOS0]


def variants(base: Cfg, **kw) -> Cfg:
    return replace(base, **kw)
