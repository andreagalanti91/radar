# N2 · Swing BTC con tenuta 2–3 giorni (notte 15/11/2026) · VERDETTO: NESSUNA REGOLA ACCETTABILE

Regole, soglie e criteri scritti prima dei risultati in PREREG.md; script run.py (riproducibile, ~2 s); output risultati.txt,
configurazioni.csv (32 configurazioni), vicini.csv, trades.csv.

## Impostazione
BTC perp Binance giornaliero dal 01/01/2021 al 14/11/2026, 10.000 $ a 1x, una posizione per volta, long e short in conti separati.
Segnale alla chiusura UTC, ingresso all'apertura successiva, uscita dopo 2 o 3 giorni oppure a 1,5 ATR14 di stop. Costi 0,08%/lato
+ slippage 0,05%/lato + funding reale. Flussi perp e OI con un giorno di ritardo (come dal vivo, stesso principio di W3).
8 regole in 3 famiglie: (a) A1 Donchian 10 + delta taker spot/perp > 0, A2 Donchian 20 nel verso del regime W3; (b) B1 RSI(2) 10/90
nel verso del regime, B2 RSI(2) contro/fuori regime, B3 movimento di 3 giorni oltre 2,5 ATR in contrarian; (c) C1 funding z
estremo contrarian, C2 OI in aumento + giorno e spot concordi, C3 aggressione taker spot (z90) + perp concorde.
Riferimenti: **buy & hold 22.152 $ (DD −76,7%)**, **W3 78.474 $ (DD −21,1%, MAR 1,99)**, flat il 40% dei giorni.

