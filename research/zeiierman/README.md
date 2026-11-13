# Zeiierman Trend Pressure su BTC · ciclo 1 (12/11/2026) NON REGGE · ciclo 2 (13/11/2026) RESPINTO

Verdetto: nessuna delle 24 configurazioni giornaliere (6 regole × long/short × con/senza stop) supera le soglie preregistrate;
la migliore (R1v long con stop) fa 21,1k contro buy & hold 25,6k e W3 78,5k. La zona blu non anticipa i minimi, la zona rossa
non anticipa i massimi: dopo l'ingresso in rossa BTC sale in media del 12,5% a 60 giorni (base: 5%).

File: `ztp.py` (porting), `fedelta.py`/`fedelta.txt` (controllo), `PREREG.md`, `bt.py` (backtest), `analisi.py` (vicini, coerenza,
errori), `risultati_ciclo1.txt` (tutte le tabelle), `risultati_ciclo1.csv`, `vicini.csv`, `coerenza_eventi.csv`, `episodi_zone.csv`,
`trades/` (liste trade ed errori), `CICLO2_PROPOSTE.md`.

## 1. Fedeltà del porting
Pine v6 tradotto barra per barra (ud, dd, tz, est, ucn, lcn ricorsivi; highest/lowest inclusa la barra corrente; ta.ema con seme
SMA; nz; mintick 0,01). Confronto con gli screenshot (BTCUSDT 1D, barra parziale 12/11 da Binance a 71.562):

| Lettura dello screenshot | Porting | Esito |
|---|---|---|
| Oggi Z-Pulse sulla linea blu (~ −88) | pz −89,2 | ok |
| Z-Trend in rapida discesa poco sotto −50 | tz −50,0 → −58,4 in 5 giorni | ok |
| Core rossa | core bear dal 10/11 (cz −63) | ok |
| Ott 2026 zona rossa ampia, tz vicina a 0 | tz −5/−6 (fine set–metà ott) | ok |
| Giu–lug 2026 zona blu con minimo | tz ≤ −70 dal 05/06 al 20/07, minimo −95 a inizio lug | ok |
| Nov 2025–apr 2026 lunghe zone blu | tz ≤ −70 04/11→12/01 e 22/01→09/04 | ok |
| Ott–nov 2025 inizio con rosso | rossa 04–11/10/2025 | ok |

Scoperta: il riempimento colorato segue la **sola Z-Trend** (fra Z-Trend e linea del Core); la definizione "pz e tz entrambe nella
fascia" è intermittente (nov 2025–apr 2026: blu visivo continuo, Z-Pulse fino a −30). Testate entrambe (R1v visiva, R1u letterale).
L'esaurimento dell'autore (est) con i default dà 7 zone rosse e **zero** zone blu dal 2021: R2 long è vuota (come nella lezione 70).

## 2. Risultati (1D, 1x, 10.000 $ per periodo; IS 2021–23, OOS 2024→11/2026)

| Regola | Lato | Stop | Trade | Finale tot | DD tot | MAR | Finale IS / OOS | MAR IS / OOS | PF IS / OOS | Placebo p | Senza top 3 | Vicini in profitto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Buy & hold | long | – | 1 | 25.590 | −76,6 | 2,03 | 14.619 / 17.504 | 0,60 / 1,42 | – | – | – | – |
| W3 (riferimento) | l/s | trailing | 13 | 78.474 | −21,1 | 32,4 | 33.407 / 24.327 | – | – | – | – | – |
| R1v zona visiva | long | 2,5 ATR | 13 | 21.137 | −54,5 | 2,04 | 10.706 / 19.743 | 0,13 / 4,17 | 1,36 / 5,57 | 0,14 | 9.472 | 10/10 |
| R1v zona visiva | long | no | 7 | 9.584 | −71,7 | −0,06 | 6.829 / 14.035 | − / 0,88 | 0,94 / 2,82 | 0,54 | 4.545 | 2/10 |
| R1v zona visiva | short | 2,5 ATR | 14 | 15.299 | −43,3 | 1,22 | 10.496 / 14.576 | 0,13 / 2,32 | 1,34 / 2,51 | 0,084 | 7.762 | 10/10 |
| R1v zona visiva | short | no | 8 | rovina | <−100 | – | 9.743 / 9.363 | − / − | 1,19 / 0,95 | 0,21 | – | 0/10 |
| R1u letterale | long | 2,5 ATR | 15 | 16.644 | −63,6 | 1,04 | 9.460 / 17.594 | − / 2,38 | 1,19 / 3,42 | 0,27 | 7.028 | 10/10 |
| R2 autore | short | 2,5 ATR | 7 | 5.118 | −52,7 | − | 7.251 / 7.058 | − / − | 0,35 / 0,00 | 0,79 | 5.049 | 0/10 |
| R2v rilascio visivo | long | 2,5 ATR | 14 | 11.747 | −51,3 | 0,34 | 9.305 / 12.932 | − / 1,01 | 1,11 / 2,93 | 0,46 | 5.600 | 9/10 |
| R3 trend | long | no | 29 | 13.605 | −34,6 | 1,04 | 10.783 / 13.657 | 0,23 / 1,08 | 1,33 / 1,94 | 0,39 | 6.036 | 10/10 |
| R3 trend | short | no | 28 | 9.954 | −59,1 | − | 14.092 / 7.064 | 1,53 / − | 2,70 / 0,58 | 0,11 | 4.541 | 3/10 |
| R4 continuazione | long | 2,5 ATR | 7 | 10.472 | −29,1 | 0,16 | 8.804 / 11.895 | − / 0,68 | 0,43 / 4,01 | 0,57 | 7.549 | 9/10 |

