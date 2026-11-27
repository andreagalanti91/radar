"""Opzioni e direzione · fase 1 · costruzione degli indicatori (NESSUN rendimento futuro qui).

Uso: python3 costruisci.py   (dentro research/opzioni_direzione/, dopo scarica.py)

Prodotti in dati/:
  settimanale_<CUR>.csv   una riga per domenica (decisione di W3.2 alla chiusura della domenica, 24:00 UTC):
      rr25, iv_p25, iv_c25, iv_atm, scad, gg, n_p25, n_c25, n_atm, rr25s (fascia 0,20-0,30)  (scadenza 20-50 g più vicina a 30, giornata intera)
      pc_vol, pc_buy, vol_c, vol_p, buy_c, buy_p, scambi            (tutte le scadenze, giornata intera)
      dvol, dvol_d7                                                 (chiusura giornaliera DVOL della domenica; ln rapporto a 7 g)
      pc_camp7 (solo BTC)                                           (rapporto put/call del campione 3 finestre/giorno, lun-dom)
  vol_strike_campione.csv.gz   quantità per (giorno, scadenza, strike, tipo) dal campione di research/opzioni_studio
  maxpain.csv            una riga per scadenza mensile BTC 2021-01 → 2026-10: proxy del massimo dolore a E-7 e E-3
  validazione_maxpain.csv  proxy contro massimo dolore da open interest vero (istantanea Deribit di oggi)
"""
import datetime as dt
import glob
import gzip
import json
import math
import os

import numpy as np
import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.path.join(QUI, "dati")
CAMPIONE = os.path.join(QUI, "..", "opzioni_studio", "dati", "cache")
MESI = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def nome(n):
    _, s, k, t = n.split("-")
    return dt.date(2000 + int(s[-2:]), MESI[s[-5:-2]], int(s[:-5])), float(k), t


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def leggi(p):
    with gzip.open(p, "rt") as f:
        meta = json.loads(f.readline()[1:])
        df = pd.read_csv(f)
    return meta, df


def mediana_pesata(v, w):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return float(v[o][np.searchsorted(c, 0.5 * c[-1])])


def domenica(p):
    """Indicatori di una domenica intera. Riferimento: domenica 24:00 UTC."""
    meta, df = leggi(p)
    d = dt.date.fromisoformat(os.path.basename(p)[:10])
    out = {"data": d.isoformat(), "scambi": len(df)}
    if df.empty:
        return out
    info = {n: nome(n) for n in df["instrument_name"].unique()}
    df["scad"] = df["instrument_name"].map(lambda n: info[n][0])
    df["K"] = df["instrument_name"].map(lambda n: info[n][1])
    df["tipo"] = df["instrument_name"].map(lambda n: info[n][2])
    df = df[(df["amount"] > 0) & (df["index_price"] > 0)]
    c, pu = df["tipo"] == "C", df["tipo"] == "P"
    buy = df["direction"] == "buy"
    out.update(vol_c=df.loc[c, "amount"].sum(), vol_p=df.loc[pu, "amount"].sum(),
               buy_c=df.loc[c & buy, "amount"].sum(), buy_p=df.loc[pu & buy, "amount"].sum())
    out["pc_vol"] = out["vol_p"] / out["vol_c"] if out["vol_c"] > 0 else np.nan
    out["pc_buy"] = out["buy_p"] / out["buy_c"] if out["buy_c"] > 0 else np.nan
    # skew 25-delta sulla scadenza 20-50 g più vicina a 30 g dalla domenica 24:00
    rif = dt.datetime.combine(d + dt.timedelta(days=1), dt.time(0))
    gg = {s: (dt.datetime.combine(s, dt.time(8)) - rif).total_seconds() / 86400 for s in df["scad"].unique()}
    cand = [s for s, g in gg.items() if 20 <= g <= 50]
    if not cand:
        return out
    s = min(cand, key=lambda x: (abs(gg[x] - 30), gg[x]))
    g = df[(df["scad"] == s) & (df["iv"] > 1) & (df["iv"] < 500)].copy()
    t_ms = pd.Timestamp(dt.datetime.combine(s, dt.time(8)), tz="UTC").value // 10**6
    T = (t_ms - g["timestamp"].values) / (365 * 86_400_000)
    sig = g["iv"].values / 100
    d1 = (np.log(g["index_price"].values / g["K"].values) + 0.5 * sig**2 * T) / (sig * np.sqrt(T))
    nd1 = np.array([ncdf(x) for x in d1])
    g["delta"] = np.where(g["tipo"] == "C", nd1, nd1 - 1)
    out.update(scad=s.isoformat(), gg=round(gg[s], 2))
    for k, m in (("c25", (g["tipo"] == "C") & g["delta"].between(0.15, 0.35)),
                 ("p25", (g["tipo"] == "P") & g["delta"].between(-0.35, -0.15)),
                 ("atm", g["delta"].abs().between(0.40, 0.60)),
                 ("c25s", (g["tipo"] == "C") & g["delta"].between(0.20, 0.30)),   # vicino: fascia stretta
                 ("p25s", (g["tipo"] == "P") & g["delta"].between(-0.30, -0.20))):
        x = g[m]
        out["n_" + k] = len(x)
        out["iv_" + k] = mediana_pesata(x["iv"].values, x["amount"].values.astype(float)) if len(x) >= 5 else np.nan
    out["rr25"] = out["iv_p25"] - out["iv_c25"]
    out["rr25s"] = out["iv_p25s"] - out["iv_c25s"]
    return out


