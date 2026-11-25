"""Validazione della superficie: scrive VALIDAZIONE.md (copertura, 23 operazioni vere, DVOL, controlli di qualità).

Uso: python3 valida.py   (dopo costruisci.py)
"""
import datetime as dt
import math
import os
import sys

import numpy as np
import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
RADAR = os.path.abspath(os.path.join(QUI, "..", "..", ".."))
sys.path.insert(0, os.path.dirname(QUI))
sys.path.insert(0, QUI)
import superficie as S  # noqa: E402
from costruisci import scadenza_da_nome  # noqa: E402

FINE = dt.date(2026, 11, 23)


def pct(x):
    return f"{100 * x:.0f}%"


def copertura():
    righe = []
    d0 = dt.date(2018, 1, 1)
    giorni = [d0 + dt.timedelta(days=i) for i in range((FINE - d0).days + 1)]
    rec = []
    for d in giorni:
        F = S.spot(d)
        r = {"anno": d.year, "data": d}
        for N in (14, 30, 60, 90):
            sc = S.scadenza_vicina(d, N)
            ok_sc = sc is not None
            r[f"dist{N}"] = abs((sc - (d + dt.timedelta(days=N))).days) if ok_sc else np.nan
            for nome, K, tipo in (("0", F, "C"), ("+10", F * math.exp(0.1) if F == F else F, "C"),
                                  ("-10", F * math.exp(-0.1) if F == F else F, "P")):
                q = S.iv(d, sc, K, tipo)[1] if ok_sc and F == F else "mancante"
                r[f"{N}_{nome}"] = q
        rec.append(r)
    df = pd.DataFrame(rec)
    cols = [c for c in df.columns if c not in ("anno", "data") and not c.startswith("dist")]
    out = ["| anno | giorni | " + " | ".join(f"{c.replace('_', 'g ')}" for c in cols) + " |",
           "|---|---|" + "---|" * len(cols)]
    for anno, g in df.groupby("anno"):
        out.append(f"| {anno} | {len(g)} | " + " | ".join(pct((g[c] == "scambi").mean()) for c in cols) + " |")
    tot = " | ".join(pct((df[c] == "scambi").mean()) for c in cols)
    out.append(f"| tutto | {len(df)} | {tot} |")
    # copertura "qualsiasi valore" (scambi + interpolata + estesa)
    out2 = ["| anno | " + " | ".join(f"{c.replace('_', 'g ')}" for c in cols) + " |", "|---|" + "---|" * len(cols)]
    for anno, g in df.groupby("anno"):
        out2.append(f"| {anno} | " + " | ".join(pct((g[c] != "mancante").mean()) for c in cols) + " |")
    out3 = ["| anno | 14g | 30g | 60g | 90g |", "|---|---|---|---|---|"]
    for anno, g in df.groupby("anno"):
        out3.append(f"| {anno} | " + " | ".join(f"{g[f'dist{N}'].median():.0f}" for N in (14, 30, 60, 90)) + " |")
    return "\n".join(out), "\n".join(out2) + "\n\nDistanza mediana (giorni) fra la scadenza scelta e D+N:\n\n" + "\n".join(out3), df


