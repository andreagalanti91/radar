import sys, re, warnings, inspect; warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/user/radar"); sys.path.insert(0, "/home/user/radar/research/w2_migliorie")
import numpy as np, pandas as pd
from radar import weekly as W
from eng import load_repo, load_long
f = load_repo(); fl = load_long(f)
src = inspect.getsource(W.simulate)
src = src.replace("def simulate(f: pd.DataFrame, start: str = START, capital: float = 10000.0, lev: float = 1.0) -> dict:",
                  "def simulate_x(f, start=START, capital=10000.0, lev=1.0, chase=None, flow_n=None, be=None, end=None):\n    f = f.loc[:end] if end else f")
src = src.replace('    w = weekly_bars(f)\n', '    w = weekly_bars(f)\n    w["wchg"] = (w["close"] - w["close"].shift()) / w["atr"]\n    neg = (w["flow"] < 0).astype(int); w["negrun"] = neg.groupby((neg == 0).cumsum()).cumsum()\n    pos = (w["flow"] > 0).astype(int); w["posrun"] = pos.groupby((pos == 0).cumsum()).cumsum()\n')
# P3 pareggio: dentro il controllo dello stop
src = src.replace('            tr["stop"] = stop\n', '            if be is not None and (tr["best"] - tr["entry_px"]) * side >= be * tr["curatr"]:\n                stop = max(stop, tr["entry_px"] * 1.002) if side > 0 else min(stop, tr["entry_px"] * 0.998)\n            tr["stop"] = stop\n')
# P1 e P2 nella decisione della domenica
src = src.replace('            d = _decide(wk, side)\n', '''            d = _decide(wk, side)
            if d and d[0] == "enter" and chase is not None and abs(wk["wchg"]) > chase: d = None
            if d is None and side and flow_n is not None and (wk["negrun"] if side > 0 else wk["posrun"]) >= flow_n: d = ("exit", "flow")
''')
ns = dict(vars(W)); exec(src, ns); sim = ns["simulate_x"]
def run(**kw):
    out = {}
    for per, (x, s, e) in {"2021→": (f, "2021-01-01", None), "2018–20": (fl, "2018-01-01", "2020-12-31")}.items():
        r = sim(x, start=s, end=e, **kw); eq = r["equity"]; dd = float((eq / eq.cummax() - 1).min() * 100)
        out[per] = (round(float(eq.iloc[-1])), round(dd, 1), [(t["entry"], t["exit"], round(t["pnl"] * 100, 1)) for t in r["trades"]])
    return out
base = run(); rows = []
def changed(a, b): return len(set(x[:2] for x in a) ^ set(x[:2] for x in b))
for name, kw in [("W3 (base)", {})] + [(f"P1 non inseguire k={k}", dict(chase=k)) for k in (1.5, 2.0, 2.5)] + \
        [(f"P2 flusso contro n={n}", dict(flow_n=n)) for n in (2, 3, 4)] + [(f"P3 pareggio m={m}", dict(be=m)) for m in (1.0, 1.5, 2.0)]:
    r = run(**kw); last = [t for t in r["2021→"][2] if t[0] == "2026-08-24"]
    rows.append(dict(regola=name, fin_21=r["2021→"][0], dd_21=r["2021→"][1], camb_21=changed(base["2021→"][2], r["2021→"][2]),
                     fin_1820=r["2018–20"][0], dd_1820=r["2018–20"][1], camb_1820=changed(base["2018–20"][2], r["2018–20"][2]),
                     trade_ago26=(f"{last[0][2]}% (uscita {last[0][1]})" if last else "evitato")))
d = pd.DataFrame(rows); d.to_csv("risultati.csv", index=False); pd.set_option("display.width", 220); print(d.to_string(index=False))
