# Peso del capitale fra BTC ed ETH con W3.2 · 25/11/2026

**Verdetto: la regola preregistrata sceglie BTC 100% (tutto il capitale crypto su BTC, ETH a zero) e la scelta passa tutti e
quattro i criteri in OOS: per il PREREG il cambio va proposto all'utente.** Però non è una scoperta nuova: è lo stesso fatto visto
sei volte, cioè W3.2 su BTC ha reso più di W3.2 su ETH in quasi ogni anno. Le regole di W3 sono state costruite su BTC: per BTC il
2023–26 non è un vero fuori campione, per ETH sì, e questo favorisce BTC. Inoltre più BTC non riduce il DD, lo aumenta un po'. Il
ricampionamento dà alla scelta il 73% di probabilità di battere il 50/50 su 3 anni: c'è comunque un 27% di probabilità di fare
peggio. Proposta: BTC 100% come esito formale; 2/3–1/3 (40.000 + 20.000 $) come compromesso, non preregistrato, che conserva
metà della diversificazione. Finché l'utente non decide resta il 50/50. Nessuna modifica al tool né ai capitali (PREREG c7d618a).

## Cosa è stato provato
- Trade di W3.2 da `radar.weekly.simulate` invariato (R 0,25, trailing 2,5 ATRw) su BTC ed ETH, dati di
  `research/w32_asset2/crypto/data`, dal 2020-06-01 al 2026-11-24. Ogni asset ha il suo conto, che parte flat all'inizio del periodo.
- Pesi BTC 50 / 60 / 2/3 / 75 / 100%, il resto su ETH. Modo A senza ribilanciamento (come oggi); modo B ribilanciamento ogni 1° gennaio.
- Scelta sul solo IS 2020-06 → 2022-12 (CAGR/DD più alto con DD ≥ −30%); giudizio in OOS 2023-01 → 2026-11 con i 4 criteri.
- Esecuzione: `python3 run.py` (~3 s) → `out.txt`, `risultati.csv`.

**Controlli** (tutti superati): BTC dal 06/2020 225.069 $, DD −21,1%, 17 trade; ETH 53.394 $, DD −27,5%, 16 trade; trade identici
uno per uno a `w32_asset2/trades_crypto.csv`; 50/50 A dal 06/2020 139.232 $, CAGR/DD 2,44 (= q6); 2/3 A 2,62 (= revisione critica).

## Risultati (conto unico da 10.000 $; C/DD = CAGR/DD; anno peggiore con 2020 e 2026 parziali)
| BTC · modo | IS 2020-06 → 22: finale · DD · C/DD | OOS 2023 → oggi: finale · CAGR · DD · C/DD · anno peggiore | Intero 2020-06 →: finale · CAGR · DD · C/DD |
|---|---|---|---|
| **50 A (in uso)** | 43.638 · −13,0 · 5,92 | **25.968 · 27,8 · −24,5 · 1,13** · 2025 +8,1% | 139.232 · 50,1 · −20,6 · 2,44 |
| 50 B | 41.901 · −12,8 · 5,79 | 25.737 · 27,5 · −24,5 · 1,12 · 2025 +9,4% | 118.151 · 46,4 · −19,9 · 2,33 |
| 60 A | 47.068 · −13,1 · 6,28 | 27.384 · 29,5 · −25,0 · 1,18 · 2025 +7,3% | 156.399 · 52,9 · −20,7 · 2,55 |
| 60 B | 45.393 · −12,9 · 6,16 | 27.165 · 29,2 · −25,0 · 1,17 · 2025 +8,5% | 135.741 · 49,6 · −20,1 · 2,47 |
| 2/3 A | 49.355 · −13,1 · 6,51 | 28.328 · 30,6 · −25,3 · 1,21 · 2025 +6,8% | 167.844 · 54,5 · −20,8 · 2,62 |
| 2/3 B | 47.800 · −13,0 · 6,40 | 28.127 · 30,4 · −25,3 · 1,20 · 2025 +7,9% | 148.455 · 51,6 · −20,3 · 2,55 |
| 75 A | 52.214 · −13,2 · 6,79 | 29.507 · 32,0 · −25,8 · 1,24 · 2025 +6,3% | 182.150 · 56,5 · −20,9 · 2,70 |
| 75 B | 50.897 · −13,1 · 6,70 | 29.340 · 31,8 · −25,8 · 1,24 · 2025 +7,1% | 165.512 · 54,2 · −20,5 · 2,65 |
| **100 A = B (scelta IS)** | **60.791 · −13,8 · 7,31** | **33.046 · 35,9 · −27,0 · 1,33** · 2025 +4,9% | 225.069 · 61,7 · −21,1 · 2,92 |

