"""Controllo del wrapper (primo passo dopo il commit del PREREG): con i dati e i costi di BTC swm_engine deve riprodurre
research/swing_sr/risultati.txt. Uso: python3 swm_check.py  → controllo.txt"""
from __future__ import annotations

import warnings

warnings.filterwarnings("ignore")
import swm_engine as M  # noqa: E402

F, _ = M.E.frames()
S = M.signals(F)
out = []
for cfg, want in ((("X", "R1", "LS", "SS", "TSR"), 5626), (("B", "R2", "LS", "SF", "TSR"), 21611)):
    m = M.metrics(M.simulate(S, cfg, "2021-01-01", cost="btc"))
    out.append(f"BTC {'/'.join(cfg)} dal 2021 con il wrapper e i costi di BTC: {m['fin']:,} $ · DD {100*m['dd']:.1f}% · trade {m['n']} · "
               f"PF {m['pf']:.2f} (atteso {want:,} $) → {'OK' if m['fin'] == want else 'DIVERSO'}")
    assert m["fin"] == want
m = M.metrics(M.simulate(S, ("X", "R1", "LS", "SS", "TSR"), "2021-01-01", cost="std"))
out.append(f"Stessa serie BTC con i costi 'std' (0,05% + 0,05%), solo per mostrare l'effetto dei costi: {m['fin']:,} $")
assert (M.W.FEE_SPOT, M.W.FEE_PERP, M.W.SLIP) == M.COSTS["btc"]
out.append("Costi di radar.weekly ripristinati dopo ogni chiamata: True")
print("\n".join(out))
(M.HERE / "controllo.txt").write_text("\n".join(out) + "\n")
