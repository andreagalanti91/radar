# PREREG · Swing su supporti/resistenze settimanali (stop 5–10%, TP 10–15%) su azioni, indici e materie prime · 22/11/2026

Scritto e committato da solo PRIMA di calcolare qualsiasi rendimento sui 15 asset. Finora eseguiti solo `swm_fetch.py` (dati) e
`swm_count.py` (conteggi di livelli, segnali e distanze degli stop; nessuna simulazione, nessun P&L): `conteggi.txt`.
Regole operative: docstring di `research/swing_sr/sw_engine.py` (importato senza modifiche tramite `swm_engine.py`).

## Domanda
La strategia respinta su BTC (lezione 106, `research/swing_sr/`) funziona su mercato azionario e materie prime? Stesse regole,
stessi parametri (K = 3, livelli attivi 104 settimane, tolleranza 1%, cuscinetto 1%, ritest entro 20 barre), stessi per tutti.

## Asset (15) e dati
SPY, QQQ, GLD, SLV, USO, AAPL, AMZN, AVGO, BRK-B, GOOGL, LLY, META, MSFT, NVDA, TSLA. Giornalieri Yahoo fino al 20/11/2026, OHLC
rettificati per split e dividendi (uno short paga quindi i dividendi). Esclusi per qualità dei dati: indici SPX/SPXTR (non
negoziabili, apertura non affidabile: lezione 104), future continui GC=F, SI=F, BZ=F, CL=F (barre piatte, OHLC incoerenti, salti
di rollover, prezzo negativo del WTI nel 2020); per il petrolio si usa l'ETF USO. Limite noto: le 10 azioni sono state scelte
ex post fra le vincenti (favorisce i long e il buy & hold).

## Esecuzione e costi
10.000 $ per asset, ogni asset separato, 1x senza leva, una posizione per volta, capitale composto, liquidità non remunerata.
Commissione 0,05% per lato; slippage 0,05% su ingressi a mercato e stop; TP come ordine limite. Short senza funding; costo del
prestito titoli NON modellato. Stop e TP nello stesso giorno: vale lo stop. Aperture in gap oltre lo stop: uscita all'apertura.
Primo passo dopo questo commit: `swm_check.py` deve riprodurre con il wrapper e i costi di BTC il numero di
`research/swing_sr/risultati.txt` (X/R1/LS/SS/TSR dal 2021 = 5.626 $); se non lo riproduce ci si ferma.

## Griglia (270 configurazioni = griglia di BTC senza R2, che richiede il flusso perp)
Ingresso B / X / T × regime R0 / R1 × lato L / S / LS × stop ST / SS / SF × uscita T10 / T15 / TSR / TH / TT.

## Periodi (fissati dalla sola lunghezza della storia; calcolati da `swm_engine.periods`)
Scelta da max(primo dato + 52 settimane, 01/01/1996). Giudizio dal 01/01/2016 se la scelta dura almeno 8 anni, altrimenti dal
punto di mezzo fra inizio della scelta e 20/11/2026. Ogni periodo ha due metà (per il giudizio: 01/01/2021 oppure il punto di mezzo).
| Asset | Scelta | Giudizio | Metà del giudizio |
|---|---|---|---|
| SPY, AAPL, LLY, MSFT | 1996-01-01 → 2015-12-31 | 2016-01-01 → 2026-11-20 | 2021-01-01 |
| BRK-B / AMZN / NVDA / QQQ | dal 1997-05-08 / 1998-05-14 / 2000-01-21 / 2000-03-08 → 2015-12-31 | idem | 2021-01-01 |
| GOOGL / GLD / USO / SLV | dal 2005-08-18 / 2005-11-17 / 2007-04-09 / 2007-04-27 → 2015-12-31 | idem | 2021-01-01 |
| AVGO | 2010-08-05 → 2018-09-26 | 2018-09-27 → 2026-11-20 | 2022-10-24 |
| TSLA | 2011-06-28 → 2019-03-09 | 2019-03-10 → 2026-11-20 | 2023-01-14 |
| META | 2013-05-17 → 2020-02-16 | 2020-02-17 → 2026-11-20 | 2023-07-05 |