Nessun anno negativo per nessuna combinazione. Il modo B fa sempre un po' peggio del modo A: il ribilanciamento toglie a BTC, che
rende di più. Il buy & hold (dal 06/2020: BTC 63.073 $, DD −76,6%; ETH 72.266 $, DD −79,3%) resta molto sotto in CAGR/DD.

**Date di partenza (fino a oggi), C/DD · DD:**
| Inizio | 50 A | 60 A | 2/3 A | 75 A | 100 |
|---|---|---|---|---|---|
| 2020-06 | 2,44 · −20,6 | 2,55 · −20,7 | 2,62 · −20,8 | 2,70 · −20,9 | 2,92 · −21,1 |
| 2020-09 | 2,40 · −20,6 | 2,53 · −20,8 | 2,61 · −20,9 | 2,70 · −20,9 | 2,95 · −21,1 |
| 2021-01 | 1,80 · −20,2 | 1,86 · −20,4 | 1,90 · −20,6 | 1,94 · −20,7 | 2,07 · −21,1 |
| 2021-06 | 1,40 · −20,3 | 1,47 · −20,5 | 1,52 · −20,6 | 1,58 · −20,8 | 1,74 · −21,1 |
| 2022-01 | 1,32 · −20,2 | 1,40 · −20,5 | 1,45 · −20,6 | 1,51 · −20,7 | 1,68 · −21,1 |
| 2023-01 | 1,13 · −24,5 | 1,18 · −25,0 | 1,21 · −25,3 | 1,24 · −25,8 | 1,33 · −27,0 |

## Criteri (scelta BTC 100%, OOS 2023-01 → oggi)
1. C/DD > 50/50 A: **sì** (1,33 contro 1,13).
2. Togliendo il trade migliore di BTC (long 12/02/2024, +42,2%) e quello di ETH (long 22/01/2024, +57,3%): **sì** (23.233 $, C/DD
   0,89 contro 17.622 $, 0,64).
3. Almeno 4 delle 6 date di partenza: **sì, 6 su 6**.
4. DD non peggiore di oltre 3 punti: **sì, al limite** (−27,0 contro −24,5: 2,5 punti peggio).

Descrittivo, non preregistrato: anche 60, 2/3 e 75% in modo A passano tutti e quattro i criteri (6/6 date; DD OOS −25,0 / −25,3 /
−25,8). **Ricampionamento** (5.000 estrazioni, blocchi di 13 settimane, 3 anni): BTC 100% batte il 50/50 in C/DD nel 72,6% dei
casi, nel finale nell'82,5%, ma ha un DD più piccolo solo nel 38,5%; differenza di C/DD mediana +0,54 (5°–95° percentile −1,48 /
+3,06). Per confronto 2/3 A batte il 50/50 nel 79,5%: rischia meno di sbagliare perché si allontana meno dal 50/50.

## Cosa dicono i dati
- **Non è ETH che pesa sul DD.** Il DD massimo del 50/50 (06/10/2025 → 14/01/2026, −20,6%) viene da BTC per 16,7 punti e da ETH
  per 3,8: al picco BTC era già il 79% del conto, perché nel modo A la quota che rende di più cresce da sola. Con più BTC il DD
  peggiora di poco (−20,6 → −21,1 dal 2020; −24,5 → −27,0 dal 2023). La correlazione settimanale dei due conti è solo 0,33.
- **2/3–1/3 sembra meglio perché BTC rende di più.** Conto BTC / conto ETH per anno: 2020 (da giugno) +133% / +35% · 2021 +118% /
  +104% · 2022 +19% / −4% · 2023 +46% / +22% · 2024 +103% / +28% · 2025 +5% / +14% · 2026 +19% / +14%. ETH vince solo nel 2025.
  Il distacco viene soprattutto dal 2020, dal 2023 e dal 2024.
- **La griglia non poteva scegliere una via di mezzo.** Il C/DD cresce con il peso di BTC in ogni periodo e in ogni data: la
  regola "C/DD massimo" sceglie per forza l'estremo. I 6 confronti si sovrappongono quasi tutti: valgono come una sola prova.
