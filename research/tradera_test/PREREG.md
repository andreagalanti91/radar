# tradera_test · PREREG — backtest del rilevatore "linea + rottura + ritest" di TraderA (23/11/2026)

Scritto e committato DA SOLO dopo la fase 1 (replica: `tt_detect.py`, `tt_replica.py`, `replica.txt`, `fetch.py`) e PRIMA di
calcolare qualsiasi rendimento, R o equity del rilevatore. Nessun backtest è stato eseguito finora.

## Fase 1 (già fatta, dichiarata)
Parametri calibrati su 3 esempi (LMT, NVDA, BTC): rischio di adattamento dichiarato. Su LMT 72 combinazioni su 162 riproducono
linea, ingresso, stop e obiettivo entro l'1%; la riproduzione dipende da TOL ≤ 0,5 ATR e BASE ≤ 3 (con TOL 1 o BASE 5 no).
INV è passato da 0,5 a 1,0 e le zone da ZK 4/ZW 6% a ZK 3/ZW 10% guardando gli esempi.

## Parametri congelati (tt_detect.P)
PIV 10 · WIN 250 · GAP 20 · EXP 250 · MOM 1,5 ATR · TOL 0,5 ATR · INV 1,0 ATR · K 40 barre · CF 1,0 ATR · BASE 3 · MARG 0,1% ·
RRMIN 2,0 · zone ZK 3, ZW 10%, ZN 2. ATR 14 (Wilder), EMA 12/26/50/200 sulle chiusure. Gli stessi su tutti gli asset; per il 4h di
BTC gli stessi valori in barre.

## Universo e dati
- Azioni (primario): le 20 azioni U2 di research/trend_multi/ADDENDUM.md (Dow Jones al 01/01/2000 con perpetuo OKX/Bitget oggi:
  BA CAT C GE HD HPQ IBM INTC JNJ JPM KO MCD MO MRK MSFT PG RTX T WMT XOM), OHLC Yahoo rettificati (cache di multi_asset).
- LMT e NVDA: casi di esempio dichiarati (usati per calibrare), riportati a parte e in un portafoglio "U2 + esempi" descrittivo.
- Crypto: BTCUSDT ed ETHUSDT giornalieri Binance (data-api.binance.vision, dal 17/08/2017); BTC 4h (research/ema_sma/data) come
  robustezza.
- Periodi (segnali con data in): azioni 2016-01-01 → 2020-12-31 e 2021-01-01 → 2026-11-20; crypto 2018-01-01 → 2020-12-31 e
  2021-01-01 → 2026-11-22. Il rilevatore gira su tutta la storia (riscaldamento), si contano solo i segnali nel periodo; un
  trade aperto a fine periodo si chiude al valore di chiusura dell'ultimo giorno del periodo. Ogni periodo riparte da 10.000 $.

## Esecuzione
- Segnale alla chiusura t, ingresso all'apertura t+1; niente ingresso se l'apertura è già oltre lo stop o oltre l'obiettivo.
- Stop e obiettivo come ordini da t+1 compreso: stop eseguito a min(apertura, stop) (long; speculare short), obiettivo a
  max(apertura, obiettivo); se nella stessa barra si toccano entrambi conta lo stop. Nessuna gestione attiva, nessuna uscita a
  tempo. Una posizione per asset alla volta (i segnali durante un trade aperto si ignorano).
- Costi: 0,10% per lato (commissione + slippage). Azioni come perpetui: funding long 5% annuo sul nozionale (sensibilità 0% e
  10%), short 1% annuo. Crypto: long spot senza funding, short perp senza funding (ipotesi dichiarata: in media gli short
  incassano, quindi prudente). Liquidità non remunerata. Nessuna leva (Σ nozionale ≤ capitale).
- Dimensione: (a) **rischio fisso 2%** del capitale del portafoglio allo stop (nozionale = 2% / distanza dello stop, tetto 1x
  del capitale e capitale libero); (b) **capitale pieno**: ogni asset 1x sul suo capitale; portafoglio = quote uguali per asset
  (1/N), non ribilanciato.
- R di un trade = rendimento netto per unità di nozionale / distanza dello stop all'ingresso.