Le altre combinazioni (R1u short, R2v short, R4 short, varianti senza stop) sono tutte peggiori: vedi `risultati_ciclo1.txt`.
A 2x: R1v long con stop 27,8k con DD −82%; senza stop il capitale si azzera.
**4h** (dal 03/2022, B&H 17,1k, MAR 1,06): la migliore è R2v long (rilascio visivo blu) 24,8k, DD −44,6%, MAR 3,32, vicini 10/10,
placebo p 0,041 (solo indizio), ma OOS MAR 0,67 contro B&H 1,40 e senza i 3 trade migliori 9.467: non regge. 80 trade, WR 42%.

## 3. Robustezza
- Nessuna configurazione passa il placebo corretto (p ≤ 0,008); solo la 4h R2v long arriva a p 0,041.
- Tutte le configurazioni in profitto perdono senza i 3 trade migliori (R1v long 21,1k → 9,5k).
- Lo stop di 2,5 ATR è ciò che salva R1: senza stop le zone durano mesi e la stessa regola perde (R1v long 9,6k, short in rovina).
- IS e OOS si rovesciano: il long rende nel 2024–26, lo short (R3) nel 2021–23. È il regime, non l'indicatore.

## 4. Coerenza delle zone (1D dal 2021; base = media di tutti i giorni)
| Evento | n | 7 g | 30 g | 60 g | % positivi a 30 g |
|---|---|---|---|---|---|
| Base | 2.111 | +0,6 | +2,5 | +5,0 | 53 |
| Ingresso zona blu visiva | 17 | +1,9 | +1,0 | +3,0 | 59 |
| Rilascio blu visivo | 17 | +2,4 | +3,4 | +3,0 | 65 |
| Ingresso zona rossa visiva | 19 | +0,7 | +5,1 | **+12,5** | 53 |
| Inizio esaurimento rosso (us) | 7 | +2,1 | **+10,1** | +12,1 | 86 |
| Rilascio rosso (ubk) | 7 | +4,3 | +7,8 | +9,0 | 71 |
15 episodi blu dal 2021 (mediana 46 giorni, massimo 103): rendimento in zona mediano +3,2%, ma minimo −53% (mag–ago 2022), −33%
(gen–apr 2026), −29% (dic 2021–feb 2022). La zona blu "compra" anche dentro i bear. La rossa è continuazione del trend (fino a
+121% dentro la zona gen–mag 2021).

## 5. Errori principali
- R1v long (6 perdenti su 13): 3 "zona lunga in trend forte" (tutti 2022, perdite −14/−18%), 2 rilasci falsi, 1 laterale.
- R1v short (8 su 14): 5 laterali in trend rialzista, 3 rilasci falsi (short appena entrata la rossa, stop in 1–3 giorni).
- 4h R2v long (46 su 80): 23 laterali, 15 ingressi tardivi (rilascio dopo un rimbalzo > 2 ATR), 8 rilasci falsi.

## 6. Ciclo 2 (13/11/2026) · P1, P2, P3 tutte RESPINTE
Regole preregistrate alle 02:33 UTC in `PREREG.md` (sezione "Ciclo 2"), codice `c2.py`, output `risultati_ciclo2.txt`, CSV
`risultati_ciclo2.csv`, `vicini_ciclo2.csv`, `p3_ciclo2.csv`, `p3_trade_ciclo2.csv`, `trades/c2_*.csv`. Motore W3 verificato
prima di P3: 10k → 78.474, DD −21,1% (2018–20: 25.142, DD −37,3%). Placebo corretto per 11 famiglie: p ≤ 0,0045.

