# w32_top100 · W3.2 sulle prime 100 crypto · NON SI TRASFERISCE (1 altcoin su 27: ETH)

**Verdetto**: con i parametri di BTC (radar/weekly.py invariato, rischio 25%) passa il criterio preregistrato, la conferma e il
placebo con Holm solo **ETH** fra le 27 altcoin valutabili (3,7%; soglia "non si trasferisce" < 20%). BTC passa (riferimento).
Nessuna altra altcoin supera insieme DD ≥ −35% e WR ≥ 60%: il limite resta il drawdown (DD mediano −65%, WR mediano 33%).
Conferma le lezioni 74, 87 e 110 su un universo 3 volte più grande. PREREG: `PREREG.md`, commit **866f3eb** (da solo, prima dei
prezzi). Codice: `universe.py`, `fetch.py`, `run.py`; risultati `risultati.csv`, `portafogli.csv`, `out.txt`; dati `data/` (6 MB).

## Universo e conteggi
CoinGecko `/coins/markets` del 22/11/2026, prime 100. Escluse 28 (19 stablecoin, oro XAUT/PAXG, 7 fondi tokenizzati/RWA; nessun
wrapped/staked/bridged fra le prime 100). Restano 72: **57 con perp USDT-M** Binance (versione completa), 1 solo spot (NEXO),
14 senza dati Binance (token di exchange e simili: LEO, WBT, CRO, OKB, MNT, BGB, KCS, GT, HTX, PI, RAIN, PEARL, BDX, XDC).
Delle 57: 8 con meno di 180 g di test (non simulate), 21 simulate ma con < 3 anni (fuori conteggio), **28 valutabili** (BTC + 27
altcoin). Passano 1–5: BTC, ETH; conferma (senza trade migliore, vicini 2,0/3,0 ATR) e placebo: BTC p = 0,0015, ETH p = 0,0055,
entrambe significative dopo Holm (m = 2). Verifica: BTC con i dati scaricati = **78.474 $** (identico a w32_multi).
Correzioni ai dati (dichiarate, non nel PREREG): LITUSDT fino al 2025 è Litentry (altra moneta) → LIT solo dal 23/12/2025; TON
delistato da Binance a fine 06/2026 (perp fermo) → TON fino al 22/06/2026. Nessuna delle due è valutabile.
**Bias di sopravvivenza**: la top 100 di oggi esclude le monete morte (LUNA, FTT…); i B&H sono gonfiati, ma anche così la
maggior parte delle altcoin ha B&H in perdita dal suo inizio.

## Migliori 15 e peggiori 5 (valutabili, per CAGR/DD; 10.000 $; criteri 1 C/DD>B&H · 2 DD≥−35 · 3 WR≥60 · 4 metà >0 · 5 ≥8 trade)
| Moneta | Inizio | Finale | DD | Trade | WR | CAGR/DD | B&H finale · DD · C/DD | Metà 1 / 2 | Falliti |
|---|---|---|---|---|---|---|---|---|---|
| BTC | 2021-01-01 | 78.474 | −21,1 | 13 | 92% | 2,00 | 25.412 · −76,6 · 0,23 | +235% / +135% | – |
| TRX | 2021-01-01 | 100.705 | −44,4 | 19 | 58% | 1,09 | 118.241 · −69,5 · 0,75 | +137% / +270% | 2, 3 |
| SOL | 2021-07-13 | 52.528 | −39,8 | 21 | 43% | 0,92 | 26.980 · −96,3 · 0,21 | +549% / −19% | 2, 3, 4 |
| **ETH** | 2021-01-01 | 34.760 | −27,5 | 15 | 60% | 0,86 | 27.770 · −79,3 · 0,24 | +139% / +46% | – |
| INJ | 2023-06-15 | 23.299 | −44,7 | 15 | 33% | 0,63 | 13.520 · −94,7 · 0,10 | +128% / +1% | 2, 3 |
| ALGO | 2021-04-14 | 23.069 | −30,0 | 16 | 44% | 0,54 | 594 · −96,7 · −0,41 | +13% / +105% | 3 |
| ADA | 2021-01-01 | 25.675 | −46,5 | 23 | 43% | 0,38 | 9.546 · −95,2 · −0,01 | +188% / −11% | 2, 3, 4 |
| BNB | 2021-01-01 | 29.566 | −67,4 | 25 | 28% | 0,30 | 181.443 · −70,9 · 0,90 | +56% / +94% | 1, 2, 3 |
| HBAR | 2022-01-13 | 14.029 | −42,0 | 21 | 38% | 0,17 | 2.204 · −87,0 · −0,31 | −23% / +83% | 2, 3, 4 |
| ZEC | 2021-01-01 | 14.850 | −68,4 | 28 | 29% | 0,10 | 162.723 · −94,3 · 0,65 | −16% / +57% | 1–4 |
| BCH | 2021-01-01 | 11.032 | −63,3 | 27 | 44% | 0,03 | 6.726 · −94,2 · −0,07 | +18% / −37% | 2, 3, 4 |
| DOT | 2021-06-20 | 10.151 | −50,0 | 23 | 52% | 0,01 | 416 · −98,6 · −0,45 | +23% / −18% | 2, 3, 4 |
| ETC | 2021-01-01 | 10.475 | −79,4 | 27 | 37% | 0,01 | 11.848 · −95,5 · 0,03 | +63% / −36% | 1–4 |
| AAVE | 2021-08-14 | 10.178 | −56,0 | 19 | 37% | 0,01 | 2.880 · −88,1 · −0,24 | +24% / +0% | 2, 3 |
| UNI | 2021-07-17 | 8.344 | −53,4 | 22 | 32% | −0,06 | 4.063 · −92,4 · −0,17 | −20% / +4% | 2, 3, 4 |
| … | | | | | | | | | |
| SHIB | 2022-03-08 | 4.960 | −60,8 | 22 | 32% | −0,23 | 1.954 · −88,6 · −0,33 | −29% / −30% | 2, 3, 4 |
| POL | 2021-08-20 | 4.034 | −67,8 | 23 | 30% | −0,24 | 598 · −97,6 · −0,43 | −42% / −30% | 2, 3, 4 |
| LTC | 2021-01-01 | 2.506 | −87,4 | 27 | 26% | −0,24 | 4.068 · −89,4 · −0,16 | −6% / −73% | 1–4 |
| XMR | 2021-01-01 | 2.318 | −88,1 | 32 | 19% | −0,25 | 35.923 · −78,4 · 0,31 | −62% / −32% | 1–4 |
| QNT | 2023-08-18 | 2.502 | −77,6 | 18 | 22% | −0,45 | 18.663 · −66,3 · 0,32 | −35% / −63% | 1–4 |

