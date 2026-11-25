# w32_asset2 · W3.2 su altri asset, ciclo 2 · NON SI TRASFERISCE (TRX con il cancello di BTC: da approfondire, non da promuovere)

PREREG `PREREG.md`, commit **f40f7a6** (da solo, prima di ogni rendimento). Dati congelati in `crypto/` e `azioni/` (`DATI.md`).
Motore: `radar.weekly.simulate` invariato (crypto) e `ma_lib.s1_sim` (azioni). Risultati dal 01/06/2020 (inizio della versione
completa) al 24/11/2026; 10.000 $ per asset, 1x, costi e funding inclusi.

**Verdetto (soglie del PREREG)**
- **Q1 · crypto valutabili, parametri di BTC: NON SI TRASFERISCE.** 0 altcoin su 78 passano davvero. Passano 1–5 e conferma solo
  ETH e STX (con BTC), ma nessuna supera Holm su 79 asset: con 2.000 prove il p minimo è 0,0005 e Holm su 79 chiede p ≤ 0,00063,
  cioè il solo pavimento; neanche BTC passerebbe (Holm 0,12). È un effetto della regola più severa, non una prova contro ETH: ETH
  resta in uso per la lezione 111 e questo studio non lo mette in discussione. Conferma la lezione 111 anche dal 2020.
- **Q2 · top 200 del 2020 (senza bias di sopravvivenza): NON SI TRASFERISCE.** 0 su 54 altcoin; passa 1–5 solo ETH. Conto
  equipesato W3.2: 19.161 $ (valutabili 2020) contro 22.736 $ (valutabili di oggi): il bias vale circa 3.600 $ su 10.000.
- **Q3 · azioni con `cmf20`: AZIONI CHIUSE PER W3.2.** 0 titoli su 124 passano 1–5, sia solo prezzo sia con `cmf20` (mediana
  CAGR/DD −0,06 contro 0,30 del buy & hold; WR mediano 31%). `cmf20` non cambia nulla (differenza mediana +0,01).
- **Q4 · BTC come cancello: SOLO CASI ISOLATI.** 1 altcoin su 78 passa davvero: **TRX** (87.198 $, DD −22,5%, 12 trade, WR 83%,
  placebo 0 su 20.000 anche vincolato al cancello, p < 0,00005, Holm su 78 ≤ 0,004, Bonferroni su tutto il ciclo ≤ 0,03; perp su
  Bitget e OKX). Due trade (06/2023–03/2024 +96%, 09–12/2024 +161%) fanno l'80% del guadagno: senza i due migliori 17.017 $;
  perdita massima per trade −4,4%. Revisione critica: **da approfondire, non da promuovere**. Il cancello riduce il DD mediano (−39% contro −56%) ma non crea un vantaggio diffuso.
- **Q5 · parametri per classe: NON MIGLIORA** né per le altcoin (scelta IS 3,0 ATRw / 25%; in OOS passano 1–5 in 2 contro 3) né per
  le azioni (scelta IS 2,5 / 10%; 1 contro 1). Nessun asset passa davvero in OOS.
- **Q6 · portafoglio: MIGLIORA dal 2021 e dal 2023, ma dal 06/2020 lo stesso effetto si ottiene ripesando BTC 2/3 – ETH 1/3
  (CAGR/DD 2,62 contro 2,49 con TRX): il contributo di TRX viene dal 2023–24.** BTC + ETH + TRX(Q4): CAGR/DD 2,49 contro 2,44 dal
  06/2020 (DD −18,9 contro −20,6) e 2,13 contro 1,80 dal 2021 (DD −18,2 contro −20,2). Aggiunge 1,9 operazioni l'anno, 84% delle
  settimane nello stesso verso di BTC.
- **Q7 · SOL e TAO: NON OPERARLE CON W3.2.** SOL rende (80.661 $) ma con DD −39,8% e WR 48%, e dal 2024 perde (−10% in tre anni);
  TAO perde (6.512 $, DD −52%, WR 21%).
- **Q8 · screener all'indietro: NON GIUSTIFICA IL MOTORE NEL TOOL.** Dal 2022 il conto "screener" fa 8.535 $ (DD −30%) contro
  22.762 $ di BTC + ETH e 11.198 $ di "tutte le idonee": gli asset con un buon passato non lo ripetono.

**Controlli**: (a) BTC 2021-01-01 → 2026-11-10 con motore e dati nuovi = **78.474 $** (identico); (b) ETH = 34.758 $ contro 34.760 $
di w32_top100: la differenza di 2 $ è il funding 01–10/11/2026 dello short ETH aperto il 09/11 (w32_top100 aveva il funding fino al
31/10; togliendolo torna 34.760 $; prezzi e taker buy identici); (c) la copia del motore per Q5 (`weekly_q5.py`) a 2,5/0,25 dà
trade e finale identici a `radar.weekly` su BTC, ETH, SOL; (d) `ma_lib.s1_sim` riproduce 864/864 righe di `azioni/counts.csv`.
**Riferimenti**: BTC W3.2 dal 2021 78.474 $ (al 10/11) / 84.820 $ (al 24/11), dal 06/2020 225.069 $ (DD −21,1%); ETH W3.2 dal
2021 39.572 $, dal 06/2020 53.394 $ (DD −27,5%); liquidità 10.000 $.

Colonne delle tabelle: finale da 10.000 $, CAGR, DD giornaliero, trade (posizione aperta inclusa), WR, buy & hold (finale · DD ·
CAGR/DD), IS 2020–22 / OOS 2023→ (o le due metà se l'IS o l'OOS è < 6 mesi), criteri falliti (1 CAGR/DD > B&H · 2 DD ≥ −35% · 3 WR
≥ 60% · 4 IS e OOS positivi · 5 ≥ 8 trade), conferma (senza il trade migliore > 10.000 $ e vicini 2,0/3,0 ATRw sopra il B&H in
almeno metà), p del placebo (2.000 prove, seme 7), p aggiustato di Holm sul numero di asset valutati nella domanda, perp Bitget/OKX.

## Q1 · crypto, motore completo, parametri di BTC
### Q1 · top 20 crypto di oggi (CoinGecko 25/11/2026, dopo le esclusioni)
| Asset | Inizio | Finale | CAGR | DD | Trade | WR | B&H finale · DD · C/DD | IS / OOS | Falliti | Conf. | p | p Holm | Bitget/OKX |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. BTC | 2020-06-01 | 225.069 | 61,7% | -21,1 | 17 | 94% | 63.073 · -76,6 · 0,43 | +508% / +230% | – | sì | 0,0015 | 0,116 | sì/sì |
| 2. ETH | 2020-06-01 | 53.394 | 29,5% | -27,5 | 16 | 62% | 72.266 · -79,3 · 0,45 | +165% / +89% | – | sì | 0,0045 | 0,342 | sì/sì |
| 4. BNB | 2020-06-01 | 31.694 | 19,5% | -67,4 | 29 | 31% | 319.688 · -70,9 · 1,00 | +107% / +53% | 1,2,3 | no | 0,1384 | 1,000 | sì/sì |
| 6. XRP | 2020-06-01 | 3.814 | -13,8% | -79,7 | 31 | 29% | 45.522 · -83,2 · 0,32 | -15% / -55% | 1,2,3,4 | no | 0,4198 | 1,000 | sì/sì |
| 7. SOL | 2021-01-11 | 80.661 | 42,7% | -39,8 | 23 | 48% | 201.456 · -96,3 · 0,69 | +266% / +121% | 2,3 | sì | 0,0115 | 0,840 | sì/sì |
| 8. TRX | 2020-06-01 | 90.570 | 40,5% | -44,4 | 22 | 59% | 194.102 · -69,5 · 0,83 | +35% / +571% | 2,3 | sì | 0,0005 | 0,040 | sì/sì |
| 10. HYPE (breve) | 2026-03-02 | 9.515 | -6,6% | -37,2 | 3 | 33% | 18.941 · -38,3 · 3,64 | +22% / -11% (metà) | 1,2,3,4,5 | no | – | – | sì/sì |
| 11. ZEC | 2020-06-01 | 12.091 | 3,0% | -68,4 | 30 | 30% | 142.988 · -94,3 · 0,54 | -34% / +112% | 1,2,3,4 | no | 0,1664 | 1,000 | sì/sì |
| 12. XMR | 2020-06-01 | 3.301 | -15,7% | -88,7 | 33 | 24% | 74.793 · -78,4 · 0,46 | -1% / -67% | 1,2,3,4 | no | 0,6662 | 1,000 | sì/no |
| 13. DOGE | 2020-10-26 | 43.898 | 27,6% | -77,3 | 36 | 33% | 207.694 · -92,3 · 0,70 | +232% / +39% | 1,2,3 | no | 0,0375 | 1,000 | sì/sì |
| 14. LEO (solo prezzo) | 2020-10-27 | 19.599 | 11,7% | -58,1 | 26 | 27% | 74.048 · -56,5 · 0,69 | +162% / -28% | 1,2,3,4 | – | – | – | no/no |
| 15. LINK | 2020-06-01 | 11.364 | 2,0% | -49,9 | 26 | 38% | 21.359 · -90,2 · 0,14 | +52% / -29% | 1,2,3,4 | no | 0,1079 | 1,000 | sì/sì |
| 16. WBT | – | senza dati: nessun dato W3.2 | | | | | | | | | | | no/no |
| 18. ADA | 2020-06-01 | 38.687 | 23,2% | -46,5 | 24 | 46% | 19.486 · -95,2 · 0,11 | +196% / +16% | 2,3 | sì | 0,0155 | 1,000 | sì/sì |
| 21. XLM | 2020-06-01 | 4.928 | -10,3% | -79,8 | 30 | 33% | 17.561 · -90,3 · 0,10 | +59% / -71% | 1,2,3,4 | no | 0,1949 | 1,000 | sì/sì |
| 22. BCH | 2020-06-01 | 11.104 | 1,6% | -63,3 | 29 | 41% | 8.250 · -94,2 · -0,03 | +75% / -38% | 2,3,4 | no | 0,0490 | 1,000 | sì/sì |
| 23. NEAR | 2021-07-19 | 5.375 | -11,0% | -75,7 | 24 | 33% | 15.087 · -95,2 · 0,08 | -5% / -37% | 1,2,3,4 | no | 0,3898 | 1,000 | sì/sì |
| 24. LTC | 2020-06-01 | 4.128 | -12,8% | -87,4 | 29 | 28% | 8.929 · -89,7 · -0,02 | +129% / -82% | 1,2,3,4 | no | 0,4583 | 1,000 | sì/sì |
| 25. CC | – | breve: nessun dato W3.2 | | | | | | | | | | | sì/sì |
| 26. AVAX | 2021-06-28 | 6.331 | -8,1% | -65,4 | 25 | 40% | 5.981 · -95,6 · -0,09 | -9% / -32% | 1,2,3,4 | no | 0,3688 | 1,000 | sì/sì |

