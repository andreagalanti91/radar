# Stato — Oggi come panoramica, Grafico professionale, un solo motore per livelli e liquidazioni

**Stato:** COMPLETATO · 24/11/2026 · Opus 5.5 medium (regia), agente radar-ui

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
- [x] 1. Oggi forbice + Contesto + notizie; Grafico BTC 4h/1D/1W/1M con volumi, 11 interruttori, tabella completa; motore unico report["livelli"] anche per Pre-analisi e Telegram; calcolo live JS = Python; LIQ_ON=false; 398 test verdi
- [x] 2. Deploy e verifica sul sito (24/11 10:21 UTC): LIQ_ON=false, Liquidazioni fuori dal menu, livelli.tocco e livelli.serie presenti, MACD solo nei testi delle regole di W3.2

## Come riprendere
**Prossima azione:** nessuna. Facoltativo: legenda del grafico apribile su telefono.
