# Preregistrazione · "effetti dei market maker": assorbimento e compressione → rottura (BTC, 1h/4h) · 18/11/2026

Scritta PRIMA di eseguire qualsiasi script e di guardare qualsiasi risultato. Va committata da sola prima della fase 2.
Regole, parametri, vicini e soglie non si cambiano dopo. Solo BTC (gli altri asset solo come verifica informativa, sezione 8).

## 1. Ipotesi dell'utente (post di un trader) e cosa c'è di nuovo
I market maker comprimono il prezzo in range stretti (2–3%) assorbendo gli ordini aggressivi; la rottura del range prosegue con
forza verso le liquidazioni. Già bocciato e NON ripetuto qui: compressione Bollinger + rottura Donchian su 4h (intraday2 A4/A5),
Donchian/breakout swing di 2–3 giorni su giornaliero (lezione 95), S/R e volume profile (68, 75–77), liquidazioni stimate come
calamita o squilibrio come segnale d'ingresso (72, 81, 92, 93). Nuovo: (a) la barra di "assorbimento" (volume alto, range basso)
con il lato letto dal delta taker spot+perp orario e dalla variazione di OI; (b) compressione oraria filtrata da assorbimento e
mappa delle liquidazioni insieme; (c) le stesse regole solo nel verso del regime W3 e a W3 flat.
Aspettativa a priori bassa: su 1h/4h a mano nulla ha retto i costi (lezioni 78, 82, 95); i costi qui valgono ~0,26% andata e
ritorno, cioè 0,1–0,25R con range dell'1–3%.

## 2. Dati e convenzioni (nessun look-ahead)
- Prezzo ed esecuzione: candele 1h perp Binance BTCUSDT (archivio, `research/liq_fasce/lf_data.hourly`, cache
  /tmp/radar-work/liqsqueeze/h.pkl; estesa con `--refresh` fino all'ultima ora chiusa; le ore finali coperte solo da spot Binance
  vanno marcate). Le candele 4h si costruiscono dalle 1h (00, 04, … 20 UTC), usate solo a 4h chiusa.
- Volume e delta taker: data/taker_1h.csv (spot e perp Binance, dal 2022-01-01). delta = 2·taker − volume (spot e perp separati);
  D = (delta_spot + delta_perp) / (vol_spot + vol_perp). Volume totale = vol_spot + vol_perp (BTC).
- OI orario: oi_usd di h.pkl (ultimo valore dentro l'ora, noto alla chiusura); OI in BTC = oi_usd / close; ΔOI della barra =
  variazione dell'OI in BTC fra la chiusura della barra precedente e quella della barra (a 4h: sulle 4 ore).
- Mappa delle liquidazioni STIMATA (solo Binance USDT-M, `radar/liqmap.build` sulle 504 ore prima di T): cache
  /tmp/radar-work/liqsqueeze/hmaps.pkl, estesa con research/liq_squeeze/sq_data.py. Fascia densa = cluster con rel ≥ 0,30.
  Squilibrio I = (S6 − L6) / (S6 + L6) (short sopra e long sotto entro ±6%). Se la mappa non si estende oltre il 13/11/2026 la
  fine del campione per le regole che la usano è l'ultima ora disponibile (dichiarata).
- Funding reale a 8h (research/intraday2/data/BTCUSDT_funding.csv.gz; dove manca, data/funding.csv giornaliero / 3), pagato o
  incassato a 00/08/16 UTC se la posizione è aperta in quell'istante.
- Decisione alla chiusura dell'ora t, ingresso all'apertura dell'ora t+1. Costi su OGNI riempimento (ingresso, stop, target,
  tempo): commissione 0,08% + slippage 0,05% = 0,13% per lato. Se nella stessa ora si toccano stop e target vale lo stop; nell'ora
  d'ingresso si controlla prima lo stop. Se l'apertura d'ingresso è già oltre lo stop o oltre il target: nessun trade.
