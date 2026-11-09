# Ciclo di ricerca intraday 2 — BTC, ETH, SOL (preregistrazione, 09/11/2026)

Richiesta dell'utente: intraday su BTC, ETH, SOL; timeframe 1h–4h; stile scelto dai dati; leva bassa 2x–5x; capitale 10.000 $;
esecuzione a mano dagli alert; long e short; pochi trade di qualità, drawdown contenuto; presa di profitto con una "costante"
(es. TP1/TP2) scelta dai test, non decisa a priori.

## Regole comuni (valgono per tutti gli agenti, fissate PRIMA dei risultati)
- Dati e motore: research/intraday2/ (engine.py). Ingresso all'apertura della barra successiva; costi 0,05% + slippage 0,02%
  per lato (0,05% sugli stop), funding reale, liquidazione alla leva scelta.
- Periodi: scelta di regole e parametri SOLO sul 2021-01-01 → 2023-12-31; giudizio sul 2024-01-01 → oggi (fuori campione),
  senza ritocchi dopo averlo visto.
- Stessi parametri sui 3 asset (nessuna taratura per asset). Capitale unico 10.000 $, una posizione per asset.
- Al massimo 8 varianti per famiglia, scritte in research/intraday2/<famiglia>/PREREG.md prima di guardare i risultati.
- Uscite di riferimento durante la scelta degli ingressi: stop 1,5 ATR, TP1 +1,5R (metà), stop a pareggio dopo TP1, TP2 +3R,
  uscita a tempo 48 barre (1h) / 12 barre (4h). Lo studio delle uscite (TP1/TP2, trailing, leva) è una fase separata.
- Leva: 2x di riferimento (sizing al rischio 1% del capitale per trade, leva massima 5x).

## Criteri per passare (fuori campione 2024→oggi)
1. Profit factor ≥ 1,3 e aspettativa ≥ +0,15R per trade al netto dei costi.
2. Max drawdown giornaliero ≤ 20% sul conto da 10.000 $.
3. Positivo in entrambe le metà (2021–23 e 2024→oggi) e su almeno 2 dei 3 asset.
4. Pochi trade: tra 2 e 12 al mese in totale sui 3 asset.
5. Placebo (ingressi casuali con stessa frequenza, lati e uscite, 500 giri): risultato sopra il 90° percentile.
6. Vicini dei parametri: la mediana dei vicini resta positiva (niente picchi isolati).
7. Senza il trade migliore il risultato resta positivo.

## Famiglie (un agente ciascuna, in parallelo)
- A · Trend e rotture 4h: rotture di range/Donchian, compressione di volatilità, filtro di regime giornaliero.
- B · Pullback nel trend 1h: ingressi 1h nella direzione del trend 4h/giornaliero (ritest di medie, RSI, VWAP di sessione).
- C · Flusso e derivati: funding estremo, open interest, delta taker, long/short ratio affollato, cascate di liquidazione.
- D · (dopo A–C) Uscite e leva: TP1/TP2/TP3, pareggio, trailing, uscita a tempo, leva 2–5x sugli ingressi che passano.
- Revisione critica finale (radar-review) prima di qualsiasi messa "su carta".

## Esito
Una strategia passa solo con tutti i criteri. Se nessuna passa, si dice chiaramente (come nella lezione 78) e niente va nel tool.
Una strategia che passa va prima SU CARTA con alert Telegram, mai direttamente con capitale reale.
