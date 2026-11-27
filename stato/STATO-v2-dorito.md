# STATO · Oggi in variante V2 + studio indicatore "dorito" · avviato 26/11/2026

Stato: IN CORSO

## Prompt originale
"Analizza questo indicatore come gli altri. Stesso procedimento avvia ciclo di backtest e se serve implementare nella strategia.
Per la grafica ok V2. Procedi" (screenshot post X @CryptoJelleNL: "The famous dorito indicator has flashed again… flashes when
a trend is getting exhausted - and usually means a reversal is near", grafico BTC con triangoli; research/dorito/post_utente.png).

## Decisioni
- Vista Oggi del tool in variante V2 "Una domanda per scheda" (stato/ux-varianti/oggi5/V2.html), con il Mercato power incluso;
  grafica del resto del tool invariata. W3.2 e numeri invariati.
- Dorito: ricostruire la logica da fonti pubbliche, PREREG committato da solo, backtest come gli altri indicatori (da solo e
  come filtro/uscita su W3.2), revisione critica; nel tool solo se supera i criteri (e prima chiesto all'utente).

## Prossima azione
Due agenti in parallelo: UI (template) e ricerca (research/dorito/).

## Aggiornamento 26/11 22:25 UTC · COMPLETATO
- Dorito: esito negativo (0/8, placebo p 0,44–1,00), lezione 127; nessun ingresso in W3.2.
- V2 Oggi: commit 225b0ec, deploy, verifica sul sito a 400/1280: 6 schede presenti, 12 link Dettagli, pannello apre, 0 errori JS.
- In attesa dell'utente: % BTC in "Come vanno le posizioni?" (sul capitale +6,8% o movimento prezzo +7,0%).
