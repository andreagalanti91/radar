# Addendum alla preregistrazione · regola "flip" dei livelli orizzontali · 23/11/2026

Scritto DOPO aver visto i risultati del PREREG (commit 32bcbba) e PRIMA di eseguire questa parte. Il PREREG non cambia.
Motivo: secondo messaggio dello stesso trader (23/11): livelli "flip" 81,4k e 74,4k (supporti che, rotti, diventano resistenze),
short aperto alla perdita di 81,4k, obiettivo il livello successivo sotto; livelli attraversati 81,4k → 74,4k → 62,5k → 60,3k →
minimo 55,1k.

**Stato di conoscenza (va dichiarato): questa parte è ESPLORATIVA, non di conferma.** Conosco già: (a) T5 del PREREG (rotture dei
livelli swing con spot contro perp: −2,9 punti a 7 g, segno opposto all'atteso); (b) le 405 configurazioni di research/swing_sr
(lezione 106), che contengono proprio "rottura X / ritest T, solo short, obiettivo livello successivo". Nessun p di questa parte
entra nel conteggio di Holm; un risultato positivo varrebbe solo come ipotesi per una nuova preregistrazione.

## Regole (motori esistenti, nessun parametro nuovo)
Livelli: swing settimanali di `sw_engine.levels` (K = 3, 104 settimane). BTC, 01/01/2021 → 15/11/2026, tutti i casi.
| Id | Regola |
|---|---|
| F1 | short all'apertura dopo una chiusura giornaliera sotto il supporto più vicino (segnale X short, nessun filtro di regime); stop sopra il livello rotto (SS, minimo 2%); obiettivo = livello successivo sotto distante 5–30% (TSR); 1x, costi W3.2 |
| F2 | come F1 ma ingresso sul ritest da sotto respinto entro 20 giorni (segnale T short) |
| F1s / F2s | F1 / F2 solo se la vendita a 3 giorni è guidata dallo spot (classe "spot", D0 0,5) al segnale; confronto con i segnali "perp" e "misto" (rendimento medio per trade, permutazione delle etichette, 5.000) |
| F3 | su W3.2: uscita totale dai long alla chiusura sotto il supporto (X short) e dagli short alla chiusura sopra la resistenza (X long); rientro come E-out del PREREG |
| F3s | come F3 solo se il movimento contrario è guidato dallo spot |
Metriche: F1/F2 finale, DD, trade, WR, PF, due metà, contro W3.2 e buy & hold; F3 come le varianti del PREREG (senza placebo).

## Descrittivo sul caso
- I livelli del trader (81,4k / 74,4k / 62,5k / 60,3k) coincidono, entro l'1,5%, con i livelli che `sw_engine.levels` e
  `radar/levels.py` producevano alle stesse date (prima della rottura)?
- Quando F1 è entrata short nel calo del 2026 e a che prezzo, contro W3.2 (short dal 16/11 a 65.286 $) e contro la chiamata a 81,4k.
