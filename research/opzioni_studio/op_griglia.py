"""Opzioni · griglia reale dei prezzi d'esercizio, ricavata dagli scambi Deribit campionati (dati/cache/AAAA/*.csv.gz, sola
lettura). Per ogni scadenza: prezzi d'esercizio con il giorno del primo scambio visto. strikes(D, scadenza) = quelli già visti
fino a D compreso (solo passato e giorno corrente, come la superficie). Uscita: cache/griglia.csv
"""
from __future__ import annotations

import gzip
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE / "dati" / "cache"
OUT = HERE / "cache" / "griglia.csv"
MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}


def _exp(s: str) -> str:
    return f"{2000 + int(s[-2:])}-{MON[s[-5:-2]]:02d}-{int(s[:-5]):02d}"


def build() -> pd.DataFrame:
    first: dict[tuple[str, float], str] = {}
    for p in sorted(SRC.glob("*/*.csv.gz")):
        day = p.name[:10]
        with gzip.open(p, "rt") as fh:
            d = pd.read_csv(fh, comment="#", usecols=["instrument_name"])
        for name in d["instrument_name"].unique():
            parts = name.split("-")
            if len(parts) != 4:
                continue
            k = (_exp(parts[1]), float(parts[2]))
            if k not in first or day < first[k]:
                first[k] = day
    g = pd.DataFrame([(e, k, d) for (e, k), d in first.items()], columns=["scadenza", "strike", "primo"])
    g = g.sort_values(["scadenza", "strike"])
    g.to_csv(OUT, index=False)
    return g


class Griglia:
    def __init__(self):
        g = pd.read_csv(OUT, parse_dates=["scadenza", "primo"]) if OUT.exists() else build()
        g["scadenza"], g["primo"] = pd.to_datetime(g["scadenza"]), pd.to_datetime(g["primo"])
        self.by = {e: (x["strike"].to_numpy(), x["primo"].to_numpy()) for e, x in g.groupby("scadenza")}

    def strikes(self, d, exp) -> list[float]:
        x = self.by.get(pd.Timestamp(exp))
        if x is None:
            return []
        k, p = x
        return [float(v) for v in k[p <= pd.Timestamp(d).to_datetime64()]]


if __name__ == "__main__":
    g = build()
    print(OUT, len(g), "coppie scadenza/strike;", g["scadenza"].nunique(), "scadenze")
