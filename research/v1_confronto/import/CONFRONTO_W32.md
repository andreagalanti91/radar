# Confronto con W3.2 del radar · tutte le movimentazioni

Gli algoritmi di analisi tecnica su BTC (v1 a voto, v2 a tre schermi, da [`REGOLE_AT.md`](REGOLE_AT.md)) messi a confronto
con W3.2, la strategia in uso nel repo radar dal 22/11/2026. Dati fino al 22/11/2026.

> Ricerca su dati storici, non una raccomandazione d'investimento.

## 1. Sintesi

**W3.2 è migliore di entrambi gli algoritmi tecnici: rende di più, ha meno drawdown e vince più spesso. La combinazione
metà W3.2 e metà v1 rende quanto W3.2 nel periodo intero, ma non la migliora dal 2021.**

| Dal 01/2018 al 22/11/2026 | W3.2 radar | v1 · voto | v2 · tre schermi | 50% W3.2 + 50% v1 |
|---|---|---|---|---|
| 10.000 $ diventano | 209.002 $ | 184.406 $ | 132.529 $ | 223.979 $ |
| Rendimento annuo | +40,8% | +38,8% | +33,7% | +41,9% |
| Max drawdown | −37,3% | −49,4% | −54,1% | −42,1% |
| Operazioni / vincenti | 23 / 78% | 30 / 47% | 9 / 56% | – |
| Dal 2021: rendimento annuo / drawdown | +43% / −21% | +30% / −34% | +17% / −54% | +38% / −21% |
| Posizione oggi | short dal 16/11 | fuori | fuori | – |

- **W3.2 vince dove conta**: dal 2021, con i dati reali del perp, non ha avuto un anno negativo e ha chiuso in guadagno 13
  operazioni su 14.
- **Gli algoritmi tecnici vincono solo nel 2018–20**, quando W3.2 usa un flusso stimato e parte con una perdita del 25% sulla
  prima operazione.
- **La differenza sta negli short e nelle uscite.** W3.2 ha guadagnato su 6 short su 7 (uno ancora aperto); v1 su 3 su 7; v2
  non ne ha fatti. W3.2 esce dai long quando il funding è alto e il flusso gira, prima che il prezzo scenda.
- **Sono quasi sempre dalla stessa parte**: quando W3.2 è long, v1 lo è nell'88% dei giorni; posizioni opposte solo nello
  0,1% dei giorni. Per questo combinarli aggiunge poco.

![Confronto](results/w32/confronto_w32.png)

## 2. Le regole a confronto

| | W3.2 radar | v1 · voto | v2 · tre schermi |
|---|---|---|---|
| Scala | settimanale | giornaliera | settimanale + giornaliera |
| Trend | chiusura sopra la SMA 40 settimane ed EMA 20 in salita | voto di 17 indicatori | chiusura sopra la SMA 40 settimane e struttura non ribassista |
| Ingresso | chiusura oltre la EMA 21 **e flusso del perp a favore** | voto ≥ 0,50 (long) o ≤ −0,90 (short) | chiusura sopra il massimo a 55 giorni |
| Uscita | trailing 2,5 ATR settimanali, chiusura oltre la EMA 21, **distribuzione (funding alto e flusso contrario)** | voto che rientra oltre ±0,25 | chandelier a 5 ATR giornalieri |
| Dimensione | rischio 25% allo stop: esposizione fra 0,4x e 1x | 1x fisso | 1x fisso |
| Dati usati | prezzo, flusso e funding del perp | solo prezzo e volume | solo prezzo |
| Testabile dal | 2021 con dati reali (2018–20 con flusso stimato) | 2018 | 2018 |

## 3. Risultati

