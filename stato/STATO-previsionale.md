# Stato — Modello previsionale direzionale BTC (7 e 30 giorni)

**Stato:** IN CORSO · 23/11/2026 · Fable 5.2 high (regia), agenti radar-ricerca, radar-review, radar-ui

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
- [ ] 1. radar-ricerca: PREREG (da solo), dataset, modelli, validazione walk-forward, test come filtro/dimensione di W3.2   ← IN CORSO
- [ ] 2. radar-review: revisione critica
- [ ] 3. Se passa: registro delle previsioni + riga in Pre-analisi/dashboard/Telegram, test, deploy; altrimenti solo report e lezione
- [ ] 4. Memoria, RESEARCH.md (lezione 112), chiusura

## Come riprendere
**Prossima azione:** attendere l'esito dell'agente di ricerca (research/previsionale/), poi revisione critica.
