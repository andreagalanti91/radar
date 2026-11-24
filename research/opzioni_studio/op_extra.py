"""Opzioni · fase 2 · descrittivi aggiunti dopo op_fase2 (nessun effetto sui verdetti): B0 con scadenza ad almeno 21 giorni
(lo studio dell'utente stava fra 25 e 46), e B0 senza 2018. Aggiunge una sezione in fondo a risultati.txt."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import op_engine as E  # noqa: E402
import op_fase2 as F  # noqa: E402
from op_prezzatore import PrezzatoreSuperficie  # noqa: E402


def main() -> None:
    F.PZ = PrezzatoreSuperficie()
    tr = pd.read_csv(HERE / "cache" / "op_w32_trades.csv")
    pw = E.piano_w32(tr, F.DAYS)
    store = {}
    F.corri(E.Conf(), pw, "B0", store)
    F.corri(E.Conf(min_giorni=21), pw, "B0 scadenza ≥ 21 giorni", store)
    F.corri(E.Conf(min_giorni=21, spread_k=0.20), pw, "Spread −20% con scadenza ≥ 21 giorni", store)
    F.OUT.clear()
    F.say("")
    F.say("== DESCRITTIVI AGGIUNTIVI (op_extra.py, dopo i verdetti): scelta della scadenza")
    F.tabella("B0 con il venerdì più vicino a 30 giorni (regola) contro il più vicino fra quelli ad almeno 21 giorni", store, list(store))
    d = F.ops_df(store["B0 scadenza ≥ 21 giorni"]["dal 2018"])
    F.say("giorni alla scadenza (≥ 21): " + ", ".join(f"{x.entra}: {x.giorni:.0f}" for x in d.itertuples()))
    with open(HERE / "risultati.txt", "a", encoding="utf-8") as fh:
        fh.write("\n".join(F.OUT) + "\n")


if __name__ == "__main__":
    main()
