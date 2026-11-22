"""Fase 2 · CONTEGGIO degli eventi (nessun rendimento, P&L o esito di trade). Output: conteggi.txt. Uso: python3 sw_count.py"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sw_engine as E  # noqa: E402

F, FL = E.frames()
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


PER = {"2014-17": (FL, "2014-06-01", "2017-12-31"), "2018-20": (FL, "2018-01-01", "2020-12-31"),
       "2021-23": (F, "2021-01-01", "2023-12-31"), "2024-26": (F, "2024-01-01", "2026-11-15")}
say("Dati: frame lungo", FL.index[0].date(), "→", FL.index[-1].date(), "· frame del tool", F.index[0].date(), "→", F.index[-1].date())
# coerenza dei prezzi fra i due frame nel 2021+
j = F.index.intersection(FL.index)
j = j[j >= "2021-01-01"]
say("Chiusure 2021+ identiche nei due frame:", bool(np.allclose(F.loc[j, "close"], FL.loc[j, "close"], rtol=1e-4)))

for k in (2, 3, 4):
    say(f"\n== K = {k} settimane per lato (livelli attivi {E.LIFE} settimane) ==")
    for name, x in (("lungo", FL), ("tool", F)):
        S = E.signals(x, k=k)
        nact = np.array([len(a) for a in S["act"]])
        say(f"frame {name}: {S['nlev']} livelli · attivi per giorno mediana {int(np.median(nact[nact > 0]))}")
    SL, ST = E.signals(FL, k=k), E.signals(F, k=k)
    say("segnali grezzi (giorni con segnale; stop strutturale ≤ 10% fra parentesi) per periodo, tipo, lato e regime")
    for per, (x, a, b) in PER.items():
        S = SL if x is FL else ST
        m = (S["idx"] >= a) & (S["idx"] <= b)
        for e in E.ENTRIES:
            row = []
            for s, lab in ((1, "L"), (-1, "S")):
                sg = S["sig"][(e, s)]
                d = s * (S["C"] - S["stp"][(e, s)]) / S["C"]
                for r in E.REGIMES:
                    q = sg & m & S["reg"][(r, s)]
                    row.append(f"{lab}{r} {int(q.sum())} ({int((q & (d <= E.SMAX)).sum())})")
            say(f"  {per} {e}: " + " · ".join(row))
    if k == E.K:
        d = np.concatenate([s * (ST["C"] - ST["stp"][(e, s)])[ST["sig"][(e, s)]] / ST["C"][ST["sig"][(e, s)]]
                            for e in E.ENTRIES for s in (1, -1)])
        say("distanza dello stop strutturale (tutti i segnali, frame del tool): quartili",
            " / ".join(f"{100*v:.1f}%" for v in np.percentile(d, [25, 50, 75])), f"· sotto 5%: {100*(d < .05).mean():.0f}%",
            f"· oltre 10%: {100*(d > .10).mean():.0f}%")
        for r in ("R1", "R2"):
            for s, lab in ((1, "long"), (-1, "short")):
                say(f"giorni in regime {r} {lab} 2021+: {100*ST['reg'][(r, s)][ST['idx'] >= '2021-01-01'].mean():.0f}%",
                    f"· 2014–20: {100*SL['reg'][(r, s)][(SL['idx'] >= '2014-06-01') & (SL['idx'] <= '2020-12-31')].mean():.0f}%")
(HERE / "conteggi.txt").write_text("\n".join(OUT) + "\n")
