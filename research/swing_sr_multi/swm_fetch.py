"""Swing S/R multi-asset · dati mancanti (SPY, QQQ, petrolio) dalla stessa fonte pubblica di research/multi_asset/fetch.py
(Yahoo chart API, stesso User-Agent dichiarato, stesso taglio 2026-11-20, stessa rettifica split+dividendi). Uso: python3 swm_fetch.py
Salva in research/swing_sr_multi/data/. Non tocca research/multi_asset/data/."""
from __future__ import annotations

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "multi_asset"))
import fetch as F  # noqa: E402

NEW = {"SPY": "SPY", "QQQ": "QQQ", "BRENT": "BZ=F", "WTI": "CL=F", "USO": "USO"}

if __name__ == "__main__":
    for name, sym in NEW.items():
        try:
            df = F.yahoo(sym)
            df.to_csv(HERE / "data" / f"{name}.csv.gz")
            print(f"{name:6s} {sym:5s} {df.index[0].date()} -> {df.index[-1].date()} {len(df):6d} righe")
        except Exception as e:  # noqa: BLE001
            print(name, sym, "ERRORE", e)
        time.sleep(0.5)
