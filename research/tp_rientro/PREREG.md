# Preregistrazione · Take profit a +10/15% e rientro su W3.2 (BTC settimanale) · 22/11/2026

Scritta PRIMA di qualsiasi rendimento delle varianti. Finora il motore `tp_engine.py` è stato solo verificato: riproduce
radar.weekly (W3.2) al centesimo (2021+ 78.474 $, 13 trade; IS 2021–23 33.477 $; OOS 2024–26 23.488 $; 2018–20 25.142 $) e le
configurazioni degeneri (TP a +900%, trailing stretto mai attivo o a 2,5) danno equity identica. Va committata da sola.
Regole, parametri, vicini e soglie non si cambiano dopo; ogni idea nata dai risultati va in una nuova preregistrazione.

## 1. Domanda dell'utente
"Quando l'operazione arriva tra il 10 e il 15% uscire, poi rientrare se ci sono le condizioni. Trovare una costante."
Già nel diario: lezione 105 (TP 1/3 a +3R non scatta mai dal 2021; uscite parziali costano), lezione 106 (TP 10–15% dentro il
regime W3.1 dimezza il rendimento, ma con ingressi swing, non sui trade W3), lezione 73 (le uscite parziali tagliano le code).
Novità: TP in % sul prezzo d'ingresso dei trade W3.2 (non in R), con rientro esplicito; trailing stretto dopo +10%.

## 2. Riferimento, dati, costi
- W3.2 = radar/weekly.py: rischio allo stop iniziale 25%, stop e trailing 2,5 ATRw a cricchetto sulla miglior chiusura, uscite
  settimanali EMA21 e distribuzione; long spot 1x, short perp; spot 0,1%/lato, perp 0,05%/lato + funding reale, slippage 0,1%.
- Dati congelati research/p2_nuovi (`p2_data.load`): f_repo per 2021-01-01 → 2026-11-15; f_long (proxy, flusso CVD spot prima
  del 2019-09, funding assente 2018–19) per 2018-01-01 → 2020-12-31. 10.000 $, 1x. IS e OOS ripartono da 10.000 $.

## 3. Regole delle varianti (motore `tp_engine.py`)
- TP: limite a prezzo d'ingresso × (1 ± p), controllo giornaliero su massimo (long) / minimo (short), riempito al livello o
  all'apertura se il prezzo apre oltre, con slippage 0,1% e commissione. Il giorno in cui scatta lo stop vale lo stop.
- "Tutto": si chiude tutta la posizione. "Metà": si chiude il 50% della quantità, il resto segue le regole W3.2 (nessun rientro).
- Rientro A: dopo il TP totale si è flat e vale la logica W3.2 (alla decisione settimanale si entra se il segnale è vero).
- Rientro B (X = 5%, fissato ora): come A, più rientro nello stesso lato alla decisione settimanale se il regime di quel lato è
  ancora valido (long: chiusura > SMA40 e EMA20 in salita; short: chiusura < SMA40, SMA40 in calo su 4 settimane, EMA20 in calo)
  e la chiusura settimanale è entro ±5% dal prezzo di uscita del TP. La possibilità decade a regime finito o al primo ingresso.
- Rientri: stessa dimensione (rischio 25% allo stop iniziale 2,5 ATRw dalla chiusura del segnale), stessi costi.
- Trailing stretto: quando la miglior chiusura supera +10% dal prezzo d'ingresso il trailing passa a 1,5 ATRw (a cricchetto).

## 4. Varianti (8)
| Id | Regola | Vicini (descrittivi) |
|---|---|---|
| V1 | TP +10% tutto, rientro A | V2 |
| V2 | TP +12,5% tutto, rientro A | V1, V3 |
| V3 | TP +15% tutto, rientro A | V2 |
| V4 | TP +10% metà | V5 |
| V5 | TP +12,5% metà | V4, V6 |
| V6 | TP +15% metà | V5 |
| V7 | TP +12,5% tutto, rientro B (X 5%) | X 2,5% e 7,5% |
| V8 | trailing 1,5 ATRw dopo +10% | k 1,25/1,75; attivazione +7,5/+12,5% |

## 5. Prima dei rendimenti (descrittivo)
- Conteggio eventi: quanti trade W3.2 (2021+ e 2018–20) toccano +10%, +12,5%, +15% (massimo/minimo intragiornaliero).
- MFE per trade (intragiornaliero e su chiusura) e quota restituita prima dell'uscita = (MFE − movimento all'uscita) / MFE.

## 6. Metriche
Finale, CAGR, max DD giornaliero, CAGR/DD, trade (con rientri), win rate, peggiore, per 2021+, IS 2021–23, OOS 2024–26, 2018–20.
Buy & hold come riferimento. Trade aperto al 15/11 chiuso all'ultima chiusura (come radar.weekly.metrics).

## 7. Criteri (tutti, per ciascuna variante)
1. CAGR/DD migliore di W3.2 sia in IS 2021–23 sia in OOS 2024–26.
2. 2018–20: CAGR/DD non peggiore di W3.2.
3. DD 2021+ entro −30%.
4. Non dipende da ≤ 2 trade: somma dei Δ log-rendimento per trade (variante − W3.2, abbinati per data del segnale; i rientri
   si sommano al trade d'origine) ancora > 0 togliendo i 2 Δ più favorevoli.
5. Permutazione dei segni sui Δ per trade (esatta se ≤ 20 Δ non nulli, altrimenti 20.000 estrazioni, seme 20261122):
   p ≤ soglia di Holm su 8 test (α 0,05).
6. Placebo: 500 ripetizioni della stessa variante con livello del TP estratto a caso per ogni trade, uniforme in [5%, 30%]
   (per V8 l'attivazione estratta in [5%, 30%]); p = quota delle ripetizioni con CAGR/DD 2021+ ≥ variante; serve p < 0,05.
Win rate riportato per tutte (l'utente vuole > 70%), non è un criterio. Una variante che passa NON entra in radar/:
si segnala all'utente.

## 8. Robustezza aggiuntiva (descrittiva)
Vicini della tabella 4; capitale senza il trade migliore; stessa analisi MFE e regole sul 2018–20. Solo BTC (lezioni 87, 104).
