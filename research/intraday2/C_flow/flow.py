"""Famiglia C (flusso e derivati), 4h. Varianti preregistrate in PREREG.md.
Uso: python3 flow.py is | oos | robust <ID>"""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from engine import (Exits, Sizing, Costs, load_all, backtest, metrics, breakdown, placebo, neighbours, atr,
                    DATA, IS_END)

TF = "4h"
EX = Exits(stop_atr=1.5, tp=[(1.5, .5), (3.0, .5)], tp_unit="R", be_after_tp1=True, time_bars=12,
           reverse_exit=False, reverse_entry=False)
SZ = Sizing(mode="risk", risk_pct=0.01, leverage=2, allocation="shared", max_exposure=5.0)
CO = Costs()
START, CUT = "2021-01-01", IS_END
ZW = 180


def z(s, w=ZW):
    m, sd = s.rolling(w, min_periods=w // 2).mean(), s.rolling(w, min_periods=w // 2).std()
    return (s - m) / sd


def funding_level(asset, idx):
    f = pd.read_csv(os.path.join(DATA, f"{asset}_funding.csv.gz"))
    f["ts"] = pd.to_datetime(f["ts"], utc=True)
    f["r8"] = f["rate"] * 8 / f["interval_h"].fillna(8)
    s = f.groupby(f["ts"].dt.floor(TF))["r8"].last()   # last event inside the 4h bar (known at bar close)
    return s.reindex(idx).ffill()


def feats(b, asset):
    c = b.close
    F = pd.DataFrame(index=b.index)
    F["fz"] = z(funding_level(asset, b.index))
    oi = b["oi"].replace(0, np.nan) if "oi" in b else pd.Series(np.nan, b.index)
    F["oiz"] = z(oi / oi.shift(6) - 1)
    vol = b.volume
    d = (2 * b.taker_buy_volume - vol).fillna(0)
    v = vol.fillna(0)
    F["dr6"] = d.rolling(6).sum() / v.rolling(6).sum()
    F["dr20z"] = z(d.rolling(20).sum() / v.rolling(20).sum())
    F["lsz"] = z(b["glob_acc_ls"]) if "glob_acc_ls" in b else np.nan
    F["atr"] = atr(b)
    e20, e50 = c.ewm(span=20, adjust=False).mean(), c.ewm(span=50, adjust=False).mean()
    F["e_up"], F["e_dn"] = e20 > e50, e20 < e50
    return F


def mom(b, F, n=20):
    up = (b.close > b.high.rolling(n).max().shift()) & F.e_up
    dn = (b.close < b.low.rolling(n).min().shift()) & F.e_dn
    return up, dn


def side(up, dn):
    return pd.DataFrame({"side": up.fillna(False).astype(int) - dn.fillna(False).astype(int)})


def sig_C0(b, F, n=20): return side(*mom(b, F, n))


def sig_C1(b, F, z_=2.0, n=6):
    lo_ext = (F.fz <= -z_).astype(float).rolling(n).max() > 0
    hi_ext = (F.fz >= z_).astype(float).rolling(n).max() > 0
    up = lo_ext & (b.close > b.high.rolling(n).max().shift())
    dn = hi_ext & (b.close < b.low.rolling(n).min().shift())
    return side(up, dn)


def sig_C2(b, F, z_=1.0, n=20):
    up, dn = mom(b, F, n)
    return side(up & (F.fz < z_), dn & (F.fz > -z_))


def sig_C3(b, F, z_=1.0, n=20):
    up, dn = mom(b, F, n)
    return side(up & (F.oiz > z_), dn & (F.oiz > z_))


def sig_C4(b, F, k=3.0, z_=2.0):
    r6 = b.close - b.close.shift(6)
    flush = F.oiz <= -z_
    up = (r6 <= -k * F.atr) & flush & (b.close > b.open)
    dn = (r6 >= k * F.atr) & flush & (b.close < b.open)
    return side(up, dn)


def sig_C5(b, F, n=20, z_=1.0):
    up = (b.low <= b.low.rolling(n).min()) & (F.dr20z >= z_) & (b.close > b.open)
    dn = (b.high >= b.high.rolling(n).max()) & (F.dr20z <= -z_) & (b.close < b.open)
    return side(up, dn)


def sig_C6(b, F, z_=2.0, n=6):
    lo = (F.lsz <= -z_).astype(float).rolling(n).max() > 0
    hi = (F.lsz >= z_).astype(float).rolling(n).max() > 0
    up = lo & (b.close > b.high.rolling(n).max().shift())
    dn = hi & (b.close < b.low.rolling(n).min().shift())
    return side(up, dn)


def sig_C7(b, F, n=20, fmax=2.0):
    up, dn = mom(b, F, n)
    up = up & (F.dr6 > 0) & (F.oiz > 0) & (F.fz < fmax)
    dn = dn & (F.dr6 < 0) & (F.oiz > 0) & (F.fz > -fmax)
    return side(up, dn)


VARIANTS = {"C0": (sig_C0, {"n": 20}), "C1": (sig_C1, {"z_": 2.0, "n": 6}), "C2": (sig_C2, {"z_": 1.0}),
            "C3": (sig_C3, {"z_": 1.0}), "C4": (sig_C4, {"k": 3.0, "z_": 2.0}), "C5": (sig_C5, {"n": 20, "z_": 1.0}),
            "C6": (sig_C6, {"z_": 2.0, "n": 6}), "C7": (sig_C7, {})}
NEED_OI = {"C3", "C4", "C6", "C7"}   # sample from 2021-12

BARS = load_all(TF)
FEATS = {a: feats(b, a) for a, b in BARS.items()}


def sigs(vid, **p):
    fn, base = VARIANTS[vid]
    q = {**base, **p}
    return {a: fn(BARS[a], FEATS[a], **q) for a in BARS}


def start_of(vid): return "2021-12-01" if vid in NEED_OI else START


def run(vid, start=None, end=None, **p):
    return backtest(BARS, sigs(vid, **p), EX, SZ, CO, start or start_of(vid), end)


def row(res, vid, per):
    m = metrics(res)
    t = res.trades
    pa = t.groupby("asset")["pnl"].sum() if len(t) else pd.Series(dtype=float)
    best = t["pnl"].max() if len(t) else 0
    return {"id": vid, "per": per, "final": m.get("final"), "ret": m.get("ret_pct"), "dd": m.get("max_dd"),
            "tpm": m.get("trades_per_month"), "n": m.get("trades"), "wr": m.get("win_rate"), "pf": m.get("pf"),
            "expR": m.get("exp_R"), "mar": m.get("mar"), "assets_pos": int((pa > 0).sum()),
            "long_R": round(t[t.side == 1].R.mean(), 3) if len(t) else np.nan,
            "short_R": round(t[t.side == -1].R.mean(), 3) if len(t) else np.nan,
            "no_best": round(float(t.pnl.sum() - best), 0) if len(t) else 0}


if __name__ == "__main__":
    mode = sys.argv[1]
    pd.set_option("display.width", 250)
    if mode == "is":
        rows = [row(run(v, end=CUT), v, "IS") for v in VARIANTS]
        print(pd.DataFrame(rows).to_string(index=False))
    elif mode == "oos":
        rows = []
        for v in VARIANTS:
            rows += [row(run(v, end=CUT), v, "IS"), row(run(v, start=CUT), v, "OOS"), row(run(v), v, "ALL")]
        df = pd.DataFrame(rows)
        df.to_csv(os.path.join(HERE, "results.csv"), index=False)
        print(df.to_string(index=False))
    elif mode == "robust":
        vid = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 500
        res = run(vid, start=CUT)
        pl = placebo(res, BARS, EX, SZ, CO, n=n, seed=1)
        print("placebo OOS", pl["pctl"], pl["real"], "placebo median ret", pl["runs"].ret_pct.median(),
              "trades med", pl["runs"].trades.median(), "real n", len(res.trades))
        base = VARIANTS[vid][1]
        if base:
            nb = neighbours(lambda p: run(vid, start=CUT, **p), base, rel=(0.8, 1.2))
            print("neighbours OOS\n", nb.to_string(index=False), "\nmedian ret", nb.ret_pct.iloc[1:].median())
            nbi = neighbours(lambda p: run(vid, end=CUT, **p), base, rel=(0.8, 1.2))
            print("neighbours IS\n", nbi.to_string(index=False), "\nmedian ret", nbi.ret_pct.iloc[1:].median())
        b = breakdown(run(vid))
        print(b["years"].to_string(index=False)); print(b["assets"].to_string(index=False)); print(b["sides"].to_string(index=False))
        run(vid).trades.to_csv(os.path.join(HERE, f"trades_{vid}.csv"), index=False)


def placebo_one(vid, n=500):
    res = run(vid, start=CUT)
    pl = placebo(res, BARS, EX, SZ, CO, n=n, seed=1)
    return {"id": vid, "pctl_ret": pl["pctl"].get("ret_pct"), "placebo_med_ret": pl["runs"].ret_pct.median()}


if __name__ == "__main__" and sys.argv[1] == "placebo_all":
    from multiprocessing import Pool
    with Pool(4) as p:
        out = pd.DataFrame(p.map(placebo_one, list(VARIANTS)))
    out.to_csv(os.path.join(HERE, "placebo.csv"), index=False)
    print(out.to_string(index=False))
