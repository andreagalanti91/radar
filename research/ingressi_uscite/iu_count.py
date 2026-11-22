"""Fase 1 · controlli del motore e CONTEGGIO degli eventi per regola (nessun rendimento, P&L, DD o esito di trade, salvo la
riproduzione di W3.1 richiesta come controllo). Output: conteggi.txt. Uso: python3 iu_count.py"""
from __future__ import annotations

import sys
import warnings
from collections import Counter
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "research" / "p2_nuovi"))
import iu_engine as E  # noqa: E402
from p2_data import load  # noqa: E402
from radar import weekly as W  # noqa: E402

d = load()
F, FL = d["f"], d["fl"]
PER = {"2021+": (F, "2021-01-01", None), "IS 21-23": (F, "2021-01-01", "2023-12-31"),
       "OOS 24-26": (F, "2024-01-01", None), "2018-20": (FL, "2018-01-01", "2020-12-31")}
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def run(cfg, per):
    x, s, e = PER[per]
    if cfg.get("g7"):
        return E.simulate_g7(x, {kk: v for kk, v in cfg.items() if kk != "g7"}, start=s, end=e)
    return E.simulate(x, cfg, start=s, end=e)


def tl(r):
    return r["trades"] + ([r["open"]] if r["open"] else []) + r.get("open_list", [])


# ---------------------------------------------------------------- 1. riproduzione di W3.1 (unico numero di rendimento ammesso)
for per in PER:
    x, s, e = PER[per]
    xx = x if e is None else x[x.index <= e]
    a, b = W.simulate(xx, start=s), run({}, per)
    eqb = b["equity"]
    dd = float((eqb / eqb.cummax() - 1).min())
    same = np.allclose(a["equity"].to_numpy(), eqb.to_numpy(), rtol=0, atol=1e-6)
    say(f"W3.1 {per}: identico a radar.weekly={same} · finale {eqb.iloc[-1]:,.0f} $ · DD {100*dd:.1f}% · trade {len(tl(b))}")
assert round(float(run({}, "2021+")["equity"].iloc[-1])) == 27190

# ---------------------------------------------------------------- 2. invarianze (configurazioni degeneri = W3.1)
base = run({}, "2021+")["equity"].to_numpy()
for name, cfg in [("E1 una parte", dict(entry=("E1", (0,)))), ("E2 n=1", dict(entry=("E2", 1))),
                  ("U1 a=1", dict(exit=("U1", 1.0))), ("U2 2,5/2,5", dict(exit=("U2", 2.5, 2.5))),
                  ("D3 s=1", dict(dist=("D3", 1.0))), ("D2 n=1", dict(dist=("D2", 1))),
                  ("TP a +99R", dict(tp=dict(levels=(99,), frac=1 / 3)))]:
    ok = np.allclose(run(cfg, "2021+")["equity"].to_numpy(), base, rtol=0, atol=1e-6)
    say(f"invarianza {name}: {ok}")
    assert ok, name

# ---------------------------------------------------------------- 3. varianti preregistrate (principale + vicini)
V = {
    "E1 lun/mer/ven": dict(entry=("E1", (0, 2, 4))), "E1v lun/gio": dict(entry=("E1", (0, 3))),
    "E1v lun-ven 5": dict(entry=("E1", (0, 1, 2, 3, 4))),
    "E2 3 sett.": dict(entry=("E2", 3)), "E2v 2 sett.": dict(entry=("E2", 2)), "E2v 4 sett.": dict(entry=("E2", 4)),
    "E3 0,5 ATR 14g": dict(entry=("E3", 0.5, 14)), "E3v 0,25 ATR": dict(entry=("E3", 0.25, 14)),
    "E3v 0,75 ATR": dict(entry=("E3", 0.75, 14)),
    "U1 1/2+1/2": dict(exit=("U1", 0.5)), "U1v 1/3": dict(exit=("U1", 1 / 3)), "U1v 2/3": dict(exit=("U1", 2 / 3)),
    "U2 2,0/3,0": dict(exit=("U2", 2.0, 3.0)), "U2v 2,25/2,75": dict(exit=("U2", 2.25, 2.75)),
    "U2v 1,75/3,25": dict(exit=("U2", 1.75, 3.25)),
    "T1 1/3 a +3R": dict(tp=dict(levels=(3,), frac=1 / 3)), "T1v +2R": dict(tp=dict(levels=(2,), frac=1 / 3)),
    "T1v +4R": dict(tp=dict(levels=(4,), frac=1 / 3)),
    "K 2,0 (vicino)": dict(k=2.0), "K 2,25": dict(k=2.25), "K 2,75": dict(k=2.75), "K 3,0": dict(k=3.0),
    "K 3,25 (vicino)": dict(k=3.25),
    "D1 senza": dict(dist=("D1",)), "D2 2 dom.": dict(dist=("D2", 2)), "D2v 3 dom.": dict(dist=("D2", 3)),
    "D3a soglie x0,8": dict(dist=("D3", 0.8)), "D3av x0,7": dict(dist=("D3", 0.7)), "D3av x0,9": dict(dist=("D3", 0.9)),
    "D3b soglie x1,2": dict(dist=("D3", 1.2)), "D3bv x1,1": dict(dist=("D3", 1.1)), "D3bv x1,3": dict(dist=("D3", 1.3)),
    "G7 7 giorni": dict(g7=True),
}
BASE = {p: run({}, p) for p in PER}


def sig(t):
    return (t["signal"], t["side"], t.get("anchor"))


def diff(r, b):
    """Trade cambiati rispetto a W3.1: (tolti, nuovi, stessa entrata con uscita o riempimenti diversi). Nessun P&L."""
    bt = {sig(t): t for t in tl(b)}
    vt = {sig(t): t for t in tl(r)}
    gone = sorted(set(bt) - set(vt))
    new = sorted(set(vt) - set(bt))
    chg = [s for s in set(bt) & set(vt)
           if (bt[s].get("exit"), bt[s].get("reason")) != (vt[s].get("exit"), vt[s].get("reason"))
           or vt[s].get("n_fills", 1) != 1 or vt[s].get("partial", 0) or vt[s].get("tp_done", 0)]
    return gone, new, sorted(chg)


say("\nW3.1 motivi d'uscita (conteggio):", {p: dict(Counter(t.get("reason", "open") if t.get("exit") else "aperto"
                                                          for t in tl(BASE[p]))) for p in PER})
say("\nVariante | periodo | trade | tolti/nuovi/modificati vs W3.1 | eventi")
for name, cfg in V.items():
    for per in PER:
        if cfg.get("g7") is None and False:
            pass
        r = run(cfg, per)
        if cfg.get("g7"):
            n_by = {a: len(tl(rr)) for a, rr in r["runs"].items()}
            say(f"{name} | {per} | {len(tl(r))} | trade per giorno {n_by} | eventi "
                f"{dict(Counter(e['kind'] for e in r['events']))}")
            continue
        g, n, c = diff(r, BASE[per])
        evs = Counter(e["kind"] for e in r["events"])
        rs = Counter(t.get("reason") for t in r["trades"])
        say(f"{name} | {per} | {len(tl(r))} | {len(g)}/{len(n)}/{len(c)} | {dict(evs)} | uscite {dict(rs)}")
        if per == "2021+" and (g or n or c):
            say(f"   tolti {[s[0] for s in g]} nuovi {[s[0] for s in n]} modificati {[s[0] for s in c]}")

(HERE / "conteggi.txt").write_text("\n".join(OUT) + "\n")
