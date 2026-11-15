"""Controlli DOPO il risultato su H4 (premio Coinbase), NON preregistrati e non decisivi: vicini (finestra, soglia),
anno per anno, controllo per il momentum a 30 giorni. Uso: python research/notte_1511/n3/controlli_h4.py >> risultati.txt"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from radar.data import load_all  # noqa
from radar.features import build_features  # noqa
f = build_features(load_all()); f = f[f["close"].notna()]
px = f["close"]; lp = np.log(px)
fwd7 = (lp.shift(-7) - lp) * 100
D = HERE / "data"
cb = pd.read_csv(D / "coinbase_btcusd_1d.csv", parse_dates=["date"]).set_index("date")["close"].reindex(px.index)
ut = pd.read_csv(D / "coinbase_usdtusd_1d.csv", parse_dates=["date"]).set_index("date")["close"].reindex(px.index).ffill().fillna(1.0)
prem = (cb / (px * ut) - 1) * 100
print("\n" + "=" * 100)
print("Controlli su H4 DOPO il risultato (non preregistrati, non decisivi). diff 7 g = media ON − OFF, punti %")
print("Vicini (finestra media, soglia in punti %):")
for n in (3, 7, 14, 30):
    for th in (-0.02, 0.0, 0.02):
        s = (prem.rolling(n, min_periods=max(2, n * 2 // 3)).mean().shift(1) > th)
        out = []
        for a, b in (("2021", "2023"), ("2024", "2026")):
            r = fwd7.loc[a:b]; ss = s.reindex(r.index); ok = r.notna()
            out.append(r[ok & ss].mean() - r[ok & ~ss].mean())
        print(f"  n={n:2d} soglia {th:+.2f}: IS {out[0]:+5.2f}  OOS {out[1]:+5.2f}")
s = prem.rolling(7, min_periods=5).mean().shift(1) > 0
print("Anno per anno (n=7, soglia 0): diff 7 g / quota ON")
for y in range(2021, 2027):
    r = fwd7.loc[str(y)]; ss = s.reindex(r.index); ok = r.notna()
    print(f"  {y}: {r[ok & ss].mean() - r[ok & ~ss].mean():+5.2f}  ON {ss[ok].mean()*100:4.0f}%")
mom = (lp - lp.shift(30)) > 0
print("Controllo momentum 30 g (diff H4 dentro ciascun regime di momentum, 2021–26):")
for mv, lab in ((True, "momentum +"), (False, "momentum −")):
    r = fwd7.loc["2021":]; m = mom.reindex(r.index) == mv; ss = s.reindex(r.index); ok = r.notna() & m
    print(f"  {lab}: diff {r[ok & ss].mean() - r[ok & ~ss].mean():+5.2f}  (n ON {int((ok & ss).sum())}, OFF {int((ok & ~ss).sum())})")
print(f"Accordo H4 con momentum 30 g > 0: {(s == mom).loc['2021':].mean()*100:.0f}% dei giorni")
