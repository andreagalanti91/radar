# STATO · Messaggi Telegram più chiari · avviato 25/11/2026

Stato: IN CORSO

## Prompt originale
"Rendi più chiaro i segnali del bot telegram. Più visivi, più carini, più semplici. Fammi delle preview di tutti gli stati."

## Piano
1. Inventario di tutti i messaggi inviati oggi (testo reale dal codice). 2. Nuovo formato. 3. Anteprime di tutti gli stati
(attuale contro nuovo) in `stato/telegram-preview/`. 4. Solo dopo l'approvazione dell'utente: implementazione, test, deploy.

## Vincoli
Nessun messaggio nuovo e nessun cambio al bot senza approvazione; contenuti e logica di W3.2 invariati; token solo nei Secrets.

## Avanzamento
- Inventario e anteprime: 27 tipi di messaggio + 1 alternativa, in `stato/telegram-preview/` (index.html, PROPOSTA.md, 28 PNG; tutti_*.png solo locali). FATTO.

## Decisione dell'utente (25/11)
"Procedi come proposto": tutte e 8 le scelte come raccomandato (1 sì, 2 sì, 3 sì, 4 etichetta: valore, 5 ogni messaggio di trading, 6 sì, 7 solo nella salute, 8 sì).

- Implementazione (25/11): radar/telegram.py (formato comune, riepilogo «Oggi» con riga di salute, testi tecnici), radar/weekly.py
  (eventi W3.2, stop orario con esito in $, salute), radar/cli.py (salute separata solo con problemi, avvisi fonti dentro la salute,
  v2 eliminata), guard, coherence, intraday (solo candele orarie), daily.yml/liqsnap.yml (parse_mode=HTML, RADAR_V2_ALERTS tolta),
  README. Test: tests/test_telegram_formato.py (12) + 10 file aggiornati; suite 454 test verde. Anteprime rigenerate dal codice vero
  (index.html, 28 PNG): 01–13, 16, 19, 20, 23–28 identici alla proposta. FATTO, non committato.

## Prossima azione
Presentare all'utente; dopo l'ok: commit, push, invio di prova (test-telegram) e verifica sul sito/chat.
