# PROMPT · W3.2 su altri asset, ciclo 2 (top 20 crypto e top 10 azioni dal 2020) · preparato il 25/11/2026

Da incollare all'avvio o da eseguire dopo il comando "procedi". Autosufficiente: chi lo legge non ha bisogno della chat.

## Contesto
RadarSignal opera W3.2 su BTC (30.000 $) ed ETH (30.000 $, capitale separato). Regole in `radar/weekly.py`, scheda in
`memoria/01-strategia/W3.2.md`. Le due posizioni short aperte (BTC dal 16/11, ETH dal 09/11) sono in guadagno del 10% e del
15%. L'utente vuole più occasioni durante l'anno su altri asset, operabili solo su Bitget o OKX (niente ETF o ETP), con
rendimento e drawdown paragonabili. Si parte da top 20 crypto e top 10 azioni; la top 50 è un ciclo successivo.

Leggi prima, in `RESEARCH.md`: "W3 IN USO", "Memoria dell'algoritmo principale", "Errori operativi da non ripetere" e le
lezioni 74, 87, 104, 107, 110, 111, 118. Poi `research/w32_multi/README.md`, `research/w32_top100/README.md` (codice
riutilizzabile: `universe.py`, `fetch.py`, `run.py`) e `research/multi_asset/README.md` (`fetch.py` per Yahoo, `ma_lib.py`).

## Cosa è già stato fatto (da NON ripetere come studio nuovo)
- W3.2 con i parametri di BTC sulle prime 100 crypto, dal 2021: passa solo ETH (1 su 27 altcoin); TRX e SOL rendono ma con DD
  −40/−44% e WR sotto 60%; altcoin mediane DD −65% (lezione 111).
- W3.1 senza flusso perp su 13 asset, comprese le grandi azioni USA: 0 su 13 (lezione 104). Indici: 0 su 8 (lezione 110).
- Il vantaggio di W3.2 viene dal flusso perp (lezioni 74, 110): dove manca, la strategia non regge.

## Domande del ciclo 2 (in quest'ordine)
- **Q1 · Replica dal 2020.** Top 20 crypto con i parametri di BTC, W3.2 completa dove esiste il perp: cambia qualcosa
  aggiungendo il 2020? Riferimento e controllo della lezione 111, costo basso (codice esistente).
- **Q2 · Universo senza bias di sopravvivenza.** Le stesse regole sulla top 20 crypto e sulla top 10 azioni **al 01/01/2020**
  (non solo quella di oggi): quante sarebbero passate scegliendo allora?
- **Q3 · Flusso per le azioni (ipotesi nuova).** W3.2 sulle top 10 azioni con un indicatore di flusso dai dati giornalieri al
  posto del flusso perp (definizione unica, fissata nel PREREG prima dei rendimenti: per esempio pressione di volume
  settimanale tipo Chaikin Money Flow 20 giorni > 0 per i long e < 0 per gli short). Se fallisce, le azioni sono chiuse per W3.2.
- **Q4 · BTC come cancello per le altcoin (ipotesi nuova).** Un'altcoin si opera solo nello stesso verso di W3.2 su BTC, con
  le proprie regole d'ingresso e uscita. Dichiarare subito il limite: non aggiunge momenti nuovi, solo asset correlati.
