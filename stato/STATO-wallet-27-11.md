# STATO · Wallet (posizioni reali) e stati del bot 27/11/2026
Stato: PUBBLICATO (attesa prova di accesso dell'utente)

Richiesta: voce di menu "Wallet" separata con posizioni reali (aggiungi, modifica, DCA, performance, confronto con la strategia);
login Supabase senza registrazione (gli account li crea l'utente, uno per email); stile e brand (brand/DESIGN.md). Inoltre: rivedere
gli stati del bot Telegram e definirne la lista.

## Fasi
1. Inventario stati del bot (Explore) → lista da definire con l'utente. [ ]
2. Pagina Wallet + supabase/schema.sql + modalità demo per anteprime (radar-ui). [ ]
3. Progetto Supabase: la creazione via API è negata (accesso limitato al progetto "Training App"); serve che l'utente crei il progetto
   "RadarSignal Wallet" (gratuito). Non usare Training App: disattivare le registrazioni lì toccherebbe l'altra app. [ ]
4. Configurazione (schema, registrazioni disattivate, segreti GitHub RADAR_SUPABASE_URL/RADAR_SUPABASE_ANON), test, render, deploy, verifica. [ ]
- 27/11 16:28 UTC: online login globale, Wallet, Profilo, tab bar scorrevole; verifica: schermata di accesso a 400/1280, supabase-js 2.119.0 caricato, 0 errori JS. Da fare: prova di accesso reale dell'utente, registrazione PIEVERSE, decisioni sul bot (stato/BOT-STATI.md), protezione vera dei dati (proposta).
