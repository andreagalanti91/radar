"""Opzioni e direzione · fase 1 · conteggi e copertura (NESSUN rendimento). Uso: python3 conteggi.py > conteggi.txt"""
import os

import numpy as np
import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(QUI, "dati")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def per_anno(df, col_data, cols):
    a = df[col_data].str[:4]
    t = pd.DataFrame({c: df[c].notna().groupby(a).sum() for c in cols})
    t.insert(0, "righe", a.value_counts().sort_index())
    t.loc["tutto"] = t.sum()
    return t.astype(int)


print("# Conteggi · opzioni e direzione · fase 1 (nessun rendimento calcolato)\n")

for cur in ("BTC", "ETH"):
    for res, att in (("1D", "giorni"), ("3600", "ore")):
        dv = pd.read_csv(os.path.join(D, f"dvol_{cur}_{res}.csv"), parse_dates=["t"])
        passo = pd.Timedelta(days=1) if res == "1D" else pd.Timedelta(hours=1)
        atteso = pd.date_range(dv["t"].min(), dv["t"].max(), freq=passo)
        manca = atteso.difference(pd.DatetimeIndex(dv["t"]))
        buchi = dv["t"].diff().gt(passo).sum()
        print(f"DVOL {cur} {res}: {len(dv)} {att}, {dv['t'].min():%Y-%m-%d %H:%M} → {dv['t'].max():%Y-%m-%d %H:%M}; "
              f"mancanti {len(manca)} ({buchi} buchi)" + (f", es. {list(manca[:3].strftime('%Y-%m-%d %H:%M'))}" if len(manca) else ""))
        if res == "1D":
            print("   per anno:", dv["t"].dt.year.value_counts().sort_index().to_dict())
print()

for cur in ("BTC", "ETH"):
    w = pd.read_csv(os.path.join(D, f"settimanale_{cur}.csv"))
    cols = ["rr25", "rr25s", "iv_atm", "pc_vol", "pc_buy", "dvol", "dvol_d7"] + (["pc_camp7"] if cur == "BTC" else [])
    print(f"## Domeniche {cur} (giornata intera): {len(w)} domeniche {w['data'].min()} → {w['data'].max()}")
    print("osservazioni valide per anno:")
    print(per_anno(w, "data", cols).to_string())
    print(f"scambi per domenica: mediana {w['scambi'].median():.0f}, min {w['scambi'].min()}, max {w['scambi'].max()}")
    for k in ("n_p25", "n_c25", "n_atm"):
        print(f"{k}: mediana {w[k].median():.0f}, 5° percentile {w[k].quantile(.05):.0f}, domeniche < 5 scambi: {(w[k] < 5).sum()}")
    print(f"giorni alla scadenza scelta: mediana {w['gg'].median():.1f}, min {w['gg'].min():.1f}, max {w['gg'].max():.1f}")
    print("domeniche senza rr25:", list(w.loc[w['rr25'].isna(), 'data'])[:12])
    print()

m = pd.read_csv(os.path.join(D, "maxpain.csv"))
print(f"## Massimo dolore (proxy dal campione) · scadenze mensili BTC: {len(m)} ({m['scadenza'].min()} → {m['scadenza'].max()}), "
      f"trimestrali {int(m['trimestrale'].sum())}")
print(per_anno(m, "scadenza", ["mp7_cum", "mp3_cum", "mp7_28g", "mp3_28g"]).to_string())
print(f"quantità del campione alla data E-7 (BTC di nozionale): mediana {m['n7_cum'].median():.0f}, min {m['n7_cum'].min():.0f}; "
      f"strike con volume: mediana {m['strike7_cum'].median():.0f}, min {m['strike7_cum'].min()}")
print()

v = pd.read_csv(os.path.join(D, "validazione_maxpain.csv"))
print("## Validazione del proxy contro l'open interest vero (istantanea Deribit di oggi; proxy dal campione fino al 2026-11-23)")
print(v.to_string(index=False))
for k in ("cum", "28g"):
    e = v[f"err_{k}_pct"].abs()
    print(f"proxy {k}: errore assoluto (punti % del prezzo) mediana {e.median():.2f}, media {e.mean():.2f}, "
          f"esatti {(e == 0).sum()}/{e.notna().sum()}, entro 2% {(e <= 2).sum()}/{e.notna().sum()}, "
          f"stesso lato rispetto al prezzo {int(v[f'lato_{k}'].sum())}/{e.notna().sum()}, proxy sopra il vero {(v[f'err_{k}_pct'] > 0).sum()}")
print()

g = pd.read_csv(os.path.join(QUI, "..", "opzioni_studio", "dati", "giorni.csv"))
g = g[g["data"] >= "2021-01-01"]
print("## Campione giornaliero esistente (research/opzioni_studio/dati, 3 finestre da 1000 scambi alle 00/08/16 UTC)")
print(g.groupby(g["data"].str[:4]).agg(giorni=("data", "size"), scambi_mediani=("validi", "median"),
                                           giornata_intera=("intero_giorno", "sum")).to_string())
print()
for f, nome in (("../../data/spot.csv", "BTC spot giornaliero (Binance)"), ("../../data/eth_spot.csv", "ETH spot giornaliero"),
                ("../../data/spot_1h.csv", "BTC spot orario"), ("../opzioni_studio/cache/btc_0800.csv", "BTC 08:00 UTC (regolamento)")):
    x = pd.read_csv(os.path.join(QUI, f))
    c = x.columns[0]
    print(f"{nome}: {len(x)} righe, {x[c].iloc[0]} → {x[c].iloc[-1]}")
