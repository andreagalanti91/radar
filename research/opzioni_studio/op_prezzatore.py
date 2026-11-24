"""Opzioni · fase 2 · prezzatore sulla superficie Deribit (superficie.py, sola lettura) per op_engine.

Istante di ogni data: le 12:00 UTC (ADDENDUM-1 punto 3). F = apertura oraria Binance delle 12:00 di quel giorno
(cache/btc_0800.csv, colonna open_1200): la superficie va sempre chiamata con il prezzo del momento. Scadenze: solo i venerdì
di superficie.scadenze(D). Griglia: op_griglia (prezzi d'esercizio già scambiati fino a D). Regolamento: apertura oraria
Binance delle 08:00. Cache dei prezzi in memoria (stessa chiamata, stesso risultato).
"""
from __future__ import annotations

import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import superficie as SU  # noqa: E402
from op_griglia import Griglia  # noqa: E402


class PrezzatoreSuperficie:
    ora = 12.0

    def __init__(self):
        h = pd.read_csv(HERE / "cache" / "btc_0800.csv", index_col=0, parse_dates=True)
        full = pd.date_range(h.index[0], h.index[-1])
        # 8 giorni senza candela oraria Binance (2018-02-08/09, 2018-06-26, 2018-10-19, 2018-11-14, 2019-05-15, 2019-08-15,
        # 2021-09-29) e un mezzogiorno (2020-02-19): interpolazione nel tempo fra le ore vicine
        self.s12 = h["open_1200"].reindex(full).interpolate("time")
        self.s8 = h["open_0800"].reindex(full).interpolate("time")
        self.g = Griglia()
        self.qual = Counter()          # qualità delle chiamate di prezzo (tutte, comprese le valutazioni giornaliere)

    def spot(self, data):
        return float(self.s12[pd.Timestamp(data).normalize()])

    @lru_cache(maxsize=None)
    def _scad(self, d):
        return [pd.Timestamp(s) for s in SU.scadenze(d.date()) if s.weekday() == 4]

    def scadenze(self, data):
        return self._scad(pd.Timestamp(data).normalize())

    def strikes(self, data, scadenza):
        return self.g.strikes(data, scadenza)

    def iv(self, data, scadenza, strike, tipo):
        d = pd.Timestamp(data)
        return SU.iv(d.date(), pd.Timestamp(scadenza).date(), float(strike), tipo, F=self.spot(d), ora=self.ora)

    @lru_cache(maxsize=None)
    def _prezzo(self, d, e, K, tipo):
        v, q = SU.prezzo(d.date(), e.date(), K, tipo, F=self.spot(d), ora=self.ora)
        return (None if not np.isfinite(v) else float(v)), q

    def prezzo(self, data, scadenza, strike, tipo):
        v, q = self._prezzo(pd.Timestamp(data).normalize(), pd.Timestamp(scadenza).normalize(), float(strike), tipo)
        self.qual[q] += 1
        return v, q

    def regolamento(self, scadenza):
        return float(self.s8[pd.Timestamp(scadenza).normalize()])