## Risultati (H = tenuta in giorni; criteri: OOS>0 · PF>1,2 in entrambe le metà · placebo corretto · vicini · ≥20 trade per metà)
| config | 10k → | DD % | trade (anno) | WR % | PF | PF IS / OOS | OOS % | senza top5 | p (corr.) | vicini | corr W3 | W3 + regola | criteri |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1L2 | 11.245 | -28,3 | 68 (11,6) | 44 | 1,19 | 1,63 / 0,96 | -6,0 | 6.507 | 0,18 (1,00) | 2/4 | 0,13 | 80.580 (-21,1) | ....x |
| A1L3 | 11.555 | -30,2 | 64 (10,9) | 48 | 1,21 | 1,55 / 0,99 | -4,8 | 6.700 | 0,19 (1,00) | 2/4 | 0,13 | 79.731 (-22,4) | ....x |
| A1S2 | 8.184 | -36,0 | 78 (13,3) | 36 | 0,91 | 0,95 / 0,87 | -10,2 | 4.688 | 0,35 (1,00) | 0/4 | 0,04 | 83.462 (-20,3) | ....x |
| A1S3 | 6.144 | -47,9 | 72 (12,3) | 38 | 0,80 | 1,04 / 0,60 | -35,7 | 3.254 | 0,64 (1,00) | 0/4 | 0,04 | 75.591 (-26,8) | ....x |
| A2L2 | 10.516 | -26,7 | 65 (11,1) | 54 | 1,12 | 1,12 / 1,12 | +3,0 | 6.000 | 0,21 (1,00) | 2/4 segno≠ | 0,36 | 53.491 (-21,1) | x...x |
| A2L3 | 12.193 | -30,9 | 54 (9,2) | 50 | 1,29 | 1,57 / 1,03 | -1,5 | 6.974 | 0,14 (1,00) | 1/4 segno≠ | 0,39 | 53.683 (-21,1) | ....x |
| A2S2 | 11.700 | -13,6 | 15 (2,6) | 47 | 1,74 | 1,59 / 2,14 | +7,3 | 8.022 | 0,07 (1,00) | 3/4 | 0,10 | 81.535 (-21,1) | xx.x. |
| A2S3 | 11.095 | -20,2 | 12 (2,0) | 42 | 1,55 | 1,23 / 3,85 | +7,9 | 7.806 | 0,15 (1,00) | 2/4 segno≠ | 0,11 | 79.703 (-21,1) | xx... |
| B1L2 | 8.838 | -40,1 | 87 (14,8) | 52 | 0,96 | 1,44 / 0,62 | -28,3 | 5.578 | 0,36 (1,00) | 1/4 segno≠ | 0,15 | 64.752 (-29,1) | ....x |
| B1L3 | 8.505 | -40,7 | 80 (13,6) | 45 | 0,96 | 1,37 / 0,65 | -30,3 | 5.090 | 0,43 (1,00) | 1/4 segno≠ | 0,20 | 49.068 (-32,3) | ....x |
| B1S2 | 9.307 | -28,6 | 50 (8,5) | 46 | 0,94 | 1,21 / 0,48 | -13,3 | 6.596 | 0,35 (1,00) | 0/4 | 0,15 | 76.311 (-24,2) | ..... |
| B1S3 | 12.933 | -20,6 | 47 (8,0) | 49 | 1,42 | 1,88 / 0,78 | -7,6 | 7.952 | 0,08 (1,00) | 0/4 segno≠ | 0,17 | 82.678 (-24,2) | ..... |
| B2L2 | 11.261 | -31,9 | 95 (16,2) | 54 | 1,14 | 1,15 / 1,12 | +4,1 | 7.150 | 0,15 (1,00) | 1/4 segno≠ | -0,17 | 72.786 (-39,1) | x...x |
| B2L3 | 7.806 | -55,9 | 83 (14,1) | 55 | 0,95 | 0,87 / 1,10 | +2,3 | 4.305 | 0,46 (1,00) | 1/4 segno≠ | -0,17 | 68.663 (-52,4) | x...x |
| B2S2 | 3.351 | -71,4 | 161 (27,4) | 44 | 0,66 | 0,53 / 0,84 | -20,6 | 2.062 | 0,83 (1,00) | 0/4 | -0,34 | 68.621 (-26,3) | ....x |
| B2S3 | 1.961 | -83,1 | 142 (24,2) | 41 | 0,54 | 0,41 / 0,70 | -37,1 | 1.251 | 0,97 (1,00) | 0/4 | -0,37 | 61.866 (-29,8) | ....x |
| B3L2 | 9.195 | -20,9 | 21 (3,6) | 48 | 0,87 | 1,64 / 0,53 | -15,0 | 6.642 | 0,52 (1,00) | 0/6 segno≠ | -0,08 | 62.490 (-24,3) | ..... |
| B3L3 | 5.951 | -45,8 | 20 (3,4) | 40 | 0,38 | 0,33 / 0,44 | -20,4 | 4.611 | 0,98 (1,00) | 0/6 | -0,07 | 51.801 (-32,0) | ..... |
| B3S2 | 5.594 | -46,2 | 34 (5,8) | 24 | 0,23 | 0,27 / 0,18 | -26,1 | 4.834 | 0,98 (1,00) | 0/6 | -0,09 | 69.319 (-24,2) | ..... |
| B3S3 | 4.904 | -53,3 | 30 (5,1) | 17 | 0,13 | 0,10 / 0,17 | -26,0 | 4.414 | 0,99 (1,00) | 0/6 | -0,16 | 74.723 (-24,2) | ..... |
| C1L2 | 12.102 | -25,0 | 66 (11,2) | 56 | 1,32 | 0,97 / 1,76 | +24,8 | 8.942 | 0,14 (1,00) | 1/4 segno≠ | -0,01 | 78.286 (-28,6) | x...x |
| C1L3 | 10.814 | -25,6 | 48 (8,2) | 56 | 1,18 | 0,72 / 1,75 | +22,1 | 8.235 | 0,28 (1,00) | 1/4 segno≠ | -0,07 | 76.859 (-23,7) | x...x |
| C1S2 | 4.858 | -54,0 | 100 (17,0) | 43 | 0,67 | 0,75 / 0,58 | -31,1 | 2.806 | 0,78 (1,00) | 0/4 | -0,30 | 94.795 (-21,1) | ....x |
| C1S3 | 4.360 | -58,7 | 75 (12,8) | 39 | 0,58 | 0,58 / 0,58 | -28,4 | 2.766 | 0,89 (1,00) | 0/4 | -0,27 | 85.243 (-24,0) | ....x |
| C2L2 | 7.640 | -29,5 | 29 (4,9) | 34 | 0,44 | 0,59 / 0,28 | -15,5 | 6.514 | 0,86 (1,00) | 0/4 | 0,03 | 64.013 (-26,7) | ..... |
| C2L3 | 7.992 | -30,4 | 29 (4,9) | 41 | 0,62 | 0,66 / 0,57 | -10,0 | 6.196 | 0,74 (1,00) | 0/4 segno≠ | 0,05 | 66.264 (-25,1) | ..... |
| C2S2 | 11.852 | -17,4 | 33 (5,6) | 58 | 1,46 | 7,93 / 0,78 | -10,4 | 8.327 | 0,07 (1,00) | 0/4 segno≠ | 0,04 | 91.606 (-22,8) | ..... |
| C2S3 | 13.456 | -19,0 | 33 (5,6) | 64 | 1,64 | 6,04 / 1,14 | +3,3 | 9.026 | 0,04 (1,00) | 2/4 segno≠ | 0,02 | 108.934 (-21,2) | x.... |
| C3L2 | 7.097 | -29,0 | 22 (3,7) | 36 | 0,35 | 0,61 / 0,10 | -21,0 | 6.036 | 0,93 (1,00) | 0/4 segno≠ | 0,13 | 61.458 (-24,5) | ..... |
| C3L3 | 8.309 | -21,2 | 22 (3,7) | 46 | 0,64 | 1,13 / 0,21 | -17,9 | 6.423 | 0,70 (1,00) | 0/4 segno≠ | 0,05 | 62.997 (-24,5) | ..... |
| C3S2 | 12.520 | -16,5 | 33 (5,6) | 54 | 1,84 | 1,84 / 1,82 | +7,1 | 8.817 | 0,06 (1,00) | 2/4 | -0,03 | 97.290 (-21,1) | xx... |
| C3S3 | 13.773 | -22,7 | 33 (5,6) | 54 | 1,95 | 1,58 / 4,48 | +17,3 | 9.003 | 0,04 (1,00) | 2/4 | -0,04 | 110.601 (-21,1) | xx... |

