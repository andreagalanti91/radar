"""Parte 2 · congela i dati giornalieri usati dalla ricerca (fase 1, 18/11/2026).

- f_repo.csv.gz: frame giornaliero del tool (radar.features.build_features su data/*.csv), 2019-09 → 2026-11-15.
- f_long.csv.gz: frame lungo 2014 → 2026-11-15 (research/short_w2/short_lab.load_long: Bitstamp/Binance + CVD spot come
  proxy del flusso prima del 2019-09), per il campione 2018–20.
- load(): frame + dati esterni (DVOL, opzioni della domenica, ETHBTC, BTCDOM) già allineati per data.
Non modifica radar/. Il motore W3 resta radar.weekly.simulate.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D = HERE / "data"
CUT = "2026-11-15"   # ultima candela settimanale chiusa (domenica): W3 flat, 10k -> 78.474 $


def freeze() -> None:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "research" / "short_w2"))
    from radar.data import load_all
    from radar.features import build_features
    import short_lab
    f = build_features(load_all())
    f = f[f["close"].notna() & (f.index <= CUT)]
    fl = short_lab.load_long(f)
    fl = fl[fl.index <= CUT]
    f.to_csv(D / "f_repo.csv.gz")
    fl.to_csv(D / "f_long.csv.gz")
    print("f_repo", f.index[0].date(), f.index[-1].date(), len(f), "| f_long", fl.index[0].date(), fl.index[-1].date(), len(fl))


def load() -> dict[str, pd.DataFrame]:
    rd = lambda n: pd.read_csv(D / n, index_col=0, parse_dates=True)  # noqa: E731
    out = {"f": rd("f_repo.csv.gz"), "fl": rd("f_long.csv.gz"), "dvol": rd("dvol_btc_1d.csv"),
           "ethbtc": rd("ethbtc_1d.csv"), "btcdom": rd("btcdom_1d.csv")}
    p = D / "deribit_opt_sunday.csv"
    if p.exists():
        out["opt"] = rd("deribit_opt_sunday.csv")
    return out


if __name__ == "__main__":
    freeze()