def campione_per_strike():
    """Aggrega il campione (3 finestre da 1000 scambi al giorno) per giorno, scadenza, strike, tipo. Dal 2020-01-01."""
    p_out = os.path.join(DATI, "vol_strike_campione.csv.gz")
    if os.path.exists(p_out):
        return pd.read_csv(p_out)
    parti = []
    for p in sorted(glob.glob(os.path.join(CAMPIONE, "*", "*.csv.gz"))):
        d = os.path.basename(p)[:10]
        if d < "2020-01-01":
            continue
        _, df = leggi(p)
        if df.empty:
            continue
        df = df[df["amount"] > 0]
        info = {n: nome(n) for n in df["instrument_name"].unique()}
        df["scad"] = df["instrument_name"].map(lambda n: info[n][0].isoformat())
        df["K"] = df["instrument_name"].map(lambda n: info[n][1])
        df["tipo"] = df["instrument_name"].map(lambda n: info[n][2])
        a = df.groupby(["scad", "K", "tipo"], as_index=False)["amount"].sum()
        a.insert(0, "data", d)
        parti.append(a)
    v = pd.concat(parti, ignore_index=True)
    v.to_csv(p_out, index=False, compression="gzip")
    return v


def max_pain(oi):
    """oi: DataFrame K, tipo, q. Strike (fra quelli quotati) che minimizza il valore intrinseco totale per chi ha comprato."""
    ks = np.sort(oi["K"].unique())
    c = oi[oi["tipo"] == "C"].groupby("K")["q"].sum().reindex(ks, fill_value=0).values
    p = oi[oi["tipo"] == "P"].groupby("K")["q"].sum().reindex(ks, fill_value=0).values
    dolore = [(c * np.maximum(x - ks, 0)).sum() + (p * np.maximum(ks - x, 0)).sum() for x in ks]
    return float(ks[int(np.argmin(dolore))])


def ultimo_venerdi(y, m):
    d = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - 4) % 7)


def proxy(v, scad, fino, finestra=None):
    """Pseudo open interest = quantità del campione per strike della scadenza nei giorni <= fino (da quotazione o ultimi N g)."""
    x = v[(v["scad"] == scad) & (v["data"] <= fino)]
    if finestra:
        x = x[x["data"] > (dt.date.fromisoformat(fino) - dt.timedelta(days=finestra)).isoformat()]
    return x.rename(columns={"amount": "q"})


