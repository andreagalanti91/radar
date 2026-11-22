# STATO — Ingressi/uscite (DCA, TP, stop), book e liquidazioni, proposte della revisione
Data: 22/11/2026 · Stato: COMPLETATO · Regia Fable 5.2, ricerca e dati Opus 5.5
- [x] 1. Applicate subito: registro domenicale provvisori vs definitivi; soglie d'allarme (equity −15%, 2 stop consecutivi) con avviso Telegram; registro dei muri del book lato server
- [x] 2. PREREG (da solo): griglia ingresso (unico / DCA a tempo / su ritracciamento) × uscita (unica / a scaglioni) × TP × stop k; decisione su 7 giorni; uscita per distribuzione
- [x] 3. Backtest e confronto vecchia vs nuova (2021+, IS/OOS, 2018–20)
- [x] 4. Book + liquidazioni + S/R sullo storico orario disponibile (3–4 settimane: indicativo)
- [x] 5. Revisione critica, report, memoria/
Decisione D1: se una configurazione supera i criteri → prima i dati all'utente, poi si applica.
Log:
- 22/11 avvio.
- 22/11 punto 1 online; PREREG ingressi/uscite 08da8cc; book e liquidazioni: nessun supporto misurabile (15 giorni, indicativo), da rifare 20/12 (1h) e marzo 2027 (muri).
- 22/11 backtest: nessuna delle 14 varianti batte W3.1 (lezione 105). Il motore è stato esteso dopo il PREREG con due funzioni di registrazione senza cambiare le regole (riproduzione verificata, deviazioni nel README). Revisione critica separata: non eseguita, esito nullo (nessuna proposta da applicare).