### Q1 · migliori 15 e peggiori 5 (79 valutabili, per CAGR/DD)
| Asset | Inizio | Finale | CAGR | DD | Trade | WR | B&H finale · DD · C/DD | IS / OOS | Falliti | Conf. | p | p Holm | Bitget/OKX |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTC | 2020-06-01 | 225.069 | 61,7% | -21,1 | 17 | 94% | 63.073 · -76,6 · 0,43 | +508% / +230% | – | sì | 0,0015 | 0,116 | sì/sì |
| ETH | 2020-06-01 | 53.394 | 29,5% | -27,5 | 16 | 62% | 72.266 · -79,3 · 0,45 | +165% / +89% | – | sì | 0,0045 | 0,342 | sì/sì |
| SOL | 2021-01-11 | 80.661 | 42,7% | -39,8 | 23 | 48% | 201.456 · -96,3 · 0,69 | +266% / +121% | 2,3 | sì | 0,0115 | 0,840 | sì/sì |
| VET | 2020-06-01 | 93.522 | 41,2% | -41,0 | 23 | 70% | 7.734 · -98,3 · -0,04 | +351% / +94% | 2 | sì | 0,0010 | 0,078 | sì/no |
| STX | 2023-06-12 | 23.352 | 27,8% | -28,4 | 11 | 73% | 4.838 · -96,7 · -0,20 | +116% / +11% (metà) | – | sì | 0,0075 | 0,562 | sì/sì |
| TRX | 2020-06-01 | 90.570 | 40,5% | -44,4 | 22 | 59% | 194.102 · -69,5 · 0,83 | +35% / +571% | 2,3 | sì | 0,0005 | 0,040 | sì/sì |
| INJ | 2022-12-05 | 30.595 | 32,5% | -44,7 | 18 | 44% | 35.779 · -94,7 · 0,40 | +264% / -16% (metà) | 2,3,4 | no | 0,0820 | 1,000 | sì/sì |
| IOTX | 2021-11-29 | 19.323 | 14,1% | -25,9 | 17 | 41% | 149 · -98,7 · -0,58 | -3% / +107% | 3,4 | sì | 0,0220 | 1,000 | sì/no |
| RUNE | 2021-06-07 | 32.906 | 24,4% | -45,8 | 17 | 59% | 467 · -98,1 · -0,44 | +8% / +214% | 2,3 | sì | 0,0140 | 1,000 | sì/no |
| ADA | 2020-06-01 | 38.687 | 23,2% | -46,5 | 24 | 46% | 19.486 · -95,2 · 0,11 | +196% / +16% | 2,3 | sì | 0,0155 | 1,000 | sì/sì |
| ALGO | 2020-10-05 | 22.350 | 14,0% | -33,4 | 19 | 42% | 2.517 · -96,9 · -0,21 | -10% / +139% | 3,4 | sì | 0,0250 | 1,000 | sì/sì |
| GRT | 2021-09-20 | 23.333 | 17,8% | -44,3 | 12 | 50% | 197 · -98,9 · -0,54 | +42% / +64% | 2,3 | sì | 0,0230 | 1,000 | sì/sì |
| DOGE | 2020-10-26 | 43.898 | 27,6% | -77,3 | 36 | 33% | 207.694 · -92,3 · 0,70 | +232% / +39% | 1,2,3 | no | 0,0375 | 1,000 | sì/sì |
| THETA | 2020-09-14 | 28.502 | 18,4% | -59,8 | 15 | 53% | 2.338 · -99,1 · -0,21 | +130% / +19% | 2,3 | sì | 0,0660 | 1,000 | sì/sì |
| BNB | 2020-06-01 | 31.694 | 19,5% | -67,4 | 29 | 31% | 319.688 · -70,9 · 1,00 | +107% / +53% | 1,2,3 | no | 0,1384 | 1,000 | sì/sì |
| … | | | | | | | | | | | | | |
| ATOM | 2020-06-01 | 2.715 | -18,2% | -78,1 | 29 | 34% | 4.564 · -97,4 · -0,12 | -70% / -12% | 1,2,3,4 | no | 0,7031 | 1,000 | sì/sì |
| ZEN | 2021-04-12 | 3.575 | -16,7% | -73,6 | 25 | 28% | 493 · -97,6 · -0,43 | +3% / -67% | 2,3,4 | no | 0,6232 | 1,000 | sì/sì |
| COMP | 2021-03-29 | 2.167 | -23,7% | -85,1 | 21 | 29% | 477 · -98,2 · -0,42 | +38% / -86% | 2,3,4 | no | 0,6612 | 1,000 | sì/sì |
| LDO | 2023-02-13 | 5.126 | -16,2% | -55,9 | 17 | 18% | 909 · -94,0 · -0,50 | -17% / -40% (metà) | 2,3,4 | no | 0,9190 | 1,000 | sì/sì |
| QNT | 2023-02-06 | 2.390 | -31,4% | -77,7 | 20 | 25% | 10.565 · -66,3 · 0,02 | -20% / -70% (metà) | 1,2,3,4 | no | 0,7416 | 1,000 | sì/sì |
| … | | | | | | | | | | | | | |

**Universo largo (79 valutabili, 78 altcoin)**: altcoin 78 · finale quartili 5.929 / 10.381 / 14.577 · DD mediano -56,2 · WR mediano 40% · CAGR/DD mediano 0,01 (B&H -0,27, B&H finale mediano 2.096) · c1 64, c2 7, c3 3, c4 17, c5 78 · 1–5 2 · 1–5+conferma 2 · p<0,05 14 · sopra 10.000 $ 40  
Solo top 200 di oggi: altcoin 49 · finale quartili 6.620 / 11.077 / 22.350 · DD mediano -56,4 · WR mediano 42% · CAGR/DD mediano 0,03 (B&H -0,19, B&H finale mediano 4.513) · c1 37, c2 6, c3 3, c4 14, c5 49 · 1–5 2 · 1–5+conferma 2 · p<0,05 12 · sopra 10.000 $ 30
Rispetto alla lezione 111 (dal 2021, 27 altcoin): aggiungere il 2020 e allargare a 78 altcoin non cambia il quadro. Passano 1–5
ETH e STX (STX era breve nel ciclo 1); TRX e SOL rendono ma falliscono DD e WR; VET fallisce solo il DD (−41%). Con la regola Holm
del ciclo 1 (solo sugli asset che passano 1–5, m = 3) passerebbero ETH e STX (2 su 78 = 2,6%, "casi isolati"): la regola del
PREREG, più severa, li esclude. Brevi e solo prezzo (descrittive): 54 simulate · passano 1–5: [] · finale mediano 9.547, DD mediano -32,1; solo prezzo 25 · passano 1–5: [] · finale mediano 10.742, DD mediano -54,9

