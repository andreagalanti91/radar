"""w32_asset2/crypto: CONTEGGI (nessun rendimento). Per ogni moneta inclusa: anni di dati spot/perp con taker buy/funding,
inizio della versione completa (primo segnale W3.2 calcolabile: SMA 40 settimane + flusso perp, dal 2020-01-01), ingressi
W3.2 per anno e lato (radar.weekly.simulate invariato, parametri di BTC), settimane con condizione d'ingresso vera,
sovrapposizione settimanale con le posizioni di BTC. Scrive data/counts.csv, data/counts_anno.csv e universe.csv.
Il controllo del motore (BTC 2021-01-01 -> 2026-11-10 riproduce w32_top100) stampa solo sì/no."""
import json, sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; D = HERE / "data"
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402
SINCE = "2019-09-01"   # inizio della storia prezzi usata (come w32_top100): le EMA/ATR settimanali dipendono dal punto di partenza
LAST = pd.Timestamp("2026-11-24"); S20 = pd.Timestamp("2020-01-01"); Y3 = pd.Timedelta(days=round(3 * 365.25))

def z(s, n): return (s - s.rolling(n, min_periods=n // 2).mean()) / s.rolling(n, min_periods=n // 2).std()   # = top10_w3

def rd(t, k):
    p = D / f"{t}_{k}.csv.gz"
    return pd.read_csv(p, index_col=0, parse_dates=True) if p.exists() else None

def feats(t, end=LAST, since=SINCE):
    """= w32_top100/run.py feats (spot opzionale, prezzo dal perp dove manca lo spot); fine = ultimo giorno del perp se fermo.
    since: i file hanno lo spot dal 2018-06; per i conteggi si parte dal 2019-09 come w32_top100 (stesse EMA iniziali)."""
    sp, pp, fu = (None if x is None or not len(x[x.index >= since]) else x[x.index >= since] for x in (rd(t, "spot"), rd(t, "perp"), rd(t, "funding")))
    if sp is None and pp is None: return None
    if pp is not None and pp.index[-1] < end: end = pp.index[-1]            # perp delistato/fermo: il flusso finisce lì
    elif pp is None: end = min(end, sp.index[-1])
    idx = pd.date_range(min(x.index[0] for x in (sp, pp) if x is not None), end)
    px = pd.DataFrame(index=idx, columns=["open", "high", "low", "close"], dtype=float)
    if pp is not None: px = pp[["open", "high", "low", "close"]].reindex(idx)
    if sp is not None: px = sp[["open", "high", "low", "close"]].reindex(idx).combine_first(px)
    f = px.copy()
    if pp is not None:
        q = pp.reindex(idx); d = 2 * q["tbv"] - q["volume"]
        f["pf14z"] = z(d.rolling(14).sum() / q["volume"].rolling(14).sum(), 180)
    else: f["pf14z"] = np.nan
    f["funding"] = (fu["funding"] if fu is not None else pd.Series(dtype=float)).reindex(idx).ffill(limit=3)
    return f[f["close"].notna()]

def years(x, col=None):
    if x is None: return 0.0
    if col: x = x[x[col].notna()]
    return round(len(x) / 365.25, 2)

def full_start(f):
    w = W.weekly_bars(f); ok = w[(w.index >= S20) & w["sma"].notna() & w["flow"].notna()]
    return None if ok.empty else ok.index[0] + pd.Timedelta(days=1)        # lunedì dopo la prima domenica calcolabile

def pos_weekly(o, idx):
    """lato in posizione (+1/-1/0) a ogni domenica, dai trade simulati."""
    s = pd.Series(0, index=idx)
    for t in o["trades"] + ([o["open"]] if o["open"] else []):
        a = pd.Timestamp(t["entry"]); b = pd.Timestamp(t["exit"]) if t.get("exit") else idx[-1] + pd.Timedelta(days=1)
        s[(s.index >= a) & (s.index < b)] = 1 if t["side"] == "long" else -1
    return s[s.index.dayofweek == 6]

def btc_check():
    f = feats("BTC", pd.Timestamp("2026-11-10")); o = W.simulate(f, start="2021-01-01")
    return round(float(o["equity"].iloc[-1])) == 78474                       # riferimento w32_top100/w32_multi

if __name__ == "__main__":
    u = pd.read_csv(D / "universe_raw.csv"); ops = pd.read_csv(D / "ops.csv").set_index("ticker")
    print("motore su formato: BTC riproduce w32_top100 =", btc_check(), flush=True)
    fb = feats("BTC"); ob = W.simulate(fb, start=str(full_start(fb).date())); pb = pos_weekly(ob, fb.index)
    rows, yrows = [], []
    for r in u.itertuples():
        base = dict(ticker=r.ticker, simbolo=r.symbol, nome=r.name, rank_oggi=r.rank_oggi, rank_2020=r.rank_2020, simbolo_2020=r.symbol_2020,
                    categoria=r.escluso if isinstance(r.escluso, str) else "crypto")
        if isinstance(r.escluso, str): rows.append(dict(base, classe="esclusa")); continue
        sp, pp, fu = rd(r.ticker, "spot"), rd(r.ticker, "perp"), rd(r.ticker, "funding")
        f = feats(r.ticker)
        row = dict(base, dati_da=None, dati_a=None, anni_spot=years(sp), anni_perp=years(pp), anni_perp_tbv=years(pp, "tbv"),
                   anni_funding=years(fu), perp_da=str(pp.index[0].date()) if pp is not None else "", completa_da="", anni_completa=0.0)
        if f is None: rows.append(dict(row, classe="senza dati")); continue
        row.update(dati_da=str(min(x.index[0] for x in (sp, pp) if x is not None).date()), dati_a=str(f.index[-1].date()))   # da = file (spot dal 2018-06)
        st = full_start(f) if f["pf14z"].notna().any() else None
        f18 = feats(r.ticker, since="2018-01-01"); s18 = full_start(f18) if st is not None else None
        row["completa_da_storia2018"] = str(s18.date()) if s18 is not None else ""
        if st is None or st > f.index[-1]:
            rows.append(dict(row, classe="solo prezzo" if f["pf14z"].notna().sum() == 0 else "breve")); continue
        yrs = round((f.index[-1] - st).days / 365.25, 2)
        o = W.simulate(f, start=str(st.date()))
        tr = o["trades"] + ([o["open"]] if o["open"] else [])
        w = o["weekly"]; w = w[w.index >= st - pd.Timedelta(days=1)]
        for y in range(2020, LAST.year + 1):
            e = [t for t in tr if pd.Timestamp(t["entry"]).year == y]; wy = w[w.index.year == y]
            yrows.append(dict(ticker=r.ticker, anno=y, ingressi_long=sum(t["side"] == "long" for t in e), ingressi_short=sum(t["side"] == "short" for t in e),
                              sett_cond_long=int(wy["long"].sum()), sett_cond_short=int(wy["short"].sum()), sett_attive=len(wy)))
        pw = pos_weekly(o, f.index); j = pd.concat([pw, pb], axis=1, keys=["a", "b"]).dropna(); inpos = j[j.a != 0]
        row.update(completa_da=str(st.date()), anni_completa=yrs, motore_ok=True, ingressi=len(tr), ingressi_long=sum(t["side"] == "long" for t in tr),
                   ingressi_short=sum(t["side"] == "short" for t in tr), posizione_aperta=o["open"]["side"] if o["open"] else "",
                   sett_in_pos=len(inpos), sovr_btc_stesso_lato_pct=round(100 * (inpos.a == inpos.b).mean(), 1) if len(inpos) else None,
                   sovr_btc_opposto_pct=round(100 * ((inpos.b != 0) & (inpos.a != inpos.b)).mean(), 1) if len(inpos) else None,
                   btc_flat_pct=round(100 * (inpos.b == 0).mean(), 1) if len(inpos) else None,
                   classe="valutabile" if f.index[-1] - st >= Y3 else "breve")
        rows.append(row); print(r.ticker, row["classe"], row["completa_da"], row["ingressi"], flush=True)
    c = pd.DataFrame(rows).merge(ops, left_on="ticker", right_index=True, how="left")
    c.to_csv(D / "counts.csv", index=False); pd.DataFrame(yrows).to_csv(D / "counts_anno.csv", index=False)
    uv = c.rename(columns={"categoria": "categoria"})[["simbolo", "ticker", "nome", "rank_oggi", "rank_2020", "simbolo_2020", "categoria", "dati_da", "dati_a",
                                                     "completa_da", "classe", "bitget_perp", "okx_perp"]].copy()
    uv["valutabile"] = uv.classe == "valutabile"
    for k in ("rank_oggi", "rank_2020"): uv[k] = uv[k].astype("Int64")
    uv[["simbolo", "ticker", "nome", "rank_oggi", "rank_2020", "simbolo_2020", "categoria", "dati_da", "dati_a", "completa_da", "valutabile", "classe",
        "bitget_perp", "okx_perp"]].sort_values(["rank_oggi", "rank_2020"]).to_csv(HERE / "universe.csv", index=False)
    print(c.classe.value_counts().to_string())