## Scelta (solo sul periodo di scelta di ciascun asset)
Ammissibile su un asset: ≥ 30 trade, profit factor ≥ 1,2 in ciascuna metà del periodo di scelta (simulate separatamente),
DD giornaliero ≥ −20% (stessa soglia del giudizio).
- **Famiglia primaria, S\*(asset)**: per ogni asset la configurazione ammissibile con il CAGR/DD più alto. Se nessuna è
  ammissibile lo si dichiara e si prende il CAGR/DD più alto fra quelle con ≥ 30 trade.
- **Famiglia secondaria, G\***: una sola configurazione per tutti: quella ammissibile sul maggior numero di asset; a parità,
  la mediana più alta del CAGR/DD sui 15 asset. Se nessuna è ammissibile su alcun asset: mediana più alta del CAGR/DD fra le
  configurazioni con ≥ 30 trade su almeno 8 asset.

## Giudizio (una sola volta, 10.000 $ all'inizio del periodo di giudizio)
Su un asset la configurazione è **valida** se soddisfa tutti:
0. almeno 20 trade nel giudizio (altrimenti "non valutabile", conta come non valida);
1. finale > 10.000 $ e profit factor ≥ 1,2 in ciascuna metà del giudizio (ognuna riparte da 10.000 $);
2. DD massimo giornaliero non oltre −20%;
3. placebo: 1.000 simulazioni con ingressi a caso (stesso numero di trade per lato, giorni estratti fra quelli in cui il regime
   ammette quel lato, distanze di stop ricampionate dai trade veri, stessa uscita); p = (1 + n. placebo ≥ reale)/(1 + 1.000);
   deve superare la correzione di **Holm sui 15 asset** (α = 0,05) dentro la propria famiglia;
4. finale > 10.000 $ anche togliendo i 2 trade migliori;
5. vicini che agiscono su ogni tipo d'ingresso: K = 2, K = 4, vita dei livelli 52 e 156 settimane; almeno 3 su 4 chiudono
   > 10.000 $ con profit factor > 1.
È **conveniente** se, oltre a essere valida, ha CAGR/DD superiore al buy & hold dello stesso asset nello stesso periodo
(buy & hold: acquisto all'apertura del primo giorno con gli stessi costi; si riportano finale, DD, CAGR/DD).

## Verdetto di trasferibilità
- **"Funziona fuori da BTC"** solo se S\*(asset) è valida su almeno 8 asset su 15. "Conviene" solo se è anche conveniente su ≥ 8.
- Se la primaria fallisce ma G\* è valida su ≥ 8/15: "indicazione da confermare su dati nuovi", non "funziona".
- Altrimenti: **non funziona**. Si riporta anche il dettaglio per classe (5 ETF di indici/materie prime, 10 azioni), descrittivo.

## Descrittivo (non cambia il verdetto; filtri scritti qui)
- Le 270 configurazioni nel giudizio per asset: quota con finale > 10.000 $, quota con CAGR/DD > buy & hold, mediane.
- Correlazione di rango fra CAGR/DD di scelta e di giudizio, sulle configurazioni con ≥ 30 trade in scelta e ≥ 20 nel giudizio.
- Mediane per dimensione (ingresso, regime, lato, stop, uscita) del finale di giudizio, su tutte le coppie asset × configurazione
  e numero di asset in cui ogni valore è il migliore: risponde alla domanda su stop e TP.
- S\* e buy & hold dal 01/01/2021 (finestra abituale dell'utente), S\* a costi zero e a costi doppi.
- Migliore a posteriori per asset (≥ 20 trade nel giudizio): riportata come "non utilizzabile", senza placebo.

## Secondo ciclo
Nessun secondo giro di scelta sui dati di giudizio. Ammessa solo la correzione di un errore del motore, dichiarata nel README.