## Q2 · top 20 del 2020 (CMC 29/12/2019)
### Q2 · top 20 crypto al 29/12/2019 (CMC, dopo le esclusioni)
| Asset | Inizio | Finale | CAGR | DD | Trade | WR | B&H finale · DD · C/DD | IS / OOS | Falliti | Conf. | p | p Holm | Bitget/OKX |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. BTC | 2020-06-01 | 225.069 | 61,7% | -21,1 | 17 | 94% | 63.073 · -76,6 · 0,43 | +508% / +230% | – | sì | 0,0015 | 0,080 | sì/sì |
| 2. ETH | 2020-06-01 | 53.394 | 29,5% | -27,5 | 16 | 62% | 72.266 · -79,3 · 0,45 | +165% / +89% | – | sì | 0,0045 | 0,234 | sì/sì |
| 3. XRP | 2020-06-01 | 3.814 | -13,8% | -79,7 | 31 | 29% | 45.522 · -83,2 · 0,32 | -15% / -55% | 1,2,3,4 | no | 0,4198 | 1,000 | sì/sì |
| 5. BCH | 2020-06-01 | 11.104 | 1,6% | -63,3 | 29 | 41% | 8.250 · -94,2 · -0,03 | +75% / -38% | 2,3,4 | no | 0,0490 | 1,000 | sì/sì |
| 6. LTC | 2020-06-01 | 4.128 | -12,8% | -87,4 | 29 | 28% | 8.929 · -89,7 · -0,02 | +129% / -82% | 1,2,3,4 | no | 0,4583 | 1,000 | sì/sì |
| 7. EOS | 2020-06-01 | 12.676 | 3,7% | -51,4 | 24 | 42% | 244 · -99,6 · -0,44 | +31% / +2% | 2,3 | no | 0,0100 | 0,510 | sì/sì |
| 8. BNB | 2020-06-01 | 31.694 | 19,5% | -67,4 | 29 | 31% | 319.688 · -70,9 · 1,00 | +107% / +53% | 1,2,3 | no | 0,1384 | 1,000 | sì/sì |
| 9. BSV (breve) | 2024-07-22 | 9.090 | -4,0% | -28,9 | 13 | 38% | 2.916 · -87,0 · -0,47 | +4% / -7% (metà) | 3,4 | no | – | – | sì/no |
| 10. XLM | 2020-06-01 | 4.928 | -10,3% | -79,8 | 30 | 33% | 17.561 · -90,3 · 0,10 | +59% / -71% | 1,2,3,4 | no | 0,1949 | 1,000 | sì/sì |
| 11. TRX | 2020-06-01 | 90.570 | 40,5% | -44,4 | 22 | 59% | 194.102 · -69,5 · 0,83 | +35% / +571% | 2,3 | sì | 0,0005 | 0,028 | sì/sì |
| 12. XTZ | 2020-06-29 | 9.231 | -1,2% | -59,0 | 24 | 54% | 897 · -97,8 · -0,32 | +31% / -38% | 2,3,4 | no | 0,0810 | 1,000 | sì/sì |
| 13. ADA | 2020-06-01 | 38.687 | 23,2% | -46,5 | 24 | 46% | 19.486 · -95,2 · 0,11 | +196% / +16% | 2,3 | sì | 0,0155 | 0,775 | sì/sì |
| 14. LEO (solo prezzo) | 2020-10-27 | 19.599 | 11,7% | -58,1 | 26 | 27% | 74.048 · -56,5 · 0,69 | +162% / -28% | 1,2,3,4 | – | – | – | no/no |
| 15. ATOM | 2020-06-01 | 2.715 | -18,2% | -78,1 | 29 | 34% | 4.564 · -97,4 · -0,12 | -70% / -12% | 1,2,3,4 | no | 0,7031 | 1,000 | sì/sì |
| 16. XMR | 2020-06-01 | 3.301 | -15,7% | -88,7 | 33 | 24% | 74.793 · -78,4 · 0,46 | -1% / -67% | 1,2,3,4 | no | 0,6662 | 1,000 | sì/no |
| 17. HT | – | senza dati: nessun dato W3.2 | | | | | | | | | | | no/no |
| 18. LINK | 2020-06-01 | 11.364 | 2,0% | -49,9 | 26 | 38% | 21.359 · -90,2 · 0,14 | +52% / -29% | 1,2,3,4 | no | 0,1079 | 1,000 | sì/sì |
| 19. NEO | 2020-06-01 | 10.811 | 1,2% | -52,8 | 27 | 48% | 1.382 · -98,8 · -0,27 | +34% / -27% | 2,3,4 | no | 0,1099 | 1,000 | sì/sì |
| 20. MIN | – | senza dati: nessun dato W3.2 | | | | | | | | | | | no/no |
| 21. ETC | 2020-06-01 | 10.629 | 0,9% | -79,4 | 28 | 36% | 8.268 · -95,9 · -0,03 | +89% / -47% | 2,3,4 | no | 0,0965 | 1,000 | sì/sì |

**Universo largo (55 valutabili del 2020, 54 altcoin)**: altcoin 54 · finale quartili 5.514 / 9.980 / 15.100 · DD mediano -59,4 · WR mediano 39% · CAGR/DD mediano 0,00 (B&H -0,24, B&H finale mediano 2.428) · c1 42, c2 3, c3 2, c4 11, c5 54 · 1–5 1 · 1–5+conferma 1 · p<0,05 10 · sopra 10.000 $ 27
Delle 191 monete del 2020 dopo le esclusioni solo 55 sono valutabili e 101 non hanno alcun dato operabile (token morti o mai
quotati con perp): chi avesse scelto allora la top 200 non avrebbe potuto operarne più di un terzo.

### Q2 · portafogli equipesati dal 01/06/2020 (capitali separati, liquidità prima dell'inizio)
| Portafoglio | N | Finale | CAGR | DD | CAGR/DD |
|---|---|---|---|---|---|
| W3.2 valutabili top 200 2020 | 55 | 19.161 | 10,6% | -18,6 | 0,57 |
| B&H valutabili top 200 2020 | 55 | 23.658 | 14,2% | -85,0 | 0,17 |
| W3.2 valutabili top 200 oggi | 50 | 22.736 | 13,5% | -16,6 | 0,82 |
| B&H valutabili top 200 oggi | 50 | 31.067 | 19,1% | -82,6 | 0,23 |
| W3.2 tutte le 79 valutabili | 79 | 17.782 | 9,3% | -17,6 | 0,53 |
| B&H tutte le 79 valutabili | 79 | 20.233 | 11,5% | -83,4 | 0,14 |
| W3.2 solo BTC | 1 | 225.069 | 61,7% | -21,1 | 2,92 |
| W3.2 solo ETH | 1 | 53.394 | 29,5% | -27,5 | 1,07 |

## Q3 · azioni: solo prezzo contro `cmf20` (124 titoli, dal 2020)
### Q3 · top 10 azioni di oggi (CompaniesMarketcap 25/11/2026)
| Titolo · variante | Inizio | Finale | CAGR | DD | Trade | WR | B&H finale · DD · C/DD | IS / OOS | Falliti | Conf. | p | p Holm | Bitget/OKX |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Apple · prezzo | 2020-01-02 | 20.529 | 11,0% | -40,8 | 25 | 48% | 49.659 · -33,4 · 0,78 | +48% / +36% | 1,2,3 | no | 0,3668 | 1,000 | sì/sì |
| 1. Apple · cmf20 | 2020-01-02 | 12.625 | 3,4% | -57,5 | 25 | 44% | 49.659 · -33,4 · 0,78 | +31% / -4% | 1,2,3,4 | no | 0,6847 | 1,000 | sì/sì |
| 2. NVIDIA · prezzo | 2020-01-02 | 117.097 | 42,9% | -47,7 | 19 | 63% | 261.835 · -66,3 · 0,91 | +260% / +236% | 1,2 | no | 0,0315 | 1,000 | sì/sì |
| 2. NVIDIA · cmf20 | 2020-01-02 | 99.769 | 39,6% | -47,7 | 18 | 56% | 261.835 · -66,3 · 0,91 | +185% / +250% | 1,2,3 | no | 0,0940 | 1,000 | sì/sì |
| 3. Microsoft · prezzo | 2020-01-02 | 12.773 | 3,6% | -31,0 | 24 | 38% | 33.148 · -37,1 · 0,51 | +35% / -11% | 1,3,4 | no | 0,2254 | 1,000 | sì/sì |
| 3. Microsoft · cmf20 | 2020-01-02 | 13.020 | 3,9% | -31,5 | 20 | 40% | 33.148 · -37,1 · 0,51 | +24% / -2% | 1,3,4 | no | 0,3368 | 1,000 | sì/sì |
| 4. Alphabet (Google) · prezzo | 2020-01-02 | 25.419 | 14,5% | -38,3 | 25 | 40% | 41.742 · -44,3 · 0,52 | +73% / +40% | 1,2,3 | no | 0,2084 | 1,000 | sì/sì |
| 4. Alphabet (Google) · cmf20 | 2020-01-02 | 27.394 | 15,7% | -34,7 | 20 | 50% | 41.742 · -44,3 · 0,52 | +67% / +58% | 1,3 | no | 0,1904 | 1,000 | sì/sì |
| 5. Amazon · prezzo | 2020-01-02 | 7.420 | -4,2% | -66,7 | 33 | 30% | 26.884 · -56,1 · 0,27 | +49% / -52% | 1,2,3,4 | no | 0,5202 | 1,000 | sì/sì |
| 5. Amazon · cmf20 | 2020-01-02 | 10.810 | 1,1% | -55,4 | 23 | 43% | 26.884 · -56,1 · 0,27 | +56% / -32% | 1,2,3,4 | no | 0,3708 | 1,000 | sì/sì |
| 6. TSMC · prezzo | 2020-01-02 | 29.941 | 17,2% | -39,6 | 22 | 41% | 73.558 · -44,8 · 0,75 | +98% / +58% | 1,2,3 | no | 0,0565 | 1,000 | sì/sì |
| 6. TSMC · cmf20 | 2020-01-02 | 28.286 | 16,3% | -32,8 | 18 | 39% | 73.558 · -44,8 · 0,75 | +137% / +44% | 1,3 | no | 0,0650 | 1,000 | sì/sì |
| 7. SpaceX | – | meno di un anno di dati: non valutato | | | | | | | | | | | sì/sì |
| 8. Saudi Aramco · prezzo | 2020-12-11 | 11.937 | 3,0% | -22,4 | 19 | 53% | 11.835 · -28,5 · 0,10 | +5% / +13% | 3 | sì | 0,1274 | 1,000 | no/no |
| 8. Saudi Aramco · cmf20 | 2020-12-11 | 11.388 | 2,2% | -22,4 | 19 | 47% | 11.835 · -28,5 · 0,10 | +5% / +8% | 1,3 | sì | 0,1569 | 1,000 | no/no |
| 9. Tesla · prezzo | 2020-01-02 | 29.467 | 17,0% | -65,8 | 35 | 34% | 135.793 · -73,6 · 0,62 | +525% / -56% | 1,2,3,4 | no | 0,0930 | 1,000 | sì/sì |
| 9. Tesla · cmf20 | 2020-01-02 | 20.536 | 11,0% | -76,4 | 33 | 30% | 135.793 · -73,6 · 0,62 | +474% / -69% | 1,2,3,4 | no | 0,1954 | 1,000 | sì/sì |
| 10. Meta Platforms (Facebook) · prezzo | 2020-01-02 | 14.536 | 5,6% | -65,9 | 26 | 31% | 28.773 · -76,7 · 0,22 | +35% / +9% | 1,2,3 | no | 0,2074 | 1,000 | sì/sì |
| 10. Meta Platforms (Facebook) · cmf20 | 2020-01-02 | 21.455 | 11,7% | -66,5 | 21 | 38% | 28.773 · -76,7 · 0,22 | +96% / +11% | 1,2,3 | no | 0,1714 | 1,000 | sì/sì |

