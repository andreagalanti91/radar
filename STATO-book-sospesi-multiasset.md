# Stato — Book multi-borsa con liquidazioni e sentiment, lavori in sospeso, swing su azioni e materie prime

**Stato:** IN CORSO
**Ultimo aggiornamento:** 2026-11-22
**Modello / effort usati:** Fable 5.2 · high (regia), agenti radar-ui, radar-dati, radar-ricerca, radar-review

## Prompt originale
> (due screenshot di un post X: heatmap dell'order book ETHUSDT e BTCUSDT a 30 minuti, linea del prezzo, muri etichettati con
> prezzo e dimensione — es. 62.000 · 7,35M, 59.050 · 1,91M —, scala d'intensità 3×–8×, profilo laterale)
> Utilizza orchestratore. Modifica nel tool, sezione orderbook voglio una cosa simile. Estrapolare i dati live da altri. Binance e
> altri. Interpolare con liquidazioni per determinazione del sentiment di mercato. Orderbook e liquidazione fanno capire se si va
> up o down. Attenzione anche alle manipolazioni mercato, market maker. Riprendi task che erano in sospeso. Analizzare strategia
> anche su mercato azionario e materie prime.

Poi: "Ok procedi. Backtesta tutto. Apprendi dai propri sbagli e revisiona".

## Scelte dell'utente
- Nessuna risposta puntuale alle domande: valgono i default della scheda. Autonomia A su formula del sentiment e sospesi che non
  toccano W3.1; le correzioni che toccano i dati di W3.1 si presentano prima. NESSUN DEPLOY senza autorizzazione esplicita (il
  sito si pubblica dal branch predefinito claude/vibrant-brahmagupta-fvv2gh; questa sessione scrive su
  claude/swing-strategy-review-5g3jul). Strategia multi-asset = swing S/R (stop 5–10%, TP 10–15%). Book: BTC ed ETH.
- "Backtesta tutto": anche l'indicatore di sentiment va testato sullo storico disponibile.

## Specifica comune del sentiment (fissata dalla regia prima dei test)
- I = (bid_usd − ask_usd) / (bid_usd + ask_usd) entro ±1% dal prezzo medio, book aggregato delle borse.
- L = (liquidazioni short − liquidazioni long) / (somma) in dollari negli ultimi 30 minuti (0 se non ci sono liquidazioni).
- S = 0,5·I + 0,5·L in [−1, +1]; S > +0,2 "pressione al rialzo", S < −0,2 "pressione al ribasso", altrimenti "neutro".
- Manipolazione: muro = livello ≥ 3× la media dei livelli visibili; "ritirato" se scompare (−70%) mentre il prezzo è entro 0,3% senza
  scambi corrispondenti; "eseguito" se scompare con il prezzo che lo attraversa. In pagina: "non validato" finché non c'è il test.

## Piano
- [ ] A. radar-ui: radar/pages/book.html (heatmap 30 min, più borse, etichette muri, liquidazioni, sentiment, muri ritirati)   ← IN CORSO
- [ ] B. radar-dati: registro lato server di muri (ritirati/eseguiti) e liquidazioni per validare il sentiment   ← IN CORSO
- [ ] C. sospesi: punti 3–5 di STATO-revisione.md e voci aperte di memoria/04 che non toccano W3.1   ← IN CORSO
- [ ] D. radar-ricerca: swing S/R su azioni e materie prime (research/swing_sr_multi/)   ← IN CORSO
- [ ] E. radar-ricerca: backtest del sentiment sullo storico disponibile (research/book_sentiment/)   ← IN CORSO
- [ ] F. Revisione critica (radar-review) di D ed E e del codice di A/B/C
- [ ] G. Suite verde, render 400/1280, commit e push sul branch di lavoro; deploy solo con autorizzazione

## Risultati e file prodotti
- (in corso)

## Decisioni prese
- Orchestrazione con cinque agenti in parallelo su file separati, regia nella sessione principale (in autonomia).

## Problemi aperti
- Deploy non autorizzato: chiedere all'utente a fine lavoro.

## Come riprendere
**Prossima azione:** raccogliere gli esiti degli agenti A–E; nessun agente committa (tranne i PREREG, da soli). Poi fase F e G.