| Strategia | 10.000 $ → (2018–2026) | CAGR | Max DD | Sharpe | Operazioni | Vincenti | 2018–20: CAGR / DD | 2021–23: CAGR / DD | 2024–26: CAGR / DD | Dal 2021: CAGR / DD |
|---|---|---|---|---|---|---|---|---|---|---|
| W3.2 radar (rischio 25%) | 209.002 | +40,8% | -37,3% | 1,25 | 23 | 78% | +36% / -37% | +50% / -19% | +37% / -21% | +43% / -21% |
| v1 · voto di 17 indicatori | 184.406 | +38,8% | -49,4% | 0,95 | 30 | 47% | +58% / -49% | +45% / -32% | +14% / -34% | +30% / -34% |
| v2 · tre schermi | 132.529 | +33,7% | -54,1% | 0,96 | 9 | 56% | +72% / -36% | +8% / -54% | +25% / -23% | +17% / -54% |
| BTC comprato e tenuto | 45.793 | +18,7% | -81,2% | 0,59 | – | – | +29% / -81% | +13% / -77% | +12% / -53% | +13% / -77% |
| 50% W3.2 + 50% v1 | 223.979 | +41,9% | -42,1% | 1,18 | – | – | +49% / -42% | +50% / -20% | +26% / -21% | +38% / -21% |
| 1/3 W3.2 + 1/3 v1 + 1/3 v2 | 203.113 | +40,3% | -39,8% | 1,18 | – | – | +58% / -40% | +36% / -25% | +26% / -18% | +32% / -25% |

Anno per anno:

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| W3.2 radar (rischio 25%) | -10% | +41% | +97% | +92% | +19% | +46% | +103% | +5% | +17% |
| v1 · voto di 17 indicatori | +3% | +61% | +136% | +115% | +3% | +40% | +65% | +16% | -21% |
| v2 · tre schermi | +0% | +77% | +189% | +50% | -19% | +6% | +99% | +1% | +0% |
| BTC comprato e tenuto | -72% | +94% | +302% | +60% | -64% | +156% | +121% | -6% | -30% |
| 50% W3.2 + 50% v1 | -2% | +55% | +119% | +108% | +14% | +44% | +86% | +11% | -3% |
| 1/3 W3.2 + 1/3 v1 + 1/3 v2 | -0% | +63% | +142% | +90% | +2% | +31% | +91% | +8% | -1% |

- **2018–20**: v1 e v2 fanno meglio (+58% e +72% annuo contro +36%). W3.2 perde il 25% sulla prima operazione di gennaio
  2018 e il 18% sullo short di marzo 2020. In questo periodo W3.2 usa un flusso stimato dallo spot, non quello del perp.
- **2021–23**: W3.2 e v1 simili per rendimento (+50% e +45%), ma W3.2 con drawdown −19% contro −32%.
- **2024–26**: W3.2 nettamente avanti (+37% annuo contro +14% e +25%). Nel 2026 W3.2 fa +17%, v1 −21%.

## 4. Quanto si somigliano

| Posizione di W3.2 | Giorni | v1 long | v1 fuori | v1 short | v2 long | v2 fuori |
|---|---|---|---|---|---|---|
| long | 1040 | 88% | 12% | 0% | 77% | 23% |
| fuori | 1512 | 29% | 61% | 11% | 33% | 67% |
| short | 696 | 1% | 68% | 32% | 0% | 100% |