- Percentili "su 30 giorni": rango della barra rispetto alle 720 barre 1h (180 barre 4h) PRECEDENTI, barra esclusa.
- ATR_d = media a 14 giorni del true range giornaliero (giorni UTC chiusi prima di t, dalle 1h).
- Capitale 10.000 $, 1x (nozionale = 100% dell'equity all'ingresso), una posizione alla volta per regola, long e short in perp.
  DD = massimo drawdown sul mark-to-market giornaliero (chiusura UTC). MAR = rendimento totale % / |DD| %.
- Periodi: IS 2022-02-01 → 2023-12-31 (1h), OOS 2024-01-01 → 2026-11-17 (o ultima ora disponibile). Tabella principale da
  10.000 $ al 01/01/2021 come da metodo: le regole restano in liquidità finché i dati non ci sono (2022-02-01); W3 e buy & hold
  dal 01/01/2021 e, per confronto equo, anche ribasati al 2022-02-01.

## 3. Uscite comuni (tutte le regole e i controlli)
- Range di riferimento [Lo, Hi], ampiezza W = Hi − Lo (definito da ogni regola). Trade solo se W / prezzo ≥ 1,0% (costi ≤ ~0,26R).
- Stop = lato opposto del range (long: Lo; short: Hi). Non si sposta.
- Target = prima fascia densa della mappa all'ora d'ingresso nel verso del trade a distanza fra 1·W e 3·W dal prezzo d'ingresso;
  se non c'è (o la mappa manca), entry ± 2·W.
