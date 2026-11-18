# STATO — Pre-analisi giornaliera + nuovi indicatori/strategie + pensiero dirompente
Data: 18/11/2026 · Stato: IN CORSO · Parte 1 oggi, Parte 2 report domattina 09:00
Classe: lunga · Opus 5.5, effort alto

Parte 1 (tool)
- [x] Backend: preview.position_block (W3 short: P&L, stop, soglia d'uscita EMA21, distribuzione) e preview.today (flussi, funding, OI, liquidazioni, mappa, distanze, S/R con tenuta storica vs casuale, situazioni simili con IC)
- [ ] UI: blocchi Posizione e "Oggi · contesto" nel riquadro Pre-analisi
- [x] Riepilogo Telegram giornaliero "RADAR SIGNAL BTC · Oggi" (una volta al giorno, indipendente da v2)
- [ ] Test, render con dati reali, deploy, verifica online
Parte 2 (ricerca)
- [ ] PREREG committato da solo (opzioni/DVOL, dimensione della posizione, ETH/BTC e dominanza, piramidazione) con conteggio eventi
- [ ] Backtest e revisione critica
- [x] Pensiero dirompente: cosa non torna in W3 e nel sistema
- [ ] Report 09:00
Log:
- 18/11 avviati backend, UI, avvocato del diavolo e PREREG Parte 2.
- 18/11 pensiero dirompente: rischio allo stop 25% per trade (vincolo DD ≤ 15–20% violato), short con base debole; proposta rischio 10–15% (lezione 99), decisione dell'utente.
- 18/11 decisioni dell'utente: rischio per trade → decide dopo il test della Parte 2; short aperto → tenuto così (esposizione 0,97).
- 18/11 delega dell'utente: decido io stop, TP e capitale investito con backtest dal 2021 e aggiorno la strategia valida. Regola di scelta preregistrata in F2: max CAGR/DD con DD ≤ 15% (2021+) e ≤ 25% (2018–20), perdita allo stop ≤ 15%, OOS non peggiore di W3, vicini stabili; altrimenti rischio 10% con stop attuale. Backend pre-analisi giornaliera pubblicato (204 test).