Stessa posizione di W3.2: v1 nel 63% dei giorni, v2 nel 56%. Posizioni opposte (uno long e l'altro short): v1 nel 0,1% dei giorni. Correlazione dei rendimenti mensili con W3.2: v1 0,72, v2 0,71.

- Quando W3.2 è long, gli algoritmi tecnici lo sono quasi sempre. La differenza è nei periodi in cui W3.2 è fuori o short:
  lì v1 resta long nel 29% dei giorni.
- Quando W3.2 è short, v1 è per lo più fuori (68%) e short solo un terzo del tempo: la soglia di v1 per lo short è molto
  severa.

## 5. Movimentazioni di W3.2

Esposizione = quota del capitale impegnata. "Sul capitale" = risultato dopo costi e funding, sull'intero capitale.

| # | Periodo | Verso | Mercato | Segnale | Entra | Esce | Prezzo | Esposizione | Mossa del prezzo | Sul capitale | Uscita | v1 all'ingresso | v2 all'ingresso |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2018–20 | long | spot | 2018-01-07 | 2018-01-08 | 2018-01-16 | 16.235 → 9.654 | 0,62x | -40,5% | -25,1% | trailing 2,5 ATR settimanali | long | fuori |
| 2 | 2018–20 | long | spot | 2018-04-29 | 2018-04-30 | 2018-05-14 | 9.426 → 8.671 | 0,40x | -8,0% | -3,3% | chiusura settimanale oltre la EMA 21 | fuori | fuori |
| 3 | 2018–20 | short | perp | 2018-10-14 | 2018-10-15 | 2019-04-02 | 6.333 → 4.551 | 0,59x | +28,1% | +16,7% | trailing 2,5 ATR settimanali | fuori | fuori |
| 4 | 2018–20 | long | spot | 2019-05-12 | 2019-05-13 | 2019-06-27 | 6.975 → 10.559 | 1,00x | +51,4% | +51,1% | trailing 2,5 ATR settimanali | long | long |
| 5 | 2018–20 | long | spot | 2020-02-09 | 2020-02-10 | 2020-02-17 | 10.162 → 9.901 | 0,93x | -2,6% | -2,6% | distribuzione (funding e flusso) | long | fuori |
| 6 | 2018–20 | short | perp | 2020-03-15 | 2020-03-16 | 2020-04-27 | 5.355 → 7.701 | 0,40x | -43,8% | -17,9% | chiusura settimanale oltre la EMA 21 | fuori | fuori |
| 7 | 2018–20 | long | spot | 2020-05-03 | 2020-05-04 | 2020-08-03 | 8.903 → 11.060 | 0,67x | +24,2% | +16,0% | distribuzione (funding e flusso) | long | fuori |
| 8 | 2018–20 | long | spot | 2020-10-25 | 2020-10-26 | 2020-11-23 | 13.043 → 18.395 | 1,00x | +41,0% | +40,8% | distribuzione (funding e flusso) | long | long |
| 9 | 2018–20 | long | spot | 2020-12-13 | 2020-12-14 | 2020-12-31 | 19.194 → 28.924 | 1,00x | +50,7% | +50,4% | chiusa a fine periodo (cambio di dati al 31/12/2020) | long | long |
| 10 | 2021+ | long | spot | 2021-01-31 | 2021-02-01 | 2021-02-22 | 33.126 → 57.355 | 0,72x | +73,1% | +52,2% | distribuzione (funding e flusso) | long | long |
| 11 | 2021+ | long | spot | 2021-08-01 | 2021-08-02 | 2021-09-27 | 39.890 → 43.118 | 0,54x | +8,1% | +4,3% | chiusura settimanale oltre la EMA 21 | long | fuori |
| 12 | 2021+ | long | spot | 2021-10-03 | 2021-10-04 | 2021-11-08 | 48.248 → 63.210 | 0,68x | +31,0% | +20,9% | distribuzione (funding e flusso) | long | long |
| 13 | 2021+ | short | perp | 2022-01-02 | 2022-01-03 | 2022-03-28 | 47.239 → 46.875 | 0,64x | +0,8% | +1,0% | chiusura settimanale oltre la EMA 21 | fuori | fuori |
| 14 | 2021+ | short | perp | 2022-08-14 | 2022-08-15 | 2023-01-16 | 24.281 → 20.894 | 0,56x | +13,9% | +8,3% | chiusura settimanale oltre la EMA 21 | fuori | fuori |
| 15 | 2021+ | long | spot | 2023-01-22 | 2023-01-23 | 2023-08-17 | 22.729 → 25.966 | 0,94x | +14,2% | +13,3% | trailing 2,5 ATR settimanali | long | fuori |
| 16 | 2021+ | long | spot | 2023-10-22 | 2023-10-23 | 2024-01-01 | 30.022 → 42.241 | 1,00x | +40,7% | +40,5% | distribuzione (funding e flusso) | long | long |
| 17 | 2021+ | long | spot | 2024-02-11 | 2024-02-12 | 2024-03-11 | 48.348 → 68.887 | 1,00x | +42,5% | +42,2% | distribuzione (funding e flusso) | long | long |
| 18 | 2021+ | long | spot | 2024-09-22 | 2024-09-23 | 2025-02-26 | 63.642 → 85.256 | 0,91x | +34,0% | +30,8% | trailing 2,5 ATR settimanali | fuori | fuori |
| 19 | 2021+ | long | spot | 2025-04-27 | 2025-04-28 | 2025-10-10 | 93.843 → 104.715 | 0,99x | +11,6% | +11,3% | trailing 2,5 ATR settimanali | long | fuori |
| 20 | 2021+ | short | perp | 2025-11-30 | 2025-12-01 | 2026-04-27 | 90.270 → 78.736 | 0,89x | +12,8% | +11,9% | chiusura settimanale oltre la EMA 21 | short | fuori |
| 21 | 2021+ | short | perp | 2026-05-24 | 2026-05-25 | 2026-08-20 | 76.988 → 73.287 | 1,00x | +4,8% | +5,7% | trailing 2,5 ATR settimanali | fuori | fuori |
| 22 | 2021+ | long | spot | 2026-08-23 | 2026-08-24 | 2026-11-09 | 77.812 → 74.777 | 1,00x | -3,9% | -4,1% | chiusura settimanale oltre la EMA 21 | long | fuori |
| 23 | 2021+ | short | perp | 2026-11-15 | 2026-11-16 | aperta | 65.286 → 61.271 | 0,97x | +6,1% | +5,9% | aperta | fuori | fuori |

2018–20: 9 operazioni, 56% in guadagno, media +14,0% sul capitale, peggiore -25,1%.

2021+: 14 operazioni, 93% in guadagno, media +17,4% sul capitale, peggiore -4,1%.

## 6. Movimentazioni di v1 (voto di 17 indicatori)

Esposizione sempre 1x. Risultato dopo costi e funding. La prima riga è una posizione già aperta a fine 2017.

| # | Verso | Entra | Esce | Giorni | Prezzo | Risultato | Voto all'ingresso | W3.2 all'ingresso |
|---|---|---|---|---|---|---|---|---|
| 1 | long | 2018-01-01 | 2018-01-16 | 16 | 13.716 → 10.900 | -20,6% | 0,41 | fuori |
| 2 | long | 2018-05-04 | 2018-05-10 | 7 | 9.750 → 9.002 | -7,8% | 0,53 | long |
| 3 | short | 2018-11-19 | 2019-02-18 | 92 | 5.662 → 3.899 | +28,4% | -1,00 | short |
| 4 | long | 2019-04-05 | 2019-07-24 | 111 | 4.899 → 9.763 | +99,1% | 0,53 | fuori |
| 5 | long | 2019-08-03 | 2019-08-28 | 26 | 10.524 → 9.721 | -7,7% | 0,53 | fuori |
| 6 | short | 2019-11-25 | 2020-01-12 | 49 | 6.903 → 8.185 | -17,9% | -1,00 | fuori |
| 7 | long | 2020-01-29 | 2020-02-26 | 29 | 9.374 → 8.785 | -6,4% | 0,53 | fuori |
| 8 | long | 2020-05-04 | 2020-09-03 | 123 | 8.894 → 10.141 | +13,9% | 0,53 | long |
| 9 | long | 2020-10-11 | 2021-04-22 | 194 | 11.293 → 51.691 | +357,3% | 0,71 | fuori |
| 10 | long | 2021-08-02 | 2021-09-21 | 51 | 39.845 → 40.734 | +2,1% | 0,53 | long |
| 11 | long | 2021-10-04 | 2021-11-18 | 46 | 48.200 → 56.892 | +17,9% | 0,65 | long |
| 12 | short | 2022-01-24 | 2022-02-08 | 16 | 36.245 → 44.043 | -19,2% | -1,00 | short |
| 13 | short | 2022-05-08 | 2022-08-14 | 99 | 35.472 → 24.305 | +27,6% | -1,00 | fuori |
| 14 | long | 2023-01-14 | 2023-03-08 | 54 | 19.930 → 21.705 | +8,8% | 0,53 | short |
| 15 | long | 2023-03-15 | 2023-05-24 | 71 | 24.670 → 26.329 | +6,6% | 0,71 | long |
| 16 | long | 2023-05-29 | 2023-06-05 | 8 | 28.065 → 25.728 | -8,4% | 0,71 | long |
| 17 | long | 2023-06-21 | 2023-08-17 | 58 | 28.308 → 26.623 | -6,0% | 0,53 | long |
| 18 | long | 2023-10-23 | 2024-05-01 | 192 | 29.992 → 58.365 | +94,4% | 0,65 | long |
| 19 | long | 2024-05-19 | 2024-06-11 | 24 | 66.915 → 67.314 | +0,5% | 0,59 | fuori |
| 20 | long | 2024-07-20 | 2024-08-02 | 14 | 66.660 → 61.498 | -7,8% | 0,53 | fuori |
| 21 | long | 2024-09-27 | 2024-10-01 | 5 | 65.174 → 60.806 | -6,8% | 0,59 | long |
| 22 | long | 2024-10-16 | 2025-02-09 | 117 | 67.074 → 96.463 | +43,7% | 0,71 | long |
| 23 | long | 2025-04-28 | 2025-08-25 | 120 | 93.749 → 110.112 | +17,3% | 0,53 | long |
| 24 | long | 2025-09-17 | 2025-09-23 | 7 | 116.789 → 111.999 | -4,2% | 0,53 | long |
| 25 | long | 2025-10-02 | 2025-10-10 | 9 | 118.595 → 112.774 | -5,0% | 0,59 | long |
| 26 | short | 2025-11-17 | 2026-01-13 | 58 | 94.261 → 95.414 | -2,7% | -1,00 | fuori |
| 27 | short | 2026-02-01 | 2026-03-15 | 43 | 78.741 → 72.815 | +1,5% | -1,00 | short |
| 28 | long | 2026-05-11 | 2026-05-17 | 7 | 82.210 → 77.458 | -5,9% | 0,53 | fuori |
| 29 | short | 2026-06-29 | 2026-07-26 | 28 | 59.577 → 65.400 | -9,2% | -1,00 | short |
| 30 | long | 2026-08-22 | 2026-10-29 | 69 | 78.338 → 77.992 | -0,5% | 0,53 | fuori |

30 operazioni, 47% in guadagno, media +19,4%, peggiore -20,6%.

## 7. Movimentazioni di v2 (tre schermi)

Esposizione sempre 1x. Il motivo di ogni ingresso e uscita è in [`REGOLE_AT.md`](REGOLE_AT.md), capitolo 7.

| # | Verso | Entra | Esce | Prezzo | Mossa del prezzo | W3.2 all'ingresso |
|---|---|---|---|---|---|---|
| 1 | long | 2019-04-23 | 2019-08-28 | 5.493 → 9.721 | +77,0% | fuori |
| 2 | long | 2020-05-07 | 2021-05-17 | 9.986 → 43.538 | +336,0% | long |
| 3 | long | 2021-08-20 | 2021-12-04 | 49.322 → 49.152 | -0,3% | long |
| 4 | long | 2022-03-27 | 2022-04-26 | 46.828 → 38.113 | -18,6% | short |
| 5 | long | 2023-03-17 | 2023-06-05 | 27.395 → 25.728 | -6,1% | long |
| 6 | long | 2023-06-21 | 2023-08-17 | 29.994 → 26.623 | -11,2% | long |
| 7 | long | 2023-10-23 | 2024-06-24 | 33.070 → 60.293 | +82,3% | long |
| 8 | long | 2024-10-15 | 2025-02-26 | 67.074 → 84.250 | +25,6% | long |
| 9 | long | 2025-05-01 | 2025-09-25 | 96.490 → 108.994 | +13,0% | long |

## 8. Posizione oggi

| | Posizione oggi | Dettaglio |
|---|---|---|
| W3.2 radar | **short** dal 2026-11-16 | ingresso 65.286 $, esposizione 0,97x, ultimo prezzo 61.271 $, +5,9% sul capitale, trailing a 75.764 $ |
| v1 · voto | **fuori** | voto -0,76: short a −0,90, long a +0,50 |
| v2 · tre schermi | **fuori** | marea neutra: prezzo sotto la media a 40 settimane, struttura non ancora ribassista |

W3.2 è l'unica in posizione: è short dal 16/11 perché il flusso del perp era negativo con il prezzo sotto la EMA 21 e la
media a 40 settimane in calo. Gli algoritmi tecnici non hanno ancora il consenso richiesto per lo short.

## 9. Cosa prendere da questo confronto

1. **Tenere W3.2 come strategia principale.** Nessuno dei due algoritmi tecnici la supera su rendimento, drawdown o
   percentuale di vincenti.
2. **v1 è utile come controllo indipendente**, non come sostituto: usa solo il prezzo, quindi conferma o smentisce W3.2 senza
   dipendere dagli stessi dati. Quando W3.2 è long e il voto è negativo, è un caso raro (12% dei giorni long) da guardare.
3. **La combinazione metà e metà non migliora W3.2 dal 2021** (+38% annuo e −21% contro +43% e −21%). Ha senso solo se si
   teme che il vantaggio del flusso del perp sparisca.
4. **Il vantaggio di W3.2 sono il flusso e l'uscita "distribuzione"**: 7 delle sue 23 operazioni escono così, tutte in
   guadagno tranne una. È anche il suo punto fragile, già segnalato nel radar.

## 10. Limiti

- **W3.2 nel 2018–20 usa un flusso stimato** dal volume spot (il frame lungo del radar): quei tre anni non sono confrontabili
  alla pari con il periodo dal 2021. Le due parti sono unite al 31/12/2020, dove la posizione aperta viene chiusa e riaperta
  dal segnale successivo.
- **Costi leggermente diversi**: W3.2 usa i costi del radar (spot 0,1% + slippage 0,1%; perp 0,05% + 0,1%); v1 e v2 usano
  0,10% per lato. La differenza è di pochi decimi di punto l'anno.
- **Dimensione diversa**: W3.2 riduce l'esposizione quando lo stop è lontano (0,4–1x), v1 e v2 stanno sempre a 1x. Parte del
  drawdown più basso di W3.2 viene da qui.
- **Poche operazioni** per tutte (23, 30 e 9): le percentuali di vincenti sono stime grossolane.
- **Il confronto dal 2021 non è alla pari**: W3.2 è stata sviluppata e tarata guardando tutto il 2021–26 (rischio 25% e filtro
  MACD decisi a novembre 2026), mentre v1 e v2 hanno i parametri scelti sul 2018–21 e il 2022–26 come verifica. Il vantaggio di
  W3.2 dal 2021 va letto con questo sconto.
- **Funding 2018–19**: nel frame lungo del radar manca e per W3.2 vale zero; v1 accredita agli short lo 0,03% al giorno
  ipotizzato (circa +3,9% in tutto). Favorisce v1 in quel periodo.
- **v1 è sensibile al ritardo di esecuzione**: con un giorno in più il rendimento annuo scende da +38,8% a +33,0%.
- **Percentuale di vincenti di W3.2**: il 78% include lo short ancora aperto e il long chiuso d'ufficio al 31/12/2020; sulle 21
  operazioni chiuse per regola è il 76%. Senza la cucitura al 31/12/2020 W3.2 farebbe meglio (2021 a +118% invece di +92%).
- **Verifica indipendente**: un secondo agente ha ricalcolato rendimenti, drawdown e tabelle delle operazioni e ha cercato usi
  di dati futuri in v1 e v2 (troncando i dati a 150 date casuali): numeri confermati, nessun uso di dati futuri.

## 11. Riproducibilità

```bash
python backtest/w32_compare.py
```

```bash
python backtest/build_report.py
```

`vendor/radar_weekly_w32.py` è `radar/weekly.py` al commit `2ec2afd` del repo radar; `data/btc/f_radar_live.csv.gz` e
`data/btc/f_long_radar.csv.gz` sono i frame del radar. Le movimentazioni sono anche in `results/w32/movimenti_w32.csv`,
`movimenti_v1.csv` e `movimenti_v2.csv`.
