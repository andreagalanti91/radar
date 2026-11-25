# w32_asset2 · crypto · DATI E CONTEGGI (nessun rendimento) · 25/11/2026

**Sintesi.** Universo crypto = top 200 di oggi (CoinGecko) ∪ top 200 al 29/12/2019 (CoinMarketCap via Common Crawl): 361 monete
distinte, 39 in comune. Escluse 62 (56 oggi, 9 nel 2020: stablecoin, RWA/fondi, oro, azioni tokenizzate). Restano **299**:
**79 valutabili** (≥ 3 anni di versione completa W3.2 dal 2020), **74 brevi**, **25 solo prezzo** (nessun flusso perp), **121 senza
dati** (nessuna serie su Binance né OKX; 101 sono della top 2020). Oggi: 144 incluse → 50 valutabili, 59 brevi, 12 solo
prezzo, 23 senza dati. 2020: 191 incluse → 55 valutabili, 17 brevi, 18 solo prezzo, 101 senza dati. Tutte le 50 valutabili di oggi
hanno il perp su Bitget o OKX; delle 55 valutabili del 2020 ne restano operabili 45 (10 delistate o senza perp: MKR, XEM, WAVES,
OMG, SXP, ICX, VIC, RLC, REN, LRC). Il motore `radar.weekly.simulate` gira sul formato: con questi file BTC 2021-01-01 → 2026-11-10
riproduce esattamente il riferimento di w32_top100 (controllo sì/no, nessun rendimento nuovo riportato).
**SOL** valutabile (versione completa dal 11/01/2021, 5,9 anni). **TAO** breve: perp Binance dall'11/04/2024, versione completa dal
29/07/2024 = **2,3 anni** (< 3): solo descrittivo.

## 1. Universo e fonti
- **Oggi**: CoinGecko `/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250` (API pubblica senza chiave),
  25/11/2026 08:08 UTC, prime 200 (`data/raw/cg_top.json`).