Solo prezzo (separata): NEXO dal 23/02/2023 9.919 $, DD −57,2%, 17 trade, WR 18% (B&H 9.464, −56,8%): non passa.

## Distribuzione (27 altcoin valutabili, versione completa)
Finale: minimo 2.318, quartili 4.755 / **8.344** / 18.960, massimo 100.705 (13 su 27 sopra 10.000 $; 15 sopra il B&H). DD
mediano −65,4% (solo 2 su 27 ≥ −35%), WR mediano 33% (1 su 27 ≥ 60%). CAGR/DD batte il B&H in 16 su 27 (mediana della differenza
+0,10), ma soprattutto perché i B&H crollano (mediano 9.126 $): battere un −90% con un −65% non è un vantaggio utile. Positive in
entrambe le metà: 6 su 27. Fra le 21 con < 3 anni passa 1–5 solo STX (17.081 $, DD −28%, 10 trade, WR 70%, dal 20/12/2023):
da osservare, non conta.

## Portafogli equipesati dal 01/01/2021 (quote indipendenti, liquidità prima dell'inizio)
| Portafoglio | Finale | CAGR | DD | CAGR/DD | 2021–23 / 2024→ |
|---|---|---|---|---|---|
| W3.2 solo BTC | 78.474 | 42,2% | −21,1 | 2,00 | +235% / +135% |
| (a) W3.2 EW 28 valutabili (onesto) | 18.130 | 10,7% | −15,8 | 0,68 | +57% / +15% |
| (a') W3.2 EW 27 altcoin | 15.895 | 8,2% | −18,5 | 0,45 | +51% / +5% |
| B&H EW 27 altcoin | 26.735 | 18,3% | −76,0 | 0,24 | +91% / +35% |
| (b) W3.2 BTC + ETH [SCELTO A POSTERIORI] | 56.617 | 34,5% | −20,2 | 1,71 | +187% / +98% |
| B&H BTC + ETH | 26.591 | 18,2% | −77,4 | 0,23 | +128% / +13% |
Diversificare sulle altcoin abbassa il DD ma diluisce BTC: (a) rende un quarto di BTC da solo; (b) è distorto dalla selezione
e resta sotto BTC da solo.

## Lezione proposta
**Lezione 111**: W3.2 con i parametri di BTC sulle prime 100 crypto di oggi (72 dopo stablecoin/RWA, 57 con perp, 28 con ≥ 3 anni):
passa il criterio, la conferma e il placebo con Holm solo ETH fra 27 altcoin (BTC 78.474 $, ETH 34.760 $); TRX e SOL rendono di più
del B&H ma con DD −40/−44% e WR < 60%; altcoin mediana 8.344 $, DD −65%, WR 33%. Il portafoglio equipesato delle 27 altcoin fa
15.895 $ (DD −18,5%) contro 78.474 $ di BTC da solo. Il vantaggio non si trasferisce alle altcoin; ETH resta l'unico candidato.
research/w32_top100/README.md (PREREG 866f3eb).
