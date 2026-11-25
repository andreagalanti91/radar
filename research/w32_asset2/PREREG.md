# PREREG · W3.2 su altri asset, ciclo 2 · top 200 crypto, top 100 azioni, dal 2020 · 25/11/2026

Scritto e committato da solo PRIMA di qualsiasi rendimento. Finora eseguiti solo dati e conteggi (`crypto/DATI.md`,
`azioni/DATI.md`; i conteggi non contengono P&L). Già noti e dichiarati: lezioni 74, 87, 104, 110, 111 (W3.2 con i parametri
di BTC dal 2021 passa solo su ETH fra 27 altcoin; W3.1 senza flusso 0/13 asset, azioni comprese). Prompt completo:
`stato/PROMPT-w32-asset-ciclo2.md`.

## Universo (fissato dai file di dati, non si cambia)
- **Crypto**: top 200 CoinGecko del 25/11/2026 ∪ top 200 CoinMarketCap del 29/12/2019 (istantanea Common Crawl), esclusioni di
  `crypto/universe.csv`. **Valutabili** = ≥ 3 anni di versione completa (flusso perp) dal 2020: 79. Nucleo: le prime 20 di
  ciascuna classifica dopo le esclusioni (la top 20 del 2020 è quella CMC; le monete senza dati restano dichiarate, non sostituite).
- **Azioni**: top 100 CompaniesMarketcap di oggi ∪ top 100 di fine 2019 (`azioni/universe.csv`), 124 con dati. Nucleo: prime 10
  di ciascuna classifica. Prezzi rettificati di borsa (i perp su azioni esistono solo dal 2026).

## Motore e regole
- **Crypto, versione completa**: `radar.weekly.simulate` invariato (W3.2, R 0,25, trailing 2,5 ATRw), storia prezzi dal
  2019-09-01 (con questa scelta BTC riproduce il riferimento), test dal giorno in cui la versione completa è disponibile
  (2020-06-01 per le monete più vecchie) o dal 2020-06-01 se successivo; costi e funding come `w32_top100`.
- **Crypto solo prezzo** (monete senza perp Binance): descrittive, come `w32_multi` (0,2% per lato, short 10% annuo).
- **Azioni**: `ma_lib.s1_sim` (W3.2 senza flusso perp, funding e distribuzione), decisione al venerdì, 0,05% per lato, short 3%
  annuo (stima prudente: funding mediano osservato sui perp su azioni ≈ +1% annuo). Inizio 2020-01-01, storia dal 2019-01-02.
- **Q3 · flusso per le azioni**: una sola definizione, fissata ora: **Chaikin Money Flow a 20 sedute alla chiusura del venerdì
  (`cmf20`): ingresso long solo se > 0, short solo se < 0**, il resto delle regole invariato. Le altre serie (`cmf_w4`,
  `obv_slope20`, `obv_chg20`, `ad_slope20`) sono i "vicini" del criterio di conferma, non alternative da scegliere.
- **Q4 · BTC come cancello**: un'altcoin entra solo se alla stessa domenica W3.2 su BTC è in posizione nello stesso verso (o vi
  entra quel giorno); uscite proprie.
- **Q5 · parametri per classe**: griglia trailing {2,0; 2,5; 3,0} ATRw × rischio {0,10; 0,15; 0,25} = 9 celle, una scelta per
  classe (altcoin valutabili; azioni con `cmf20` se Q3 passa, altrimenti solo prezzo). Scelta sul solo IS: la cella con la
  **mediana di classe del CAGR/DD più alta fra quelle con mediana di classe del DD ≥ −35%**. Giudizio in OOS per asset. Se il
  motore non accetta i parametri senza modificare `radar/weekly.py`, se ne usa una copia in `research/w32_asset2/` con la sola
  sostituzione delle due costanti (verifica: con 2,5/0,25 deve dare gli stessi trade di `radar.weekly`).

## Periodi
Intero: dall'inizio del test all'ultimo dato (crypto 24/11/2026, azioni 24–25/11/2026). IS: inizio → 2022-12-31. OOS:
2023-01-01 → fine. Ogni periodo riparte da 10.000 $ e da flat.

