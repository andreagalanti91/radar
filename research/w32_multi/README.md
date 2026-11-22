# w32_multi · W3.2 su ETH, SOL e 8 indici azionari · NON TRASFERIBILE (1 asset su 10: ETH)

**Verdetto**: con gli stessi parametri di BTC, W3.2 passa il criterio preregistrato solo su **ETH** (completa, con flusso perp;
WR esattamente 60%, al limite); SOL fallisce DD, WR e la metà 2024→; **0 indici su 8** passano (solo prezzo: WR 26–56%, CAGR/DD
sempre sotto il buy & hold). Per il PREREG (≤ 2 asset) l'esito è "non trasferibile". Conferma le lezioni 74, 87 e 104.
PREREG: `PREREG.md`, commit **b99fe66** (da solo, prima di ogni rendimento). Codice: `fetch.py`, `run.py`, `placebo.py`;
risultati `risultati.csv`, `out.txt`, `placebo.txt`.

**Dati e regole**. ETH/SOL: `radar.weekly.simulate` invariato (W3.2, R 0,25), dati Binance spot + perp USDT-M con taker buy e
funding (research/top10_w3/data, fino al 10/11/2026); il flusso esiste da fine 2019 → versione completa da 29/10/2020 (ETH) e
13/07/2021 (SOL). Dal 2018 solo ETH e solo prezzo (spot Binance dal 2017). Indici: Yahoo chart API (stessa funzione di
multi_asset/fetch.py, al 20/11/2026), indici di prezzo senza dividendi, `ma_lib.s1_sim` (W3.2 senza flusso/funding/distribuzione),
W-FRI, long e short, 0,05% per lato e short 3%/anno. Crypto solo prezzo: 0,2% per lato, short 10%/anno. Verifica: BTC 78.474 $.

## Dal 2021, rischio 25% (10.000 $; CAGR/DD; criteri 1 CAGR/DD>B&H · 2 DD≥−35 · 3 WR≥60 · 4 due metà >0 · 5 ≥8 trade)
| Asset | Versione | Finale | CAGR | DD | Trade | WR | CAGR/DD | B&H finale · DD · C/DD | Metà 21–23 / 24→ | Criteri falliti |
|---|---|---|---|---|---|---|---|---|---|---|
| BTC (rif.) | completa | 78.474 | 42,2% | −21,1 | 13 | 92% | 2,00 | 25.412 · −76,6 · 0,23 | +235% / +135% | – |
| **ETH** | completa | 34.760 | 23,7% | −27,5 | 15 | 60% | 0,86 | 27.770 · −79,3 · 0,24 | +139% / +46% | **nessuno** |
| SOL (dal 13/07/21) | completa | 52.528 | 36,5% | −39,8 | 21 | 43% | 0,92 | 26.980 · −96,3 · 0,21 | +549% / −19% | 2, 3, 4 |
| S&P 500 | solo prezzo | 13.561 | 5,3% | −23,2 | 17 | 53% | 0,23 | 18.338 · −25,4 · 0,43 | +6% / +29% | 1, 3 |
| Nasdaq 100 | solo prezzo | 14.753 | 6,8% | −23,4 | 16 | 56% | 0,29 | 19.308 · −35,6 · 0,33 | +34% / +14% | 1, 3 |
| Dow Jones | solo prezzo | 11.611 | 2,6% | −17,0 | 17 | 53% | 0,15 | 15.705 · −21,9 · 0,36 | +6% / +10% | 1, 3 |
| DAX | solo prezzo | 10.477 | 0,8% | −24,7 | 19 | 53% | 0,03 | 17.838 · −26,4 · 0,39 | +5% / +1% | 1, 3 |
| FTSE MIB | solo prezzo | 15.476 | 7,7% | −20,2 | 15 | 53% | 0,38 | 21.723 · −27,7 · 0,51 | +13% / +37% | 1, 3 |
| Nikkei 225 | solo prezzo | 11.233 | 2,0% | −33,6 | 25 | 28% | 0,06 | 20.446 · −26,3 · 0,49 | −17% / +35% | 1, 3, 4 |
| Russell 2000 | solo prezzo | 6.664 | −6,7% | −58,3 | 23 | 26% | −0,11 | 13.054 · −33,0 · 0,14 | −19% / −14% | 1, 2, 3, 4 |
| Euro Stoxx 50 | solo prezzo | 9.279 | −1,3% | −28,8 | 23 | 35% | −0,04 | 16.648 · −25,5 · 0,36 | −11% / +5% | 1, 3, 4 |

