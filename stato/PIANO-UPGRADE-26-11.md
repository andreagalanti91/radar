# Piano di miglioria · strategia e tool · per il 26/11/2026, ore 8:00

**In sintesi:** W3.2 non va riscritta: tredici famiglie di idee testate in questi giorni non la battono (lezioni 106–126). Il margine
vero adesso è altrove: **affidabilità dei dati del segnale, esecuzione dal vivo, controllo nel tempo**. Sotto le proposte in ordine
di priorità, con costo stimato e cosa serve da te. Nulla parte senza il tuo ok.

## A. Prima del prossimo segnale (priorità alta)

| # | Proposta | Perché | Costo | Serve da te |
|---|---|---|---|---|
| A1 | **Dati provvisori OKX del flusso perp**: correggere i due problemi critici rimasti aperti dalla revisione del 13/11 (volume OKX ≈ 0,5–0,6× Binance e taker non pesato; funding OKX senza fonte). Il segnale della domenica può partire con dati provvisori diversi dai definitivi | Il flusso perp è il cuore del vantaggio di W3.2 (lezioni 74, 110): un segnale sbagliato per dati provvisori costa più di qualsiasi ottimizzazione | medio | scelta fra le 3 opzioni già proposte (stato/STATO-revisione.md) |
| A2 | **Diario delle operazioni vere**: dal primo segnale reale, registro di prezzo eseguito, data, importo, commissioni e slittamento rispetto al segnale, con confronto automatico "reale contro modello" in Movimenti | Inizi a operare al prossimo segnale: serve misurare subito se l'esecuzione reale segue il backtest | medio | ok; come inserire le operazioni (comando al bot o file) |
| A3 | **Invio di prova del nuovo formato Telegram** | Il riquadro richiudibile non è ancora stato visto in chat | minimo | "invia prova" |
| A4 | **Promemoria del lunedì** con i testi nuovi | Il resoconto settimanale si può aggiornare solo dalla conversazione originale | minimo | aggiornarlo da lì (testo pronto in `deploy/RESOCONTO-SETTIMANALE.md`) |

## B. Controllo nel tempo (priorità media)

| # | Proposta | Perché | Costo |
|---|---|---|---|
| B1 | **Allarme "fuori dal backtest"**: avviso se il calo dal vivo supera il peggiore storico (−21% dal 2021, −37% dal 2018) o se le perdite di fila superano 2 | Unico modo onesto di capire presto se la strategia ha smesso di funzionare | basso |
| B2 | **Revisione semestrale fissa** (fine maggio, fine novembre): W3.2 reale contro modello, distacco BTC−ETH (lezione 124), TRX sulla carta, registro scommesse, opzioni sulla carta | Le decisioni sul peso BTC/ETH e sulle osservazioni hanno date già fissate: farle in un'unica sessione | basso |
| B3 | **Studi da rifare con più dati**: book e liquidazioni (20/12 e marzo 2027), sentiment book (febbraio 2027) | Erano "non dimostrabili" per pochi giorni di dati, non bocciati | medio |

## C. Tool (priorità media-bassa)

| # | Proposta | Perché | Costo |
|---|---|---|---|
| C1 | **Pagina più leggera**: oggi `index.html` pesa 1,1 MB (dati incorporati); caricare a parte i dati delle pagine secondarie (Scanner, Notizie, storico) | Apertura più veloce dal telefono | medio |
| C2 | **Legenda del Grafico apribile su telefono** (proposta già fatta) | Leggibilità | basso |
| C3 | **Vista "Confronto" v1** solo se la vuoi (consiglio: no, il rapporto basta) | — | medio |
| C4 | **Opzioni**: riattivarle quando vorrai riprenderle (calcolo e archivio girano già) | — | minimo |

## D. Da non fare (già provato, non funziona)

Swing su supporti/resistenze, TP fissi o con rientro, cascata, forza giornaliera, EMA/SMA, Supertrend, Zeiierman, metodo TraderA,
previsionale, trend multi-mercato, W3.2 su altcoin e azioni (salvo TRX in osservazione), screener per scegliere gli asset, peso
100% BTC, v1 a 17 indicatori, indicatore UTXO/MVRV come regola, filtri VIX. Restano come contesto nel tool dove già presenti.

## Proposta di ordine per domani

1. A1 (decisione tua sulle 3 opzioni, poi studio preregistrato e correzione) · 2. A2 · 3. A3 + A4 · 4. B1 · poi il resto.

Controlli automatici già programmati: lunedì 30/11 alle 10:00 (Scanner, registro scommesse, cache, dato MVRV dal server).
