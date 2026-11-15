# N3 · Preregistrazione (scritta il 15/11/2026 PRIMA di calcolare qualsiasi risultato condizionato)

Dati verificati da questo container (curl 200), salvati in `data/`: FRED DFF, WALCL, WTREGEN, RRPONTSYD, DTWEXBGS, M2SL
(fredgraph.csv, pubblico); DefiLlama `stablecoins.llama.fi/stablecoincharts/all` (API pubblica gratuita); calendario FOMC
ufficiale (federalreserve.gov, stessa pagina già letta da radar/news.py); Coinbase Exchange API pubblica (candele 1d BTC-USD e
USDT-USD). Prezzo BTC: `data/spot.csv` (Binance BTCUSDT, chiusura 00:00 UTC). Nessuno scraping contro i termini d'uso.
Baseline W3 riprodotta prima dei test: `weekly.simulate` dal 2021 = 78.474 $, 13 trade, DD −21,1% (non modificata).

## Metro comune (H1, H2, H4)
- Rendimento futuro log close→close da t a t+h, h ∈ {1, 7, 30} giorni; il segnale usa solo dati noti alla chiusura di t
  (ritardi di pubblicazione sotto).
- Statistica: differenza in punti % fra media dei rendimenti con segnale ON e con segnale OFF; si riporta anche la base
  incondizionata e la quota di giorni ON.
- Periodi: IS 2021-01-01 → 2023-12-31; OOS 2024-01-01 → ultimo giorno disponibile. Stesse regole, nessun parametro scelto dopo.
- Placebo: spostamento circolare del segnale dentro ogni periodo (offset casuale fra 60 giorni e N−60), 2.000 estrazioni;
  p unilaterale nella direzione attesa (ON > OFF). Conserva l'autocorrelazione del segnale e dei rendimenti sovrapposti.
- **Criterio di successo** (per ipotesi, orizzonte primario): differenza > 0 sia in IS sia in OOS, con p placebo < 0,10 in
  entrambi; l'orizzonte secondario deve avere lo stesso segno. Con 4 ipotesi il criterio congiunto (~0,01 se indipendenti)
  equivale a una correzione di Bonferroni approssimativa. Tutto il resto è descrittivo.

## H1 · Offerta di stablecoin (DefiLlama, totalCirculatingUSD.peggedUSD)
Segnale ON se la variazione a 30 giorni dell'offerta totale, ritardata di 1 giorno, è > 0. Orizzonte primario 30 g,
secondario 7 g. Variante descrittiva (non decisiva): ON se la crescita a 30 g è sopra la sua mediana mobile a 365 g.
Avvertenza: serie DefiLlama ricostruita a posteriori (possibili revisioni).

## H2 · Liquidità netta Fed = WALCL − WTREGEN − RRPONTSYD×1000 (milioni $)
WALCL e WTREGEN (mercoledì, H.4.1 pubblicato giovedì sera) usati dal venerdì (ritardo 2 giorni); RRP (giornaliero) dal giorno
dopo (ritardo 1). Valori portati in avanti. Segnale ON se la variazione a 28 giorni è > 0. Primario 30 g, secondario 7 g.

## H3 · FOMC (date ufficiali 2021-01 → 2026-10, 47 decisioni; decisione alle 18:00/19:00 UTC del giorno t)
Finestre: (a) pre = chiusura t−3 → chiusura t−1 (prima della decisione); (b) reazione = chiusura t−1 → chiusura t+1;
(c) dopo = chiusura t+1 → chiusura t+8. Statistica: media della finestra sugli eventi. Placebo: 5.000 estrazioni di 47 mercoledì
lontani ≥ 8 giorni da un FOMC; p bilaterale. Successo: per una finestra, p < 0,0167 (Bonferroni su 3) sul totale e stesso
segno in IS (2021–23) e OOS (2024–26).

## H4 · Premio Coinbase (proxy della domanda USA/ETF) = Coinbase BTC-USD / (Binance BTCUSDT × Coinbase USDT-USD) − 1
USDT-USD = 1 prima del 05/2021. Segnale ON se la media a 7 giorni del premio, ritardata di 1 giorno, è > 0. Primario 7 g,
secondario 30 g. Si riporta la correlazione con il flusso perp di W3 (pf14z) per capire se è informazione nuova.

## Filtro su W3 (solo per le ipotesi che passano il criterio)
W3 invariata salvo: un nuovo LONG entra solo se il segnale è ON alla domenica del segnale (short invariati). Si confronta con
78.474 $ (DD −21,1%): finale, DD, trade, rendimento 2021–23 e 2024–26 separati; placebo = 200 segnali spostati circolarmente.
Promuovibile come proposta all'utente solo se migliora finale e MAR in entrambe le metà e batte il 90° percentile del placebo.
Con 13 trade il test ha bassa potenza: un "non peggiora" non è una prova.

## Escluse dal test (motivate prima)
Dollaro (DTWEXBGS): già bocciato come filtro di W2 (lezione 86). Funding/basis/OI estremi: già bocciati (iter. 5, lezioni 38, 86).
Momentum di serie temporale 1–4 settimane: è già la logica di W3 (lezione 70). M2: mensile con revisioni, ~70 osservazioni.
Stagionalità (giorno, mese) e halving: alta probabilità di data mining, 4 halving soltanto; solo descrittive se resta tempo.
