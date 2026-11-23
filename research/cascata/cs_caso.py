"""Caso del 21/11/2026 (fuori campione): cosa avrebbero fatto le definizioni e le varianti. Dati del tool fino al 21/11 +
candele giornaliere Binance spot del 22/11 (chiusa) e del 23/11 (in corso: ultimo prezzo) da dati/btc_1d.json. → caso.txt"""
import json
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import cs_engine as E  # noqa: E402
import cs_lib as L  # noqa: E402

CAP = 50000.0
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


f = L.btc_live()
k = json.loads((L.HERE / "dati/btc_1d.json").read_text())
for r in k:
    d = pd.Timestamp(r[0], unit="ms")
    if d > f.index[-1]:
        f.loc[d, ["open", "high", "low", "close"]] = [float(v) for v in r[1:5]]
last_day, last_px = f.index[-1], float(f["close"].iloc[-1])
x = L.feats(f)
D1, D3 = dict(rA=2, vr=2), dict(eA=1.25, vr=2, tail=0.5)
say(f"Dati: tool fino al 21/11, 22/11 chiusa, {last_day.date()} in corso (ultimo prezzo {last_px:.0f})")
t = pd.concat([f[["open", "high", "low", "close"]], x[["atr1", "vr", "rA_S", "eA_S", "tail_S"]]], axis=1).loc["2026-11-16":"2026-11-21"].copy()
t["D1"], t["D3"] = L.trig(x, D1, "S").reindex(t.index), L.trig(x, D3, "S").reindex(t.index)
for kk in (1.25, 1.5, 2.0, 2.5):
    t[f"lim{kk}"] = (f["close"].shift(1) - kk * x["atr1"]).reindex(t.index).round(0)
    t[f"toc{kk}"] = t["low"] <= t[f"lim{kk}"]
say(t.round(2).to_string())
w = L.W.weekly_bars(f)
say("\nDecisione domenicale 22/11:", w.loc["2026-11-22", ["close", "ema21", "sma", "flow", "atr", "short", "long"]].to_dict())

never = pd.Series(False, index=f.index)
CASES = {"W3.2 (tiene)": {}, "C1/C4 D1": dict(trig=(L.trig(x, D1, "L"), L.trig(x, D1, "S"))),
         "C5 D3 tutto R1": dict(trig=(L.trig(x, D3, "L"), L.trig(x, D3, "S"))),
         "C5' D3 tutto R2 5%": dict(trig=(L.trig(x, D3, "L"), L.trig(x, D3, "S")), reentry=("R2", 0.05)),
         "D3 metà": dict(trig=(L.trig(x, D3, "L"), L.trig(x, D3, "S")), frac=0.5),
         "D3 tutto, nessun rientro (R3)": dict(trig=(L.trig(x, D3, "L"), L.trig(x, D3, "S")), reentry="R3", windows=[("2026-11-16", None)]),
         "C6 LIM 2 ATR": dict(lim=2.0), "vicino LIM 1,5 ATR": dict(lim=1.5), "vicino LIM 1,25 ATR": dict(lim=1.25),
         "LIM 1,25 ATR, nessun rientro": dict(lim=1.25, reentry="R3", windows=[("2026-11-16", None)])}
say(f"\nCapitale {CAP:.0f} $ al 15/11 (flat). Valore al {last_day.date()} a {last_px:.0f} $ (candela in corso, funding 22–23/11 non incluso):")
base = None
for nm, cfg in CASES.items():
    r = E.simulate(f, cfg, start="2026-11-10", capital=CAP)
    eq = r["equity"]
    fin = float(eq.iloc[-1])
    if base is None:
        base = fin
    ev = "; ".join(f"uscita {e['day']} a {e['px']:.0f}" for e in r["evlog"]) or "nessuna uscita"
    tr = "; ".join(f"{q['side']} {q['entry']} a {q['entry_px']:.0f} (espos. {q['expo']}) → {q.get('exit')} a {q.get('exit_px')} [{q.get('reason')}, {q['kind']}]" for q in r["trades"])
    op = r["open"]
    ops = f"aperto: {op['side']} dal {op['entry']} a {op['entry_px']:.0f} (espos. {op['expo']}, {op['kind']}), stop {op['stop']:.0f}" if op else "flat"
    say(f"{nm:30s} {fin:9.0f} $  P/L {fin - CAP:+7.0f}  contro W3.2 {fin - base:+7.0f} | {ev} | {tr} | {ops}")
# ipotetico impossibile: chiusura al minimo
r = E.simulate(f, {}, start="2026-11-10", capital=CAP)
op = r["open"]
q = op["expo"] * CAP / op["entry_px"]
say(f"\nPosizione W3.2: short {q:.4f} BTC da {op['entry_px']:.1f} (nozionale {q*op['entry_px']:.0f} $ su {CAP:.0f}).")
for lab, px in (("minimo 55.130 (non eseguibile)", 55130.0), ("apertura 22/11 (eseguibile, con slippage)", float(f.loc['2026-11-22', 'open']) * 1.001),
                ("chiusura 21/11", float(f.loc['2026-11-21', 'close'])), (f"ultimo prezzo {last_px:.0f}", last_px)):
    say(f"  chiusura a {lab}: {px:.0f} → P/L lordo {q * (op['entry_px'] - px):+.0f} $ ({(1 - px / op["entry_px"]) * 100:+.1f}% sul prezzo)")
(L.HERE / "caso.txt").write_text("\n".join(OUT) + "\n")
