"""Previsionale 2 · stato attuale di regime e politica economica e probabilità dei modelli R, P, RP con i dati più recenti
del repo (data/*.csv) e di FRED (data/ di questa cartella). SOLO ESEMPIO: non entra nel giudizio. Nessuna rete.
Uso: python3 research/previsionale2/p2_oggi.py (dopo p2_run.py)
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
from p2_data import POL, build, labels  # noqa: E402
from p2_run import MAIN, MINREL, QHI, QLO, predict, train  # noqa: E402
from fc_data import features, frozen  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402


def latest_x() -> pd.DataFrame:
    """Come fc_oggi.main del primo ciclo: dati congelati fino all'inizio di data/, poi data/ del repo."""
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
    return features(b)


def main() -> None:
    d = build(latest_x())
    t = d.index[-1]
    r = d.loc[t]
    tasso = "RIALZO" if r["pol"] > 0.125 else ("TAGLIO" if r["pol"] < -0.125 else "FERMO")
    bil = "QE" if r["walcl13"] > 1 else ("QT" if r["walcl13"] < -1 else "STABILE")
    out = {"data_chiusura": str(t.date()), "close": float(r["close"]),
           "regime": {"T": r["T"], "V": r["V"], "close_su_sma200": round(float(r["close"] / r["sma200"] - 1), 3), "vol30": round(float(r["vol30"]), 4)},
           "politica": {"tasso": tasso, "bilancio": bil, "dff": float(r["dff"]), "walcl13_pct": round(float(r["walcl13"]), 2),
                        "ry": float(r["ry"]), "vix_livello": float(r["vixlvl"]), "cpi_annuo": float(r["cpi_yoy"]),
                        "giorni_al_fomc": int(r["fomc_days"]), **{c: round(float(r[c]), 3) for c in POL}},
           "flusso": {c: round(float(r[c]), 3) for c in ("pf", "sf", "rsi", "vol")}}
    for h in (7, 30):
        mod = train(d, labels(d, h), h, t + pd.Timedelta(days=1))
        p = predict(mod, d.loc[[t]]).iloc[0]
        past = pd.read_csv(HERE / f"prob2_h{h}.csv", index_col=0, parse_dates=True)
        o = {"base_complessiva": round(mod["base"], 3), "base_del_regime": round(float(p["p0c"]), 3)}
        for m in MAIN + ["PF"]:
            q = past.loc[past["T"] == r["T"], m]
            q = q if len(q) >= MINREL else past[m]
            lo, hi = np.quantile(q, [QLO, QHI])
            o[m] = {"p": round(float(p[m]), 3), "soglie_relative": [round(float(lo), 3), round(float(hi), 3)],
                    "chiamata": "su" if p[m] >= hi else ("giù" if p[m] <= lo else "incerto")}
        out[f"h{h}"] = o
    (HERE / "oggi.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
