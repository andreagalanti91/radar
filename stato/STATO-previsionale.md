# Stato — Modello previsionale direzionale BTC (7 e 30 giorni)

**Stato:** IN ATTESA DELL'UTENTE · 23/11/2026 · Fable 5.2 high (regia), agenti radar-ricerca, radar-review, radar-ui

## Prompt originale
> Nella conversazione analisi strategie abbiamo notato che questa 3.2 è la migliore. Adesso ti chiedo tramite apprendimento e
> imparare dai propri errori un modello previsionale di prezzo. Non deve essere preciso deve avere direzionalità. Fammi domande,
> analizziamolo insieme, costruiamolo insieme. Utilizza orchestratore. Questo è ultimo step per riuscire ad essere profittevoli
> nel mercato btc
Risposte: "Previsionale a 7 giorni, 30 giorni. Probabilità in Dashboard. Da capire se funzionale per la strategia 3.2. Solo btc.
Ok per il resto fai tu analisi sulla migliore decisione da prendere. Procedi".

## Scelte
- Orizzonti 7 e 30 giorni; solo BTC; uscita = probabilità in dashboard (contesto). Test se utile a W3.2 come filtro o dimensione:
  si applica SOLO se batte W3.2 e con il sì dell'utente.
- Default della regia: fascia incerta 45–55%; soglia di successo ≥ 55% di direzioni corrette fuori campione in 2021–23 e 2024–26
  e meglio dei riferimenti (sale sempre, persistenza, segnale W3.2); registro delle previsioni salvate prima dell'esito.

## Piano
- [x] 1. Ricerca: NON FUNZIONA a 7 e 30 giorni (uguale a "sale sempre", AUC < 0,5, 0/8 test; su W3.2 0/8 varianti) — PREREG f656594
- [x] 2. Revisione critica: verdetto confermato, nessun errore; correzioni annotate nel README
- [x] 3. Nulla in dashboard (non supera i criteri)
- [x] 4. Lezione 112, memoria aggiornate

## Come riprendere
**Domanda in attesa:** l'utente vuole il registro prospettico? Una sola regola fissata ora (segno del flusso perp a 30 giorni con
|pf| > 0,5), salvata ogni domenica prima dell'esito con research/previsionale/forecast_log.py, mostrata in dashboard come
"in prova, non un segnale" e giudicata contro "sale sempre" dopo ≥ 100 previsioni risolte (~2 anni). Se sì: portare forecast_log
nel tool con test, riga nella Pre-analisi, deploy.
