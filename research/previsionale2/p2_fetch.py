"""Previsionale 2 · scarico dei dati di politica economica (PREREG §1). FRED fredgraph.csv (pubblico, senza chiave) e date
FOMC in calendario. Scrive research/previsionale2/data/. Uso: python3 research/previsionale2/p2_fetch.py
Date FOMC 2015–2020: giorno della decisione delle riunioni IN CALENDARIO, dalle pagine ufficiali
federalreserve.gov/monetarypolicy/fomchistoricalYYYY.htm (la riunione del 17–18/03/2020 era in calendario ed è stata
sostituita da quella straordinaria del 15/03: resta, perché prima era nota; le straordinarie sono escluse). Dal 2021: stesso
file di research/notte_1511/n3/data/fomc_dates.csv (calendario ufficiale).
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SERIES = ["DFF", "WALCL", "WTREGEN", "RRPONTSYD", "DGS10", "DGS2", "DFII10", "DTWEXBGS", "VIXCLS", "CPIAUCNS", "M2SL"]
FOMC_1520 = """2015-01-28 2015-03-18 2015-04-29 2015-06-17 2015-07-29 2015-09-17 2015-10-28 2015-12-16
2016-01-27 2016-03-16 2016-04-27 2016-06-15 2016-07-27 2016-09-21 2016-11-02 2016-12-14
2017-02-01 2017-03-15 2017-05-03 2017-06-14 2017-07-26 2017-09-20 2017-11-01 2017-12-13
2018-01-31 2018-03-21 2018-05-02 2018-06-13 2018-08-01 2018-09-26 2018-11-08 2018-12-19
2019-01-30 2019-03-20 2019-05-01 2019-06-19 2019-07-31 2019-09-18 2019-10-30 2019-12-11
2020-01-29 2020-03-18 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16""".split()


def main() -> None:
    DATA.mkdir(exist_ok=True)
    for s in SERIES:
        try:   # curl: dal container la libreria requests non attraversa il proxy, curl sì
            subprocess.run(["curl", "-sS", "-f", "-m", "90", "-o", str(DATA / f"{s}.tmp"),
                            f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}"], check=True)
            d = pd.read_csv(DATA / f"{s}.tmp")
            (DATA / f"{s}.tmp").unlink()
            d.columns = ["date", s]
            d.to_csv(DATA / f"{s}.csv", index=False)
            print(s, d["date"].iloc[0], d["date"].iloc[-1], len(d))
        except Exception as e:  # noqa: BLE001
            print(s, "NON SCARICATA:", type(e).__name__, e)
        time.sleep(0.5)
    n3 = pd.read_csv(HERE.parents[0] / "notte_1511" / "n3" / "data" / "fomc_dates.csv")["date"].tolist()
    pd.DataFrame({"date": sorted(set(FOMC_1520) | set(n3))}).to_csv(DATA / "fomc_dates.csv", index=False)
    print("FOMC", len(FOMC_1520), "+", len(n3))


if __name__ == "__main__":
    main()
