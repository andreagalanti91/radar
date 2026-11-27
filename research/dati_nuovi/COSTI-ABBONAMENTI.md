# Costi degli abbonamenti a fonti dati crypto

Data della ricerca: 27/11/2026. Fonti: pagine pricing e documentazione ufficiale dei fornitori, più alcune prove dirette
sulle API gratuite (nessun account creato, nessun dato personale inserito).
Uso considerato: progetto personale, trading settimanale BTC/ETH più scanner di altcoin, codice Python via API, storico dal 2018
se possibile.

## Conclusione

- **Per questo uso non serve Glassnode.** L'accesso API completo richiede il piano Professional, che costa almeno 7.008 USD l'anno,
  più un add-on API dal prezzo non pubblico.
- **Gran parte dell'on-chain essenziale è già gratis.** Il community API di CoinMetrics, senza chiave, dà ogni giorno exchange
  inflow/outflow, exchange supply (il saldo sugli exchange), MVRV, hash rate, fee ed emissione per BTC ed ETH, con storico dal
  2011 (BTC) e dal 2015 (ETH). L'ho verificato oggi con chiamate reali.
- **Spesa consigliata: 1.000–1.600 USD l'anno.**
  - **CryptoQuant Professional, annuale.** 1.188 USD l'anno a listino, 713 USD con lo sconto in corso. Aggiunge SOPR, miner
    flows, flussi per singolo exchange, risoluzione oraria e per blocco, API a 120 richieste/min e storico completo.
  - **Coinglass Hobbyist, annuale.** 420 USD l'anno a listino, 273 USD con lo sconto in corso. Aggiunge open interest, funding
    e liquidazioni aggregati su più exchange, con dati giornalieri su tutto lo storico.

## Dettaglio per fornitore

