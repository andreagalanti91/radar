"""Caso del 13/11 (Coinglass vs mappa): v1/v2/v2k su Binance USDT-M dal vivo, come la dashboard (archivio + OKX dopo l'archivio).

Ore dopo l'archivio: OI stimato con extend_oi (OKX) e quota taker OKX (rubik taker-volume-contract)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import liqmap  # noqa: E402

okx = liqmap.okx_hourly()
h, info = liqmap.extend_oi(liqmap.binance_hourly(), okx)
tk = liqmap.okx_taker_hourly(100)
nb = int(h["b"].isna().sum())
h["b"] = h["b"].fillna(tk.reindex(h.index))
win = h.iloc[-liqmap.LOOKBACK_H:]
p = float(win["close"].iloc[-1])
print(f"Binance fino a {win.index[-1]} (OI vero fino a {info['oi_until']}, {info['extended_h']} ore stimate), prezzo {p:.0f}; "
      f"ore senza taker Binance {nb}, coperte da OKX {nb - int(h['b'].isna().sum())}")
for name, sh in (("v1", None), ("v2", win["b"]), ("v2k", (0.5 + 3 * (win["b"] - 0.5)))):
    x = win[["high", "low", "close", "oi_usd"]].copy()
    if sh is not None:
        x["long_share"] = sh
    w = liqmap.window(liqmap.build(x), p, 0.15)
    r = []
    for rng in (0.05, 0.10, 0.15):
        im = liqmap.imbalance(w, p, rng)
        r.append(f"±{rng * 100:.0f}% short sopra {im['short_above'] / 1e6:5.0f} M long sotto {im['long_below'] / 1e6:5.0f} M")
    up = [c for c in liqmap.clusters(w, p, "short", rng=0.12) if c["sig"]]
    print(f"{name:4s} " + " | ".join(r) + " | cluster short: " + ", ".join(f"{c['price']:.0f} {c['usd'] / 1e6:.0f}M" for c in up[:5]))
d = win.resample("D").agg({"close": "last", "oi_usd": "last", "b": "mean"})
print((d.assign(oi_b=d.oi_usd / 1e9).drop(columns="oi_usd")).tail(10).round(3).to_string())
