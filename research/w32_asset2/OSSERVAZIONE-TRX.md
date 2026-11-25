# Osservazione sulla carta · TRX con il cancello di BTC · regole fissate il 25/11/2026

Decisione dell'utente del 25/11/2026 ("Ok procedi tutto") sulla proposta della lezione 123. Solo carta: nessun capitale, nessun
ordine, nessun avviso Telegram. Le regole sotto non si cambiano durante l'osservazione.

## Regole (identiche a Q4 di `PREREG.md`, commit f40f7a6)
- Motore `radar.weekly` invariato (W3.2: SMA 40 settimane, EMA 20/21, flusso perp di TRX, filtro MACD, trailing 2,5 ATRw,
  uscita su EMA 21 e distribuzione, rischio 25%), applicato a TRX con i dati spot e perp TRXUSDT.
- Cancello: si entra solo se alla stessa domenica W3.2 su BTC è in posizione nello stesso verso (o vi entra quel giorno). Le
  uscite sono quelle di TRX.
- Capitale sulla carta: 10.000 $ (circa 1/6 del capitale crypto di 60.000 $), separato da BTC ed ETH.

## Registro e valutazione
- Registro in avanti dal 25/11/2026 (`data/trx_carta.json`): ogni ingresso e uscita con data, prezzo, motivo, risultato.
- Riferimento storico (backtest, non ripetibile): dal 06/2020 87.198 $ da 10.000, DD −22,5%, 12 trade, WR 83%; senza i due
  migliori 17.017 $. Circa 1,9 operazioni l'anno: in 12 mesi ci si aspettano 1–3 operazioni.
- Valutazione a 6 e a 12 mesi (fine maggio e fine novembre 2027): operazioni, risultato, DD, confronto con BTC ed ETH nello
  stesso periodo. La decisione di passare a una quota reale spetta all'utente; con meno di 3 operazioni chiuse il registro non
  basta per giudicare e lo si dice.