### Q3 · top 10 azioni a fine 2019
| Titolo · variante | Inizio | Finale | CAGR | DD | Trade | WR | B&H finale · DD · C/DD | IS / OOS | Falliti | Conf. | p | p Holm | Bitget/OKX |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Saudi Aramco · prezzo | 2020-12-11 | 11.937 | 3,0% | -22,4 | 19 | 53% | 11.835 · -28,5 · 0,10 | +5% / +13% | 3 | sì | 0,1274 | 1,000 | no/no |
| 1. Saudi Aramco · cmf20 | 2020-12-11 | 11.388 | 2,2% | -22,4 | 19 | 47% | 11.835 · -28,5 · 0,10 | +5% / +8% | 1,3 | sì | 0,1569 | 1,000 | no/no |
| 2. Apple · prezzo | 2020-01-02 | 20.529 | 11,0% | -40,8 | 25 | 48% | 49.659 · -33,4 · 0,78 | +48% / +36% | 1,2,3 | no | 0,3668 | 1,000 | sì/sì |
| 2. Apple · cmf20 | 2020-01-02 | 12.625 | 3,4% | -57,5 | 25 | 44% | 49.659 · -33,4 · 0,78 | +31% / -4% | 1,2,3,4 | no | 0,6847 | 1,000 | sì/sì |
| 3. Microsoft · prezzo | 2020-01-02 | 12.773 | 3,6% | -31,0 | 24 | 38% | 33.148 · -37,1 · 0,51 | +35% / -11% | 1,3,4 | no | 0,2254 | 1,000 | sì/sì |
| 3. Microsoft · cmf20 | 2020-01-02 | 13.020 | 3,9% | -31,5 | 20 | 40% | 33.148 · -37,1 · 0,51 | +24% / -2% | 1,3,4 | no | 0,3368 | 1,000 | sì/sì |
| 4. Alphabet (Google) · prezzo | 2020-01-02 | 25.419 | 14,5% | -38,3 | 25 | 40% | 41.742 · -44,3 · 0,52 | +73% / +40% | 1,2,3 | no | 0,2084 | 1,000 | sì/sì |
| 4. Alphabet (Google) · cmf20 | 2020-01-02 | 27.394 | 15,7% | -34,7 | 20 | 50% | 41.742 · -44,3 · 0,52 | +67% / +58% | 1,3 | no | 0,1904 | 1,000 | sì/sì |
| 5. Amazon · prezzo | 2020-01-02 | 7.420 | -4,2% | -66,7 | 33 | 30% | 26.884 · -56,1 · 0,27 | +49% / -52% | 1,2,3,4 | no | 0,5202 | 1,000 | sì/sì |
| 5. Amazon · cmf20 | 2020-01-02 | 10.810 | 1,1% | -55,4 | 23 | 43% | 26.884 · -56,1 · 0,27 | +56% / -32% | 1,2,3,4 | no | 0,3708 | 1,000 | sì/sì |
| 6. Meta Platforms (Facebook) · prezzo | 2020-01-02 | 14.536 | 5,6% | -65,9 | 26 | 31% | 28.773 · -76,7 · 0,22 | +35% / +9% | 1,2,3 | no | 0,2074 | 1,000 | sì/sì |
| 6. Meta Platforms (Facebook) · cmf20 | 2020-01-02 | 21.455 | 11,7% | -66,5 | 21 | 38% | 28.773 · -76,7 · 0,22 | +96% / +11% | 1,2,3 | no | 0,1714 | 1,000 | sì/sì |
| 7. Alibaba · prezzo | 2020-01-02 | 10.748 | 1,1% | -69,8 | 33 | 33% | 4.159 · -80,1 · -0,15 | +40% / -24% | 2,3,4 | no | 0,1474 | 1,000 | sì/no |
| 7. Alibaba · cmf20 | 2020-01-02 | 11.196 | 1,7% | -70,4 | 28 | 32% | 4.159 · -80,1 · -0,15 | +37% / -18% | 2,3,4 | no | 0,1159 | 1,000 | sì/no |
| 8. Berkshire Hathaway · prezzo | 2020-01-02 | 7.510 | -4,1% | -37,9 | 27 | 26% | 25.345 · -29,6 · 0,49 | -27% / +0% | 1,2,3,4 | no | 0,7491 | 1,000 | sì/sì |
| 8. Berkshire Hathaway · cmf20 | 2020-01-02 | 7.782 | -3,6% | -35,9 | 25 | 28% | 25.345 · -29,6 · 0,49 | -24% / -1% | 1,2,3,4 | no | 0,8866 | 1,000 | sì/sì |
| 9. Tencent · prezzo | 2020-01-02 | 24.121 | 13,6% | -38,3 | 22 | 55% | 10.197 · -72,8 · 0,00 | +30% / +66% | 2,3 | sì | 0,0180 | 1,000 | sì/sì |
| 9. Tencent · cmf20 | 2020-01-02 | 23.744 | 13,4% | -43,0 | 18 | 56% | 10.197 · -72,8 · 0,00 | +58% / +34% | 2,3 | sì | 0,0275 | 1,000 | sì/sì |
| 10. ICBC · prezzo | 2020-01-02 | 8.254 | -2,7% | -48,5 | 27 | 33% | 20.877 · -31,6 · 0,36 | -40% / +34% | 1,2,3,4 | no | 0,6467 | 1,000 | no/no |
| 10. ICBC · cmf20 | 2020-01-02 | 8.896 | -1,7% | -44,0 | 24 | 33% | 20.877 · -31,6 · 0,36 | -32% / +31% | 1,2,3,4 | no | 0,5407 | 1,000 | no/no |

**Universo largo**: 
- Azioni prezzo: 124 titoli · finale quartili 5.526 / 8.496 / 14.756 · DD mediano -55,5 · WR mediano 31% · CAGR/DD mediano -0,06 (B&H 0,30) · c1 11, c2 7, c3 2, c4 22, c5 123 · 1–5 0 · p<0,05 7 · migliori per CAGR/DD: GE Vernova 2,01 (B&H 1,64, DD -23,6, WR 67%, falliti 5), NVIDIA 0,90 (B&H 0,91, DD -47,7, WR 63%, falliti 1,2), General Electric 0,77 (B&H 0,50, DD -31,3, WR 42%, falliti 3), Cisco 0,48 (B&H 0,36, DD -26,0, WR 38%, falliti 3), TSMC 0,44 (B&H 0,75, DD -39,6, WR 41%, falliti 1,2,3), AMD 0,42 (B&H 0,57, DD -44,6, WR 50%, falliti 1,2,3)
- Azioni cmf20: 124 titoli · finale quartili 5.702 / 8.328 / 13.783 · DD mediano -53,0 · WR mediano 31% · CAGR/DD mediano -0,06 (B&H 0,30) · c1 12, c2 12, c3 2, c4 25, c5 123 · 1–5 0 · p<0,05 5 · migliori per CAGR/DD: GE Vernova 2,27 (B&H 1,64, DD -23,6, WR 100%, falliti 5), NVIDIA 0,83 (B&H 0,91, DD -47,7, WR 56%, falliti 1,2,3), General Electric 0,68 (B&H 0,50, DD -32,2, WR 44%, falliti 3), TSMC 0,50 (B&H 0,75, DD -32,8, WR 39%, falliti 1,3), Cisco 0,48 (B&H 0,36, DD -26,6, WR 37%, falliti 3), Alphabet (Google) 0,45 (B&H 0,52, DD -34,7, WR 50%, falliti 1,3)
- cmf20 contro solo prezzo (stesso titolo): CAGR/DD più alto in 66/124, DD meno profondo in 70/124, mediana della differenza di CAGR/DD 0,01
Nessun titolo passa 1–5 in nessuna variante: il criterio che cade quasi sempre è il WR (2 su 124 ≥ 60%) insieme al DD (7–12 su 124
≥ −35%) e al confronto con il buy & hold (11–12 su 124). Il flusso dai volumi giornalieri non sostituisce il flusso perp.
Per il PREREG le azioni sono chiuse per W3.2.

