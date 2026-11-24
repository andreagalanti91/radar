# ADDENDUM 1 al PREREG · soglie di F3 e scelte operative · 24/11/2026 22:00 UTC

Committato da solo, dopo i soli conteggi (`conteggi.txt`, nessun rendimento calcolato) e prima di qualsiasi rendimento.
Proposta dell'agente di ricerca in `PROPOSTA-ADDENDUM.md`, accolta con le precisazioni sotto.

## Soglie di F3 (una per segnale, non si cambiano dopo)
| Segnale | Regola | Operazioni IS / OOS (conteggio) | Ruolo |
|---|---|---|---|
| a | chiusura sopra (sotto) SMA 40 settimane ed EMA 20 settimanale in salita (discesa) → call (put) | 42 / 52 | giudicabile |
| b | condizioni d'ingresso di W3.2 ogni settimana, flusso perp > 0 (< 0) | 16 / 26 | descrittivo (IS < 20; 98% dentro W3.2) |
| c | IV a 30 giorni < realizzata a 30 giorni, oppure IV nel quintile basso delle ultime 52 settimane → straddle | 19 / 37 con IV provvisoria | giudicabile solo se, ricontato con la superficie, IS ≥ 20; altrimenti descrittivo |
| d | ampiezza Bollinger 20 settimane nel quintile basso delle ultime 52 settimane → straddle | 15 / 15 | descrittivo |
| e | settimana con un giorno a −10% o peggio → call | 12 / 6 | descrittivo |
| f | valore atteso a scadenza secondo il cono ≥ 1,4 × costo → call o put (la maggiore) | 22 / 35 | giudicabile, con riserva |

Riserva su f: la deriva storica del cono rende la call "conveniente" nel 98% delle settimane; la soglia 1,4 è stata scelta
solo per arrivare a 20 operazioni per metà. Se f passa, va verificato che non sia una call permanente travestita: si riporta
accanto la "call sempre" (ogni mese una call alla pari) come riferimento, e f deve batterla in OOS.
Regole comuni di F3: come in `PROPOSTA-ADDENDUM.md` (decisione domenica, ingresso lunedì, ≈30 giorni alla pari, 5%, una
posizione per volta, conto separato per segnale).

## Scelte operative (valgono per tutte le famiglie)
1. B0: l'operazione n. 9 usa l'uscita vera di W3.2 (2021-01-04), non il taglio del CSV al 31/12/2020.
2. Uscite di W3.2 durante la giornata (trailing): l'opzione si vende al prezzo del giorno successivo. Scelta prudente.
3. Prezzi della superficie riferiti alle 12:00 UTC del giorno; l'ingresso del lunedì usa la superficie del lunedì.
4. Dati fino al 2026-11-21 (ultimo giorno in `data/`). L'operazione aperta è valutata a quella data ed esclusa dai conteggi
   di operazioni chiuse.
5. Limiti dichiarati: flusso perp vero dal 2020-04 (prima proxy dallo spot), funding dal 2020-01, IV dal 2019 (il 2018 solo
   se la superficie lo copre), scadenze 2018–19 fra 18 e 74 giorni.
6. Prima dei rendimenti il motore va riprovato con `superficie.py` sulle 23 operazioni: scarto mediano del moltiplicatore
   entro ±15% rispetto a `storico_prezzi_veri.csv`, altrimenti ci si ferma (PREREG).
