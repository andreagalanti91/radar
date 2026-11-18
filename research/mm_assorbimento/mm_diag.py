"""Diagnostica descrittiva (nessun rendimento): quante barre superano ogni passo della definizione di assorbimento.
Uso: python research/mm_assorbimento/mm_diag.py  → diag.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mm_data import load  # noqa: E402

d = load()
out = []
for tag, X in (("1h", d["H"]), ("4h", d["B4"])):
    X = X.dropna(subset=["vol_pct", "rng_pct", "D"])
    sg = np.sign(X["D"])
    out.append(f"{tag}: barre valutabili {len(X)}, correlazione log(volume)–log(range) "
               f"{np.corrcoef(np.log(X['vol']), np.log(X['rng'] + 1e-9))[0, 1]:.2f}")
    for vp, rp in ((80, 30), (90, 20)):
        m = (X["vol_pct"] >= vp) & (X["rng_pct"] <= rp)
        m1 = m & (X["D"].abs() >= 0.10); m1b = m & (X["D"].abs() >= 0.05)
        m2 = m1 & (np.sign(X["dS"]) == sg) & (np.sign(X["dP"]) == sg); m2b = m1b & (np.sign(X["dS"]) == sg) & (np.sign(X["dP"]) == sg)
        m3 = m2 & (X["dOI"] > 0)
        out.append(f"  volume ≥ {vp}° e range ≤ {rp}°: {int(m.sum())} · |D| ≥ 0,10: {int(m1.sum())} · delta concordi: {int(m2.sum())}"
                   f" · ΔOI > 0: {int(m3.sum())} (vicino largo |D| ≥ 0,05 senza OI: {int(m2b.sum())})")
    for vp, rp in ((80, 50), (70, 30), (70, 50)):
        m = (X["vol_pct"] >= vp) & (X["rng_pct"] <= rp)
        out.append(f"  (solo conteggio, non testato) volume ≥ {vp}° e range ≤ {rp}°: {int(m.sum())}")
txt = "\n".join(out)
print(txt)
(HERE / "diag.txt").write_text(txt + "\n")
