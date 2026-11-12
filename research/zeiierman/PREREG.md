# Zeiierman Trend Pressure · ciclo 1 — preregistrazione (12/11/2026, prima dei risultati delle regole)

Stato al momento della scrittura: porting fatto (`ztp.py`) e controllo di fedeltà sui valori dell'indicatore (nessun backtest
eseguito). Dal controllo sono già noti due fatti che cambiano la traduzione delle regole (non sono risultati di trading):

1. **Zona visiva**: negli screenshot il riempimento rosso/blu segue la sola **Z-Trend** (linea lilla spessa, gradiente fra Z-Trend
   e la linea del Core): nov 2025–apr 2026 è blu continuo mentre la Z-Pulse (linea bianca) risale fino a −30. La definizione
   "entrambe le linee nella fascia" (flag `red`/`blue` di `ztp.py`) è intermittente. Quindi:
   - **zona blu visiva** = tz ≤ −70; **zona rossa visiva** = tz ≥ −30 (flag `vblue`/`vred`);
   - la definizione letterale (pz e tz entrambe nella fascia) resta come variante.
2. **Esaurimento (est)** con i default (sn=7, zn=20): soglie ±12/−88, conferma 2 barre. Dal 2021 sul giornaliero: 7 inizi di
   zona rossa (us) e 7 rilasci rossi (ubk), **zero** zone blu (ls/lbk): con pz e tz entrambe ≤ −88 per 2 barre non accade mai
   (già visto nella lezione 70). La regola R2 dell'autore sul lato long è quindi vuota per costruzione.

## Dati, esecuzione, costi (uguali per tutte le regole)
- 1D: data/spot.csv (Binance BTCUSDT, dal 2019-09, warm-up incluso); 4h: data/spot_1h.csv ricampionato (dal 2022-02: IS 4h
  = 2022-03→2023-12, più corto: documentato).
- Segnale alla chiusura della barra t, esecuzione all'**apertura di t+1**. Niente look-ahead.
- Perp: commissione 0,08%/lato sul nozionale; funding reale (data/funding.csv, tasso giornaliero; 4h = 1/6 per barra): il long
  paga, lo short incassa. Nozionale = esposizione × capitale all'ingresso (1x principale, 2x per confronto con W3).
- Stop di emergenza: 2,5 × ATR(14) (RMA, come Pine) della barra del segnale, fisso dal prezzo d'ingresso; se l'apertura salta
  oltre lo stop si esce all'apertura. Varianti senza stop.
- Periodi: totale 2021-01-01→2026-11-11; IS 2021-01→2023-12; OOS 2024-01→2026-11. Ogni periodo parte flat con 10.000 $.
- Metriche: trade, % vincenti, finale, rendimento, CAGR, max DD giornaliero (chiusure), MAR = rendimento totale / |DD| (metro del
  progetto) e CAGR/|DD|, profit factor, esposizione nel tempo. Confronti: buy & hold spot e W3 (10k→78.474, DD −21,1%).

## Regole (long e short valutate separatamente; parametri dell'indicatore = default)
- **R1v "zona" (lettura dell'utente)**: long all'ingresso in zona blu visiva (tz scende a ≤ −70), uscita all'ingresso in zona
  rossa visiva (tz sale a ≥ −30). Short simmetrico (entra in rossa, esce in blu).
- **R1u** come R1v ma con la definizione letterale (pz e tz entrambe in [−100,−70] / [−30,0]).
- **R2 "rilascio" (autore)**: long a lbk, uscita a ubk; short a ubk, uscita a lbk. Poiché lbk non accade mai, uscita di riserva a
  30 giorni (orizzonte della lezione 70) — scritta ora, non ottimizzata. Il long è vuoto per costruzione.
- **R2v "rilascio visivo"**: long quando tz risale sopra −70 dopo essere stata ≤ −70; uscita quando tz riscende sotto −30 dopo
  essere stata ≥ −30 (rilascio rosso visivo). Short simmetrico.
- **R3 "trend"**: long finché tz > −50 e core bull, flat altrimenti; short finché tz < −50 e core bear.
- **R4 "continuazione"**: dentro lo stato R3 long, ingresso sull'incrocio xup (pz sopra tz); uscita quando lo stato R3 finisce.
  Short: stato R3 short + xdn.
Ogni regola × {long, short} × {stop 2,5 ATR, senza stop} a 1x; 2x solo riportata. 6 regole × 2 lati × 2 = 24 configurazioni
sul 1D: più del limite di 8 del metodo per richiesta esplicita dell'utente; per la molteplicità la soglia del placebo è
p ≤ 0,05/6 ≈ 0,008 per dire "significativo", p ≤ 0,05 solo "indizio".

## Soglie di giudizio (scritte ora)
Una configurazione **"regge"** solo se tutte vere:
1. ≥ 8 trade dal 2021 e in profitto sia in IS sia in OOS;
2. MAR (rend./|DD|) superiore al buy & hold nello stesso lato/periodo in IS e in OOS (per gli short: superiore a 0, cioè
   guadagno con DD < 100%; il B&H short non è un riferimento sensato);
3. profit factor ≥ 1,3 in IS e in OOS;
4. placebo p ≤ 0,05 (≤ 0,008 per "significativo");
5. togliendo i 3 trade migliori resta in profitto;
6. vicini: ≥ 8 dei 10 vicini in profitto dal 2021.
**"Utile per W3"** (da portare al ciclo 2 come filtro/contesto) solo se regge E non è la stessa informazione del trend (R3
correlato col regime di W3) — in questo ciclo si giudica solo il "regge". Nessuna regola sostituisce W3 se non ne batte il MAR
(rend./|DD| = 684,7/21,1 = 32,4) dal 2021 a pari esposizione.

## Robustezza
- Vicini (uno alla volta, ±1 passo): fl 18/24, sl 50/60, ml 110/130, zn 18/22, sn 6/8 (zn e sn influenzano solo est → R2).
- Placebo: stessi numeri e durate dei trade, stesse durate dei periodi flat, ordine casuale (1000 permutazioni), stesso lato,
  rendimento open→open con costi e funding, senza stop; p = (1 + #placebo ≥ reale)/1001.
- Concentrazione: rendimento composto senza i 3 trade migliori.

## Coerenza delle zone (1D, dal 2021)
Rendimento a 7/30/60 giorni dall'apertura successiva a: ingresso in zona blu visiva, rilascio blu visivo, inizio zona blu
letterale; idem rosso (e us/ubk dell'autore). Confronto con il rendimento medio non condizionato a pari orizzonte. Episodi di zona
visiva (gap ≤ 5 barre fusi): durata, rendimento dentro la zona, escursione avversa massima (blu: minimo vs ingresso; rossa:
massimo vs ingresso).

## Analisi degli errori (regole che reggono o, in mancanza, le 2 migliori per MAR dal 2021)
Classificazione meccanica dei perdenti, in quest'ordine: **ingresso tardivo** (nelle 5 barre prima dell'ingresso il prezzo si è
già mosso a favore > 2 ATR); **rilascio falso** (perdita chiusa entro 10 barre); **zona lunga in trend forte** (durata > 30
barre ed escursione avversa > 15%); **laterale** (il resto).