def main():
    # --- domeniche (entrambe le valute) ---
    for cur in ("BTC", "ETH"):
        file = sorted(glob.glob(os.path.join(DATI, "domeniche", cur, "*.csv.gz")))
        w = pd.DataFrame([domenica(p) for p in file])
        dv = pd.read_csv(os.path.join(DATI, f"dvol_{cur}_1D.csv"))
        dv["data"] = dv["t"].str[:10]
        dv = dv.set_index("data")["close"]
        w["dvol"] = w["data"].map(dv)
        w["dvol_d7"] = np.log(w["dvol"] / w["data"].map(
            lambda d: dv.get((dt.date.fromisoformat(d) - dt.timedelta(days=7)).isoformat(), np.nan)))
        if cur == "BTC":
            v = campione_per_strike()
            gt = v.groupby(["data", "tipo"])["amount"].sum().unstack()

            def pc7(d):
                d0 = (dt.date.fromisoformat(d) - dt.timedelta(days=6)).isoformat()
                x = gt.loc[(gt.index >= d0) & (gt.index <= d)]
                return x["P"].sum() / x["C"].sum() if len(x) == 7 else np.nan
            w["pc_camp7"] = w["data"].map(pc7)
        w.to_csv(os.path.join(DATI, f"settimanale_{cur}.csv"), index=False)
        print(cur, len(w), "domeniche")

    # --- massimo dolore (proxy) per le scadenze mensili BTC ---
    v = campione_per_strike()
    righe = []
    for y in range(2021, 2027):
        for m in range(1, 13):
            E = ultimo_venerdi(y, m)
            if E > dt.date(2026, 10, 31):
                continue
            r = {"scadenza": E.isoformat(), "trimestrale": m in (3, 6, 9, 12)}
            for lag in (7, 3):
                fino = (E - dt.timedelta(days=lag + 1)).isoformat()  # giorni interi prima delle 08:00 di E-lag
                for nomep, fin in (("cum", None), ("28g", 28)):
                    x = proxy(v, E.isoformat(), fino, fin)
                    r[f"mp{lag}_{nomep}"] = max_pain(x) if len(x) else np.nan
                    r[f"n{lag}_{nomep}"] = round(float(x["q"].sum()), 1)
                    r[f"strike{lag}_{nomep}"] = x["K"].nunique()
            righe.append(r)
    pd.DataFrame(righe).to_csv(os.path.join(DATI, "maxpain.csv"), index=False)
    print("maxpain", len(righe), "scadenze")

    # --- validazione: proxy (campione fino al 2026-11-23) contro open interest vero dell'istantanea di oggi ---
    bk = sorted(glob.glob(os.path.join(DATI, "book_BTC_*.csv.gz")))[-1]
    b = pd.read_csv(bk)
    info = b["instrument_name"].map(nome)
    b["scad"], b["K"], b["tipo"] = [info.map(lambda t: t[0].isoformat()), info.map(lambda t: t[1]), info.map(lambda t: t[2])]
    spot = float(b["estimated_delivery_price"].median())
    val = []
    for s, g in b.groupby("scad"):
        vero = max_pain(g.rename(columns={"open_interest": "q"})[["K", "tipo", "q"]])
        r = {"scadenza": s, "oi_btc": round(g["open_interest"].sum(), 1), "mp_oi": vero, "spot": round(spot, 2)}
        for nomep, fin in (("cum", None), ("28g", 28)):
            x = proxy(v, s, "2026-11-23", fin)
            r["mp_" + nomep] = max_pain(x) if len(x) else np.nan
            r["err_" + nomep + "_pct"] = round(100 * (r["mp_" + nomep] - vero) / spot, 2) if len(x) else np.nan
            r["lato_" + nomep] = bool(np.sign(r["mp_" + nomep] - spot) == np.sign(vero - spot)) if len(x) else np.nan
        val.append(r)
    pd.DataFrame(val).to_csv(os.path.join(DATI, "validazione_maxpain.csv"), index=False)
    print("validazione", len(val), "scadenze; file", os.path.basename(bk))


if __name__ == "__main__":
    main()
