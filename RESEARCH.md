# Diario di ricerca · Radar Signal BTC

Ciclo di miglioramento automatico: **2 giri al giorno** (07:17 e 19:17 ora italiana): pensiero, apprendimento, test. Il controllo orario di prezzi, ordini, stop e target gira gratis su GitHub Actions.

**Obiettivo (dal 30/10/2026): rendimento corretto per il rischio** = rendimento totale / |max drawdown| (MAR). Il win rate è un vincolo, non l'obiettivo. Ogni iterazione prova un'idea, la valuta con
`python -m radar.research` e la promuove solo se supera il gate in `radar/research.py`:

- MAR (rendimento / max drawdown) migliore di almeno il 5% (obiettivo principale)
- aspettativa nel test (2024–2025) non peggiore di oltre 0,1 punti
- migliore in almeno il 60% dei semestri dal 2022, nessun semestre peggiore di oltre 1,5 punti per trade
- probabilità ≥ 75% che l'aspettativa superi la base (ricampionamento dei trade)
- win rate pulito non più basso di oltre 3 punti
- nessun peggioramento oltre 0,25 punti nel periodo di conferma (2026–oggi)
- non peggiora troppo nel training (2022–23): altrimenti è rumore
- win rate test non più basso di 2 punti, max drawdown non peggiore di 3 punti
- almeno l'80% dei trade attuali
- robustezza: tutte le varianti vicine dei parametri in profitto e con win rate ≥ 70%
- non concentrato: togliendo il trade (o i due trade) che migliorano di più, il candidato deve restare migliore della base (aggiunto dopo l'iterazione 3)
- i nuovi parametri introdotti dal candidato vanno variati anche loro nel test di robustezza: un risultato "a gradino" non si promuove

Regole operative: nessuna promozione mentre un trade è aperto;
ogni promozione viene annunciata su Telegram e annotata qui.

## Studio indicatori tecnici (completato 30/10/2026, iterazione 5)
Esito: nessun indicatore classico migliora la strategia. Su 59 condizioni e 165 incroci, 5 incroci stabili contro 2,9 attesi per caso (p95 7): nessuno significativo. Stabile solo il flusso perp (già nello score). RSI>70 e ADX>25 con DI− hanno edge sul mercato ma non sui trade. MACD, RSI, %B, stocastico, EMA 9/21, OBV sono ridondanti con lo score (ρ 0,6–0,9). Fibonacci, Bollinger/squeeze, proxy liquidazioni, funding/basis/F&G estremi non stabili. Testati in strategia: setup momentum (Donchian 55 + RSI>70) test exp 1,29 vs 1,92; setup short di trend (EMA21×50 + ADX>25 DI−) test exp 1,36 o ridondante: gate NO. Script: indicators.py, evalcand.py (scratchpad di sessione). Piano originale:
1. Calcolare su BTC giornaliero (senza look-ahead): SMA 20/50/100/200 e incroci, EMA 9/21/50/200 e incroci, MACD (12,26,9: linea,
   istogramma, incroci), RSI 14 (zone, divergenze), volume (z-score, OBV, volume relativo, CVD già presente), proxy di
   liquidazioni (crolli dell'open interest insieme a movimenti forti di prezzo e sbilanciamento taker: lo storico delle
   liquidazioni vere non è disponibile gratis), ritracciamenti di Fibonacci (distanza dai livelli 0,382/0,5/0,618 dell'ultimo
   swing a 60–90 giorni), ADX/DI 14 (forza del trend), Bande di Bollinger (posizione %B, ampiezza e squeeze), più altri utili:
   Stocastico, ATR percentuale, Donchian, VWAP ancorato, funding/basis estremi, Fear & Greed.
2. Per ogni indicatore e condizione: potere predittivo sul rendimento a 7/14/30 giorni (correlazione di rango e tasso di
   successo condizionato), separato per periodo 2020–21, 2022–23, 2024–25, 2026, per vedere se è stabile.
3. Incroci: combinazioni di 2–3 condizioni (es. trend ADX forte + RSI in ipervenduto + prezzo sul 0,618 di Fibonacci;
   squeeze di Bollinger + flusso perp positivo). Riportare numero di casi, successo e rendimento medio, sempre per periodo.
   Penalizzare le combinazioni con pochi casi (< 15) e controllare l'effetto "data mining" (quante combinazioni provate).
4. Confrontare con lo score attuale (CVD perp − long/short retail): un indicatore aggiunge informazione nuova o è ridondante?
5. Per i 2–3 risultati più promettenti: test come filtro o come nuovo setup nella strategia con la scorecard e il gate.
6. Conclusione: cosa è favorevole e stabile, cosa no; rapporto in RESEARCH.md e su Telegram come "Giro N · RAPPORTO indicatori".

## Parametri di rischio scelti dall'utente (30/10/2026, 20:30)
Uso del **100% del capitale**, **leva massima 5x**, **long e short**, rischio per trade più alto di prima (da calibrare nei test).
I giri misurano sempre cosa significa in drawdown giornaliero, liquidazione (margine isolato/cross) e peggior trade,
e riportano la frontiera rendimento/DD per leva 1–5x: l'obiettivo DD ≤ 15–20% resta il vincolo dichiarato dall'utente.

## Mandato dell'utente (30/10/2026 sera) — giri autonomi di scoperta
Due giri al giorno (07:17, 19:17) per **scoprire nuove strategie** e **migliorare ingressi e uscite**, in autonomia:
proporre, creare, confrontare con backtest; **se passa il gate si esegue** (promozione con test, README, dashboard, Telegram).
**Gate per nuove strategie** (in aggiunta ai criteri esistenti, mai abbassati): confronto a DD giornaliero fisso 15% (rendimento a
parità di rischio), batte un placebo con la stessa meccanica (ingressi casuali, p ≤ 0,05), walk-forward con geometria scelta solo
sul passato positivo in ogni finestra, vicini dei parametri, esecuzione su 4h/1h con slippage 0,1%, WR ≥ 70%, solo BTC.
**Catalogo da esplorare** (il planner sceglie e aggiunge idee proprie):
- ingressi: flusso perp pf14z come asse (lezione 17), conferma su 4h (reclaim, sweep del minimo), limit dentro la regione prevista,
  ingresso a 2 livelli vicini (famiglia A del giro 10), size per livello di pf14z;
- uscite: TP in R coerente con lo stop, TP parziale + pareggio dopo +0,5 R, uscita su perdita di momentum 4h, uscita a tempo breve,
  zona di vendita prevista come target;
- strategie nuove: posizionamento (short affollati/funding negativo, S3), squeeze dopo liquidazioni, breakout di volatilità
  compressa, reazione a eventi macro (CPI/FOMC), weekend/sessioni, regime trend vs range con regole diverse;
- portafoglio: strategia + quota trend SMA (giro 9 H), più strategie poco correlate con budget di rischio comune.
- osservazione su carta della famiglia A congelata dal 31/10/2026 (2 livelli 40/60 a −0,5 ATR, stop 1 ATR, TP 1 R, rischio 3%).

## AUDIT DEGLI ERRORI (30/10/2026, giro 9, agente K) — base solida
Verificati dati, feature, segnali, ordine degli eventi (48 trade rifatti su candele 1h e 4h), contabilità, live.
Errori corretti (con test in tests/test_audit.py):
1. **Open interest a 0** nell'archivio Binance (07/03/2022, 10/07/2024, 12/07/2024) letto come calo del 100%: due segnali capit falsi
   che spostavano tutta la sequenza e nascondevano uno stop (28/07/2024, −8,4%). Ora OI ≤ 0 = dato mancante.
2. **Stop a pareggio nel giorno del TP1** mai controllato lo stesso giorno: trade chiusi 1–2 giorni dopo, segnali successivi persi.
   Ora si verifica con data/spot_1h.csv (solo se le candele orarie ricompongono il giorno).
3. **Live**: segnali notificati anche con un trade aperto (98 su 147 storici). Ora soppressi come nel backtest.
Effetto: +57,0% → **+34,9%** (1x), 2x +115% → **+57,1%**, 49 trade, WR 81,6%, WR pulito 26,5%, DD giornaliero invariato −28,1% / −50,4%.
Simulazione completa su 1h: +33,9% (il motore giornaliero ora è coerente).
Dubbi aperti: (a) il MAR del gate include test e holdout, ormai non più fuori campione dopo 8 giri → serve un holdout nuovo
(dati futuri) e un gate che usi il DD giornaliero; (b) DD sui minimi del giorno −32,8% (1x); (c) nel piano live i TP sono sul medio
a DCA completa (TP1 ≈ +0,55 ATR) mentre il backtest usa l'ingresso: allineare; (d) un solo trade spostato cambia il risultato
di 5–7 punti: la sequenza è fragile.
**Lezione 16**: validare i dati grezzi prima delle feature (zeri, infiniti, salti >25%) e controllare i valori che hanno fatto
scattare ogni trade. Con ~50 trade in sequenza un segnale falso sposta tutti i successivi.

## Giro 9 · ricerca di fondo (30/10/2026, solo BTC) — sintesi
- **H, famiglie di strategie**: l'unico vantaggio stabile in tutti i periodi è il trend long/flat su media fissa SMA 50/100/200
  (MAR 3,98 dal 2022-03, ma WR 24%, DD −33%); scegliere il "miglior" trend è rumore (walk-forward −11,5%); buy-the-dip semplici
  e filtro SMA200 sulla strategia attuale peggiorano. 50% attuale + 50% media SMA: MAR 3,57, DD −25,7% (correlazione 0,27).
- **I, prevedibilità**: l'unico predittore fuori campione è il flusso perp pf14z (AUC per anno 0,59–0,62, p<0,05 contro etichette
  rimescolate; long 3/3/30 con pf14z>1: +1,0–1,6 ATR nel 2020–25, debole nel 2026). Modelli multivariati, retail L/S, funding,
  OI, F&G, zona prevista: nessun valore aggiunto; probabilità non calibrate (Brier skill negativo).
