"""Diagnostica NON preregistrata (dopo i risultati): regime W2 (SMA40 in calo) senza il filtro di flusso, con/senza MACD."""
import sys
sys.path.insert(0, '.')
from short_lab import *  # noqa
f = load_repo(); fl = load_long(f)
for name, ff, a, b in (("2021-oggi", f, "2021-01-01", None), ("2021-23", f, "2021-01-01", "2023-12-31"),
                       ("2024-oggi", f, "2024-01-01", None), ("2018-20", fl, "2018-01-01", "2020-12-31")):
    w = weekly_bars(ff); c = w["close"]
    D = {"D1 W2-regime senza flusso": (w["dn_w2"] & (c < w["ema21"])).fillna(False)}
    D["D2 D1+MACD"] = (D["D1 W2-regime senza flusso"] & w["mbear"]).fillna(False)
    D["S0 (W2 short, fee 0,1%)"] = (w["dn_w2"] & (c < w["ema21"]) & (w["flow"] < 0)).fillna(False)
    for k, s in D.items():
        cfg = short_cfg("S0" if k.startswith("S0") else "S1", size="R25")
        for lg in (False, True):
            m = metrics(simulate(ff, w, s, cfg, longs=lg, start=a, end=b))
            print(f"{name:<10} {k:<28} {'combo' if lg else 'solo ':<6} {m['final']:>8,} {m['ret']:>7.1f}% DD {m['dd']:>6.1f} n {m['n']:>2} WR {m['wr']} MAR {m['mar']}")
        if name == "2021-oggi":
            x = simulate(ff, w, s, cfg, longs=False, start=a)
            print("   ", " | ".join(f"{t['entry']}→{t['exit']} {t['pnl']*100:+.1f}% {t['reason']}" for t in x["trades"]))
