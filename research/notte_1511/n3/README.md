# N3 · Letteratura su BTC → ipotesi testabili → test preregistrati (notte 15–16/11/2026)

**Conclusione.** Nessuna delle 4 ipotesi testate (stablecoin, liquidità netta Fed, FOMC, premio Coinbase) passa il criterio
preregistrato, e nessuna migliora W3 come filtro (78.474 $ → 42–69k). Il candidato più vicino è il **premio Coinbase**: segno
positivo a 7 e 30 giorni sia nel 2021–23 sia nel 2024–26 (+2,4 e +1,2 punti a 7 g; p 0,03 e 0,10) e correlazione ~0 con il
flusso perp di W3 (+0,02), quindi informazione nuova. Però manca la soglia OOS per poco, è instabile su vicini e anni (2022 e 2024
negativi) e come filtro di W3 toglie rendimento. Proposta: tenerlo **solo come contesto in dashboard e seguirlo su carta** (nuova
preregistrazione fra 6–12 mesi), non come regola. W3 resta invariata. La letteratura conferma il quadro delle lezioni 70/86:
l'unico effetto robusto e replicato su BTC è il momentum/trend (già in W3); macro, ETF, stablecoin e funding sono soprattutto
contemporanei (spiegano il movimento dello stesso periodo) e non lo anticipano.

File: `PREREG.md` (scritto prima dei risultati), `test.py` (test decisivi), `controlli_h4.py` e `stagionalita.py` (solo
descrittivi, dopo i risultati), `risultati.txt`, `condizionati.csv`, `fomc_eventi.csv`, `w3_filtro.csv`, `segnali.csv`, `data/`.

## 1. Cosa dice la letteratura (2018–2026)

| Tema | Affermazione | Orizzonte | Dimensione | Campione | Robustezza (giudizio) |
|---|---|---|---|---|---|
| Momentum di serie temporale [1] | Il rendimento di questa settimana predice le prossime 1–4 | 1–4 sett. | +1 dev.st. → +3,2/3,7/3,5/1,5% a settimana; quintile alto 11,2%/sett. contro 2,6% | BTC 2011–2018 | Alta come esistenza (replicato [2][3][4]), ma l'ampiezza 2011–18 non è ripetibile; campione di una bolla |
| Trend following a ensemble [3] | Donchian su più lookback, size a volatilità, top 20 coin | giorni–mesi | Sharpe > 1,5 netto, alpha 10,8%/anno su BTC | 2015–03/2025, senza sopravvivenza | Media-alta (dati senza sopravvivenza, costi), ma alpha in gran parte da altcoin |
| TSMOM contro CSMOM [2] | TSMOM forte, cross-sectional debole; comprare dopo cali perde | 1–4 sett. | n.d. negli estratti | crypto multi-coin | Media (working paper) |
| Dual momentum oro/BTC [5] | Lookback 4–12 settimane il "punto dolce", 8 il migliore | settimanale | n.d. | pratica | Bassa: scelta del lookback a posteriori |
| Politica monetaria [6] | Dal 2020 la stretta Fed abbassa BTC; prima lo alzava | settimane (VAR) | segno cambiato nel 2020 | 2014–2022, alta frequenza + proxy VAR | Alta come metodo; dice che l'effetto non è stabile nel tempo |
| FOMC [7][8] | Gli annunci muovono la volatilità più del rendimento medio | ore–giorni | Interdax: CAAR significativo nelle 6 h dopo | 2019–2020 (blog) / 2020 (COVID) | Bassa-media: campioni piccoli, segni opposti fra studi |
| Liquidità globale/M2 [9][10] | BTC segue M2 globale con ~60 giorni di ritardo | 2–3 mesi | correlazione dei livelli 0,8–0,9 | 2013–2025 (pratica) | **Bassa**: correlazione di livelli con trend comuni; sulle variazioni ~0,04; ritardo instabile; nel 2025–26 divergono |
| Liquidità netta Fed (WALCL−TGA−RRP) [11][12] | Correlazione a 12 mesi 0,5–0,85 | mesi | descrittiva | 2020–2026 (pratica) | Bassa: contemporanea, nessun test predittivo |
| Dollaro DXY [13] | Relazione negativa, instabile e in calo nel tempo | lungo periodo | n.d. | 2015–2024 | Media; già bocciato come filtro di W2 (lezione 86) |
| Flussi ETF spot [14][15][16] | FalconX: Granger p 0,004, risposta +1,2% al giorno 3–4; DWF: correlazione con i 5 giorni dopo 0,03, con i 5 prima 0,54 | 1–5 giorni | debole | 10 mesi (2024) / 694 giorni (2024–2026) | **Bassa come predittore**: il campione più lungo dice che i flussi seguono il prezzo; feedback bidirezionale (Bitwise) |
| Stablecoin [17][18][19] | Emissioni di Tether dopo i cali precedono rialzi (2017); ritorni anomali nelle 24 h attorno alle emissioni; afflussi USDT agli exchange predicono BTC a 1–6 h | ore–giorni | n.d. / intraday | 2017–18; 2019–20 (565 emissioni); 2017–23 intraday | Contestata (Lyons–Viswanath-Natraj: nessun effetto sistematico); effetto intraday, non settimanale |
| Funding/basis [20][21][22] | Carry fino a 40–60%/anno da domanda a leva; basis miglior predittore cross-section ma ad alta frequenza; funding non predice BTC il giorno dopo (R² 0) | giorni | contemporaneo R² 12,5% a 7 g | 2017–2024 | Alta sul meccanismo, nulla come segnale direzionale su BTC (coerente con lezioni 38, 86) |
| Stagionalità [23][24][25] | Nessun effetto giorno/mese persistente; solo volatilità più bassa nel weekend | giorno | piccolo, instabile | 2011–2019; 2013–2026 | Bassa: risultati opposti fra studi, tipico data mining |
| Halving [26][27] | Rendimenti anomali attorno agli halving in calo; Asness: t = +0,35 | ±60 g / 1 anno | non significativo | 4 eventi | Non testabile (4 eventi) |
| On-chain (netflow, MVRV) [19][28] | Afflussi netti BTC agli exchange non predicono BTC (salvo 4 h); MVRV utile solo agli estremi di ciclo | ore / cicli | n.d. | 2017–2023 | Bassa; MVRV non scaricabile gratis in modo lecito e stabile |

