"""ema_sma · tabelle leggibili dei dati (DATI.md, DATI-giornaliero.md, DATI-4h*.md) e CSV in data/. Stessa funzione delle medie
dello studio (es_lib.ma). Sono dati, non risultati."""
import numpy as np, pandas as pd
import es_lib as L

a = L.load_4h(cut=None); d = L.daily_from(a); d = d[d.index <= a.index[-1].normalize()]; w = L.weekly_from(d)
last4 = a.index[-1] + pd.Timedelta(hours=4)
assert a.index[-1].hour == 20, "l'ultimo giorno deve essere completo"
HEAD = (f"Fonte: BTCUSDT spot Binance, archivio pubblico data.binance.vision (candele 4h; giornaliero e settimanale ricostruiti dal 4h). "
        f"Orari in UTC. Ultimo dato: candela 4h chiusa il {last4:%d/%m/%Y alle %H:%M} UTC (ultimo giorno completo {d.index[-1]:%d/%m/%Y}, "
        f"ultima settimana chiusa domenica {w.index[-1]:%d/%m/%Y}). Prezzi in dollari (USDT), arrotondati al dollaro. Generato da `es_dati.py`.\n")


def table(b, mas, ohlc, tfmt):
    out = pd.DataFrame(index=b.index)
    if ohlc:
        out["apertura"], out["massimo"], out["minimo"] = b["open"], b["high"], b["low"]
    out["chiusura"] = b["close"]
    for k, n in mas:
        out[f"{k}{n}"] = L.ma(b["close"], k, n)
    out = out.loc["2021-01-01":]
    out.index = out.index.strftime(tfmt)
    return out


def md(t, first):
    f = t.round(0)
    lines = ["| " + first + " | " + " | ".join(t.columns) + " |", "|---|" + "---:|" * len(t.columns)]
    v = f.to_numpy()
    for i, ix in enumerate(f.index):
        lines.append("| " + ix + " | " + " | ".join("–" if np.isnan(x) else f"{int(x)}" for x in v[i]) + " |")
    return "\n".join(lines) + "\n"


E, S = "EMA", "SMA"
tw = table(w, [(E, 20), (E, 21), (E, 50), (E, 100), (E, 200), (S, 20), (S, 40), (S, 50), (S, 100), (S, 200)], True, "%Y-%m-%d")
td = table(d, [(E, 20), (E, 50), (E, 100), (E, 200), (S, 20), (S, 50), (S, 100), (S, 200)], True, "%Y-%m-%d")
a2 = a.copy(); a2.index = a2.index + pd.Timedelta(hours=4)                      # ora di CHIUSURA della candela
t4 = table(a2, [(E, 20), (E, 50), (E, 200), (S, 20), (S, 50), (S, 200)], False, "%Y-%m-%d %H:%M")
tw.round(2).to_csv(L.HERE / "data" / "BTCUSDT_1w_medie.csv.gz", index_label="chiusura_settimana_domenica")
td.round(2).to_csv(L.HERE / "data" / "BTCUSDT_1d_medie.csv.gz", index_label="giorno_utc")
t4.round(2).to_csv(L.HERE / "data" / "BTCUSDT_4h_medie.csv.gz", index_label="chiusura_candela_utc")

# coerenza con lo studio: stesse serie e stessa funzione (le medie sono causali: il taglio al 15/11 non cambia i valori precedenti)
a0 = L.load_4h(); d0 = L.daily_from(a0); w0 = L.weekly_from(d0)
for b, b0, n in ((d, d0, "1D"), (w, w0, "1W"), (a, a0, "4h")):
    for k in L.KINDS:
        for p in L.PERS:
            x, y = L.ma(b["close"], k, p).reindex(b0.index), L.ma(b0["close"], k, p)
            assert np.allclose(x.dropna(), y.dropna(), rtol=0, atol=1e-9), (n, k, p)
print("medie delle tabelle = medie dello studio (scarto 0) su 4h, 1D, 1W")