## Criteri per asset (come `w32_top100`, sul periodo intero)
1. CAGR/DD > CAGR/DD del buy & hold dello stesso periodo · 2. DD giornaliero ≥ −35% · 3. win rate ≥ 60% · 4. rendimento positivo
in IS e in OOS · 5. ≥ 8 trade (posizione aperta inclusa, valutata alla chiusura).
**Conferma**: senza il trade migliore finale > 10.000 $; vicini (trailing 2,0 e 3,0 ATRw; per Q3 anche i 4 flussi vicini):
CAGR/DD > B&H in almeno metà. **Placebo**: metodo di `w32_multi/placebo.py` (2.000 prove, seme 7). **Holm** α = 0,05 sul numero
di asset **valutati** in quella domanda (non solo su quelli che passano 1–5: più severo di `w32_top100`, dichiarato).
"Passa davvero" = 1–5 + conferma + placebo significativo dopo Holm.

## Domande e verdetti (fissati prima)
- **Q1** (crypto valutabili, motore completo): si confronta con la lezione 111. "Si trasferisce" se passano davvero ≥ 20% delle
  altcoin valutabili; "solo casi isolati" se 1 – < 20%; "non si trasferisce" se 0 (BTC escluso dal denominatore, ETH incluso).
- **Q2** (bias di sopravvivenza): stessa regola sulle valutabili della top 200 del 2020; si riporta quante passano e il conto
  equipesato "tutte le valutabili del 2020" contro "tutte quelle di oggi".
- **Q3** (azioni): solo prezzo contro `cmf20`, stessa soglia del 20% sulle 124. Se `cmf20` non passa su almeno 1 titolo, le
  azioni sono chiuse per W3.2.
- **Q4**: come Q1 sulle altcoin valutabili con il cancello di BTC; si riporta anche la quota di operazioni sovrapposte a BTC.
- **Q5**: una classe "migliora" se in OOS la mediana di classe del CAGR/DD della cella scelta supera quella con i parametri di
  BTC e la quota di asset che passano 1–5 in OOS aumenta. Risultato a posteriori riportato come "non utilizzabile".
- **Q6 · portafoglio**: BTC + ETH (capitali uguali e separati) contro BTC + ETH + ogni asset che passa davvero in Q1–Q5 e che è
  operabile su Bitget o OKX (capitale uguale e separato). Migliora se CAGR/DD del conto unico è più alto e DD non peggiore di 3
  punti. Si riportano operazioni l'anno aggiunte e sovrapposizione settimanale con BTC.
- **Q7 · SOL e TAO** (descrittivo, non cambia nessun verdetto): SOL valutabile (giudicata nelle domande come le altre) più
  rischio 10/15/25%, operazione per operazione, IS/OOS, segnale attuale; TAO breve (versione completa dal 29/07/2024):
  operazione per operazione, solo descrittivo.
- **Q8 · motore di ricerca settimanale (prova all'indietro senza sguardo al futuro)**: ogni 1° gennaio dal 2022 si scelgono gli
  asset (crypto valutabili a quella data, con ≥ 2 anni di dati) che passano i criteri 1–3 e 5 sulla sola storia precedente
  (rischio e parametri di BTC); l'anno dopo si operano con W3.2 a capitale uguale e separato. Conto "screener" contro BTC + ETH
  e contro "tutte le valutabili". Solo crypto (Q3 decide se aggiungere le azioni in un ciclo futuro). Descrittivo ma riportato
  per anno: serve a decidere se costruire lo screener nel tool.

## Revisione e secondo ciclo
Revisione critica di un agente separato (`radar-review`, sola lettura) con trade ricalcolati a mano. Un solo secondo ciclo, per
errore del motore o ipotesi motivata dalla diagnosi, con addendum committato prima; risultati esplorativi.

## Vincoli
W3.2, `radar/weekly.py`, i segnali, gli stop e i capitali di BTC ed ETH non cambiano. Nessuna modifica al tool, nessun avviso.
Un asset che passa produce solo una proposta all'utente.
