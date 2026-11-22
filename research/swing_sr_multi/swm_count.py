"""Fase 1 · solo conteggi (nessun rendimento, nessuna simulazione): dati, periodi, livelli, segnali, distanze degli stop.
Uso: python3 swm_count.py  → conteggi.txt"""
from __future__ import annotations

import warnings

import numpy as np

warnings.filterwarnings("ignore")
import swm_engine as M  # noqa: E402

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


say("Conteggi senza rendimenti. Fra parentesi i segnali con stop strutturale entro il 10% (gli altri sono scartati da ST e SS).")
say("Un segnale non è un trade: con una posizione per volta i trade sono meno dei segnali.")
tot = {}
for name, (_, lab) in M.ASSETS.items():
    f = M.load(name)
    P = M.periods(f)
    yc, yj = (P["c1"] - P["c0"]).days / 365.25, (P["j1"] - P["j0"]).days / 365.25
    say(f"\n=== {name} · {lab} · dati {f.index[0].date()} → {f.index[-1].date()} ({len(f)} barre) · barre piatte (max = min) dal "
        f"{P['c0'].year}: {100*(f.high == f.low)[f.index >= P['c0']].mean():.1f}%")
    say(f"scelta {P['c0'].date()} → {P['c1'].date()} ({yc:.1f} anni; metà al {P['cm'].date()}) · giudizio {P['j0'].date()} → "
        f"{P['j1'].date()} ({yj:.1f} anni; metà al {P['jm'].date()})")
    for k in (2, 3, 4):
        S = M.signals(f, k=k)
        idx = S["idx"]
        per = {"scelta": (idx >= P["c0"]) & (idx <= P["c1"]), "giudizio": idx >= P["j0"]}
        say(f"K={k}: livelli {S['nlev']} · attivi per giorno (mediana dal {P['c0'].year}) "
            f"{int(np.median([len(a) for a, ok in zip(S['act'], idx >= P['c0']) if ok]))}")
        for pn, m in per.items():
            for e in M.ENTRIES:
                row = []
                for s, sl in ((1, "L"), (-1, "S")):
                    sg = S["sig"][(e, s)]
                    d = s * (S["C"] - S["stp"][(e, s)]) / S["C"]
                    for r in M.REGIMES:
                        q = sg & m & S["reg"][(r, s)]
                        row.append(f"{sl}{r} {int(q.sum())} ({int((q & (d <= M.E.SMAX)).sum())})")
                        if k == M.E.K:
                            tot.setdefault((pn, e, sl + r), []).append(int((q & (d <= M.E.SMAX)).sum()) / (yc if pn == "scelta" else yj))
                say(f"  {pn:8s} {e}: " + " · ".join(row))
        if k == M.E.K:
            m = idx >= P["c0"]
            d = np.concatenate([s * (S["C"] - S["stp"][(e, s)])[S["sig"][(e, s)] & m] / S["C"][S["sig"][(e, s)] & m]
                                for e in M.ENTRIES for s in (1, -1)])
            say("  distanza dello stop strutturale (tutti i segnali): quartili", " / ".join(f"{100*v:.1f}%" for v in np.percentile(d, [25, 50, 75])),
                f"· sotto 2%: {100*(d < .02).mean():.0f}% · sotto 5%: {100*(d < .05).mean():.0f}% · oltre 10%: {100*(d > .10).mean():.0f}%")
            say(f"  ATR14 giornaliero / chiusura, mediana: scelta {100*np.median((S['atr']/S['C'])[per['scelta']]):.1f}% · giudizio "
                f"{100*np.median((S['atr']/S['C'])[per['giudizio']]):.1f}%")
            for r in ("R1",):
                say("  giorni in regime R1: " + " · ".join(f"{sl} {pn} {100*S['reg'][(r, s)][mm].mean():.0f}%" for s, sl in ((1, "long"), (-1, "short"))
                                                           for pn, mm in per.items()))
say("\n=== Segnali per anno con stop entro il 10% (K=3): mediana fra i 15 asset [minimo–massimo]")
for (pn, e, key), v in sorted(tot.items()):
    say(f"  {pn:8s} {e} {key}: {np.median(v):5.1f} [{min(v):.1f}–{max(v):.1f}]")
(M.HERE / "conteggi.txt").write_text("\n".join(OUT) + "\n")
