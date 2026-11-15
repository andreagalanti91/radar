"""N4 · stato di oggi per la parte A: in quali celle ammissibili si trova l'ultima chiusura e con quali probabilità storiche.
Uso: python a_oggi.py → a_oggi_celle.csv (tutte le celle che contengono oggi), stampa il riassunto in JSON
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from n4_data import VARS, build  # noqa: E402

PRINCIPALE = ["REG", "PFt", "SFt"]          # regime + flusso perp + flusso spot (domanda dell'utente)


def main():
    df, f = build()
    last = df.index[-1]
    st = {v: (None if pd.isna(df[v].iloc[-1]) else str(df[v].iloc[-1])) for v in VARS}
    raw = {k[2:]: round(float(df[k].iloc[-1]), 3) for k in df.columns if k.startswith("x_") and pd.notna(df[k].iloc[-1])}
    A = pd.read_csv(HERE / "a_celle.csv")

    def match(c):
        return all(st.get(kv.split("=")[0]) == kv.split("=")[1] for kv in c.split(" & "))

    O = A[A.cella.map(match)].copy()
    O.to_csv(HERE / "a_oggi_celle.csv", index=False, float_format="%.4g")
    out = {"data_chiusura": str(last.date()), "prezzo": round(float(df["close"].iloc[-1]), 0), "stato": st, "valori": raw,
           "celle_ammissibili_che_contengono_oggi": int(O.cella.nunique())}
    # cella principale: la più ricca fra REG×PFt×SFt e i suoi sottoinsiemi ammissibili
    cand = [" & ".join(f"{v}={st[v]}" for v in c) for c in (PRINCIPALE, ["PFt", "SFt"], ["REG", "PFt"], ["REG", "SFt"])]
    princ = next((c for c in cand if c in set(O.cella)), None)
    out["cella_principale"] = princ
    out["nota_cella"] = ("REG×PFt×SFt di oggi non ammissibile (< 40 osservazioni indipendenti): usata la combinazione più ricca disponibile"
                         if princ != cand[0] else "")
    for h in (7, 14, 30):
        x = O[O.h == h]
        r = {"base_P": round(float(x.base_P.iloc[0]), 3), "base_media_pct": round(float(x.base_m.iloc[0]) * 100, 2),
             "mediana_P_celle_di_oggi": round(float(x.P.median()), 3),
             "quota_celle_sopra_base": round(float((x.P > x.base_P).mean()), 2)}
        if princ:
            p = x[x.cella == princ].iloc[0]
            r["principale"] = {"P": round(p.P, 3), "IC95": [round(p.P_lo, 3), round(p.P_hi, 3)], "media_pct": round(p.media * 100, 2),
                               "IC95_media_pct": [round(p.m_lo * 100, 2), round(p.m_hi * 100, 2)], "P_IS": round(p.P_is, 3),
                               "P_OOS": round(p.P_oos, 3), "n_ind7": int(p.n_ind7)}
        one = x[~x.cella.str.contains("&")]
        r["singole"] = {c: {"P": round(p, 3), "IC95": [round(a, 3), round(b, 3)], "media_pct": round(m * 100, 2)}
                        for c, p, a, b, m in zip(one.cella, one.P, one.P_lo, one.P_hi, one.media)}
        out[f"h{h}"] = r
    js = json.dumps(out, ensure_ascii=False, indent=1)
    (HERE / "a_oggi.json").write_text(js)
    print(js)


if __name__ == "__main__":
    main()