def operazioni():
    v = pd.read_csv(os.path.join(RADAR, "research", "opzioni_import", "storico_prezzi_veri.csv"))
    out = ["| n | entra | contratto | iv vera | iv sup. | qualità | premio vero (BTC) | premio sup. (BTC) | scarto premio | "
           "premio sup. con spot del giorno |", "|---|---|---|---|---|---|---|---|---|---|"]
    dv, dp, dp2 = [], [], []
    for _, r in v.iterrows():
        sc, K, t = scadenza_da_nome(r.contratto)
        F = K / (1 + r.K_su_S)  # prezzo del momento d'ingresso implicito in K_su_S = K/S - 1
        iv_s, q = S.iv(r.entra, sc, K, t, F=F, ora=0)
        p, _ = S.prezzo(r.entra, sc, K, t, F=F, ora=0)
        p2, _ = S.prezzo(r.entra, sc, K, t, ora=0)
        pb, pb2 = p / F, p2 / S.spot(r.entra)
        if iv_s == iv_s:
            dv.append(iv_s - r.iv_vera)
            dp.append(pb / r.premio - 1)
            dp2.append(pb2 / r.premio - 1)
        out.append(f"| {r.n} | {r.entra} | {r.contratto} | {r.iv_vera:.3f} | {iv_s:.3f} | {q} | {r.premio:.4f} | "
                   f"{pb:.4f} | {100 * (pb / r.premio - 1):+.1f}% | {100 * (pb2 / r.premio - 1):+.1f}% |")
    dv, dp, dp2 = np.array(dv), np.array(dp), np.array(dp2)
    sintesi = (f"Operazioni valutate: {len(dv)}/23. Volatilità (superficie − vera, punti di vol): mediana "
               f"{100 * np.median(dv):+.1f}, mediana assoluta {100 * np.median(abs(dv)):.1f}, massimo assoluto "
               f"{100 * np.max(abs(dv)):.1f}.\n"
               f"Premio (superficie/vero − 1), con il prezzo del momento d'ingresso (S = K/(1+K_su_S)): mediana "
               f"{100 * np.median(dp):+.1f}%, mediana assoluta {100 * np.median(abs(dp)):.1f}%, massimo assoluto "
               f"{100 * np.max(abs(dp)):.1f}%.\n"
               f"Premio con lo spot mediano del giorno (spot(D)) invece del prezzo d'ingresso: mediana "
               f"{100 * np.median(dp2):+.1f}%, mediana assoluta {100 * np.median(abs(dp2)):.1f}%, massimo assoluto "
               f"{100 * np.max(abs(dp2)):.1f}%.")
    return "\n".join(out), sintesi


def dvol(cop):
    dv = pd.read_csv(os.path.join(QUI, "dvol.csv"), parse_dates=["date"])
    dv["d"] = dv["date"].dt.date
    dv["dvol"] = (dv["open"] + dv["close"]) / 2 / 100
    rec = []
    for d in dv["d"]:
        if d > FINE:
            continue
        F = S.spot(d)
        if F != F:
            continue
        c, q = S.iv(d, d + dt.timedelta(days=30), F, "C")
        p, _ = S.iv(d, d + dt.timedelta(days=30), F, "P")
        rec.append({"d": d, "iv30": np.nanmean([c, p]), "q": q})
    m = pd.DataFrame(rec).merge(dv[["d", "dvol"]], on="d").dropna()
    corr = m["iv30"].corr(m["dvol"])
    diff = m["iv30"] - m["dvol"]
    solo = m[m["q"] != "estesa"]
    m["anno"] = pd.to_datetime(m["d"]).dt.year
    per_anno = m.groupby("anno").apply(lambda g: pd.Series({"giorni": len(g), "corr": g["iv30"].corr(g["dvol"]),
                                                             "scarto_mediano": 100 * (g["iv30"] - g["dvol"]).median()}))
    testo = (f"Giorni confrontati: {len(m)} (dal {m['d'].min()} al {m['d'].max()}). Correlazione dei livelli: {corr:.3f}; "
             f"correlazione delle variazioni giornaliere: {m['iv30'].diff().corr(m['dvol'].diff()):.3f}. "
             f"Scarto mediano (superficie − DVOL): {100 * diff.median():+.1f} punti di vol; mediana assoluta "
             f"{100 * diff.abs().median():.1f}; 95° percentile assoluto {100 * diff.abs().quantile(0.95):.1f}. "
             f"Esclusi i giorni 'estesa': {len(solo)} giorni, correlazione {solo['iv30'].corr(solo['dvol']):.3f}.")
    tab = ["| anno | giorni | correlazione | scarto mediano (punti) |", "|---|---|---|---|"]
    for a, r in per_anno.iterrows():
        tab.append(f"| {a} | {int(r.giorni)} | {r['corr']:.3f} | {r.scarto_mediano:+.1f} |")
    return testo, "\n".join(tab)


