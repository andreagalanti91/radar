"""Test di v1.py sul giornaliero allegato (btc_giornaliero.csv) e sui file di W3.2 2018-2026."""
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import v1 as V

QUI = Path(__file__).parent
D = pd.read_csv(QUI / "btc_giornaliero.csv", index_col=0, parse_dates=True)
SIM = V.simulate(D)


def test_riproduce_lo_studio():
    m = V.metrics(SIM["equity"], SIM["trades"])
    assert m["finale_10k"] == 184406 and m["operazioni"] == 30                        # CONFRONTO_W32.md: 184.406 $, 30 operazioni
    assert round(m["cagr"] * 100, 1) == 38.8 and round(m["dd"] * 100, 1) == -49.4
    assert sum(t["verso"] == "short" for t in SIM["trades"]) == 7


def test_nessun_dato_futuro():
    full = V.signals(D)
    for cut in ("2020-03-15", "2022-06-19", "2025-04-09"):                          # una domenica e due giorni infrasettimanali
        part = V.signals(D.loc[:cut])
        pd.testing.assert_frame_equal(part, full.loc[:cut])


def test_soglie_e_isteresi():
    sc = pd.Series([0.0, 0.5, 0.3, 0.24, -0.88, -0.9, -0.3, -0.24, 0.49], pd.date_range("2024-01-01", periods=9))
    assert V.decide(sc).tolist() == [0, 1, 1, 0, 0, -1, -1, 0, 0]


def test_stato_di_oggi_e_distanze():
    e = V.evaluate(D, capital=45000.0)
    assert e["data"] == "2026-11-22" and e["posizione"] == "fuori" and abs(e["voto"] + 0.765) < 0.001
    assert e["conteggio"] == {"long": 2, "short": 15, "neutri": 0} and len(e["componenti"]) == 17
    assert e["distanze"] == {"per_long": 11, "per_short": 2}                          # long: da 2 a 13 voti; short: tutti tranne al massimo uno neutro


def test_confronto():
    eq = pd.read_csv(QUI / "w32_equity_2018_2026.csv", index_col=0, parse_dates=True)["w32_equity"]
    tw = pd.read_csv(QUI / "w32_operazioni_2018_2026.csv")
    tr = [{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()} for r in tw.to_dict("records")]
    c = V.confronto(D, eq, tr, sim=SIM)
    m = c["metriche"][0]["righe"]
    assert m["W3.2"]["finale_10k"] == 209002 and m["v1"]["finale_10k"] == 184406
    assert abs(sum(s["quota"] for s in c["accordo"]["stati"]) - 1) < 1e-9
    assert len(c["indicatori"]) == 17 and len(c["operazioni_v1"]) == 30
