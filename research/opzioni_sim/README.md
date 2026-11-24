# Opzioni con i segnali di W3.2 · quanto spendere per operazione con 50.000 $ · dal 2021 · 24/11/2026

**Verdetto: i dati non indicano una spesa "migliore". Il risultato cresce in proporzione alla spesa, in guadagno come in
perdita; la scelta riguarda solo quanta perdita si accetta. Descrittivo: 13 operazioni, nessuna regola cambiata, nessuna quota
scelta sui risultati.** Le 7 regole dello studio (`../opzioni_import/OPZIONI_W32.md`) restano: 5% del capitale.

Fonte: `../opzioni_import/storico_prezzi_veri.csv` (prezzi veri Deribit), operazioni con ingresso dal 2021, chiuse (n. 10–22).
`mult` = valore finale dell'opzione / premio pagato. Esecuzione: `python3 sim.py` → `risultati.md`.

| Spesa per opzione | Finale | Guadagno | Perdita peggiore vista | In guadagno |
|---|---|---|---|---|
| 1.500 $ fissi | 85.370 $ | +35.370 $ | −1.038 $ | 10/13 |
| 2.000 $ fissi | 97.160 $ | +47.160 $ | −1.384 $ | 10/13 |
| 2.500 $ fissi (5% di 50.000) | 108.950 $ | +58.950 $ | −1.730 $ | 10/13 |
| 5% del conto, ricalcolato a ogni operazione | 147.448 $ | +97.448 $ | −4.178 $ | 10/13 |
| 10% del conto | 372.198 $ | +322.198 $ | −17.954 $ | 10/13 |
| W3.2 a metà dimensione | 150.483 $ | +100.483 $ | — | — |
| W3.2 intera | 392.370 $ | +342.370 $ | — | — |

## Limiti (da leggere prima dei numeri)
- **Il 2021–26 è il periodo favorevole.** 10 operazioni su 13 in guadagno e nessuna opzione scaduta a zero (peggiore: −69% del
  premio). Dal 2018 le operazioni in guadagno sono il 65% e due premi su 23 sono stati persi per intero: la perdita vera per
  operazione è l'intera spesa (1.500 / 2.000 / 2.500 $), non quella della tabella.
- **Tre operazioni fanno metà del risultato.** Senza le tre migliori: 1.500 $ → 64.139 $ · 2.000 $ → 68.852 $ · 5% → 78.131 $.
- **Non batte W3.2.** A pari rischio (5% del conto) rende quanto W3.2 a metà dimensione (147.000 contro 150.000 $); il 10% rende
  meno di W3.2 intera. Cambia il profilo della perdita: fissata in partenza, senza stop.
- Scegliere la spesa guardando questa tabella sarebbe un'ottimizzazione su 13 operazioni: non va fatto.
- 2021–23: 6/7 in guadagno; 2024–26: 4/6. Dettaglio per periodo in `risultati.md`.

## Cosa significa per l'operatività
Con 50.000 $ la regola del 5% dà 2.500 $ per operazione. 1.500–2.000 $ (3–4%) sono una versione più prudente della stessa
regola, coerente con l'avvio graduale indicato dallo studio. Cinque premi persi di fila costano 7.500 $ (1.500), 10.000 $
(2.000) o 12.500 $ (2.500): dal 2018 la serie peggiore è stata di due perdite.
