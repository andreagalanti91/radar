"""Opzioni · fase 1 · segnali (nessun rendimento).

(a) Operazioni di W3.2 dal 2018-01-01 con radar.weekly.simulate (non modificato) sul frame lungo, confrontate con le 23 righe di
    research/opzioni_import/storico_prezzi_veri.csv.
(b) Serie settimanali (decisione alla chiusura UTC della domenica, ingresso lunedì) per i segnali F3 del PREREG:
    tendenza di solo prezzo, condizioni d'ingresso di W3.2 ogni settimana, volatilità realizzata 30 g, volatilità implicita
    (proxy provvisoria, sostituita da superficie.py), ampiezza delle bande settimanali, giorni di cascata, cono a 30 giorni
    (radar/cone.py, solo storia fino alla domenica).

Fonti (tutte già nel repo, nessuna modifica):
- prezzi 2014 → 2017-08 Bitstamp, 2017-08 → 2019-08 Binance spot (research/short_w2/data), 2019-09 → oggi data/spot.csv
  (frame del tool, radar.features.build_features su data/*.csv); unione con research/short_w2/short_lab.load_long.
- flusso perp pf14z: vero (CVD perp Binance, z a 180 g) dal 2020-04-12; prima un proxy dal CVD spot (2017-11-27 → 2020-04-11).
- funding: data/funding.csv dal 2020-01-01 (prima vuoto → 0 in weekly.simulate: niente uscita "distribuzione" nel 2018–19).
- open interest / long-short: data/metrics.csv dal 2021-12-01. Liquidazioni: data/liquidations.csv solo dal 2026-10-30.
- volatilità implicita (proxy per i conteggi): DVOL Deribit dal 2021-03-24, prima l'IV alla pari degli scambi Deribit della
  domenica (research/p2_nuovi/data/deribit_opt_sunday.csv) dal 2019-01-06; 2018 senza dato.
- regolamento a scadenza: apertura oraria Binance delle 08:00 UTC (cache/btc_0800.csv, op_fetch_0800.py).
Uso: python3 research/opzioni_studio/op_segnali.py [--refresh]   (scrive cache/ e stampa il confronto con le 23 operazioni)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = HERE / "cache"
sys.path.insert(0, str(ROOT))
from radar import cone as CONE  # noqa: E402
from radar import weekly as W  # noqa: E402

START = "2018-01-01"
IS_END, OOS_START = "2021-12-31", "2022-01-01"
CSV_VERI = ROOT / "research/opzioni_import/storico_prezzi_veri.csv"
P2 = ROOT / "research/p2_nuovi/data"
CONE_PATHS, CONE_Q = 2000, np.linspace(0.005, 0.995, 100)   # 100 quantili della chiusura a 30 giorni (ln)


# ------------------------------------------------------------------ dati
def frame(refresh: bool = False) -> pd.DataFrame:
    """Frame giornaliero lungo (2014 → ultimo giorno di data/spot.csv), congelato in cache/op_frame.csv.gz."""
    p = CACHE / "op_frame.csv.gz"
    if p.exists() and not refresh:
        return pd.read_csv(p, index_col=0, parse_dates=True)
    sys.path.insert(0, str(ROOT / "research/short_w2"))
    from radar.data import load_all
    from radar.features import build_features
    import short_lab
    f = build_features(load_all())
    f = f[f["close"].notna()]
    fl = short_lab.load_long(f)
    fl["pf14z_vero"] = f["pf14z"].reindex(fl.index).notna()
    CACHE.mkdir(exist_ok=True)
    fl.to_csv(p)
    return fl


def settle_0800() -> pd.Series:
    return pd.read_csv(CACHE / "btc_0800.csv", index_col=0, parse_dates=True)["open_0800"]


def iv_proxy() -> pd.DataFrame:
    """IV a 30 giorni provvisoria (decimale) alla domenica: DVOL se c'è, altrimenti IV alla pari degli scambi Deribit."""
    dv = pd.read_csv(P2 / "dvol_btc_1d.csv", index_col=0, parse_dates=True)["close"] / 100
    op = pd.read_csv(P2 / "deribit_opt_sunday.csv", index_col=0, parse_dates=True)["atm_iv"] / 100
    s = dv.reindex(op.index.union(dv.index))
    src = pd.Series(np.where(s.notna(), "dvol", "deribit_atm"), s.index)
    s = s.fillna(op)
    return pd.DataFrame({"iv": s, "fonte": src}).dropna()