files4 = []
txt4 = "# BTCUSDT · candele a 4 ore con EMA e SMA (dal 01/01/2021)\n\n" + HEAD + \
    "\nLa data è l'ora di CHIUSURA della candela (UTC): la riga `2021-01-01 04:00` è la candela 00:00–04:00. Medie calcolate sulle chiusure 4h con la storia dal 17/08/2017.\n"
body = {y: md(t4[t4.index.str[:4] == str(y)], "chiusura (UTC)") for y in sorted(set(t4.index.str[:4].astype(int)))}
if len(txt4) + sum(map(len, body.values())) <= 1_500_000:
    (L.HERE / "DATI-4h.md").write_text(txt4 + "".join(f"\n## {y}\n\n{b}" for y, b in body.items())); files4 = ["DATI-4h.md"]
else:
    for y, b in body.items():
        (L.HERE / f"DATI-4h-{y}.md").write_text(txt4.replace("(dal 01/01/2021)", f"({y})") + f"\n## {y}\n\n{b}"); files4.append(f"DATI-4h-{y}.md")
(L.HERE / "DATI-giornaliero.md").write_text(
    "# BTCUSDT · candele giornaliere con EMA e SMA (dal 01/01/2021)\n\n" + HEAD +
    "\nGiorno UTC (00:00–24:00). Medie sulle chiusure giornaliere; prima del 17/08/2017 (inizio di Binance) la storia che scalda le medie è il giornaliero del repo (Bitstamp, dal 2014).\n\n" + md(td, "giorno"))
(L.HERE / "DATI.md").write_text(
    "# BTCUSDT · dati con EMA e SMA: settimanale, giornaliero, 4 ore (dal 01/01/2021)\n\n" + HEAD + f"""
## Colonne
- **data**: settimanale = domenica di chiusura della settimana (lunedì 00:00 → domenica 24:00 UTC, come W3.2); giornaliero = giorno UTC; 4 ore = ora di chiusura della candela.
- **apertura, massimo, minimo, chiusura**: prezzi della candela.
- **EMAn**: media mobile esponenziale di n chiusure (peso 2/(n+1), avviata dalla prima chiusura della storia, valida dopo n chiusure).
- **SMAn**: media mobile semplice delle ultime n chiusure. "–" = media non ancora calcolabile.
- Le medie usano la storia PRECEDENTE al 2021 e sono quindi corrette dalla prima riga: 4h dal 17/08/2017 (Binance); giornaliero e
  settimanale dal 2014 (prima del 17/08/2017 giornaliero del repo, Bitstamp: pesa ancora sulle medie settimanali a 200 periodi del 2021,
  circa il 17% della EMA200 settimanale a gennaio 2021, poi sempre meno).
- Stessa funzione di calcolo dello studio (`es_lib.ma`); verifica automatica in `es_dati.py` (scarto 0).

## File
- Questo file: tabella settimanale completa ({len(tw)} settimane).
- [DATI-giornaliero.md](DATI-giornaliero.md): {len(td)} giorni, chiusura con EMA 20/50/100/200 e SMA 20/50/100/200.
- 4 ore ({len(t4)} candele, chiusura con EMA 20/50/200 e SMA 20/50/200, una sezione per anno): {", ".join(f"[{f}]({f})" for f in files4)}.
- CSV compressi con due decimali: [data/BTCUSDT_1w_medie.csv.gz](data/BTCUSDT_1w_medie.csv.gz), [data/BTCUSDT_1d_medie.csv.gz](data/BTCUSDT_1d_medie.csv.gz),
  [data/BTCUSDT_4h_medie.csv.gz](data/BTCUSDT_4h_medie.csv.gz); candele 4h grezze dal 2017: [data/BTCUSDT_4h.csv.gz](data/BTCUSDT_4h.csv.gz).
- Controllo: le candele giornaliere ricostruite dal 4h coincidono con i dati del repo (2017-08-17 → 2026-11-15, 3.378 giorni, scarto 0).

## Settimanale

""" + md(tw, "domenica"))
print(len(tw), len(td), len(t4), files4, tw.isna().sum().sum(), td.isna().sum().sum(), t4.isna().sum().sum())
