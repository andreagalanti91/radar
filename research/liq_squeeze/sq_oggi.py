"""Stato di OGGI secondo le regole (ultima ora chiusa), con la mappa ricostruita come nel backtest e con squeeze.state.
Uso: python research/liq_squeeze/sq_oggi.py → oggi.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
import squeeze  # noqa: E402
from radar import levels, liqmap  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

W_ = Path("/tmp/radar-work/liqsqueeze")
h = pd.read_pickle(W_ / "h.pkl"); M = pd.read_pickle(W_ / "hmaps.pkl")
CL, CS = pd.read_pickle(W_ / "casc.pkl")
T = M.index[-1]
win = h[(h.index >= T - pd.Timedelta(hours=liqmap.LOOKBACK_H)) & (h.index < T)][["high", "low", "close", "oi_usd"]].dropna()
p = float(win["close"].iloc[-1])
w = liqmap.window(liqmap.build(win), p, 0.15)
f = build_features(load_all()); f = f[f["close"].notna()]
rep = {"liqmap": {"price": p, "bins": w[["price", "long", "short"]].values.tolist()}, "levels": levels.compute(f[f.index < T.normalize()])}
last = {s: (str(x[x].index[-1]) if x.any() else None) for s, x in (("long", CL), ("short", CS))}
hist = {"long": M["L6"].iloc[-2161:-1], "short": M["S6"].iloc[-2161:-1]}
st = squeeze.state(rep, candles_1h=h[h.index < T], now=T, last_cascade_utc=last, hist_rad=hist)
st["decision_utc"] = str(T); st["last_cascade_hour_utc"] = last
for r in (0.10, 0.06):
    k = (w["price"] - p).abs() <= r * p
    st[f"short_above_{int(r*100)}"] = round(float(w.loc[k & (w.price > p), "short"].sum()))
    st[f"long_below_{int(r*100)}"] = round(float(w.loc[k & (w.price < p), "long"].sum()))
k = (w.price > p) & (w.price <= 76000)
st["short_fino_76k"] = round(float(w.loc[k, "short"].sum()))
st["oi_info"] = h.attrs.get("oi_info")
(HERE / "oggi.json").write_text(json.dumps(st, indent=1, default=str, ensure_ascii=False))
print(json.dumps(st, indent=1, default=str, ensure_ascii=False))
