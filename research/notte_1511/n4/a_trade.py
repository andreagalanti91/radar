"""N4 · Parte A, traduzione in trade (PREREG.md): migliore cella long e short della classifica → posizione per h giorni
(prolungata se alla scadenza si è ancora nella cella). 10.000 $ a 1x dal 2021, costi inclusi. Confronto con W3 e buy & hold.
Uso: python a_trade.py → a_trade.csv, a_trade.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from n4_data import build, raw  # noqa: E402
from radar import weekly  # noqa: E402

SLIP, FEE = {1: 0.001, -1: 0.001}, {1: 0.001, -1: 0.0005}


def in_cell(df, spec):
    m = pd.Series(True, index=df.index)
    for kv in spec.split(" & "):
        k, v = kv.split("=")
        m &= df[k] == v
    return m.fillna(False).to_numpy()


def sim(df, f, mask, h, side, start="2021-01-01", end=None):
    d = df[(df.index >= start) & ((df.index <= end) if end else True)]
    fu = f["funding"].fillna(0).reindex(d.index).to_numpy(float)
    m = mask[(df.index >= start) & ((df.index <= end) if end else True)]
    C = d["close"].to_numpy(float)
    cash, qty, eq, trades, until, e0, px0 = 1.0, 0.0, np.zeros(len(d)), [], -1, 0, 0
    for i in range(len(d)):
        if qty and i >= until:
            if m[i] and i < len(d) - 1:
                until = i + h
            else:
                px = C[i] * (1 - SLIP[side] * side)
                cash += qty * px - abs(qty) * px * FEE[side] - qty * px0
                trades.append(dict(entry=str(d.index[i0].date()), exit=str(d.index[i].date()), pnl=cash / e0 - 1))
                qty = 0.0
        if qty and side < 0:
            cash -= qty * C[i] * fu[i]          # short in perp: funding positivo incassato
        if not qty and m[i] and i < len(d) - 1:
            px0 = C[i] * (1 + SLIP[side] * side)
            e0 = cash
            qty = side * cash / px0
            cash -= abs(qty) * px0 * FEE[side]
            until, i0 = i + h, i
        eq[i] = cash + (qty * (C[i] - px0) if qty else 0.0)
    if qty:
        trades.append(dict(entry=str(d.index[i0].date()), exit="aperto", pnl=eq[-1] / e0 - 1))
    return pd.Series(eq, d.index), trades


def met(eq, trades):
    e = eq / eq.iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e / e.cummax() - 1).min())
    cagr = e.iloc[-1] ** (1 / yrs) - 1
    pn = np.array([t["pnl"] for t in trades]) if trades else np.zeros(0)
    best = pn.max() if len(pn) else 0
    return dict(finale=round(10000 * e.iloc[-1]), rend=round((e.iloc[-1] - 1) * 100, 1), dd=round(dd * 100, 1), trade=len(pn),
                wr=round((pn > 0).mean() * 100, 1) if len(pn) else np.nan, mar=round(cagr / abs(dd), 2) if dd else np.nan,
                senza_migliore=round(10000 * e.iloc[-1] / (1 + best)))


def placebo(df, f, trades, side, pool=None, ntrials=1000, seed=3):
    """Ingressi casuali con le STESSE durate dei trade reali (permutate), nel periodo dal 2021 (o fra i giorni di `pool`):
    capitale finale composto con gli stessi costi (funding degli short ignorato nel placebo)."""
    rng = np.random.default_rng(seed)
    d = df[df.index >= "2021-01-01"]
    C = d["close"].to_numpy(float)
    pos = {str(t.date()): i for i, t in enumerate(d.index)}
    dur = [pos.get(t["exit"], len(d) - 1) - pos[t["entry"]] for t in trades]
    cost = 2 * (SLIP[side] + FEE[side])
    out = []
    for _ in range(ntrials):
        cap = 1.0
        for L_ in dur:
            cand = np.arange(len(d) - L_ - 1) if pool is None else pool[pool < len(d) - L_ - 1]
            i = rng.choice(cand)
            cap *= 1 + side * (C[i + L_] / C[i] - 1) - cost
        out.append(cap * 10000)
    return np.array(out)


def main():
    f = raw()
    top = pd.read_csv(HERE / "a_top.csv")
    rows, lines = [], []
    df0, _ = build(0.43, 0.5, f)
    d21 = df0[df0.index >= "2021-01-01"]
    bh = d21["close"] / d21["close"].iloc[0]
    r_bh = met(bh, [dict(pnl=bh.iloc[-1] - 1)])
    w = weekly.simulate(f)
    r_w3 = met(w["equity"], w["trades"] + ([dict(pnl=w["open"]["pnl_close"])] if w["open"] else []))
    rows.append(dict(regola="Buy & hold", **r_bh)); rows.append(dict(regola="W3 (radar/weekly.py)", **r_w3))
    for side in ("long", "short"):
        t = top[top.side == side].iloc[0]
        sg = 1 if side == "long" else -1
        for th, thd, hh, lab in ((0.43, 0.5, t.h, "base"), (0.30, 0.30, t.h, "soglie ±0,30"), (0.60, 0.60, t.h, "soglie ±0,60"),
                                 (0.43, 0.5, max(t.h // 2, 3), "h/2"), (0.43, 0.5, t.h * 2, "2h")):
            df, _ = build(th, thd, f)
            mask = in_cell(df, t.cella)
            eq, tr = sim(df, f, mask, int(hh), sg)
            r = met(eq, tr)
            a = met(*sim(df, f, mask, int(hh), sg, end="2023-12-31"))
            b = met(*sim(df, f, mask, int(hh), sg, start="2024-01-01"))
            bh1 = d21.loc[:"2023-12-31", "close"]; bh2 = d21.loc["2024-01-01":, "close"]
            row = dict(regola=f"{side} {t.cella} h{int(hh)} [{lab}]", **r, rend_2123=a["rend"], mar_2123=a["mar"], rend_24=b["rend"], mar_24=b["mar"])
            if lab == "base":
                pl = placebo(df, f, tr, sg)
                row["placebo_pct"] = round(float((pl < r["finale"]).mean() * 100), 1)
                pd.DataFrame(tr).to_csv(HERE / f"a_trade_{side}.csv", index=False)
            rows.append(row)
    bh_a = met(d21.loc[:"2023-12-31", "close"] / d21["close"].iloc[0], [dict(pnl=0)])
    bh_b = met(d21.loc["2024-01-01":, "close"] / d21.loc["2024-01-01":, "close"].iloc[0], [dict(pnl=0)])
    rows[0].update(rend_2123=bh_a["rend"], mar_2123=bh_a["mar"], rend_24=bh_b["rend"], mar_24=bh_b["mar"])
    T = pd.DataFrame(rows)
    T.to_csv(HERE / "a_trade.csv", index=False)
    txt = T.to_string()
    (HERE / "a_trade.txt").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