## Q4 · BTC come cancello (78 altcoin valutabili)
### Q4 · cancello BTC: top 20 oggi e 2020 (altcoin valutabili) + migliori per CAGR/DD
| Asset | Inizio | Finale | CAGR | DD | Trade | WR | B&H finale · DD · C/DD | IS / OOS | Falliti | Conf. | p | p Holm | Bitget/OKX |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TRX | 2020-06-01 | 87.198 | 39,7% | -22,5 | 12 | 83% | 194.102 · -69,5 · 0,83 | +50% / +482% | – | sì | 0,0005 | 0,039 | sì/sì |
| ZEC | 2020-06-01 | 43.155 | 25,3% | -22,7 | 9 | 56% | 142.988 · -94,3 · 0,54 | +12% / +269% | 3 | sì | 0,0080 | 0,608 | sì/sì |
| RUNE (fuori nucleo) | 2021-06-07 | 33.771 | 24,9% | -26,2 | 11 | 64% | 467 · -98,1 · -0,44 | +21% / +188% | – | sì | 0,0140 | 1,000 | sì/no |
| BNB | 2020-06-01 | 66.985 | 34,1% | -39,6 | 18 | 39% | 319.688 · -70,9 · 1,00 | +272% / +80% | 1,2,3 | no | 0,0140 | 1,000 | sì/sì |
| STX (fuori nucleo) | 2023-06-12 | 20.670 | 23,4% | -27,5 | 8 | 75% | 4.838 · -96,7 · -0,20 | +118% / -5% (metà) | 4 | sì | 0,0145 | 1,000 | sì/sì |
| SOL | 2021-01-11 | 52.037 | 32,5% | -40,1 | 15 | 60% | 201.456 · -96,3 · 0,69 | +115% / +142% | 2 | sì | 0,0230 | 1,000 | sì/sì |
| INJ (fuori nucleo) | 2022-12-05 | 31.197 | 33,2% | -43,6 | 12 | 50% | 35.779 · -94,7 · 0,40 | +327% / -27% (metà) | 2,3,4 | no | 0,1004 | 1,000 | sì/sì |
| LRC (fuori nucleo) | 2021-03-15 | 22.999 | 18,0% | -25,5 | 11 | 55% | 451 · -99,3 · -0,46 | +111% / -2% | 3,4 | sì | 0,0115 | 0,862 | no/no |
| VET (fuori nucleo) | 2020-06-01 | 38.712 | 23,2% | -33,1 | 13 | 77% | 7.734 · -98,3 · -0,04 | +134% / +54% | – | sì | 0,0050 | 0,385 | sì/no |
| ETH | 2020-06-01 | 30.796 | 19,0% | -28,2 | 12 | 58% | 72.266 · -79,3 · 0,45 | +57% / +83% | 3 | sì | 0,0205 | 1,000 | sì/sì |
| ADA | 2020-06-01 | 51.887 | 28,9% | -48,5 | 14 | 64% | 19.486 · -95,2 · 0,11 | +239% / +37% | 2 | sì | 0,0115 | 0,862 | sì/sì |
| QTUM (fuori nucleo) | 2020-06-08 | 21.835 | 12,8% | -24,8 | 16 | 69% | 3.445 · -97,8 · -0,16 | +84% / +8% | – | sì | 0,0275 | 1,000 | sì/sì |
| DOGE | 2020-10-26 | 35.168 | 23,0% | -55,2 | 20 | 50% | 207.694 · -92,3 · 0,70 | +120% / +71% | 1,2,3 | no | 0,0615 | 1,000 | sì/sì |
| EOS | 2020-06-01 | 18.668 | 10,1% | -25,1 | 12 | 58% | 244 · -99,6 · -0,44 | +29% / +53% | 3 | sì | 0,0320 | 1,000 | sì/sì |
| BCH | 2020-06-01 | 23.196 | 13,9% | -43,0 | 16 | 56% | 8.250 · -94,2 · -0,03 | +66% / +36% | 2,3 | sì | 0,0270 | 1,000 | sì/sì |
| AVAX | 2021-06-28 | 14.870 | 7,6% | -38,9 | 11 | 55% | 5.981 · -95,6 · -0,09 | +36% / +6% | 2,3 | no | 0,1359 | 1,000 | sì/sì |
| NEAR | 2021-07-19 | 13.496 | 5,8% | -49,7 | 11 | 55% | 15.087 · -95,2 · 0,08 | +25% / +11% | 2,3 | no | 0,0940 | 1,000 | sì/sì |
| XTZ | 2020-06-29 | 11.445 | 2,1% | -53,8 | 9 | 67% | 897 · -97,8 · -0,32 | +37% / -26% | 2,4 | no | 0,1349 | 1,000 | sì/sì |
| LINK | 2020-06-01 | 10.319 | 0,5% | -41,1 | 15 | 40% | 21.359 · -90,2 · 0,14 | +30% / -24% | 1,2,3,4 | no | 0,3003 | 1,000 | sì/sì |
| LTC | 2020-06-01 | 9.718 | -0,4% | -67,7 | 14 | 36% | 8.929 · -89,7 · -0,02 | +153% / -62% | 2,3,4 | no | 0,2759 | 1,000 | sì/sì |
| NEO | 2020-06-01 | 9.631 | -0,6% | -44,8 | 12 | 58% | 1.382 · -98,8 · -0,27 | +2% / -12% | 2,3,4 | no | 0,3788 | 1,000 | sì/sì |
| XRP | 2020-06-01 | 8.359 | -2,7% | -56,8 | 19 | 37% | 45.522 · -83,2 · 0,32 | +10% / -24% | 1,2,3,4 | no | 0,2859 | 1,000 | sì/sì |
| XLM | 2020-06-01 | 7.243 | -4,9% | -63,5 | 16 | 31% | 17.561 · -90,3 · 0,10 | +70% / -59% | 1,2,3,4 | no | 0,3143 | 1,000 | sì/sì |
| XMR | 2020-06-01 | 6.234 | -7,0% | -63,2 | 18 | 22% | 74.793 · -78,4 · 0,46 | +4% / -40% | 1,2,3,4 | no | 0,6897 | 1,000 | sì/no |
| ETC | 2020-06-01 | 7.546 | -4,3% | -36,0 | 8 | 50% | 8.268 · -95,9 · -0,03 | -13% / -18% | 1,2,3,4 | no | 0,4883 | 1,000 | sì/sì |
| ATOM | 2020-06-01 | 6.446 | -6,6% | -42,9 | 8 | 12% | 4.564 · -97,4 · -0,12 | -33% / -7% | 1,2,3,4 | no | 0,7576 | 1,000 | sì/sì |

- BTC (cancello) dal 2020-06-01: 17 operazioni; domeniche con cancello long/short/flat: 142/73/163
- altcoin valutabili 78 · passano 1-5 7 · conferma 7 · davvero 1
- mediane Q4: finale 12386, DD -38.8, WR 50, trade 11, CAGR/DD 0.13
- mediane Q1 stesse monete: finale 10381, DD -56.2, WR 40, trade 22, CAGR/DD 0.01
- operazioni Q1 delle altcoin con BTC nello stesso verso alla domenica del segnale: 680/1690 (40%)
- Q4: settimane in posizione con BTC nello stesso verso (mediana per moneta) 86%
Limite dichiarato: il cancello non aggiunge momenti nuovi; per costruzione l'altcoin è quasi sempre nello stesso verso di BTC
(TRX 84% delle settimane in posizione, 0% opposto).

## Q5 · parametri per classe (scelta sul solo IS)
```
[altcoin] griglia (mediane di classe; IS su 66 asset, OOS su 78):
  k    r  n_is  is_cd_med  is_dd_med  oos_cd_med  oos_dd_med  oos_15
2.0 0.10    66       0.44     -18.75       -0.07      -30.70       2
2.0 0.15    66       0.45     -26.80       -0.10      -42.70       2
2.0 0.25    66       0.42     -40.90       -0.15      -61.05       2
2.5 0.10    66       0.41     -15.40       -0.07      -25.20       3
2.5 0.15    66       0.39     -21.90       -0.09      -35.35       3
2.5 0.25    66       0.35     -33.55       -0.15      -51.65       3
3.0 0.10    66       0.48     -13.45       -0.06      -21.95       2
3.0 0.15    66       0.48     -19.00       -0.07      -31.10       2
3.0 0.25    66       0.48     -28.30       -0.11      -46.10       2
[altcoin] SCELTA IS: trailing 3.0 ATRw, rischio 0.25 (mediana IS CAGR/DD 0.48, DD -28.3) · OOS: mediana CAGR/DD -0.11 contro -0.15 dei parametri di BTC; passano 1–5 in OOS 2 contro 3 → NON migliora · passano davvero in OOS 0: [] · passano 1–5 OOS: ['ETH', 'STX']
[altcoin] a posteriori (NON utilizzabile): cella OOS migliore 3.0/0.1, mediana CAGR/DD -0.06

[azioni] griglia (mediane di classe; IS su 123 asset, OOS su 124):
  k    r  n_is  is_cd_med  is_dd_med  oos_cd_med  oos_dd_med  oos_15
2.0 0.10   123      -0.14      -31.2        0.04      -31.10       2
2.0 0.15   123      -0.18      -38.6        0.04      -35.75       2
2.0 0.25   123      -0.20      -41.2        0.03      -37.35       2
2.5 0.10   123      -0.11      -28.4        0.04      -28.65       1
2.5 0.15   123      -0.14      -36.7        0.01      -35.50       1
2.5 0.25   123      -0.18      -42.2        0.00      -38.05       1
3.0 0.10   123      -0.11      -24.7        0.06      -25.65       2
3.0 0.15   123      -0.15      -32.9        0.03      -33.10       2
3.0 0.25   123      -0.21      -40.8        0.00      -37.85       2
[azioni] SCELTA IS: trailing 2.5 ATRw, rischio 0.1 (mediana IS CAGR/DD -0.11, DD -28.4) · OOS: mediana CAGR/DD 0.04 contro 0.01 dei parametri di BTC; passano 1–5 in OOS 1 contro 1 → NON migliora · passano davvero in OOS 0: [] · passano 1–5 OOS: ['SAP.DE']
[azioni] a posteriori (NON utilizzabile): cella OOS migliore 3.0/0.1, mediana CAGR/DD 0.06
```
Mediane di classe; `oos_15` = asset che passano i criteri 1–5 sul solo OOS. Il CAGR/DD quasi non cambia con il rischio (lezione 101): la scelta fra le righe a 3,0 ATRw si decide al quarto decimale. Il DD sì: per le altcoin il rischio 10% porta il DD mediano OOS da −52% a −25%, ma il rendimento scende con lui.

## Q6 · portafoglio (capitali uguali e separati)
| Dal | Portafoglio | Finale | CAGR | DD | CAGR/DD | Trade | Trade/anno |
|---|---|---|---|---|---|---|---|
| 2020-06-01 | BTC solo (BTC) | 225.069 | 61.7% | -21.1 | 2.92 | 17 | 2.6 |
| 2020-06-01 | BTC + ETH (BTC+ETH) | 139.232 | 50.1% | -20.6 | 2.44 | 33 | 5.1 |
| 2020-06-01 | BTC + ETH + candidati (BTC+ETH+TRX(q4)) | 121.887 | 47.1% | -18.9 | 2.49 | 45 | 6.9 |
| 2021-01-01 | BTC solo (BTC) | 84.820 | 43.7% | -21.1 | 2.07 | 14 | 2.4 |
| 2021-01-01 | BTC + ETH (BTC+ETH) | 62.196 | 36.4% | -20.2 | 1.8 | 29 | 4.9 |
| 2021-01-01 | BTC + ETH + candidati (BTC+ETH+TRX(q4)) | 68.913 | 38.7% | -18.2 | 2.13 | 39 | 6.6 |

