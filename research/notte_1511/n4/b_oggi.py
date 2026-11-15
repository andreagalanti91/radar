"""N4 · range S/R di oggi (radar/levels.compute sui dati fino all'ultima chiusura) con la statistica storica di tenuta (b_tenuta.csv)
e assemblaggio di oggi.json (parte A da a_oggi.json). Uso: python b_oggi.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from n4_data import raw  # noqa: E402
from b_sr import bucket  # noqa: E402
from radar import levels  # noqa: E402


def stat(S, sc, side, typ, b):
    x = S[(S.scala == sc) & (S.lato == side) & (S.tipo == typ) & (S.distanza == b)]
    if not len(x):
        return None
    r = x.iloc[0]
    return {"P_tenuta": round(r.P_tenuta, 3), "P_casuale": round(r.P_tenuta_casuale, 3), "diff_punti": round(r["diff"] * 100, 1),
            "IC95_diff": [round(r.ic_lo * 100, 1), round(r.ic_hi * 100, 1)], "tocchi": int(r.n_tocchi),
            "P_tocco": round(r.P_tocco, 3)}


def main():
    f = raw()
    lv = levels.compute(f)
    S = pd.read_csv(HERE / "b_tenuta.csv")
    px, atr = lv["price"], lv["atr"]
    zones = []
    for z in lv["supports"] + lv["resistances"]:
        side = z["kind"]
        typ = "W" if z["weekly"] else ("V" if z["touches"] == 0 else "G")
        dist = abs(z["price"] / px - 1)
        b = bucket(dist)
        e = {"tipo_zona": side, "centro": z["price"], "fascia": [round(z["lo"] - 0.25 * atr), round(z["hi"] + 0.25 * atr)],
             "zona_tool": [z["lo"], z["hi"]], "distanza_pct": z["dist_pct"], "tipo": {"W": "settimanale", "G": "giornaliero", "V": "nodo di volume"}[typ],
             "forza": z.get("strength"), "tocchi": z["touches"], "ultimo_tocco": z["last"], "volume_pct": z["volume"]}
        if b:
            e["storico"] = {sc: stat(S, sc, side, typ, b) for sc in ("D3", "D6", "W10")}
            e["storico_tutti_i_tipi"] = {sc: stat(S, sc, side, "tutti", b) for sc in ("D3", "W10")}
        else:
            e["storico"] = "oltre il 15%: fuori dal test"
        zones.append(e)
    A = json.loads((HERE / "a_oggi.json").read_text())
    out = {"generato": "15/11/2026 (dati fino al " + lv["date"] + ")", "prezzo_chiusura": px, "atr_giornaliero": atr,
           "A_probabilita": A, "B_supporti_resistenze": zones,
           "avvertenze": ["Nessuna cella supera la correzione per test multipli (BH q 0,10) in IS: le probabilità sono descrittive.",
                          "La tenuta storica dei livelli è confrontata con livelli casuali alla stessa distanza: vedi diff_punti e IC.",
                          "OI del 14/11 stimato con la variazione OKX (archivio Binance non ancora pubblicato)."]}
    (HERE / "oggi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    pd.DataFrame([{k: v for k, v in z.items() if not isinstance(v, dict)} for z in zones]).to_csv(HERE / "b_oggi_livelli.csv", index=False)
    for z in zones:
        st = z["storico"]
        d3 = st.get("D3") if isinstance(st, dict) else None
        print(z["tipo_zona"], z["fascia"], z["distanza_pct"], z["tipo"], z["forza"], d3)


if __name__ == "__main__":
    main()