# ------------------------------------------------------------------ (a) operazioni di W3.2
def w32_trades(f: pd.DataFrame) -> pd.DataFrame:
    r = W.simulate(f, start=START)
    rows = r["trades"] + ([dict(r["open"], exit=None, reason="open", pnl=r["open"]["pnl_close"])] if r["open"] else [])
    t = pd.DataFrame([{k: x.get(k) for k in ("signal", "entry", "side", "exit", "reason", "entry_px", "exit_px", "pnl", "expo")}
                      for x in rows])
    return t


def confronto_23(t: pd.DataFrame) -> pd.DataFrame:
    c = pd.read_csv(CSV_VERI)
    out = []
    for i, r in c.iterrows():
        m = t[t["entry"] == r["entra"]]
        x = m.iloc[0] if len(m) else None
        ex = None if x is None else ("aperta" if pd.isna(x["exit"]) or not x["exit"] else x["exit"])
        out.append({"n": r["n"], "verso": r["verso"], "entra_csv": r["entra"], "esce_csv": r["esce"],
                    "entra_w32": None if x is None else x["entry"], "verso_w32": None if x is None else x["side"],
                    "esce_w32": ex, "motivo": None if x is None else x["reason"],
                    "w32_csv": round(r["w32"], 4), "w32_qui": None if x is None else round(float(x["pnl"]), 4),
                    "uguale": x is not None and x["side"] == r["verso"] and ex == r["esce"]})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ (b) serie per i segnali F3
def _pct_rank(s: pd.Series, n: int | None) -> pd.Series:
    """Rango percentile del valore corrente fra gli ultimi n valori (n=None: tutta la storia fino a lì), solo passato e presente."""
    if n is None:
        return s.expanding(min_periods=52).apply(lambda a: (a <= a[-1]).mean(), raw=True)
    return s.rolling(n, min_periods=n).apply(lambda a: (a <= a[-1]).mean(), raw=True)


def cone_week(hist: pd.DataFrame, day: pd.Timestamp, horizon: int = CONE.H, n_paths: int = CONE_PATHS) -> dict:
    """Cono del tool calcolato con la sola storia fino alla chiusura di `day` (compreso): σ, deriva, quantili ln(S_T/S_0)."""
    h = hist[hist.index <= day]
    p = CONE.prepare(h)
    end, _, _ = CONE.simulate(p["zr"], p["zu"], p["zd"], p["sigma"], p["drift"], n_paths, CONE.SEED, horizon)
    return {"sigma": p["sigma"], "drift": p["drift"], "q": np.quantile(end, CONE_Q)}


