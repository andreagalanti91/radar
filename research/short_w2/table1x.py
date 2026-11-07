"""Tabella comparativa a 1x (richiesta utente): W2 com'è vs long W2 + nuovo short vs nuovo short da solo; split; CSV trade."""
import sys
sys.path.insert(0, '.')
import pandas as pd
from short_lab import *  # noqa
from run import run
f = load_repo(); fl = load_long(f)
PER = {"2021-oggi": (f, "2021-01-01", None), "2021-23": (f, "2021-01-01", "2023-12-31"),
       "2024-oggi": (f, "2024-01-01", None), "2018-20": (fl, "2018-01-01", "2020-12-31")}
def sims(rule, ff, a, b, size, longs):
    w = weekly_bars(ff); c = w["close"]
    if rule == "W2":
        return simulate(ff, w, short_rules(w)["S0"], short_cfg("S0", size="R25"), longs=True, start=a, end=b, w2_short_fees=True)
    if rule == "D1":
        s = (w["dn_w2"] & (c < w["ema21"])).fillna(False)
        return simulate(ff, w, s, short_cfg("S1", size=size), longs=longs, start=a, end=b)
    return run(ff, w, rule, size, longs, a, b)
for size in ("1x", "R25"):
    print(f"\n### size short {size}")
    for name, (ff, a, b) in PER.items():
        for rule, longs in (("W2", True), ("S1", True), ("S1", False), ("S5", True), ("S5", False), ("D1", True), ("D1", False)):
            if rule == "W2" and size == "R25": continue
            m = metrics(sims(rule, ff, a, b, size, longs))
            lab = "W2 com'è (short R25)" if rule == "W2" else f"{rule} {'+ long W2' if longs else 'da solo'}"
            print(f"{name:<10}|{lab:<22}|{m['final']:>9,}|{m['ret']:>8.1f}|{m['dd']:>6.1f}|{m['n']:>3}|{m['wr']}|{m['mar']}|{m['tim']}")
for rule in ("S1", "D1"):
    r = sims(rule, f, "2021-01-01", None, "1x", False)
    pd.DataFrame(r["trades"]).drop(columns=["best", "curatr"], errors="ignore").to_csv(f"trades_{rule}_1x_2021.csv", index=False)
