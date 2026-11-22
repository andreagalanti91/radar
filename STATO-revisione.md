# STATO — Revisione completa della strategia e del tool
Data: 13/11/2026 · aggiornato 22/11/2026 · Stato: IN ATTESA DELL'UTENTE
Classe: lunga · Opus 5.5, effort alto

- [x] 0. Chiusura del lavoro sulla mappa liquidazioni v2 (in corso)
- [x] 1. Revisori in parallelo: A1 strategia W3 (ricostruzione indipendente) · A2 segnale dal vivo e Telegram · A3 dati · A4 dashboard · A5 operazioni
- [x] 2. Verifica incrociata: ogni problema riprodotto da un agente separato, i non riprodotti si scartano
- [x] 3. Correzioni una per volta con test: chiuse tutte quelle che non toccano W3.1 (inventario sotto); quelle su W3.1 attendono l'utente
- [x] 4. Protezioni permanenti: controlli di coerenza orari (radar/coherence.py), avviso Telegram, regola in CLAUDE.md/RESEARCH.md
- [ ] 5. Verifica sul sito pubblicato e report: le correzioni del 22/11 sono verificate in locale (400/1280, chiaro/scuro, report pubblicato del 21/11) ma NON pubblicate: il deploy richiede l'autorizzazione dell'utente

Decisioni: D1 tutto il tool; D2 correzioni dirette se non toccano W3; D3 wallet/Chento/liquidazioni inclusi, priorità bassa.
Log:
- 13/11 avviati A1, A2, A5; A3 e A4 dopo la mappa v2.
- 13/11 A1 finito: W3 riprodotta in modo indipendente trade per trade (78.473,92, DD −21,13%); nessun CRITICO; 2 MEDI (sensibilità del flusso ±1 giorno; dati provvisori OKX riscritti dall'archivio Binance), 5 BASSI.
- 13/11 A5 finito: nessun CRITICO; 3 MEDI (cron 00:30 mai partito → W3 valutato fino a ~4,7h dopo la chiusura; rebase -X theirs su .csv.gz scritti da due workflow; dati persi se push fallisce 3 volte), 5 BASSI.
- 13/11 A3 finito: 2 CRITICI sui dati provvisori OKX (flusso perp: volume OKX ~0,5–0,6× Binance e taker non pesato, scarto pf14z fino a 0,47σ; funding OKX senza colonna source, z provvisorio 1,11 vs finale 0,60) — non hanno cambiato segnali nelle ultime settimane; 1 MEDIO (taker_1h perp 28/10 mancante); BASSI. Le correzioni toccano i dati che W3 usa per decidere: richiedono approvazione.
- 13/11 A4 finito: numeri W3 corretti ovunque (simulatore = backtest); 2 MEDI (Cascata usa prezzo server invece di REF; card Oggi da flat mostra la chiusura senza etichetta), BASSI di formato/testo (MAR come rendimento/DD, decimali misti, orario FOMC fisso in marzo, testi incoerenti, etichette tagliate a 400 px).
- 13/11 A2 finito: segnale dal vivo = backtest su tutti i 13 trade (replay 2021–2026 con giri ripetuti, saltati, invii falliti); 2 MEDI (funding OKX vs Binance; stato non salvato se il push fallisce), 3 BASSI. Avviata la verifica incrociata di 21 punti.
- 13/11 verifica incrociata: confermati 2 CRITICI sugli avvisi W3 (B1 'stop toccato' dopo uscita EMA; B3 variabile con virgola blocca il giro), M4 alta operativa (giro 00:30 mai partito); M1 ridimensionato (pf14z 0,05σ, non 0,47σ); avvio correzioni in 3 agenti con file separati.
- 22/11 inventario dei problemi MEDI/BASSI del log, verificato sul codice (il dettaglio dei BASSI di A1, A2 e A5 non è nel repository: solo il conteggio):

| Voce | Stato | Riferimento |
|---|---|---|
| B1 avviso "stop toccato" dopo uscita EMA; B3 variabile con virgola | già risolta | weekly._env_float, tests/test_alerts.py |
| M4 giro 00:30 mai partito | già risolta | daily.yml (cron :07/:37 + catena liqsnap, gate), cli.brief_due, test_workflows.TestGate |
| M5 rebase -X theirs sui .csv.gz | già risolta | liqsnap sync, test_workflows.test_niente_theirs_e_requirements |
| M6 / A2 stato e dati persi se il push fallisce | già risolta | daily.yml: 5 tentativi, stato in cache, avviso; TestStateRestore |
| A3 taker_1h perp 28/10 mancante | già risolta | data/taker_1h.csv: 24 ore su 24 il 28/10, nessuna ora mancante |
| A4 Cascata con prezzo server invece di REF | già risolta | pages/liquidazioni.html: price() usa window.REF |
| A4 card Oggi da flat senza etichetta | già risolta | dashboard_template.html: "prezzo BTC alla chiusura del…" |
| A4 MAR come rendimento/DD | già risolta | dashboard_template.html: riga "Rend./DD" |
| A4 orario FOMC fisso in marzo | già risolta | news.fomc_time_rome |
| A4 etichette tagliate a 400 px | corretta 22/11 | "Treasury 10 anni" tagliato nella Pre-analisi; tests/test_dashboard_phone.py |
| A4 decimali misti | corretta 22/11 (caso trovato) | funding "−0,0%/anno" → preview._fund_txt |
| A4 testi incoerenti | corretta 22/11 | "Limiti": 78.000 $ e DD −21% (W3 al 25%) → numeri W3.1 dal report |
| Punto 4: controlli che scrivevano solo nel log | corretta 22/11 | radar/coherence.py + cli.daily, tests/test_coherence.py |
| Pre-analisi lunga su telefono (memoria/04) | corretta 22/11 | card da 1.126 a 706 px a 400 px, nessuna informazione tolta |
| Promemoria del lunedì scritto per W2 (memoria/04) | aperta | attività pianificata fuori dal repo: testo W3.1 pronto in deploy/RESOCONTO-SETTIMANALE.md, modificabile solo dalla conversazione principale |
| A3 CRITICI: flusso perp provvisorio OKX (volume 0,5–0,6× Binance, taker non pesato) | aperta, tocca W3.1 | data.fetch_perp; da 22/11 lo misura provlog.py |
| A3/A2: funding provvisorio OKX (z 1,11 contro 0,60 definitivo) | aperta, tocca W3.1 | data.fetch_funding; colonna source aggiunta il 22/11 (solo etichetta) |
| A1: sensibilità del flusso a ±1 giorno; provvisori riscritti dall'archivio | aperta, tocca W3.1 | weekly.live_flow; coherence.py avvisa se lo storico cambia |

- 22/11 resta aperto, e perché: (1) i tre punti su W3.1 qui sopra e l'uscita "distribuzione" → decisione dell'utente; (2) promemoria del
  lunedì → va applicato dalla conversazione principale (prossimo avvio 23/11 08:41 con il testo vecchio); (3) deploy e verifica
  online delle correzioni del 22/11 → autorizzazione dell'utente; (4) liqstream su VM europea e verifica della vista Book dal
  browser dell'utente → serve l'utente.
