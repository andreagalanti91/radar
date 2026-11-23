"""Previsionale 2 · controllo di sanità (NON preregistrato, dichiarato nel README): un segnale finto iniettato al posto della
variabile `fomc` (esito futuro + rumore, AUC vera ~0,65) deve essere ritrovato dal walk-forward del modello P; lo stesso
segnale sfasato di 400 giorni no. Verifica l'allineamento della pipeline, non dice nulla sul mercato.
Uso: python3 research/previsionale2/p2_sanity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from p2_data import build, labels  # noqa: E402
import p2_run as R  # noqa: E402

rng = np.random.default_rng(113)
d0 = build()
lines = []
for h in (7, 30):
    y = labels(d0, h).fillna(0.5).to_numpy()
    sig = (y - 0.5) * 1.1 + rng.normal(size=len(y))
    for name, s in (("allineato", sig), ("sfasato 400 g", np.roll(sig, 400))):
        d = d0.copy()
        d["fomc"] = s
        w, _ = R.walk_forward(d, h)
        o = w[(w.index >= "2021-01-01") & w["y"].notna()]
        a = {pn: R.F1.auc(o.loc[x:z, "y"], o.loc[x:z, "P"]) for pn, (x, z) in (("2021-23", ("2021", "2023")), ("2024-26", ("2024", "2026")))}
        lines.append(f"h={h} segnale iniettato {name}: AUC di P 2021-23 {a['2021-23']:.3f}, 2024-26 {a['2024-26']:.3f} (AUC del segnale da solo {R.F1.auc(o['y'], d.loc[o.index, 'fomc']):.3f})")
        print(lines[-1], flush=True)
(HERE / "risultati_sanita.txt").write_text("\n".join(lines) + "\n")
