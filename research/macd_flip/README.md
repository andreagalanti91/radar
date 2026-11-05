# MACD settimanale "flip" long/short — BTC, ETH, SOL (2021 → nov 2026)

Proposta dell'utente: swing settimanale long+short sui cross MACD 12/26/9 (CM_Ult_MacD_MTF, close),
con EMA20/EMA50/EMA200/SMA200 come contesto. Note discrezionali su SOL 1W: Short 180→30, Long 20→160,
Short 160→stop 160, Long 170→200, Short 200→95, Long 160→200, Short 200→80.

File: `fetch.py` (klines 1d spot da data-api.binance.vision → `data/`), `backtest.py` (tutto il resto),
`results.csv`, `split.csv`, `vicini.csv`, `output.txt` (stampa completa), `trades_<ASSET>_<R>.csv` per R1/R4a/R7.

## Metodo
- Barre 1W come TradingView (lun 00:00 UTC → dom close), costruite da 1d; settimana in corso esclusa.
- Segnale alla close settimanale, fill all'open del lunedì dopo (fill alla close: risultati identici a ±0,1%).
- Costi 0,1%/lato. Funding short = 0 (di norma gli short *ricevono* funding positivo: ipotesi prudente).
- 1x, capitale pieno, compounding, 10.000 $ al 2021-01-01, partenza flat. DD su equity giornaliera.
  Short 1x liquidato se il prezzo raddoppia (−100%).
- SMA200/EMA200 1W richiedono ~200 settimane: per SOL (dati da 2020-08) la SMA200 esiste solo da ~giu 2024,
  quindi R6 usa EMA50 come ripiego prima di allora (su SOL R6 ≡ R2).

Famiglia preregistrata (identica sui 3 asset): R1 flip puro; R2 R1 + filtro close vs EMA50; R3a cross "alert"
(UP con macd>0 / DN con macd<0); R3b cross d'inversione (opposto); R4a R1 + stop all'estremo della settimana
del segnale; R4b R1 + stop 2×ATR14; R5 R1 solo long; R6 R1 + filtro SMA200; R7 ingressi R1, uscita su cross
opposto **o** close oltre EMA20 (aggiunta dopo lo screenshot, prima di vedere i risultati).

## Reverse-engineering dei trade SOL
La regola è il **flip puro sui cross MACD 1W (R1)**: tutti i 7 ingressi dell'utente coincidono con un cross.
Lo "stop 160" coincide esattamente con il massimo della settimana del segnale (160,0) → logica R4a.
Ma la lista dell'utente **omette 5 trade perdenti** che la stessa regola genera, e due uscite (30, 95) sono
minimi intra-settimana, non riproducibili da alcuna regola (hindsight).

| Utente | Regola R1 (ingresso → uscita, lunedì) | R1 % |
|---|---|---|
| Short 180→30 | 2021-12-13 172,8 → 2022-08-01 42,3 | +75,2 |
| — (omesso) | Long 2022-08-01 42,3 → 2023-09-18 18,8 (FTX) | **−55,7** |
| — (omesso) | Short 2023-09-18 18,8 → 2023-10-02 23,9 | **−27,1** |
| Long 20→160 | 2023-10-02 23,9 → 2024-04-29 138,0 | +476,7 |
| Short 160→stop 160 | 2024-04-29 138,0 → 2024-10-28 176,6 (R4a: stop 160,0 = −16%) | **−28,2** |
| Long 170→200 | 2024-10-28 176,6 → 2025-01-13 188,5 | +6,5 |
| — (omessi) | Short 188,5→252,4 e Long 252,4→203,5 (whipsaw gen-2025) | **−34,0 / −19,5** |
| Short 200→95 | 2025-02-03 203,5 → 2025-05-19 173,3 (95 = minimo apr-25) | +14,6 |
| Long 160→200 | 2025-05-19 173,3 → 2025-10-27 200,0 | +15,2 |
| Short 200→80 | 2025-10-27 200,0 → 2026-04-20 83,5 | +58,0 |
| (aperto) | Long 2026-04-20 83,5 → 95,6 | +14,3 |

Composto dei trade dell'utente (senza costi): **×52,6**. Stessa regola, stesso periodo (dic-21 → oggi): **×3,2**.