## 2. Ipotesi testabili (dati gratuiti e leciti, verificati con curl da questo container)
1. **H1 stablecoin**: crescita a 30 g dell'offerta totale (DefiLlama) > 0 → BTC migliore a 7/30 g. **Testata.**
2. **H2 liquidità netta Fed**: variazione a 28 g di WALCL − TGA − RRP (FRED, con ritardi di pubblicazione) > 0. **Testata.**
3. **H3 FOMC**: deriva prima, reazione e 7 giorni dopo le 47 decisioni 2021–26 (calendario ufficiale Fed). **Testata.**
4. **H4 premio Coinbase** (proxy della domanda USA/ETF, perché i flussi ETF giornalieri non hanno una fonte gratuita con API
   lecita: Farside escluso): Coinbase BTC-USD / (Binance BTCUSDT × USDT-USD) − 1, media 7 g > 0. **Testata.**
5. Dollaro (DTWEXBGS 20 g in calo): non testata, già bocciata come filtro di W2 (lezione 86).
6. Funding/basis estremi come contrarian: non testata, già bocciata (iterazione 5, lezioni 38, 86); la letteratura concorda.
7. Momentum 1–4 settimane: è già la logica di W3 (lezione 70); la letteratura lo conferma, nessun test nuovo utile.
8. Stagionalità giorno/mese: solo descrittiva.

## 3. Esiti (dettaglio in `risultati.txt`)
Rendimento futuro medio ON − OFF in punti %, p = placebo a spostamento circolare (unilaterale).

