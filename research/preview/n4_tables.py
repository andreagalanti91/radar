"""Tabelle fisse per la sezione "Oggi" della pre-analisi (radar/preview.py), derivate dallo studio N4 del 15/11/2026.
Nessun ricalcolo: si leggono i CSV di research/notte_1511/n4/ e si scrivono due JSON piccoli in research/preview/.
- analog.json: P(rendimento > 0) a 7 e 30 giorni per le 9 celle pf14z × sf14z a terzili fissi (±0,43, come N4) e per i terzili
  singoli (ripiego se una variabile manca), con IC 95% (bootstrap a blocchi) e media a 7 giorni; base di tutto il periodo.
- sr_hold.json: tenuta storica dei livelli del tool (D3 giornaliero ±3% e W10 settimanale ±10%) per lato, tipo e distanza,
  contro livelli casuali alla stessa distanza e larghezza (b_tenuta.csv).
Uso: python3 research/preview/n4_tables.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
N4 = HERE.parent / "notte_1511" / "n4"


def _pct(x: float, d: int = 1) -> float:
    return round(float(x) * 100, d)


def analog() -> dict:
    A = pd.read_csv(N4 / "a_celle.csv")
    A = A[A["h"].isin([7, 30])]
    names = [f"PFt={p} & SFt={s}" for p in ("lo", "mid", "hi") for s in ("lo", "mid", "hi")]
    names += [f"PFt={t}" for t in ("lo", "mid", "hi")] + [f"SFt={t}" for t in ("lo", "mid", "hi")]
    cells = {}
    for nm in names:
        x = A[A["cella"] == nm].set_index("h")
        if not {7, 30} <= set(x.index):
            continue
        r7, r30 = x.loc[7], x.loc[30]
        cells[nm] = {"n_ind7": int(r7["n_ind7"]), "days": int(r7["n"]),
                     "p7": _pct(r7["P"]), "ci7": [_pct(r7["P_lo"]), _pct(r7["P_hi"])],
                     "p30": _pct(r30["P"]), "ci30": [_pct(r30["P_lo"]), _pct(r30["P_hi"])],
                     "mean7": _pct(r7["media"], 2), "p7_is": _pct(r7["P_is"]), "p7_oos": _pct(r7["P_oos"])}
    b7, b30 = A[A["h"] == 7].iloc[0], A[A["h"] == 30].iloc[0]
    return {"source": "research/notte_1511/n4/a_celle.csv (studio N4 del 15/11/2026, dati 01/01/2021 → ottobre 2026). "
                      "P = P(rendimento > 0) in %, IC 95% bootstrap a blocchi di 30 giorni; n_ind7 = osservazioni indipendenti a 7 giorni.",
            "thresholds": {"lo": -0.43, "hi": 0.43},
            "base": {"p7": _pct(b7["base_P"]), "p30": _pct(b30["base_P"]), "mean7": _pct(b7["base_m"], 2)},
            "verdict": "0 celle su 5.790 test superano la correzione per test multipli (lezione 97): solo descrizione.",
            "cells": cells}


def sr_hold() -> dict:
    B = pd.read_csv(N4 / "b_tenuta.csv")
    B = B[B["scala"].isin(["D3", "W10"])]
    rows = [{"scale": r.scala, "side": r.lato, "type": r.tipo, "dist": r.distanza, "touches": int(r.n_tocchi),
             "hold_pct": _pct(r.P_tenuta), "random_pct": _pct(r.P_tenuta_casuale), "diff_pts": _pct(r["diff"]),
             "ci_diff": [_pct(r.ic_lo), _pct(r.ic_hi)]} for _, r in B.iterrows()]
    return {"source": "research/notte_1511/n4/b_tenuta.csv (studio N4 del 15/11/2026, 743 zone reali contro 14.860 casuali). "
                      "Tenuta = rimbalzo di x% oltre la zona prima di una chiusura x% oltre il lato opposto, dopo il primo tocco "
                      "(D3: x = 3% in 30 giorni; W10: x = 10% in 12 settimane). Tipi: G giornaliero, W settimanale, V nodo di volume.",
            "verdict": "0/72 test superano la correzione: i livelli tengono come livelli casuali alla stessa distanza (lezione 97).",
            "rows": rows}


def main() -> None:
    (HERE / "analog.json").write_text(json.dumps(analog(), ensure_ascii=False, indent=1) + "\n")
    (HERE / "sr_hold.json").write_text(json.dumps(sr_hold(), ensure_ascii=False, indent=1) + "\n")
    print("scritti analog.json e sr_hold.json")


if __name__ == "__main__":
    main()