- **Al 01/01/2020**: CoinGecko pubblico non dà storico oltre 365 giorni (errore 10012 su `/history` e `/market_chart/range`;
  idem CoinPaprika). Fonte usata: l'istantanea settimanale di **CoinMarketCap `/historical/20191229/`** (ultima prima del
  01/01/2020, 200 righe con capitalizzazione e `cmc_rank`), letta **dall'archivio pubblico Common Crawl** (`data.commoncrawl.org`,
  raccolta CC-MAIN-2021-04, ricerca nell'indice CDX con richieste Range; non dal sito CMC; web.archive.org non è raggiungibile da
  questo ambiente). Controlli: istantanea CMC del 05/01/2020 (stessa raccolta, colonna `rank_20200105` in `data/universe_raw.csv`)
  e home page **CoinGecko del 24/01/2020** (CC-MAIN-2020-05, prime 99, colonna `rank_cg_20200124`). Copertura: 200/200.
  Differenze da sapere: la top 20 CMC 2019 contiene token con offerta dichiarata dubbia (MIN #20, 999 #22, HEDG #24) che CoinGecko
  non mette nelle prime 100; CoinGecko 24/01/2020 ha invece CKB, GT, STX, CEL (e DAI) fuori dalla top 200 CMC. Il rank 2020 nel file
  è quello CMC 29/12/2019; la scelta definitiva della "top 20 2020" va fissata nel PREREG.
- Codice: `cc.py` (Common Crawl), `cmc2020.py` (istantanee), `universe.py` (unione, esclusioni, catene di ticker), `bv_list.py`
  (elenco simboli e mesi dell'archivio Binance, anche delistati, dal listing S3 pubblico).
- Abbinamento 2020 → oggi per ticker con rinomine dichiarate (`MAP20`, `CHAIN` in `universe.py`): MATIC→POL, FTM→S, EOS→A (Vaulta),
  MIOTA→IOTA, LUNA→LUNC (fino al 12/05/2022, poi LUNCUSDT; LUNAUSDT dal 31/05/2022 è Terra 2.0), BTT→BTTC (prezzo /1000), NPXS→PUNDIX
  (×1000), XZC→FIRO, NANO→XNO, GNT→GLM, STRAT→STRAX, TOMO→VIC, BCHABC→BCH. MKR resta MKR (non convertita in SKY). Ticker Binance
  **riusati per altre monete** (nessun dato attribuito): LA (oggi Lagrange), NET, BZ; BEAM del 2020 ≠ BEAM di oggi (BEAMX).

## 2. Esclusioni (motivo)
Categorie CoinGecko (`/coins/markets?category=…`, file in `data/raw/`): stablecoins, yield-bearing-stablecoins, wrapped-tokens,
bridged-tokens, liquid-staking/restaking-tokens, tokenized-btc, tokenized-gold/silver/commodities, tokenized-treasuries,
tokenized-money-market-fund-mmfs, tokenized-private-credit, tokenized-credit, tokenized-stock, tokenized-exchange-traded-funds-etfs,
tokenized-products; più MGLO (fondo Midas a valore ~1, non categorizzato). SPX6900 non escluso (CoinGecko lo mette fra i bridged
per le copie su altre reti). Le RWA "di protocollo" (LINK, XLM, QNT, ONDO, ALGO, INJ, XDC…) restano: sono token volatili.
- **Oggi (56)**: 34 stablecoin, 16 RWA/fondi (FIGR_HELOC, USDY, USYC, EURSAFO, BUIDL, USTB, JAAA, EUTBL, OUSG, SAFO, MGLO, USTBL,
  PC0000031/33/97, …), 4 oro/argento (XAUT, PAXG, KAU, KAG), 2 azioni tokenizzate (NVDAB, NVDAX). Nessun wrapped/staked nella top 200.
- **2020 (9)**: USDT, USDC, PAX, TUSD, SAI, EURS, USDK (stablecoin), KBC (oro), CIX100 (indice tokenizzato).
- Token **senza dati non sostituiti** (oggi, 23): WBT, RAIN, HTX, MNT, BGB, KCS, PEARL, GT, BDX, XDC, HASH, DRV, APEPE, OZO, OHM, BP,
  BTSE, SHFL, KOGE, GOMINING, GEOD, MX, BORG (token di exchange e simili: non su Binance né OKX in USDT).

## 3. Bias di sopravvivenza (top 200 al 29/12/2019, 191 incluse) · `data/survivorship.csv`
- Ancora nella top 200 di oggi: **37**. Quotate su Binance oggi: 74 (33 in top 250 CoinGecko, 41 fuori). **Delistate da Binance: 13**
  (dati ancora nell'archivio fino al delisting): REP (fino 12/2022), BTG (10/2022), SXP (05/2026), MCO (10/2020), KMD (07/2025),
  HC (11/2020), BTS (05/2024), ARDR (07/2026), BEAM (01/2023), ELF (04/2025), FIRO/XZC (04/2025), AION (02/2023), WAN (04/2026).
  Inoltre perp delistati con spot ancora quotato o fermo: MKR, XEM, WAVES, OMG, ICX, VIC, REN, LRC, FTT, BTTC, DGB, SC, STRAX, SNT, FUN,
  NULS, TON (le serie finiscono all'ultimo giorno scambiato).
- **Mai su Binance in USDT: 104** (di cui 101 senza alcun dato anche su OKX): HT, MIN, 999, HEDG, INO, INB, THR, THX, PZM, CNX,
  CENNZ, SEELE, ZB, XIN, ABBC, MOF, CCA, FST, BTM, BCD, FAB, GAP, EON, VSYS, BXK, NOAH, EKT, BCN, MONA, NRG, BRZE, MB, DX, QC, SLV, BOTX,
  FXC, AE, XET, JUL, LA, ETN, DGD, BCZERO, CRPT, SOLVE, NEX, BF, BTMX, CSC, MAID, BNK, CCC, ECOREAL, DGTX, GRIN, ENG, NET, ETP, VLX, ADK,
  BTC2, GNY, GXC, JWL, DTR, HPT, ELA, PLC, RCN, BRD, BZ, AGVC, HYN, WICC, VEST, VERI, DCN, QBIT, R, NAS, PPT, RDD, TNT, LAMB, DPT, DIVI,
  LOKI, BHD, ILC, XMX, XAC, NEW, IGNIS, YOU, DRG, EDC, TRUE, più KCS, BDX, MX (anche oggi in top 200, senza dati) e LEO, CRO, OKB
  (solo prezzo da OKX). Sono in gran parte token morti o illiquidi: chi avesse scelto la top 200
  del 2020 non avrebbe potuto operarli con W3.2 (niente perp). Il bias quindi pesa soprattutto sul **buy & hold** e sulla scelta
  dell'universo, meno sulla parte operabile: delle 191, 72 hanno il flusso perp (55 valutabili + 17 brevi).
- LUNA/LUNC (rank 59 nel 2020) è dentro con il crollo del 05/2022 (buco di 119 giorni fra LUNAUSDT e LUNCUSDT/1000LUNCUSDT); FTT
  (rank 37) con il crollo del 11/2022 (perp fino al 2022, breve).

## 4. Dati · formato e copertura
Formato identico a `research/w32_top100/data`: `data/<T>_spot.csv.gz`, `<T>_perp.csv.gz` (date,open,high,low,close,volume,tbv),
`<T>_funding.csv.gz` (date,funding = somma giornaliera). 479 file per 181 monete (15 MB) + grezzi riscaricabili in `data/raw/` (22 MB).
- **Fonti** (per moneta in `data/sources.csv`): archivio `data.binance.vision` (spot 1d con taker buy dal 2018-06; perp USDT-M 1d con
  taker buy: l'archivio parte dal **2020-01** anche per BTC; funding mensile fino al 10/2026; giorni di novembre dai file giornalieri
  fino al **24/11/2026**). I 169 file di w32_top100 fanno da seme (stessi valori, verificato) e sono stati estesi.
  **OKX** (API pubblica): funding 01–24/11/2026 per le monete con perp OKX (mese non ancora nell'archivio Binance; senza OKX il funding
  si ferma al 31/10) e prezzi (senza taker buy) per 9 monete assenti da Binance (LEO, CRO, OKB, PI, FLR, NFT, ZBCN, DGAI, CARDS).
  **Bitget**: solo TAO spot prima di Binance. Binance fapi/api non usate (bloccate dal runner USA).
- **Storia prezzi e motore**: le EMA/ATR/MACD settimanali di `weekly_bars` dipendono dal primo giorno della serie (ewm). Con lo spot dal
  2018-06 BTC non riproduce più il riferimento; con lo spot dal **2019-09-01** sì. I conteggi usano quindi la storia dal 2019-09
  (`counts.py`, `SINCE`), come w32_top100; i file contengono lo spot dal 2018-06. **Da fissare nel PREREG.** Conseguenza: la versione
  completa delle monete vecchie parte il **01/06/2020** (SMA 40 settimane), non prima; con la storia dal 2018 partirebbe il 20/04/2020
  per BTC/ETH (colonna `completa_da_storia2018`), limitata dal perp (archivio dal 2020-01 + 90 giorni di z-score).
- **Versione completa da** = lunedì dopo la prima domenica ≥ 2020-01-01 con SMA 40 settimane e flusso perp (pf14z, z 180 g con
  minimo 90) calcolabili. **Fine** = ultimo giorno del perp scambiato (dopo il delisting il flusso non esiste).
- **Controlli di qualità** (`data/qc.csv`, `build.py`): 0 OHLC incoerenti; 0 tbv > volume; giorni a **volume zero tolti** (14.464 su 27
  serie: l'archivio continua a pubblicare prezzi congelati dopo il delisting, es. TON da 06/2026, RAYUSDT da 11/2022, ICP perp
  06–08/2022); salti ×3 in un giorno controllati a mano: DOGE 01/2021, LUNC 05/2022, FTT 11/2022 (veri), RAY e VIC (ripresa del perp
  dopo un buco), STRAX 03/2024 (ridenominazione non corretta: STRAX è breve). Correzioni: SUN solo dal 18/06/2021 (ridenominazione),
  PUMP perp dal 10/07/2025 (prima altro contratto), LIT dal 23/12/2025 (prima Litentry), RAY perp = RAYUSDT fino al 11/2022 poi
  RAYSOLUSDT. Serie ferme (ultimo dato > 3 giorni prima del 24/11): 19 perp e 26 spot, tutte delisting veri. Spot/perp: solo FIL con
  6 giorni di differenza > 5% (inizio quotazione 10/2020).

## 5. Operabilità per l'utente (liste pubbliche del 25/11/2026, `data/ops.csv`, `ops.py`)
Bitget `/api/v2/mix/market/contracts?productType=USDT-FUTURES` (894 contratti) e `/api/v2/spot/public/symbols`; OKX
`/api/v5/public/instruments?instType=SWAP` (554) e `SPOT`. Delle 299 incluse: perp Bitget 139, perp OKX 112, almeno uno 140.
Valutabili operabili: oggi 50/50, 2020 45/55. Le date di apertura delle liste (Bitget `openTime`, spesso vuota; OKX `listTime`)
possono essere riaperture, non la prima quotazione.

## 6. SOL e TAO
- **SOL**: spot dal 10/04/2020 (SOLBUSD fino all'avvio di SOLUSDT l'11/08/2020; BUSD ≈ USD), perp Binance dal 14/09/2020, funding
  dal 13/09/2020; versione completa dall'**11/01/2021** (5,9 anni, valutabile). OKX perp dal 22/01/2021, Bitget spot dal 22/06/2021,
  perp Bitget attivo (data non dichiarata). Ingressi W3.2 dal 2021: 15 long / 8 short (2021 4/0, 2022 1/2, 2023 2/3, 2024 2/0,
  2025 5/1, 2026 1/2); in posizione 145 settimane, 70% nello stesso verso di BTC, 14% opposto, 17% con BTC flat. Posizione aperta
  oggi: short.
- **TAO**: spot Bitget dal 30/03/2023 (prima fonte disponibile, senza taker buy), spot e perp Binance dall'**11/04/2024**, perp
  Bitget dall'11/04/2024, perp OKX dal 20/09/2024, spot OKX dal 30/06/2026 (data di lista). Versione completa dal **29/07/2024 =
  2,3 anni (< 3: breve, solo descrittivo)**; prezzo dal 2023 utile solo per medie e buy & hold. Ingressi: 5 long / 9 short (2024 1/0,
  2025 2/4, 2026 2/5); 63 settimane in posizione, 56% stesso verso di BTC, 22% opposto, 22% BTC flat. Oggi flat.

## 7. Conteggi (nessun rendimento) · `data/counts.csv`, `data/counts_anno.csv`
Ingressi = operazioni aperte da `simulate` (parametri di BTC, rischio 25%, stop/trailing 2,5 ATR) dalla versione completa;
"sett_cond" in `counts_anno.csv` = settimane con condizione d'ingresso vera (indipendente dalla posizione). Sovrapposizione =
settimane in posizione della moneta con BTC nello stesso verso / verso opposto / BTC flat. Altcoin valutabili: mediana 4,1 ingressi
l'anno (BTC 2,6), stesso verso di BTC 44%, opposto 27%, BTC flat 31%.

Somma degli ingressi long/short per anno, valutabili: 2020 63/15 · 2021 217/16 · 2022 34/163 · 2023 146/139 · 2024 227/123 ·
2025 118/204 · 2026 71/171. Brevi: 2024 50/39 · 2025 51/126 · 2026 88/123.

### Top 20 di oggi (rank CoinGecko; sovr_BTC = stesso/opposto/flat %)
| rank | moneta | classe | dati | perp_da | completa_da | anni_c | ingr_L_S | sovr_BTC | bitget | okx | cat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | BTC | valutabile | 2018-06-01→2026-11-24 | 2020-01-01 | 2020-06-01 | 6.48 | 12/5 | 100/0/0 | sì | sì |  |
| 2 | ETH | valutabile | 2018-06-01→2026-11-24 | 2020-01-01 | 2020-06-01 | 6.48 | 11/5 | 74/3/23 | sì | sì |  |
| 3 | USDT | esclusa |  |  |  |  |  |  | no | no | stablecoin |
| 4 | BNB | valutabile | 2018-06-01→2026-11-24 | 2020-02-10 | 2020-06-01 | 6.48 | 20/9 | 58/9/33 | sì | sì |  |
| 5 | USDC | esclusa |  |  |  |  |  |  | no | no | stablecoin |
| 6 | XRP | valutabile | 2018-06-01→2026-11-24 | 2020-01-06 | 2020-06-01 | 6.48 | 22/9 | 62/9/28 | sì | sì |  |
| 7 | SOL | valutabile | 2020-04-10→2026-11-24 | 2020-09-14 | 2021-01-11 | 5.87 | 15/8 | 70/14/17 | sì | sì |  |
| 8 | TRX | valutabile | 2018-06-11→2026-11-24 | 2020-01-15 | 2020-06-01 | 6.48 | 18/4 | 59/6/35 | sì | sì |  |
| 9 | FIGR_HELOC | esclusa |  |  |  |  |  |  | no | no | rwa/fondo |
| 10 | HYPE | breve | 2025-05-30→2026-11-24 | 2025-05-30 | 2026-03-02 | 0.73 | 3/0 | 38/48/14 | sì | sì |  |
| 11 | ZEC | valutabile | 2019-03-21→2026-11-24 | 2020-02-05 | 2020-06-01 | 6.48 | 24/6 | 36/30/34 | sì | sì |  |
| 12 | XMR | valutabile | 2019-03-15→2026-11-23 | 2020-02-03 | 2020-06-01 | 6.48 | 24/9 | 52/9/38 | sì | no |  |
| 13 | DOGE | valutabile | 2019-07-05→2026-11-24 | 2020-07-10 | 2020-10-26 | 6.08 | 26/10 | 55/9/36 | sì | sì |  |
| 14 | LEO | solo prezzo | 2020-01-01→2026-11-24 |  |  |  |  |  | no | no |  |
| 15 | LINK | valutabile | 2019-01-16→2026-11-24 | 2020-01-17 | 2020-06-01 | 6.48 | 15/11 | 61/12/26 | sì | sì |  |
| 16 | WBT | senza dati |  |  |  |  |  |  | no | no |  |
| 17 | USDS | esclusa |  |  |  |  |  |  | no | no | stablecoin |
| 18 | ADA | valutabile | 2018-06-01→2026-11-24 | 2020-01-31 | 2020-06-01 | 6.48 | 14/10 | 60/14/26 | sì | sì |  |
| 19 | USDE | esclusa |  |  |  |  |  |  | no | no | stablecoin |
| 20 | DAI | esclusa |  |  |  |  |  |  | no | no | stablecoin |


### Top 20 al 29/12/2019 (rank CMC)
| rank | moneta | classe | dati | perp_da | completa_da | anni_c | ingr_L_S | sovr_BTC | bitget | okx | cat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | BTC | valutabile | 2018-06-01→2026-11-24 | 2020-01-01 | 2020-06-01 | 6.48 | 12/5 | 100/0/0 | sì | sì |  |
| 2 | ETH | valutabile | 2018-06-01→2026-11-24 | 2020-01-01 | 2020-06-01 | 6.48 | 11/5 | 74/3/23 | sì | sì |  |
| 3 | XRP | valutabile | 2018-06-01→2026-11-24 | 2020-01-06 | 2020-06-01 | 6.48 | 22/9 | 62/9/28 | sì | sì |  |
| 4 | USDT | esclusa |  |  |  |  |  |  | no | no | stablecoin |
| 5 | BCH | valutabile | 2018-11-16→2026-11-24 | 2020-01-01 | 2020-06-01 | 6.48 | 17/12 | 48/14/38 | sì | sì |  |
| 6 | LTC | valutabile | 2018-06-01→2026-11-24 | 2020-01-09 | 2020-06-01 | 6.48 | 17/12 | 56/12/32 | sì | sì |  |
| 7 | A (EOS) | valutabile | 2018-06-01→2026-11-24 | 2020-01-08 | 2020-06-01 | 6.48 | 12/12 | 44/22/34 | sì | sì |  |
| 8 | BNB | valutabile | 2018-06-01→2026-11-24 | 2020-02-10 | 2020-06-01 | 6.48 | 20/9 | 58/9/33 | sì | sì |  |
| 9 | BSV | breve | 2023-10-20→2026-11-24 | 2023-10-20 | 2024-07-22 | 2.34 | 1/12 | 37/37/25 | sì | no |  |
| 10 | XLM | valutabile | 2018-06-01→2026-11-24 | 2020-01-20 | 2020-06-01 | 6.48 | 18/12 | 50/17/33 | sì | sì |  |
| 11 | TRX | valutabile | 2018-06-11→2026-11-24 | 2020-01-15 | 2020-06-01 | 6.48 | 18/4 | 59/6/35 | sì | sì |  |
| 12 | XTZ | valutabile | 2019-09-24→2026-11-23 | 2020-02-06 | 2020-06-29 | 6.4 | 9/15 | 46/24/30 | sì | sì |  |
| 13 | ADA | valutabile | 2018-06-01→2026-11-24 | 2020-01-31 | 2020-06-01 | 6.48 | 14/10 | 60/14/26 | sì | sì |  |
| 14 | LEO | solo prezzo | 2020-01-01→2026-11-24 |  |  |  |  |  | no | no |  |
| 15 | ATOM | valutabile | 2019-04-29→2026-11-24 | 2020-02-07 | 2020-06-01 | 6.48 | 11/18 | 32/34/35 | sì | sì |  |
| 16 | XMR | valutabile | 2019-03-15→2026-11-23 | 2020-02-03 | 2020-06-01 | 6.48 | 24/9 | 52/9/38 | sì | no |  |
| 17 | HT | senza dati |  |  |  |  |  |  | no | no |  |
| 18 | LINK | valutabile | 2019-01-16→2026-11-24 | 2020-01-17 | 2020-06-01 | 6.48 | 15/11 | 61/12/26 | sì | sì |  |
| 19 | NEO | valutabile | 2018-06-01→2026-11-24 | 2020-02-17 | 2020-06-01 | 6.48 | 15/12 | 42/22/36 | sì | sì |  |
| 20 | MIN | senza dati |  |  |  |  |  |  | no | no |  |


### Valutabili (79), per data d'inizio
| Moneta | Rank oggi | Rank 2020 | Completa da | Anni | Dati fino al | Ingressi L/S | Sovr. BTC stesso/opposto/flat % | Bitget | OKX |
|---|---|---|---|---|---|---|---|---|---|
| BTC | 1 | 1 | 2020-06-01 | 6.5 | 2026-11-24 | 12/5 | 100/0/0 | sì | sì |
| ETH | 2 | 2 | 2020-06-01 | 6.5 | 2026-11-24 | 11/5 | 74/3/23 | sì | sì |
| BNB | 4 | 8 | 2020-06-01 | 6.5 | 2026-11-24 | 20/9 | 58/9/33 | sì | sì |
| XRP | 6 | 3 | 2020-06-01 | 6.5 | 2026-11-24 | 22/9 | 62/9/28 | sì | sì |
| TRX | 8 | 11 | 2020-06-01 | 6.5 | 2026-11-24 | 18/4 | 59/6/35 | sì | sì |
| ZEC | 11 | 35 | 2020-06-01 | 6.5 | 2026-11-24 | 24/6 | 36/30/34 | sì | sì |
| XMR | 12 | 16 | 2020-06-01 | 6.5 | 2026-11-23 | 24/9 | 52/9/38 | sì | no |
| LINK | 15 | 18 | 2020-06-01 | 6.5 | 2026-11-24 | 15/11 | 61/12/26 | sì | sì |
| ADA | 18 | 13 | 2020-06-01 | 6.5 | 2026-11-24 | 14/10 | 60/14/26 | sì | sì |
| XLM | 21 | 10 | 2020-06-01 | 6.5 | 2026-11-24 | 18/12 | 50/17/33 | sì | sì |
| BCH | 22 | 5 | 2020-06-01 | 6.5 | 2026-11-24 | 17/12 | 48/14/38 | sì | sì |
| LTC | 24 | 6 | 2020-06-01 | 6.5 | 2026-11-24 | 17/12 | 56/12/32 | sì | sì |
| ETC | 70 | 21 | 2020-06-01 | 6.5 | 2026-11-24 | 13/15 | 37/29/34 | sì | sì |
| ATOM | 85 | 15 | 2020-06-01 | 6.5 | 2026-11-24 | 11/18 | 32/34/35 | sì | sì |
| DASH | 103 | 28 | 2020-06-01 | 6.5 | 2026-11-24 | 13/12 | 27/30/43 | sì | sì |
| VET | 106 | 30 | 2020-06-01 | 6.5 | 2026-11-23 | 15/8 | 51/19/30 | sì | no |
| IOTA | 182 | 25 | 2020-06-01 | 6.5 | 2026-11-24 | 16/9 | 48/22/29 | sì | sì |
| A |  | 7 | 2020-06-01 | 6.5 | 2026-11-24 | 12/12 | 44/22/34 | sì | sì |
| NEO |  | 19 | 2020-06-01 | 6.5 | 2026-11-24 | 15/12 | 42/22/36 | sì | sì |
| ONT |  | 29 | 2020-06-01 | 6.5 | 2026-11-24 | 13/21 | 31/27/42 | sì | sì |
| BAT |  | 32 | 2020-06-01 | 6.5 | 2026-11-24 | 15/12 | 33/32/35 | sì | sì |
| QTUM |  | 41 | 2020-06-08 | 6.5 | 2026-11-24 | 20/18 | 47/19/34 | sì | sì |
| IOST |  | 83 | 2020-06-08 | 6.5 | 2026-11-24 | 13/16 | 34/33/34 | sì | sì |
| XTZ | 138 | 12 | 2020-06-29 | 6.4 | 2026-11-23 | 9/15 | 46/24/30 | sì | sì |
| THETA | 196 | 65 | 2020-09-14 | 6.2 | 2026-11-24 | 7/8 | 41/24/34 | sì | sì |
| ALGO | 81 | 47 | 2020-10-05 | 6.1 | 2026-11-24 | 9/10 | 47/24/29 | sì | sì |
| ZIL |  | 99 | 2020-10-05 | 6.1 | 2026-11-24 | 10/12 | 34/26/40 | sì | sì |
| ZRX |  | 45 | 2020-10-12 | 6.1 | 2026-11-24 | 10/17 | 50/28/22 | sì | sì |
| OMG |  | 58 | 2020-10-19 | 4.3 | 2025-01-31 | 9/4 | 34/27/39 | no | no |
| DOGE | 13 | 34 | 2020-10-26 | 6.1 | 2026-11-24 | 26/10 | 55/9/36 | sì | sì |
| RLC |  | 135 | 2020-11-16 | 6.0 | 2026-11-24 | 13/18 | 40/23/37 | no | no |
| WAVES |  | 55 | 2020-11-30 | 3.5 | 2024-06-11 | 5/4 | 28/33/39 | no | no |
| ICX |  | 84 | 2021-01-04 | 5.6 | 2026-08-26 | 9/17 | 45/21/34 | no | no |
| SOL | 7 |  | 2021-01-11 | 5.9 | 2026-11-24 | 15/8 | 70/14/17 | sì | sì |
| S |  | 170 | 2021-01-11 | 5.9 | 2026-11-24 | 15/4 | 60/22/18 | sì | sì |
| ENJ |  | 74 | 2021-01-18 | 5.8 | 2026-11-24 | 10/14 | 26/39/34 | sì | sì |
| VIC |  | 119 | 2021-01-25 | 5.5 | 2026-08-07 | 8/6 | 63/6/31 | no | no |
| REN |  | 153 | 2021-02-01 | 3.8 | 2024-12-03 | 4/11 | 27/29/44 | no | no |
| POL | 75 | 112 | 2021-02-08 | 5.8 | 2026-11-24 | 12/17 | 32/32/37 | sì | sì |
| KNC |  | 127 | 2021-03-15 | 5.7 | 2026-11-24 | 11/13 | 36/28/36 | sì | no |
| LRC |  | 174 | 2021-03-15 | 5.0 | 2026-03-24 | 14/10 | 38/33/29 | no | no |
| COMP | 163 |  | 2021-03-29 | 5.7 | 2026-11-24 | 9/12 | 41/23/36 | sì | sì |
| SNX |  | 38 | 2021-04-12 | 5.6 | 2026-11-24 | 7/14 | 37/37/27 | sì | sì |
| ZEN |  | 82 | 2021-04-12 | 5.6 | 2026-11-23 | 14/11 | 38/29/33 | sì | sì |
| MKR |  | 26 | 2021-04-26 | 4.4 | 2025-09-08 | 8/7 | 46/27/27 | no | no |
| SXP |  | 73 | 2021-04-26 | 4.6 | 2025-12-05 | 8/13 | 33/29/38 | no | no |
| CHZ |  | 149 | 2021-05-10 | 5.5 | 2026-11-24 | 8/15 | 18/53/29 | sì | sì |
| CRV | 126 |  | 2021-05-17 | 5.5 | 2026-11-24 | 9/11 | 53/15/32 | sì | sì |
| DOT | 63 |  | 2021-05-24 | 5.5 | 2026-11-24 | 5/18 | 31/39/30 | sì | sì |
| LUNC | 133 | 59 | 2021-05-24 | 5.5 | 2026-11-24 | 7/2 | 8/46/46 | sì | no |
| RUNE | 167 |  | 2021-06-07 | 5.5 | 2026-11-24 | 9/8 | 47/33/20 | sì | no |
| RVN |  | 46 | 2021-06-14 | 5.5 | 2026-11-24 | 12/11 | 38/32/30 | sì | no |
| UNI | 30 |  | 2021-06-21 | 5.4 | 2026-11-24 | 13/9 | 55/14/32 | sì | sì |
| AVAX | 26 |  | 2021-06-28 | 5.4 | 2026-11-24 | 11/14 | 45/28/27 | sì | sì |
| MANA |  | 117 | 2021-06-28 | 5.4 | 2026-11-24 | 11/9 | 43/27/30 | sì | sì |
| HBAR | 36 | 175 | 2021-07-05 | 5.4 | 2026-11-24 | 12/12 | 61/16/24 | sì | sì |
| NEAR | 23 |  | 2021-07-19 | 5.3 | 2026-11-24 | 15/9 | 43/36/21 | sì | sì |
| AAVE | 52 |  | 2021-07-19 | 5.3 | 2026-11-24 | 11/8 | 65/7/27 | sì | sì |
| FIL | 101 |  | 2021-07-19 | 5.3 | 2026-11-24 | 5/13 | 40/32/28 | sì | sì |
| HOT |  | 51 | 2021-07-19 | 5.3 | 2026-11-24 | 9/14 | 43/29/28 | sì | no |
| XEM |  | 31 | 2021-08-30 | 3.3 | 2024-12-09 | 8/11 | 41/28/31 | no | no |
| GRT | 162 |  | 2021-09-20 | 5.2 | 2026-11-24 | 5/7 | 47/23/30 | sì | sì |
| IOTX |  | 182 | 2021-11-29 | 5.0 | 2026-11-24 | 6/11 | 44/30/27 | sì | no |
| SHIB | 41 |  | 2022-02-14 | 4.8 | 2026-11-24 | 11/11 | 46/26/29 | sì | sì |
| ICP | 64 |  | 2022-02-14 | 4.8 | 2026-11-24 | 8/12 | 38/30/32 | sì | sì |
| AR | 176 |  | 2022-02-14 | 4.8 | 2026-11-24 | 6/7 | 40/32/28 | sì | sì |
| RAY | 116 |  | 2022-05-16 | 4.5 | 2026-11-24 | 3/5 | 49/28/22 | sì | sì |
| ENS | 183 |  | 2022-08-15 | 4.3 | 2026-11-24 | 7/10 | 42/24/34 | sì | sì |
| JASMY | 173 |  | 2022-08-29 | 4.2 | 2026-11-24 | 10/11 | 36/31/32 | sì | no |
| INJ | 90 |  | 2022-12-05 | 4.0 | 2026-11-24 | 6/12 | 60/19/22 | sì | sì |
| QNT | 40 | 102 | 2023-02-06 | 3.8 | 2026-11-24 | 10/10 | 41/19/40 | sì | sì |
| LDO | 152 |  | 2023-02-13 | 3.8 | 2026-11-24 | 10/7 | 46/23/31 | sì | sì |
| OP | 171 |  | 2023-03-06 | 3.7 | 2026-11-24 | 3/6 | 38/38/23 | sì | sì |
| FET | 135 | 148 | 2023-05-08 | 3.5 | 2026-11-24 | 5/11 | 45/32/23 | sì | sì |
| RENDER | 84 |  | 2023-05-22 | 3.5 | 2026-11-24 | 5/9 | 45/31/23 | sì | sì |
| CFX | 166 |  | 2023-06-05 | 3.5 | 2026-11-24 | 4/7 | 45/30/25 | sì | sì |
| STX | 97 |  | 2023-06-12 | 3.5 | 2026-11-24 | 6/5 | 48/28/24 | sì | sì |
| APT | 117 |  | 2023-07-24 | 3.3 | 2026-11-24 | 3/9 | 40/44/17 | sì | sì |
| XVG |  | 86 | 2023-10-23 | 3.1 | 2026-11-24 | 13/5 | 42/22/36 | sì | no |

### Brevi (74): moneta (completa da, anni)
BTS (2021-05-17, 1.2); BTTC (2021-07-26, 0.7); SC (2021-07-26, 0.9); DGB (2021-08-09, 2.6); FTT (2022-08-01, 0.3); BNT (2023-11-27, 3.0); ARB (2023-12-25, 2.9); STRAX (2024-01-29, 0.1); RIF (2024-02-05, 2.8); PEPE (2024-02-05, 2.8); SUI (2024-02-05, 2.8); FLOKI (2024-02-05, 2.8); SNT (2024-02-19, 0.2); TWT (2024-02-19, 2.8); CAKE (2024-02-19, 2.8); STEEM (2024-02-26, 2.7); PENDLE (2024-04-08, 2.6); WLD (2024-04-29, 2.6); LSK (2024-05-13, 2.5); SEI (2024-05-20, 2.5); GLM (2024-06-10, 2.5); ARK (2024-06-24, 2.4); BSV (2024-07-22, 2.3); TAO (2024-07-29, 2.3); TIA (2024-08-05, 2.3); KAS (2024-08-19, 2.3); BEAMX (2024-08-19, 2.3); BONK (2024-08-26, 2.2); PYTH (2024-08-26, 2.2); JTO (2024-09-09, 2.2); ONDO (2024-10-21, 2.1); JUP (2024-11-04, 2.0); STRK (2024-11-25, 2.0); TON (2024-12-02, 1.6); NULS (2024-12-09, 0.3); SUN (2024-12-09, 2.0); ETHFI (2024-12-23, 1.9); ENA (2025-01-06, 1.9); ZRO (2025-03-24, 1.7); FUN (2025-07-14, 0.8); KAIA (2025-08-04, 1.3); GRASS (2025-08-11, 1.3); JST (2025-08-11, 1.3); PUNDIX (2025-08-18, 1.3); AKT (2025-08-25, 1.2); MORPHO (2025-09-01, 1.2); AERO (2025-09-08, 1.2); SPX (2025-09-15, 1.2); VIRTUAL (2025-09-15, 1.2); PENGU (2025-09-22, 1.2); KMNO (2025-09-22, 1.2); TRUMP (2025-10-20, 1.1); VVV (2025-11-03, 1.1); HYPE (2026-03-02, 0.7); M (2026-04-13, 0.6); PUMP (2026-04-13, 0.6); WLFI (2026-05-25, 0.5); XPL (2026-05-25, 0.5); SKY (2026-06-15, 0.4); UB (2026-06-15, 0.4); ASTER (2026-06-22, 0.4); FF (2026-07-06, 0.4); MON (2026-07-13, 0.4); 币安人生 (2026-07-27, 0.3); KITE (2026-08-03, 0.3); CC (2026-08-03, 0.3); STABLE (2026-08-10, 0.3); PIEVERSE (2026-08-17, 0.3); SENT (2026-08-17, 0.3); NIGHT (2026-09-14, 0.2); LIT (2026-09-28, 0.2); ZAMA (2026-10-12, 0.1); BTW (nan, 0.0); CAP (nan, 0.0)

### Solo prezzo (25)
Oggi: LEO, CRO, OKB, NEXO, PI, FLR, GNO, DCR, NFT, ZBCN, DGAI, CARDS (nessun perp Binance con taker buy; i prezzi OKX non hanno taker buy). Solo 2020: REP, BTG, XNO, MCO, KMD, HC, ARDR, BEAM, ELF, FIRO, AION, WIN, WAN.

## 8. Limiti e cosa manca
- La versione completa non può partire prima del **01/06/2020** con la convenzione dal 2019-09 (archivio perp dal 2020-01); il 2020
  aggiunge al massimo 7 mesi rispetto al 2021. Un perp più lungo (fapi dal 09/2019) non è nell'archivio.
- Classifica 2020 da **CoinMarketCap** (non CoinGecko): CoinGecko storico è a pagamento; il controllo CoinGecko copre solo le prime 99
  e 3 settimane dopo. Il rank può differire di qualche posizione (es. MIN, 999, HEDG solo CMC).
- OKX e Bitget non danno taker buy storico (OKX `taker-volume` ~100 giorni): dove manca Binance non esiste versione completa.
  Funding OKX via API solo ~3 mesi: usato solo per novembre 2026.
- Abbinamenti per ticker: verificati con i salti di prezzo e le date di quotazione, ma un riuso di ticker senza salto non si vede.
  STRAX non è corretto per la ridenominazione del 03/2024 (irrilevante: breve). MKR non è unita a SKY.
- Rendimenti, criteri e placebo non calcolati (compito di chi scrive il PREREG). I file `data/` non sono in `.gitignore`
  (w32_top100 sì): 15 MB di dati + 22 MB di grezzi; decidere se committare solo `data/*.csv.gz` e i csv.

## 9. File e come rifare
`universe.csv` (una riga per moneta: simbolo, ticker, rank oggi, rank 2020, categoria, dati da/a, completa da, valutabile, classe,
perp Bitget, perp OKX). In `data/`: `universe_raw.csv`, `counts.csv` (tutte le colonne, operabilità inclusa), `counts_anno.csv`,
`survivorship.csv`, `ops.csv`, `sources.csv`, `qc.csv`, file per moneta. Ordine: `python3 cmc2020.py` → `python3 bv_list.py` →
`python3 universe.py` → `nohup python3 fetch.py > data/raw/fetch.log &` (riprendibile, 4 thread, pause, 0 errori su 494 serie) →
`python3 okx.py candles|funding|tao` → `python3 ops.py` → `python3 build.py` → `python3 survivors.py` → `python3 counts.py` →
`python3 summary.py`. User-Agent `radar-research-script/1.0 (python-requests; academic backtest)`. Solo numpy/pandas/requests.
