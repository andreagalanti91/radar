# Preregistrazione · Parte 2: opzioni, dimensione della posizione, rotazione crypto, piramidazione (BTC settimanale) · 18/11/2026

Scritta PRIMA di qualsiasi backtest delle regole: in fase 1 sono stati solo scaricati i dati e CONTATI gli eventi (lezione 98;
`p2_count.py` stampa solo conteggi, nessun capitale, rendimento, DD o esito di trade). Va committata da sola prima della fase 2.
Regole, parametri, vicini, soglie e regola di scelta non si cambiano dopo. Solo BTC: gli altri asset non sono un criterio (87).

## 1. Cosa c'è già nel diario (non ripetuto) e cosa è nuovo
- Volatilità come peso: provata su v2 (r1, lezioni 28–29: peggiora) e su W2 all'ingresso (01/11, "B, size a rischio": il vol
  targeting taglia i grandi trend, Δ −1,0/−1,2 MAR a pari DD; lezione 60). Nuovo qui: ribilanciamento SETTIMANALE su W3.
- Rischio allo stop: W3 usa già il tetto 25% (R_LONG/R_SHORT, lezioni 83, 85); quota di capitale 50–100% (01/11, tabella):
  il DD scala con la quota. Nuovo: griglia rischio × distanza dello stop × presa parziale con regola di scelta preregistrata
  (delega dell'utente: "decidi tu stop, TP e capitale investito").
- Uscite parziali: lezione 73 (C "metà a +30%" e B′ non reggono fuori campione: tagliano le code destre). Qui SOLO controllo.
- Kelly: mai provato. Con esposizione massima 1x il Kelly continuo su W3 satura a 1x; si riporta solo come informazione (sezione 4, F2).
- Piramidazione: provata su W2 il 31/10 (0,5x/0,75x → 1x alla rottura del massimo a 26 settimane: vince 2021–26, perde nel
  2018–20, lezione 49; filtro "rottura non estesa": 1 aumento su 8, lezione 50). Nuovo: aggiunte a +1/+2 ATRw dalla chiusura
  del segnale, su W3 (tetto 25%, cricchetto), anche sugli short, stop comune. Aspettativa a priori bassa.
- S&P 500, Nasdaq, dollaro, VIX come filtri: censimento 11/11 (lezione 86), nessun effetto; indici come asset: lezione 74.
  Oro: mai testato (rimandato al 2027 per mancanza di dati affidabili). Non fanno parte di questo ciclo.
- DVOL, skew/put-call delle opzioni, ETH/BTC, dominanza BTC: mai testati nel diario.

## 2. Dati (scaricati in fase 1, gratuiti e leciti, API pubbliche documentate; `fetch.py`)
- `data/dvol_btc_1d.csv`: DVOL BTC giornaliero, Deribit `public/get_volatility_index_data` (www.deribit.com). Esiste dal
  24/03/2021: 2018–20 NON testabile per le regole DVOL. Valore usato alla decisione della domenica = chiusura della candela
  giornaliera della domenica (00:00 del lunedì UTC, cioè l'istante della decisione W3; il DVOL è in tempo reale).
- `data/deribit_opt_sunday.csv`: tutte le opzioni BTC scambiate su Deribit nelle 24 ore della domenica UTC (archivio ufficiale
  history.deribit.com, `public/get_last_trades_by_currency_and_time`), dal 06/01/2019, aggregate per domenica: volumi put/call
  (BTC), volumi in acquisto del taker, IV media ponderata per volume delle put OTM (strike/indice 0,80–0,95), delle call OTM
  (1,05–1,20) e ATM (0,97–1,03), scadenze 7–45 giorni. Non esiste uno storico gratuito di skew 25-delta o put/call ufficiale:
  questo è un proxy costruito dai trade (dichiarato). Valido solo se volume ≥ 10 BTC su entrambe le ali (sennò NaN = nessun
  blocco). 2019: ~700 trade per domenica (sottile), dal 2021 ~5.000–13.000.
- `data/ethbtc_1d.csv`: ETHBTC spot Binance giornaliero (data-api.binance.vision), dal 14/07/2017.
- `data/btcdom_1d.csv`: BTCDOMUSDT perp Binance (indice di dominanza Binance, archivio data.binance.vision), dal 21/06/2021.
  Non è la dominanza di capitalizzazione (quella storica gratuita non è disponibile senza chiave); 2018–20 NON testabile.
  Correlazione delle variazioni settimanali log ETHBTC/BTCDOM: −0,88 (le due misure sono quasi la stessa informazione).
- Frame giornalieri congelati (`p2_data.py`): `f_repo.csv.gz` (feature del tool, 2019-09 → 15/11/2026) e `f_long.csv.gz`
  (2014 → , flusso proxy CVD spot prima del 2019-09, come nei cicli precedenti) per il 2018–20.
- Fine del campione: domenica 15/11/2026 (ultima candela settimanale chiusa; W3 flat). W3 invariata su questi dati:
  10.000 $ → 78.474 $, DD −21,1%, 13 trade, WR 92,3% (riprodotta; `p2_engine.py` = radar.weekly.simulate al centesimo).

## 3. Convenzioni comuni
- Motore `p2_engine.py` (copia di W3 con agganci; ad agganci spenti identico a radar.weekly). Stessi segnali, decisione della
  domenica, esecuzione all'apertura del lunedì, costi di W3 (spot 0,1%/lato, perp 0,05%/lato, slippage 0,1%, funding reale);
  ribilanciamenti, aggiunte e prese parziali pagano commissione e slippage sulla quantità scambiata. Esposizione massima 1x.
- Filtri sugli ingressi: se il filtro blocca, W3 non entra quella domenica e può entrare la domenica dopo se il segnale resta.
- Periodi: tutto dal 01/01/2021 (10.000 $); IS 2021-01-01 → 2023-12-31 e OOS 2024-01-01 → 2026-11-15, ciascuno ripartito da
  10.000 $; 2018-01-01 → 2020-12-31 su `f_long` dove i dati esterni esistono.
- Metriche: capitale finale, rendimento, DD massimo giornaliero (mark-to-market), trade, WR, MAR del progetto (rendimento
  totale % / |DD| %), CAGR/DD (CAGR % / |DD| %), peggior trade, esposizione media. Confronto con W3 invariata e buy & hold
  (spot, costi inclusi).
- Rischio di rovina (F2 e F4): bootstrap a blocchi dei rendimenti giornalieri della variante (blocchi di 60 giorni, 10.000
  percorsi di 6 anni): P(DD ≥ 30%), P(DD ≥ 50%), P(capitale < 50% dell'iniziale).
- Senza il trade migliore: si toglie il trade con il P&L più alto della variante (rendimento di quel trade sostituito da 0).

## 4. Regole (8 in 4 famiglie; parametri fissati + vicini)

### F1 · Opzioni
- **O1 · premio della volatilità implicita come filtro di W3.** VRP = DVOL / (vol realizzata 30 g annualizzata × 100), vol
  realizzata = deviazione standard dei rendimenti log giornalieri degli ultimi 30 giorni × √365. Ogni nuovo ingresso W3 (long e
  short) è bloccato se VRP > 1,2 alla domenica del segnale (il mercato prezza un rischio che l'ATR, che guarda indietro, non vede).
  Vicini: 1,1 e 1,4. Prima del 2021-04 nessun blocco. La definizione iniziale (DVOL z-score a 180 g > 1,5) è stata SCARTATA prima
  dei risultati perché quasi non produce eventi (tabella 5): gli ingressi W3 avvengono quasi sempre con DVOL normale o basso.
- **O2 · segnale autonomo "picco di DVOL rientrato" (solo long).** z = (DVOL − media 180 g)/dev. std 180 g (min 90 g), valore
  della domenica. Segnale: max z delle 4 domeniche precedenti ≥ 2,0 e z della domenica ≤ 1,5 (il picco si sta sgonfiando). Long
  spot 1x all'apertura del lunedì, stop iniziale 2,5 ATRw dalla chiusura del segnale con trailing W3 a cricchetto, uscita a tempo
  all'apertura del lunedì dopo la 4ª domenica. Una posizione alla volta; un nuovo segnale a posizione aperta si ignora.
  Vicini: (picco 1,5; rientro 1,0; 4 settimane) e (2,0; 1,0; 8 settimane). Anche come complemento: portafoglio W3 + O2 sullo
  stesso capitale, O2 solo quando W3 è flat (W3 ha la priorità: se W3 entra, O2 chiude alla stessa apertura).
  Potenza: dal 2021 ci sono solo 10 episodi indipendenti di DVOL z ≥ 2; nessuna definizione sensata supera ~10 trade (tabella 5).
  La prima versione (rientro ≤ 1,0, 8 settimane: 7 trade) è diventata un vicino; la principale è quella con più eventi.
- **O3 · skew delle opzioni come filtro di W3.** skew = IV put OTM − IV call OTM (punti di vol, domenica del segnale). Long W3
  bloccato se skew > 0 (protezione al ribasso più cara del rialzo), short W3 bloccato se skew < 0 (call più care). Vicini: soglia
  1 e 2 punti (long bloccato se skew > T, short se skew < −T). Definizione iniziale z a 26 settimane ≥ 1,5 SCARTATA per assenza
  di eventi. 2018–20 testabile solo dal 2019 (dati sottili).

### F2 · Dimensione della posizione (stessi segnali W3, esposizione massima 1x)
- **G · griglia rischio × stop × presa parziale.** Esposizione all'ingresso = min(1, r / (k·ATRw/close)), r = rischio allo stop
  iniziale ∈ {5, 10, 15, 20, 25%}; k = distanza di stop iniziale E trailing ∈ {2,0; 2,5; 3,0} ATRw (stesso k per entrambi); presa
  parziale ∈ {nessuna (W3); 1/3 della quantità iniziale a +2R e 1/3 a +3R con limite, resto in trailing} (R = k·ATRw del segnale;
  nel giorno in cui si toccano stop e livello vale lo stop). 5 × 3 × 2 = 30 configurazioni; r 25% / k 2,5 / nessuna = W3.
  Le 15 con presa parziale sono SOLO controllo (lezione 73): non sono eleggibili.
  **Regola di scelta (fissata ora, delega dell'utente)**: fra le 15 configurazioni senza presa parziale si sceglie quella con il
  massimo CAGR/DD (DD giornaliero) dal 01/01/2021 che rispetta TUTTI i vincoli:
  (a) DD giornaliero ≤ 15% dal 2021; (b) DD giornaliero ≤ 25% nel 2018–20; (c) perdita allo stop ≤ 15% dell'equity (r ≤ 15% e
  peggior trade realizzato ≥ −15%, gap compresi); (d) CAGR/DD nell'OOS 2024–26 (da 10.000 $) ≥ quello di W3 attuale nello
  stesso periodo; (e) tutti i vicini esistenti (±1 passo su r a k fisso, ±1 passo su k a r fisso) hanno CAGR/DD dal 2021 ≥ 80%
  di quello della configurazione. A parità entro il 5% della metrica vince il rischio più basso (poi il k più vicino a 2,5, poi il
  k più piccolo). Se nessuna configurazione rispetta i vincoli: r 10% con stop attuale (k 2,5), senza presa parziale.
  Il risultato è la PROPOSTA da presentare all'utente per il tool (nessuna modifica a radar/ in questo ciclo).
- **V · volatility targeting settimanale.** Esposizione = min(1, 50% / vol realizzata 30 g) all'ingresso, ricalcolata ogni
  domenica a trade aperto ed eseguita al lunedì se cambia di almeno 0,10; sostituisce il tetto R25; stop e uscite W3 invariati.
  Vicini: obiettivo 40% e 60%. Confronto principale: W3 scalata con una quota di liquidità allo STESSO DD giornaliero.
- **Kelly frazionato (solo informativo, non è una configurazione):** dai trade W3 2021–23, in multipli di R (R = perdita allo
  stop iniziale), r* = p − (1 − p)/b (p = quota vincenti, b = R medio vinto / R medio perso); si riporta ¼·r* e ½·r* e la
  configurazione G più vicina. Se nell'IS non ci sono perdenti o r* ≥ 1 si scrive "Kelly non stimabile / saturo".

### F3 · Rotazione crypto (filtro di regime di W3, long e short)
Ipotesi unica: i trend di BTC rendono di più quando il capitale ruota VERSO BTC (dominanza in salita).
- **R1 · ETHBTC.** Ingresso W3 (long o short) solo se la chiusura settimanale ETHBTC della domenica è sotto la sua EMA 20
  settimane. Vicini: EMA 10 e 40. Testabile 2018–20.
- **R2 · BTCDOM.** Ingresso W3 solo se BTCDOM è sopra la sua EMA 20 settimane (dal 21/06/2021 + 20 settimane; prima nessun
  blocco). Vicini: EMA 10 e 40. 2018–20 non testabile.

### F4 · Piramidazione
- **P1.** Ingresso W3 a 1/3 dell'esposizione W3 (E, con tetto 25%); +1/3·E all'apertura dopo la prima chiusura giornaliera oltre
  chiusura del segnale + 1 ATRw (long; short speculare), +1/3·E dopo la prima oltre +2 ATRw (ATRw del segnale). Stop comune:
  trailing W3 a cricchetto sull'intera posizione; uscite W3 invariate; esposizione massima E (≤ 1x). Vicini: base 1/2 con
  aggiunte 1/4 + 1/4 a +1/+2 ATRw; base 1/3 con aggiunte a +0,5/+1 ATRw.

## 5. Eventi contati in fase 1 (solo conteggi; `p2_count.py`, output in `conteggi.txt`)
Conteggi su ingressi/uscite simulati di W3 (nessun P&L guardato). "Tolti/nuovi" = trade W3 (data del segnale e lato) che
spariscono o compaiono rispetto a W3 invariata; W3 ha 7 trade nel 2021–23, 6 nel 2024–26, 9 nel 2018–20 (f_long).

| Regola (principale; vicini) | 2021–23 | 2024–26 | 2018–20 | Nota |
|---|---|---|---|---|
| O1 VRP > 1,2 (1,1; 1,4) | 18 dom. bloccate, 4 tolti/3 nuovi (5/3; 3/2) | 6 dom., 2/1 (3/2; 0/0) | n.d. | vicino 1,4 senza eventi OOS |
| O1 scartato: DVOL z180 > 1,5 (1,0; 2,0) | 0 (1/0; 0) | 1/1 (1/0; 0) | n.d. | quasi nessun evento |
| O2 picco 2,0 → 1,5, 4 sett. (1,5→1,0; 2,0→1,0 8 sett.) | 3 trade (3; 2) | 7 (7; 5) | n.d. | 10 trade: al limite di potenza |
| O3 skew > 0 / < 0 (1; 2 punti) | 7 dom., 2/0 (2/1; 1/1) | 5 dom., 3/2 (2/1; 1/1) | 7 dom., 2/1 | |
| O3 scartato: skew z26 ≥ 1,5 | 0 | 0 | 0 | nessun evento |
| R1 ETHBTC < EMA20 (10; 40) | 13 dom., 5/3 (5/3; 6/2) | 2 dom., 1/0 (1/0; 1/0) | 13 dom., 7/3 (4/0; 4/2) | OOS 1 solo trade cambiato |
| R2 BTCDOM > EMA20 (10; 40) | 4 dom., 2/2 (2/2; 1/1) | 1 dom., 1/1 (1/0; 0/0) | n.d. | ρ −0,88 con ETHBTC |
| V vol target 50% (40; 60) | 5 ingressi < 1x, 13 ribil. (17; 6) | 1 < 1x, 4 ribil. (8; 2) | 5 < 1x, 10 ribil. | |
| G 30 configurazioni | 7 trade (9 con k 2,0); con r ≤ 10% tutti sotto 1x, r 15% tutti tranne 1 | 6 trade; r ≤ 15%: tutti sotto 1x tranne 1 (k 2,0) | 9 | prese parziali 1–3 per metà, 3–5 nel 2018–20 |
| P1 1/3 + 1/3 + 1/3 a +1/+2 ATRw (base 1/2; +0,5/+1) | 7 con 1ª aggiunta, 4 con 2ª (7/4; 7/7) | 6/5 (6/5; 6/6) | 5/5 | |

Lettura: gli ingressi W3 avvengono quasi sempre con DVOL normale o basso (filtri sul livello di DVOL senza eventi); le regole
di filtro cambiano al massimo 3–8 trade su 13: tutte a bassa potenza, il verdetto atteso più probabile è "senza potenza".
R1 nell'OOS cambia 1 solo trade e R2 nel 2018–20 non esiste: criterio 1 (≥ 1 trade per metà) appena raggiunto.
Output completo: `conteggi.txt`.

## 6. Robustezza e placebo
- IS/OOS e 2018–20 come sopra; anni singoli; senza il trade migliore; vicini.
- Placebo (2.000 estrazioni, metrica CAGR/DD dal 2021; p = (k+1)/2.001):
  filtri O1, O3, R1, R2: si bloccano lo stesso numero di domeniche-segnale scelte a caso fra quelle in cui W3 avrebbe un ingresso
  (stessa metà IS/OOS); O2: stesso numero di trade a domeniche casuali della stessa metà, stesso stop e stessa durata;
  V: settimane della vol realizzata permutate a blocchi di 8 settimane; P1: aggiunte nei giorni casuali dello stesso trade, stesso
  numero di aggiunte. G: nessun placebo (scelta di dimensione sugli stessi segnali; la protezione è la regola dei vicini).
- Bonferroni sul totale delle configurazioni: O1 3 + O2 3 + O3 3 + V 3 + R1 3 + R2 3 + P1 3 + G 30 = **51** → soglia
  p < 0,05/51 = **0,00098**. Se per una regola il p minimo raggiungibile dal placebo (combinazioni distinte) è sopra la soglia,
  la regola può essere al massimo "su carta", mai proposta per il tool.

## 7. Criteri di accettazione (configurazione principale; "su carta" solo se TUTTI, "proponibile" se anche il placebo passa)
Filtri O1, O3, R1, R2 e piramide P1:
1. Potenza: almeno 3 trade W3 cambiati (tolti, aggiunti o, per P1, con aggiunte) dal 2021 e almeno 1 per metà; sennò "senza potenza".
2. Capitale finale e MAR superiori a W3 sia nel 2021–23 sia nel 2024–26; DD giornaliero non peggiore di oltre 2 punti in ciascuna.
3. 2018–20 dove i dati ci sono: MAR non inferiore a W3 (W3 2018–20 su f_long: 10.000 → 25.142 $, DD −37,3%); se non
   testabile la regola resta al massimo "su carta".
4. Entrambi i vicini con MAR dal 2021 superiore a W3.
5. Senza il trade migliore: capitale finale ≥ W3 senza il suo trade migliore.
6. Placebo p < 0,00098.
V: come sopra ma confrontata con W3 scalata allo stesso DD (criteri 2–5 a pari DD) e con P(DD ≥ 50%) non superiore a W3.
O2: ≥ 10 trade dal 2021 (sennò "senza potenza"); PF ≥ 1,2 in entrambe le metà; MAR superiore al buy & hold; placebo p < 0,00098;
portafoglio W3 + O2 superiore a W3 in capitale e MAR in entrambe le metà con DD non peggiore di oltre 2 punti.
G: regola di scelta della sezione 4 (nessun altro criterio; i controlli con presa parziale si riportano a fianco).
Nessuna regola, soglia o vicino nuovi dopo i risultati: le idee emerse vanno in una nuova preregistrazione.

## 8. Report (fase 2)
Script e output in research/p2_nuovi/. README.md in italiano: tabella dal 01/01/2021 (capitale finale, rendimento, DD
giornaliero, trade, WR, MAR, CAGR/DD) per O1, O2, O3, V, R1, R2, P1, la configurazione G scelta, W3 (78.474 $) e buy & hold;
tabella IS/OOS/2018–20; vicini; placebo; senza il trade migliore; griglia G completa (30 righe) con i vincoli; rischio di rovina;
Kelly informativo; verdetto e testo della lezione per RESEARCH.md.
