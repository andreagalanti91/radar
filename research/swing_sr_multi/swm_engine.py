"""Swing S/R multi-asset · wrapper di research/swing_sr/sw_engine.py (importato, NON modificato). 22/11/2026.

Cosa cambia rispetto a BTC, senza toccare le regole del motore:
- costi: sw_engine legge FEE_SPOT, FEE_PERP e SLIP da radar.weekly al momento della simulazione; qui vengono sostituiti in
  memoria solo per la durata della chiamata (`costs`) e poi ripristinati. Profilo "std" (azioni, ETF): commissione 0,05% per
  lato, slippage 0,05% su ingressi a mercato e stop, TP come ordine limite senza slippage. Profilo "btc": i valori di W3.1.
- funding: colonna a zero (lo short non paga funding; il costo del prestito titoli NON è modellato);
- flusso perp: colonna vuota, quindi il regime R2 non ha mai segnali e non viene usato (REGIMES = R0, R1).
Le candele settimanali restano W-SUN: per i mercati chiusi nel fine settimana la settimana lun–ven è chiusa il venerdì e il
livello/regime è usabile dal lunedì. RET (20) e ATR14 sono in giorni di borsa.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "swing_sr"))
import sw_engine as E  # noqa: E402

W = E.W
COSTS = {"btc": (W.FEE_SPOT, W.FEE_PERP, W.SLIP), "std": (0.0005, 0.0005, 0.0005), "zero": (0.0, 0.0, 0.0),
         "x2": (0.001, 0.001, 0.001)}
ENTRIES, REGIMES, SIDES, STOPS, TPS = E.ENTRIES, ("R0", "R1"), E.SIDES, E.STOPS, E.TPS
END = "2026-11-20"
# nome -> (file, etichetta). ETF e azioni: OHLC rettificati per split e dividendi (Yahoo, adjclose/close).
MA, OWN = HERE.parent / "multi_asset" / "data", HERE / "data"
ASSETS = {"SPY": (OWN, "S&P 500 (ETF SPY)"), "QQQ": (OWN, "Nasdaq 100 (ETF QQQ)"), "GLD": (MA, "Oro (ETF GLD)"),
          "SLV": (MA, "Argento (ETF SLV)"), "USO": (OWN, "Petrolio WTI (ETF USO)"),
          "AAPL": (MA, "Apple"), "AMZN": (MA, "Amazon"), "AVGO": (MA, "Broadcom"), "BRK-B": (MA, "Berkshire B"),
          "GOOGL": (MA, "Alphabet"), "LLY": (MA, "Eli Lilly"), "META": (MA, "Meta"), "MSFT": (MA, "Microsoft"),
          "NVDA": (MA, "Nvidia"), "TSLA": (MA, "Tesla")}
CH0, JUDGE, MINCH = pd.Timestamp("1996-01-01"), pd.Timestamp("2016-01-01"), 8.0


def load(name: str) -> pd.DataFrame:
    d = pd.read_csv(ASSETS[name][0] / f"{name}.csv.gz", index_col=0, parse_dates=True)
    d = d[d.index <= END][["open", "high", "low", "close"]].copy()
    d["funding"], d["pf14z"] = 0.0, float("nan")
    return d


def periods(f: pd.DataFrame) -> dict:
    """Scelta e giudizio fissati dalla sola lunghezza della storia (regola del PREREG):
    scelta da max(primo dato + 52 settimane, 1996-01-01); giudizio dal 2016-01-01 se la scelta dura almeno 8 anni, altrimenti
    dal punto di mezzo fra inizio della scelta e ultimo dato. Ogni periodo è diviso in due metà per il criterio dei PF."""
    a, z = max(f.index[0] + pd.Timedelta(weeks=52), CH0), f.index[-1]
    j = JUDGE if (JUDGE - a).days / 365.25 >= MINCH else (a + (z - a) / 2).normalize()
    jm = pd.Timestamp("2021-01-01") if j == JUDGE else (j + (z - j) / 2).normalize()
    cm = (a + (j - a) / 2).normalize()
    d = pd.Timedelta(days=1)
    return dict(c0=a, c1=j - d, cm=cm, j0=j, jm=jm, j1=z)


@contextmanager
def costs(profile: str = "std"):
    old = (W.FEE_SPOT, W.FEE_PERP, W.SLIP)
    W.FEE_SPOT, W.FEE_PERP, W.SLIP = COSTS[profile]
    try:
        yield
    finally:
        W.FEE_SPOT, W.FEE_PERP, W.SLIP = old


def signals(f: pd.DataFrame, **kw) -> dict:
    return E.signals(f, **kw)


def simulate(S: dict, cfg: tuple, start, end=None, cost: str = "std", **kw) -> dict:
    with costs(cost):
        return E.simulate(S, *cfg, start=str(pd.Timestamp(start).date()), end=None if end is None else str(pd.Timestamp(end).date()), **kw)


metrics = E.metrics
