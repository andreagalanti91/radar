"""Forma sopra/sotto: livelli REALI on-chain (data/liqsnap, Hyperliquid e Lighter) contro le mappe stimate v1/v2 alla stessa ora."""
from __future__ import annotations

import gzip
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import liqmap  # noqa: E402


def snaps(name):
    fr = []
    for p in sorted((ROOT / "data/liqsnap").glob(f"{name}_20??-??.csv.gz")):
        fr.append(pd.read_csv(io.StringIO(gzip.open(p, "rt").read())))
    x = pd.concat(fr)
    x = x[x["ts"] != "ts"].astype({"mid": float, "k": int, "long_usd": float, "short_usd": float})
    return x


def share(rows, lim):
    k = rows["k"] * liqmap.BIN
    s = rows.loc[(k >= 0) & (k < lim), "short_usd"].sum()
    l = rows.loc[(k < 0) & (k >= -lim), "long_usd"].sum()
    return s, l


okx = liqmap.okx_hourly()
h, _ = liqmap.extend_oi(liqmap.binance_hourly(), okx)
h["b"] = h["b"].fillna(liqmap.okx_taker_hourly(100).reindex(h.index))
out = []
for name in ("hl", "lighter"):
    S = snaps(name)
    for ts, g in S.groupby("ts"):
        T = pd.Timestamp(ts).floor("h")
        win = h[h.index < T].iloc[-liqmap.LOOKBACK_H:]
        if len(win) < 400:
            continue
        p = float(g["mid"].iloc[0])
        r = {"src": name, "ts": ts}
        for lim in (0.05, 0.10):
            s, l = share(g, lim)
            r[f"real{int(lim * 100)}"] = s / (s + l) if s + l else np.nan
            for v, sh in (("v1", None), ("v2", win["b"])):
                x = win[["high", "low", "close", "oi_usd"]].copy()
                if sh is not None:
                    x["long_share"] = sh
                w = liqmap.window(liqmap.build(x), p, 0.15)
                im = liqmap.imbalance(w, p, lim)
                r[f"{v}{int(lim * 100)}"] = im["short_above"] / (im["short_above"] + im["long_below"]) if im["short_above"] + im["long_below"] else np.nan
        out.append(r)
D = pd.DataFrame(out)
D.to_csv(Path(__file__).resolve().parent / "onchain.csv", index=False)
txt = []
for src, g in D.groupby("src"):
    txt.append(f"{src}: {len(g)} fotografie {g['ts'].min()} → {g['ts'].max()}")
    for lim in (5, 10):
        c1 = g[[f"real{lim}", f"v1{lim}"]].corr().iloc[0, 1]
        c2 = g[[f"real{lim}", f"v2{lim}"]].corr().iloc[0, 1]
        txt.append(f"  ±{lim}%: quota short reale media {g[f'real{lim}'].mean() * 100:.0f}% | v1 {g[f'v1{lim}'].mean() * 100:.0f}% (corr {c1:+.2f}) | "
                   f"v2 {g[f'v2{lim}'].mean() * 100:.0f}% (corr {c2:+.2f}) | ultima reale {g[f'real{lim}'].iloc[-1] * 100:.0f}% v1 {g[f'v1{lim}'].iloc[-1] * 100:.0f}% v2 {g[f'v2{lim}'].iloc[-1] * 100:.0f}%")
print("\n".join(txt))
(Path(__file__).resolve().parent / "onchain.txt").write_text("\n".join(txt) + "\n")
