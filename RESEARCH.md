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

## Registro dei trade reali (31/10/2026)

Richiesta dell'utente: "così i giri imparano anche dalla mia esecuzione reale". L'utente registra via Telegram i trade eseguiti
(`/entrato`, `/limit`, `/uscito`, radar/journal.py) in **data/journal.json**: per trade strategia, lato, exchange, ingressi, uscita,
risultato % e confronto col segnale (prezzo del segnale, slippage reale %, ritardo in ore; slippage positivo = peggio del segnale).
- **Ogni giro legge data/journal.json e research/LOSERS.md** prima di pianificare.
- Con **almeno 5 trade reali** il backtest usa lo **slippage reale misurato** (media di ingresso, limit e uscita del registro, `journal.averages`) al
  posto dello 0,1% fisso se è più alto; se è più basso si tiene lo 0,1% finché i trade sono pochi. Annotare qui il valore usato.
  Il ritardo medio d'ingresso va confrontato con la lezione sulla latenza (il vantaggio di v2 sta nella barra di conferma).
- **Exchange**: l'esecuzione reale è su **Bybit/OKX**, non su Binance (dati e backtest restano su Binance). Commissioni taker
  futures circa 0,055% (Bybit) / 0,05% (OKX), spot 0,1%. Funding: da verificare che sia simile a quello Binance (prima di fidarsi
  dei costi del backtest sugli short e sulla leva, confrontare il funding storico Bybit/OKX con data/funding.csv).

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

## ATTIVAZIONE W2 settimanale (31/10/2026)
Attivata come SECONDO segnale reale (settimanale) la versione **W2 V1 con tetto di rischio solo sugli short (S-R25)**; v2 invariata.
- Scelta: nessuna variante preregistrata di W5 passava tutti i criteri (R25 su tutti i trade: MAR 11,94 < 14,27). S-R25 (tetto
  R=0,25 solo sugli short, long spot 1x invariati) è una scelta **a posteriori**, per prudenza sulla coda: lo short del 16/03/2020
  passa da −44,7% (1x) a circa −17,9%; dal 2021 cambia solo l'esposizione dei due short del 2022 e di quello del 2025.
- Codice `radar/weekly.py`: porta pulita di /tmp/radar-work/w5/scripts/sim3.py (F1 E1 X3, ex='S', R=0,25, Rshort_only) sui dati del
  repo (data/spot.csv giornaliero, pf14z da `features.build_features`, data/funding.csv), candele W-SUN chiuse. `simulate(f, start)`
  storico; `evaluate(f)` stato (nessuno / segnale / aperto / uscita) con piano in $ su RADAR_CAPITAL × RADAR_WEEKLY_SHARE (1,0).
- Numeri riprodotti esattamente (2021-01-01 → 30/10/2026): 19 trade, 3,26/anno, WR 68,4%, medio +13,4%, peggiore −18,3%, +617,6%,
  DD giornaliero −42,6%, MAR 14,50, 10.000 $ → 71.761 $ (2x 178.309 $, DD −70%). Per anno +135,4 / +19,4 / +42,1 / +54,3 / +1,9 / +14,2%.
  Stessi 19 ingressi, motivi ed esposizioni di research/weekly_w2_sr25_trades.csv. Posizione aperta: long spot dal 24/08/2026 a 77.812.
- Dal vivo (`radar/cli.py daily`, in try/except): stato in data/state.json chiave "weekly"; eventi SEGNALE SETTIMANALE, trailing
  aggiornato (spostamento > 1 ATR giornaliero), allerta distribuzione (una per settimana), USCITA SETTIMANALE (decisa per il lunedì
  o registrata nello storico), stop toccato in tempo reale su candele 1h (una allerta per livello). Primo avvio: un solo messaggio
  "posizione settimanale in corso". Dashboard: sezione Settimanale in Oggi e in Statistiche; Laboratorio "W2 settimanale (in uso,
  short con tetto)". Test: tests/test_weekly.py.
- Limiti: P(DD>40%) circa 50% (bootstrap W5); 19 trade; il flusso perp della domenica può mancare per il ritardo dell'archivio (si usa
  l'ultimo valore disponibile della settimana, come nella ricerca) e un ricalcolo successivo potrebbe cambiare un segnale marginale.

## Priorità dell'utente (31/10/2026 sera): MIGLIORARE L'ALGORITMO
"Per adesso migliora l'algoritmo, lasciamo in secondo piano l'esecuzione vera." I giri orari si concentrano su v2 e W2 (ingressi,
uscite, size, regime, nuove strategie confrontate allo stesso DD); niente lavoro su esecuzione/ordini reali salvo errori.

## Decisione dell'utente (31/10/2026 pomeriggio): segnale SETTIMANALE nel tool
"Trova strategia con meno operazioni, settimanale; adesso vedo tantissime operazioni da 3/5%." L'utente accetta il drawdown in cambio
di poche operazioni grandi: W2 (long in spot, short in perp) viene attivata come SECONDO segnale reale, settimanale, accanto a v2
(che resta), con il rischio dichiarato (DD storico −42,6%, coda fino a −45% su un trade nel 2020). Prima dell'attivazione si testa
il tetto di rischio per trade (lezione 43) e, se migliora la coda senza perdere il profilo, si attiva la versione con tetto.

## Focus dell'utente (31/10/2026, giro delle 12): APPRENDIMENTO DELL'ANALISI TECNICA
"Molti analisti tecnici fanno long o short di BTC con risultati incredibili." Imparare i metodi dell'analisi tecnica discrezionale
(struttura di mercato HH/HL–LH/LL e rottura di struttura, supporti/resistenze con cambio di ruolo, trendline, pattern grafici
— testa e spalle, doppio massimo/minimo, triangoli, bandiere —, ritracciamenti ed estensioni di Fibonacci, divergenze RSI/MACD
settimanali e giornaliere, Wyckoff accumulo/distribuzione, volume profile, medie 20/50/200 e 21W EMA, confluenze), TRADURLI IN
REGOLE OGGETTIVE e testarli con il nostro processo (preregistrazione, walk-forward, placebo, vicini, bootstrap, slippage), dal 2021,
su timeframe settimanale e giornaliero, come strategia a sé e come filtro/uscita di W2 e v2. Attenzione dichiarata: i risultati
pubblicati dagli analisti soffrono di selezione e sopravvivenza (si vedono i trade riusciti); la regola codificata va giudicata
contro il caso. Ogni metodo testato va annotato nelle Lezioni (cosa funziona e cosa no, con i numeri).