- Tempo massimo 48 ore dall'ingresso (uscita all'apertura dell'ora 48).
- Sensibilità solo informative (non contano per l'accettazione né per Bonferroni): target sempre 2·W; tempo 24h e 72h.

## 4. Regole (6, in 3 famiglie; ogni regola: parametri fissati + 2 vicini → 18 configurazioni)

### Famiglia A · Assorbimento ("effort vs result")
Barra di assorbimento: volume totale ≥ 80° percentile E range (high − low)/close ≤ 30° percentile, |D| ≥ 0,10, delta spot e
delta perp dello stesso segno di D, ΔOI > 0 (posizioni nuove aperte dagli aggressori, carburante per le liquidazioni).
Lato: D > 0 = compratori aggressivi assorbiti da venditori passivi → setup SHORT; D < 0 = venditori assorbiti → setup LONG.
Zona: massimo e minimo delle ultime 12 ore fino alla barra di assorbimento compresa. Ingresso alla prima chiusura 1h oltre la
zona nel verso del setup (short: sotto Lo; long: sopra Hi) entro la finestra; una chiusura oltre il lato opposto annulla il setup.
Una nuova barra di assorbimento sostituisce il setup attivo; con una posizione aperta i setup si ignorano.
- **A1** · barre 1h, finestra 24 ore.
- **A2** · barre 4h (zona = barra + le 2 precedenti, 12 ore), finestra 48 ore; ingresso sulle chiusure 1h.
- Vicini (per A1 e A2): (a) più stretto: volume ≥ 90° e range ≤ 20° percentile; (b) più largo: |D| ≥ 0,05 e senza condizione su ΔOI.

### Famiglia B · Compressione → rottura
Box all'ora t = massimo/minimo delle N ore chiuse [t−N, t−1]; compresso se W ≤ k·ATR_d E W/prezzo ≤ 3,5%. Rottura: chiusura
dell'ora t sopra Hi (long) o sotto Lo (short) con box compresso. Dopo un trade, un nuovo segnale richiede un box che inizia dopo
l'ingresso precedente. Parametri: N = 24, k = 1,0.
- **B1** · compressione + assorbimento: nel box c'è almeno una barra di assorbimento 1h (definizione A1) il cui setup ha lo stesso
  verso della rottura. Vicini: (a) N = 48, k = 1,25; (b) N = 24, k = 0,8.
- **B2** · B1 + mappa: rottura verso il lato più carico, long solo se I ≥ +0,10, short solo se I ≤ −0,10 (mappa dell'ora
  d'ingresso). Vicini: (a) soglia 0 (basta il lato più carico); (b) soglia 0,30.

### Famiglia C · Complementare a W3
Regime W3 = regime settimanale di `radar/weekly` (long / short / neutro) dell'ultima candela settimanale chiusa (domenica UTC).
W3 flat = nessuna posizione W3 aperta in quel giorno UTC secondo `radar/weekly.simulate` (la versione che fa 10k → 78.474 $).
Trade solo nel verso del regime (in regime neutro nessun trade) e solo a W3 flat. Se W3 apre mentre un trade C è aperto, il
trade C si chiude alla stessa apertura (priorità a W3).
- **C1** · B1 con filtro W3. Vicini: quelli di B1 con lo stesso filtro.
- **C2** · A1 con filtro W3. Vicini: quelli di A1 con lo stesso filtro.
- Effetto su W3: portafoglio W3 + C sullo stesso capitale (C usa il 100% dell'equity solo quando W3 è flat), DD giornaliero,
  confronto con W3 da sola (10k → 78.474 $, DD −21,1%) dal 2021, 2021–23 e 2024→oggi.

## 5. Controlli di riferimento (non ammissibili, stesse uscite)
- **K0** · compressione → rottura senza filtri (B con N = 24, k = 1,0, nessun filtro): il "breakout semplice" dell'ipotesi.
- **K1** · rottura delle 24 ore senza compressione (box = ultime 24 ore, nessun filtro su W oltre l'1%).
- Scomposizioni solo informative: K0 + sola mappa (I ≥ 0,10); A1/B1 solo long e solo short; K0 e K1 anche dal 2021-01-22
  (non richiedono il taker spot).

## 6. Robustezza e placebo
- IS/OOS come sopra; anni singoli; senza i 5 trade migliori; long e short separati.
- Placebo (1.000 estrazioni per configurazione): ogni trade della regola viene spostato a un'ora casuale della stessa metà
  (IS/OOS; per C dentro le ore a W3 flat con regime nello stesso verso), senza sovrapposizioni, con lo stesso verso, la stessa
  distanza percentuale di stop e target e lo stesso tempo massimo; esito ricalcolato sui prezzi reali con gli stessi costi e
  funding. p = (k + 1) / 1.001, k = estrazioni con rendimento composto ≥ quello della regola.
- Bonferroni sulle 18 configurazioni: soglia p < 0,05 / 18 = 0,0028 (in pratica k ≤ 1 su 1.000).

## 7. Criteri di accettazione (per regola, configurazione principale; ACCETTATA per carta solo se TUTTI)
1. ≥ 30 trade nell'IS e ≥ 30 nell'OOS.
2. PF ≥ 1,2 sia nell'IS sia nell'OOS (dopo costi e funding); capitale finale > 10.000 $; MAR > 0.
3. Nell'OOS media netta per trade e PF superiori sia a K0 sia a K1 (per B2 anche a B1: il filtro mappa deve aggiungere).
4. Placebo p < 0,0028.
5. Entrambi i vicini con PF > 1 sull'intero periodo e media per trade > 0 nell'OOS.
6. Senza i 5 trade migliori: capitale finale > 10.000 $.
7. Solo C1/C2: il portafoglio W3 + C batte W3 da sola in capitale finale E MAR sia nel 2021–23 sia nel 2024→oggi, con DD
   giornaliero non peggiore di oltre 2 punti. Se C ha < 30 trade per metà il verdetto è "senza potenza", non "accettata".
Una regola accettata va solo su carta; nessuna modifica a W3 senza decisione dell'utente. Nessuna regola nuova, soglia o vicino
aggiunti dopo i risultati: eventuali idee emerse vanno in una nuova preregistrazione.

## 8. Report (fase 2)
Script e output in research/mm_assorbimento/ (dati, regole, motore, run; trade per regola in CSV). README.md in italiano con
tabella dal 01/01/2021 (capitale finale, rendimento, DD giornaliero, trade, WR, PF, MAR) per A1, A2, B1, B2, C1, C2, K0, K1,
W3 (78.474 $) e buy & hold; tabella IS/OOS; vicini; placebo; senza top 5; effetto su W3; verdetto e testo della lezione.
Verifica informativa (non criterio, lezione 87) solo per le regole accettate: stessi parametri su ETH e SOL perp 1h
(research/intraday2/data), con delta solo perp e senza mappa (B2 non verificabile).
