"""Dorito indicator = Leledc Exhaustion Bar (glaz) / Leledc levels (InSilico).

Porting della funzione Pine pubblica (open source su TradingView):
    bindex += close > close[4];  sindex += close < close[4]
    if bindex > bars and close < open and high >= highest(high, len): bindex = 0 -> -1 (triangolo rosso, in alto)
    elif sindex > bars and close > open and low <= lowest(low, len): sindex = 0 -> +1 (triangolo sotto)
InSilico "Leledc levels (IS)": len 40, bars 10 (default letti dai metadati della pagina TradingView).
glaz "Leledc Exhaustion Bar": major 6/30 (default), minor 5/5. In glaz i due if sono indipendenti (niente else):
se scattano entrambi vince +1; qui il parametro `elif_` replica le due versioni.
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def daily(include_partial=False):
    """Candele giornaliere UTC: f_long (dal 2014) fino al 31/08/2019, data/spot.csv (Binance) dopo,
    Binance pubblico (data-api.binance.vision) per i giorni successivi all'ultimo di spot.csv."""
    fl = pd.read_csv(os.path.join(ROOT, "research/p2_nuovi/data/f_long.csv.gz"), parse_dates=["date"])
    sp = pd.read_csv(os.path.join(ROOT, "data/spot.csv"), parse_dates=["date"])
    a = fl[fl.date < sp.date.min()][["date", "open", "high", "low", "close"]]
    b = sp[["date", "open", "high", "low", "close"]]
    rows = json.load(open(os.path.join(HERE, "data/binance_1d_nov2026.json")))
    c = pd.DataFrame([[pd.Timestamp(k[0], unit="ms"), *map(float, k[1:5])] for k in rows],
                     columns=["date", "open", "high", "low", "close"])
    c = c[c.date > b.date.max()]
    if not include_partial:
        c = c[c.date < pd.Timestamp("2026-11-26")]  # 26/11 ancora aperta allo scarico (21:51 UTC)
    d = pd.concat([a, b, c]).drop_duplicates("date").sort_values("date").set_index("date")
    return d


def resample(d, days, phase=0):
    """Barre di `days` giorni. phase = (giorni dall'epoca 1970-01-01 dell'apertura) mod days.
    days=7 con phase=4 -> settimane che aprono il lunedi."""
    if days == 1:
        return d.copy()
    ep = (d.index - pd.Timestamp("1970-01-01")).days
    key = (ep - phase) // days
    g = d.groupby(key)
    out = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(),
                        "close": g.close.last(), "n": g.close.size()})
    out.index = pd.to_datetime([d.index[key == k][0] for k in out.index])
    out.index.name = "date"
    return out


def resample_year(d, days):
    """Barre di `days` giorni ricominciate ogni 1 gennaio (come appaiono le barre 3D di TradingView sul grafico
    dello screenshot: la griglia 2025 e quella 2026 differiscono di fase). L'ultima barra dell'anno puo essere corta."""
    if days == 1:
        return d.copy()
    doy = d.index.dayofyear - 1
    key = d.index.year * 1000 + doy // days
    g = d.groupby(key)
    out = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(),
                        "close": g.close.last(), "n": g.close.size()})
    first = pd.Series(d.index, index=d.index).groupby(key).first()
    out.index = pd.to_datetime(first.loc[out.index].values)
    out.index.name = "date"
    return out


def lele(df, bars, length, elif_=True):
    o, h, l, c = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    n = len(c)
    hh = pd.Series(h).rolling(length, min_periods=length).max().to_numpy()
    ll = pd.Series(l).rolling(length, min_periods=length).min().to_numpy()
    bi = si = 0
    out = np.zeros(n, int)
    for t in range(n):
        if t >= 4:
            if c[t] > c[t - 4]:
                bi += 1
            if c[t] < c[t - 4]:
                si += 1
        r = 0
        up = bi > bars and c[t] < o[t] and not np.isnan(hh[t]) and h[t] >= hh[t]
        if up:
            bi = 0
            r = -1
        if (not up or not elif_) and si > bars and c[t] > o[t] and not np.isnan(ll[t]) and l[t] <= ll[t]:
            si = 0
            r = 1
        out[t] = r
    return pd.Series(out, index=df.index)


VARIANTS = {
    "IS_40_10": dict(bars=10, length=40, elif_=True),    # InSilico, primaria
    "glaz_maj_30_6": dict(bars=6, length=30, elif_=False),  # glaz, major (default)
}
