# STATO — Revisione completa della strategia e del tool
Data: 13/11/2026 · Stato: IN CORSO
Classe: lunga · Opus 5.5, effort alto

- [x] 0. Chiusura del lavoro sulla mappa liquidazioni v2 (in corso)
- [x] 1. Revisori in parallelo: A1 strategia W3 (ricostruzione indipendente) · A2 segnale dal vivo e Telegram · A3 dati · A4 dashboard · A5 operazioni
- [x] 2. Verifica incrociata: ogni problema riprodotto da un agente separato, i non riprodotti si scartano
- [ ] 3. Correzioni una per volta con test (W3: prima l'approvazione dell'utente)
- [ ] 4. Protezioni permanenti: controlli di coerenza orari, avviso Telegram, regola in CLAUDE.md/RESEARCH.md
- [ ] 5. Verifica sul sito pubblicato e report

Decisioni: D1 tutto il tool; D2 correzioni dirette se non toccano W3; D3 wallet/Chento/liquidazioni inclusi, priorità bassa.
Log:
- 13/11 avviati A1, A2, A5; A3 e A4 dopo la mappa v2.
- 13/11 A1 finito: W3 riprodotta in modo indipendente trade per trade (78.473,92, DD −21,13%); nessun CRITICO; 2 MEDI (sensibilità del flusso ±1 giorno; dati provvisori OKX riscritti dall'archivio Binance), 5 BASSI.
- 13/11 A5 finito: nessun CRITICO; 3 MEDI (cron 00:30 mai partito → W3 valutato fino a ~4,7h dopo la chiusura; rebase -X theirs su .csv.gz scritti da due workflow; dati persi se push fallisce 3 volte), 5 BASSI.
- 13/11 A3 finito: 2 CRITICI sui dati provvisori OKX (flusso perp: volume OKX ~0,5–0,6× Binance e taker non pesato, scarto pf14z fino a 0,47σ; funding OKX senza colonna source, z provvisorio 1,11 vs finale 0,60) — non hanno cambiato segnali nelle ultime settimane; 1 MEDIO (taker_1h perp 28/10 mancante); BASSI. Le correzioni toccano i dati che W3 usa per decidere: richiedono approvazione.
- 13/11 A4 finito: numeri W3 corretti ovunque (simulatore = backtest); 2 MEDI (Cascata usa prezzo server invece di REF; card Oggi da flat mostra la chiusura senza etichetta), BASSI di formato/testo (MAR come rendimento/DD, decimali misti, orario FOMC fisso in marzo, testi incoerenti, etichette tagliate a 400 px).
- 13/11 A2 finito: segnale dal vivo = backtest su tutti i 13 trade (replay 2021–2026 con giri ripetuti, saltati, invii falliti); 2 MEDI (funding OKX vs Binance; stato non salvato se il push fallisce), 3 BASSI. Avviata la verifica incrociata di 21 punti.
- 13/11 verifica incrociata: confermati 2 CRITICI sugli avvisi W3 (B1 'stop toccato' dopo uscita EMA; B3 variabile con virgola blocca il giro), M4 alta operativa (giro 00:30 mai partito); M1 ridimensionato (pf14z 0,05σ, non 0,47σ); avvio correzioni in 3 agenti con file separati.