def qualita():
    g = pd.read_csv(os.path.join(QUI, "giorni.csv"))
    sp = pd.read_csv(os.path.join(RADAR, "data", "spot.csv"))
    sp["mid"] = (sp["open"] + sp["close"]) / 2
    m = g.merge(sp[["date", "low", "high", "mid"]], left_on="data", right_on="date")
    m["scarto"] = m["indice"] / m["mid"] - 1
    fuori = m[(m["indice"] < m["low"] * 0.99) | (m["indice"] > m["high"] * 1.01)]
    d0, d1 = dt.date(2018, 1, 1), FINE
    attesi = (d1 - d0).days + 1
    vuoti = g[g.get("validi", pd.Series(0, index=g.index)).fillna(0) == 0]
    testo = (f"Giorni in cache: {len(g)} su {attesi} attesi; giorni senza scambi validi: {len(vuoti)}"
             f"{' (' + ', '.join(vuoti['data'].head(10)) + (' …' if len(vuoti) > 10 else '') + ')' if len(vuoti) else ''}. "
             f"Giorni con campione dell'intera giornata: {int(g['intero_giorno'].sum())}. "
             f"Indice Deribit vs data/spot.csv (Binance, metà fra apertura e chiusura, dal {m['date'].min()}): "
             f"scarto mediano {100 * m['scarto'].median():+.2f}%, mediana assoluta {100 * m['scarto'].abs().median():.2f}%; "
             f"giorni con indice fuori dal minimo/massimo Binance (±1%): {len(fuori)}"
             f"{' (' + ', '.join(fuori['data'].head(10)) + ')' if len(fuori) else ''}.")
    per_anno = g.assign(anno=g["data"].str[:4]).groupby("anno").agg(
        giorni=("data", "size"), scambi_mediani=("validi", "median"), interi=("intero_giorno", "sum"))
    tab = ["| anno | giorni | scambi validi per giorno (mediana) | giorni con campione intero |", "|---|---|---|---|"]
    for a, r in per_anno.iterrows():
        tab.append(f"| {a} | {int(r.giorni)} | {r.scambi_mediani:.0f} | {int(r.interi)} |")
    return testo, "\n".join(tab)