## Focus dell'utente (31/10/2026, oggi): STRATEGIA SETTIMANALE — poche operazioni, grandi movimenti
"Meglio 3–4 operazioni l'anno da +20/30% l'una, accettando drawdown, che 100 operazioni da 2–3%." Swing SETTIMANALI, non giornalieri.
Cercare strategie note (online), integrare indicatori, produrre un pensiero proprio per battere il mercato; backtest dal 2021 a oggi
(con storico settimanale dal 2017–2018 per scaldare gli indicatori) con tutto il processo di selezione (preregistrazione, walk-forward,
placebo, vicini, bootstrap a blocchi, slippage). Metriche di riferimento: trade/anno (obiettivo 2–6), guadagno medio per trade
(obiettivo ≥ +15–20%), rendimento annuo composto, max DD giornaliero (accettato più alto, da riportare), MAR, confronto con buy & hold
e con v2. Spunti dalla letteratura: momentum di serie temporale settimanale su BTC (Liu–Tsyvinski 2018: 1–4 settimane), trend
long/flat su medie settimanali (unico vantaggio stabile trovato dall'agente H, giro 9), 200W MA come zona di accumulo, indicatori
di ciclo (MVRV, Pi Cycle) indeboliti negli ultimi cicli (Quantpedia).

## Decisione dell'utente (31/10/2026): estendere v2 ad altri asset (azioni, materie prime, crypto)
Sostituisce "SOLO BTC" per questa linea: analizzare in profondità e testare se v2 conviene su altri asset; se conviene,
upgrade del tool con un filtro per asset. BTC resta il riferimento e il segnale principale finché un asset non passa i criteri
(parametri v2 congelati, senza riottimizzare per asset; criteri obbligatori invariati). Fonti: Binance (spot, perp, metrics,
taker) per le crypto e per XAU/XAG/PAXG; azioni da verificare (Yahoo risponde 429, stooq bloccato).

## Focus dell'utente (31/10/2026, mattina): limitare il drawdown imparando dai trade passati
1. Studiare e apprendere dai trade passati (research/LOSERS.md) per limitare il drawdown: regole candidate R1 (peso v2 solo
   sulla 1ª tranche), R2 (rischio ×0,5 entro 48h da FOMC/CPI/NFP), R3 (short ipervenduti ×0,6), più nuove regole dal registro.
2. Spot vs futures, sempre in DCA: confronto onesto (spot = solo long, niente funding e liquidazione, leva 1x; futures = v2).
3. Swing long o short: trovare la congruenza (confluenza) dei fattori per decidere quando andare a mercato.
4. Addestrare un modello: meta-labeling dei trade v2 (probabilità TP vs stop dai valori all'ingresso) usato come PESO,
   con walk-forward, placebo e calibrazione; niente modelli enormi (lezioni 17, 30).

## Focus dell'utente (31/10/2026): short e direzione del mercato
"Nei periodi difficili meglio short che long": analizzare gli short e la migliore strategia per anticipare se il mercato sale o
scende; backtest dal 2021 a oggi (1h/taker da scaricare per il 2021; metrics solo dal 12/2021). Giri orari tutto il giorno
(minuto 47, tranne 07 e 19). Usare tutte le ricerche fatte (lezioni 1–29): niente ripetizioni di idee bocciate.

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
**Campione attuale: v2 (notte 01:47, H2 con size su delta taker e W-SMA40), nei segnali reali dal 31/10/2026**; v1 = H2 del giro 12 (WR 79%, +85,4%, DD −11,4%, MAR 7,5; fallisce solo i vicini 2022–23).
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

### Notte · ora 22:47 (2) — multi-timeframe: trend settimanale/giornaliero su H2 · NON PROMUOVERE (sfidante su carta)
Preregistrato, 15 combinazioni (W-SMA10/20/40, pendenza W-EMA20, D-50/200 × filtro / peso / peso solo short).
Miglior: **W-SMA40 filtro** (long solo sopra la SMA 40 settimane, short solo sotto): WR 81,8%, 77 trade; a DD 15% **+190%**
(H2 +127%), a DD 20% +311% (H2 +198%); walk-forward positivo; placebo p 0,024. NON passa il bootstrap (P(DD>20%) 27% > 15%),
nel 2026 rende meno di H2 (+10,9 vs +16,9), vicini fragili (SMA32 r15 54,5) e contro "togli 50 long a caso" p 0,07.
Al rischio massimo che tiene il bootstrap: W40 +160,9% vs H2 +123,4%. W-SMA40 peso (4%/2%): +158,9% a DD 15%.
**Lezione 21**: i filtri di trend GIORNALIERI peggiorano (SMA50/200 anche su H2: r15 60,6 vs 127); la media SETTIMANALE lunga
no — precisazione della 7b. Gli short di H2 sono già tutti sotto la W-SMA40; il filtro agisce solo sui long contro trend
(ancora in profitto, ma pesano sul DD). Prossimo: peso continuo sulla distanza dalla W-SMA40 e rischio 2% ai long contro trend,
con placebo "togli trade a caso" obbligatorio.

### Notte · ora 23:47 — volume e CVD intraday 4h su H2 · NON PROMUOVERE (sfidante su carta)
Preregistrato, 24 combinazioni (volume relativo, delta taker, CVD 6/12 × filtro / peso 4%-2%) sulla barra 4h di conferma.
Tutti i 12 FILTRI peggiorano H2 (perdono buoni trade, 2022–23 negativo). I PESI sul delta taker migliorano sempre.
Miglior: **D10 peso** (rischio 4% se delta taker della barra di conferma nella direzione del trade ≥ 0,10, altrimenti 2%):
stessi 105 trade, WR 79%; a DD 15% **+217%** (H2 +127%), a DD 20% +345% (H2 +198%); placebo segnali p 0,024 e placebo
"pesi a caso" p 0,040; vicini tutti positivi in ogni periodo. NON passa il bootstrap al rischio di DD 15% (P(DD>20%) 20,5%)
e il walk-forward sceglie V10+D0 peso, non D10. Al rischio massimo che tiene il bootstrap: +176,8% (H2 +123,4%).
**Lezione 22**: il flusso taker intraday funziona come PESO della size, non come filtro; il volume relativo da solo non serve.
I pesi concentrati alzano la coda del bootstrap anche se il DD storico scende: va sempre verificato al rischio di DD 15%.
Prossimo: peso continuo clip(DT,0,0,15) + peso W-SMA40, delta taker perp e divergenza perp−spot.

### Notte · ora 00:47 — size continua di H2 (delta taker spot/perp + W-SMA40) · NON PROMUOVERE (miglior sfidante finora)
Preregistrato, 20 combinazioni; rendimento valutato al rischio che tiene il bootstrap P(DD>20%) ≤ 15% (r_boot).
**Mk1.5+W0.6**: rischio = 5,24% × (0,5 + 1,5·clip(DT_mix,0,0,15)/0,15) × (0,6 se long sotto la SMA 40 settimane),
DT_mix = media delta taker spot e perp sulla barra 4h di conferma; stessi 105 trade di H2 (WR 79%).
**r_boot +226% (H2 +124%)**, DD −13,5%, per periodo +34 / +63 / +49; placebo segnali p 0,024; pesi permutati p 0,035;
vicini tutti in profitto (k 2,0 e clip 0,10 superano il bootstrap). NON passa il walk-forward per coerenza (train 22–23 sceglie
la fonte spot, 22–25 il mix; entrambi positivi nel test). 10.000 $ al rischio r_boot: 32.580 $ (H2 22.460 $).
**Lezione 23**: il delta taker come peso CONTINUO quasi raddoppia il rendimento a parità di rischio di coda; il delta perp da
solo non basta, la media spot/perp regge meglio il bootstrap; un clip stretto concentra il rischio e fa esplodere la coda.
Prossimo: walk-forward con fonte come unico iperparametro (k 1,5, W 0,6 fissi), tetto al rischio per trade.

### Notte · ora 01:47 — conferma preregistrata dello sfidante di size · NUOVO CAMPIONE DI RICERCA **v2** (con riserva)
Fonte DT come unico iperparametro, selezione per r_boot: il walk-forward sceglie il **mix spot/perp in entrambe le finestre**
(test 24–25 +63,2% DD 13,4% vs H2 +37,2%; test 2026 +45,9% DD 4,2% vs H2 +22,7%). Criteri obbligatori tutti passati:
r_boot +226% vs +124% (1,82×), placebo p 0,024 / 0,035, vicini in profitto in ogni periodo, bootstrap 15,0% (al limite),
slippage 0,2% (rischio 4,67%: +140% vs H2 +71%). Tetto 1,6× inutile (toglie rendimento, non abbassa la coda).
**Riserva**: con il delta taker della barra PRIMA della conferma il vantaggio sparisce (2026 +48,6 → +11,8%; totale +122% vs
H2 +124%): non è look-ahead (la barra di conferma chiude prima dell'ingresso), ma in tempo reale il delta va letto subito alla
chiusura della barra 4h di conferma. Alcuni vicini (k 2,0, clip 0,12, W 0,7) sforano il bootstrap.
**v2 = H2 con size**: rischio = 5,24% × (0,5 + 1,5·clip(segno·DT_mix,0,0,15)/0,15) × m; m = 0,6 se long e ultima chiusura
settimanale < SMA 40 settimane, altrimenti 1; DT_mix = media spot/perp di (2·taker_buy − volume)/volume sulla barra 4h di
conferma; leva = min(5, rischio/stop%); con slippage reale 0,2% rischio base 4,67%. 10.000 $ → 32.580 $ (DD −13,5%) vs H2 22.460 $.
**Lezione 24**: selezionare per r_boot (rendimento al rischio che tiene la coda) rende il walk-forward coerente; il vantaggio del
flusso taker è nella barra di conferma stessa: la latenza di esecuzione conta. Prossimo: modulo su carta anche per v2 (serve il
download dei klines con taker buy spot e perp nel workflow orario), delta su 1h dentro la barra di conferma, rischio che scala col DD.
- Notte · ora 02:47 — v2 aggiunta al modulo su carta (dal 31/10/2026, 10.000 $ virtuali, accanto a H2): `fetch_taker_1h` in radar/data.py
  (data/taker_1h.csv dal 2022-01, ~2,4 MB: spot da data-api.binance.vision in tempo reale, perp dall'archivio data.binance.vision
  mensile/giornaliero; fapi bloccata 451), `dt_4h` / `v2_risk` in radar/paper.py (stesso `simulate` di H2 con funzione di rischio),
  data/paper.json con i conti "h2" e "v2" (rischio per trade nel riferimento storico), riquadro "Su carta · H2 e v2" in dashboard.
  **Regola sul perp**: l'archivio perp arriva con ~1 giorno di ritardo; se manca il perp della barra 4h di conferma, DT_mix = DT spot
  (prudente: spot da solo r_boot +206% vs mix +226%). Riprodotto sui dati al 2026-10-30: 105 trade, WR 79,0%, +225,8%, DD −13,5%,
  10.000 $ → 32.580 $ (ricerca: 32.580 $), stessi trade di H2; test di non regressione in tests/test_paper.py.

## PROMOZIONE v2 nei segnali reali (31/10/2026, approvata dall'utente)
L'utente ha approvato al mattino di sostituire i segnali reali (strategia giornaliera, +34,9% DD giornaliero −28,1%) con **v2**
(campione della notte 01:47). Solo BTC. Rischio base dal vivo **4,67%** (`RADAR_RISK`, validato con slippage 0,2%; ricerca 5,24%).
- `radar/live.py`: il report viene dal motore v2 (`paper.simulate` con `v2_risk(base=RADAR_RISK)` su candele 4h dal vivo);
  stati nessuno / conferma (soglia 4h e scadenza 72h) / ingresso (piano in $ su `RADAR_CAPITAL`, rischio, leva) / aperto;
  rischio dei trade reali congelato alla conferma in data/state.json (`v2_risk_frozen`); storico v2 dal 2022-03 per statistiche
  e dashboard. Eventi: segnale, ingresso confermato, limit eseguito, TP, stop, uscita a tempo, segnale scaduto.
- `radar/intraday.py`: controllo orario su candele 1h di soglia di conferma, limit, stop e TP (una allerta per livello).
- `radar/telegram.py`, dashboard, README aggiornati; il modulo su carta (H2 e v2 virtuali) resta invariato.
  `radar/paper.py` ha solo parametri opzionali (rischio base, slippage) e dettagli dei trade non salvati in paper.json.
- La strategia giornaliera resta in `radar/backtest.py` e `radar/research.py` come banco di ricerca.

Numeri dal vivo (dati al 2026-10-30, rischio 4,67%, slippage 0,1%): 105 trade, WR 79,0%, **+191,6%, DD giornaliero −12,0%**;
2022–23 +30,3% (DD −11,5), 2024–25 +56,9% (−12,0), 2026 +42,7% (−3,9); per anno +15,4 / +12,9 / +10,4 / +42,1 / +42,7%.
10.000 $: 1x 29.151 $, 2x 77.479 $ (DD per trade −22,5%), 5x 835.257 $ (−53,8%). Con slippage 0,2%: +140,3%, DD −12,8%, WR 76,9%.
Test: tests/test_live.py (stati su dati tagliati al trade del 19/08/2026: conferma → ingresso → limit → TP; numeri storici;
slippage 0,2%; messaggi Telegram; controllo orario). Riserve note: bootstrap al limite (15,0%), dipendenza dal delta della barra
di conferma, perp in ritardo (~1 giorno, delta solo spot), ~1 ora di ritardo sulla conferma con il controllo orario.

### Mattino 31/10/2026 07:17 — resoconto della notte inviato su Telegram
Notte: 10 giri (modulo su carta H2 → v2, latenza ridotta; temi trend settimanale, volume/delta taker, size continua,
conferma v2, supporti/resistenze, 12 indicatori, rischio da drawdown). Campione: **v2** (r_boot +226%, DD −13,5%).
Test 23/23. Su carta: 0 trade. BTC 77.369 (30/10), nessun segnale. Decisioni chieste: v2 nei segnali reali, rischio base,
priorità della ricerca.

### Mattino 01/11/2026 07:17 — resoconto inviato su Telegram
Temi delle ultime 24 ore: 10 test (lezioni 49–58), nessuna promozione. Decisione autonoma: W2 resta a 1x (lezione 58). Stato: v2
nessun segnale; W2 long dal 24/08 a 77.812 $ (trailing 71.331 $), BTC ~77.580 $; conti su carta senza trade; test OK.

### Giro orario · 01/11 06:47 — W2: robustezza alla selezione fra 31 prove (DSR, SPA, walk-forward della scelta) · FRAGILE
Preregistrato; simulatore identico a W2 (19 trade, +617,6%, DD −42,6%). DSR 0,964 con N=31 (passa: le config sono correlate, rango
2/31, 25/30 battono B&H allo stesso DD). Ma SPA_c contro **buy&hold p 0,44** (contro flat p 0,04); scelta su 2021-01→2023-06 e
misurata su 2023-07→2026-10: +109% DD −42,6% contro B&H allo stesso DD +115% (fallisce); W2 nella metà B MAR 2,50, WR 50%
(metà A 88%). 2018–20 CVD: W2 20ª su 31 (MAR 3,82, mediana 4,12). Spearman dei ranghi fra periodi 0,13–0,31.
**Lezione 58**: il vantaggio di W2 su buy&hold sta quasi tutto nell'evitare il bear 2022; dal 07/2023 vale un B&H scalato allo
stesso DD. Robusta è la famiglia (regime + uscita su distribuzione), non la config F1E1X3. Decisione: W2 resta attiva a **1x**
(long spot, short R25), nessuna leva 2x; le varianti future si giudicano per media dei vicini/famiglia, non per massimo.

### Giro orario · 01/11 05:47 — v2: size crescente con il retail affollato contro il segnale (ls_z) · NON PROMUOVERE
Walk-forward preregistrato sui 105 trade della v2 vera (train 2022-03→2024-06, test 2024-07→2026-10), b ∈ {0,25; 0,5; 1,0}.
Spearman P–R: −0,12 nel train (segno opposto all'ipotesi), +0,12 nel test (rumore). Test: candidata b 0,5 +108,8% (DD −15,8%) contro
v2 scalata allo stesso DD +138,9% (−30 punti); peggiora in modo monotono con b; slippage 0,2% −16 punti; placebo p 0,67; bootstrap
a blocchi P(miglioramento) 4%. Controllo inverso +4 punti, incoerente.
**Lezione 57**: il posizionamento perp serve a SCEGLIERE i trade (score pf14z − ls_z), non a dimensionarli: la sua intensità al
trigger non predice la grandezza del risultato oltre al peso da DT già in v2 (conferma lezioni 41 e 45).

### Giro orario · 01/11 04:47 — W2: niente short nelle N settimane dopo una capitolazione · SENZA POTENZA
Conteggio prima della griglia: gli short W2 (R25) sono **6 in tutto il 2018–26** (2018-10 +16,6%, 2020-03 −17,9%, 2022-01 +1,0%,
2022-08 +8,3%, 2025-12 +11,9%, 2026-05 +5,7%). Settimane ≤ −2,5 ATRw: solo 2017-12-24 → la candidata (X 2,5, N 8) tocca 0 short.
X=2 tocca solo il 16/03/2020 (= NS2 già testata in W5); con il volume (z ≥ 2,5) toglie anche lo short vincente 2022-08 (+8,3%).
**Lezione 56**: il rischio di coda degli short di W2 è un solo episodio (marzo 2020), non una classe di trade; le regole a evento
dopo un crollo si riducono a NS2 o tolgono short vincenti. La coda degli short resta gestita dalla size (R25), non da filtri.

### Giro orario · 01/11 03:47 — v2-spot come campione indipendente 2017–20 · NON REGGE (ma v2-spot non è v2)
Klines spot Binance 1d/4h dal 2017-08 (motore riusabile in /tmp/radar-work/h16). Proxy preregistrati: pf14z → CVD spot 14g z,
ls_z = 0, capit/fundneg/sfund esclusi, DT spot. Coerenza 2021–26: v2-spot 67 trade, +19% (DD −16%) contro v2 vera 114 trade, +159%
(DD −11%), **solo 11 trade in comune**. Giudice 2018-01→2020-05: 12 trade, −1,2% a trade (IC 90% [−3,3; +0,8]), −14,6%; nessuna
variante (S1–S4) ha IC che esclude lo 0; buy&hold −29%. Scoperta: la v2 vera esiste davvero solo dal **2022-03** (open interest e
L/S retail dal 2021-12 + 90 giorni di z) — anche il "campione 2020-06→12" dei giri 52–54 era una v2 senza flow/capit/sflow.
**Lezione 55**: il vantaggio di v2 sta tutto nei dati di posizionamento perp (L/S retail, OI, funding); lo scheletro spot (geometria,
DCA, size da DT, filtro SMA40w) da solo non ha vantaggio né prima né dopo il 2021. v2 è validata solo sul 2022–26 dove è nata:
il rischio 4,3% resta prudente per questo. Un test indipendente vero richiede dati perp/funding pre-2020 (es. BitMEX); per ls_z non
esiste un sostituto storico, quindi le regole di v2 si giudicheranno soprattutto sui trade reali.

### Giro orario · 01/11 02:47 — v2: regola unica "età del limit + rimbalzo" sulla 2ª tranche · SENZA POTENZA, su carta
Preregistrata (D 2/3/4 giorni × MFE prima del fill m 0,3/0,5R × quota q 0/0,5; candidata D3 m0,5 q0,5), giudice SOLO il campione
indipendente 2020-06→12: 3 trade v2 (tutti long), 2 a due livelli, riempiti dopo 4h e 16h → **0 episodi** in tutta la griglia.
Contesto 2021–26 (dove è nata l'idea): 6 trade toccati (5 stop), candidata +221% vs v2 scalata allo stesso DD +193% (+28 punti):
sono gli stessi riempimenti tardivi di E48, quindi non è una conferma.
**Lezione 54**: le regole sulla 2ª tranche di v2 non si validano su BTC con i dati 4h+taker disponibili (dal 2020-06): servono klines
spot 4h dal 2017 (v2 solo spot) o i trade reali. E48/E72 restano ipotesi su carta.

### Giro orario · 01/11 01:47 — W2: ingresso DCA in 2 tranche (limit a −k·ATRw per 5 giorni) · NON PROMUOVERE
Griglia preregistrata di 12 configurazioni (k 0,25/0,5/0,75 × A "a mercato al 5° giorno" / B "resta a metà" × 1ª tranche 40/50%).
Candidata k0,5 A 50: 2021–26 +451% (DD −40,3%) contro W2 scalata allo stesso DD +546% (−94 punti); 2018–20 CVD −5 punti; bootstrap
P(miglioramento) 10%. Sul 2021–26 perdono tutte e 12; le varianti B "vincono" sul 2018–20 solo per il trade 2020-08 (+146%).
Limit eseguito in 4 trade su 19: i trend migliori (2021-10, 2023-10, 2024-02, 2024-09) non ritracciano.
**Lezione 53**: sul momentum settimanale il DCA in entrata ha valore atteso negativo: entrare tardi costa prezzo, restare a metà
costa size proprio sui vincenti. Il DCA serve dove il ritracciamento è il meccanismo del setup (v2), non su W2. Ingresso pieno al lunedì.

### Giro orario · 01/11 00:47 — v2: peso degli short da funding_z con pf14z < 0 · SENZA POTENZA
Preregistrato: rischio short × clip(0,5 + k·funding_z, 0,5, 1,5) se pf14z < 0 (k = 0,5; vicini 0,35/0,75). Campione indipendente
2020-06→12: 3 trade v2, **0 short** → test vuoto, fermato come da preregistrazione. 2021–26: 26 short, 19 toccati ma raccolti in
2–3 regimi ribassisti (10 nel 2022, 8 fra 11/2025 e 07/2026), 4 stop con funding_z di segno misto (−1,85; +0,71; +0,35; −0,80).
**Lezione 52**: la size degli short di v2 non si stima con il posizionamento (funding): nessun campione indipendente con short, e nel
2021–26 gli short sono pochi regimi, non episodi. Il campione pre-2021 serve solo per regole sui long. v2 invariata.

### Giro orario · 31/10 23:47 — W2: size asimmetrica (long ridotti, short pieni) · NON PROMUOVERE
Giudicata sui campioni non usati per l'idea: 2018–20 (CVD) perde contro W2 scalata allo stesso DD (a=0,5: +92% vs +128%; a=0,75:
+145% vs +164%); 2020 senza short → nessun test. Vince solo nel 2021–26 (dove è nata). **Lezione 51**: pesare di più gli short conviene
solo se gli short vincono; con 2–6 short per periodo il rapporto di size non si stima; lo short post-capitolazione resta il rischio
(−17,9% anche con R25). La size uniforme resta la scelta corretta.

### Giro orario · 31/10 22:47 — W2: piramide solo su rotture non estese (≤ 2 ATRw dalla SMA40) · NON PROMUOVERE
Il filtro lascia 1 aumento su 8 nel 2021–26 (il perdente) e 0 nel 2020 e nel 2018–20: MAR 9,7 vs P50 16,0, placebo p 0,64; vicini
1,5/2,5 uguali. **Lezione 50**: le rotture del massimo a 26 settimane sono quasi sempre > 2,7 ATRw sopra la SMA40 e la distanza non
separa le buone dalle cattive (2021-02 e 2024-02 estese come il perdente 2019-08) → smentisce la versione operativa della lezione 49;
con 3 episodi nel 2018–20 non si costruisce un filtro. A margine: parte del vantaggio di P50 a pari DD viene dalla size asimmetrica
(long 0,5x, short pieni): da testare preregistrata.

### Giro orario · 31/10 21:47 — W2: piramidare sui long vincenti · NON PROMUOVERE (fallisce il campione 2018–20), su carta
Long W2 a 0,5x/0,75x, poi 1x alla prima chiusura sopra il massimo a 26 settimane a trade aperto (13 episodi: 8 nel 2021–26, 2 nel 2020,
3 nel 2018–20). 2021–26: P50 +379% DD −23,7% MAR 16,0 vs W2 scalata allo stesso DD +203%; placebo p 0,005; regge senza i 2 trade
migliori; slippage 0,2% ok; 10.000 $ → 47.900 $ a 1x, 122.272 $ a 2x (DD −43%, come W2 a 1x 71.761 $). 2020: migliore. **2018–20 (CVD):
peggiore** (MAR 2,92 vs 3,82; +149% vs +193% a pari DD): le rotture del 2019 erano picchi parabolici. **Lezione 49**: aggiungere sulla
rottura funziona dopo una base lunga, non dopo un rialzo verticale. Prossimo: aumento solo se la rottura è entro ~1,5–2 ATRw dalla
SMA40 (una soglia, giudicata prima sul 2018–20).

### Approfondimento · 31/10 ore 20 — analisi tecnica seconda passata (TA2) e W2 dopo un long perso (W6) · NON PROMUOVERE
- **TA2**: pattern con tolleranze in ATR (doppi, testa e spalle, triangoli; D e W): 7/12 con < 10 trade, gli altri perdono
  (WR 31–40%, placebo 0,50–0,96) → l'obiezione "definizioni troppo strette" è smentita. Blocco di esaurimento (≥ 2 divergenze RSI
  settimanali consecutive): 1 episodio per lato in 9 anni, 0 nel 2017–2020; su W2 MAR 18–20 vs 14,5 ma da un solo trade (long
  05/2021 −18% evitato) → non promosso; al massimo avviso informativo.
- **W6**: dopo un long W2 perso, nuovo long solo su rottura del massimo a 26 settimane: 5 casi (2 fuori dal 2024); MAR 14,70 vs 14,50,
  peggiore nel 2018–20, placebo p 0,47; DD più basso solo per minore esposizione. Il long successivo a una perdita è sempre una
  ripartenza dal range.
- **Lezione 48**: le regole su eventi rari (divergenze multiple, rientri, filtri dopo perdite) producono "miglioramenti" che sono un
  solo trade; servono ≥ 8–10 episodi indipendenti. Idee: piramidare i long W2 (0,5–0,75x poi 1x sulla rottura del massimo a 26
  settimane); allerta divergenza su più asset per raccogliere episodi.

### Giro orario · 31/10 18:47 — v2: 2ª tranche ridotta se la 1ª non è mai partita (MFE basso) · NON PROMUOVERE
Preregistrato (L02/L04 + controlli H02/H04), 52 trade a 2 livelli dal 2021. Direzione smentita: le 2e tranche con MFE basso sono
le MIGLIORI (riempimento rapido, lezione 34); L02/L04 sotto v2 su ogni criterio (placebo p 0,73/0,82). I controlli opposti (×0,5 se
MFE ≥ 0,4R: rimbalzo poi ritorno tardivo) rendono +11% a r_boot ma placebo p 0,13–0,27 e sono la stessa informazione del
"riempimento tardivo" (E48). **Lezione 47**: MFE basso al riempimento = riempimento rapido = buona 2ª tranche; il segnale debole
negativo è il rimbalzo seguito da ritorno lento. Prossimo: regola unica età del limit + rimbalzo, solo su campione indipendente.

### Giro orario · 31/10 17:47 — W2: stato di range dopo un massimo come filtro dei long · NESSUN EFFETTO
Preregistrato (6 varianti): 0 long W2 su 15 cadono in range con le soglie preregistrate (la SMA40 nel 2024-05→09 saliva ancora
+3–8% in 4 settimane). Soglie larghe (a posteriori) prendono i perdenti del 2024 ma tolgono anche le ripartenze dal range (2023-10
+40%, 2024-09 +31%, 2021-10 +31%): MAR 9–12 vs 14,5 e senza il 2024 crolla. **Lezione 46**: il range del 2024 non diventa una regola;
la SMA40 è troppo lenta e le ripartenze dal range sono dove W2 guadagna di più. Idea: dopo un long perso, il successivo solo su nuova
chiusura sopra il massimo a 26 settimane (casi pochi: preregistrare una sola variante).

### Giro orario · 31/10 16:47 — v2: meta-labeling con etichetta continua (R) dal 2021 · NON PROMUOVERE
Preregistrato (GB e ridge, k 0,5/1, walk-forward semestrale, 94 trade fuori campione). Spearman ŷ–R: GB +0,08 (permutazioni p 0,19),
ridge −0,26 (anti-predittivo); terzili non monotoni. Miglior peso G05 +205% vs v2 +182% ma con più DD (14,2 vs 12,2): v2 scalata allo
stesso DD fa +224%; walk-forward sceglie v2. **Lezione 45**: con più trade e etichetta continua il vantaggio del meta-labeling del
giro 13 sparisce: le feature all'ingresso non dicono nulla sulla grandezza del risultato oltre al peso v2 (conferma 33, 37, 41).
Idea: decidere la 2ª tranche dal comportamento della 1ª nelle prime barre 4h (lezione 32), su campione indipendente.

### Giro orario · 31/10 15:47 — W2: rientro dopo un'uscita su trailing · TEST VUOTO
5 uscite su trailing dal 2021 (0 nel 2020); 0 rientri in tutte e 4 le varianti: in 4 casi su 5 il regime cade entro 1–2 settimane,
e W2 rientra già senza nuovo incrocio della EMA21 (l'unico caso, 07/2024, è l'ingresso normale finito a −15%). Il rientro cieco a k=1
(+723%) è un blocco di sequenza su un solo trade (k=2–4 crollano). **Lezione 44**: le uscite su trailing di W2 cadono a fine trend;
le seconde gambe sono già catturate. Il punto debole resta il range dopo un massimo (2024-05 → 09).

### Giro orario · 31/10 14:47 — validazione indipendente di W2 prima del 2021 · PROVA DEBOLE, W2 resta su carta
Perp/funding Binance solo dal 2020-01 (nessun archivio 2019, API 451); pf14z calcolabile dal 2020-04-12. 2020: 3 trade long (+20%, +66%,
+48% aperto), W2 +195% / V1 +214%, DD −14%, MAR 13–15 vs B&H 5,6 (B&H +302%, DD −54%), placebo p 0,04 → criteri passati, ma il MAR
vince solo perché W2 non esisteva durante il crollo di marzo; dal 13/04/2020 il B&H fa MAR 18,4 (K2 fallisce, p 0,08–0,09).
Variante preregistrata con CVD spot al posto di pf14z (2018–2020): short 16/03–27/04/2020 a **−44,7%** (entrato dopo la capitolazione,
stop a 2,5 ATR settimanali a +63%); sul 2021–26 la variante fa MAR 1,9 → il CVD spot non sostituisce pf14z.
**Lezione 43**: le uscite su distribuzione di W2 si confermano fuori campione (agosto e novembre 2020 vicino ai massimi), ma W2 ha un
rischio di coda non visto nel 2021–26: uno short di regime dopo una capitolazione può perdere ~45% a 1x. Prossimo: tetto di rischio
per trade su W2 (esposizione = min(1, 20% / distanza stop)) o niente short dopo una settimana scesa > 2 ATR, preregistrato.

### Giro orario · 31/10 13:47 — distribuzione come setup short · TEST SENZA POTENZA
Episodi distinti dal 2021: 7 (soglia 0,0006) e 5 (0,0009) < 8 richiesti → solo diagnostica. BTC dopo l'inizio dell'episodio:
14 g −4,4% / −6,9% di media contro +1,1% nei giorni con funding > 0, ma quasi tutto dal crollo di maggio 2021 (−30,5%); senza,
≈ −0,9%. Il 70% dei giorni in distribuzione è nel 2021, nessuno dal 2025. **Lezione 42**: la distribuzione è un'uscita lenta per
lo swing settimanale, non dà abbastanza eventi per un setup a sé. Idea: BTC 2019–2020 come campione indipendente, o funding_z alto
con pf14z negativo come peso continuo degli short v2.

### Giro W4 · 31/10 pomeriggio — portafoglio W2 spot + v2 a peso basso, freno anti-range · NON PROMUOVERE (revisione)
Preregistrato (5 varianti). P1 20/80 e P2 25/75 passano i 5 criteri: P1 dal 2022-03 +188,0% (v2 +170,5%), DD −13,1%, MAR 14,33 (v2 15,41),
P(DD>20%) 0,057 (0,101 con slippage 0,2%), dal 2021 +253% vs +159%, walk-forward 113,1 vs 111,8; 10.000 $ → 28.801 $ (v2 27.051 $).
Peso dinamico (P3) e freno dopo un long perso (placebo p 0,40/0,22) bocciati.
**Revisione: NON PROMUOVERE.** Togliendo il miglior trade W2 (long 02–03/2024, +61%) P1 scende a +159,5%, sotto v2; v2 scalata allo
stesso DD (≈1,1–1,2x) fa +197/+221% con MAR 16–17 e coda più bassa → P1 è dominato; il MAR cala in modo regolare con il peso di W2
(10% 15,7 → 30% 11,9): il "+15 punti" si compra con il DD; i pesi 20/25% scelti dopo il 30/70 fallito; walk-forward non fuori campione
per W2 (scelta su 2021–26); dato dal 2021 trainato dal toro 2021 di W2. Complessità operativa alta (spot+perp, due conti, ribilanciamento).
**Lezione 41**: un componente a pochi trade e DD alto supera "v2 + X punti" solo pagando DD; confrontare sempre con v2 scalata allo
stesso DD e con il test "senza i migliori 1–3 trade". Prossimo: aggiungere questi due controlli al gate; valutare il rischio di v2
~4,8–5% con bootstrap e slippage 0,2%; validare W2 su campione indipendente (BTC 2017–2020).

### Approfondimento · 31/10 ore 12 — analisi tecnica codificata (TA1) e W2 eseguita in spot (W3) · NON PROMUOVERE
- **TA1, analisi tecnica** (9 metodi tradotti in regole oggettive, 34 configurazioni preregistrate, dal 2021, perp 1x long/short):
  NON funzionano Fibonacci (WR 9–11%, 39 stop su 44), pattern grafici (doppi, triangoli; testa e spalle 0 trade con le definizioni
  Lo–Mamaysky–Wang), trendline/retest/spring giornalieri, golden/death cross, BMSB come strategie, nessuna uscita tecnica per W2.
  Migliore: divergenza RSI settimanale (2,1 trade/anno, WR 58%, medio +11,6%, +192%, DD −38%, placebo p 0,015) ma walk-forward fallito
  (2018–22 MAR −0,10; 2023–26 +113% vs B&H +366%). Trendline settimanale MAR 3,37 ma walk-forward −36%. Le scelte "migliori in campione"
  (value area MAR 16,5 nel 2018–22) diventano negative nel 2023–26. Filtro struttura settimanale su W2 passa (MAR 11,97, p 0,03) ma
  cade sui vicini (n=1 8,4; n=3 5,8). Nota: WebSearch non disponibile all'agente, fonti da Wikipedia e letteratura classica.
- **W3, W2 con long in spot** (regole invariate): +676% dal 2021 (vs +448% in perp), DD −42,6%, MAR 15,9, placebo p 0,01,
  walk-forward 2024–26 +82% vs B&H a pari DD +62%; P(DD>40%) 60% (criterio 20%) → non passa. A 0,6x: +285%, DD −27,8%, P 16%, MAR 10,2
  (sotto W2 originale per 0,05). Volatilità costante peggiore della size fissa. Portafoglio 30/70 W2spot/v2 dal 2022-03: +194,4%,
  DD −16,4%, P(DD>20%) 0,154 (limite 0,15; 0,218 con slippage 0,2%) → manca di poco.
- **Lezione 39**: tradotti in regole oggettive, i metodi classici dell'analisi tecnica non battono il caso su BTC (17 su 23 perdono);
  l'eccezione (divergenza RSI settimanale) è instabile fuori campione. I risultati "incredibili" degli analisti soffrono di
  sopravvivenza, selezione e interpretazione a posteriori: il placebo è l'arbitro. **Lezione 40**: per W2 il funding dei long in
  perp era la zavorra principale (spot: MAR 10,3 → 15,9); ridurre la size abbassa la coda ma riporta il MAR al livello originale.
- In Laboratorio: W2 spot e divergenza RSI settimanale. Giro W4 in corso: portafoglio 20/80–25/75 e freno anti-range su W2.

### Giro orario · 31/10 10:47 — "distribuzione" di W2 come peso/blocco dei long v2 · NESSUN EFFETTO POSSIBILE
Preregistrato (6 varianti). Nessuno dei 114 trade v2 dal 2021 (né i 122 segnali long grezzi, né i giorni con un long aperto) cade in
distribuzione (funding 7 g > 0,0006/0,0009 con pf14z < 0): i due regimi sono disgiunti → test senza potenza, v2 invariata.
**Lezione 38**: v2 è già fuori dal mercato quando il funding è alto (mercato a leva); la distribuzione è specifica dello swing
settimanale (spiega la bassa correlazione W2–v2, 0,16). Idea aperta: distribuzione come nuovo setup short (contare prima gli episodi).

### Giro orario · 31/10 09:47 — scadenza del limit della 2ª tranche (E48) · DA APPROFONDIRE (revisione), su carta
Preregistrato: E24/E48/E72/E96 (2ª tranche annullata dopo H ore) e R48/R72 (ridotta). E48: al 4,3% +188,2% vs +170,5%, DD −8,7% vs
−11,1%; r_boot 329,7 vs 225,9 (dal 2021 255,9 vs 181,6); placebo p 0,015/0,02; walk-forward ≥ v2 in 3 finestre; vicini E36–E72 sopra v2.
**Revisione: DA APPROFONDIRE.** L'effetto viene da 9 trade e soprattutto dai 5 riempimenti ≥ 72 h che avevano generato l'ipotesi
(lezione 34); i 4 nuovi (52–68 h) danno effetto nullo; quota di stop 6/9 vs 22/49 non significativa (p ≈ 0,17); con slippage 0,2% la
riduzione del DD sparisce; il +46% a r_boot è quasi tutto leva consentita. Decisione autonoma: NON nei segnali reali; E48/E72 su carta.
Correzione del tool trovata dalla revisione: il controllo orario sorvegliava il limit della 2ª tranche anche dopo la scadenza
(7 giorni) → ora non lo sorveglia più (radar/intraday.py).
**Lezione 37**: un'ipotesi trovata a posteriori e "confermata" sullo stesso campione resta un'ipotesi: separare i trade che hanno
generato l'idea da quelli nuovi; usare statistiche del placebo che non dipendano da un solo cluster di drawdown (R medio, perdita
media degli stop). Prossimo: quantità della 2ª tranche che scala con l'età del limit (regola continua su più trade); verifica del
meccanismo su altri asset o BTC pre-2021 come campione indipendente.

### Giorno 31/10 · ricerche W1 e W2 — STRATEGIA SETTIMANALE (poche operazioni, grandi movimenti) · NON PROMUOVERE, W2 su carta
- **W1, famiglie classiche** (33 configurazioni preregistrate, spot 1x long/flat dal 2021): ensemble momentum 4/8/13/26 settimane
  2,9 trade/anno, WR 29%, medio +11,2%, +278% (10.000 $ → 37.842 $), DD −43,7%, placebo p 0,04, walk-forward positivo; fallisce
  medio ≥ 12%, Calmar ≥ 1,5 e bootstrap (P(DD>40%) 66%; passa solo a 0,6x: +144%, DD −29%). Buy & hold 23.445 $, DD −77%.
  MOM4 da solo +623% ma i vicini +86/+181% → rumore. Funding in futures (+30%/anno nel 2021) e DCA in ingresso tolgono rendimento.
- **W2, composita nostra** (30 configurazioni preregistrate): regime W-SMA40 + pendenza W-EMA20; ingresso con chiusura oltre W-EMA21 e
  pf14z nella direzione; uscita alla prima tra trailing 2,5 ATR settimanali, chiusura oltre W-EMA21, **distribuzione** (funding 7 g
  > 0,0009/giorno con pf14z < 0; specchio per gli short); short solo in regime ribassista; perp 1x.
  **3,3 trade/anno, WR 68,4%, medio +11,5% (miglior +67%, peggior −20%), +448,5% dal 2021, DD −43,6%, 10.000 $ → 54.849 $ (2x 151.126 $,
  DD −71%)**; per anno +102 / +35 / +25 / +44 / −2 / +14; short 5/5 vincenti; placebo p 0,01; vicini 13/13 in profitto 5 anni su 6;
  walk-forward positivo (2023–26 +72,6%, 2025–26 +6,5% vs B&H −18%). Fallisce medio ≥ 12% (11,5) e bootstrap P(DD>40%) 67%.
  Portafoglio 30% W2 / 70% v2 (approssimato sul mensile): +310%, DD −14,5%, correlazione 0,16. Trade: research/weekly_w2_trades.csv.
- **Lezione 36**: nello swing settimanale il vantaggio sta nell'USCITA su distribuzione (funding alto + flusso perp che diverge):
  porta il MAR del trend puro da 1,5 a 7,6; il filtro pf14z all'ingresso batte il caso anche su scala settimanale (conferma 17);
  il DCA sul ritracciamento taglia i trade che corrono; il limite è il DD da range dopo un massimo (05–10/2024: tre long persi di fila).
- **Decisione autonoma**: W2 non entra nei segnali reali (2 criteri preregistrati falliti); va su carta e nel Laboratorio come
  "Settimanale W2". Prossimo: W2 con long su spot e short su perp a esposizione 0,6x o a volatilità costante; "distribuzione" come
  peso/blocco dei long v2; portafoglio 30/70 validato con equity giornaliera reale e lo stesso bootstrap.

### Giorno 31/10 · ricerca ma1 — v2 su altri asset (crypto, materie prime, azioni) · NESSUN ASSET AMMESSO, tool invariato
Parametri congelati, dal 2022-03, rischio 4,3%. BTC +170,5% (placebo p 0,003) unico che passa. XRP +37% (placebo p 0,007, short
positivi) fallisce solo il 2024–25 (−0,8%) → su carta; BNB +12%, LINK +4%; SOL, ETH, DOGE, ADA, AVAX negativi (−28/−46%).
Materie prime: perp XAU/XAG/CL su Binance solo dal 12/2025–04/2026, PAXG perp/metrics dal 03/2025 → storia troppo corta.
Azioni/indici: perp Binance (TSLA, NVDA, SPY, QQQ…) solo dal 2026; Yahoo 429 → nessun dato affidabile per un backtest.
Portafoglio di 9 asset: −16%; selezione fatta su 2022–23 crolla fuori campione (+20% vs BTC solo +112% su 2024–26).
**Lezione 35**: l'edge di v2 è specifico di BTC: sulle alt tutti i setup di flusso/posizionamento hanno aspettativa negativa (salvo
brk), capit scatta 298 volte (OI cala spesso, non è un flush), il delta taker non predice l'esito; la bassa correlazione non salva.
Prossimo: XRP su carta (20 trade fuori campione); oro e azioni dal 2027 con almeno 18 mesi di metrics.

### Giro orario · 31/10 08:47 — 2ª tranche DCA adattiva per trade · NON PROMUOVERE
Preregistrato, 10 varianti: 2ª tranche ridotta se il limit si riempie entro 4/8 h o se il delta taker dell'ultima barra 4h chiusa
è contrario (< −0,05/−0,10), o combinazioni. Tutte sotto v2 (r_boot 180–214 vs 226), perdita max invariata −5,59% (il trade
peggiore, 09/11/2023, ha riempito il limit dopo 84 h), placebo p 0,55–0,88, walk-forward non migliore.
**Lezione 34**: ribalta l'ipotesi — i riempimenti RAPIDI e con delta contrario sono le 2e tranche MIGLIORI (R +0,45/+0,58); è il
riempimento TARDIVO (oltre 3 giorni, 5 trade, 4 stop) a precedere lo stop (indizio trovato a posteriori, da preregistrare).
Prossimo: scadenza del limit della 2ª tranche 48–72 h invece di 7 giorni (preregistrata, placebo "stessa quota a caso").

### Decisione autonoma (31/10/2026, mandato dell'utente: "decidi tu") — rischio dal vivo 4,67% → **4,3%**
Motivo: con dati dal 2021 e slippage 0,2% il rischio massimo con P(DD>20%) ≤ 15% è 4,32% (giro 13 A). Effetto (dal 2022-03,
slippage 0,1%): +170,5% (era +191,6%), DD giornaliero −11,1% (era −12,0%), peggior trade −5,6% (era −6,1%), WR invariato 79%.
Corretto anche il calcolo 2x/5x di dashboard e README: ora rispetta il tetto di esposizione 5x come dal vivo
(10.000 $: 1x 27.056 $, 2x 55.053 $, 5x 121.995 $; prima 5x mostrava cifre senza tetto).
Sfidanti su carta (non nei segnali): R1b60 (2ª tranche ridotta), meta-labeling M2, W-SMA40 filtro, D10.

### Giro 13 · 31/10/2026 mattina — imparare dagli stop, spot vs futures, confluenza, modello · NON PROMUOVERE
- **A, regole dal registro**: R1b60 (2ª tranche DCA ridotta: nozionale ×0,444) DD −25% e perdita max −24% a parità di base,
  r_boot +245% vs +226% (+16% dal 2021), ma walk-forward 166,6 vs 168,4 (2026 peggiore) → sfidante su carta. R1 (peso solo 1ª
  tranche) 86–88% di v2; FOMC ±48h (calendario ufficiale; CPI/NFP non ricostruibili) e short ipervenduti ×0,6 non battono il caso.
  **Avviso**: dal 2021 con slippage 0,2% il r_boot di v2 è 4,32%, sotto il rischio dal vivo 4,67%.
- **A, spot vs futures** (stessi segnali e DCA, 10.000 $ dal 2022-03 a 4,67%): futures v2 29.160 $; futures solo long 20.010 $;
  spot solo long 1x 14.410 $ (tetto 1x taglia 48 long su 82); ibrido long spot + short futures 21.050 $.
- **B, confluenza** (5 fattori, peso o filtro k≥3): migliore +248% (1,096× v2), placebo p 0,15–0,61, il WR non cresce con k.
- **B, meta-labeling** (TP vs stop, walk-forward semestrale): gradient boosting profondità 2 come peso +349% vs +226% (slippage 0,2%:
  +203% vs +140%), walk-forward ≥ v2; ma AUC fuori campione 0,578 (p 0,20), non calibrato, perdita max −8,1%, appoggiato su 14 stop
  → sfidante su carta, da confermare con più trade (2021, etichetta continua in R).
- **Lezione 32**: la perdita dei trade a DCA completa nasce dalla 1ª tranche (−1,43R negli stop), la 2ª ha aspettativa positiva;
  a parità di coda nessuna regola di peso riduce la perdita massima (solo il tetto al rischio). **Lezione 33**: confluenze a soglia
  e modelli usati per separare TP/stop non battono il caso; un modello non lineare come peso può aiutare sulla grandezza dei
  risultati, ma serve un campione più grande.

### Giorno 31/10 · ricerca L1 — solo long, controllo perdite, "quando andare long", registro degli stop · NON PROMUOVERE
**Registro dei trade andati male: research/LOSERS.md e research/losers.csv** (una scheda per ognuno dei 22 stop di v2, con
pattern ricorrenti e regole candidate). Ogni giro di ricerca lo legge e lo aggiorna con i nuovi stop reali.
- Solo long: +122% vs v2 +226% (r_boot), 2026 +18% vs +49% → gli short servono (−46% di rendimento senza).
- Controllo perdite (8 varianti preregistrate): tetto al rischio 2/3/4% (perdita max −2,1/−3,2/−4,3% ma rendimento 23–56% di v2);
  uscita anticipata 3/6 barre (peggiora, anche la perdita max); 2° livello condizionato al delta (peggiora); stop dal medio −1R
  (+5%, non riduce gli stop); TP di salvataggio 0,5/0,75R (peggiora). Frontiera a parità di perdita max: con tetto 3,76% e base
  5,75% la perdita max per trade scende a −4% (10.000 $ → 21.747 $ a 1x vs 29.163 $ di v2).
- Punteggio long (W-SMA40, RSI 4h, volatilità, funding): placebo p 0,48 → bocciato.
- **Lezione 31**: TUTTI i 22 stop hanno riempito il 2° livello DCA (i 56 trade a un livello sono tutti TP); quasi nessuno stop era
  andato in profitto (MFE 0,29R); 6 su 22 sono shock (Celsius, Jackson Hole, FTX, 08/2023, carry trade 08/2024, FOMC 12/2024) dove
  lo stop stretto ha limitato il danno. Le perdite grandi sono il costo del peso sul delta taker, che però paga (terzile alto: 14%
  di stop, +2,0% medio). Unica leva sulla perdita massima: tetto al rischio, a caro prezzo.
- Prossimo: peso v2 solo sulla 1ª tranche (2ª a peso neutro); rischio ×0,5 entro 48h da FOMC/CPI/NFP; short ipervenduti ×0,6.

### Giorno 31/10 · ricerca s1 — short e previsione della direzione dal 2021 · NON PROMUOVERE (v2 resta il campione)
Dati 1h spot/perp con taker scaricati dal 2020-06 (identici al repo). Nel 2021 flow/sflow non scattano (ls_z dal 03/2022) →
v2 ridotto. v2 dal 2021 (bootstrap a blocchi, r_boot 5,07%): +199%, DD 13%; 2021 −9% (soli long fundneg/capit).
Short di v2: 26 trade, tutti sotto W-SMA40 in regime ribassista, WR 80,8%, +1,74 per trade (triplo dei long); nei ribassi
nov 2021–dic 2022 +11,5 e ott 2025–oggi +37,8 (WR 91%). Classificatore "ribasso a 2–4 settimane" (logistica walk-forward):
AUC 0,50–0,52, non batte il placebo circolare (p 0,16), non calibrato; pf14z da solo fa meglio (AUC 0,569, > 0,5 ogni anno).
Gambe short dedicate (pf14z<−x, rimbalzi con delta negativo, probabilità del modello): guadagnano solo nel 2026, perdono
2022–25, placebo non significativo; aggiunte a v2 peggiorano. Peso di regime su v2 (short ×1,5 / long ×0,67 sotto W40): 0,97× v2.
**Lezione 30**: gli short utili esistono già in v2 (sflow/sfund sotto W-SMA40); short aggiuntivi e modelli di direzione non battono
il caso; il punto debole di v2 è il 2021 (soli long, senza ls_z), non la mancanza di short. Prossimo: peso continuo su pf14z,
size short ridotta quando il prezzo è molto sotto W-SMA40 (rimbalzi), sostituto di ls_z disponibile dal 2020.

### Giorno 31/10 · ricerca r1 — volatilità realizzata come peso e seconda gamba trend · NON PROMUOVERE (v2 resta il campione)
- **A, volatilità** (7 varianti preregistrate, vol30 e ATR% su mediana 365 g): tutte peggiorano v2 (migliore +211% vs +226%,
  placebo p 0,68, walk-forward sceglie v2). Diagnostica: i trade deboli sono in BASSA volatilità (R +0,02, WR 70%), non in alta.
- **B, seconda gamba**: W-SMA40 long/flat spot (corr 0,14) in portafoglio 70/30: +248% vs v2 +252% (stesso bootstrap a blocchi),
  MAR 18,5 vs 17,3, ma 2026 +31% vs +53%, placebo p 0,10, walk-forward e vicini non passano; 50/50 non fattibile (coda).
  Compressione→breakout solo long sul 4h: −0,5%, inutile.
- **Lezione 28**: lo stop di H2 è già in ATR, quindi un peso di volatilità conta due volte il rischio. **Lezione 29**: la gamba trend
  abbassa il DD ma non aumenta il rendimento al limite della coda in modo significativo. Nota di metodo: confrontare sempre con
  lo stesso bootstrap (a blocchi sull'equity è più permissivo di quello per trade).
- Prossimo: gamba trend a volatilità costante (rende fattibile il 50/50); peso invertito sulla bassa volatilità (preregistrato).

### Notte · ora 06:47 — rischio dinamico in funzione del drawdown del conto (v2) · NON PROMUOVERE
Preregistrato, 9 varianti (gradini −6/8/10% → ×0,7, −12/14% → ×0,5; continua ×max(0,5; 1−DD/0,20); anti-martingala ×1,2 a nuovo
massimo). Migliore C20 continua: +262% vs v2 +226% (1,16×), DD 15,0%, P(DD>20%) 11,5%, slippage 0,2% +158% vs +140%;
ma 2022–23 peggiore di v2 (+29 vs +34), walk-forward sceglie ogni volta una regola diversa, e la "f casuale" (stessi moltiplicatori
in ordine casuale) arriva al 90° percentile → non significativo.
**Lezione 27**: ridurre la size nel drawdown non aumenta il rendimento a parità di rischio; permette solo di alzare il rischio base
(il limite diventa il DD storico, non la coda). Paracadute, non strumento (conferma giro 7 e giro 10 L).
Prossimo: calibrare con DD storico fino a 20% (limite dell'utente) e usare la volatilità realizzata 30 g (anticipatrice) invece del DD.

### Notte · ora 05:47 — 12 indicatori tecnici come peso della size di v2 · NON PROMUOVERE (v2 resta il campione)
Preregistrato (terzili a finestra espansiva, × 1,3 / × 0,7, direzione favorevole scelta a priori, Bonferroni p ≤ 0,004):
RSI 4h/1d, MACD 4h, ADX 1d, larghezza Bollinger 1d, %B 4h, Stocastico 4h, MFI 4h, CMF 4h, pendenza OBV 4h, SuperTrend 1d,
distanza VWAP settimanale. Nessuno batte v2 in modo significativo: migliore SuperTrend 1d contrario +231,9% vs +226% (placebo
p 0,48); tutti i p tra 0,41 e 0,77; walk-forward incoerente.
**Lezione 26**: gli indicatori classici non aggiungono nulla al delta taker della barra di conferma, neanche come peso. Diagnostica
(da preregistrare, non usare): barre di conferma ipercomprate (RSI/%B 4h estremi) rendono meno — forma a U rovesciata.

### Notte · ora 03:47 — supporti e resistenze multi-timeframe su v2 · NON PROMUOVERE (v2 resta il campione)
Preregistrato, 20 combinazioni: pivot settimanali, swing giornalieri (frattali 5 g, 60 g), livelli tondi 5.000 $; uso peso
(× 0,6/0,8 con livello avverso entro 0,5/1 ATR, bonus × 1,2 con livello dietro) e uso target (TP al livello se < 1R).
Tutte sotto v2: migliore A-PS m0,8 d0,5 +207,5% vs v2 +226% a r_boot; placebo moltiplicatori permutati p 0,65; il walk-forward
sceglie v2 in entrambe le finestre. TP al livello: WR fino a 82,9% ma rendimento +51/+75%.
**Lezione 25**: su H2/v2 la vicinanza a supporti/resistenze statici non contiene informazione (la conferma di breakout 4h
tende a superare la resistenza vicina); un pivot settimanale appena dietro l'ingresso è semmai negativo (WR 69,7% vs 83,3%).
Conferma 6 e 18: anticipare il TP alza il WR e distrugge il rendimento.

### Risolto (notte 04:47): latenza del modulo su carta
- **Candele intraday**: paper.update usa candles_4h(live=True), che accoda alle candele di data/spot_1h.csv le ore CHIUSE del
  giorno in corso (paper.hours_after, data-api.binance.vision klines 1h, close time già passato); una barra 4h di oggi si usa
  solo se ha 4 ore chiuse. Errore di rete -> soli dati salvati. data/spot_1h.csv, backtest e storico di riferimento invariati
  (candles_4h() senza argomenti). taker_1h includeva già le ore chiuse di oggi per lo spot (fetch_taker_1h esclude solo l'ora
  in corso). I segnali restano quelli della chiusura giornaliera: la conferma 4h del giorno dopo ora si vede entro ~1 ora
  (workflow orario) invece che fino a ~24 ore dopo. Prova dal vivo alle 03:49 UTC del 31/10: lette le ore 00–02 di oggi,
  barra 00:00 ancora incompleta e quindi esclusa (ultima barra usata 30/10 20:00).
- **Rischio v2 congelato**: per ogni trade v2 dal vivo (dal 31/10/2026) rischio, DT, sotto SMA40w, perp e barra di conferma
  si salvano in data/paper.json -> v2.risk_frozen ("AAAA-MM-GG lato") al primo calcolo (stato "ingresso" o trade aperto) e
  si riusano ai giri successivi (paper.frozen_risk); lo storico dal 2022 resta ricalcolato. Json e dashboard compatibili
  (solo una chiave in più). Test: numeri storici H2/v2 invariati, rischio congelato con DT cambiato (sintetico e su
  simulazione 2026), candele intraday con ore finte e rete assente.

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