## Candidate (4) e varianti descrittive
- **V1 base**: tutti i segnali ritest con R:R ≥ 2, long e short.
- **V2 completo (d)**: V1 + confluenza (EMA50 o EMA200 entro 1 ATR dalla linea al ritest).
- **V3 V2 + forza relativa (h)**: long solo se la media dei ranghi percentili dei rendimenti a 21 e 63 giorni nell'universo
  (azioni U2 fra loro; BTC ed ETH fra loro) è ≥ 0,5; short solo se ≤ 0,5.
- **V4 V2 + piano speculare (g)**: aggiunge gli ingressi del piano speculare (tt_detect: chiusura oltre linea − INV·ATR dopo lo
  slancio; stop oltre l'estremo delle ultime 3 barre; obiettivo la base della rottura; R:R ≥ 2).
- Descrittive: solo long / solo short di V1 e V2; con/senza confluenza (V1 vs V2) e con/senza forza relativa (V2 vs V3) mostrate
  come differenza di R medio con intervallo bootstrap; BTC 4h (V1, V2); funding 0/10%; vicini (PIV 5/15, MOM 1/2, TOL 0,25,
  INV 0,5, BASE 2, CF 0,5/2, RRMIN 1,5/3) su V2.
- Soglia: Bonferroni su 4 candidate (+ 2 W3.2) → p < 0,05/6 = 0,0083.

## Riferimenti
- Buy & hold equipesato dello stesso universo (azioni con funding 5% sul nozionale, come trend_multi; crypto spot).
- **Placebo**: per ogni trade reale un ingresso in un giorno casuale dello stesso asset, stesso periodo, stesso lato e stesso
  regime (chiusura sopra/sotto l'EMA200 come al segnale), con le stesse distanze in % di stop e obiettivo e le stesse regole
  di uscita; 1.000 estrazioni; p = quota di placebo con R medio ≥ quello reale. Seed 20261123.
- **Regola "flip" (lezione 114) generalizzata**: livelli = pivot settimanali (k 3) noti dalla conferma; chiusura sotto il
  livello più vicino sotto la chiusura precedente → short, stop livello + 1 ATR, obiettivo il livello successivo sotto (se
  manca, nessun trade); long speculare. Stesse esecuzioni e costi.
- W3.2 (radar.weekly, dati congelati di research/p2_nuovi per BTC; ETH da radar.data come in forza_giornaliera).

## Criteri (per mercato: azioni U2 e crypto BTC+ETH, separati; per candidata)
1. R medio > 0 dopo i costi in ENTRAMBI i periodi;
2. R medio maggiore del placebo in entrambi i periodi e p (periodi uniti) < 0,0083;
3. togliendo i 3 trade migliori la somma degli R resta > 0;
4. almeno 30 trade per periodo; altrimenti il verdetto è "non dimostrabile".
"Funziona" = 1–4 veri. "Non funziona" = criterio 1 o 2 falso con almeno 30 trade per periodo. Altrimenti "non dimostrabile".
Verdetto riportato anche per lato (long/short) con gli stessi criteri (descrittivo).

## Dentro W3.2 (solo BTC ed ETH, 2 varianti fissate ora)
- **WV1 ingresso al ritest con confluenza**: dopo il segnale W3.2 (domenica) limite sul supporto (long) = il più alto fra EMA50,
  EMA200 giornaliere e la linea rotta più recente del rilevatore (se la rottura è entro K barre) che sta sotto la chiusura ed
  entro 2 ATR giornalieri; resistenza speculare per gli short; valido 5 giorni, poi a mercato (motore di
  research/forza_giornaliera, opzione "level"). Nessun livello → come W3.2.
- **WV2 metà all'obiettivo di struttura**: metà della posizione al massimo (minimo) delle 250 barre giornaliere prima del
  segnale se dista almeno il 5% dall'ingresso; il resto segue W3.2 (copia del motore di research/tp_rientro con il livello in
  prezzo).
- "Migliora" solo se CAGR/DD > W3.2 sia nel 2021–23 sia nel 2024–26 (ripartendo da 10.000 $) e, per BTC, CAGR/DD 2018–20 non
  peggiore. ETH: 2019-09 → 2020 come 2018–20 (dati disponibili), solo descrittivo.

## Uscite
replica.txt (fase 1), risultati.txt, trade.csv, varianti.csv, README.md con verdetto, divergenze, setup di oggi e procedura di
confronto in avanti (confronto.py, confronto.csv). Nessuna modifica a radar/ o tests/.