### Glassnode
- **Piani (studio.glassnode.com/pricing):**
  - **Advanced:** 49 USD al mese, oppure 34,30 USD al mese con fatturazione annuale (411,60 USD il primo anno, poi 588 USD
    l'anno). Include 270+ metriche on-chain e 40+ di mercato, risoluzione 24h, 4 anni di storico. **L'API non è inclusa.**
    Secondo la documentazione gli abbonati Advanced hanno solo l'"API Light": 14 giorni di storico, risoluzione 1d, 50
    chiamate al giorno.
  - **Professional:** da 584 USD al mese, solo con fatturazione annuale (almeno 7.008 USD l'anno). Include 570+ metriche
    on-chain e 180+ di mercato, risoluzione fino a 10 minuti e 15+ anni di storico.
- **Accesso API:** l'API completa è un add-on opzionale del Professional, con prezzo non pubblico (va chiesto alle vendite). Si
  aggiungono i "Data Credits": 1 credito per chiamata su BTC, 2 per le altcoin, in pacchetti da 50 a illimitati, con prezzo non
  pubblicato.
- **Metriche:** le metriche sono divise in tre tier, T1 Basic, T2 Essential e T3 Premium; il Professional le include tutte.
  Exchange netflow/balance, SOPR, MVRV e metriche dei miner sono nel catalogo. Il tier esatto di ciascuna non è dichiarato
  chiaramente, ma con il Professional la questione non si pone.
- **Licenza:** nessun piano "personale con API". I termini commerciali sono su misura.
- **Cosa offre di non gratuito:** metriche proprietarie (entity-adjusted, cohort, SOPR/LTH/STH), risoluzione a 10 minuti, ampia
  copertura altcoin.
- **Giudizio:** fuori scala per un progetto personale.

### CryptoQuant
- **Piani (cryptoquant.com/pricing; le FAQ riportano i prezzi di listino):**

  | Piano | Mensile | Annuale (USD/mese) | Annuale con lo sconto in corso | API | Risoluzione | Storico |
  |---|---|---|---|---|---|---|
  | Basic | 0 | 0 | – | Solo dati di mercato, 10K crediti al mese | Giornaliera | 3 anni |
  | Advanced | 39 | 29 (348/anno) | 20,30 (−30%, 243,60/anno) | Solo dati di mercato, 300K crediti | Oraria e per blocco | Completo |
  | **Professional** | 109 | **99 (1.188/anno)** | **59,40 (−40%, 712,80/anno)** | **Mercato + on-chain, 500K crediti, 120 richieste/min** | Oraria e per blocco | Completo |
  | Premium | – | 799 (solo annuale) | – | Crediti illimitati, API Analyst Consensus | Tutte | Completo |

- **Nota sui prezzi:** la tabella della pagina mostra 20,30 e 59,40 USD, cioè i prezzi annuali con lo sconto applicato. Le FAQ
  mostrano il listino. Lo sconto è un'offerta temporanea: verificare la scadenza prima di acquistare.
- **Endpoint API (catalogo ufficiale, 242 endpoint):** Exchange Flows per BTC, ETH, stablecoin, ERC20 e XRP (inflow, outflow,
  netflow, reserve, per singolo exchange, a finestra giornaliera, oraria o per blocco). Inoltre BTC Miner Flows, Market
  Indicator (SOPR, MVRV e altri), Flow Indicator, Fund Data (premium Coinbase/ETF) e Market Data.
- **Licenza:** nella pagina i CSV restano sotto la "personal-use licence" del piano con cui sono stati scaricati. L'uso
  personale è quindi coperto; l'uso commerciale non è descritto. Un utente per account.
- **Cosa offre di non gratuito:** flussi per singolo exchange e per entità, flussi dei miner, SOPR, risoluzione oraria e per
  blocco, indicatori Coinbase premium e stablecoin.
- **Limite:** copertura on-chain solo per BTC, ETH, stablecoin/ERC20, XRP e TRX. Non è uno strumento per scansionare altcoin
  generiche.

### CoinMetrics (acquisita da Talos; i domini docs reindirizzano a talos.com e kb.talostrading.com)
- **Community, gratuito:** non serve una chiave API. Limite di 10 richieste ogni 6 secondi per IP, da documentazione. Licenza
  Creative Commons (la variante esatta, probabilmente CC BY-NC 4.0, non è confermata dalle pagine lette oggi: va verificata).
  L'uso personale non commerciale è comunque nello spirito della licenza.
- **Cosa è gratis (verificato oggi via API, 31 metriche per BTC e 31 per ETH):** PriceUSD, CapMrktCurUSD, CapMVRVCur,
  FlowInExNtv/USD, FlowOutExNtv/USD, SplyExNtv/USD (saldo exchange), HashRate, FeeTotNtv, IssTotNtv/USD, AdrActCnt,
  AdrBalCnt, TxCnt, SplyCur, ROI30d/1yr, volume_reported_spot_usd_1d.
  - Storico giornaliero dal 2011 per BTC e dal 2015 per ETH. Ho verificato che le serie restituiscono dati dal 2018-01-01.
  - Le metriche di flusso hanno stato "flash", quindi sono soggette a revisione.
- **Cosa non è gratis (Pro):** CapRealUSD, RevUSD (ricavi dei miner) e tutte le metriche avanzate (SOPR, cohort, supply
  attiva). Sono escluse anche ReferenceRate con storico (gratis solo gli ultimi 7 giorni circa), i dati di mercato e
  derivati per mercato e gli asset minori.
- **Pro:** prezzo non pubblico, contratti istituzionali.

### Coinglass (API v4)
- **Piani (coinglass.com/pricing, prezzi annuali; oggi sconto Black Friday del 35%):**

  | Piano | Listino annuale | Annuale scontato | Equivalente mensile (scontato) | Endpoint | Richieste/min | Licenza |
  |---|---|---|---|---|---|---|
  | **Hobbyist** | 420 | **273** | 22,75 | 80+ | 30 | **Personale** |
  | Startup | 1.140 | 741 | 61,75 | 130+ | 80 | Personale |
  | Standard | 4.548 | 2.956 | 246 | 150+ | 300 | Commerciale |
  | Professional | 10.548 | 6.856 | 571 | 160+ | 1.200 | Commerciale |

- **Mensile:** l'opzione esiste, ma il prezzo mensile non compare nel testo della pagina.
- **Endpoint (documentazione):** liquidation history per coppia e aggregata, Aggregated OI OHLC (anche stablecoin- e
  coin-margined) e funding OI-weighted e volume-weighted sono tutti disponibili da Hobbyist. Hobbyist richiede intervalli di
  almeno 4h; Startup scende a 30 minuti.
- **Storico:** dati giornalieri su tutto lo storico per tutti i piani. Lo storico intraday è limitato per piano: da 6 giorni
  per l'intervallo di 1 minuto a 720 giorni.
  - L'inizio effettivo delle serie aggregate dipende da quando Coinglass ha iniziato a tracciare ogni exchange; non l'ho
    verificato.
  - È probabile che lo storico aggregato prima del 2019–2020 sia scarso: verificare con l'endpoint prima di contarci per il
    2018.
- **Cosa offre di non gratuito:** aggregazione multi-exchange di OI, funding e liquidazioni, liquidazioni storiche (gli
  exchange non le archiviano a lungo), long/short ratio, flussi degli ETF. Con il piano Startup anche CVD e whale alert su
  Hyperliquid.
- **Giudizio:** per il trading settimanale bastano dati a 4h o giornalieri, quindi Hobbyist è sufficiente.

### Kaiko (e Amberdata)
- **Kaiko:** non ha un listino pubblico per privati; i prezzi sono su richiesta. Listini indicativi trovati tramite ricerca su
  pagine Kaiko, da confermare: "Level 1 Aggregations" da circa 1.000 USD al mese; Market Explorer da 1.000 a 4.333 USD al mese.
  Una stima di terzi (Vendr) indica una spesa media di circa 28.500 USD l'anno.
- **Amberdata:** è stata acquisita da Kaiko nel 2026. amberdata.io/pricing reindirizza al comunicato dell'acquisizione, e i
  prodotti di Amberdata (analytics derivati/opzioni, on-chain) sono ora sulla piattaforma Kaiko. Non esiste più un listino
  Amberdata separato.
- **Giudizio:** fornitori istituzionali, fuori scala.

### Laevitas (opzioni e derivati)
- **Piani (laevitas.ch/pricing):**
  - **Free:** 1 settimana di storico.
  - **Premium:** 50 USD al mese per seat. 1 anno di storico ed export CSV; l'API non è indicata.
  - **Enterprise:** 500 USD al mese per seat. Storico via API.
  - **Custom Enterprise:** prezzo su misura.
- **Pagamento:** mensile, trimestrale, semestrale o annuale, prepagato, anche in USDC. Il prezzo annuale non è indicato.
- **Cosa offre:** superfici di volatilità, skew, term structure, flussi delle opzioni Deribit/CME, basis dei futures datati.
- **Giudizio:** costoso (6.000 USD l'anno per l'API). Il DVOL e i dati opzioni di base si ottengono gratis da Deribit.

### Santiment
- **Piani per individui (app.santiment.net/pricing e academy):**
  - **Free:** 1.000 chiamate API al mese. Le metriche ristrette hanno 1 anno di storico e 30 giorni di ritardo.
  - **Sanbase Pro:** 49 USD al mese, oppure 529 USD l'anno. 5.000 chiamate al mese, stessi limiti di storico e ritardo del
    Free sulle metriche ristrette.
  - **Sanbase Max:** 249 USD al mese, oppure 2.700 USD l'anno. 80.000 chiamate al mese, 100 al minuto. Le metriche ristrette
    hanno **solo 2 anni di storico**, ma nessun ritardo.
- **Piani business:**
  - **Business Pro:** 420 USD al mese, oppure 4.788 USD l'anno. 2 anni di storico sulle metriche ristrette.
  - **Business Max:** 999 USD al mese, oppure 11.388 USD l'anno. Accesso completo.
  - Questi prezzi compaiono su api.santiment.net, ma secondo un changelog di terzi i piani sarebbero stati rimossi a giugno
    2026: **prezzo possibilmente obsoleto**.
- **Cosa offre di non gratuito:** metriche social e di sentiment, dev activity, MVRV e age consumed per molte altcoin (utile
  per lo scanner).
- **Limite:** lo storico completo dal 2018 sulle metriche ristrette richiede Business Max. Rapporto qualità/prezzo basso per
  questo uso.

### Nansen (rilevanza bassa)
- **API (nansen.ai/api):** piano Free con 100 crediti di prova più 10 al giorno; piano Pro a 49 USD al mese con 2.000 crediti.
  In alternativa, pagamento per chiamata da 0,01 USD (x402 in USDC). Il costo in crediti per endpoint non è indicato.
- **Cosa offre:** wallet etichettati, smart money, flussi on-chain su token DeFi. Poco utile per BTC/ETH settimanale; forse
  utile per lo scanner su token EVM/Solana, ma senza un vero storico dal 2018.

### Tardis.dev (tick storici)
- **Prezzi mensili (tardis.dev):**

  | Pacchetto | Academic* | Solo | Professional | Business |
  |---|---|---|---|---|
  | Perpetuals | 350 | 700 | 1.000 | 3.000 |
  | Options | 350 | 700 | 1.000 | 3.000 |
  | Derivatives | 450 | 900 | 1.350 | 3.500 |
  | All Exchanges | 650 | 1.200 | 2.200 | 6.000 |

  *Academic: solo fatturazione trimestrale o annuale. L'ordine minimo è 300 USD. Nessuno sconto annuale indicato.
- **Accesso per piano:**
  - **Academic e Solo:** solo download CSV, senza API di replay.
  - **Professional:** aggiunge l'API raw replay e Tardis Machine.
  - **Storico:** 4 anni con fatturazione annuale, 5 con fatturazione a fattura, per tutti i piani tranne Business. **Solo
    Business ha lo storico completo**: dal 2018 servono 3.000 USD al mese o più.
- **Dati:** trades, L2 incrementale, snapshot del book, quotes, derivative ticker (funding, OI, mark), liquidazioni,
  options chain.
- **Licenza:** il piano Solo è descritto come "per quant solisti e trader indipendenti". Non c'è una clausola personale o
  commerciale esplicita.
- **Campioni gratuiti:** sono pubblicati CSV di esempio. È noto (non confermato dalla pagina letta oggi) che il primo giorno
  di ogni mese sia scaricabile gratis.
- **Giudizio:** inutile per una strategia settimanale.

## Tabella comparativa

Prezzi in USD. "Annuale" è il costo per un anno con il piano minimo che dà l'API con storico.

| Fornitore | Piano minimo con API e storico | Mensile | Annuale | Storico e frequenza | Licenza personale | Cosa dà di non gratuito | Note sul prezzo |
|---|---|---|---|---|---|---|---|
| Glassnode | Professional + add-on API | da 584 (solo annuale) + add-on | ≥ 7.008 + add-on + crediti | 15+ anni, 10 min | Su misura | SOPR/cohort/entity, 10 min, molte altcoin | Add-on e crediti non pubblici |
| **CryptoQuant** | **Professional** | 109 | **1.188 (713 con lo sconto)** | Completo, orario/blocco, 120 richieste/min | **Sì ("personal-use licence")** | Flussi per exchange, miner flows, SOPR | Sconto del 40% temporaneo |
| CoinMetrics | Community (gratis) / Pro | 0 / non pubblico | 0 / non pubblico | Giornaliero dal 2011 (BTC) | CC (non commerciale da verificare) | Pro: realized cap, SOPR, mercati | Pro su richiesta |
| **Coinglass** | **Hobbyist** | non mostrato | **420 (273 con lo sconto)** | Giornaliero su tutto lo storico, intraday ≥ 4h, 30 richieste/min | **Sì ("Personal")** | OI, funding e liquidazioni aggregati | Sconto Black Friday del 35% |
| Kaiko (+ Amberdata) | Su contratto | ~1.000+ (indicativo) | ~12.000+ (media ~28.500 secondo terzi) | Tick e storico lungo | Istituzionale | Dati di mercato normalizzati, derivati | Non pubblico |
| Laevitas | Enterprise | 500 per seat | ~6.000 | API storica | Non specificata | Analytics opzioni | Annuale non indicato |
| Santiment | Sanbase Max (Business Max per lo storico completo) | 249 (999) | 2.700 (11.388) | 2 anni sulle metriche ristrette (Max) | Individui / business | Social, dev activity, altcoin | Piani business forse rimossi |
| Nansen | API Pro | 49 | ~588 | Limitato | Sì | Wallet etichettati, smart money | Costo dei crediti non dichiarato |
| Tardis.dev | Solo CSV (4 anni) / Business (completo) | 700–1.200 / 3.000–6.000 | 8.400+ / 36.000+ | Tick; dal 2018 solo con Business | Indie (Solo) | Tick, book e liquidazioni storici | – |

## Raccomandazione: rapporto qualità/prezzo per questo uso

1. **Base gratuita, da sfruttare prima di pagare:**
   - **CoinMetrics community** (community-api.coinmetrics.io, senza chiave): exchange flows e saldo exchange, MVRV, hash rate,
     fee ed emissione. Giornaliero, dal 2011 (BTC) e 2015 (ETH).
   - **Archivi Binance** (data.binance.vision): kline spot dal 2017–2018, funding dei perpetual USDT-M (file mensili, almeno
     dal 2020; via REST dal 2019), file "metrics" giornalieri (OI, long/short) almeno da settembre 2020. Verificato oggi.
   - **Deribit API pubblica:** indice DVOL storico (risposta verificata oggi, dati 2021) e book/ticker delle opzioni in tempo
     reale.
   - **blockchain.com Charts API:** hash rate, ricavi dei miner, fee e difficoltà di BTC. Gratuita.
   - **CFTC COT:** posizionamento sui futures Bitcoin ed Ether del CME, settimanale. Gratuito via cftc.gov (dataset Socrata);
     storico CME BTC da dicembre 2017.
2. **Se serve on-chain a pagamento: CryptoQuant Professional, annuale.**
   - 1.188 USD l'anno a listino, 712,80 USD se lo sconto del 40% è ancora attivo.
   - È l'unico fornitore con API on-chain a prezzo personale, con licenza d'uso personale esplicita e storico completo.
   - Aggiunge, rispetto al gratuito: flussi per exchange, miner flows, SOPR e risoluzione oraria.
3. **Se servono derivati aggregati: Coinglass Hobbyist, annuale.**
   - 420 USD l'anno a listino, 273 USD scontato.
   - Il giornaliero e il 4h bastano per una strategia settimanale.
   - Prima di contare sul 2018, verificare con l'endpoint fin dove arrivano le serie aggregate.
4. **Totale consigliato:** circa 1.000–1.600 USD l'anno (circa 990 con gli sconti attuali, circa 1.610 a listino).
   - Glassnode, Kaiko/Amberdata, Laevitas, Santiment Business e Tardis non hanno un rapporto qualità/prezzo adeguato per un
     progetto personale settimanale.
   - Tardis ha senso solo per ricerca intraday su microstruttura; in quel caso conviene partire dai campioni gratuiti.
5. **Prima di pagare:**
   - Fare un backtest con le sole serie gratuite di CoinMetrics (flussi e saldo exchange, MVRV).
   - Abbonarsi solo se una metrica a pagamento (SOPR, miner flows, OI aggregato) migliora in modo misurabile il segnale fuori
     campione.
   - CryptoQuant Advanced offre una prova di 7 giorni, ma solo con i dati di mercato e senza l'API on-chain.

## Fonti principali
- https://studio.glassnode.com/pricing?billingCycle=yearly ; https://docs.glassnode.com/further-information/faq ; https://glassnode.com/pricing/data
- https://cryptoquant.com/pricing ; https://docs.cryptoquant.com/catalog/catalog.json
- https://community-api.coinmetrics.io/v4/ (prove dirette) ; https://docs.coinmetrics.io/cm-api-spec/rate-limits ; https://www.talos.com/our-solutions/data/community-resources
- https://www.coinglass.com/pricing ; https://docs.coinglass.com/reference/endpoint-overview
- https://www.kaiko.com/about-kaiko/pricing-and-contracts ; https://www.kaiko.com/news/kaiko-acquires-amberdata-in-landmark-digital-asset-data-consolidation ; https://www.vendr.com/buyer-guides/kaiko
- https://www.laevitas.ch/pricing
- https://app.santiment.net/pricing ; https://academy.santiment.net/products-and-plans/sanapi-plans/ ; https://api.santiment.net/
- https://www.nansen.ai/api
- https://tardis.dev/#pricing
- https://data.binance.vision ; https://www.deribit.com/api/v2/public/get_volatility_index_data (prove dirette)