## Risultati dal 2021-01-01 (10.000 $, fill open, costi inclusi)
| Asset | Regola | Finale $ | Rend. % | CAGR | Max DD | MAR | Trade | WR |
|---|---|---|---|---|---|---|---|---|
| BTC | B&H | 27.805 | +178 | 19,1 | −76,6 | 0,25 | – | – |
| BTC | **W2+MACD (produzione)** | **~122.700** | +1127 | ~53 | **−22,7** | ~2,3 | 14 | 93 |
| BTC | R1 flip | 22.222 | +122 | 14,7 | −46,0 | 0,32 | 18 | 50 |
| BTC | R3a alert | 31.769 | +218 | 21,9 | −28,8 | 0,76 | 7 | 71 |
| BTC | R4a stop | 15.897 | +59 | 8,3 | −37,2 | 0,22 | 18 | 28 |
| BTC | R7 EMA20 | 19.685 | +97 | 12,3 | −31,4 | 0,39 | 18 | 44 |
| ETH | B&H | 32.891 | +229 | 22,6 | −79,3 | 0,29 | – | – |
| ETH | R1 flip | 44.005 | +340 | 28,9 | −55,8 | 0,52 | 18 | 56 |
| ETH | R3a alert | 16.369 | +64 | 8,8 | −30,0 | 0,29 | 4 | 50 |
| ETH | R4a stop | 35.287 | +253 | 24,1 | −41,4 | 0,58 | 18 | 39 |
| ETH | R7 EMA20 | 26.091 | +161 | 17,8 | −37,4 | 0,48 | 18 | 56 |
| SOL | B&H | 633.049 | +6231 | 103,5 | −96,3 | 1,07 | – | – |
| SOL | R1 flip | 302.327 | +2923 | 79,3 | −81,8 | 0,97 | 15 | 60 |
| SOL | R3a alert | 20.139 | +101 | 12,7 | −58,3 | 0,22 | 4 | 50 |
| SOL | R4a stop | 500.849 | +4909 | 95,5 | −68,5 | 1,39 | 15 | 27 |
| SOL | R5 solo long | 859.841 | +8498 | 114,4 | −84,8 | 1,35 | 8 | 75 |
| SOL | R7 EMA20 | 922.541 | +9125 | 117,0 | −67,5 | 1,73 | 15 | 47 |

Altre regole (R2, R3b, R4b, R6) in `results.csv`: nessuna migliore in modo coerente sui 3 asset.
Su SOL il primo long 2021 (3,4→31,9, **+823%**) fa quasi tutto: senza il miglior trade R1 finisce a 32.700 $.
Short su SOL con R1: contributo composto netto **×0,35** (perdono soldi); su BTC ×0,97.

## Robustezza
- **Split** (ripartenza flat 10k) R1: BTC CAGR 0,8% (21–23) / 13,6% (24–oggi); ETH 13,5 / 30,0;
  SOL 184,9 / **−1,1**. R7: BTC −0,9 / 10,7; ETH 24,9 / −2,2; SOL 328 / −4,7. R4a SOL 24–oggi −20,9%.
  Dal 2024 su SOL nessuna variante batte il cash (B&H −2,2%/anno nello stesso periodo).
- **Parametri vicini** (8/21/5, 19/39/9): R1 su SOL **liquidato (−100%)** con entrambi (short 1x durante
  i rally 2021); su BTC 8/21/5 migliora (70k) ma 19/39/9 crolla (12k, DD −68%). R7 è la più stabile ma
  oscilla 140k–920k su SOL e 12k–26k su ETH.
- **Senza lo short 2022**: R1 BTC 22,2k → 15,2k; ETH 44,0k → 25,4k; SOL 302k → 172k. Lo short 2022 da solo
  vale ~30–45% del risultato.

## Verdetto
La regola dell'utente è il flip puro sui cross MACD 1W; "sembra funzionare" perché la lista ricorda i 7
trade buoni ed esclude i 5 perdenti (−55%, −27%, −28%, −34%, −20%) e usa uscite sui minimi visti a posteriori.
Applicata in modo meccanico: su BTC rende meno del B&H e **5× meno di W2+MACD** con DD doppio; su ETH batte
il B&H ma con DD −56%; su SOL rende meno del B&H e dipende dal 2021. Instabile a parametri e sotto-periodi,
short 1x su alt a rischio liquidazione. **Non adottare come strategia autonoma**; al massimo il cross MACD 1W
resta un filtro/contesto (come già in W2+MACD). Nessuna modifica a `radar/`.
