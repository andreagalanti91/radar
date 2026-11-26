# PREREG · Dati provvisori OKX nel flusso perp e nel funding di W3.2 (A1, 26/11/2026)

Scritto prima di eseguire gli script di misura. NON committato dall'agente (vincolo del compito: niente commit):
l'ordine è documentato solo dall'ora dei file.

## Domande
1. A che ora (UTC) i file giornalieri Binance (klines 1d perp, metrics, premiumIndexKlines) del sabato e della domenica
   compaiono su data.binance.vision? Quanti giorni della finestra della decisione sono davvero provvisori al primo giro utile
   del lunedì (00:07–01:07 UTC)?
2. Con i provvisori OKX (ricostruiti con la stessa logica di data.fetch_perp / fetch_funding / features.build_features) quanto si
   spostano flow (media pf14z di gio-ven-sab) e fund7 rispetto ai definitivi Binance? Quante decisioni W3.2 cambiano?
3. Le correzioni proposte riducono l'errore residuo e le decisioni cambiate?

## Misure (fissate prima)
- Errore flusso: |flow_prov − flow_def| (mediana, p95, massimo) e numero di domeniche con segno diverso.
- Errore funding: |fund7_prov − fund7_def| (mediana, p95, max), in unità di funding/giorno; distanza dalla soglia più vicina
  (0,0009 long, −0,0003 short).
- Decisioni: esito di weekly._decide (ingresso long/short, uscita ema/dist, nessuna, e blocco del filtro F1) con provvisori
  e con definitivi, su tutte le domeniche dal 2021 per le quali la ricostruzione è possibile; poi la simulazione completa
  (trade diversi, rendimento, DD) con il dato provvisorio al posto del definitivo alla data della decisione.
- Scenari di ritardo dell'archivio: 0, 1, 2, 3 giorni finali della finestra (gio/ven/sab) da OKX; il funding della
  settimana tutto OKX (archivio mensile).

## Regola di scelta della correzione (fissata prima)
- Si consiglia la correzione con 0 decisioni cambiate sullo storico ricostruito; a parità, quella con p95 dell'errore più
  basso; a parità, quella con meno codice e senza nuove fonti.
- Una correzione che sposta l'ora della decisione/esecuzione cambia la regola di esecuzione di W3.2 (ingresso all'apertura
  del lunedì): si considera solo se l'archivio è disponibile prima delle 00:30 UTC nel 95% delle domeniche; altrimenti si
  riporta solo come informazione, con il costo misurato.
- Nessuna correzione entra in radar/ o data/: patch proposta in un .diff.