Unico candidato operabile che passa davvero: TRX con il cancello di BTC (Q4). Migliora CAGR/DD e DD in entrambi i periodi, ma
rende meno di BTC da solo (dal 2021 68.913 $ contro 84.820 $): diversifica poco (84% delle settimane nello stesso verso di BTC).

## Q7 · SOL e TAO, in parole semplici
**In breve.** SOL con W3.2 avrebbe guadagnato bene fino al 2023, ma con oscillazioni del conto che la regola di W3.2 non accetta
(−40% al rischio 25%) e vincendo meno di un'operazione su due; dal 2024 a oggi avrebbe perso il 10%. TAO, con poco più di due anni
di storia, avrebbe perso il 35%. Nessuna delle due passa i criteri: **non vanno aggiunte a W3.2**. Non ho chiesto come le operavi:
il confronto è con il buy & hold e con BTC, ed è probabile che i buoni ricordi vengano dai grandi rialzi del 2021 e del 2023–24, in
cui qualunque strategia long su SOL guadagnava molto.

### SOL (versione completa dall'11/01/2021, 5,9 anni)
| Rischio allo stop | Finale da 10.000 $ | CAGR | DD | Trade | WR | CAGR/DD | Senza il trade migliore |
|---|---|---|---|---|---|---|---|
| 10% | 29.611 | 20,3% | −20,2 | 23 | 48% | 1,01 | 16.742 |
| 15% | 43.917 | 28,7% | −27,3 | 23 | 48% | 1,05 | 20.399 |
| 25% (come BTC/ETH) | 80.661 | 42,7% | −39,8 | 23 | 48% | 1,07 | 27.607 |
| Buy & hold SOL | 201.456 | 66,8% | −96,3 | – | – | 0,69 | – |
| BTC W3.2, stesso periodo | 84.820 | 43,7% | −21,1 | 14 | 93% | 2,08 | – |

Per anno (rischio 25%): 2021 +251% · 2022 +4% · 2023 +147% · 2024 +10% · 2025 −28% · 2026 +13%. IS 2021–22 +266%, OOS 2023→
+121%; dal 01/01/2024 −10% (DD −40%), mentre BTC con W3.2 fa +154% e il buy & hold di SOL −37%.

**Da dove vengono guadagni e perdite.** Tre operazioni long fanno tutto il risultato: aprile–maggio 2021 (+77%), agosto–settembre
2021 (+70%) e ottobre 2023–gennaio 2024 (+192%, da 24 a 102 $). Senza la migliore il conto finisce a 27.607 $. Le perdite sono
tante e piccole-medie: false ripartenze long in cui il prezzo torna sotto la media a 21 settimane dopo 2–4 settimane (−17% a
07/2024, −17% a 01/2025, cinque long in fila tutti in perdita nel 2025 per −42 punti). Gli short guadagnano poco (8 short, 5 vinti,
+24% il migliore nel 2025–26). SOL si muove circa il doppio di BTC: lo stop a 2,5 ATR settimanali è lontano, quindi l'esposizione è
più bassa (0,4–0,8 del capitale) e ogni falso segnale costa di più in rapporto al guadagno.

**Con quale rischio sarebbe accettabile.** Il CAGR/DD resta ~1,0 a qualunque rischio (metà di BTC, 2,08): abbassare il rischio
riduce il DD (−20% al 10%) ma non migliora la qualità. Il WR del 48% e la dipendenza da 3 operazioni non cambiano. Anche con il
cancello di BTC (solo nel verso di W3.2 su BTC): 52.037 $, DD −40,1%, WR 60%, placebo non significativo (p 0,023).

**Segnale attuale.** Short dal 09/11/2026 a 86,45 $ (ultimo 69,69 $, +13,2% sul capitale), trailing a 101,5 $; prezzo sotto la SMA
40 settimane (87,3) e la EMA 21 (92,6), flusso perp negativo. Con il cancello di BTC lo short sarebbe entrato il 16/11 a 72,70 $.

**Avrebbe senso operarla con W3.2?** No, alle regole attuali. L'unica condizione in cui la considererei: capitale separato piccolo,
rischio 10% (DD storico −20%), sapendo che vince meno di una volta su due, che negli ultimi tre anni non ha guadagnato e che il
placebo non è significativo dopo Holm (p 0,0115). Il risultato atteso è inferiore a quello che lo stesso capitale fa su BTC o ETH.

Operazioni di SOL (rischio 25%):

| Segnale | Ingresso | Verso | Prezzo in | Esposizione | Uscita | Prezzo out | Motivo | Mossa del prezzo | Risultato sul capitale |
|---|---|---|---|---|---|---|---|---|---|
| 2021-01-17 | 2021-01-18 | long | 3.83 | 0.43 | 2021-02-01 | 4.25 | distribuzione (funding e flusso perp) | +11.0% | +4.7% |
| 2021-04-04 | 2021-04-05 | long | 23.8 | 0.80 | 2021-05-17 | 46.8 | distribuzione (funding e flusso perp) | +96.7% | +77.4% |
| 2021-08-22 | 2021-08-23 | long | 72.82 | 0.65 | 2021-09-13 | 151.31 | trailing 2,5 ATR settimanali | +107.8% | +69.9% |
| 2021-10-03 | 2021-10-04 | long | 173.16 | 0.68 | 2021-10-25 | 201.95 | distribuzione (funding e flusso perp) | +16.6% | +11.2% |
| 2022-04-03 | 2022-04-04 | long | 137.04 | 0.44 | 2022-04-11 | 110.95 | chiusura settimanale oltre la EMA 21 | -19.0% | -8.5% |
| 2022-08-21 | 2022-08-22 | short | 36.44 | 0.22 | 2022-11-14 | 13.19 | distribuzione (funding e flusso perp) | +63.8% | +11.0% |
| 2022-12-18 | 2022-12-19 | short | 12.37 | 0.14 | 2023-01-02 | 10 | distribuzione (funding e flusso perp) | +19.2% | +2.4% |
| 2023-02-05 | 2023-02-06 | short | 23.44 | 0.33 | 2023-02-20 | 24.85 | chiusura settimanale oltre la EMA 21 | -6.0% | -2.0% |
| 2023-02-26 | 2023-02-27 | short | 23.23 | 0.34 | 2023-04-17 | 25.37 | chiusura settimanale oltre la EMA 21 | -9.2% | -3.0% |
| 2023-04-23 | 2023-04-24 | short | 21.45 | 0.39 | 2023-07-10 | 21.34 | chiusura settimanale oltre la EMA 21 | +0.5% | +0.5% |
| 2023-07-16 | 2023-07-17 | long | 27.44 | 0.56 | 2023-08-21 | 21.76 | chiusura settimanale oltre la EMA 21 | -20.7% | -11.7% |
| 2023-10-01 | 2023-10-02 | long | 23.9 | 0.59 | 2024-01-01 | 101.62 | distribuzione (funding e flusso perp) | +325.2% | +192.1% |
| 2024-07-21 | 2024-07-22 | long | 184.67 | 0.67 | 2024-08-05 | 138.18 | chiusura settimanale oltre la EMA 21 | -25.2% | -16.9% |
| 2024-09-22 | 2024-09-23 | long | 144.78 | 0.52 | 2024-12-09 | 236.78 | distribuzione (funding e flusso perp) | +63.5% | +32.6% |
| 2025-01-19 | 2025-01-20 | long | 252.65 | 0.64 | 2025-02-17 | 188.07 | chiusura settimanale oltre la EMA 21 | -25.6% | -16.6% |
| 2025-05-11 | 2025-05-12 | long | 173.37 | 0.52 | 2025-06-02 | 157.52 | chiusura settimanale oltre la EMA 21 | -9.1% | -4.8% |
| 2025-07-20 | 2025-07-21 | long | 181.62 | 0.63 | 2025-08-04 | 161.82 | chiusura settimanale oltre la EMA 21 | -10.9% | -7.0% |
| 2025-08-31 | 2025-09-01 | long | 200.82 | 0.66 | 2025-10-10 | 171.89 | trailing 2,5 ATR settimanali | -14.4% | -9.6% |
| 2025-10-26 | 2025-10-27 | long | 200.23 | 0.59 | 2025-11-03 | 187.52 | chiusura settimanale oltre la EMA 21 | -6.3% | -3.9% |
| 2025-11-09 | 2025-11-10 | short | 164.37 | 0.48 | 2026-03-30 | 81.53 | distribuzione (funding e flusso perp) | +50.4% | +24.2% |
| 2026-04-05 | 2026-04-06 | short | 81.81 | 0.41 | 2026-08-21 | 90.49 | trailing 2,5 ATR settimanali | -10.6% | -4.3% |
| 2026-08-30 | 2026-08-31 | long | 101.85 | 0.79 | 2026-11-02 | 94.45 | chiusura settimanale oltre la EMA 21 | -7.3% | -5.9% |
| 2026-11-08 | 2026-11-09 | short | 86.45 | 0.69 | aperta | 69.69 | posizione aperta | +19.4% | +13.2% |

### TAO (versione completa dal 29/07/2024, 2,3 anni: solo descrittivo)
| Rischio | Finale | CAGR | DD | Trade | WR | Senza il migliore |
|---|---|---|---|---|---|---|
| 10% | 8.574 | −6,4% | −24,7 | 14 | 21% | 7.912 |
| 15% | 7.870 | −9,8% | −35,0 | 14 | 21% | 6.992 |
| 25% | 6.512 | −16,9% | −52,2 | 14 | 21% | 5.384 |
| Buy & hold TAO | 5.383 | −23,4% | −79,5 | – | – | – |
| BTC W3.2, stesso periodo | 17.849 | – | −21,1 | 6 | 83% | – |

