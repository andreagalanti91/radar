"""Esegue la famiglia A secondo PREREG.md. python3 research/intraday2/A_trend/run_a.py"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from engine import load_all, backtest, metrics, placebo, neighbours, Costs  # noqa
from strategies_a import VARIANTS, EXITS, SIZING  # noqa

CUT = "2024-01-01"
bars = load_all("4h")
NPL = int(os.environ.get("NPL", 500))


def run(fn, p, start, end=None):
    return backtest(bars, {a: fn(b, **p) for a, b in bars.items()}, EXITS, SIZING, Costs(), start, end)


rows, res_store = [], {}
for name, (fn, p) in VARIANTS.items():
    r = {k: run(fn, p, s, e) for k, (s, e) in {"IS": ("2021-01-01", CUT), "OOS": (CUT, None), "ALL": ("2021-01-01", None)}.items()}
    res_store[name] = r
    row = {"var": name}
    for k in ("IS", "OOS", "ALL"):
        m = metrics(r[k])
        for f in ("final", "ret_pct", "max_dd", "trades_per_month", "win_rate", "pf", "exp_R", "mar", "trades"):
            row[f"{k}_{f}"] = m.get(f)
    t = r["OOS"].trades
    row["OOS_assets_pos"] = int((t.groupby("asset")["pnl"].sum() > 0).sum()) if len(t) else 0
    row["OOS_wo_best"] = round(float(t["pnl"].sum() - t["pnl"].max()), 0) if len(t) else np.nan
    rows.append(row)
    print(name, {k: row[k] for k in row if k.startswith("IS_")}, flush=True)

df = pd.DataFrame(rows)
# selection on IS only (PREREG)
adm = df[(df.IS_trades_per_month.between(2, 12)) & (df.IS_pf >= 1.1) & (df.IS_exp_R > 0)].sort_values("IS_exp_R", ascending=False)
sel = None
if len(adm):
    top = adm.IS_exp_R.iloc[0]
    sel = adm[adm.IS_exp_R >= top - 0.02].sort_values("IS_trades").iloc[0]["var"]
print("ADMITTED:", adm["var"].tolist(), "SELECTED:", sel, flush=True)

# placebo (OOS, 500 runs) and neighbours (OOS) for every variant
pl_rows, nb_out = [], {}
for name, (fn, p) in VARIANTS.items():
    pl = placebo(res_store[name]["OOS"], bars, EXITS, SIZING, Costs(), n=NPL, seed=0)
    nb = neighbours(lambda q: run(fn, q, CUT), p, rel=(0.8, 1.2))
    nb_all = neighbours(lambda q: run(fn, q, "2021-01-01"), p, rel=(0.8, 1.2))
    nb_out[name] = nb
    pl_rows.append({"var": name, "pl_exp_R": pl["pctl"].get("exp_R"), "pl_ret": pl["pctl"].get("ret_pct"),
                    "nb_med_expR_OOS": round(float(nb["exp_R"].iloc[1:].median()), 3),
                    "nb_med_expR_ALL": round(float(nb_all["exp_R"].iloc[1:].median()), 3),
                    "nb_share_pf1_OOS": round(nb.attrs["share_pf_gt_1"], 2)})
    print(name, pl_rows[-1], flush=True)
df = df.merge(pd.DataFrame(pl_rows), on="var")


def passes(r):
    c = {"1_pf_exp": r.OOS_pf >= 1.3 and r.OOS_exp_R >= 0.15, "2_dd": r.OOS_max_dd >= -20,
         "3_halves_assets": r.IS_ret_pct > 0 and r.OOS_ret_pct > 0 and r.OOS_assets_pos >= 2,
         "4_freq": 2 <= r.OOS_trades_per_month <= 12, "5_placebo": r.pl_exp_R > 90 and r.pl_ret > 90,
         "6_neigh": r.nb_med_expR_OOS > 0, "7_wo_best": r.OOS_wo_best > 0}
    return c


df["criteria"] = df.apply(lambda r: "".join("1" if v else "0" for v in passes(r).values()), axis=1)
df["pass_all"] = df.criteria == "1111111"
df["selected"] = df["var"] == sel
pd.set_option("display.width", 250)
print(df.to_string(index=False))
df.to_csv(os.path.join(HERE, "results_a.csv"), index=False)
for name in VARIANTS:
    nb_out[name].to_csv(os.path.join(HERE, f"neigh_{name.split()[0]}.csv"), index=False)
best = sel or df.sort_values("OOS_exp_R", ascending=False)["var"].iloc[0]
res_store[best]["ALL"].trades.to_csv(os.path.join(HERE, f"trades_{best.split()[0]}.csv"), index=False)
# extra robustness detail for the chosen one
from engine import breakdown  # noqa
b = breakdown(res_store[best]["ALL"])
print("BEST", best); print(b["years"].to_string(index=False)); print(b["assets"].to_string(index=False)); print(b["sides"].to_string(index=False))
bo = breakdown(res_store[best]["OOS"]); print(bo["assets"].to_string(index=False)); print(bo["sides"].to_string(index=False))
# buy & hold 1/3 each, 1x, from 2021-01-01
bh = sum((b_.close[b_.index >= "2021-01-01"] / b_.close[b_.index >= "2021-01-01"].iloc[0]) for b_ in bars.values()) / 3 * 10_000
d = bh.resample("1D").last()
print("B&H final", round(d.iloc[-1]), "DD", round(float((d / d.cummax() - 1).min() * 100), 1))
for k in ("IS", "OOS"):
    s, e = ("2021-01-01", CUT) if k == "IS" else (CUT, None)
    x = sum((b_.close[(b_.index >= s) & ((b_.index < e) if e else True)] / b_.close[(b_.index >= s)].iloc[0]) for b_ in bars.values()) / 3 * 10_000
    xd = x.resample("1D").last(); print("B&H", k, round(xd.iloc[-1]), round(float((xd / xd.cummax() - 1).min() * 100), 1))
