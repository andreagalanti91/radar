"""dati_nuovi · motore = W3.2 invariata (radar.weekly.simulate) + UNA regola aggiunta, senza copiare né modificare radar/weekly.py:
si avvolge weekly_bars per la sola durata della simulazione (come research/macd_sol/motore.py).

mode None : W3.2 com'è.
mode "A"  : filtro d'ingresso. Nuovo long solo se s ≠ −1; nuovo short solo se s ≠ +1 (uscite invariate).
mode "B"  : ingresso aggiuntivo. Oltre agli ingressi di W3.2, da flat si entra anche quando tutte le condizioni di PREZZO di
            W3.2 sono vere (long: regime rialzista, chiusura > EMA21, filtro F1; short: regime ribassista, chiusura < EMA21) ma il
            flusso perp ha il segno sbagliato, e la fonte conferma il verso (s = +1 per il long, −1 per lo short).
            Dimensione, stop, trailing e uscite = W3.2.
mode "E"  : ingresso ANTICIPATO long (solo miner): da flat, long anche prima del regime (senza la condizione SMA40) se la
            chiusura è sopra la EMA21, la EMA20 sale e s = +1 (finestra dopo la fine della capitolazione); flusso non richiesto.
s: Serie giornaliera {+1, 0, −1} disponibile alla data (fonti.py); si legge alla domenica della decisione.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "w32_asset2"))
from radar import weekly as W  # noqa: E402
import lib as L  # noqa: E402

END = "2026-11-24"


def frame(asset, long=False):
    """BTC: frame ufficiali di research/w32_ufficiale (lungo dal 2014 per i periodi prima del 2021, tool dal 2021).
    ETH e altri: frame di research/w32_asset2 (come macd_sol)."""
    if asset == "BTC":
        f = pd.read_csv(ROOT / "research/w32_ufficiale" / ("f_lungo.csv.gz" if long else "f_tool.csv.gz"), index_col=0, parse_dates=True)
    else:
        f = L.cfeats(asset)
    return f[f.index <= END]


def price_conds(w):
    c = w["close"]
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    pl = (up & (c > w["ema21"]) & w["f1_ok"]).fillna(False)
    ps = (dn & (c < w["ema21"])).fillna(False)
    return pl, ps


def sim(f, start, s=None, mode=None):
    orig = W.weekly_bars

    def wb(ff, _o=orig):
        w = _o(ff)
        if mode is None or s is None:
            return w
        g = s.reindex(w.index).fillna(0)
        if mode == "A":
            w["long"] = w["long"] & (g != -1)
            w["short"] = w["short"] & (g != 1)
        elif mode == "B":
            pl, ps = price_conds(w)
            w["long"] = w["long"] | (pl & (w["flow"] <= 0) & (g == 1))
            w["short"] = w["short"] | (ps & (w["flow"] >= 0) & (g == -1) & ~w["long"])
        elif mode == "E":
            early = ((w["close"] > w["ema21"]) & (w["ema20"] > w["ema20"].shift(1))).fillna(False)
            w["long"] = w["long"] | (early & (g == 1))
            w["short"] = w["short"] & ~w["long"]
        return w

    W.weekly_bars = wb
    try:
        L.setp(W)                                    # R 0,25 · k 2,5 (W3.2)
        return W.simulate(f, start=start)
    finally:
        W.weekly_bars = orig


if __name__ == "__main__":   # verifica di riproduzione senza regola
    ref = [("BTC", "2021-01-01", False, 84820), ("BTC", "2018-01-01", True, 242755), ("ETH", "2021-01-11", False, 39572)]
    for a, st, lg, v in ref:
        x = sim(frame(a, lg), st)["equity"].iloc[-1]
        print(f"{a} dal {st}: {x:,.0f} $ · riferimento {v:,} $ · {'OK' if abs(x - v) <= 1 else 'DIVERSO'}")