Metà 07/2024–09/2025 +24%, 09/2025–11/2026 −49%. Vince solo 3 operazioni su 14 (long 09–12/2024 +21%, short 02–04/2025 +8%,
short 11/2025–02/2026 +14%); le altre 11 escono dopo 1–8 settimane per chiusura oltre la EMA 21: il prezzo di TAO attraversa la media
continuamente e W3.2 entra e esce in perdita (2026: −35%). **Segnale attuale**: flat; prezzo 190,7 $ sotto SMA 40 (242) ed EMA 21
(239) ma flusso perp positivo (+1,38): nessun ingresso short. **Non operarla con W3.2.**

Operazioni di TAO (rischio 25%):

| Segnale | Ingresso | Verso | Prezzo in | Esposizione | Uscita | Prezzo out | Motivo | Mossa del prezzo | Risultato sul capitale |
|---|---|---|---|---|---|---|---|---|---|
| 2024-09-22 | 2024-09-23 | long | 470.27 | 0.41 | 2024-12-09 | 712.19 | distribuzione (funding e flusso perp) | +51.4% | +20.9% |
| 2025-02-09 | 2025-02-10 | short | 365.03 | 0.25 | 2025-04-14 | 240.24 | distribuzione (funding e flusso perp) | +34.2% | +8.3% |
| 2025-05-11 | 2025-05-12 | long | 459.26 | 0.41 | 2025-06-16 | 366.73 | chiusura settimanale oltre la EMA 21 | -20.1% | -8.4% |
| 2025-08-03 | 2025-08-04 | short | 349.45 | 0.37 | 2025-08-11 | 389.29 | chiusura settimanale oltre la EMA 21 | -11.4% | -4.2% |
| 2025-08-17 | 2025-08-18 | short | 372.73 | 0.42 | 2025-10-13 | 383.78 | chiusura settimanale oltre la EMA 21 | -3.0% | -1.0% |
| 2025-11-02 | 2025-11-03 | long | 489.19 | 0.53 | 2025-11-17 | 320.18 | chiusura settimanale oltre la EMA 21 | -34.5% | -18.5% |
| 2025-11-23 | 2025-11-24 | short | 297.4 | 0.32 | 2026-02-09 | 163.36 | distribuzione (funding e flusso perp) | +45.1% | +14.0% |
| 2026-03-29 | 2026-03-30 | long | 315.82 | 0.45 | 2026-04-13 | 259.04 | chiusura settimanale oltre la EMA 21 | -18.0% | -8.2% |
| 2026-04-26 | 2026-04-27 | short | 250.95 | 0.39 | 2026-05-04 | 289.69 | chiusura settimanale oltre la EMA 21 | -15.4% | -6.1% |
| 2026-05-10 | 2026-05-11 | long | 320.82 | 0.51 | 2026-05-18 | 262.84 | chiusura settimanale oltre la EMA 21 | -18.1% | -9.4% |
| 2026-05-31 | 2026-06-01 | short | 255.44 | 0.42 | 2026-06-15 | 271.07 | chiusura settimanale oltre la EMA 21 | -6.1% | -2.6% |
| 2026-06-28 | 2026-06-29 | short | 205.09 | 0.33 | 2026-08-24 | 237.84 | chiusura settimanale oltre la EMA 21 | -16.0% | -5.1% |
| 2026-08-30 | 2026-08-31 | short | 227.37 | 0.51 | 2026-09-07 | 266.07 | chiusura settimanale oltre la EMA 21 | -17.0% | -8.6% |
| 2026-09-13 | 2026-09-14 | short | 231.37 | 0.50 | 2026-09-21 | 261.86 | chiusura settimanale oltre la EMA 21 | -13.2% | -6.6% |


