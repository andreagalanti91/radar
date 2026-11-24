# Reddit: quali indicatori vengono indicati come "i migliori" (ricerca del 23/11/2026)

**Conclusione in tre righe.** Reddit non è accessibile al nostro strumento (blocco del sito verso l'accesso automatico): nessun
thread è stato letto per intero, solo estratti restituiti dal motore di ricerca. Con questo limite, il quadro è coerente: gli
indicatori più nominati sono i soliti (RSI, medie mobili, MACD, VWAP, volume profile, ADX, Supertrend, squeeze), ma il parere
prevalente di chi ha esperienza è che nessun indicatore da solo dia un vantaggio e che contino regime, rischio e verifica fuori
campione. Le evidenze numeriche raggiungibili (non di Reddit) dicono la stessa cosa del progetto: reggono solo le regole di trend
lente, che riducono il drawdown più che battere il buy & hold. Nessun candidato nuovo ha una plausibilità alta; la lista corta
serve a chiudere il tema con lo stesso metro, non a promettere un miglioramento di W3.2.

---

## 1. Metodo e copertura

### Accesso
- `reddit.com` (anche con filtro di dominio nella ricerca): **non raggiungibile**. Errore dello strumento: dominio non accessibile
  al nostro user agent. Blocco rispettato: nessun User-Agent alterato, nessun proxy, nessuna API non ufficiale.
- Il motore di ricerca ha però restituito estratti di alcuni thread, indicizzati tramite copie pubbliche di terzi (istanze
  "redlib/libreddit"). **Non ho aperto quelle copie** (sono di fatto proxy di Reddit): ho usato solo l'estratto fornito dalla
  ricerca. Le citazioni sotto sono quindi "come riportate dall'estratto": possono essere parafrasi e vanno verificate sul thread.
- I voti dei commenti e l'ordine "più votati" **non sono verificabili**: gli estratti non li riportano in modo affidabile.

### Query (47 in totale: 5 con filtro sul dominio reddit.com, tutte bloccate; 42 eseguite, di cui 8 in modalità estesa)
Temi cercati, ciascuno in più formulazioni e con i nomi dei subreddit: best indicator tradingview · most successful/profitable
indicator · indicator that actually works · what indicators do profitable traders use · best free tradingview indicators ·
best indicator swing trading · best indicator bitcoin/crypto weekly (bull market support band, 200 week, Pi cycle, weekly MACD) ·
supertrend strategy / settings / backtest · algotrading "do indicators work" / overfitting / regime · moving average crossover e RSI
backtest · LuxAlgo worth it · squeeze momentum / WaveTrend / Market Cipher / Hull / Ichimoku · chandelier exit / ATR trailing /
Donchian · r/Forex best indicator · r/technicalanalysis e r/Trading best indicator · r/RealDayTrading wiki · articoli di stampa
(Benzinga/Yahoo) su thread Reddit · ricerche mirate sui titoli dei thread trovati.

### Thread Reddit trovati: 8 (tutti solo in estratto, nessuno per intero)
URL canonici ricostruiti dall'identificativo del thread; non aperti.

| # | Subreddit, data | Titolo | Commenti (da estratto) | URL |
|---|---|---|---|---|
| R1 | r/TradingView, 06/2023 | Most successful indicator | n.d. (molti) | https://www.reddit.com/r/TradingView/comments/1426vuh/ |
| R2 | r/TradingView, 02/2024 | What is everyone's favorite indicators to use? | n.d. | https://www.reddit.com/r/TradingView/comments/1au3o4l/ |
| R3 | r/TradingView, 07/2024 | What are the best indicators on TradingView? | ~98 | https://www.reddit.com/r/TradingView/comments/1dxgaiu/ |
| R4 | r/algotrading, 10/2023 | Thinking of automating a trading strat involving ADX, MACD and RSI | 103 | https://www.reddit.com/r/algotrading/comments/171h9aq/ |
| R5 | r/algotrading, 08/2025 | Looking for Feedback on Algo Bot Settings – Uses RSI, MACD, VWAP, OBV, SuperTrend, TTM | 58 (commenti non visti) | https://www.reddit.com/r/algotrading/comments/1mok6i5/ |
| R6 | r/Daytrading, 03/2025 | The Best Trading Strategy? After 3 Years, Here's What Actually Works | 243 | https://www.reddit.com/r/Daytrading/comments/1jmzyt3/ |
| R7 | r/Trading, 2026 (data n.d.) | "Are profitable traders just boring or do most…" | n.d. | letto tramite l'articolo Benzinga/Yahoo del 18/05/2026 (sotto) |
| R8 | r/RealDayTrading, 02/2022 | Analysis paralysis | n.d. | https://www.reddit.com/r/RealDayTrading/comments/t1hmm8/ (solo titolo: nessun contenuto) |

Comparsi solo come titolo, senza contenuto utile: r/Daytrading 11l5b5f "My simple profitable day trading strategy" (03/2023);
r/RealDayTrading nzxxwj "Simple and effective day trading method" (06/2021); r/TradingAnalytics 1j61h6l (03/2025, opzioni).

**Non trovati affatto** (nessun estratto): thread di r/swingtrading, r/BitcoinMarkets, r/CryptoCurrency, r/Forex,
r/technicalanalysis, r/pinescript; thread Reddit dedicati a Supertrend; i thread "storici più votati". È il limite principale.

### Fonti non-Reddit lette per intero (pagina aperta e riassunta dallo strumento)
- Yahoo Finance/Benzinga, 18/05/2026, articolo sul thread R7: https://finance.yahoo.com/markets/options/articles/traders-overcomplicate-trading-until-stops-154608926.html
- BoringEdge, Supertrend su BTC giornaliero 2017–2026: https://boringedge.com/bitcoin-supertrend-strategy-backtest/
- CoinQuant, Supertrend su ETH 4h 2020–2026: https://www.coinquant.ai/blog/supertrend-on-ethereum-6-years-of-backtest-results
- HackerNoon, Supertrend di KivancOzbilgic su oro e NZDUSD 2020–2026: https://hackernoon.com/the-truth-about-tradingviews-supertrend-strategy-after-67-years-of-backtesting
- CoinPaprika, otto segnali da manuale su 8 crypto: https://coinpaprika.com/education/crypto-indicators-actually-work
- dev.to (Tessen), 13 strategie classiche su crypto, 6 anni: https://dev.to/tessen/we-graded-13-famous-trading-strategies-on-6-years-of-data-all-13-failed-26o4
- arXiv 2009.12155 (solo abstract): https://arxiv.org/abs/2009.12155v1

### Non raggiungibili
- Quantified Strategies, Donchian su BTC (verifica anti-bot): https://www.quantifiedstrategies.com/?p=1192563 — solo estratto di ricerca.
- Interactive Brokers Campus / Databento sugli indicatori (HTTP 403): solo estratto di ricerca.

### Fonte scartata
- theledgermind.com ("Trading Indicators Reddit", "15.000 post analizzati", "Redditor che ha testato 52 indicatori", percentuali di
  successo): compare in quasi tutte le ricerche ma **non cita i thread** e i numeri non sono riscontrabili. Non usata.
  Stesso giudizio per le pagine tipo "guida Reddit a Supertrend" su domini riciclati (testi generati, senza fonti).

---

## 2. Classifica degli indicatori citati

Le "menzioni" sono il numero di thread Reddit (su 8, in estratto) in cui l'indicatore compare. Con un campione così piccolo la
classifica è **indicativa**: l'ordine oltre le prime tre posizioni non è significativo. La colonna "fuori da Reddit" dice se guide,
pagine di script e forum (BabyPips, EarnForex, TradingView) lo confermano come molto citato: è popolarità, non prova.

| Pos. | Indicatore | Thread Reddit | Comunità | Uso | Parametri / intervalli citati | Regola come la descrivono | Fuori da Reddit |
|---|---|---|---|---|---|---|---|
| 1 | **RSI** | 4 (R2, R3, R4, R5) | TradingView, algotrading | momentum, ingresso, divergenze | 14 periodi; soglie 30/70 | R2: EMA + RSI per vedere le divergenze. R3: "RSI per il momentum". R4: RSI per gli ingressi, ADX per il regime ("basically"). R5: orientamento da RSI e MACD allineati su più intervalli | in ogni guida; "sopra 70 = movimento esteso, non inversione" |
| 2 | **Medie mobili (EMA/SMA, 200 MA)** | 3 (R1, R2, R3) | TradingView | trend, filtro | 200 MA come conferma; fuori da Reddit EMA 9/21 (intraday), 20/21 e 50 (swing), 50/200 | R1: usare l'indicatore solo insieme a supporti/resistenze o alla 200 MA. R3: "medie mobili per la direzione" | regola tipica dei blog: tenere finché il prezzo chiude sopra la media, uscire alla chiusura sotto |
| 3 | **MACD** | 3 (R3, R4, R5) | TradingView, algotrading | forza/conferma del trend | 12, 26, 9 | R3: "MACD per la forza del trend". R4 (dissenso): un commentatore lo definisce il peggiore dei tre e dice che evitarli è stata la sua scelta migliore | incrocio MACD/segnale come segnale swing |
| 4 | **ADX/DMI** | 2 (R4, R5) | algotrading | regime (trend o laterale) | 14 (implicito) | R4: ADX decide il regime, poi l'ingresso con altro | ADX > 20–25 = trend |
| 5 | **Volume Profile** | 1 (R3) + script LuxAlgo "Volume Profile Regression Channel" | TradingView | livelli di prezzo | — | R3: "Volume Profile per i livelli" | "se ne usi uno solo, usa il volume" (attribuzione a Reddit non verificata) |
| 6 | **VWAP** | 1 (R5) | algotrading | filtro intraday, livello | giornaliero | R5: punti al punteggio se sopra VWAP, punti negativi sul rifiuto del VWAP | primo in quasi tutte le guide di day trading: long solo sopra VWAP. Strumento intraday |
| 7 | **Supertrend** | 1 (R5) | algotrading | trend, stop | ATR 10 × 3 (predefinito) | R5: una delle voci del punteggio | fuori da Reddit: long alla chiusura sopra la linea, uscita alla chiusura sotto; per crypto molti alzano il moltiplicatore a 3,5–5 |
| 8 | **TTM Squeeze / Squeeze Momentum (LazyBear)** | 1 (R5) | algotrading | volatilità, rottura | BB 20/2 dentro Keltner 20/1,5 | R5: etichetta "squeeze" nel punteggio | molto citato nelle liste di script gratuiti |
| 9 | **OBV** | 1 (R5) | algotrading | volume | — | R5: voce del punteggio | — |
| 10 | **Bollinger / Keltner** | 1 (R1) | TradingView | ritorno alla media | 20, 2 | R1: funzionano in mercato bilanciato; contro un trend forte "sei nei guai senza piano d'uscita" | — |
| 11 | **Script della comunità** | R1: Lorentzian Classification (machine learning), Laguerre Multi-Filter. R2: SSL, "entropy". R3: Adaptive Trend Finder (log; regressione lineare, citazione vista in un solo estratto), Risk Radar Pro, Maverick oscillator, SlingShot Pro, script LuxAlgo | TradingView | vari | — | R1: Lorentzian "soprattutto insieme a indicatori di trend" | parte dei commenti è promozione di strumenti a pagamento (segnalato negli estratti) |
| — | **Nessun indicatore: price action, livelli, apertura** | 3 (R1, R6, R7) | Daytrading, Trading, TradingView | ingresso | massimi/minimi del giorno prima, pre-mercato, primi 5 minuti; rottura del range d'apertura | R6: rottura e ritorno sul livello; R7: "togli tutti gli indicatori" | intraday, non trasferibile a W3.2 |

**Non trovati citati negli estratti Reddit** (quindi non in classifica): Ichimoku, WaveTrend, Market Cipher, Hull MA, Chandelier
exit, ATR come indicatore, Donchian, EMA ribbon, Parabolic SAR, Pi cycle, bull market support band, media a 200 settimane.
Compaiono solo in pagine di script TradingView, guide commerciali o forum diversi da Reddit (es. ATR per stop e dimensione: stop a
1,5–2 ATR, su TradingView ed EarnForex). Con l'accesso diretto a Reddit quasi certamente comparirebbero: l'assenza è un limite di
copertura, non un dato.

---

## 3. Cosa dicono i trader esperti e algoritmici

### Consenso (ricorre in tutti i thread con contenuto)
1. **Nessun indicatore singolo funziona; servono come conferma, non come innesco.**
   - "Don't rely on indicators or base your strategy on them" — R1, https://www.reddit.com/r/TradingView/comments/1426vuh/
   - "All indicators are lagging. Some are called leading, but they are just speculating" — R1, stesso URL
2. **Prima l'idea, poi l'indicatore; cercare la combinazione che rende porta al sovradattamento.** È la risposta più votata di R4
   (parafrasi dell'estratto: formare prima l'ipotesi e scegliere gli indicatori per realizzarla; cercare un mix "che risulta
   profittevole" produce sistemi sovradattati) — https://www.reddit.com/r/algotrading/comments/171h9aq/
3. **Conta il regime.** Gli strumenti di trend falliscono in laterale e quelli di ritorno alla media falliscono in trend.
   - "Any mean reversion system - keltner channels, Bollinger bands will have this issue" — R1
   - In R4 la divisione dei ruoli "ADX per il regime, RSI per gli ingressi" riceve un "basically".
4. **La complessità è un sintomo; i filtri aggiunti a posteriori uccidono la strategia.**
   - "Complexity is usually a symptom of not trusting the system" — R7, via https://finance.yahoo.com/markets/options/articles/traders-overcomplicate-trading-until-stops-154608926.html
   - "Every time a setup does not work you add a filter to avoid that loss in hindsight" — R7, stesso URL
   - "After six months you have seventeen conditions that all have to align and the strategy fires twice a year" — R7, stesso URL
5. **Quello che conta è fuori dall'indicatore**: gestione del rischio (indicata nell'articolo su R7 come linea di separazione fra chi
   guadagna e chi no), costanza, verifica fuori campione. Un estratto di r/algotrading (thread non identificato) riassume: gli
   indicatori e la logica "mean nothing if your model doesn't perform OOS".
   - "When trading works, it gets boring because you are basically just sitting on your hands" — R7

### Dissenso
- **Combinazioni pesate**: in R4 e R5 c'è chi costruisce punteggi con molti indicatori a pesi diversi (R5: oltre 50 etichette). Altri
  nello stesso R4 ribattono che è proprio la strada del sovradattamento. Non c'è accordo.
- **"Innesco più filtri"**: un commentatore di R4 descrive come pratica comune trovare un buon innesco con un buon rapporto
  rischio/rendimento e poi aggiungere filtri finché compare un vantaggio; è l'opposto del punto 4.
- **MACD**: consigliato in R3 come misura della forza del trend, definito "il peggiore" in R4.
- **Script di machine learning e a pagamento** (Lorentzian, LuxAlgo): consigliati da alcuni, liquidati da altri ("most seem pretty
  poor", R1); una parte dei consigli viene da venditori.
- **Indicatori sì/no**: in r/Daytrading e r/Trading prevale "toglili tutti, guarda prezzo e livelli"; in r/TradingView prevale
  "pochi e come conferma". Sono comunità intraday: il loro "funziona" non riguarda una strategia settimanale.

### Errori tipici indicati
Ottimizzare i parametri sul passato; scegliere la migliore di molte varianti e presentarla come non ottimizzata; ignorare
commissioni e slippage; campioni troppo piccoli; usare dati futuri senza accorgersene (look-ahead); entrare tardi perché il
segnale arriva a movimento fatto; usare strumenti di inversione contro un trend forte senza regola d'uscita.

**Lettura per W3.2.** La frase "diciassette condizioni e la strategia scatta due volte l'anno" è un avvertimento diretto: W3.2 fa
2–3 operazioni l'anno e ha 13 trade dal 2021. Ogni filtro aggiunto su 13 trade è quasi per definizione scelto a posteriori; lo
standard del progetto (scelta su 2014–20, giudizio unico dal 2021, placebo) è coerente con ciò che questi trader raccomandano.

---

## 4. Evidenze numeriche e loro affidabilità

Nei thread Reddit raggiunti **non c'è alcun backtest verificabile**. Le evidenze vengono da fonti collegate, tutte di autori
singoli o di venditori di piattaforme.

| Fonte | Cosa testa | Risultato | Affidabilità |
|---|---|---|---|
| BoringEdge | Supertrend 10×3, BTC giornaliero, long/flat, 08/2017–03/2026, costi 0,05% per lato | CAGR 33,0% contro 37,6% del buy & hold; DD −61,5% contro −83,2%; 38 trade, 42% vincenti, vincita media +42% contro perdita −10%; nel 2021 tre entrate/uscite a vuoto fra 45k e 60k | **media**: regola predefinita, costi inclusi, ma nessuna prova su altri parametri, nessun fuori campione, 38 trade; il periodo include il 2017. Utile come riferimento per research/supertrend |
| CoinQuant | Supertrend 10×3, ETH 4h, long/flat, 2020–05/2026, costi 0,1% | +811%, CAGR 41,7%, DD −53%, 160 trade, 34% vincenti, profit factor 1,20, 8 perdite di fila, recupero in ~3,75 anni | **medio-bassa**: articolo promozionale, buy & hold non riportato, nessuna sensibilità; profit factor 1,20 è un margine sottile |
| HackerNoon | Supertrend 10×3 sempre a mercato su oro e NZDUSD, M15–D1, 2020–09/2026, spread e commissioni reali | Oro H4 profit factor 1,97, ma il 97% del profitto viene dal 2024–26 (2020–23: 1,02–1,09); giornaliero in perdita; NZDUSD in perdita su 3 intervalli su 4; pochi trade fanno tutto l'utile. Giudizio dell'autore: "a good trend filter and a poor standalone robot" | **medio-alta** come smentita: costi reali, sottoperiodi, griglia di parametri dichiarata. Due soli strumenti, non crypto |
| CoinPaprika | 8 segnali da manuale su 8 crypto, 23.602 barre giornaliere, rendimento a 1/7/30 giorni | Incrocio rialzista MACD **sotto** il caso in ogni taglio (49,1% a 7 giorni; 46,3% dal 2023); RSI < 30 sopra la base a 7 giorni (59,7%, 53,8% dopo aver tolto i segnali ravvicinati) ma sotto a 30; golden cross peggio del death cross; base: 49,9% di giorni seguiti da un prezzo più alto dopo una settimana | **media**: buona impostazione (tasso base, eventi indipendenti, sottoperiodi), ma senza costi né regole d'uscita, con distorsione da sopravvivenza; l'autore stesso li chiama "tetti, non stime". Conferma le lezioni del progetto su MACD e incroci di medie |
| dev.to / Tessen | 13 strategie classiche, 10+ coppie crypto, 6 anni, parametri scelti in addestramento e voto fuori campione, costi inclusi | 0 su 13 passa tutti i criteri; le migliori sono di trend (ADX trend rider +10,7 punti base per trade, rottura di Bollinger +3,8, MACD momentum +3,5); il ritorno alla media perde; le due con più vincite perdono dopo i costi | **medio-bassa**: regole, intervallo e costi non pubblicati; l'autore vende il motore di valutazione. La direzione (trend meglio di inversione, margini minimi) è credibile |
| Quantified Strategies (estratto) | Donchian su BTC giornaliero dal 2015; insieme di finestre 5–360 giorni su più crypto | CAGR ~90% contro ~66% del buy & hold; nello studio a portafoglio ~18% e "i costi riducono molto il netto" | **bassa** qui: pagina non letta, periodo dal 2015 dominato dai primi cicli |
| arXiv 2009.12155 (abstract) | Trend following su crypto, walk-forward, primi dieci anni di bitcoin | "255% annualizzato" | **bassa** per l'uso odierno: dati fino al 2020, solo abstract letto |
| Pagine di script TradingView | Supertrend e varianti, profit factor 1,2–1,3 su BTC/ETH; un'analisi su migliaia di combinazioni trova 2 risultati con profit factor > 1, Sharpe > 0 e vincite > 50% | — | **bassa**: risultati dell'autore, selezione a posteriori dichiarata dagli stessi script ("may be due to overfitting") |

**Sintesi delle evidenze.** (a) Supertrend e Donchian su BTC sono varianti dello stesso effetto: stare long nei trend lunghi e
fuori nei ribassi; riducono il drawdown, non battono il buy & hold in rendimento, e hanno 35–45% di trade vincenti. (b) I segnali
d'incrocio (MACD, golden cross) non superano il caso. (c) I risultati dipendono da pochi trade e da un sottoperiodo. Tutto ciò
coincide con la conclusione generale del progetto ("dal 2021 solo il trend settimanale regge") e con W3.2 che ha DD −21% contro
−61% di Supertrend giornaliero: un indicatore di trend generico difficilmente migliora W3.2, al più la replica peggio.

---

## 5. Lista corta per lo studio di backtest

Ordine per plausibilità di aggiungere qualcosa **dentro W3.2** (non come strategia a sé). Parametri predefiniti da manuale, da non
ottimizzare; valutare su 4h, giornaliero e settimanale, BTC (ed ETH come controllo), con lo stesso metro del progetto: scelta su
2014–20, giudizio unico dal 01/01/2021, costi, confronto con W3.2 (78.474 $, DD −21,1%) e con un placebo.
"Già testato" deriva da `memoria/02-ricerca/INDICE.md`, `memoria/01-strategia/STRATEGIE.md` e da una ricerca per parola chiave in
`RESEARCH.md` (righe indicate): va riletto il testo prima di rifare o saltare un test.

| # | Candidato | Regola meccanica e parametri predefiniti | Uso in W3.2 | Già testato nel progetto | Plausibilità |
|---|---|---|---|---|---|
| 1 | **Supertrend** | ATR(10) Wilder × 3,0. Long alla chiusura sopra la linea, uscita alla chiusura sotto. Varianti fisse: ×4 e ×5 (crypto), giornaliero e settimanale | conferma dell'ingresso; uscita alternativa | **in corso** (research/supertrend). Come filtro giornaliero già provato: nessun vantaggio significativo (RESEARCH.md riga ~1122) | media: è il più simile a W3.2; atteso DD peggiore (rif. BoringEdge −61,5%) |
| 2 | **Chandelier exit** | Uscita long = massimo più alto a 22 barre − 3 × ATR(22); uscita alla chiusura sotto. Settimanale: 22 → 10 settimane non ottimizzato | sola uscita, al posto dell'uscita di W3.2 | **in parte**: trailing ATR e chandelier nominati (RESEARCH.md ~1253, ~1474); trailing 1,5 ATR bocciato (lezione 109: W3.2 restituisce il 62% del massimo favorevole) | medio-bassa: è l'unico punto dove W3.2 lascia margine, ma i trailing stretti hanno già perso; provare solo quello largo |
| 3 | **Donchian (Turtle)** | Ingresso alla chiusura sopra il massimo a 20 barre, uscita sotto il minimo a 10; versione lenta 55/20. Settimanale: 20/10 settimane | ingresso/uscita alternativi | **in parte**: "canale 20/10" in uno studio (~1370), Donchian come filtro (~44, ~189), Turtle in elenco (~195) | medio-bassa: stesso effetto di Supertrend |
| 4 | **ADX/DMI come regime** | ADX(14) > 25 e +DI > −DI = trend rialzista; ADX < 20 = laterale (niente ingressi) | filtro sugli ingressi W3.2 | **sì** come filtro (~1122, ~1386); regime ADX < 20 "a gradino" (~1160) | bassa: già respinto; è però l'indicatore meglio piazzato nel test Tessen |
| 5 | **Squeeze Momentum (TTM/LazyBear)** | Squeeze attivo se Bollinger(20, 2) dentro Keltner(20, 1,5 ATR). Long alla prima barra di rilascio con momentum (regressione lineare a 20 barre) > 0; uscita quando il momentum cala per 2 barre o diventa < 0 | innesco su giornaliero/4h con W3.2 long; nessun ingresso in squeeze contrario | **in parte**: squeeze di Bollinger come condizione (~43–48), Keltner come filtro (~187); la regola completa non risulta | bassa: studiato per l'intraday |
| 6 | **Rottura di Bollinger (trend)** | Long alla chiusura sopra la banda superiore (20, 2); uscita alla chiusura sotto la media a 20 | ingresso anticipato rispetto a W3.2 | Bollinger testato (%B, ampiezza, inversione: negativa, ~286); la rottura in senso di trend va verificata | bassa: 2° nel test Tessen ma +3,8 punti base per trade |
| 7 | **RSI come regime di trend** | Long se RSI(14) settimanale > 50 (ingresso alla chiusura sopra 55, uscita sotto 45); niente uso 30/70 | filtro o conferma | **sì**: RSI testato (lezioni 38, 86, 91; file ta_rsi_div_weekly, weekly_macd_rsi) | bassa |
| 8 | **Canale di regressione lineare (tipo Adaptive Trend Finder, log)** | Regressione del log-prezzo su 100 barre giornaliere; long se pendenza > 0 e chiusura sopra la linea centrale; uscita alla chiusura sotto la banda −2 deviazioni standard | filtro di trend | non risulta | bassa: citato una volta; variante di una media lenta (cfr. lezione 117) |
| 9 | **Hull MA** | HMA(55) giornaliera: long se HMA sale (HMA oggi > HMA ieri) per 2 chiusure; uscita quando scende per 2 chiusure | filtro di trend rapido | non risulta (studio 117 copre EMA/SMA, non Hull) | bassa: **non citato su Reddit**, solo pagine di script; più reattivo quindi più falsi segnali |
| 10 | **Fascia di supporto del mercato rialzista** | SMA 20 settimane + EMA 21 settimane: long con chiusura settimanale sopra entrambe, uscita con chiusura sotto entrambe | filtro | **sì** in sostanza: atlante EMA/SMA settimanale (lezione 117) | molto bassa: **non citata su Reddit** negli estratti; duplicato |
| 11 | **Lorentzian Classification** (script di machine learning) | Segnali long/short dello script con impostazioni predefinite, giornaliero; ingresso al segnale, uscita al segnale opposto | conferma | non risulta; affine a "indicatori TradingView vari" e Zeiierman (respinti, lezione 91) e al modello previsionale (lezione 112) | molto bassa: va replicato fuori da TradingView per escludere ricalcolo a posteriori |
| 12 | **VWAP / Volume Profile** | VWAP ancorato all'ultimo minimo settimanale rilevante: long solo sopra; punto di controllo del volume a 26 settimane come livello | filtro | **sì**: lezione 68 (volume profile e VWAP ancorato "non aggiungono nulla"), VWAP 26 settimane (~1370) | nessuna: non rifare |

**Raccomandazione.** Completare il n. 1 (già avviato); se si vuole chiudere il tema, n. 2, 3, 5, 6, 8, 9 in un unico studio con
regole fisse e senza griglie. I n. 4, 7, 10, 12 sono già coperti: citarli e non rifarli. Attesa realistica: 0 su 6, in linea con
le lezioni 38, 86, 91 e 117. Con 13 trade dal 2021, una variante che "batte" W3.2 togliendo uno o due trade è indistinguibile dal
caso.

---

## 6. Avvertenze

- **Copertura**: 8 thread, tutti in estratto, 4 comunità su 10; nessun thread crypto, swing o Supertrend di Reddit. Le "menzioni"
  non sono una statistica. Per una classifica vera serve leggere Reddit da un browser (ricerca interna per "best indicator",
  ordinamento "Top", ultimi 12 mesi e sempre) oppure l'API ufficiale con un accesso autorizzato dall'utente.
- **Citazioni**: riportate come nell'estratto del motore di ricerca o nell'articolo Benzinga/Yahoo; non verificate sull'originale.
  Le parafrasi sono indicate come tali.
- **Selezione**: i thread raccontano i casi riusciti; chi ha perso con un indicatore non scrive "questo è il migliore". Una parte dei
  consigli è promozione di script a pagamento o di corsi (segnalato negli estratti di R1, R2, R3).
- **Opinione contro evidenza**: tutta la sezione 2 è opinione. Le sole evidenze sono in sezione 4, nessuna indipendente e
  replicata; tre su sette provengono da venditori di piattaforme.
- **Trasferibilità**: quasi tutti i consigli riguardano intraday su azioni, indici e futures (VWAP, apertura, EMA 9/21). W3.2 è
  settimanale su BTC ed ETH con 2–3 trade l'anno: la popolarità di un indicatore su r/Daytrading non dice nulla sul suo uso qui.
- **Nessuna modifica** a strategia, dati o sito: questo file è solo ricerca, non committato.