- **J, scala DCA**: MAE/MFE confermano stop 3 ATR e TP +1/+3; 60/40 a −1,2 ATR migliore (MAR seq. 3,17→4,62, bootstrap 64%: no).
- **Lezione 17**: il segnale che conta è il flusso perp; il resto della differenza la fa la gestione del rischio (size, DD), non
  nuovi indicatori. Prossimi: flow guidato da pf14z, size per livello di pf14z, portafoglio a due parti, rischio fisso per trade.

## Obiettivo aggiornato dall'utente (30/10/2026, 22:30) — sostituisce i precedenti
**Massimo rendimento con drawdown giornaliero calcolato 15–20%** (la leva/size si sceglie per stare in quel DD).
Il **win rate si misura sull'intero periodo** e può essere più basso se il rendimento a DD 15–20% è più alto
(nessun vincolo di WR per singolo anno o per vicino; si riporta sempre). Restano obbligatori: walk-forward positivo,
placebo, vicini in profitto in ogni periodo, bootstrap P(DD > 20%) ≤ 15%, slippage 0,1%.
Con questa definizione H2 (v1) soddisfa i criteri del giro 12 (tutti i vicini in profitto in ogni periodo).
**Timeframe**: usare 1h, 4h, giornaliero e settimanale (trend/livelli settimanali, conferme 4h/1h).
**Modulo su carta**: approvato dall'utente; segue dal vivo il campione (H2) e i candidati, su dashboard e nel resoconto.
**Telegram**: niente messaggi orari di notte; un unico resoconto alle 7 (giro del mattino).

## Giri notturni orari (dal 30/10/2026, richiesta dell'utente) — campione/sfidante
Ogni ora dalle 22:47 alle 06:47 (Roma) un giro breve: una linea di ricerca, un agente, test completo.
**Campione attuale (versione di ricerca v1)**: H2 del giro 12 (WR 79%, +85,4%, DD −11,4%, MAR 7,5; fallisce solo i vicini 2022–23).
Ogni giro prova a creare una **versione migliore** (v2, v3, …): se batte il campione su MAR a DD fisso, WR ≥ 70%, walk-forward,
placebo e vicini, diventa il nuovo campione e si annota qui con i numeri. Nel tool entra SOLO se passa tutti i criteri del gate.
**Catalogo notturno** (un tema per ora, a rotazione, evitando ciò che è già bocciato):
1. Indicatori uno per uno come filtro/conferma di H2: RSI, MACD, Stocastico, ADX/DMI, Bollinger (larghezza, %B), Keltner,
   EMA/SMA (cross e distanza), Ichimoku, SuperTrend, Parabolic SAR, ATR%, OBV, MFI, CMF, VWAP (giornaliero/settimanale,
   ancorato ai pivot), Donchian, Williams %R, CCI, ROC, divergenze RSI/CVD.
