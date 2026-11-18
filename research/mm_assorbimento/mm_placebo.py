"""Placebo (PREREG sezione 6): ogni trade spostato a un'ora casuale della stessa metà, stesso verso, stesse distanze di stop
e target in %, stesso tempo massimo, senza sovrapposizioni (finestre di 48 ore); esito sui prezzi reali con costi e funding.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

from mm_bt import FEE, SLIP, IS0, OOS0, Data


class Placebo:
    def __init__(self, dt: Data, tmax: int = 48):
        self.dt, self.tmax = dt, tmax
        O = dt.O
        n = dt.n - tmax
        self.n = n
        self.hr = swv(dt.Hh, tmax)[:n] / O[:n, None]
        self.lr = swv(dt.L, tmax)[:n] / O[:n, None]
        self.orl = swv(O, tmax)[:n] / O[:n, None]
        self.exit_t = O[tmax:tmax + n] / O[:n]
        cf = np.concatenate([[0], np.cumsum(dt.FR)])
        self.fund = cf[np.arange(n) + tmax] - cf[np.arange(n) + 1]   # settlement in (h, h+tmax)
        end = dt.idx.searchsorted(dt.idx[-1]) - tmax
        a, b, c = dt.idx.searchsorted(IS0), dt.idx.searchsorted(OOS0), min(end, n - 1)
        self.half = {"IS": (a, b - tmax), "OOS": (b, c)}

    def outcome(self, h: np.ndarray, side: np.ndarray, sd: np.ndarray, td: np.ndarray) -> np.ndarray:
        hr, lr, orl = self.hr[h], self.lr[h], self.orl[h]
        K = self.tmax
        up = side[:, None] > 0
        st_hit = np.where(up, lr <= (1 - sd)[:, None], hr >= (1 + sd)[:, None])
        tg_hit = np.where(up, hr >= (1 + td)[:, None], lr <= (1 - td)[:, None])
        ks = np.where(st_hit.any(1), st_hit.argmax(1), K)
        kt = np.where(tg_hit.any(1), tg_hit.argmax(1), K)
        rows = np.arange(len(h))
        stop_px = np.where(side > 0, np.minimum(orl[rows, np.minimum(ks, K - 1)], 1 - sd),
                           np.maximum(orl[rows, np.minimum(ks, K - 1)], 1 + sd))
        stop_px = np.where(ks == 0, np.where(side > 0, 1 - sd, 1 + sd), stop_px)
        tg_px = np.where(side > 0, np.maximum(orl[rows, np.minimum(kt, K - 1)], 1 + td),
                         np.minimum(orl[rows, np.minimum(kt, K - 1)], 1 - td))
        tg_px = np.where(kt == 0, np.where(side > 0, 1 + td, 1 - td), tg_px)
        px = np.where((ks <= kt) & (ks < K), stop_px, np.where(kt < K, tg_px, self.exit_t[h]))
        ef = 1 + side * SLIP
        xf = px * (1 - side * SLIP)
        return side * (xf / ef - 1) - FEE - FEE * xf / ef - side * self.fund[h]

    def templates(self, tr: pd.DataFrame):
        ref = tr["ef"] / (1 + tr["side"] * SLIP)
        sd = ((ref - tr["stop"]) * tr["side"] / ref).to_numpy()
        td = ((tr["tgt"] - ref) * tr["side"] / ref).to_numpy()
        half = np.where(tr["entry"] < OOS0, "IS", "OOS")
        return tr["side"].to_numpy(int), sd, td, half

    def draw_contig(self, rng, nh: int, a: int, b: int) -> np.ndarray:
        L = b - a + 1
        free = L - nh * self.tmax
        if free < nh:                                          # troppo denso: sovrapposizioni ammesse
            return rng.integers(a, b + 1, nh)
        x = np.sort(rng.integers(0, free, nh))
        return a + x + np.arange(nh) * self.tmax

    def draw_masked(self, rng, sides, allowed: dict) -> np.ndarray:
        occ = np.zeros(self.n + self.tmax, bool)
        out = np.empty(len(sides), int)
        for i in rng.permutation(len(sides)):
            cand = allowed[sides[i]]
            for _ in range(200):
                h = cand[rng.integers(len(cand))]
                if not occ[h:h + self.tmax].any():
                    break
            occ[h:h + self.tmax] = True
            out[i] = h
        return out

    def run(self, tr: pd.DataFrame, n_draws=1000, seed=7, w3=False) -> dict:
        side, sd, td, half = self.templates(tr)
        real = float(np.prod(1 + tr["r"].to_numpy()))
        rng = np.random.default_rng(seed)
        allowed = None
        if w3:
            dt = self.dt
            allowed = {}
            for hn, (a, b) in self.half.items():
                for s in (1, -1):
                    hh = np.arange(a, b + 1)
                    allowed[(hn, s)] = hh[dt.flat[hh] & (dt.reg[hh] == s)]
        sims = np.empty(n_draws)
        for k in range(n_draws):
            h = np.empty(len(side), int)
            for hn, (a, b) in self.half.items():
                m = half == hn
                if not m.any():
                    continue
                if w3:
                    sub = {s: allowed[(hn, s)] for s in (1, -1)}
                    h[m] = self.draw_masked(rng, side[m], sub)
                else:
                    h[m] = rng.permutation(self.draw_contig(rng, int(m.sum()), a, b))
            sims[k] = np.prod(1 + self.outcome(h, side, sd, td))
        kk = int((sims >= real).sum())
        return dict(p=(kk + 1) / (n_draws + 1), k=kk, real=real, med=float(np.median(sims)), p95=float(np.quantile(sims, .95)))