| Regola (dal 2021, 10k, 1x) | Trade | Finale | DD | MAR | Finale IS / OOS | MAR IS / OOS | Esito |
|---|---|---|---|---|---|---|---|
| Buy & hold | 1 | 25.590 | −76,6 | 2,03 | 14.619 / 17.504 | 0,60 / 1,42 | – |
| W3 | 13 | 78.474 | −21,1 | 32,4 | 33.477 / 23.488 | 12,2 / 6,4 | riferimento |
| Migliore ciclo 1 (R1v long stop) | 13 | 21.137 | −54,5 | 2,04 | 10.706 / 19.743 | 0,13 / 4,17 | – |
| P1a rilascio blu + SMA200 + Core non rosso | 1 | 9.000 | −14,5 | − | 10.000 / 9.000 | − / − | RESPINTA |
| P1b rilascio blu + regime W3 + Core non rosso | 2 | 8.825 | −14,5 | − | 9.806 / 9.000 | − / − | RESPINTA |
| P2a = P1a + uscita al rilascio rosso | 1 | 10.054 | −5,4 | 0,10 | 10.000 / 10.054 | − / 0,10 | RESPINTA |
| P2b = P1a + metà in rossa, metà al rilascio | 1 | 10.282 | −4,2 | 0,68 | 10.000 / 10.282 | − / 0,68 | RESPINTA |
| P3 = W3 al 50% con tz < −50 e Core rosso | 13 | 72.241 | −24,2 | 25,7 | 32.432 / 22.319 | 11,6 / 5,1 | RESPINTA |

- **P1/P2 sono vuote per costruzione**: dei 17 rilasci blu dal 2021 il Core è rosso in 13 e la chiusura è sotto la SMA200 in 15
  (la zona blu è il prezzo nella parte bassa del range a 120 giorni: la conferma di trend la contraddice). Restano 1–2 trade
  (16/07/2024), sotto la soglia di 8; placebo e "senza top 3" non hanno senso con un trade. Vicini in profitto: P1a 1/8, P1b 0/6,
  P2a 4/8, P2b 7/8 (tutti fra 8,6k e 11,4k). Esposizione: 1% dei giorni, phi con W3 −0,08: non è "W3 più lento", è quasi nulla.
- **P3 peggiora W3** in ogni periodo dal 2021 (MAR 25,7 contro 32,4; IS 11,6 contro 12,2; OOS 5,1 contro 6,4) e alza il DD
  (−24,2% contro −21,1%); 2018–20 neutro (25.150 contro 25.142, MAR 4,07 contro 4,06). Vicini sopra W3: 0 su 8 (il migliore,
  tz < −55, 31,6). Placebo (2000 spostamenti circolari): p 0,28, mediana del caso 22,2. Trade toccati: 3 su 13 dal 2021, tutti
  in peggio (08/2021 4,3 → 2,1; 01/2023 13,3 → 12,1; 04/2025 11,3 → 5,8 con 8 cambi d'esposizione: dimezza vicino ai minimi
  di ago–set 2025 e ricompra più in alto); 1 nel 2018–20 (+0,04 punti). I 3 trade migliori di W3 non vengono toccati (0%): lo
  stato "trend negativo" non c'è mai nei grandi trend, quindi non protegge né taglia le code, aggiunge solo rumore nei laterali.

**Opinione.** La Z-Trend è un %R a 120 giorni smussato: dice dove sta il prezzo nel suo range, cioè la stessa informazione del
trend che W3 ha già (SMA40w/EMA21) e con ritardo. Le zone non anticipano inversioni, come regola a sé non batte il buy & hold e
dentro W3 non aggiunge nulla. Uso sensato: solo contesto visivo (quanto è "esteso" il prezzo nel range), non regola né filtro.
Studio chiuso; un ciclo 3 avrebbe senso solo con un'ipotesi nuova, non con altre combinazioni delle stesse soglie.

## Lezione proposta per RESEARCH.md (cicli 1 e 2)
**Lezione 91**: Zeiierman Trend Pressure (porting fedele; la zona colorata segue la sola Z-Trend, un %R a 120 giorni smussato)
non dà vantaggio su BTC dal 2021. Ciclo 1: 24 regole giornaliere (zona, rilascio, trend, continuazione; long/short; con/senza
stop) sotto il buy & hold in almeno una metà, nessun placebo, tutte dipendenti dai 3 trade migliori; la zona blu dura mesi anche
nei bear (−53% nel 2022), la rossa è continuazione (+12,5% a 60 giorni). Ciclo 2 (preregistrato): il rilascio blu con filtro di
trend (SMA200 o regime W3) e Core non rosso dà 1–2 trade in 6 anni (il Core è rosso in 13 dei 17 rilasci: zona blu e conferma di
trend si escludono); uscire al rilascio rosso, intero o a metà, non cambia nulla; dentro W3 ridurre al 50% con tz < −50 e Core
rosso abbassa il MAR (25,7 contro 32,4) e alza il DD (−24,2% contro −21,1%), vicini 0/8, placebo p 0,28, non tocca i grandi
trend. Conferma le lezioni 70 e 86: è informazione di trend già contenuta in W3. Solo contesto visivo. File: research/zeiierman/.

