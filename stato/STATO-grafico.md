# Stato — Oggi come panoramica, Grafico professionale, un solo motore per livelli e liquidazioni

**Stato:** IN CORSO · 24/11/2026 · Opus 5.5 medium (regia), agente radar-ui

## Prompt originale (sintesi fedele)
> Le liquidazioni di "oggi" non corrispondono con "liquidazioni" e nemmeno con "grafico": deve essere tutto coerente, stesso motore.
> Eliminare Liquidazioni dalla navigazione. Oggi: solo overview (Livelli e probabilità a 30 giorni come forbice con principali
> supporti, resistenze e liquidazioni vicine), contesto, notizie di oggi. Grafico: approfondimento completo e professionale, solo
> BTC, volumi, togliere MACD, interruttori on/off per liquidazioni/supporti/resistenze, sotto TUTTI i livelli come in Oggi.
Risposte: "Calcola sul prezzo live" · "Grafico 4h, giornaliero, settimanale e mensile" · "Procedi".

## Decisioni
- Motore unico: report["livelli"] (radar/livelli.py) per Oggi, Grafico, tabella, Pre-analisi e Telegram; nessun ricalcolo dei
  cluster nel browser. Probabilità e distanze ricalcolate sul prezzo live nel browser con i parametri del cono (radar/cone.py).
- Liquidazioni: fuori dal menu, pagina conservata e riattivabile (come Book).
- 4h dal browser (Binance, riserva Coinbase); 1D e 1W dai dati del tool; mensile costruito dal giornaliero.

## Piano
- [ ] 1. radar-ui: Oggi panoramica, Grafico professionale, motore unico, Pre-analisi/Telegram allineati, test, render   ← IN CORSO
- [ ] 2. Regia: suite, render, commit, deploy, verifica sul sito

## Come riprendere
**Prossima azione:** attendere l'agente; poi suite, render, deploy.
