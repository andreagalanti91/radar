# STATO · Statistiche/Simulatore unificati, fonti liquidazioni, analisi messaggio trader
Data: 2026-11-13 · Stato: IN CORSO
Classe: lungo · Modello consigliato: Sonnet 5.5 (UI e ricerca dati) con Opus 5.5 per il giudizio sul flusso · Effort: alto

## Checklist
- [x] 1. Unire Statistiche e Simulatore: lista dei trade del backtest + card che apre il simulatore
- [ ] 2. Censimento fonti liquidazioni (gratuite, API pubbliche, nessuno scraping) e prova di raggiungibilità
- [ ] 3. Integrazione delle fonti utili nella raccolta oraria
- [x] 4. Analisi del messaggio del trader: flusso taker perp vs spot su Binance; verifica sui nostri dati
- [ ] 5. Test, verifica live, pubblicazione

## Decisioni aperte
- D1 Sezione unificata: nome "Storico" e rimozione del tab Simula (5 tab) — sì/no
- D2 Laboratorio (strategie su carta) nel Simulatore: rimuoverlo — sì/no
- D3 Fonti a pagamento (Coinglass API, Kaiko, CryptoQuant): escluse salvo indicazione

## Decisioni prese
- D1 sì (Storico, 5 tab) · D2 sì (Laboratorio rimosso) · D3 sì (niente fonti a pagamento) — opzioni consigliate, nessuna risposta diversa

## Log
- 2026-11-13 richiesta ricevuta, scheda di avvio presentata
- 2026-11-13 "procedi": avviati 3 agenti (UI Storico; fonti liquidazioni; test tesi flusso perp/spot)
- 2026-11-13 punto 4 chiuso: solo contesto (lezione 89)
- 2026-11-13 punto 1 chiuso: vista Storico (5 tab), Laboratorio rimosso
