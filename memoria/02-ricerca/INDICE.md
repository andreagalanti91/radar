# Ricerca: cosa è stato provato (dettagli e numeri in RESEARCH.md, lezioni numerate)
Conclusione generale: dal 2021 solo il trend settimanale (W3) regge; tutto il resto è contesto.
| Tema | Esito | Lezione | Cartella |
|---|---|---|---|
| Liquidazioni (calamita, fasce, cascate, squeeze, mappa v2) | nessun vantaggio | 72, 81, 92, 93 | research/liquidazioni, liq_fasce, liq_squeeze, liqmap_v2 |
| Supporti/resistenze, intraday, swing 2–3 g | nessun vantaggio | 75–77, 82, 95, 97 | research/intraday*, notte_1511/n2, n4 |
| Indicatori classici, Zeiierman, MACD, Ichimoku | nessun vantaggio | 38, 86, 91 | research/indicatori_tv, zeiierman |
| Macro (Fed, FOMC, M2), ETF, stablecoin, premio Coinbase | solo contesto | 96 | research/notte_1511/n3 |
| Giorno di decisione (domenica) | convenzione, tenere | 94 | research/notte_1511/n1 |
| Market maker (assorbimento, compressione) | nessun vantaggio | 98 | research/mm_assorbimento |
| Opzioni (DVOL, skew), ETH/BTC, dominanza, vol targeting, piramidazione | respinti; O2 su carta | 100 | research/p2_nuovi |
| Rischio per trade (avvocato del diavolo) | 25% troppo alto → 10% | 99 | research/dirompente |
| Trader seguito (Chento) | registro dei segnali | 90 | research/chento, radar/xinbox.py |
| W3.1 solo-prezzo su S&P 500, oro, argento, 10 azioni, Dow 2000 | non si trasferisce (0/13) | 104 | research/multi_asset |
| Indicatore EMA200D+VIX | assicurazione sui ribassi dell'indice, non per BTC | 104 | research/ema200_vix, multi_asset |
| Revisione Fable di W3.1 | confermata; uscita 'distribuzione' fragile | 101–103 | — |
| Ingressi a scaglioni (DCA), uscite a scaglioni, TP, stop, distribuzione, 7 giorni | W3.1 resta la migliore | 105 | research/ingressi_uscite |
| Order book e liquidazioni (15 giorni) | nessun supporto, rifare 20/12 e 03/2027 | 105 | research/book_liq |
| Swing brevi su S/R settimanali, stop 5–10%, TP 10–15%, 70/30 con W3.1 (405 configurazioni) | non valida, 0/405 battono W3.1 | 106 | research/swing_sr |
| Swing S/R su 15 asset (indici, oro, argento, petrolio, 10 azioni) | 0/15 validi, sotto il buy & hold | 107 | research/swing_sr_multi |
| Sentiment book + liquidazioni (pagina Book) | descrittivo, 0/14 test; rifare a febbraio 2027 | 108 | research/book_sentiment |
| Take profit +10/15% con rientro, trailing stretto (su W3.2) | 0/8; W3.2 restituisce il 62% dell'MFE: costo dei trend lunghi | 109 | research/tp_rientro |
| W3.2 su ETH, SOL e 8 indici (rischio 25%) | solo ETH al limite; SOL e indici no | 110 | research/w32_multi |
| W3.2 sulle top 100 crypto (27 altcoin valutabili) | passa solo ETH (1/27) | 111 | research/w32_top100 |
| Modello previsionale direzionale BTC a 7 e 30 giorni (logistica, ceppi, walk-forward) | non funziona: uguale a "sale sempre"; il solo flusso perp ha AUC ~0,6 (già in W3.2) | 112 | research/previsionale |
| Previsionale con regimi di mercato e politica economica (Fed, liquidità, rendimenti, dollaro, VIX, CPI) | non funziona (0/6); la politica peggiora il flusso perp | 113 | research/previsionale2 |
| Forza giornaliera: spot contro perp, livelli flip del trader, ingressi/uscite giornalieri su W3.2 | non regge (0/8); regola flip meccanica 10k → 5,1k | 114 | research/forza_giornaliera |
| Cono di probabilità a 30 giorni dalla volatilità (card "Fra 30 giorni") | calibrato, in uso come contesto; il flusso non lo migliora | 115 | research/cono30 |
| Uscita di profitto nel giorno di cascata a favore, con rientro (su W3.2) | non regge (0/6); dentro i trade il trend prosegue 10 volte su 14 | 116 | research/cascata |
| EMA/SMA su 4h, giornaliero e settimanale: atlante di 360 eventi e 4.017 regole di entrata/uscita long/short | nessuna regge; solo il trend lento long/flat ≈ buy & hold con metà DD | 117 | research/ema_sma (anche DATI*.md) |
| Portafoglio di trend su più mercati: 19 ETF (riferimento) e perpetui azioni/materie prime su OKX/Bitget | non funziona; accanto a W3.2 vale quanto la liquidità | 118 | research/trend_multi |
| Supertrend 10/3 su 4h, giornaliero, settimanale; da solo e dentro W3.2 | non regge (0/11 e 0/4); il cambio 1W non chiude mai un trade | 119 | research/supertrend |
| Ricerca Reddit sugli indicatori più citati (solo estratti: accesso bloccato) | lista corta per i test; consenso: nessun indicatore singolo dà vantaggio | — | research/reddit_indicatori |
| TraderA (@TraderA_NB): dossier del metodo (trendline + ritest + confluenza medie, zone orizzontali, piani 3R long/short) | solo apprendimento, nessun test | — | research/tradera |
| Replica e test del metodo di TraderA (trendline + ritest + confluenza EMA, obiettivo alla struttura) | replica parziale; azioni: non funziona (WR 14–16%); crypto: non dimostrabile; W3.2 non migliora | 120 | research/tradera_test (confronto.csv per i nuovi grafici) |
| Zeiierman ciclo 3: regola dell'utente "buy a −90, sell a −20" (giornaliero e 4h, dentro W3.2) | non regge (0/13); vende la forza | 121 | research/zeiierman3 |
| Opzioni su BTC: struttura, uscite, sei segnali indipendenti, opzione al posto dello stop (superficie Deribit 2018–26) | niente batte le 7 regole sul segnale di W3.2 (45–48k $ dal 2018 sulle operazioni chiuse, ≈ W3.2 a metà, perdita massima 5%); nessun segnale in più utile | 122 | research/opzioni_studio (guida operativa: guida/OPZIONI-OKX.md) |
| W3.2 ciclo 2: top 200 crypto (oggi e 2020), top 100 azioni, cancello BTC, parametri per classe, screener annuale, SOL e TAO | non si trasferisce; TRX con cancello BTC da osservare sulla carta (2 trade fanno l'80%); SOL e TAO no; screener no | 123 | research/w32_asset2 |
| Peso del capitale BTC/ETH con W3.2 (50/50, 60, 2/3, 75, 100; con e senza ribilanciamento) | la regola sceglie 100/0 ma la revisione non lo promuove (bias di sviluppo su BTC); 50/50 resta; 2/3–1/3 solo preferenza | 124 | research/peso_btc_eth |
| Indicatore UTXO P/L Count Ratio (CryptoQuant, sostituto MVRV) come supporto a W3.2 | no come regola: H1 migliora per un solo trade dal 2021, placebo p 0,13; chiudere il long in euforia dannoso; solo contesto | 125 | research/utxo_pl |
| Strategia v1 dell'utente (voto di 17 indicatori di trend) contro W3.2 | v1 batte W3.2 solo nel 2018–21 (dove ha scelto le soglie); 2022–26 21,8k contro 44,0k, DD −34 contro −21; 50/50 peggiora; al massimo confronto informativo | 126 | research/v1_confronto |
| Indicatore "dorito" (Leledc InSilico 40/10, 3D e 1D) da solo, come uscita e come filtro di W3.2 | no: 0/8 configurazioni, placebo p 0,44–1,00; uscita al triangolo 68,8k contro 78,5k | 127 | research/dorito |
| Opzioni come direzione di BTC: skew RR25, put/call, DVOL, massimo dolore, B0r filtrata per costo | no per la direzione (segno instabile IS/OOS); massimo dolore non attira (31–44%, p 0,64); DVOL utile solo per l'ampiezza | 128 | research/opzioni_direzione |