def main():
    q_testo, q_tab = qualita()
    cop, cop2, cdf = copertura()
    op_tab, op_sint = operazioni()
    dv_testo, dv_tab = dvol(cdf)
    sup = pd.read_csv(os.path.join(QUI, "superficie.csv.gz"))
    md = f"""# Validazione della superficie di volatilità (opzioni BTC, Deribit)

Generato da `dati/valida.py` il {dt.date.today()} su `superficie.csv.gz` ({len(sup)} righe, {sup['data'].nunique()} giorni,
{sup['data'].min()} → {sup['data'].max()}). Ricostruire: `python3 scarica.py scambi 2018-01-01 AAAA-MM-GG`,
`python3 scarica.py dvol`, `python3 costruisci.py`, `python3 valida.py` (dentro `dati/`).

## Campione e controlli di qualità
Per ogni giorno UTC al massimo 3 pagine da 1000 scambi (dalle 00:00, 08:00 e 16:00 UTC); nei giorni poco liquidi una
pagina copre l'intera giornata.

{q_testo}

{q_tab}

## (a) Copertura per anno
Per ogni giorno: scadenza = venerdì scambiato (in D o nei 3 giorni prima) più vicino a 14/30/60/90 giorni, come farà il
motore (nel 2018–2019 le scadenze erano poche: vedi la distanza mediana sotto); strike alla pari (call, K = spot), +10% (call, ln K/F = +0,10), −10% (put, ln K/F = −0,10).
Percentuale dei giorni di calendario con qualità **"scambi"** (scadenza scambiata quel giorno nel campione, stesso tipo,
una fascia con scambi a moneyness media entro 0,05 da quella richiesta):

{cop}

Percentuale dei giorni con un valore qualsiasi (scambi + interpolata + estesa; il resto è "mancante"):

{cop2}

## (b) Le 23 operazioni vere (`research/opzioni_import/storico_prezzi_veri.csv`)
Superficie valutata al giorno d'ingresso, all'ora 00:00 UTC, con F = prezzo implicito in `K_su_S` (K/S − 1). Il premio
vero è il prezzo medio degli scambi veri del contratto in BTC (premio/prezzo).

{op_sint}

Attenzione: il confronto non è indipendente, perché gli scambi veri del contratto nel giorno d'ingresso possono far parte
del campione della superficie; misura soprattutto la coerenza del metodo (fasce, mediane, Black-76 con F = indice).
Lo scarto sul premio con la stessa IV viene da F = indice invece del future (base) e dall'ora degli scambi veri;
con lo spot mediano del giorno gli scarti esplodono nei giorni di forte movimento: per prezzare un ingresso
passare sempre F = prezzo del momento.

{op_tab}

## (c) Volatilità a 30 giorni alla pari contro DVOL (dal 2021-03)
Superficie: media call/put a ln(K/F) = 0, T = 30 giorni (interpolazione della varianza totale fra le scadenze). DVOL:
media fra apertura e chiusura del giorno.

{dv_testo}

DVOL misura la varianza a 30 giorni su tutta la curva (ali comprese, stile VIX): è atteso che stia sopra la volatilità
alla pari, di più quando lo skew è ripido (2021–2022). Nessun giorno dei dati ha qualità "estesa": ogni giorno dal
2018-01-01 ha scambi nel campione.

{dv_tab}

## (d) Limiti noti
- Campione, non volume completo: dal 2020 circa le 3 pagine coprono solo alcune ore (00–04, 08–12, 16–20 UTC circa);
  la mediana del giorno pesa queste ore. Le scadenze lontane e le ali (±20/40%) restano spesso senza scambi nel
  campione e vengono interpolate/estese.
- F ≈ indice spot, non il future della scadenza: con base positiva (contango, tipico 2020–2021) le call in denaro e le put
  fuori denaro risultano con moneyness leggermente spostata; l'effetto sulle IV per fascia è piccolo ma non nullo.
- L'IV è quella dello scambio fornita da Deribit (calcolata sul mark del future); le mediane per fascia con 1–2 scambi
  sono rumorose (colonna `n`). Nessun filtro su scambi in blocco o anomali oltre 1% < IV < 500%.
- spot(D) è la mediana dell'indice nel campione del giorno: nei giorni di forte movimento differisce dall'apertura
  (es. 2018-01-08, 2019-05-13). Per prezzare un ingresso passare F = prezzo del momento (parametro `F` di iv/prezzo).
- "estesa" usa il giorno precedente (fino a 3 giorni) con la stessa moneyness: nessun anticipo del futuro, ma il
  sorriso non segue i movimenti di quei giorni.
- Il file contiene anche le scadenze del giorno stesso (gg < 0, scambi prima delle 08:00) e le giornaliere: IV estreme
  (546 righe fuori da 10%–300%, quasi tutte a meno di 1 giorno o nelle ali ±40%) sono scambi veri, non filtrati;
  superficie.py non usa scadenze a meno di 2 giorni per interpolare. Il 14% delle righe ha un solo scambio (`n` = 1).
- Black-76 senza tassi né base; Deribit quota in BTC (opzioni inverse): premio_BTC = premio_USD / F.
"""
    with open(os.path.join(QUI, "VALIDAZIONE.md"), "w") as f:
        f.write(md)
    print(md[:3000])


if __name__ == "__main__":
    main()
