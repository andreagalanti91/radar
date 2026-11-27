"""dati_nuovi · costruzione dei segnali delle fonti nuove (definizioni fissate in PREREG.md, nessun rendimento qui).

Ogni funzione restituisce una Serie giornaliera già "disponibile alla data": il valore all'indice d è quello che si poteva
conoscere alla chiusura della domenica d (ritardi di pubblicazione applicati). Il segnale settimanale è il valore alla domenica.
Segnale s ∈ {+1 rialzista, 0 neutro/assente, −1 ribassista}.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D = HERE / "data"
IDX = pd.date_range("2016-01-01", "2026-11-30")

# finestre di pubblicazione ritardata del COT (shutdown del governo USA): i report con data nel periodo si considerano
# disponibili solo dalla data indicata (approssimazione prudente, vedi PREREG §2a)
COT_LATE = [("2018-12-18", "2019-03-01", "2019-03-08"), ("2025-09-30", "2026-01-13", "2026-01-23")]


def _sign(x):
    return np.sign(x).fillna(0).astype(int)


def _daily(s, lag_days):
    s = s.sort_index(); s = s[~s.index.duplicated(keep="last")]
    s = s.reindex(IDX.union(s.index)).ffill(limit=10).reindex(IDX)
    return s.shift(lag_days)


# ------------------------------------------------------------------ (a) COT CFTC · asset manager CME
def cot_level(asset):
    d = pd.read_csv(D / "cot" / f"{asset}_CME.csv")
    t = pd.to_datetime(d["report_date_as_yyyy_mm_dd"].str[:10])
    oi = pd.to_numeric(d["open_interest_all"], errors="coerce")
    am = (pd.to_numeric(d["asset_mgr_positions_long"], errors="coerce") - pd.to_numeric(d["asset_mgr_positions_short"], errors="coerce")) / oi
    pub = t + pd.Timedelta(days=3)                                   # martedì → venerdì
    for a, b, rel in COT_LATE:
        m = (t >= a) & (t <= b); pub[m] = pd.Timestamp(rel)
    return pd.DataFrame({"report": t, "pub": pub, "am_net": am.values}).sort_values("report").reset_index(drop=True)


def cot_signal(asset, n=4):
    """s = segno della variazione della posizione netta degli asset manager (% OI) rispetto a n report prima.
    Disponibile dalla domenica successiva al venerdì di pubblicazione."""
    x = cot_level(asset)
    x["chg"] = x["am_net"] - x["am_net"].shift(n)
    known = x.dropna(subset=["chg"])
    # se un report vecchio esce dopo uno più nuovo (backlog), conta l'ultimo per data di report fra quelli pubblicati
    out = pd.Series(np.nan, index=IDX)
    pubs = known["pub"].values; reps = known["report"].values; vals = np.sign(known["chg"].values)
    for d in IDX:
        m = pubs <= np.datetime64(d)
        if m.any():
            out[d] = vals[m][np.argmax(reps[m])]
    return out.fillna(0).astype(int)


# ------------------------------------------------------------------ (b) base dei future Deribit (trimestrale vs perpetual)
def basis_daily(asset, min_days=14):
    q = pd.read_csv(D / "basis" / f"deribit_{asset}_quarterly.csv", parse_dates=["t", "expiry"])
    p = pd.read_csv(D / "basis" / f"deribit_{asset}_perp.csv", parse_dates=["t"])
    q["d"] = q["t"].dt.normalize(); p["d"] = p["t"].dt.normalize()
    q["dte"] = (q["expiry"] + pd.Timedelta(hours=8) - (q["t"] + pd.Timedelta(days=1))).dt.total_seconds() / 86400
    q = q[q["dte"] >= min_days].sort_values(["d", "dte"]).groupby("d").first()       # trimestrale più vicina con ≥ 14 gg
    perp = p.set_index("d")["close"]
    j = q.join(perp.rename("perp"), how="inner")
    b = (j["close"] / j["perp"] - 1) * 365 / j["dte"]
    return b                                                              # indice = giorno d'apertura della candela (08:00 UTC)


def basis_signal(asset, n=28):
    """s = segno della variazione a n giorni della base annualizzata (media 7 giorni). Candela del giorno d (08:00→08:00)
    chiusa il giorno d+1: disponibile alla domenica se d ≤ sabato → ritardo 1 giorno."""
    b7 = basis_daily(asset).rolling(7, min_periods=5).mean()
    return _sign(_daily(b7, 1) - _daily(b7, 1).shift(n)).astype(int)


# ------------------------------------------------------------------ (c) funding medio multi-exchange
def funding_daily(asset, binance=None):
    """Funding giornaliero (somma del giorno, unità di data/funding.csv) per borsa; media semplice delle borse disponibili."""
    cols = {}
    if binance is not None:
        cols["binance"] = binance
    de = pd.read_csv(D / "funding" / f"deribit_{asset}.csv")
    de["d"] = pd.to_datetime(de["timestamp"], unit="ms").dt.normalize()
    cols["deribit"] = de.groupby("d")["interest_8h"].mean() * 3
    hl = pd.read_csv(D / "funding" / f"hyperliquid_{asset}.csv")
    hl["d"] = pd.to_datetime(hl["time"], unit="ms").dt.normalize()
    g = hl.groupby("d")["fundingRate"]
    cols["hyperliquid"] = g.sum()[g.count() >= 20]
    df = pd.DataFrame(cols)
    return df, df.mean(axis=1, skipna=True)


def funding_signal(asset, binance, hi=0.90, lo=0.10, win=365):
    """s = −1 se il funding medio a 7 giorni è ≥ percentile hi dei 365 giorni precedenti (long affollati), +1 se ≤ lo, 0 altrimenti.
    Ritardo 1 giorno (come il flusso di W3.2)."""
    _, avg = funding_daily(asset, binance)
    f7 = avg.rolling(7, min_periods=5).mean()
    f7 = _daily(f7, 1)
    r = f7.rolling(win, min_periods=180).rank(pct=True)
    s = pd.Series(0, index=IDX)
    s[r >= hi] = -1; s[r <= lo] = 1
    return s.astype(int)


def funding_signal_b(asset, binance, hi=0.90, win=365):
    """B · s = +1 se il funding medio a 7 giorni è sotto zero (short che pagano: carburante per una salita), −1 se ≥ percentile hi
    dei 365 giorni precedenti (long affollati), 0 altrimenti. Ritardo 1 giorno."""
    _, avg = funding_daily(asset, binance)
    f7 = _daily(avg.rolling(7, min_periods=5).mean(), 1)
    r = f7.rolling(win, min_periods=180).rank(pct=True)
    s = pd.Series(0, index=IDX)
    s[r >= hi] = -1; s[f7 < 0] = 1
    return s.astype(int)


# ------------------------------------------------------------------ (d) miner · hash ribbon (blockchain.com)
def hash_ribbon(a=30, b=60):
    """segno(SMA a − SMA b) della potenza di calcolo BTC (blockchain.com); ritardo 2 giorni. −1 = capitolazione dei miner."""
    h = pd.read_csv(D / "miner" / "hash-rate.csv", parse_dates=["date"]).set_index("date")["hash-rate"]
    h = h.asfreq("D").interpolate(limit=3)
    s = h.rolling(a).mean() - h.rolling(b).mean()
    return _sign(_daily(s, 2)).astype(int)


def hash_signal(a=30, b=60):
    """A · s = −1 durante la capitolazione (ribbon −1), 0 altrimenti: blocca solo i nuovi long (gli short non sono toccati).
    Usato anche per ETH (segnale di mercato: ETH non ha miner dal 09/2022)."""
    r = hash_ribbon(a, b)
    return (-(r == -1).astype(int)).astype(int)


def hash_signal_b(a=30, b=60, weeks=8):
    """B · s = +1 nelle `weeks` settimane dopo la fine di una capitolazione (ribbon da −1 a +1), 0 altrimenti."""
    r = hash_ribbon(a, b)
    end = (r == 1) & (r.shift(1) == -1)
    s = pd.Series(0, index=IDX)
    for d in r.index[end]:
        s.loc[d:d + pd.Timedelta(weeks=weeks)] = 1
    return s.astype(int)


# ------------------------------------------------------------------ (e) flussi verso gli exchange (CoinMetrics, metriche "flash")
def _cm(asset):
    d = pd.read_csv(D / "cmflows" / f"{asset.lower()}_flows.csv", parse_dates=["date"]).set_index("date")
    return d


def cm_netflow_signal(asset, n=7):
    """A · s = −segno della somma a n giorni dei flussi netti verso gli exchange (entrate − uscite): afflusso = pressione in vendita."""
    d = _cm(asset)
    nf = (d["FlowInExNtv"] - d["FlowOutExNtv"]).rolling(n, min_periods=n).sum()
    return (-_sign(_daily(nf, 1))).astype(int)


def cm_balance_signal(asset, n=28):
    """B · s = −segno della variazione a n giorni del saldo sugli exchange (SplyExNtv): saldo in calo = accumulo."""
    d = _cm(asset)
    sp = _daily(d["SplyExNtv"], 1)
    return (-_sign(sp - sp.shift(n))).astype(int)
