# Multi-asset · W3.1 "solo prezzo" ed EMA200D + VIX su indice, metalli, 10 azioni e BTC — PREREGISTRAZIONE

Scritta il 22/11/2026 PRIMA di calcolare qualsiasi rendimento. In fase 1 sono stati scaricati i dati e contati gli eventi
(`count.py` → `conteggi.txt`, `conteggi.csv`): nessun capitale, CAGR, DD o win rate è stato calcolato. Da committare da solo
prima della fase 2. Motivo nuovo rispetto alle lezioni 74 e 87 (W2 + MACD su indici e altcoin: non si trasferisce): qui si
prova la versione W3.1 a rischio 10% senza flusso perp, su azioni singole e metalli (mai testati), e l'indicatore fornito
dall'utente (research/ema200_vix/LOGICA.md).

## 1. Dati (gratuiti, pubblici; in data/, CSV gzip; script fetch.py)
| Serie | Fonte | Da | Note |
|---|---|---|---|
| S&P 500 `^GSPC` | Yahoo chart API pubblica | 1927-12-30 | indice di prezzo (senza dividendi); OHLC veri solo dal 1962 (prima solo chiusure: stop valutati sulle chiusure) |
| S&P 500 TR `^SP500TR` | Yahoo | 1988-01-04 | solo controllo del buy & hold con dividendi |
| Oro, argento: GLD, SLV | Yahoo (ETF, rettificati) | 2004-11-18 / 2006-04-28 | **serie usate per i metalli** (OHLC coerenti, costo di gestione già nel prezzo) |
| Oro, argento: GC=F, SI=F | Yahoo (future continuo) | 2000-08-30 | salvati ma NON usati: 2003–2011 OHLC incoerenti (441 e 243 giorni con high/low fuori da open/close, 15–27% di barre piatte) e salti di rollover |
| NVDA AAPL MSFT GOOGL AMZN META AVGO TSLA BRK-B LLY | Yahoo | IPO o primo dato (vedi conteggi) | OHLC rettificati per split e dividendi (fattore adjclose/close) |
| Controllo: 24 componenti del Dow al 01/01/2000 con storia continua | Yahoo | 1962–1983 | AXP BA CAT C KO XOM GE HPQ HD HON IBM INTC IP JNJ JPM MCD MRK MMM MO PG WMT DIS RTX T (esclusi EK, GM, AT&T storica, Alcoa, DuPont: senza serie continua; MSFT già nel campione) |
| VIX | CBOE (cdn.cboe.com, storico ufficiale) | 1990-01-02 | controllo con Yahoo `^VIX`: 9 giorni su 9.289 con differenza > 0,05 |
| DVOL BTC | research/p2_nuovi/data (Deribit) | 2021-03-24 | |
| BTC giornaliero | research/p2_nuovi/data/f_repo.csv.gz (frame del tool) | 2019-09 | taglio 2026-11-15 come in p2_nuovi |

Taglio azioni/ETF/VIX: venerdì 2026-11-20. Stooq: connessione rifiutata da questo container; FRED: non raggiungibile
(errore del proxy), sostituito da Yahoo come controllo del VIX. Liquidità remunerata a 0% (prudente); dividendi: inclusi per
le azioni (serie rettificate), esclusi per l'S&P 500 sia nella strategia sia nel buy & hold (confronto alla pari; con
`^SP500TR` si riporta anche il buy & hold con dividendi).

## 2. Regole (parametri fissi, identici su tutti gli asset, nessuna ottimizzazione per asset) — 8 varianti
- **V1 · S1 "W3.1 solo prezzo", long e short** (`ma_lib.s1_sim`): candele settimanali W-FRI (BTC: W-SUN come W3.1). Regime long:
  chiusura > SMA40 e EMA20 in salita; short: chiusura < SMA40, SMA40 in calo su 4 settimane, EMA20 in calo. Ingresso: chiusura dal lato
  giusto della EMA21; filtro MACD(8,21,5) > segnale e > 0 per i long se la chiusura è sopra la SMA40 da ≥ 16 settimane. Decisione
  all'ultima seduta della settimana, esecuzione all'apertura della seduta successiva. Uscite: stop iniziale 2,5 ATRw dalla chiusura del
  segnale, trailing 2,5 ATRw dalla miglior chiusura giornaliera a cricchetto (controllo giornaliero; se l'apertura salta lo stop,
  riempimento all'apertura), chiusura settimanale oltre la EMA21. Nessun flusso, funding, distribuzione. Esposizione
  min(1, 0,10 / (2,5·ATRw/chiusura)) = rischio 10% allo stop iniziale, long e short.
- **V2 · S1 solo long**: V1 senza short.
- **V3 · S2 "EMA200D"**: long alla chiusura del giorno in cui close incrocia sopra la EMA200 giornaliera, uscita alla chiusura del
  crossunder; 1x, nessuno stop.
- **V4 · S3 "EMA200D + VIX"**: indicatore completo coi default (VIX 34, 60 giorni di calendario, stop spento). Interpretazione fissata
  (da verificare sul Pine se disponibile): ingresso VIX solo da flat al crossover della chiusura del VIX sopra 34, eseguito alla chiusura
  dell'asset dello stesso giorno (o alla prima successiva); durante un trade VIX valgono solo la regola dei 60 giorni (alla prima
  chiusura ≥ ingresso + 60 giorni: se close > EMA200 diventa trade di trend, altrimenti esce) e l'eventuale stop; a parità di giorno
  vince l'ingresso di trend. VIX per tutti gli asset (stessi parametri, anche metalli e azioni).
