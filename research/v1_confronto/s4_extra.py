"""Punto 3, aggiunte: 50/50 ribilanciato ogni giorno (come nel confronto dell'utente) e v1 a pari drawdown di W3.2."""
import numpy as np
import pandas as pd
import s3_confronto as C   # riesegue s3 (stessi dati) e riusa serie e funzioni

out = []
for lab, a, b in C.PER[:5]:
    for nm, ew in (("Radar", C.EW), ("utente", C.EU)):
        rw, rv = ew.loc[a:b].pct_change().fillna(0), C.EV.loc[a:b].pct_change().fillna(0)
        reb = (1 + 0.5 * rw + 0.5 * rv).cumprod()
        sep = C.p5050(ew, C.EV, a, b)
        out.append(f"{lab:<34} W3.2 {nm:<6} | 50/50 separati {C.fmt(C.met(sep))} | ribilanciato ogni giorno {C.fmt(C.met(reb))}")
    # v1 a pari drawdown: esposizione k costante (resto in liquidità a 0%)
    dw = C.met(C.EW, None, a, b)["dd"]
    rv = C.EV.loc[a:b].pct_change().fillna(0)
    ks = np.linspace(0.05, 1.0, 96)
    dds = [C.met((1 + k * rv).cumprod())["dd"] for k in ks]
    k = ks[np.argmin([abs(x - dw) if x >= dw else 9 for x in dds])]
    out.append(f"{lab:<34} v1 a pari DD di W3.2 ({100*dw:.1f}%): esposizione {k:.2f}x -> {C.fmt(C.met((1 + k * rv).cumprod()))} | W3.2 {C.fmt(C.met(C.EW, None, a, b))}")
print("\n".join(out))
open(C.HERE / "risultati_extra.txt", "w").write("\n".join(out) + "\n")
