# W3 sulle top 10 crypto · 11/11/2026 · NON generalizza (solo BTC, ETH come seconda scelta)

Universo: CoinGecko /coins/markets dell'11/11/2026, esclusi stablecoin (USDT, USDC, USDS, USDe, DAI) e il token RWA
FIGR_HELOC: **BTC, ETH, BNB, XRP, SOL, TRX, HYPE, ZEC, XMR, DOGE**. Dati Binance `<SYM>USDT`: spot (data-api), perp USDT-M
1d con taker buy e funding (data.binance.vision). Verifica: con questi dati BTC dà W2 118.628 $ e W3 78.474 $, identici al repo.
Dal 01/01/2021 (SOL dal 13/07/2021, DOGE dall'08/05/2021, HYPE dal 28/03/2026: 200 giorni di flusso) al 10/11/2026,
10.000 $, 1x, costi di weekly.py, stessi parametri ovunque. W3 = flusso medio 3 g + cricchetto + tetto rischio long 25%, senza
rendimento della liquidità. Script: `fetch.py`, `run.py`; risultati `per_asset.csv`, `portafogli.csv`. Preregistrazione: `PREREG.md`.

## Per asset (capitale finale $, DD giornaliero %, MAR; "batte B&H" = MAR W3 > MAR B&H in 2021–23 / 2024→)
| Asset | W3 | DD | trade/WR | MAR | W2 | DD | B&H | DD | MAR B&H | batte B&H 21–23 / 24→ | W3 senza miglior trade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTC | 78.474 | −21,1 | 13 / 92% | 2,00 | 118.628 | −22,7 | 25.438 | −76,6 | 0,23 | sì / sì | 51.561 |
| ETH | 34.760 | −27,5 | 15 / 60% | 0,86 | 36.090 | −40,9 | 27.797 | −79,3 | 0,24 | sì / sì | 19.923 |
| BNB | 29.566 | −67,4 | 25 / 28% | 0,30 | 36.612 | −67,7 | 181.624 | −70,9 | 0,90 | no / sì | 7.300 |
| XRP | 4.550 | −73,8 | 25 / 32% | −0,17 | 3.237 | −83,7 | 47.981 | −83,2 | 0,37 | no / no | 3.421 |
| SOL | 52.528 | −39,8 | 21 / 43% | 0,92 | 126.965 | −52,1 | 27.007 | −96,3 | 0,21 | sì / no | 17.982 |
| TRX | 100.705 | −44,4 | 19 / 58% | 1,09 | 267.716 | −42,3 | 118.359 | −69,5 | 0,76 | no / sì | 32.455 |
| HYPE* | 9.612 | −37,3 | 3 / 33% | −0,17 | 10.893 | −44,6 | 18.649 | −30,0 | 5,75 | n/d / no | 7.759 |
| ZEC | 14.850 | −68,4 | 28 / 29% | 0,10 | 16.541 | −83,0 | 162.886 | −94,3 | 0,65 | sì / no | 7.598 |
| XMR* | 2.318 | −88,1 | 32 / 19% | −0,25 | 2.400 | −89,5 | 35.959 | −78,4 | 0,31 | no / no | 1.787 |
| DOGE | 4.299 | −73,0 | 28 / 21% | −0,19 | 864 | −92,3 | 983 | −91,7 | −0,37 | sì / sì | 1.825 |
Tempo a mercato W3: 42–60% (HYPE 88%). Trailing 2,0/3,0 ATRw non cambia il quadro (es. ETH 31k/30k, TRX 47k/122k).
*HYPE: 7 mesi, spot Binance solo da 09/2026 → prezzo del perp. XMR: spot delistato il 20/02/2024 → prezzo del perp dopo.

## Portafogli (10% per asset, indipendenti; asset non ancora partiti = liquidità)
| Portafoglio | Finale $ | CAGR | DD | MAR | 2021–23 | 2024→ |
|---|---|---|---|---|---|---|
| (i) W3 solo BTC | 78.474 | 42,2% | −21,1 | 2,00 | +235% (DD −19,3) | +135% (DD −21,1) |
| (ii) W3 equal-weight 10 | 33.166 | 22,7% | −15,7 | 1,44 | +97% (−15,7) | +68% (−13,1) |
| (iii) W3 BTC+ETH+DOGE [selezione a posteriori] | 39.178 | 26,3% | −19,9 | 1,32 | +101% | +95% |
| (iv) B&H equal-weight 10 | 64.733 | 37,6% | −70,7 | 0,53 | +163% (−70,7) | +147% (−46,7) |
| W3 50/50 BTC+ETH | 56.617 | 34,5% | −20,2 | 1,71 | +187% | +98% |
| W3 50/50 BTC+TRX | 89.589 | 45,4% | −25,0 | 1,81 | +186% | +214% |

## Verdetto
Soglie del PREREG non raggiunte: W3 batte il B&H sul MAR in 5/10 asset (serviva 7) e in entrambe le metà in 3/10 (BTC, ETH,
DOGE; serviva 5). Su 6 alt su 9 il win rate scende sotto il 35% e il DD supera il 40%: il flusso perp non separa i trade buoni.
Il portafoglio equal-weight ha il DD più basso (−15,7%) ma rende meno della metà di BTC da solo, con MAR più basso (1,44 contro 2,00):
la diversificazione riduce il DD ma diluisce l'unico asset con vantaggio. ETH è l'unico alt che passa il criterio "aggiunge valore"
(MAR > B&H in entrambe le metà, DD 50/50 −20,2% ≤ BTC) ma abbassa il MAR del portafoglio; DOGE passa per caso (B&H −90%).
TRX 50/50 rende di più ma con DD −25% e grazie a un'unica metà (2024→): non promuovibile. Conferma le lezioni 71 e 74.

## Limiti
Sopravvivenza: la top 10 di oggi non era la top 10 del 2021 (ZEC, TRX, HYPE sono saliti dopo; LUNA, DOT, AVAX esclusi perché
caduti) → il B&H delle 10 è ottimistico. Storie brevi (HYPE 7 mesi, SOL/DOGE da metà 2021). Il flusso taker degli alt è più
piccolo e più guidato dai market maker; XMR/HYPE usano il prezzo perp. Funding di novembre 2026 mancante (solo uscite "dist").
Nessun placebo: il risultato è già negativo prima di servirne uno.

**Lezione proposta (87)**: W3 applicato senza modifiche alle top 10 crypto (dal 2021) batte il buy & hold sul MAR in entrambe
le metà solo su BTC, ETH e DOGE; sugli altri il WR scende al 19–43% e il DD a −40/−88%. Il paniere a 10 dimezza il DD
(−15,7%) ma rende 33k contro 78k di BTC da solo (MAR 1,44 contro 2,00). Il vantaggio resta specifico di BTC; ETH è al massimo una
seconda gamba a basso peso. File: research/top10_w3/README.md.
