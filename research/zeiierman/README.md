# Zeiierman Trend Pressure su BTC · ciclo 1 (12/11/2026) · NON REGGE

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

## Lezione proposta per RESEARCH.md
**Lezione 91**: Zeiierman Trend Pressure (porting fedele agli screenshot; la zona colorata segue la sola Z-Trend) non dà un vantaggio
su BTC dal 2021: le 24 regole giornaliere (zona, rilascio, trend, continuazione; long/short; con/senza stop) non battono il buy & hold
in entrambe le metà, nessuna passa il placebo, tutte dipendono dai 3 trade migliori. La zona blu dura mesi anche nei bear (−53% nel
2022), la rossa è continuazione (+12,5% a 60 giorni): "compra in blu, vendi in rossa" vende i trend. L'esaurimento blu dell'autore
non si verifica mai con i default. Conferma la lezione 70. Ciclo 2 solo con le proposte in research/zeiierman/CICLO2_PROPOSTE.md.