## Q8 · screener all'indietro (ogni 1° gennaio, dal 2022)
| Anno | Idonee | Scelte (risultato dell'anno) | Screener | BTC + ETH | Tutte le idonee | Solo BTC |
|---|---|---|---|---|---|---|
| 2022 | 44 | nessuna | +0.0% (DD 0.0) | +7.7% (DD -12.8) | +7.4% (DD -4.1) | +19.4% (DD -13.4) |
| 2023 | 65 | BTC (+30%), LINK (-6%), ADA (+23%), BCH (-38%), LTC (-40%), SNX (-40%) | -11.9% (DD -30.4) | +22.2% (DD -24.5) | +3.2% (DD -14.3) | +30.4% (DD -27.0) |
| 2024 | 78 | BTC (+103%), SOL (+10%), ETH (+28%), RUNE (-9%), IOTA (-10%), ZRX (-46%), WAVES (-23%), REN (-38%) | +2.0% (DD -21.9) | +65.7% (DD -14.4) | +1.9% (DD -20.5) | +103.1% (DD -11.9) |
| 2025 | 84 | BTC (-3%), SOL (-28%), ETH (-1%) | -10.9% (DD -18.4) | -2.2% (DD -18.6) | -1.4% (DD -8.3) | -3.3% (DD -21.6) |
| 2026 | 100 | BTC (-0%), ETH (+14%) | +6.7% (DD -19.3) | +6.7% (DD -19.3) | +0.6% (DD -10.3) | -0.2% (DD -18.3) |

```
Conto composto 2022-01-01 → 2026-11-24 (ripartenza da flat ogni 1° gennaio):
  screener              8535 $, CAGR  -3.2%, DD -30.4%, CAGR/DD -0.10
  BTC + ETH            22762 $, CAGR  18.3%, DD -25.7%, CAGR/DD 0.71
  tutte le idonee      11198 $, CAGR   2.3%, DD -20.5%, CAGR/DD 0.11
  solo BTC             30519 $, CAGR  25.6%, DD -28.0%, CAGR/DD 0.92
```

Per anno lo screener sceglie da 0 (2022: sulla storia di 1,6 anni nessuna delle 44 idonee passa insieme i criteri 1, 2, 3 e 5) a 8 asset; a parte BTC ed ETH, le scelte
perdono quasi sempre l'anno dopo (2023: BCH −38%, LTC −40%, SNX −40%; 2024: ZRX −46%, REN −38%, WAVES −23%). Dal 2022 il conto
screener chiude a 8.535 $ contro 22.762 $ di BTC + ETH e 11.198 $ di "tutte le idonee". I risultati **non giustificano** uno
screener che sceglie dove mettere capitale.

### Proposta: "motore di ricerca settimanale" (progetto, nulla da costruire ora)
**Cosa calcolerebbe ogni domenica** (dopo la chiusura UTC, stesso giro di W3.2): per ogni perp USDT con storia ≥ 1 anno sulle liste
Bitget/OKX (oggi ~140 crypto con dati Binance; azioni escluse da Q3): le condizioni di W3.2 alla candela chiusa (regime SMA 40/EMA 20,
lato della EMA 21, flusso perp pf14z a 3 giorni, filtro MACD, distribuzione), lo stato di BTC (cancello di Q4), la posizione
simulata, e la scheda storica dell'asset con W3.2 dal suo inizio: CAGR/DD contro il buy & hold, DD, WR, trade, p del placebo.
**Criteri** (gli stessi di questo studio, fissi): 1 CAGR/DD > B&H · 2 DD ≥ −35% · 3 WR ≥ 60% · 4 IS e OOS positivi · 5 ≥ 8 trade,
più conferma e placebo con Holm sul numero di asset nella lista. Un asset "candidato" produce solo un avviso di revisione, mai
un'operazione.
**Cosa mostrerebbe**: una tabella "Asset in condizione W3.2 questa settimana" (lato, nuovo segnale sì/no, concordanza con BTC) e una
"scheda qualità" ordinata per CAGR/DD storico con i criteri superati; in evidenza BTC, ETH e gli eventuali candidati approvati.
**Costo in dati**: archivio pubblico `data.binance.vision` (klines giornaliere spot e perp con taker buy, funding) per ~140 simboli:
~420 file al giorno da pochi kB (~3–5 MB a settimana), scaricabili anche dal runner USA (l'archivio non è bloccato come fapi);
liste strumenti Bitget/OKX una volta a settimana. Calcolo: ~140 simulazioni W3.2 + placebo ≈ 1–2 minuti. Nessun costo monetario.
**Se i risultati lo giustificano**: no per la scelta degli asset (Q8 negativo, Q1–Q5 danno un solo candidato in 79). Al massimo una
pagina informativa di sola lettura ("chi è in condizione W3.2"), utile come contesto e per accumulare un registro dal vivo; da
decidere con l'utente, nessuna modifica al tool senza approvazione.


## Cosa dicono i dati
1. Fuori da BTC ed ETH il problema resta il **drawdown**: le altcoin valutabili hanno DD mediano −56% e WR mediano 40%; battono il
   buy & hold in CAGR/DD (64 su 78) solo perché i buy & hold crollano (finale mediano 2.096 $). Il ciclo 1 (lezione 111) è confermato
   su un universo tre volte più grande, dal 2020 e senza bias di sopravvivenza.
2. Senza bias di sopravvivenza (top 200 del 2020) va peggio: 0 su 54, e il conto equipesato perde 3.600 $ rispetto a quello costruito
   con la classifica di oggi.
3. Sulle azioni W3.2 non funziona nemmeno con un flusso dai volumi: `cmf20` lascia i risultati dove sono (lezioni 104 e 110).
4. Il cancello di BTC è l'unica idea nuova che sposta i numeri: dimezza i trade, alza il WR mediano da 40% a 50% e porta il DD
   mediano da −56% a −39%. Basta per un solo asset (TRX).
5. Cambiare trailing e rischio per classe non aiuta: il CAGR/DD non dipende dal rischio (lezione 101) e la cella migliore in IS
   non è la migliore in OOS.
6. Scegliere ogni anno "chi è andato bene" (Q8) peggiora: le altcoin con un buon passato (BCH, LTC, SNX nel 2023; ZRX, REN, WAVES
   nel 2024) perdono 23–46% l'anno dopo.

## Cosa significa per l'operatività
- **Nessun asset si aggiunge automaticamente.** BTC ed ETH restano come sono.
- **TRX con il cancello di BTC: da approfondire, non da promuovere** (revisione critica). Statisticamente solido (placebo 0 su
  20.000, anche vincolato al cancello; trade ricalcolati a mano: coincidono; nessuno sguardo al futuro), ma l'80% del guadagno
  viene da 2 trade (senza i due migliori 17.017 $, ≈ 8,6% l'anno) e dal 06/2020 ripesare BTC/ETH fa meglio. Non è un BTC a leva:
  TRX che segue solo il cancello a 1x fa DD −49%; i segnali propri di TRX dimezzano il DD (correlazione giornaliera con BTC 0,11).
  Proposta: **osservazione sulla carta per 6–12 mesi** con le regole fissate ora; solo dopo, e solo con una decisione esplicita
  dell'utente, una quota ridotta (circa 1/6 del capitale crypto), senza cambiare BTC ed ETH.
- **Peso BTC/ETH**: dal 06/2020 BTC 2/3 – ETH 1/3 ha CAGR/DD 2,62 contro 2,44 del 50/50 attuale. Non è stato preregistrato come
  domanda: è un'indicazione da studiare a parte, non una regola.
- **SOL e TAO: no** con W3.2 (sezione Q7). **Azioni: no** (Q3). **Screener: no** per ora (Q8); al più una pagina informativa.

## Limiti
- **Bias di sopravvivenza**: l'universo di oggi esclude le monete morte; quello del 2020 le include, ma 101 su 191 non hanno dati
  operabili e restano fuori (non sostituite). Anche Q8 usa un universo che contiene la classifica di oggi (sguardo al futuro nella
  scelta dell'universo, non nelle regole).
- **Classifica 2020 da una sola fonte** (istantanea CoinMarketCap 29/12/2019 via Common Crawl; controlli con CMC 05/01/2020 e
  CoinGecko 24/01/2020); per le azioni CompaniesMarketcap (fine 2019).
- **Perp su azioni solo dal 2026** (≤ 10 mesi): lo studio azioni è sui titoli in borsa, in valuta locale, con short al 3% annuo
  (stima prudente; funding osservato ≈ +1%).
- **Costi stimati**: crypto come W3.2 (0,1%/0,05% per lato, slippage 0,1%, funding reale; novembre 2026 da OKX), azioni 0,05% per
  lato; B&H 0,2% (crypto) e 0,05% (azioni) per lato.
- **Placebo a 2.000 prove**: il p minimo è 0,0005; con Holm su 79 asset la soglia del primo è 0,00063, quindi passa solo chi ha il
  p minimo. Con questa regola nemmeno BTC passerebbe (p 0,0015, Holm 0,12): la severità dichiarata nel PREREG pesa molto.
- La versione completa non parte prima del 01/06/2020 (archivio perp dal 01/2020).
- **TRX**: uscita del 04/12/2024 in un crollo intraday (minimo 0,322): con esecuzione a 0,33 il finale sarebbe 72.414 $. Liquidità:
  perp TRX su OKX ampio (spread 1 tick, ≈ 7,4 M$ in 24 ore); su Bitget ≈ 0,5 M$ in 24 ore; i long si eseguono in spot.
- **Prezzi sotto 1 $ nelle tabelle dei trade**: `entry_px`/`exit_px` di `simulate` sono arrotondati a 0,01, quindi per TRX la
  colonna `move` è falsa (trade 01/2022: +5,4% invece di −0,3%). I P&L sono corretti; non usare `move` né i prezzi di TRX da quei campi.

## Revisione critica (agente separato, sola lettura)
Nessun errore bloccante. Quattro trade di TRX con il cancello ricalcolati a mano (i due migliori, uno short, un perdente): P&L
identici; cancello letto alla domenica, senza sguardo al futuro. Placebo rifatto con 20.000 prove, libero e vincolato ai giorni in
cui BTC è nello stesso verso: 0 prove sopra il reale in entrambi. TRX per periodo: IS 2020–22 14.988 $ (DD −6,7%, CAGR/DD 2,53),
OOS 2023→ 58.178 $ (DD −22,5%, 2,54); altre date di partenza tutte sopra 69.000 $; trailing 2,0/2,25/2,75/3,0: 39.032 / 98.024 /
76.336 / 70.503 $; rischio 15/20/30%: 50.067 / 70.430 / 96.285 $. Portafoglio (CAGR/DD) dal 06/2020 · 2021 · 2023: BTC+ETH 50/50
2,44 · 1,80 · 1,13; con TRX a un terzo 2,49 · 2,13 · 2,24; BTC 2/3 – ETH 1/3 2,62 · 1,90 · 1,21; BTC 50 / ETH 33 / TRX 17 2,60 ·
2,04 · 1,70. SOL e TAO: segnali attuali corretti (SOL short dal 09/11, trailing 101,51; TAO flat). Q8: nessuno sguardo al futuro
nelle scelte; l'universo con le sopravvissute gonfia lo screener, quindi "non giustificato" vale a maggior ragione. Secondo ciclo
sconsigliato (nessun errore del motore; un'ipotesi in più aumenterebbe solo la molteplicità): non eseguito.

## Deviazioni dal PREREG (dichiarate)
1. IS/OOS: per gli asset con IS o OOS < 6 mesi (inizio dopo il 30/06/2022 o serie finita prima del 30/06/2023) si usano le due metà
   del periodo (come w32_top100).
2. Placebo: durate in sedute dell'indice (per le crypto = giorni; per le azioni evita di contare i giorni di borsa chiusa); CAGR
   annualizzato sugli anni di calendario.
3. Q5: CAGR/DD **non arrotondato** per la scelta della cella (arrotondato a 2 decimali dava mediane a pari merito: altcoin
   3,0/0,10–0,25 tutte 0,48). Per le azioni la scelta (2,5/0,10, mediana −0,1065) è quasi a pari merito con 3,0/0,10 (−0,1078),
   che avrebbe dato formalmente "migliora" (OOS 0,06 contro 0,01; 2 titoli contro 1: Saudi Aramco, non operabile, e Netflix, p 0,019,
   non significativo con Holm); nessun asset passa davvero in nessuna delle due. In OOS: criterio 4 = rendimento OOS positivo,
   criterio 5 = ≥ 8 trade nell'OOS, vicini = gli altri due trailing allo stesso rischio. Classe IS = valutabili con IS ≥ 6 mesi (66
   altcoin, 123 azioni). Azioni in solo prezzo perché `cmf20` non passa su nessun titolo.
4. Q4: BTC "in posizione" alla domenica = entrata ≤ domenica < uscita (un'uscita decisa quella domenica conta ancora); nei vicini
   (2,0/3,0) cambia solo il trailing dell'altcoin, BTC resta a 2,5.
5. Q8: idonee = classi "valutabile" e "breve" con versione completa iniziata prima del 1° gennaio, serie viva e primo prezzo ≥ 2
   anni prima (la classe finale non si usa perché dipende dal futuro); BTC è fra le idonee; ogni anno si riparte da flat il 1°
   gennaio, anche per BTC + ETH e "tutte le idonee".
6. Crypto solo prezzo: inizio = max(01/06/2020, primo dato + 300 giorni). Brevi simulate solo con ≥ 180 giorni di test (54 su 74).
7. Azioni: fine = ultimo dato (24–25/11/2026); l'eventuale settimana incompleta finale produce solo una decisione in sospeso.

## Lezione 123 proposta per RESEARCH.md
**Lezione 123**: W3.2 su 79 crypto valutabili (top 200 di oggi e del 2020, dal 06/2020) e 124 azioni (top 100 di oggi e del 2019,
dal 2020): con i parametri di BTC nessuna altcoin passa criteri, conferma e placebo con Holm (ETH e STX passano 1–5 ma non Holm su 79);
top 200 del 2020 0 su 54; azioni 0 su 124 anche con il flusso Chaikin 20 sedute. Il cancello "solo nel verso di W3.2 su BTC" porta
il DD mediano delle altcoin da −56% a −39% e fa passare solo TRX (87,2k $, DD −22,5%, WR 83%, 12 trade, p 0,0005; due trade fanno
quasi tutto: senza i due migliori 17,0k $); BTC + ETH + TRX: CAGR/DD 2,13 contro 1,80 dal 2021, ma dal 06/2020 il semplice
ripeso BTC 2/3 – ETH 1/3 fa meglio (2,62). Il placebo e Holm non proteggono dalla concentrazione su 1–2 movimenti: nei prossimi
studi servono sempre "senza i due migliori" e il confronto con il ripeso dei capitali già in uso, e 20.000 prove di placebo
quando Holm è su più di 20 asset. Trailing e rischio per classe non migliorano in OOS. Uno screener
annuale "chi ha passato i criteri" perde contro BTC + ETH (8,5k contro 22,8k dal 2022). SOL (DD −40%, WR 48%, −10% dal 2024) e TAO
(−35%) non vanno operati con W3.2. research/w32_asset2/README.md (PREREG f40f7a6).

## File
Nota: questo README è stato corretto a mano dopo la revisione critica; `build_readme.py` lo riscriverebbe dalla bozza.
`lib.py` (motore comune), `checks.py` → `out_checks.txt`; `run_crypto.py` → `risultati_crypto.csv`, `trades_crypto.csv`,
`eq_crypto.csv.gz`; `run_azioni.py` → `risultati_azioni.csv`, `trades_azioni.csv`, `eq_azioni.csv.gz`; `q4.py` → `risultati_q4.csv`,
`out_q4.txt`; `q5.py` (+ `weekly_q5.py`) → `q5_griglia.csv`, `risultati_q5.csv`, `out_q5.txt`; `q6.py` → `risultati_q6.csv`,
`out_q6.txt`; `q7_sol_tao.py` → `out_q7.txt`, `trades_q7.csv`; `q8_screener.py` → `risultati_q8.csv`, `out_q8.txt`; `tabelle.py` →
`out_tabelle.txt`; `build_readme.py` compone questo file. Ordine: checks → run_crypto → run_azioni → q4 → q5 → q6 → q7 → q8 →
tabelle → build_readme (circa 6 minuti con 4 processi).
