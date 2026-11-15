# N1 · Perché W3 decide di domenica? · preregistrazione (15/11/2026, prima dei risultati)

## Domanda
W3 usa candele settimanali W-SUN (chiusura domenica 23:59 UTC, esecuzione all'apertura del lunedì). Il risultato dipende da
questa scelta di calendario? Se sì, quanto, e la domenica è un giorno "fortunato"?

## Regole (meccaniche, nessun parametro nuovo)
W3 identica a `radar/weekly.py` (SMA40/EMA20/EMA21, ATR14 settimanale, F1 MACD 8/21/5 con trend ≥ 16 settimane, stop e trailing
2,5 ATRw a cricchetto, tetto di rischio 25% long e short, long spot 0,1%/lato, short perp 0,05%/lato + funding reale,
slippage 0,1%, nessun rendimento della liquidità). Cambia SOLO il giorno di ancoraggio D ∈ {LUN, MAR, MER, GIO, VEN, SAB, DOM}:
- candele settimanali `W-D` (chiusura UTC del giorno D, solo settimane complete); decisione alla chiusura di D, esecuzione
  all'apertura del giorno dopo;
- flusso: `live_flow` invariato (media degli ultimi 3 giorni di pf14z, ritardo di un giorno) letto al giorno D, cioè i 3 giorni
  D−3…D−1, come oggi per la domenica (giovedì–sabato);
- funding 7 giorni (distribuzione) letto al giorno D; trailing e funding giornalieri invariati; l'ATR corrente del trailing si
  aggiorna alla chiusura di D.

## Controllo preliminare (vincolante)
D = DOM deve riprodurre `radar.weekly.simulate` dal 01/01/2021: ~78.474 $, DD −21,1%, 13 trade (stesse date). Altrimenti mi fermo.

## Varianti (7 + 1, nessun'altra)
V1–V7: W3 ancorata a ciascun giorno. V8: "media dei 7 ancoraggi" = 7 sotto-portafogli da 1/7 del capitale, uno per giorno,
mai ribilanciati (equity = somma delle 7 equity).

## Misure
Per ciascuna: finale da 10.000 $ dal 01/01/2021, rendimento, max DD giornaliero, CAGR, MAR = CAGR/|DD|, trade, win rate;
IS 2021–23 e OOS 2024→oggi (ognuno riparte da 10.000 $); 2018–20 con il flusso sostitutivo (CVD spot) prima di set. 2019;
finale senza il trade migliore. Buy & hold dal 2021 come riferimento.
Sintesi sui 7 giorni: media, mediana, min, max, deviazione standard e coefficiente di variazione del finale; percentile della
domenica (rango fra 7).

## Soglie di lettura (scritte prima)
- "Ancoraggio irrilevante" se il finale minimo è ≥ 70% della mediana e la domenica sta fra il 2° e il 6° posto.
- "Domenica fortunata / rischio di ancoraggio" se la domenica è 1ª (o 7ª) sui 7 E supera la mediana di oltre il 25% su 2021→,
  oppure se la classifica dei giorni cambia completamente fra IS e OOS (rango di Spearman IS/OOS < 0,3).
- V8 è preferibile alla domenica sola se ha MAR ≥ 90% di quello della domenica e DD non peggiore, oppure se riduce il DD di
  almeno 3 punti a parità di MAR. Nessuna modifica a W3: solo proposta.
