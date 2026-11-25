"""Fase 2 · controllo di coerenza descrittivo del sostituto MVRV contro le finestre del grafico (PRIMA dei rendimenti).
Finestre lette dal grafico dell'utente e fissate qui prima di guardare le zone. Uso: python3 up_coerenza.py -> coerenza.txt"""
from pathlib import Path
import sys

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import up_engine as E  # noqa: E402

WIN = {"cap": [("inizio 2016", "2016-01-01", "2016-06-30"), ("12/2018–03/2019", "2018-11-15", "2019-04-15"),
               ("03/2020", "2020-03-01", "2020-04-30"), ("fine 2022", "2022-09-01", "2023-01-31"),
               ("09/2023", "2023-08-15", "2023-10-15"), ("metà 2026", "2026-06-01", "2026-07-31"),
               ("11/2026", "2026-11-01", "2026-11-24")],
       "eup": [("2017", "2017-02-01", "2017-12-31"), ("inizio 2021", "2020-12-15", "2021-04-15"),
               ("fine 2024", "2024-11-01", "2024-12-31")]}
z = E.zones(E.load_mvrv())
out = []
say = lambda s: (print(s), out.append(s))  # noqa: E731


def episodes(mask: pd.Series, gap: int = 30):
    d = mask[mask].index
    if not len(d):
        return []
    ep, s, p = [], d[0], d[0]
    for x in d[1:]:
        if (x - p).days > gap:
            ep.append((s, p))
            s = x
        p = x
    ep.append((s, p))
    return ep


for side in ("cap", "eup"):
    for dfn in ("a", "b"):
        col = f"{side}_{dfn}"
        m = z[col] & (z.index >= "2015-01-01")
        hit = 0
        say(f"\n== {col} (giorni dal 2015: {int(m.sum())}) ==")
        for nm, a, b in WIN[side]:
            n = int(m[(m.index >= a) & (m.index <= b)].sum())
            hit += n > 0
            say(f"  finestra {nm:16s} {a} → {b}: giorni in zona {n:4d} {'SI' if n else 'no'}")
        say(f"  coincidono {hit}/{len(WIN[side])}")
        say("  episodi (gap > 30 g): " + "; ".join(f"{s.date()}→{e.date()} ({int(m[s:e].sum())} g)" for s, e in episodes(m)))
say("\n== stato attuale (ultimi 10 giorni) ==")
say(z[["mvrv", "lo_b", "hi_b", "cap_a", "cap_b", "eup_a", "eup_b"]].tail(10).round(3).to_string())
mn = z.loc["2026-01-01":, "mvrv"]
say(f"MVRV 2026: minimo {mn.min():.3f} il {mn.idxmin().date()}, oggi {mn.iloc[-1]:.3f}")
(HERE / "coerenza.txt").write_text("\n".join(out) + "\n")
