"""tradera_test · varianti dentro W3.2 (PREREG 9da09c8): WV1 ingresso al ritest con confluenza, WV2 metà all'obiettivo di
struttura. BTC (dati congelati di research/p2_nuovi) ed ETH (radar.data come in forza_giornaliera). Output: w32.txt.
Uso: python3 tt_w32.py"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
for p in (HERE, R, R / "research" / "p2_nuovi", R / "research" / "forza_giornaliera"):
    sys.path.insert(0, str(p))
import fg_engine as FG  # noqa: E402
import tt_detect as T  # noqa: E402
import tt_w32_engine as TP  # noqa: E402
from p2_data import load  # noqa: E402

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def levels(f: pd.DataFrame):
    r = T.detect(f)
    C, A = f["close"].to_numpy(float), r["atr"]
    e50, e200 = r["ema"][50], r["ema"][200]
    n = len(C)
    sup, res = np.full(n, np.nan), np.full(n, np.nan)
    for i in range(n):
        cs = [x for x in (e50[i], e200[i], r["brk"][1][i]) if np.isfinite(x) and x < C[i] and C[i] - x <= 2 * A[i]]
        cr = [x for x in (e50[i], e200[i], r["brk"][-1][i]) if np.isfinite(x) and x > C[i] and x - C[i] <= 2 * A[i]]
        sup[i] = max(cs) if cs else np.nan
        res[i] = min(cr) if cr else np.nan
    return sup, res


def tp_fn_for(f: pd.DataFrame):
    H, L = f["high"].to_numpy(float), f["low"].to_numpy(float)

    def fn(i, side, px):
        a = max(0, i - 250)
        lvl = H[a:i].max() if side > 0 else L[a:i].min()
        d = side * (lvl / px - 1)
        return float(d) if d >= 0.05 else None
    return fn


def met(eq: pd.Series, trades: list) -> dict:
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    fin = float(eq.iloc[-1])
    cagr = (fin / 10000) ** (1 / yrs) - 1
    dd = float((eq / eq.cummax() - 1).min())
    return dict(fin=round(fin), dd=round(100 * dd, 1), cdd=round(cagr / abs(dd), 3), n=len(trades),
                wr=round(100 * np.mean([t["pnl"] > 0 for t in trades]), 1) if trades else float("nan"))


def run(name, f, start, end, var, sup_res, fn):
    if var == "W3.2":
        r = TP.simulate(f, {}, start=start, end=end)
    elif var == "WV1":
        r = FG.simulate(f, {"ein": {"level": sup_res, "K": 5}}, start=start, end=end)
    else:
        r = TP.simulate(f, {"tp": (None, 0.5), "tp_fn": fn}, start=start, end=end)
    return met(r["equity"], r["trades"]), r


def main():
    d = load()
    F, FL = d["f"], d["fl"]
    import fg_lib
    E = fg_lib.eth()
    sets = {"BTC": {"18-20": (FL, "2018-01-01", "2020-12-31"), "21-23": (F, "2021-01-01", "2023-12-31"),
                    "24-26": (F, "2024-01-01", None), "21+": (F, "2021-01-01", None)},
            "ETH": {"19-20": (E, "2019-12-01", "2020-12-31"), "21-23": (E, "2021-01-01", "2023-12-31"),
                    "24-26": (E, "2024-01-01", None), "21+": (E, "2021-01-01", None)}}
    say("=== W3.2 con le idee di TraderA (PREREG 9da09c8) · 10.000 $ per periodo, rischio 25%")
    res = {}
    for asset, per in sets.items():
        cache = {}
        for pn, (f, st, en) in per.items():
            key = id(f)
            if key not in cache:
                cache[key] = (levels(f), tp_fn_for(f))
            sr, fn = cache[key]
            for var in ("W3.2", "WV1", "WV2"):
                m, r = run(asset, f, st, en, var, sr, fn)
                res[(asset, pn, var)] = m
                extra = ""
                if var == "WV1":
                    lim = sum(1 for t in r["trades"] if t.get("limit"))
                    extra = f" · ingressi a limite {lim}/{len(r['trades'])}"
                if var == "WV2":
                    extra = f" · TP parziali eseguiti {r['n_tp']}"
                say(f"{asset} {pn:5s} {var:4s}: fin {m['fin']:>7,} · DD {m['dd']}% · CAGR/DD {m['cdd']} · trade {m['n']} · WR {m['wr']}%{extra}".replace(",", "."))
    say("\nCriterio: CAGR/DD > W3.2 in 21-23 E 24-26, e (BTC) 18-20 non peggiore")
    for asset in sets:
        lp = "18-20" if asset == "BTC" else "19-20"
        for var in ("WV1", "WV2"):
            c = [res[(asset, p, var)]["cdd"] > res[(asset, p, "W3.2")]["cdd"] for p in ("21-23", "24-26")]
            c3 = res[(asset, lp, var)]["cdd"] >= res[(asset, lp, "W3.2")]["cdd"]
            ok = all(c) and (c3 or asset == "ETH")
            say(f"{asset} {var}: 21-23 {'✓' if c[0] else '✗'} · 24-26 {'✓' if c[1] else '✗'} · {lp} {'✓' if c3 else '✗'} → "
                f"{'MIGLIORA' if ok else 'non migliora'}")
    (HERE / "w32.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