- **Q5 · Parametri per classe (ipotesi nuova, la più esposta all'adattamento).** Moltiplicatore del trailing {2,0; 2,5; 3,0}
  ATR e rischio {10%, 15%, 25%} scelti sul solo IS, una scelta per classe (altcoin, azioni), non per singolo asset.
- **Q6 · Portafoglio.** BTC + ETH + eventuali candidati, capitale separato per asset come oggi: CAGR/DD e DD del conto unico
  migliorano rispetto a BTC + ETH? Conta quante operazioni l'anno si aggiungono e quanto sono sovrapposte a BTC.

## Dati (nessuna dipendenza nuova: solo numpy, pandas, requests)
- Crypto: archivio `data.binance.vision` (spot e perp USDT-M con taker buy e funding), OKX per i buchi; dal 2019-09 o dalla
  quotazione. Binance fapi e Bybit sono bloccati dal runner USA, non dal contenitore: usa l'archivio.
- Classifica crypto al 01/01/2020 e oggi: CoinGecko API pubblica, citando da dove; escludere stablecoin, wrapped, oro e RWA;
  per i token senza dati sufficienti dirlo, non sostituirli.
- Azioni: Yahoo chart API come in `research/multi_asset/fetch.py`, prezzi rettificati; classifica per capitalizzazione oggi e
  al 01/01/2020 da una fonte pubblica citata.
- Operabilità per l'utente: verificare dalle liste pubbliche degli strumenti di Bitget e OKX quali di questi asset sono
  negoziabili (perp crypto; azioni o perp su azioni) e da quando. Un asset non operabile resta nello studio ma è marcato.
- Congelare i dati in `research/w32_asset2/data/` con data di download; niente scraping contro i termini d'uso, User-Agent
  generico onesto.

## Disciplina (obbligatoria)
1. Conteggi prima di tutto (segnali per anno e per lato, anni di dati, presenza del flusso), nessun rendimento.
2. `research/w32_asset2/PREREG.md` committato DA SOLO prima di qualsiasi rendimento: universo, regole, definizione del flusso
   per le azioni (Q3), griglia di Q5, criteri, soglie, riferimenti.
3. Periodi: intero 2020-01-01 → ultimo dato; IS 2020-01 → 2022-12; OOS 2023-01 → oggi. Ogni periodo riparte da 10.000 $.
4. Criteri per asset (come `w32_top100`): 1 CAGR/DD sopra il buy & hold · 2 DD non peggiore di −35% · 3 WR ≥ 60% · 4 entrambe
   le metà positive · 5 almeno 8 trade. Poi conferma (senza il trade migliore; vicini 2,0/3,0 ATR) e placebo (1.000 ingressi a
   caso nello stesso regime, stesso numero e lato), Holm sul numero di asset provati per domanda.
5. Q5 si giudica solo in OOS con la scelta fatta in IS; il risultato a posteriori si riporta come "non utilizzabile".
6. Costi: crypto 0,10% per lato più funding reale; azioni 0,05% per lato e short 3% annuo; perp su azioni con il funding
   reale se esiste, altrimenti stima dichiarata.
7. Riferimenti in ogni tabella: BTC W3.2 (78.474 $ dal 2021), ETH W3.2, buy & hold, liquidità.
8. Revisione critica con un agente separato (`radar-review`, sola lettura) che ricalcola a mano alcuni trade; un solo secondo
   ciclo, per errore del motore o ipotesi nata dalla diagnosi, con addendum committato prima.

## Vincoli
- W3.2, `radar/weekly.py`, i segnali, gli stop e i capitali di BTC ed ETH non si toccano. Nessun avviso Telegram nuovo.
  Nessuna modifica al tool o deploy.
- Se un asset passa tutto: proposta all'utente con capitale separato (come ETH), rischio, operabilità su Bitget/OKX e cosa
  cambierebbe nel tool. Nulla viene attivato senza la sua approvazione esplicita.
- Agenti: Opus 5.5, effort medium. Due agenti non scrivono mai gli stessi file. Commit sul branch di lavoro
  `claude/swing-strategy-review-5g3jul`; file di stato `stato/STATO-w32-asset2.md` aggiornato a ogni fase.

## Consegna
`research/w32_asset2/README.md`: verdetto in testa (una riga per Q1–Q6), tabelle per asset (finale, CAGR, DD, trade, WR,
buy & hold, IS/OOS, criteri falliti, operabile sì/no), portafoglio, cosa significa per l'operatività, limiti, deviazioni dal
PREREG, lezione 123 per `RESEARCH.md`; aggiornare `research/README.md` e `memoria/02-ricerca/INDICE.md`. Riepilogo finale
all'utente: conclusione in testa, numeri essenziali, proposte in attesa di decisione, se e come estendere alla top 50.
