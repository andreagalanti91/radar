"""Previsionale · probabilità attuali a 7 e 30 giorni con i dati più recenti del repo (data/*.csv). SOLO ESEMPIO: non entra
nel giudizio. Legge radar.data.load_all e radar.features.build_features (nessuna rete, nessuna modifica a radar/).
Uso: python3 research/previsionale/fc_oggi.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from fc_data import ALL, features, frozen, labels  # noqa: E402
from fc_models import predict, train  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402


def main() -> None:
    f = build_features(load_all())
    f = f[f["close"].notna()]
    _, fl = frozen()
    pre = fl[fl.index < f.index[0]]
    b = pd.concat([pre[["open", "high", "low", "close"]], f[["open", "high", "low", "close"]]])
    b["pf14z"] = f["pf14z"].reindex(b.index).fillna(fl["pf14z"].reindex(b.index))
    for c in ("sf14z", "funding_z", "oi_chg7"):
        b[c] = f[c].reindex(b.index)
    fng = pd.read_csv(ROOT / "data" / "fng.csv", index_col=0, parse_dates=True)["fng"]
    b["fng"] = fng.reindex(b.index).ffill(limit=2)
    x = features(b)
    t = x.index[-1]
    out = {"data_chiusura": str(t.date()), "close": float(x["close"].iloc[-1]),
           "variabili": {c: (None if not np.isfinite(x[c].iloc[-1]) else round(float(x[c].iloc[-1]), 4)) for c in ALL}}
    for h in (7, 30):
        mod = train(x, labels(x, h), h, t + pd.Timedelta(days=1))
        p = predict(mod, x.loc[[t], ALL].to_numpy(float))[0]
        out[f"h{h}"] = {"p_M1": round(float(p[0]), 3), "p_M2": round(float(p[1]), 3), "p_M3": round(float(p[2]), 3), "p_M4": round(float(p[3]), 3),
                        "base_addestramento": round(mod["base"], 3), "addestrato_fino_a": mod["until"],
                        "chiamata": "su" if p[3] > 0.55 else ("giù" if p[3] < 0.45 else "incerto")}
    (HERE / "oggi.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