2. Supporti e resistenze: pivot giornalieri/settimanali, massimi/minimi swing 4h e 1d, livelli tondi, volume profile (POC/VAH/VAL)
   su 4h/1h, zone di liquidità (cluster di massimi/minimi), retest di livelli rotti.
3. Volume: volume relativo, taker buy/sell (CVD spot e perp su 1h/4h), assorbimento (volume alto + range piccolo),
   picchi di volume ai livelli; "volume in tempo reale" = CVD/volume 1h-4h intraday prima della chiusura giornaliera.
4. Confluenze: punteggio di confluenza (segnale + livello S/R + volume + conferma 4h), richiesto ≥ k fattori.
5. Strategie migliori note in letteratura da testare onestamente su BTC (Turtle, RSI2 su trend, VWAP reversion,
   opening-range 4h, momentum time-series) contro placebo.
- Notte · ora 22:47 — costruito modulo su carta (H2 v1 dal 31/10/2026): radar/paper.py (motore H2 pulito su candele 4h da spot_1h, conto virtuale 10.000 $ a rischio 3%, data/paper.json), chiamata in `daily`, riquadro "Su carta · H2" in dashboard, tests/test_paper.py. Numeri riprodotti identici a eng.py del giro 12: 105 trade, WR 79,0%, +85,4%, DD giornaliero −11,4% (stessi trade, stesso esito trade per trade, equity finale 18.541,59 $ su 10.000).

## Giro 12 · manuale 30/10/2026 notte — test preregistrati · ESITO: NON PROMUOVERE (miglior candidato finora: H2)
- **A, "A + conferma 4h" robusta** (prereg. 24 combinazioni): vince **H2** = ingresso alla prima chiusura 4h oltre il massimo
  delle 2 candele 4h precedenti (short: sotto il minimo), 2 livelli 40/60 a −0,5 ATR dal prezzo di ingresso, stop 1 ATR, TP 1R,
  finestra 72h, tenuta 14 g, rischio 3%. **WR 79,0%, 105 trade, +85,4%, DD −11,4%, MAR 7,5**; ogni anno positivo
  (2022 +17,0, 2023 +13,5, 2024 +6,4, 2025 +17,8, 2026 +15,6 a 1x); walk-forward sceglie H2 in entrambe le finestre e resta
  positivo; placebo p 0,024; bootstrap P(DD>20%) 4%; slippage 0,2% +60%. Tutti i 16 vicini guadagnano in ogni periodo, ma
  4/15 hanno WR 64,6–68,9% nel 2022–23 → criterio preregistrato NON soddisfatto. Stop sotto lo swing 4h: peggiora sempre.
  10.000 $: 1x 19.241 (DD −11,4%), 2x 35.170 (−21,8%), 5x 156.770 (−47,9%); base 1x 13.014 (−28,4%).
- **B, S9 range preregistrata**: NON passa 4/6 criteri (24–25, vicini, walk-forward −1,6%, bootstrap P(DD>20%) 23%);
  con ADX<20 come regime crolla → risultato "a gradino". Portafoglio **50% S9 + 50% A+EMA** (corr −0,03): +78,7%, DD −6,8%,
  MAR 11,6; 2x +209% DD −13,2%; stabile cambiando i parametri di S9 (MAR 5,7–7,3), ma i pezzi non reggono i vicini.
- **Lezione 20**: una conferma di prezzo 4h (micro-breakout nella direzione del segnale) è più robusta di una media mobile;
  lo stop strutturale rende il rischio troppo variabile; due strategie fragili ma scorrelate fanno un portafoglio stabile.
  Correzione della 19: l'affollamento "in range" dipende da una sola definizione di range e da una soglia (non robusto).
