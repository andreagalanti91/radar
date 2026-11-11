"""M10 (tetto di rischio sui long) e baseline 'come dal vivo' (flusso perp del sabato). Uso: python3 run2.py > results2.txt"""
from eng import *
f = load_repo(); fl = load_long(f)
def lag(x):
    y = x.copy(); y["pf14z"] = y["pf14z"].shift(1); return y
fa, fla = lag(f), lag(fl)
def cap(R):
    return lambda wk, d: min(1.0, R / (2.5 * wk["atr"] / wk["close"]))
def m5(wk, d):
    return 1.3 if (wk["trend_age"] < 16 and wk["macd"] > wk["macd_sig"]) else 1.0
V = {"baseline": {}, "M1 liquidità 3,5%": dict(idle=0.035), "M2a 2 chiusure": dict(ema_n=2), "M2b margine 0,5": dict(ema_buf=0.5),
     "M3b pausa 2": dict(cooldown=2), "M4 runner": dict(run_r=2, run_k=3.0), "M5 leva 1,3x": dict(lev_fn=m5),
     "M6 D1": dict(short_noflow=True), "M7 R2 1,5": dict(r2=1.5), "M9 cricchetto": dict(ratchet=True),
     "M10 tetto long R25": dict(lev_fn=cap(0.25)), "M10 tetto long R20": dict(lev_fn=cap(0.20)), "M10 R30 (vicino)": dict(lev_fn=cap(0.30))}
PER = {"2021-oggi": ("2021-01-01", None, 0), "2021-23": ("2021-01-01", "2023-12-31", 0), "2024-oggi": ("2024-01-01", None, 0),
       "2018-20": ("2018-01-01", "2020-12-31", 1)}
for tag, (d0, d1) in (("DATI DEL BACKTEST (flusso della domenica)", (f, fl)), ("COME DAL VIVO (flusso del sabato)", (fa, fla))):
    print(f"== {tag} ==")
    base = {k: simulate((d0, d1)[w], start=a, end=b) for k, (a, b, w) in PER.items()}
    bm = metrics(base["2021-oggi"])
    for n, kw in V.items():
        s = f"{n:<22}"
        for k, (a, b, w) in PER.items():
            r = simulate((d0, d1)[w], start=a, end=b, **kw); m = metrics(r); c = changed(base[k], r)
            s += f"{k} {m['final']:>8,.0f} {m['dd']:>5.1f} n{m['n']:>2} WR{m['wr']:>4.0f} MAR {m['mar']:>4.2f} pegg {m['worst']:>5.1f} ({c[0]}/{c[1]})"
            if k == "2021-oggi":
                s += f" Δ{100 * (m['final'] / bm['final'] - 1):+6.1f}% senza best {m['final_wo']:>7,.0f}"
            s += " | "
        print(s)
    for n in ("M10 tetto long R25", "M10 tetto long R20"):
        r = simulate(d0, **V[n]); m = metrics(r); x, fb = equal_dd_base(d0, m["dd"])
        print(f"   {n}: pari DD → baseline x{x:.2f} = {fb:,.0f} ({100 * (m['final'] / fb - 1):+.1f}%); long ridotti:",
              [(t["entry"], t["expo"]) for t in r["trades"] if t["side"] == "long" and t["expo"] < 1])
        r = simulate(d1, start="2018-01-01", end="2020-12-31", **V[n])
        print("      2018-20 long ridotti:", [(t["entry"], t["expo"], round(t["pnl"] * 100, 1)) for t in r["trades"] if t["side"] == "long" and t["expo"] < 1])
    print()