Placebo: un trade casuale con gli stessi costi perde in media −0,16/−0,20% (long) e −0,28/−0,32% (short). "W3 + regola" = la regola
opera solo quando W3 è flat (chiusura forzata se W3 entra).

## Lettura
- **Nessuna delle 32 configurazioni passa**: il p grezzo minimo è 0,017–0,043 (2 sotto 0,05, attese 1,6 per caso su 32), dopo
  Bonferroni sono tutte 1. Nessuna ha ≥ 20 trade per metà insieme a PF > 1,2 in entrambe le metà.
- (a) Momentum: i long A1 guadagnano nel 2021–23 (PF 1,55–1,63) e perdono dal 2024 (0,96–0,99): stesso schema delle rotture 4h
  (lezione 82). A2 nel verso del regime è quasi una copia di W3 (correlazione 0,36–0,39) e combinata la peggiora (53k).
- (b) Ritorno alla media: negativo come nell'intraday (lezione 78). RSI(2) nel verso del regime funziona nel 2021–23 (PF 1,21–1,88) e
  crolla dal 2024 (0,48–0,78); contro regime gli short perdono −66/−80% e B3 (fade dei movimenti > 2,5 ATR) perde in tutte e 4 le versioni.
- (c) Flussi: funding contrarian long solo nel 2024→ (PF IS 0,72–0,97), short in perdita (−51/−56%). C2S3 e C3S3 sono i migliori
  (PF 1,64–1,95, 33 trade, +35/+38%) ma con 9–13 trade in una delle metà, vicini 0–2/4 e p corretto 1.
- Unica traccia: gli short di flusso (C2S3, C3S2, C3S3) usati quando W3 è flat portano W3 da 78k a 97–111k con DD invariato
  (MAR 2,24–2,40 contro 1,99), ma sono **8–13 trade** in sei anni, placebo della combinazione p 0,017–0,038 non corretto
  (≈ 0,5 corretto) e le stesse regole da sole non passano i vicini: è un risultato a gradino, non un vantaggio dimostrato.
- Limite: il segno grezzo del delta taker è sbilanciato (nel 2021 quasi sempre negativo), quindi A1 e C3 long scattano poco nel
  2021; la versione con z-score non è stata provata (non preregistrata).

## Verdetto
Swing BTC 2–3 giorni con momentum, ritorno alla media o flussi: **non accettabile**. Nessuna regola batte il caso dopo la
correzione per 32 prove; i vantaggi del 2021–23 si invertono dal 2024. Gli short di flusso nei periodi flat di W3 restano
**solo su carta** come ipotesi da verificare su dati nuovi (dal 2027), senza ritoccare le soglie.

## Lezione proposta per RESEARCH.md
"Swing BTC 2–3 giorni (notte 15/11, N2): 8 regole preregistrate (Donchian 10/20 con flussi o regime W3, RSI(2) nel verso e contro il
regime, fade > 2,5 ATR, funding estremo, OI + spot, aggressione taker spot), long e short, giornaliero dal 2021 con costi perp,
funding e ritardo dei dati perp: 0/32 accettabili (p corretto 1, nessuna con PF > 1,2 in entrambe le metà e ≥ 20 trade per metà).
Il momentum e l'RSI(2) nel verso del regime funzionano nel 2021–23 e si invertono dal 2024; il ritorno alla media contro regime e il
fade degli eccessi perdono fino a −80%. Unica traccia: short su aggressione taker spot / OI in aumento quando W3 è flat (W3 78k → 97–111k,
DD invariato) ma su 8–13 trade: solo carta, da rivedere con dati 2027. Non riproporre swing di 2–3 giorni su prezzo/RSI/funding."
