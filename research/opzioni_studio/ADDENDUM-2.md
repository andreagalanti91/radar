# ADDENDUM 2 al PREREG · secondo ciclo: correzione del riferimento, nessuna ipotesi nuova di rendimento · 24/11/2026

Committato da solo dopo la revisione critica (agente separato, sola lettura) e prima dell'esecuzione. Motivo ammesso dal
PREREG: errore di specifica del motore. La revisione non ha trovato errori di calcolo (11 operazioni ricalcolate: coincidono)
ma ha trovato che il B0 simulato NON è la regola in uso: `radar/opzioni.py` sceglie il venerdì più vicino a 30 giorni fra
quelli a 20–50 giorni; il motore prendeva il più vicino senza limiti (6 operazioni su 23 a 11–18 giorni).

## Cosa si esegue (tutto esplorativo per PREREG: non può da solo dare un verdetto "migliore")
A. **B0r** = B0 con la finestra 20–50 giorni di `radar/opzioni.py`; se nessun venerdì scambiato cade nella finestra,
   l'operazione si salta e lo si riporta (nel 2018 è atteso per due operazioni). B0r diventa il riferimento del rapporto.
B. **F1, F2 e F3 rieseguiti con finestre coerenti** (≈14: 10–20 giorni · ≈30: 20–50 · ≈60: 45–80 · ≈90: 70–120), stessi
   criteri e stessa regola di scelta su IS già usati, giudicati contro B0r. Soglie di F3 invariate (ADDENDUM-1).
C. **Cancello rafforzato**: (1) confronto a livello di conto composto, non solo mediana per operazione; (2) le operazioni di
   B0r rifatte con gli scambi veri di Deribit del contratto all'ingresso e all'uscita (scambio più vicino entro ±6 ore;
   altrimenti si dichiara e si usa la superficie): "B0r con prezzi veri" accanto a "B0r con superficie".
D. **Descrittivi per chi opera a mano** (nessuna regola nuova): ritardo d'ingresso di 0 / 12 / 24 / 48 / 72 ore dal lunedì
   00:00 UTC su B0r; ingresso solo se BTC non si è mosso oltre il 3% dal segnale (la soglia proposta nella guida OKX) contro
   ingresso comunque; ricampionamento (10.000 estrazioni con reinserimento) dei moltiplicatori di B0r su 3 anni (numero di
   operazioni come nello storico): distribuzione del conto al 5%, probabilità di chiudere in perdita, serie peggiore di
   premi persi, e gli stessi numeri in dollari per 1.500 e 2.000 $ fissi.

## Cosa NON si esegue
Il filtro sulla volatilità implicita alta proposto dalla diagnosi: i terzili nascono dagli stessi dati 2018–26, OOS
compreso (pesca a posteriori), e non tocca B0, positivo in tutti i terzili. F3d (compressione → straddle) non si ritesta:
resta in osservazione sulla carta, se l'utente lo approva.

## Limiti da scrivere nel rapporto
Ingresso alle 12:00 UTC del lunedì (circa 12 ore dopo il segnale), uscite al giorno dopo, superficie del giorno che include
scambi dopo le 12:00, placebo sbilanciato a favore del segnale, regolamento su Binance 08:00, incertezza dei prezzi ≈ ±15%
sul conto composto.