| Ipotesi | IS 2021–23 (primario) | OOS 2024–26 (primario) | Esito | Come filtro di W3 (10k dal 2021) |
|---|---|---|---|---|
| H1 stablecoin, 30 g | +0,51 (p 0,47) | +0,18 (p 0,55) | NO | 69,3k (DD −21,1%) contro 78,5k |
| H2 liquidità netta, 30 g | +0,77 (p 0,38); a 7 g +2,28 (p 0,03) | +1,38 (p 0,39); a 7 g −0,01 | NO | 42,6k (DD −27,9%) |
| H3 FOMC (pre / reazione / dopo) | −0,93 / +0,42 / −0,77 | −0,16 / −0,55 / −0,76 | NO (p 0,22 / 0,93 / 0,24) | — |
| H4 premio Coinbase, 7 g | +2,44 (p 0,03) | +1,15 (p 0,10) | NO, di poco | 66,2k (DD −21,1%) |

- H4 a 30 g: +5,0 (p 0,15) e +5,6 (p 0,07). Controlli dopo il risultato: positivo in 2021, 2023, 2025, 2026 e negativo in 2022 e
  2024; vicini (finestra 3–30 g, soglia ±0,02%) quasi tutti positivi ma con ampiezze che variano da −6,6 a +7,4; resta positivo
  dentro entrambi i regimi di momentum a 30 g (+1,7 / +1,1), quindi non è solo momentum; correlazione con pf14z +0,02.
- FOMC: nessuna deriva; i |rendimenti| nei 7 giorni dopo sono un po' più ampi (6,2 contro 5,4 punti): volatilità, non direzione.
- Stagionalità: nessun giorno/mese con lo stesso segno e t > 2 in entrambi i periodi ("Uptober" t 2,6 nel 2021–23, 0 dopo).
- Filtri su W3: tutti peggiorano perché bloccano long vincenti (W3 vince il 92% dei trade, ogni long tolto costa); nessuno
  supera il 90° percentile del placebo.

