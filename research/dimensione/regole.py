"""dimensione · REGOLE (codice dei segnali, da committare insieme a PREREG.md, prima di qualsiasi rendimento di variante).

Idea: invece di bloccare gli ingressi di W3.2, si RIDUCE LA DIMENSIONE di alcune operazioni. Segnali, uscite, stop e trailing di
W3.2 restano identici (la dimensione non entra in nessuna decisione di radar/weekly.py): cambia solo il rischio allo stop
iniziale dell'operazione toccata, R = 0,125 invece di 0,25 (esposizione = min(1, R / (2,5·ATRw / chiusura)), come in W3.2).

Varianti (PREREG.md §3), tutte lette alla domenica della decisione, stessi parametri su tutti gli asset:
  D1 "affollato"  long con OI Binance (USD) a 28 g sopra il 90° percentile dei 365 g precedenti OPPURE funding 7 g (lo stesso
                  fund7 che W3.2 usa per la distribuzione) sopra il 90° percentile dei 365 g precedenti E sopra il tasso neutro
                  di Binance (0,01% ogni 8 h = 0,0003 al giorno: a quel livello il premio dei perp è zero, nessun affollamento).
  D2 "giovane"    long nelle prime 3 settimane sopra la SMA40 (trend_age ≤ 3, la stessa età che W3.2 usa per F1).
  D3              D1 ∪ D2.
  D4 "short tardo" short aperto con la chiusura oltre il 35% sotto la SMA40 (chiusura/SMA40 − 1 < −0,35).

Ritardi: OI = valore del sabato (archivio Binance metrics del giorno dopo, come il flusso perp); fund7 = come in weekly_bars.
Percentile: valore corrente > quantile q dei 365 valori giornalieri PRECEDENTI (escluso il giorno), almeno 180 valori validi;
altrimenti la condizione è falsa (buco dichiarato: niente dato = nessuna riduzione).
Questo file non modifica radar/weekly.py: lo avvolge per la sola durata della simulazione (come research/dati_nuovi/motore.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "dati_nuovi"))
sys.path.insert(0, str(ROOT / "research" / "w32_asset2"))
from radar import weekly as W  # noqa: E402
import motore as M  # noqa: E402  (frame() e verifica di riproduzione)
import lib as L  # noqa: E402

END = M.END
R_BASE, R_RID = 0.25, 0.125
# parametri preregistrati e vicini (PREREG §3-§5)
PAR = {"D1": 0.90, "D2": 3, "D3": (0.90, 3), "D4": 0.35}
VICINI = {"D1": [0.80, 0.95], "D2": [2, 4], "D3": [(0.80, 2), (0.95, 4)], "D4": [0.30, 0.40]}
WIN, MINOBS = 365, 180
FUND_NEUTRO = 0.0003                                  # componente "interesse" del funding Binance: 0,01% × 3 al giorno


# ------------------------------------------------------------------ dati
def frame(asset, long=False):
    return M.frame(asset, long)


def _pct_flag(x: pd.Series, q: float) -> pd.Series:
    """True se x[t] > quantile q dei WIN valori precedenti (escluso t), con almeno MINOBS valori validi."""
    thr = x.shift(1).rolling(WIN, min_periods=MINOBS).quantile(q)
    return (x > thr) & thr.notna() & x.notna()


def oi_chg28(asset: str) -> pd.Series:
    m = pd.read_csv(ROOT / "data" / ("metrics.csv" if asset == "BTC" else "eth_metrics.csv"), parse_dates=["date"])
    s = m.set_index("date")["oi_usd"].astype(float).sort_index()
    s = s.reindex(pd.date_range(s.index[0], END)).ffill(limit=3)
    return (s / s.shift(28) - 1).shift(1)            # valore del sabato alla decisione della domenica


def fund7(f: pd.DataFrame) -> pd.Series:
    """Come weekly_bars (rolling 7 del funding giornaliero) ma senza riempire con zero i giorni senza dato."""
    return f["funding"].rolling(7, min_periods=7).mean()


def weekly(f: pd.DataFrame) -> pd.DataFrame:
    L.setp(W)
    return W.weekly_bars(f[f["close"].notna()])


# ------------------------------------------------------------------ condizioni (Serie booleane sulle domeniche)
def affollato(f, asset, q):
    w = weekly(f)
    oi = _pct_flag(oi_chg28(asset), q).reindex(w.index).fillna(False)
    f7 = fund7(f)
    fu = (_pct_flag(f7, q) & (f7 > FUND_NEUTRO + 1e-9)).reindex(w.index).fillna(False)
    return oi | fu, oi, fu


def giovane(f, n):
    w = weekly(f)
    return (w["trend_age"] <= n) & (w["trend_age"] >= 1)


def short_tardo(f, d):
    w = weekly(f)
    return (w["close"] / w["sma"] - 1) < -d


def fattore(v: str, f: pd.DataFrame, asset: str, par=None) -> pd.Series:
    """Serie sulle domeniche: R da usare SE in quella domenica nasce un ingresso (R_RID dove la regola scatta, altrimenti R_BASE).
    Le regole D1–D3 toccano solo i long, D4 solo gli short (il lato si applica in sim())."""
    par = PAR[v] if par is None else par
    if v == "D1":
        c = affollato(f, asset, par)[0]
    elif v == "D2":
        c = giovane(f, par)
    elif v == "D3":
        c = affollato(f, asset, par[0])[0] | giovane(f, par[1])
    elif v == "D4":
        c = short_tardo(f, par)
    else:
        raise ValueError(v)
    return c.fillna(False)


LATO = {"D1": 1, "D2": 1, "D3": 1, "D4": -1}


# ------------------------------------------------------------------ motore: W3.2 + dimensione ridotta
def sim(f: pd.DataFrame, start: str, cond: pd.Series | None = None, lato: int = 1, dates: set | None = None):
    """W3.2 invariata; l'operazione nata alla domenica d (segnale) usa R_RID se cond[d] è vero e il lato coincide
    (oppure se d è in `dates`, usato dal placebo). Senza cond/dates = W3.2."""
    f = f[f.index <= END]
    orig_wb, orig_ex = W.weekly_bars, W.exposure
    key = {}

    def wb(ff, _o=orig_wb):
        w = _o(ff)
        for d, c, a in zip(w.index, w["close"].to_numpy(float), w["atr"].to_numpy(float)):
            key[(c, a)] = d
        return w

    def ex(sg, close, atr, lev=1.0):
        d = key.get((float(close), float(atr)))
        hit = False
        if d is not None:
            if dates is not None:
                hit = d in dates
            elif cond is not None:
                hit = bool(cond.get(d, False)) and sg == lato
        r = R_RID if hit else (W.R_LONG if sg > 0 else W.R_SHORT)
        return lev * min(1.0, r / (W.STOP_K * atr / close))

    W.weekly_bars, W.exposure = wb, ex
    try:
        L.setp(W)                                    # R 0,25 · k 2,5 (W3.2)
        return W.simulate(f, start=start)
    finally:
        W.weekly_bars, W.exposure = orig_wb, orig_ex


def toccate(o: dict, cond: pd.Series, lato: int) -> list:
    """Operazioni (chiuse + aperta) il cui segnale cade in una domenica con cond vero, sul lato giusto."""
    tr = o["trades"] + ([o["open"]] if o["open"] else [])
    sg = {"long": 1, "short": -1}
    return [t for t in tr if sg[t["side"]] == lato and bool(cond.get(pd.Timestamp(t["signal"]), False))]


if __name__ == "__main__":   # verifica: senza regola e con regola "mai vera" = W3.2 (nessun rendimento di varianti)
    ref = [("BTC", "2021-01-01", False, 84820), ("BTC", "2018-01-01", True, 242755), ("ETH", "2021-01-11", False, 39572)]
    for a, st, lg, v in ref:
        f = frame(a, lg)
        x = sim(f, st)["equity"].iloc[-1]
        y = sim(f, st, cond=pd.Series(False, index=weekly(f).index))["equity"].iloc[-1]
        z = M.sim(f, st)["equity"].iloc[-1]
        ok = abs(x - v) <= 1 and abs(y - v) <= 1 and abs(z - v) <= 1
        print(f"{a} dal {st}: avvolto {x:,.0f} · cond falsa {y:,.0f} · motore dati_nuovi {z:,.0f} · riferimento {v:,} $ · "
              f"{'OK' if ok else 'DIVERSO'}")