- **Prossimo passo concreto**: portare nel repo un modulo di osservazione su carta (paper) che segue ogni giorno H2,
  A+EMA e il portafoglio b) congelati, con Telegram e dashboard; poi gate dedicato su 4h preregistrato (vicini con passi
  più piccoli: TP 0,9/1,1R; WR minimo valutato sull'intero periodo oltre che per periodo).

## Giro 11 · manuale 30/10/2026 sera — leva fino a 5x, ingressi/uscite, strategie nuove · ESITO: NON PROMUOVERE (3 candidati in osservazione)
Motori 4h con slippage 0,1% e liquidazione isolata. Base a 1x con slippage: +30,1%, DD −28,4%; a 5x −27,9% con DD −89,6%.
- **A, ingressi/uscite**: famiglia A + ingresso alla prima chiusura 4h sopra EMA20 4h (finestra 72h), rischio 3%:
  WR 73,6%, 110 trade, **+62,7% a 1x con DD −12,2%**; a DD 15% rende +78% (base +16%); placebo p 0,024; walk-forward ok;
  3x +264% DD −34%, 5x +549% DD −52% (0 liquidazioni). NON passa i vicini (6/17 perdono nel 2022–23, 2 con WR < 70%).
  Uscite: nessuna batte il TP unico 1R (TP parziale + pareggio alza il WR all'80–83% ma dimezza il rendimento); filtro pf14z peggiora.
- **B, strategie nuove**: S9 "regime" (in pratica posizionamento affollato simmetrico long/short SOLO in regime di range):
  WR 76%, +102,8% a 1x DD −12,2%, walk-forward positivo ogni finestra (concatenato MAR 1,75 vs 1,24), placebo p 0,
  correlazione −0,07 con l'attuale; NON passa i vicini (soglia 1,5 → WR 62,5%). S8 compressione→breakout: solo long buono
  (WR 86%), short perdono, walk-forward 22–23 −7%. S7 squeeze e S10 sweep: non distinguibili dal placebo.
- **Lezione 19**: la conferma del momentum 4h all'ingresso vale più di ogni regola di uscita; il posizionamento affollato
  funziona solo in range (fuori dal range lo stesso segnale perde: WR 62%, DD −38,6%); gli short di trend/rimbalzo non aggiungono nulla.
  A 5x il limite non è la liquidazione (stop molto prima) ma il drawdown: con DD ≤ 15–20% la leva sensata è 1,2–1,5x.
- **Osservazione su carta (congelati, senza riottimizzare)**: famiglia A; A + EMA20 4h; S9 range (pb 1, soglia 1,0, TP 1R, stop 2 ATR).
- **Prossimi giri (preregistrati)**: (1) A + EMA 4h con stop sotto il minimo dello swing 4h; (2) S9 solo range con griglia
  dichiarata soglia {0,75;1;1,25} × stop {1,5;2;2,5} × TP {0,8;1;1,2}, giudicata sui vicini; (3) portafoglio attuale 50% + S9 50%;
  (4) S8 solo long come ipotesi nuova.

## Giro 10 · SERA 30/10/2026 — DCA coerente e strategie settimanali (agenti L, M) · ESITO: NON PROMUOVERE / DA APPROFONDIRE
Base dopo l'audit: 49 trade, WR 81,6%, +34,9% 1x, DD giornaliero −28,1%; per stare a DD ≤ 15% va a 0,5x: **+17,8%, DD −14,8%** (riferimento).
- **L, geometria DCA + size a rischio fisso** (motore 4h, 5760 configurazioni dichiarate): famiglia "A" = 2 livelli vicini
  (40% all'apertura, 60% limit −0,5 ATR), stop stretto 1 ATR sotto l'ingresso, TP unico +1 R dal medio, rischio 3% del conto
  (esposizione media 1,16x): **WR 73,9%, +77,4%, DD −14,8%**, positiva in ogni periodo (22–23 +26,7, 24–25 +24,0, 2026 +12,9),
  batte 40 serie di segnali casuali, vicini WR ≥ 69,7%. MA: la scelta della geometria su 2022–23 non si trasferisce al 2024–25
  (walk-forward fallito), bootstrap P(DD > 15%) 37%. Solo 16/1440 configurazioni hanno MAR > 1 in tutti i periodi, tutte della
  stessa famiglia (2 livelli vicini, stop 1–1,75 ATR, TP 0,6–1 R): è il segnale strutturale.
- **M, strategie settimanali** (motore 4h, walk-forward): solo S3 "posizionamento" (short affollati / funding negativo /
  deleveraging, 3 limit, TP +0,5–1 ATR) supera il walk-forward con WR 89,5% e DD −9,8%, ma rende ~3%/anno, 2026 negativo e
  molto sensibile all'esecuzione (+40% → +18% con 0,2% di slippage). Zone, mean reversion, griglia, RSI2: negativi fuori campione.
- **Revisione**: nessuna promozione (walk-forward della geometria fallito, dubbi dell'audit aperti, stop stretto = esecuzione decisiva).
- **Lezione 18**: WR ≥ 70% si ottiene con il rapporto TP/stop (anche ingressi casuali arrivano all'83–89%) e il DD ≤ 15% con la
  size: il vincolo vero è l'aspettativa fuori campione. Confrontare sempre il rendimento a DD fisso (15%) e contro un placebo con la
  stessa meccanica. Stop stretto + rischio fisso (~1,2x) vale ~4 volte lo stop largo a 0,5x a parità di DD, in-sample.
- **Prossimi giri**: (1) congelare la famiglia A (2 livelli 0,5 ATR, stop 1 ATR, TP 1 R, rischio 2,25–3%) e seguirla in
  osservazione su carta su BTC dal 31/10, senza riottimizzare; (2) misurare slippage di stop stretti su candele 1h/1m;
  (3) gate nuovo: rendimento a DD 15% fisso, placebo con stessa meccanica, DD giornaliero, holdout futuro.

## SOLO BTC (decisione dell'utente, 30/10/2026)
Ogni analisi, validazione e osservazione riguarda solo BTC: niente ETH/SOL (né come banco di prova nel gate, né osservazione su carta). Validazione con periodi diversi di BTC, walk-forward, segnali presi uno per uno e barre 4h.

## CORREZIONE DEL BACKTEST (30/10/2026, giro 8, agente G) — leggere prima di tutto
Il backtest calcolava il TP del giorno sul prezzo medio DOPO i limit DCA riempiti nello stesso giorno: dentro la giornata
il massimo spesso arriva prima del calo (verificato su candele a 4 ore). Corretto (`avg_tp` in radar/backtest.py).
Nuova base: 48 trade, WR 83,3%, pulito 29,2%, >1% 66,7%, 1x +57,0% (DD trade −18,0%, giornaliero −28,1%), 2x +115,2%
(DD giornaliero −50,4%), MAR 3,17; train exp 0,57, test 1,93, holdout 0,39. L'esecuzione simulata a 4 ore dà ~+50% a 1x.
Tutti i risultati delle iterazioni 1–8 sono stati misurati con il backtest vecchio: le conclusioni qualitative restano
indicative, i numeri no. Il profilo di riferimento qui sotto è superato.

## Profilo di riferimento scelto dall'utente (30/10/2026) — SUPERATO dalla correzione
**Futures a 2x, 50.000 $ dal 01/03/2022 → ~299.400 $ (+498,9%), max drawdown −31,4% trade per trade, −40,6% reale giornaliero (misurato dal giro 6), 47 trade, win rate 89%.**
Rendimento/drawdown a 2x = 15,9 (12,3 sul drawdown giornaliero). **Traguardo: stesso rendimento (≥ +450% a 2x) con drawdown ≤ −20% (MAR 2x ≥ 22),
poche operazioni ben strutturate in DCA.** I giri valutano sempre anche il profilo 2x (`full_2x` della scorecard).
Dal giro 6 la scorecard riporta il drawdown giornaliero (`dd_daily`) e il gate lo usa: 1x −22,4%, 2x −40,6%, 3x −55,4%
(picco 22/11/2024, minimo 10/03/2025, 441 giorni sott'acqua; causa: stop flow 17/12/2024 e 06/01/2025 + capit 08/03/2025 sceso a −5,3%).

### Piano dei prossimi giri serali (aggiornabile dalla pianificazione e dall'utente)
1. **Drawdown reale + gestione del 40% che corre**: aggiungere alla scorecard l'equity giornaliera mark-to-market (anche a 2x);
   poi trailing alternativi e durata massima del runner, giudicati sul drawdown reale.
2. **Leva per setup**: leva più alta sui setup storicamente più affidabili (capit 14/14, brk 4/4) e più bassa su quelli
   deboli (sflow, fundneg); l'obiettivo è alzare il rendimento a parità di drawdown. Attenzione alla concentrazione.
3. **Drawdown di portafoglio**: size ridotta dopo uno stop o con capitale sotto il massimo, pausa dopo 2 stop di fila
   (il drawdown −31% a 2x viene dalle due perdite di dic 2024 – gen 2025).
4. **Pesi e profondità della DCA**: 30/30/40 o 25/35/40 con l'ultima tranche più profonda; giudicati sulla perdita dei 3 stop.
5. **Filtro di distribuzione** sui long (score negativo + retail long affollato anche con trend rialzista).
6. **Trade "quasi pareggio" e "piccole vincite" (richiesta dell'utente)**: 8 trade 0–1% e 17 trade +1/+3% su 47.
   (a) Valore: cosa succede a MAR, rendimento e drawdown (1x e 2x) se non ci fossero (controfattuale) e quanto capitale/tempo
   bloccano (giorni in posizione che impediscono altri segnali). (b) Prevedibilità: si distinguono al momento del segnale?
   Confronto delle feature d'ingresso (setup, score, regime, ATR, distanza dalla zona prevista, funding, OI, F&G) tra
   piccoli/pareggi e vincite piene, con test fuori campione. (c) Se prevedibili: filtrarli o gestirli diversamente
   (size ridotta, target più vicino, uscita anticipata). (d) Se non prevedibili: verificare se sono il "costo" che protegge
   dai trade perdenti (lezione 2) e tenerli. Conclusione: evitarli o mantenerli, con i numeri.
   Da affiancare al punto 1 nel giro sera 1 (secondo agente di ricerca).
Giri del mattino: verifica operativa, segnali reali contro backtest, un solo parametro veloce collegato al piano serale.
Domenica sera: revisione settimanale e riordino del piano.

## Roadmap (30/10/2026) — ogni voce: ipotesi → test → criterio di successo
Ordine dei giri serali; la pianificazione può riordinare in base ai risultati. Ogni fase si chiude con una lezione appresa.

### Fase 1 · Misurare bene (giri sera 1–2)
- **R1 Drawdown reale**: equity giornaliera mark-to-market a 1x/2x/3x nella scorecard e nel gate. Successo: metrica disponibile e usata dal gate.
- **R2 Trade piccoli e pareggi** (vedi punto 6 sotto): evitarli o tenerli? Successo: decisione motivata con controfattuale e test fuori campione.
- **R3 Campione più grande**: backtest su candele a 4 ore e su più finestre (rolling); stima del win rate con intervallo di confidenza. Successo: intervalli pubblicati in dashboard.

### Fase 2 · Uscite (giri sera 3–4) — il guadagno vero è nel 40% che corre
- **R4 Runner**: trailing ATR/chandelier/SMA20/minimo a N giorni, durata massima 30–60 giorni, uscita parziale nella zona di vendita prevista. Successo: MAR 2x +10% senza peggiorare il drawdown reale.
- **R5 Target a scaglioni**: distanza TP1/TP2 in ATR o multipli del rischio, quote 20/30/50. Successo: meno trade "quasi pareggio" a parità di perdite.

### Fase 3 · Rischio (giri sera 5–7) — traguardo 2x: ≥ +450% con drawdown ≤ −20%
- **R6 Leva per setup**: leva più alta sui setup affidabili (capit, brk), più bassa sui deboli (sflow, fundneg). Successo: MAR 2x ≥ 20 senza concentrazione.
- **R7 Drawdown di portafoglio**: size ridotta dopo uno stop o con capitale sotto il massimo, pausa dopo 2 stop di fila. Successo: drawdown 2x ≤ −22%.
- **R8 DCA**: pesi 30/30/40 o 25/35/40, ultima tranche più profonda, tranche condizionate al setup ancora attivo. Successo: perdita media dei 3 stop −20% senza perdere trade vincenti.

### Fase 4 · Ingressi e nuovi segnali (giri sera 8–10)
- **R9 Filtro di distribuzione** sui long (score negativo + retail affollato anche in trend rialzista).
- **R10 Timing a 4 ore** dentro la regione prevista: tranche al primo rimbalzo invece che a livelli fissi.
- **R11 Nuovi setup** da dati non ancora usati: basis spot-perp, struttura a termine dei funding, OI per exchange.

### Fase 5 · Tool operativo (in parallelo, basso costo, su richiesta)
- **T1** Drawdown reale e intervalli di confidenza in dashboard; **T2** registro segnali reali con scostamento dal backtest;
  **T3** alert di "rischio evento" prima dei dati macro ad alto impatto; **T4** revisione dei difetti grafici segnalati.

### Fase 6 · Dati futuri (dal 2027)
- **R12 Liquidazioni reali** raccolte da oggi; **R13** rivalutazione di SOL dopo 10 trade su carta.

## Obiettivi e struttura dei giri (dal 30/10/2026)
**Obiettivo (utente, 30/10/2026 sera) — sostituisce i precedenti**: strategia swing **con DCA** su BTC con
**win rate ≥ 70%** e **max drawdown giornaliero reale ≤ 15%** (mark-to-market, a 1x; la leva si sceglie dopo in base al DD),
massimizzando il rendimento dentro questi due vincoli. Base corretta oggi: WR 83,3%, DD giornaliero 1x −28,1%, +57%:
il vincolo da conquistare è il **drawdown**, non il win rate.
**Prima di tutto una base solida**: audit completo di motore, dati, feature e segnali (look-ahead, ordine degli eventi
nella giornata, riempimenti, commissioni/funding, date) con verifica su candele a 4h/1h. Nessuna promozione finché
l'audit non è chiuso; ogni errore trovato va corretto con un test di non regressione e i numeri aggiornati ovunque.
**Vincoli**: almeno 8 trade l'anno; perdita massima per trade a 1x ≤ 9%; nessun peggioramento nel 2026.
**Struttura**: 2 giri al giorno (07:17 mattino, 19:17 sera), ognuno con tre fasi: **pensiero** (piano e ipotesi),
**apprendimento** (lezioni dai giri e dai segnali reali), **test** (backtest e gate).

**Giro del mattino (07:17) · verifica e operatività** — breve:
dati e test, segnale della notte, ordini toccati, registro dei segnali reali contro il backtest, SOL su carta,
regione prevista del giorno, calendario macro della giornata; una sola idea "veloce" (parametro singolo) se c'è tempo.
**Giro della sera (19:17) · ricerca approfondita** — una famiglia di idee della roadmap, fino a 5–6 varianti, gate completo,
eventuale promozione.
**Domenica sera · revisione settimanale**: riepilogo della settimana, lezioni apprese, riordino della roadmap.
**Ogni giro impara**: aggiorna "Lezioni apprese" (nuova lezione, conferma o correzione con i numeri) prima di chiudere.
**Ogni giro** chiude il messaggio Telegram con 2–3 **idee proposte** per i giri successivi (cosa, perché, impatto atteso):
l'utente sceglie in chat; senza risposta si segue la roadmap.

**Roadmap della ricerca** (ordine per impatto atteso):
1. Gestione del 40% lasciato correre (fonte principale del guadagno): trailing alternativi (chandelier, SMA20, minimo a N giorni),
   durata massima 30/45/60 giorni, uscita parziale sulla zona di vendita prevista.
2. Drawdown di portafoglio: size ridotta dopo uno stop o con capitale sotto il massimo, pausa dopo stop consecutivi.
3. Filtro di "distribuzione": long bloccati quando score negativo e retail long affollato anche con trend rialzista.
4. Ingressi più precisi con candele a 4 ore dentro la regione prevista (anche per avere più trade e un campione più grande).
5. Liquidazioni reali (quando `data/liquidations.csv` avrà almeno 2–3 mesi).

## Lezioni apprese (aggiornare a ogni giro: è la memoria del ciclo)
1. Più tranche riempite nei trade che poi vanno in stop = perdite più grandi: avvicinare i limit DCA peggiora il drawdown (it. 1).
2. Lo stop a pareggio dopo il TP1 protegge più di quanto costa: toglierlo o allargarlo alza il win rate pulito ma fa crollare l'aspettativa (it. 3).
3. Un miglioramento che dipende da 1–2 trade non è un miglioramento: controllare sempre la concentrazione e variare anche i nuovi parametri (it. 3).
4. Uno stop più largo va sempre abbinato a una size più piccola, altrimenti aumenta la perdita reale sul capitale (it. 3).
5. Il vantaggio di un asset va verificato anno per anno: risultati aggregati possono nascondere un edge concentrato in un periodo (SOL 2022–23, it. 2).
7b. Un vantaggio dell'indicatore sul mercato non diventa vantaggio sui trade: la strategia compra apposta nelle condizioni "brutte" (ADX con DI− dominante: 17 trade, 100% vincenti). Giudicare gli indicatori sui trade, non sul mercato (it. 5).
8. Il drawdown reale (giornaliero) è più ampio di quello trade per trade: 1x −22,4 vs −16,4, 2x −40,6 vs −31,4. Ogni decisione sul rischio va presa sul giornaliero (it. 6).
9. I trade "quasi pareggio" e "piccole vincite" vanno tenuti: toglierli peggiora il MAR in tutti i controfattuali (anche con l'oracolo); non si prevedono al segnale; occupando la posizione bloccano segnali di "secondo ordine" con aspettativa −1,37% (26% perdite) (it. 6).
10. Il trailing a 3 ATR del runner è già vicino all'ottimo: le alternative muovono il DD di ≤ 3 punti e quando sembrano migliori spostano la sequenza dei trade (it. 6).
11. Leva per setup e regole sul capitale (size dopo stop, size sul drawdown, anti-martingala) non creano vantaggio: spostano la leva effettiva o dipendono dai 2 stop di dic 2024–gen 2025. La pausa di 21–45 giorni dopo uno stop raggiunge il traguardo 2x su carta (+616%, DD −17,9) ma salta un solo trade: non dimostrabile con 3 stop (it. 7).
12. Con 47 trade in sequenza ogni modifica che cambia le date di uscita produce risultati "a gradino": per giudicare servono più stop (ETH/SOL come banco di prova, candele a 4 ore) (it. 6–7).
14. Dopo uno stop i segnali dello stesso setup NON sono peggiori (489 segnali, 27 stop reali su BTC/ETH/SOL, eccesso +1,3/+5,4, p 0,71–0,96): pause e reazioni agli stop sono smentite; corregge la lezione 11 (it. 8).
15. La perdita per stop si riduce solo uscendo prima sui trade a DCA completa (TP1 di salvataggio 0,4–0,7 ATR, misurato sul motore vecchio): pesi, profondità, tetti e stop a scaglioni colpiscono i vincenti (it. 8).
13. Prima di ottimizzare, verificare la misura: il backtest giornaliero gonfiava i risultati (TP calcolato dopo i fill dello stesso giorno). Ogni nuova regola di esecuzione va controllata su candele a 4 ore (it. 8).
6. Il guadagno vero arriva dal 40% lasciato correre (uscite a tempo +12%, trailing +8,9%): proteggerlo prima di ottimizzare altro.
7. Il sizing a rischio fisso non crea vantaggio da solo; con soli 3 stop in 47 trade ogni confronto stop largo + sizing dipende da 2–3 trade: giudicarlo a parità di perdita massima per stop, non di drawdown (it. 4).

## Osservazione SOL (dal 30/10/2026, decisione dell'utente)
SOL viene seguito a ogni giro con `python -m radar.observe SOLUSDT` (stessa strategia e parametri di BTC,
dati in `data/SOLUSDT/`, trade solo su carta). Non entra nel tool operativo: niente alert di trading, niente dashboard.
Lo stato è riportato nel messaggio Telegram di ogni giro. Rivalutazione dopo 10 trade chiusi fuori campione o 6 mesi
(criteri: aspettativa > +1%, drawdown del portafoglio non peggiore di BTC da solo, nessun trade < −12%).

## Valutazione ETH e SOL (completata 30/10/2026, iterazione 2)
**Raccomandazione: ETH non aggiungere; SOL solo osservazione; BTC unico operativo.**

Futures 1x, parametri di default (trade / WR / WR>1% / WR pulito / exp % / rend % / maxDD %):

| Periodo | BTC | ETH | SOL |
|---|---|---|---|
| Train 22-23 | 20/90,0/60,0/25,0/+2,01/+46,9/−4,4 | 22/68,2/59,1/22,7/−0,78/−21,5/−45,5 | 20/95,0/95,0/45,0/+7,57/+293,8/−15,2 |
| Test 24-25 | 19/84,2/73,7/42,1/+1,92/+40,2/−16,4 | 23/78,3/73,9/26,1/−0,03/−8,7/−35,1 | 24/75,0/70,8/33,3/+0,54/+2,2/−25,1 |
| Holdout 2026 | 8/100/100/37,5/+2,85/+24,6/0 | 7/85,7/85,7/57,1/+3,77/+28,4/−5,8 | 12/91,7/91,7/25,0/+1,50/+17,7/−10,9 |
| Full | 47/89,4/72,3/34,0/+2,12/+156,7/−16,4 | 52/75,0/69,2/28,8/+0,17/−8,0/−60,5 | 56/85,7/83,9/35,7/+3,26/+373,9/−31,1 |

PnL per anno (% capitale, 2022→2026):

| Asset | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|
| BTC | +14,9 | +25,3 | +25,3 | +11,1 | +22,8 |
| ETH | −14,4 | −2,7 | +2,2 | −2,8 | +26,4 |
| SOL | +89,6 | +61,9 | +27,7 | −14,8 | +18,0 |

Zone previste (`radar/zones.py`):

| | BTC | ETH | SOL |
|---|---|---|---|
| Tocco zona acquisto | 64,9% | 66,1% | 65,9% |
| Sotto la zona | 38,7% | 39,2% | 37,5% |
| Tocco zona vendita | 64,1% | 62,3% | 62,6% |

Portafoglio (rend / maxDD %):

| Mix | Full 1x | Test 24-25 |
|---|---|---|
| Solo BTC | +156,7 / −16,4 | +40,2 / −16,4 |
| 50/25/25 | +154,4 / −17,9 | +21,4 / −17,9 |
| 34/33/33 | +149,4 / −19,3 | +15,1 / −19,3 |
| 70/30 BTC/SOL | +229,5 / −16,1 | +31,1 / −16,1 |

Correlazione pnl mensile dei trade BTC–ETH 0,31, BTC–SOL 0,07. Approssimazione: trade ordinati per data di uscita, niente mark-to-market delle posizioni simultanee.

Rischi:

| | BTC | ETH | SOL |
|---|---|---|---|
| ATR medio dal 2022 | 3,8% | 5,2% | 7,4% |
| Giorni < −20% dal 2020 | 1 | 2 | 7 |
| Funding max \|giornaliero\| | 0,25% | 0,53% | 17,2% |
| Peggior trade 1x | −9,0% | −16,8% | −21,9% |

Piano osservazione SOL: parametrizzare `radar/data.py` per simbolo (cache `data/<SYMBOL>/`, instId OKX dal simbolo), segnali SOL in carta su dashboard/Telegram con size ~0,5x, rivalutare dopo 10 trade fuori campione o 6 mesi (criteri: exp > +1%, DD portafoglio non peggiore di BTC solo, nessun trade < −12%). Il sizing a rischio fisso (priorità "budget per operazione") potrebbe rendere SOL integrabile.

Script e dati della valutazione nella scratchpad di sessione (fetch.py, evalx.py, eval_eth_sol.json).

## Priorità dell'utente (30/10/2026, dopo l'iterazione 1) — affrontare per prime
1. **Stop calcolato**: stop non fisso a 3 ATR dal primo ingresso ma derivato da struttura/volatilità (es. sotto il bordo profondo della zona prevista − k·ATR, minimo a 20 giorni, stop sul prezzo medio dopo ogni tranche, stop a scaglioni). Misurare perdita media e massima per trade.
2. **Drawdown calcolato e limitato**: regole di rischio a livello di portafoglio, es. riduzione della size dopo una perdita o quando l'equity è sotto il massimo di X%, stop di sistema temporaneo dopo N stop consecutivi. Obiettivo: max drawdown a 1x sotto il 12% senza perdere più del 10% di rendimento.
3. **Budget per operazione**: sizing a rischio fisso (es. 1–2% del capitale perso se scatta lo stop, con size = rischio / distanza dello stop, leva massima 3x), sizing per setup in base alla sua storia, confronto con l'allocazione fissa attuale (100% del capitale × pesi DCA). Esito it. 4: con rischio 1–2% la leva media sarebbe 0,1–0,2x (rendimento quasi nullo); il budget sensato per questo sistema è intorno al 7–8% di perdita massima per stop sul capitale allocato a 1x.
4. **Win rate pulito**: riportare sempre, accanto al win rate standard, `win_rate_clean` (solo trade chiusi da target, trailing o tempo in profitto; stop e pareggi esclusi dalle vincite) e `win_rate_1pct` (trade sopra +1%). Un candidato non deve peggiorarli in modo sensibile.

## Backlog prioritario (richiesto dall'utente, 30/10/2026)
Studiare a fondo la gestione a scaglioni, una variante per iterazione:
1. **DCA in entrata**: numero di tranche (2–5), pesi (piramide crescente/decrescente/uguale), distanza tra le tranche in ATR, validità dei limit, ingresso condizionato (tranche solo se il setup resta attivo).
2. **TP in DCA**: numero di target, distanze in ATR o in % del rischio (R multipli), pesi, target su livelli di struttura (massimi a 20g), trailing sul residuo (ATR, chandelier, SMA20).
3. **Stop loss in DCA**: uscita a scaglioni invece di uno stop unico (es. 1/3 a −2 ATR, 1/3 a −2,5, 1/3 a −3), stop per singola tranche, stop temporale parziale, stop che segue il prezzo medio dopo ogni tranche.
4. **Regione prevista** (`radar/zones.py`): posizionare le tranche DCA dentro la zona di acquisto invece che a distanze fisse in ATR; target dentro la zona di vendita.
Ogni variante va confrontata con il gate standard (`radar/research.py`) e riportata qui con i numeri del test.

## Baseline v2 (30/10/2026)
47 trade futures da mar 2022, win rate 89,4%, +157% a 1x, max DD −16,4%. Test 2024–26: 27 trade, 88,9%, aspettativa +2,19%.

## Iterazioni
- **2026-10-30 10:40 UTC · Iterazione 1 · SCARTATO** — Idea: tranche DCA 2 e 3 ai bordi della zona prevista (`radar/zones.py`: buy_hi/buy_lo long, sell_lo/sell_hi short) invece di −0,75/−1,5 ATR fissi, stop invariato. Test 2024–25: aspettativa +1,92% → +1,50%, rendimento +40,2% → +24,8%, max DD −16,4% → −25,4% (train exp +2,01 → +1,94; holdout 2026 +2,85 → +3,16; full 1x +156,7% → +130,3%, 2x +498,9% → +372,1%). Motivo: aspettativa test e drawdown peggiori — la zona è più vicina (0,66/1,33 ATR) e riempie più tranche nei trade stoppati (stop pieno −10,8% a mar 2025). Prossime: tranche più profonde (buy_lo e buy_lo − 0,5 ATR) o peso ridotto nella zona, combinare con stop sul prezzo medio (backlog 3).
- **2026-10-30 11:40 UTC · Iterazione 2 · RAPPORTO** — Valutazione ETH/SOL con parametri invariati: ETH non aggiungere (full −8%, DD −60%, exp test −0,03%), SOL solo osservazione (full +374% ma edge concentrato nel 2022–23, test exp +0,54%, 2025 negativo, peggior trade −21,9%); nessun mix batte BTC da solo nel test. Dettagli nella sezione Valutazione ETH e SOL.
- **2026-10-30 13:05 UTC · Iterazione 3 · NON PROMOSSO (gate superato ma fragile)** — Stop calcolato. (a) stop sul prezzo medio avg − k·ATR: test exp 0,67–1,42 vs 1,92, scartato; (c) pareggio con margine 0,5/1 ATR o solo dopo TP2: test exp 0,85–1,16, DD −25/−28%, scartato (il pareggio dopo TP1 protegge più di quanto costa; WR pulito sale a 61% ma l'aspettativa crolla); (b) stop di struttura sotto il minimo a 20g − 0,5 ATR, limitato 3–5 ATR: test exp 1,92 → 2,95, full +156,7% → +194,9%, DD −16,4 → −7,7, gate formalmente superato. Non promosso: identico a uno stop fisso a 5 ATR, il guadagno dipende da un solo trade (17/12/2024 da −8,96% a −0,52%, che fa sparire anche lo stop del 06/01/2025), risultato a gradino (3,5 ATR peggiora, ≥4,5 migliora) e perdita potenziale per stop +67%. Gate rafforzato con il controllo di concentrazione. Prossimo: stop 3–5 ATR insieme al sizing a rischio fisso (size = rischio / distanza stop, leva max 3x), così uno stop più largo non aumenta la perdita in % del capitale.
- **2026-10-30 14:05 UTC · Iterazione 4 · NON PROMOSSO** — Stop più largo + budget a rischio fisso (size = rischio % / distanza stop dal medio a DCA completa, leva max 3x). Con rischio 1–2% la leva media è 0,1–0,2x e il rendimento full scende a +12/+24%: per rendimenti paragonabili serve rischio 8–15% per trade. Sizing a rischio fisso con stop 3 ATR a leva media 1x: +161,8% DD −17,8 (base +156,7% DD −16,4), nessun vantaggio. Migliore: stop 4,5 ATR + rischio 15,4% (leva media 1x, max 1,78x): full +205,7% DD −11,6 (obiettivo DD<12% raggiunto), test exp 3,18 vs 1,92, holdout 3,71 vs 2,85, ma train exp 1,56 < soglia 1,61 → gate NO; guadagno quasi tutto da 3 trade (17/12/2024, 06/01/2025, 22/07/2026), perdita per stop −11,6% vs −9,0% max base. Prossimo: priorità 2, drawdown di portafoglio (size ridotta dopo uno stop o con equity sotto il massimo).
- **2026-10-30 15:25 UTC · Iterazione 5 · RAPPORTO** — Studio indicatori tecnici (SMA, EMA, MACD, RSI, volume, proxy liquidazioni, Fibonacci, ADX, Bollinger, stocastico, Donchian, funding/basis, F&G): nessun miglioramento, nessun incrocio significativo oltre il caso; unico segnale stabile il flusso perp già usato. Due setup testati, gate NO. Prossimo: drawdown di portafoglio.
- **2026-10-30 16:30 UTC · Giro 6 (RICERCA, fase 1) · PROMOSSO solo misura** — A) R1 drawdown giornaliero mark-to-market integrato in backtest (`mtm`), scorecard (`dd_daily`) e gate (criterio drawdown sul giornaliero), 6 test nuovi; metriche strategia invariate. R4 runner: 13 varianti, migliore chandelier 22g×3 ATR (2x +627%, DD giorn. −37,2) gate NO (ricampionamento 56%, concentrato, SOL 3,26→2,01). B) R2 trade piccoli/pareggi: da mantenere (controfattuali tutti peggiori, non prevedibili, bloccano segnali con aspettativa −1,37%); tp_cap 8% gate NO (a gradino, SOL 0,03).
- **2026-10-30 16:30 UTC · Giro 7 (RICERCA, fase 3) · NON PROMOSSO** — C) R6 leva per setup, 8 schemi: migliore S1 MAR 2x 15,9→19,3 gate NO (ricampionamento 56%, holdout peggiore, concentrato); schemi fuori campione peggiorano (DD 2x −38%). D) R7 drawdown di portafoglio: pausa 21–45 giorni dopo stop 2x +616% DD −17,9 ma salta 1 solo trade (gate NO: 60%, concentrato); size dopo stop, size sul drawdown e anti-martingala non creano vantaggio.
  Idee proposte: 1) ridurre la perdita del singolo stop (R8: DCA 25/35/40, tetto di perdita per trade); 2) pausa per setup/direzione dopo uno stop validata su ETH e SOL (più stop); 3) campione più grande con candele a 4 ore (R3) per uscire dai risultati "a gradino"; 4) TP1 in % più vicino per i trade ad ATR alto con soglia continua.
- **2026-10-30 17:30 UTC · Giro 8 (RICERCA, 3 agenti) · CORREZIONE DEL BACKTEST + NON PROMOSSO** — G) dati 4h costruiti (2021–2026) e scoperto l'errore TP-dopo-fill: corretto in radar/backtest.py, nuova base 48 trade, +57% 1x, DD giorn. −28,1% (vedi CORREZIONE in alto); esecuzione 4h ~+50%; valutazione per singolo segnale (150 giornalieri, 282 a 4h, 24–45 stop) proposta come banco di prova. E) riduzione della perdita per stop: pesi/profondità/tetti/stop a scaglioni no; TP1 di salvataggio 0,6 ATR il migliore (motore vecchio: 2x +620% DD −21,4) ma concentrato → da rifare sulla base corretta. F) pausa per setup dopo uno stop smentita su 3 asset.
  Idee proposte: 1) motore a 4h come riferimento + banco di prova per singolo segnale nel gate; 2) TP1 di salvataggio sulla base corretta, validato sui 24–45 stop; 3) filtro di contesto all'ingresso (stop vs vincite sui 489 segnali di 3 asset); 4) brk e capit sono gli unici setup con aspettativa per segnale nettamente positiva: verificare filtro/size su flow e fundneg.