def settimanale(f: pd.DataFrame) -> pd.DataFrame:
    """Una riga per domenica (decisione), colonne per i segnali F3. Tutto calcolato con dati fino alla domenica compresa."""
    w = W.weekly_bars(f[f["close"].notna()])
    c = w["close"]
    out = w[["open", "high", "low", "close", "sma", "ema20", "ema21", "atr", "flow", "fund7", "macd", "macd_sig", "trend_age"]].copy()
    # a · tendenza di solo prezzo
    e_up, e_dn = w["ema20"] > w["ema20"].shift(1), w["ema20"] < w["ema20"].shift(1)
    out["a_pend"] = np.where((c > w["sma"]) & e_up, 1, np.where((c < w["sma"]) & e_dn, -1, 0))          # EMA20 in salita/discesa
    out["a_pos"] = np.where((c > w["sma"]) & (w["ema20"] > w["sma"]), 1, np.where((c < w["sma"]) & (w["ema20"] < w["sma"]), -1, 0))
    # b · condizioni d'ingresso di W3.2 valutate ogni settimana (regime + EMA21 + flusso + F1), con soglia sul flusso
    up = (c > w["sma"]) & e_up & (c > w["ema21"]) & w["f1_ok"]
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & e_dn & (c < w["ema21"])
    for k in (0.0, 0.5, 1.0):
        out[f"b_{k:g}"] = np.where(up & (w["flow"] > k), 1, np.where(dn & (w["flow"] < -k), -1, 0))
    out["flow_vero"] = f["pf14z_vero"].astype(bool).resample("W-SUN").last().reindex(w.index).fillna(False) \
        if "pf14z_vero" in f else False
    # c · volatilità: realizzata 30 g (annua, rendimenti log chiusura-chiusura) e implicita proxy
    r = np.log(f["close"]).diff()
    rv = (r.rolling(30).std() * np.sqrt(365)).resample("W-SUN").last()
    out["rv30"] = rv.reindex(w.index)
    iv = iv_proxy()
    out["iv30"] = iv["iv"].reindex(w.index)
    out["iv_fonte"] = iv["fonte"].reindex(w.index)
    out["iv_rv"] = out["iv30"] / out["rv30"]
    out["iv_pct52"] = _pct_rank(out["iv30"].dropna(), 52).reindex(w.index)
    # d · ampiezza delle bande settimanali (Bollinger 20 settimane, 2σ) e suo rango
    m, sd = c.rolling(20).mean(), c.rolling(20).std()
    out["bbw"] = 4 * sd / m
    for n in (52, 104):
        out[f"bbw_pct{n}"] = _pct_rank(out["bbw"].dropna(), n).reindex(w.index)
    out["bbw_pctall"] = _pct_rank(out["bbw"].dropna(), None).reindex(w.index)
    # e · cascate: peggior rendimento giornaliero della settimana (chiusura-chiusura) e peggior minimo sulla chiusura precedente
    out["min_ret_cc"] = (f["close"].pct_change()).resample("W-SUN").min().reindex(w.index)
    out["min_ret_low"] = (f["low"] / f["close"].shift(1) - 1).resample("W-SUN").min().reindex(w.index)
    return out


def cono_settimanale(f: pd.DataFrame, days: pd.DatetimeIndex) -> pd.DataFrame:
    """Cono (radar/cone.py) a ogni domenica, solo con la storia fino a quel giorno; cache/op_cono.csv."""
    p = CACHE / "op_cono.csv"
    if p.exists():
        d = pd.read_csv(p, index_col=0, parse_dates=True)
        if d.index.equals(days):
            return d
    hist = CONE.history(f)
    rows = {}
    for day in days:
        c = cone_week(hist, day)
        rows[day] = {"sigma": c["sigma"], "drift": c["drift"]} | {f"q{i:02d}": v for i, v in enumerate(c["q"])}
    d = pd.DataFrame.from_dict(rows, orient="index")
    d.index.name = "date"
    d.to_csv(p)
    return d


def w32_in_pos(t: pd.DataFrame, days: pd.DatetimeIndex, last: pd.Timestamp) -> pd.Series:
    """Lato di W3.2 (+1/−1/0) in posizione nel giorno (dall'ingresso compreso all'uscita esclusa)."""
    s = pd.Series(0, index=days)
    for _, x in t.iterrows():
        a = pd.Timestamp(x["entry"])
        b = last + pd.Timedelta(days=1) if pd.isna(x["exit"]) or not x["exit"] else pd.Timestamp(x["exit"])
        s[(s.index >= a) & (s.index < b)] = 1 if x["side"] == "long" else -1
    return s


def main(refresh: bool = False) -> None:
    f = frame(refresh)
    t = w32_trades(f)
    t.to_csv(CACHE / "op_w32_trades.csv", index=False)
    cf = confronto_23(t)
    cf.to_csv(CACHE / "op_confronto_23.csv", index=False)
    s = settimanale(f)
    s = s[s.index >= pd.Timestamp(START) - pd.Timedelta(weeks=1)]
    k = cono_settimanale(f, s.index)
    s.join(k[["sigma", "drift"]].rename(columns={"sigma": "cone_sigma", "drift": "cone_drift"})).to_csv(CACHE / "op_settimanale.csv")
    print(f"frame {f.index[0].date()} → {f.index[-1].date()}  · pf14z vero dal {f.index[f['pf14z_vero'].astype(bool)].min().date()}"
          f" · funding dal {f['funding'].first_valid_index().date()}")
    print(f"W3.2 dal {START}: {len(t)} operazioni; coincidono con il CSV: {int(cf['uguale'].sum())}/{len(cf)}")
    print(cf[~cf["uguale"]].to_string(index=False))


if __name__ == "__main__":
    main("--refresh" in sys.argv)
