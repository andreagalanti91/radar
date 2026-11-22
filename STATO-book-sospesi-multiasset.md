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
- [x] A. Pagina Book: heatmap 30 min, sei borse, muri, liquidazioni, sentiment descrittivo, muri ritirati/eseguiti — 47c9027
- [x] B. Registro lato server di muri ed esiti e di book_sentiment.csv — ef9edba (+ correzioni della revisione)
- [x] C. Sospesi: coherence.py con avviso, Pre-analisi più corta, testi e decimali — committato; STATO-revisione IN ATTESA DELL'UTENTE
- [x] D. Swing S/R su 15 asset: 0/15 validi (lezione 107) — PREREG beb05af
- [x] E. Backtest del sentiment: 0/14 test, descrittivo (lezione 108) — PREREG dacb01d
- [x] F. Revisione critica: verdetti confermati; corretti il registro (riga rovinata azzerava il file) e la soglia di 250.000 $ su L
- [x] G. Suite verde (283), render 400/1280, deploy autorizzato dall'utente: run 404 e 405 success
- [x] H. Richiesta aggiuntiva "Organizza bene GitHub e README": README riscritto, research/README.md (indice), lezioni 107–108
- [ ] I. radar-verifica sul sito pubblicato   ← IN CORSO

## Decisioni prese
- Cinque agenti in parallelo su file separati, regia nella sessione principale (in autonomia).
- Regola del muro in pagina più stretta della specifica (anche ≥ 2× le fasce vicine), dichiarata in pagina (scelta dell'agente UI, accettata).
- Soglia di 250.000 $ su L in pagina e nel registro (dalla revisione critica, in autonomia: non tocca W3.1).
- I tre punti sui dati provvisori OKX di W3.1 NON applicati: richiedono una scelta esplicita dell'utente.

## Problemi aperti
- Promemoria del lunedì: il testo si cambia solo dalla conversazione originale; non modificato. Testo pronto in deploy/RESOCONTO-SETTIMANALE.md.
- Rischio latente: book_walls.csv riscritto sul posto (un solo workflow lo scrive; manca un test su merge_file).
- radar/pages/liquidazioni.html usa ancora il vecchio percorso WebSocket di Binance forceOrder.
- Pulizie della radice da confermare: STATO-*.md in una cartella, gengar-skill.zip, nome del branch predefinito.

## Come riprendere
**Prossima azione:** leggere l'esito di radar-verifica; correggere eventuali problemi; poi Stato: COMPLETATO.