- **Il vantaggio di BTC è in parte costruito.** W2, MACD, F1, il trailing e il rischio 25% sono stati scelti guardando BTC
  2018–2026; per ETH le stesse regole sono un vero fuori campione. Una parte del distacco BTC − ETH viene da questa scelta e non si
  ripeterà per forza.

## Cosa significa per l'operatività (sui 60.000 $ attuali)
| Peso | BTC | ETH | DD OOS sul conto | Finale OOS da 60.000 $ (2023 → oggi) |
|---|---|---|---|---|
| 50/50 (in uso) | 30.000 $ | 30.000 $ | −24,5% ≈ −14.700 $ | ≈ 155.800 $ |
| 2/3–1/3 | 40.000 $ | 20.000 $ | −25,3% ≈ −15.200 $ | ≈ 170.000 $ |
| 75/25 | 45.000 $ | 15.000 $ | −25,8% ≈ −15.500 $ | ≈ 177.000 $ |
| 100/0 | 60.000 $ | 0 | −27,0% ≈ −16.200 $ | ≈ 198.300 $ |

Il segnale di ciascun asset non cambia; cambiano solo `RADAR_CAPITAL` e `RADAR_ETH_CAPITAL` (con 100/0 il conto ETH si chiude).
Modo A: si fissa il peso una volta, poi le quote crescono da sole; ribilanciare ogni gennaio non serve. Il cambio va fatto da flat
o alla chiusura di una posizione, non a metà trade. Decide l'utente.

## Limiti
- Un solo campione di 6,5 anni con due asset; le 6 date di partenza e l'OOS si sovrappongono.
- Bias di sviluppo a favore di BTC (vedi sopra); il già visto 2/3 (2,62 / 1,90 / 1,21) era noto prima del PREREG.
- BTC 100% elimina la diversificazione: un periodo in cui W3.2 fallisce su BTC non avrebbe nessun cuscinetto. Nel campione non è
  mai successo, quindi i numeri non lo misurano.
- Il criterio 4 passa con 0,5 punti di margine.

## Deviazioni dal PREREG (dichiarate)
1. Ogni periodo (IS, OOS, ciascuna data di partenza) è simulato da flat, con ciascun conto da 10.000 $ all'inizio (come q6).
2. Modo B: ribilanciamento alla chiusura del 31/12, rendimenti giornalieri.
3. Criterio 2: il trade migliore (P&L, posizione aperta inclusa) si toglie azzerando i rendimenti giornalieri del conto fra entrata e
   uscita; il 50/50 di confronto è calcolato sulle stesse curve ridotte.
4. Scelta IS con C/DD non arrotondato; 100 A e 100 B sono identici, si riporta A.
5. Ricampionamento: rendimenti settimanali (domenica) dei due conti dal 06/2020, 12 blocchi = 156 settimane, DD settimanale, modo B
   ribilanciato ogni 52 settimane, seme 7; "batte" = C/DD più alto.
6. Aggiunti come descrittivi, non preregistrati: i 4 criteri per gli altri pesi, i rendimenti annui, la scomposizione del DD.

## Lezione 124 proposta per RESEARCH.md
**Lezione 124**: peso del capitale fra BTC ed ETH con W3.2 (research/peso_btc_eth, PREREG c7d618a). Dal 06/2020 il CAGR/DD del
conto unico cresce con la quota di BTC in ogni periodo e in ogni data di partenza (50/50 2,44 · 2/3 2,62 · 100% 2,92; OOS 2023→
1,13 · 1,21 · 1,33); la regola preregistrata sceglie BTC 100% e passa i 4 criteri (6/6 date, DD OOS −27,0 contro −24,5).
Ricampionamento: 73% di probabilità di battere il 50/50 su 3 anni. Il vantaggio non viene da un DD più piccolo (ETH pesa 3,8 punti
su 20,6 nel DD massimo; più BTC peggiora un po' il DD) ma dal rendimento più alto di BTC (2020, 2022–24; ETH vince solo nel 2025),
in parte gonfiato dal fatto che W3 è stata sviluppata su BTC. Ribilanciare ogni gennaio peggiora sempre. Una griglia di pesi che
cresce in modo monotono sceglie per forza l'estremo: nei prossimi studi va dichiarato prima un limite di concentrazione. Proposto
all'utente: 100/0 come esito formale, 2/3–1/3 come compromesso; senza la sua decisione resta il 50/50.