## Dal 2018, rischio 25% (solo prezzo; ETH completa solo dal 29/10/2020)
| Asset | Finale | CAGR | DD | Trade | WR | CAGR/DD | B&H finale · DD · C/DD |
|---|---|---|---|---|---|---|---|
| BTC solo prezzo | 136.151 | 34,3% | −54,9 | 21 | 67% | 0,62 | 53.589 · −81,2 · 0,26 |
| ETH solo prezzo | 27.265 | 12,0% | −61,0 | 31 | 39% | 0,20 | 27.899 · −94,0 · 0,13 |
| ETH completa (dal 29/10/20) | 34.760 | 22,9% | −27,5 | 15 | 60% | 0,83 | 52.677 · −79,3 · 0,40 |
| S&P 500 | 10.556 | 0,6% | −39,2 | 33 | 45% | 0,02 | 25.723 · −33,9 · 0,33 |
| Nasdaq 100 | 18.365 | 7,1% | −23,4 | 26 | 58% | 0,30 | 38.877 · −35,6 · 0,46 |
| Dow Jones | 7.064 | −3,8% | −45,4 | 32 | 41% | −0,08 | 19.388 · −37,1 · 0,21 |
| DAX | 5.565 | −6,4% | −52,7 | 34 | 35% | −0,12 | 19.211 · −38,8 · 0,20 |
| FTSE MIB | 10.108 | 0,1% | −43,4 | 31 | 32% | 0,00 | 22.218 · −41,5 · 0,23 |
| Nikkei 225 | 7.731 | −2,9% | −50,6 | 42 | 19% | −0,06 | 24.435 · −31,8 · 0,33 |
| Russell 2000 | 5.357 | −6,8% | −63,3 | 39 | 26% | −0,11 | 16.790 · −43,1 · 0,14 |
| Euro Stoxx 50 | 4.937 | −7,6% | −57,4 | 41 | 24% | −0,13 | 16.995 · −38,3 · 0,16 |

## Rischio 10% (dal 2021; finale · DD · CAGR/DD)
BTC 27.190 · −9,8 · 1,91; ETH 18.641 · −11,4 · 0,98; SOL 25.094 · −20,2 · 0,94 (WR 43%, metà 24→ −6%); indici quasi
identici al 25% (S&P 13.702 · −22,3 · 0,25; Nasdaq 14.394 · −18,8 · 0,34; FTSE MIB 15.066 · −18,0 · 0,40; Russell 7.642 · −51,0):
con ATR settimanali del 2–4% lo stop a 2,5 ATR è il 5–10% del prezzo, quindi l'esposizione resta al tetto 1x in entrambi i casi.
Il rischio non cambia i segnali: sugli indici il problema sono i segnali, non la dimensione.

## Robustezza di ETH (unico che passa 1–5)
Senza il trade migliore 19.915 $ (> 10k); vicini stop/trailing 2,0 / 3,0 ATR: CAGR/DD 0,59 / 0,72 (B&H 0,24); dal primo dato
utile 0,83 contro 0,40; solo prezzo dal 2018 0,20 contro 0,13. Placebo (stessi 15 trade in date casuali, 2000 prove): p = 0,005.
Limiti: il WR è sulla soglia (9/15), il risultato era già noto (lezione 87, stessi dati), la metà 2024→ rende +46% con DD sotto
il B&H ma senza il trade migliore il CAGR dal 2021 scende a ~12%. Senza flusso perp ETH crolla (dal 2021 15.515 $, DD −58,8%, WR 43%).

## Confronto con BTC
BTC resta l'unico caso forte (CAGR/DD 2,00, WR 92%). ETH vale meno della metà per unità di DD (0,86). Sulle azioni W3.2 solo
prezzo perde contro il buy & hold ovunque: i trend degli indici sono troppo regolari (uscite EMA21 e trailing tagliano rialzi
che poi riprendono) o troppo erratici (Nikkei, Russell, Euro Stoxx: WR 19–35%). Anche BTC solo prezzo scende a 0,83 dal 2021:
gran parte del vantaggio di W3.2 è il flusso perp, che sugli indici non esiste.

**Lezione proposta (110)**: W3.2 con i parametri di BTC (rischio 25%) non si trasferisce: dal 2021 passa il criterio
preregistrato solo ETH (34,8k, DD −27,5%, WR 60% al limite, placebo p 0,005; già noto dalla lezione 87); SOL ha DD −40%, WR 43%
e perde nel 2024→; 0 indici su 8 (S&P, Nasdaq 100, Dow, DAX, FTSE MIB, Nikkei, Russell 2000, Euro Stoxx 50) battono il buy & hold
in CAGR/DD, con WR 26–56% e, dal 2018, rendimenti negativi su 5. Sugli indici rischio 10% e 25% danno quasi gli stessi numeri
(esposizione già al tetto 1x): il limite sono i segnali senza flusso. File: research/w32_multi/README.md.
