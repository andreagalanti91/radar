# STATO · Scheda "Ciclo on-chain" nella posizione aperta · avviato 25/11/2026

Stato: COMPLETATO (25/11/2026)

## Prompt originale
"Interessante l'indicatore quindi. Aggiungi sul tool durante la posizione aperta un informazione riguardante questo
indicatore. Non so come basta dia valore aggiunto ad una decisione. Anche in formato grafico ok."

## Decisioni
- Fonte: MVRV CoinMetrics community (sostituto pubblico dell'UTXO P/L di CryptoQuant), una volta al giorno; zone come in
  research/utxo_pl (capitolazione = 10% più basso a 4 anni, euforia = 10% più alto; riferimenti 1,0 e 3,0).
- Solo contesto (lezione 125): nessuna regola di W3.2 cambia, nessun avviso Telegram.
- Posizione: pagina Posizioni, nel pannello della posizione aperta (BTC); frase adattata al verso della posizione.

## Fatto (agente, 25/11)
- radar/onchain.py (MVRV CoinMetrics, data/mvrv.csv ~5 anni, ripiego cache + research/utxo_pl/mvrv.csv), aggancio _soft in
  radar/cli.py (report["onchain"]), scheda in dashboard_template.html (card BTC sotto "Quando esce"; da flat card in fondo).
- tests/test_onchain.py (12 test); suite completa verde (518); render 400/1280 chiaro/scuro guardati, 360 px senza overflow.
- Stato 24/11: capitolazione dal 18/11, MVRV 1,126 (soglia 1,202; euforia 2,334), percentile 4 anni 5%.

## Prossima azione
Revisione dell'utente, poi commit, deploy e verifica sul sito (non fatti dall'agente).

## Deploy e verifica (25/11, 20:05 UTC)
Suite 518 test; giro riuscito (commit 75d471f); sito: scheda in Posizioni dopo «Quando esce», capitolazione dal 18/11 (MVRV 1,126; soglie 1,20/2,33; percentile 5%), 0 errori JS, nessun overflow a 400/1280. Nessun ripiego segnalato; in questo giro non è servito scaricare (dato del 24/11 già fresco): la risposta di CoinMetrics dal runner USA si vede al primo giro di domani (controllo programmato lunedì 30/11 insieme allo Scanner).