- **V5 · S3 con DVOL (solo BTC)**: soglia equivalente fissata prima: percentile del VIX 34 nello storico VIX 1990–2020 = 95,11% →
  quantile 95,11% dello storico DVOL disponibile (2021-03-24 → 2026-11-17) = **93,9** (vicini: VIX 30 → 91,46% → 89,6; VIX 38 →
  96,84% → 98,3). Il DVOL usa la sua storia intera: piccolo look-ahead nella soglia, dichiarato.
- **V6 · W3.1 + ingressi "panic" VIX (BTC)**: W3.1 invariata (p2_engine); quando W3.1 è flat e senza ingresso in sospeso, un
  crossover VIX > 34 apre un long BTC alla chiusura con l'esposizione di W3.1 (rischio 10% a 2,5 ATRw); uscita con le regole S3
  oppure all'apertura del lunedì in cui W3.1 entra (W3.1 ha la precedenza).
- **V7 · come V6 con DVOL 93,9.**
- **V8 · W3.1 filtrata da EMA200D (BTC)**: ingresso long solo se close > EMA200D alla domenica di decisione, short solo se sotto.

Esecuzione dei costi: azioni, ETF, indice 0,05% per lato (commissione + slippage, come indicato dall'utente); short: 3% annuo sul
nozionale (stima dichiarata, maturato per giorno di calendario). BTC: costi di W3.1 (spot 0,1% + slippage 0,1%; perp 0,05% +
slippage, funding reale) per S1 e V6–V8; S2/S3 su BTC in spot (0,1% + 0,1% per lato). Leva 1x ovunque.

## 3. Periodi
- Test da: primo dato + 1 anno (riscaldamento); S3 non prima del 1991-01-01 (VIX dal 1990).
- Sottoperiodi del criterio (simulazioni indipendenti, si parte flat con 10.000 $): **A 2000–2010, B 2011–2020, C 2021–2026-11-20**.
  Un sottoperiodo conta solo con ≥ 3 anni testabili (META, AVGO, TSLA: solo B e C).
- BTC: dal 2021-01-01 al 2026-11-15; sottoperiodi A 2021–22, B 2023–24, C 2025–oggi. Descrittivo: BTC 2018–20 (f_long) per V6.
- Descrittivi: decenni (S&P 500 dagli anni '30), dal 2021, periodo intero.

## 4. Metriche e confronti
Capitale finale da 10.000 $, rendimento, CAGR, max DD giornaliero (mark-to-market), CAGR/DD, trade, WR, tempo in posizione,
perdita media allo stop; posizione aperta chiusa all'ultima chiusura. Confronto: buy & hold dello stesso asset nello stesso periodo
(una commissione d'ingresso), W3.1 su BTC (riferimento 2021+: 13 trade).

## 5. Robustezza (tutto riportato, nessuna scelta a posteriori)
- **Placebo**: 20.000 estrazioni per configurazione sul periodo intero: stessi trade (durata in sedute, lato, esposizione) in ordine
  casuale con intervalli flat ripartiti a caso (stessa esposizione e stesso tempo in posizione), rendimenti chiusura→chiusura con gli
  stessi costi; la statistica reale si ricalcola nella stessa rappresentazione. p = (1 + #placebo con CAGR/DD ≥ reale)/(N + 1).
  V8: placebo = blocco casuale dello stesso numero di ingressi W3.1.
- **Vicini**: S1 k = 2,0 / 3,0 ATRw; S2 EMA 150 / 250; S3 EMA 150 / 250, VIX 30 / 38 (DVOL 89,6 / 98,3), orizzonte 40 / 80.
- **Esecuzione realistica** di S2/S3 all'apertura del giorno dopo (alla chiusura il VIX delle 16:15 ET è noto 15 minuti dopo la chiusura
  delle azioni: look-ahead di 15 minuti nella versione "alla chiusura" dell'indicatore).
- **Costi doppi**: 0,15% per lato; **senza il trade migliore**.
- **Correzione per test multipli** (Bonferroni sul totale delle configurazioni eseguite): principali 13 × 4 + BTC 7 (V1–V7; V8 esclusa,
  vedi §7) = 59; vicini 13 × 12 + BTC 18 = 174; esecuzione all'apertura 13 × 2 + 3 = 29; costi doppi 57; controllo Dow 24 × 4 = 96.
  **M = 415, soglia p < 0,05/415 = 0,00012** (20.000 estrazioni: p minimo 0,00005).
- **Bias di selezione**: le 10 azioni sono i vincitori di oggi (scelte ex post): il loro buy & hold è eccezionale per costruzione e
  una strategia di trend vi trova trend lunghi per costruzione. Si riportano a parte l'indice (S&P 500) e il controllo sui 24
  componenti del Dow al 2000 (ancora sopravvissuti: bias di sopravvivenza residuo dichiarato).

## 6. Criteri di accettazione (fissati ora)
- Una regola **"funziona" su un asset** se: CAGR/DD > buy & hold in almeno 2 dei sottoperiodi disponibili (con 2 sottoperiodi: entrambi)
  **e** placebo p < 0,00012 sul periodo intero **e** ≥ 10 trade sul periodo intero.
- **"Robusta"** (etichetta aggiuntiva): inoltre almeno 2/3 dei vicini, l'esecuzione all'apertura, i costi doppi e la versione senza
  il trade migliore battono il buy & hold in CAGR/DD sul periodo intero.
- **"W3.1 è generale"** solo se V1 funziona su almeno 7 dei 13 asset non-BTC; controllo: la quota di componenti Dow 2000 che passano
  il criterio dei sottoperiodi deve essere simile (entro 20 punti) a quella delle 10 azioni scelte, altrimenti il risultato è attribuito
  alla selezione.
- **BTC**: V1–V5 come sopra contro il buy & hold di BTC (sottoperiodi BTC) e riportate contro W3.1. V6–V8 si accettano solo se
  CAGR/DD > W3.1 in ≥ 2 dei 3 sottoperiodi BTC e sul 2021+, con ≥ 5 eventi aggiunti/modificati e placebo p < 0,00012.
- Nessun cambiamento a W3.1 da questa ricerca senza approvazione esplicita dell'utente.

## 7. Conteggio degli eventi (fase 1, senza rendimenti; dettagli in conteggi.txt)
| Asset | test da | V1 S1 L/S | V2 S1 long | V3 S2 | V4 S3 (di cui VIX) |
|---|---|---|---|---|---|
| S&P 500 | 1928-12 | 363 | 235 | 345 | 125 (18) dal 1991 |
| GLD | 2005-11 | 95 | 65 | 79 | 79 (2) |
| SLV | 2007-04 | 94 | 60 | 106 | 107 (9) |
| NVDA | 2000-01 | 90 | 59 | 86 | 95 (13) |
| AAPL | 1981-12 | 158 | 104 | 170 | 134 (12) |
| MSFT | 1987-03 | 152 | 108 | 164 | 136 (16) |
| GOOGL | 2005-08 | 77 | 60 | 86 | 87 (8) |
| AMZN | 1998-05 | 115 | 80 | 128 | 124 (12) |
| META | 2013-05 | 40 | 30 | 41 | 42 (6) |
| AVGO | 2010-08 | 68 | 55 | 75 | 67 (9) |
| TSLA | 2011-06 | 79 | 55 | 99 | 93 (6) |
| BRK-B | 1997-05 | 115 | 82 | 133 | 125 (13) |
| LLY | 1973-06 | 231 | 149 | 233 | 153 (13) |
| Dow 2000 (24) | 1963–1984 | 173–306 | 114–203 | 196–407 | 133–223 |

BTC 2021-01 → 2026-11-15: W3.1 13 trade (5/5/5 nei sottoperiodi); V1 15; V2 12; V3 35; V4 30 (5 VIX); V5 38 (3 DVOL).
Incroci grezzi VIX > 34: 61 dal 1991, 7 dal 2021; DVOL > 93,9: 20 dal 2021.
**V6: 4 ingressi panic** (2021-01-27, 2022-05-09, 2024-08-05, 2025-04-04; 3 interrotti da un ingresso W3.1); vicini 2–5.
**V7: 2 ingressi** (2021-04-24, 2022-05-11); vicini 2–4. **V8: 0 domeniche bloccate** dal 2021 (il regime SMA40 di W3.1 è sempre
già dal lato della EMA200D agli ingressi): V8 coincide con W3.1 e non si esegue. Conseguenza fissata ora: V6 e V7 hanno meno di 5
eventi, quindi **non sono valutabili** statisticamente; in fase 2 si riportano solo in forma descrittiva (trade per trade).
