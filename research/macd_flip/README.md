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

## Seguito: famiglia Z — "pallino verde sotto lo zero" + EMA/SMA (`zfamily.py`)
Chiarimento dell'utente: entra long sul cross_UP con macd<0; l'ultimo (sett. 13-apr-2026) è "ancora attivo".
Stesse ipotesi di sopra. Regole preregistrate, identiche sui 3 asset (dettagli nel docstring di `zfamily.py`):
Z1 long su verde<0, uscita al primo cross_DN · Z2 Z1 + short su rosso>0 (≡ R3b) · Z3 Z1 ma ingresso solo
a close>EMA20 entro 4 settimane · Z4 uscita trend close<EMA50 (armata dopo la prima close>EMA50) o rosso>0 ·
Z5a/Z5b Z1 solo sopra/sotto SMA200 1W (SOL senza SMA200 fino a ~giu-2024 → ripiego EMA200, poco affidabile:
il pallino SOL di gen-2021 risulta "sopra" solo per questo) · Z6 Z4 + short speculare.
Output: `results_z.csv`, `split_z.csv`, `vicini_z.csv`, `output_z.txt`, `trades_<ASSET>_{Z1,Z4,Z6}.csv`.

### Pallini verdi sotto zero dal 2021 (prezzo = close settimanale; esito Z1 / Z4, uscita all'open lun.)
| Asset | Pallino (dom) | Close | Z1 | Z4 |
|---|---|---|---|---|
| BTC | 2022-04-03 | 46.407 | −15,2% | −9,3% |
| BTC | 2022-08-14 | 24.305 | +6,5% (giu-23) | +6,5% |
| BTC | **2026-04-19** | 73.802 | −19,4% (uscita 29-giu-26) | −19,4% |
| BTC | 2026-07-26 | 65.400 | **aperto +22,9%** | +17,3% (uscita 14-set) |
| ETH | 2022-04-10 | 3.203 | −9,0% | −9,0% |
| ETH | 2022-08-07 | 1.700 | +1,0% | +2,9% |
| ETH | 2023-11-05 | 1.892 | +72,2% | +72,2% |
| ETH | 2024-11-10 | 3.183 | −10,0% | −10,0% |
| ETH | 2025-05-18 | 2.498 | +59,1% | +59,1% |
| ETH | **2026-04-19** | 2.263 | −23,9% (uscita 15-giu-26) | −23,9% |
| ETH | 2026-07-12 | 1.807 | **aperto +33,9%** | +33,1% (uscita 19-ott) |
| SOL | 2021-01-10 | 3,45 | +823,5% | +823,5% |
| SOL | 2022-07-31 | 42,35 | −55,7% (FTX) | −55,7% |
| SOL | 2023-10-01 | 23,87 | +476,7% | +476,7% |
| SOL | 2025-05-18 | 173,3 | +15,2% | −9,2% |
| SOL | **2026-04-19** | 83,47 | **aperto +14,3%** (95,6 al 4-nov) | +18,7% (uscita 14-set) |

Il pallino del 13-apr-2026 (chiusura 19-apr) c'è su **tutti e 3**. È ancora attivo solo su SOL; su BTC ed ETH
un cross_DN a giugno l'ha chiuso in perdita e un nuovo pallino verde a luglio è il trade aperto oggi.

### Risultati dal 2021-01-01
| Asset | Regola | Finale $ | Rend. % | Max DD | Trade | WR | MAR |
|---|---|---|---|---|---|---|---|
| BTC | B&H | 27.805 | +178 | −76,6 | – | – | 0,25 |
| BTC | W2+MACD | ~122.700 | +1127 | −22,7 | 14 | 93 | ~2,4 |
| BTC | Z1 | 8.947 | −10,5 | −45,1 | 4 | 50 | −0,04 |
| BTC | Z3 | 6.635 | −33,7 | −37,8 | 3 | 33 | −0,18 |
| BTC | Z4 | 9.118 | −8,8 | −41,4 | 4 | 50 | −0,04 |
| BTC | Z6 | 11.582 | +15,8 | −52,1 | 11 | 55 | 0,05 |
| ETH | B&H | 32.891 | +229 | −79,3 | – | – | 0,29 |
| ETH | Z1 | 23.117 | +131 | −44,4 | 7 | 57 | 0,35 |
| ETH | Z3 | 19.909 | +99 | −48,2 | 5 | 40 | 0,26 |
| ETH | Z4 | 23.382 | +134 | −44,4 | 7 | 57 | 0,35 |
| ETH | Z6 | 25.327 | +153 | −60,8 | 14 | 57 | 0,28 |
| SOL | B&H | 633.049 | +6231 | −96,3 | – | – | 1,07 |
| SOL | Z1 | 311.255 | +3013 | −87,1 | 5 | 80 | 0,92 |
| SOL | Z3 | 613.493 | +6035 | −56,2 | 3 | 100 | 1,82 |
| SOL | Z4 | 254.597 | +2446 | −87,1 | 5 | 60 | 0,85 |
| SOL | Z6 | 91.112 | +811 | −94,5 | 11 | 55 | 0,49 |

Z2 (≡ R3b): BTC 7,0k, ETH 26,9k, SOL 150k. Regime: Z5a (sopra SMA200) ≈ Z1 su BTC/ETH (quasi tutti i pallini
sono sopra la SMA200); Z5b (sotto) BTC 0 trade, ETH 10,2k, SOL 29k → sotto la SMA200 il segnale non aiuta.
Gli short speculari (Z2/Z6) peggiorano SOL e aggiungono DD ovunque.

### Robustezza
- **Campione minimo**: 4–7 segnali per asset in quasi 6 anni. SOL dipende da un trade solo (gen-2021, +823%):
  senza il migliore Z1 SOL scende a 33,7k, Z3 a 66k; Z1 ETH 13,4k; Z1 BTC 7,3k.
- **Split 21–23 / 24–oggi (CAGR)** Z1: BTC −3,3 / −0,3; ETH 3,5 / 14,3; SOL 159,6 / 10,2. Z3: BTC −5,3 / −8,3;
  SOL 240,7 / 5,1. Dal 2024 Z1 batte il B&H su ETH e SOL (che erano piatti), ma su BTC no (B&H +25%/anno).
- **Parametri vicini** Z1/Z4: con 8/21/5 BTC 17–28k, con 19/39/9 13–14k (meglio di 12/26/9, che è
  il peggiore su BTC); ETH 24–28k stabile; SOL 142–457k. Z3 è fragile: su SOL 614k → 113k / 70k.
- Z3 su SOL "vince" (MAR 1,82) solo perché salta il pallino di lug-2022 (close sotto EMA20) → 3 trade, non
  significativo; su BTC ed ETH Z3 è la peggiore.

### Verdetto Z
Il pallino verde sotto lo zero è un **segnale raro e rumoroso**: su BTC perde soldi in tutte le varianti
(contro 122,7k di W2+MACD); su ETH rende meno del B&H con DD −44% (MAR leggermente migliore); su SOL batte il
B&H solo in rapporto rischio/rendimento, grazie al 2021. Il filtro EMA20 (Z3) e l'uscita EMA50 (Z4) non danno
un miglioramento coerente sui 3 asset. Il segnale del 13-apr-2026 è reale, ma su BTC/ETH la regola meccanica
l'ha già chiuso in perdita (−19%/−24%); oggi Z1 è long su tutti e tre (BTC dal 27-lug, ETH dal 13-lug, SOL dal 20-apr).
**Non adottare**; va bene al massimo come contesto discrezionale, non come strategia.