## 4. Proposta
1. Nessuna modifica a W3 (nessun segnale macro/flussi aggiunge informazione all'orizzonte settimanale).
2. Premio Coinbase a 7 g come **contesto** in dashboard (dato gratuito, API pubblica Coinbase, nessun nuovo vincolo) e registro
   su carta; riprovare con preregistrazione identica quando ci saranno ≥ 12 mesi nuovi.
3. Liquidità netta Fed: solo contesto macro (effetto a 7 g nel 2021–23 che sparisce dopo, tipico di un regime: QT 2022).
4. Non investire tempo su FOMC, stagionalità, halving, M2 globale: la letteratura e i nostri dati concordano che sono rumore
   o correlazioni di livelli.

## Bibliografia
1. Liu, Y., Tsyvinski, A. (2021). Risks and Returns of Cryptocurrency. *Review of Financial Studies* 34(6). NBER WP 24877. https://www.nber.org/papers/w24877
2. Han, Kang, Ryu. Time Series and Cross Sectional Momentum in the Cryptocurrency Market (working paper, AUT). https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf
3. Zarattini, C., Pagani, A., Barbon, A. (2025). Catching Crypto Trends. Swiss Finance Institute RP 25-80. https://abarbon.com/papers/catching-crypto-trends
4. Grayscale Research (2023). The Trend is Your Friend: Managing Bitcoin's Volatility with Momentum Signals. https://research.grayscale.com/reports/the-trend-is-your-friend-managing-bitcoins-volatility-with-momentum-signals
5. Quantpedia. Dual Momentum Allocation Between Physical Gold and Bitcoin. https://quantpedia.com/dual-momentum-allocation-between-physical-gold-and-bitcoin-digital-gold/
6. Karau, S. (2023). Monetary policy and Bitcoin. *Journal of International Money and Finance* 137. https://ideas.repec.org/a/eee/jimfin/v137y2023ics0261560623000815.html
7. Interdax (2020). How FOMC Announcements Affect the Price of Bitcoin. https://medium.com/interdax/how-do-fomc-announcements-affect-bitcoin-9f975de87cb3
8. Examining the Effect of Monetary Policy and Monetary Policy Uncertainty on Cryptocurrencies Market (2023). https://arxiv.org/pdf/2311.10739
9. Bitcoin Magazine Pro. Global liquidity and bitcoin price. https://bitcoinmagazine.com/markets/global-liquidity-bitcoin-price
10. BIT Academy. Global M2 decoupling. https://www.bit.com/insights/knowledge-hub/global-m2-decoupling
11. Convex. Net liquidity vs BTC. https://convextrade.com/compare/net-liquidity-vs-btc
12. Keyrock. The Liquidity Source That Leads Bitcoin. https://keyrock.com/the-liquidity-source-that-leads-bitcoin/
13. Pourpourides (2025). Long-term nexus of macroeconomic and financial fundamentals with cryptocurrencies. *Frontiers in Blockchain*. https://www.frontiersin.org/journals/blockchain/articles/10.3389/fbloc.2025.1550720/epub
14. FalconX (D. Lawant, 11/10/2024). What Can Spot ETF Flows Tell Us About the Trajectory of Bitcoin Prices? https://falconx.io/newsroom/what-can-spot-etf-flows-tell-us-about-the-trajectory-of-bitcoin-prices-a-preliminary-statistical-investigation
15. DWF Labs via Cointelegraph (22/10/2026). Bitcoin ETF flows follow price trends. https://cointelegraph.com/news/bitcoin-etf-flows-follow-price-trends-dwf-labs
16. Bitwise. Bitcoin ETP Series – Part 2. https://bitwiseinvestments.eu/blog/crypto-research/bitcoin-etp-series-part-2
17. Griffin, J., Shams, A. (2020). Is Bitcoin Really Untethered? *Journal of Finance*; critica: Lyons, Viswanath-Natraj, VoxEU. https://voxeu.org/article/stable-coins-dont-inflate-crypto-markets
18. Ante, L., Fiedler, I., Strehle, E. (2021). The influence of stablecoin issuances on cryptocurrency markets. *Finance Research Letters* 41. https://www.blockchainresearchlab.org/wp-content/uploads/2020/05/The_Influence_of_Stablecoin_Issuances_on_Cryptocurrency_Markets_BRL_Working_Paper_No_11.pdf
19. Chi, Y., Chu, Q., Hao, W. (2024–25). Return and Volatility Forecasting Using On-Chain Flows in Cryptocurrency Markets. https://arxiv.org/abs/2411.06327
20. Schmeling, M., Schrimpf, A., Todorov, K. Crypto Carry. BIS WP 1087 / CEPR DP 20719. https://www.bis.org/publ/work1087.pdf
21. Fundamentals of Perpetual Futures (arXiv 2212.06888). https://arxiv.org/abs/2212.06888v4 ; sintesi del confronto di 134 predittori (Cao et al.): https://tradingstrategy.ai/docs/learn/carry-trade.html
22. Presto Labs. Can Funding Rate Predict Price Change? https://prestolabs.io/research/can-funding-rate-predict-price-change
23. Baur, Cahill, Godfrey, Liu. Bitcoin time-of-day, day-of-week and month-of-year effects (sintesi Quantpedia). https://quantpedia.com/are-there-any-simple-calendar-effects-in-bitcoin-market/
24. Caporale, G.M., Plastun, A. (2017). The Day of the Week Effect in the Crypto Currency Market. CESifo WP 6716. https://cesifo.org/DocDL/cesifo1_wp6716.pdf
25. NYDIG (2021). The Temporalities of Bitcoin Returns. https://nydig.com/research/the-temporalities-of-bitcoin-returns
26. Veloso et al. (2025). Bitcoin halving events. *JRFM* 18(5) 242. https://www.mdpi.com/1911-8074/18/5/242
27. Asness sugli halving (DL News). https://www.dlnews.com/articles/markets/wall-street-quant-cliff-asness-analyses-bitcoin-halving/
28. Macro Hive. Do flows onto crypto exchanges predict bitcoin price moves? https://macrohive.com/hive-exclusives/do-flows-onto-crypto-exchanges-predict-bitcoin-price-moves

Nota sulle fonti: [1], [3], [6], [14], [15], [19], [20], [22] letti direttamente (abstract o testo); le altre da estratti e sintesi:
i numeri vanno ricontrollati sul testo originale prima di citarli altrove. Fonti di dati: FRED (fred.stlouisfed.org,
fredgraph.csv), DefiLlama (stablecoins.llama.fi), federalreserve.gov (calendario FOMC), Coinbase Exchange API pubblica;
Binance api/fapi rispondono 451 da qui (si usano i dati già in `data/`).
