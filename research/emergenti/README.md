# emergenti · W3.2 e varianti sulle monete poco capitalizzate · NESSUNA VARIANTE OPERABILE (0 su 10) · solo short da tenere sulla carta

PREREG `PREREG.md` (commit **1110e53**, da solo, prima dei rendimenti); dati e conteggi in `DATI.md` (commit c7bd42d);
deviazioni in `DEVIAZIONI.md`. Motore `engine.py` (copia parametrizzata di `radar.weekly.simulate`, controllo: BTC 84.820 $ ed
ETH 39.572 $, trade identici). Universo di giudizio: monete con rank 101–200 nella classifica di inizio anno (punto nel tempo),
budget 10.000 $ = 1% del capitale, al massimo 5 posizioni con margine pari a 1/5 del budget, tutte in perp, costi 0,2% per lato
più funding reale. Dal 01/01/2021 al 24/11/2026.

**Verdetto (soglie del PREREG; criteri: 1 CAGR/DD > B&H equipesato · 2 DD ≥ −40% · 3 WR ≥ 50% · 4 positiva in IS, OOS e
ultimo anno · 5 ≥ 20 operazioni · 6 conferma · 7 placebo con Holm su m = 10)**
- **V1 · W3.2 com'è, long e short: NO** (falliti 2,3,4,6,7). 18.733 $, DD −55%, WR 43%, OOS −19%, placebo p 0,55.
- **V2 · solo long: NO** (2,3,4,6,7). **5.374 $ (−46%)**, DD −81%, WR 28%. Smentisce "i long sono in netto positivo".
- **V3 · solo short: NO, ma è la più vicina** (fallisce solo il 7). 13.883 $, DD −20,8%, WR 51%, positiva in IS, OOS e ultimo
  anno, regge senza il 10% migliore (12.152 $); placebo p 0,0082 → **0,082 dopo Holm**.
- **V4 · leva adattiva 2x: NO** (2,3,4,6,7). 20.205 $ ma DD −96%: ogni stop costa quasi tutta la quota.
- **V5 · leva adattiva 5x: NO** (2,3,4,6,7). 15.537 $, DD −98%.
- **V6 · filtri di qualità: NO** (2,3,4,6,7). 14.188 $, DD −47%; peggiora V1 in IS e OOS.
- **V7 · solo con BTC: NO** (2,3,4,6,7). 7.994 $, DD −66%.
- **V8 · solo contro BTC: NO** (3,4,6,7). 10.911 $, DD −34%, WR 37%, IS −9%.
- **V9 · trailing 2,0 ATRw: NO** (2,3,4,6,7). 12.575 $, peggio di V1.
- **V10 · uscita EMA 10: NO** (2,3,4,6,7). 20.048 $, DD −60%, OOS −31%.
Nessuna variante "migliora" W3.2 com'è (CAGR/DD più alto in IS **e** in OOS). Il criterio 1 lo passano tutte solo perché il
buy & hold equipesato delle emergenti è disastroso (2.326 $, DD −97%).

## 1. Tabella (budget 10.000 $ = 1% del capitale, max 5 posizioni)
| Variante | Finale | CAGR | DD giorn. | CAGR/DD | Oper. | WR | IS 2021–23 | OOS 2024→ | Ultimo anno | Senza 10% migliore | Vicini (finale) | p · Holm | Sul capitale totale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V1 W3.2 com'è | 18.733 | 11,2% | −55,4 | 0,20 | 198 | 43% | +183% | −19% | −4% | 3.584 | 17.627 · 18.733 | 0,55 · 1 | +0,87%, DD −0,55% |
| V2 solo long | 5.374 | −10,0% | −80,7 | −0,12 | 230 | 28% | +119% | −67% | −2% | 985 | 4.936 · 5.374 | 0,95 · 1 | −0,46% |
| **V3 solo short** | **13.883** | 5,7% | **−20,8** | **0,27** | 94 | **51%** | +22% | +9% | +16% | **12.152** | 13.615 · 13.883 | **0,008 · 0,082** | +0,39%, DD −0,21% |
| V4 leva adattiva 2x | 20.205 | 12,7% | −96,1 | 0,13 | 193 | 43% | +1.508% | −82% | −16% | 189 | 20.034 · 20.942 | 0,46 · 1 | +1,0%, DD −0,96% |
| V5 leva adattiva 5x | 15.537 | 7,8% | −97,9 | 0,08 | 193 | 43% | +2.054% | −89% | −17% | 104 | 13.345 · 18.398 | 0,50 · 1 | |
| V6 qualità | 14.188 | 6,1% | −47,0 | 0,13 | 162 | 43% | +115% | −35% | +2% | 5.056 | 11.791 · 4.560 | 0,56 · 1 | |
| V7 con BTC | 7.994 | −3,7% | −66,3 | −0,06 | 163 | 40% | +113% | −50% | −14% | 3.596 | 7.573 · 7.994 | 0,98 · 1 | |
| V8 contro BTC | 10.911 | 1,5% | −33,8 | 0,04 | 76 | 37% | −9% | +15% | +27% | 6.982 | 10.686 · 10.911 | 0,11 · 0,95 | |
| V9 trailing 2,0 | 12.575 | 4,0% | −50,4 | 0,08 | 218 | 40% | +132% | −20% | −5% | 2.883 | 9.169 · 18.733 | 0,73 · 1 | |
| V10 uscita EMA 10 | 20.048 | 12,5% | −59,8 | 0,21 | 287 | 42% | +270% | −31% | +6% | 3.152 | 20.871 · 15.393 | 0,51 · 1 | |
| B&H equipesato emergenti | 2.326 | −21,9% | −97,2 | −0,23 | | | +41% | −83% | −55% | | | | |
| Contesto: W3.2 su BTC (10k) | 84.820 | | −21,1 | | 17 | | | | | | | | |
| Contesto: B&H BTC | 20.686 | | −76,6 | | | | | | | | | | |

Vicini: V1–V3 e V7–V8 costi 0,4% per lato · mantenimento 2,5%; V4–V5 margine 0,03 · 0,08; V6 (26 sett., 5 M$, 0,25σ) ·
(104 sett., 20 M$, 1,0σ); V9 trailing 1,5 · 2,5; V10 EMA 8 · 13. Placebo: 5.000 prove, mediana del placebo di V3 −0,06 contro
0,27. Ogni periodo riparte da 10.000 $. Il quadro è lo stesso degli studi precedenti: il 2021 e il 2023 fanno il guadagno dei long,
dal 2024 si perde.

## 2. Effetto della leva (stessi segnali di V1; liquidazione simulata sui minimi/massimi giornalieri)
| Size per quota (margine = 1/5 del budget) | Finale | DD | Oper. | Liquidazioni |
|---|---|---|---|---|
| W3.2 (nozionale = quota × min(1; 0,25/d); in mediana 0,36) | 18.733 | −55% | 198 | 0 |
| 1x a quota piena | 28.512 | −83% | 196 | 1 |
| **2x fisso** | **7.480** | −98% | 197 | **14** |
| **5x fisso** | **0 (budget azzerato)** | −100% | 70 | **40 su 70** |
| Adattiva min(2; 1/(d+0,05)) = V4 | 20.205 | −96% | 193 | 0 |
| Adattiva min(5; 1/(d+0,05)) = V5 | 15.537 | −98% | 193 | 0 |
| Per rischio: 5% del budget allo stop, max 2x | 18.713 | −55% | 198 | 0 |

Lo stop di W3.2 sulle emergenti è in mediana al 50% (long) e all'83% (short) dall'ingresso. A 5x è sempre oltre la
liquidazione; a 2x lo è nel 52% dei long e nel 93% degli short (`DATI.md` §5). La leva adattiva evita le liquidazioni, ma
porta il rischio per operazione quasi al 100% della quota: il DD sale a −96/−98%. **L'unica size coerente con lo stop è
quella di W3.2 (esposizione ≤ 1x della quota): la leva serve solo a impegnare meno margine, non ad aumentare l'esposizione.**
Tetto di posizioni (descrittivo): 3 → 11.648 $ (DD −52%); 10 → 15.532 $ (DD −43%). Uscita forzata dopo 4/8 settimane:
16.144 / 17.713 $, DD −66%.

## 3. "I long sono in netto positivo": NON VERIFICATA, è vero il contrario
Tutti i 470 segnali long sulle emergenti dal 2021 (prima del tetto di 5 posizioni, esito per quota con la size di W3.2):
**WR 29%, mediana −5,9%, somma −82%**. Per anno: 2021 +550% (WR 47%), 2022 −93%, 2023 +496%, 2024 −437%, 2025 −341% (WR 7%),
2026 −256% (WR 18%). **Ultimi 12 mesi: 62 long, WR 18%, media −4,3%.** Contro BTC: 28 segnali, WR 32%, somma +56% (troppo pochi
per dire qualcosa); con BTC 271, WR 28%; storia < 52 settimane: 40, WR 38%, somma −4%. Gli short sono la parte che funziona: 782
segnali, WR 48%, somma +553%, positivi nel 2021–22 e nel 2025–26, negativi nel 2023–24.
Long dello scanner al 24/11 (simulazione per moneta, per quota): JST +50% (aperto dal 13/07), NIGHT +4,5%, SENT +0,1%,
PIEVERSE −11%, BEAMX −10%. Una settimana non dice nulla: è il campione che l'utente vede, non quello storico (lezione 79).

## 4. Variante migliore: V3 (solo short). Operazioni eseguite
94 operazioni su 73 monete; per anno: 2021 6 (WR 100%), 2022 20 (65%), 2023 20 (35%), 2024 21 (29%), 2025 13 (54%), 2026 14 (64%).
Uscite: EMA 45, distribuzione 33, trailing 11, aperte 5; migliore +29,9%, peggiore −21,0% per quota. Il p del placebo
(0,0082) è buono ma non passa Holm su 10 ipotesi. A posteriori (non giudicato): V3 a quota piena 1x 27.122 $ (DD −59%), V3 2x
fisso 9.849 $ (13 liquidazioni). Elenco completo qui sotto (§9) e in `data/trades_V3.csv` (`pnl` = esito per quota, `m` = margine).

## 5. Cosa significa per l'utente (1% del capitale, Bitget/OKX, leva 2x/5x)
- **Non operare queste monete con capitale reale: nessuna variante passa.** Il budget dell'1% avrebbe reso +0,87% del capitale
  totale in sei anni con W3.2 com'è (DD del budget −55%) e −0,46% con i soli long.
- **Leva**: 5x non è mai coerente con lo stop di W3.2 (100% degli ingressi oltre la liquidazione; 5x fisso azzera il budget).
  2x solo se lo stop è più vicino del 44% (circa metà dei long, quasi nessuno short). Se mai si opera: margine isolato pari alla
  quota, esposizione = size di W3.2 (≤ 1x); la leva della borsa si usa solo per non bloccare margine.
- **Posizioni**: con 5 quote il DD resta oltre il 40% per tutte le varianti tranne V3 e V8.
- **Regola da tenere sulla carta (non in uso)**: V3 = short di W3.2 sulle monete con rank 101–200 della classifica di inizio
  anno, size di W3.2 nella quota, al massimo 5 posizioni, uscite di W3.2. Registro in avanti dal 30/11/2026; da riconsiderare con
  ≥ 20 operazioni chiuse, WR ≥ 50%, rendimento positivo e DD del budget ≥ −25%.
- **Long sulle emergenti**: da non seguire, nemmeno "contro BTC".

## 6. Proposte per lo scanner (solo proposta, nulla è stato toccato)
1. Per ogni posizione mostrare la distanza dello stop in % e la leva massima compatibile 1/(d+0,05), con l'avviso "oltre la
   liquidazione a 2x/5x".
2. Accanto ai long sulle monete fuori dalla top 100: "storico: WR 29%, mediana −6% per operazione (studio emergenti)".
3. Non evidenziare i "nuovi long" sulle emergenti; registro sulla carta solo per gli short (V3), sulla falsariga del blocco TRX.
4. Nello scanner il verso di BTC va calcolato alla data del segnale, non alla settimana corrente (NIGHT e BEAMX erano "con BTC"
   al segnale, lo scanner li mostra "opposto").

## 7. Limiti
Classifiche storiche solo fino al 200° posto (la fascia 201–500 storica manca; la vista "di oggi" 101–500 fa 9.698 $, OOS
−27%, ed è comunque ottimistica). Liste annuali; istantanea 2026 del 16/11/2025. Delisting: la posizione si chiude
all'ultimo prezzo scambiato. Operabilità storica su Bitget/OKX ignota. Funding di novembre 2026 mancante sui perp senza OKX.
Liquidazione semplificata (mantenimento fisso, nessuna commissione di liquidazione, candele giornaliere). Un segnale scartato
per quote piene non cambia la simulazione della moneta. Il placebo esce a tempo (senza stop). W3.2 è stata sviluppata su BTC.
V3 dipende dal 2021–22 e dal 2025–26 (negativa nel 2023–24 per operazione).

## 8. Lezione 131 proposta
**Lezione 131**: monete emergenti (rank 101–200 alla classifica di inizio anno, punto nel tempo; budget 1%, 5 posizioni,
0,2% per lato; research/emergenti, PREREG 1110e53): 0 varianti operabili su 10. W3.2 com'è 18,7k $ su 10k di budget (DD −55%,
OOS −19%); **solo long 5,4k $ (DD −81%, WR 28%; ultimi 12 mesi WR 18%)**: "i long sono in netto positivo" è falso. Solo short:
13,9k $, DD −21%, WR 51%, positivi in IS/OOS/ultimo anno, regge senza il 10% migliore, ma il placebo non passa Holm (0,082): da
tenere sulla carta. Lo stop di W3.2 sulle emergenti è al 50% (long) e all'83% (short) dall'ingresso: a 5x è sempre oltre la
liquidazione (5x fisso azzera il budget), a 2x lo è per metà dei long; la leva adattiva evita le liquidazioni ma porta il DD a
−96%. Con stop larghi la leva non aumenta il vantaggio, solo il rischio: sulle monete piccole si usa la size di W3.2 (≤ 1x) o
nulla. Filtri di qualità, cancello BTC (con o contro), trailing 2,0 e uscita EMA 10 non migliorano.

## 9. V3 · elenco delle operazioni
| # | Moneta | Ingresso | Uscita | Motivo | Stop d | Esito per quota | Margine $ | BTC |
|---|---|---|---|---|---|---|---|---|
| 1 | BAND | 2021-11-15 | 2022-02-14 | dist | 71% | +19.3% | 2.000 | flat |
| 2 | BAL | 2021-11-15 | 2021-12-13 | dist | 76% | +12.4% | 2.000 | flat |
| 3 | ALPHA | 2021-11-22 | 2022-04-04 | ema | 85% | +13.7% | 2.037 | flat |
| 4 | BTS | 2021-12-06 | 2022-05-16 | dist | 114% | +14.5% | 2.126 | flat |
| 5 | SRM | 2021-12-13 | 2022-03-21 | dist | 130% | +6.2% | 2.137 | flat |
| 6 | VIC | 2021-12-27 | 2022-02-28 | dist | 82% | +15.1% | 1.948 | flat |
| 7 | CELR | 2022-02-14 | 2022-04-04 | ema | 166% | -7.1% | 2.328 | con |
| 8 | CTSI | 2022-03-14 | 2022-03-21 | dist | 174% | -2.7% | 2.302 | con |
| 9 | NKN | 2022-03-21 | 2022-04-04 | ema | 133% | -10.9% | 2.342 | con |
| 10 | REN | 2022-03-28 | 2022-05-16 | dist | 96% | +15.7% | 2.168 | con |
| 11 | CTSI | 2022-04-04 | 2022-05-16 | dist | 93% | +16.1% | 2.179 | flat |
| 12 | REEF | 2022-04-04 | 2022-05-30 | dist | 137% | +12.3% | 2.179 | flat |
| 13 | SXP | 2022-04-11 | 2022-07-18 | dist | 90% | +19.9% | 2.207 | flat |
| 14 | ALPHA | 2022-06-13 | 2022-12-12 | dist | 279% | +2.4% | 2.512 | flat |
| 15 | SKL | 2022-06-13 | 2022-06-20 | dist | 282% | +0.1% | 2.512 | flat |
| 16 | COTI | 2022-06-13 | 2022-07-04 | dist | 185% | +1.1% | 2.512 | flat |
| 17 | QTUM | 2022-06-13 | 2022-08-01 | dist | 151% | -5.6% | 2.381 | flat |
| 18 | RLC | 2022-06-27 | 2022-07-04 | dist | 182% | -6.9% | 2.512 | flat |
| 19 | OGN | 2022-07-04 | 2022-07-11 | dist | 132% | +0.9% | 2.493 | flat |
| 20 | SKL | 2022-07-04 | 2023-02-06 | ema | 282% | +1.7% | 2.389 | flat |
| 21 | OCEAN | 2022-07-11 | 2022-10-24 | dist | 188% | +0.1% | 2.490 | flat |
| 22 | ZRX | 2022-07-18 | 2022-09-26 | dist | 146% | +1.4% | 2.481 | flat |
| 23 | AUDIO | 2022-08-08 | 2023-01-24 | trail | 170% | +2.8% | 2.394 | flat |
| 24 | ONT | 2022-10-03 | 2023-01-30 | ema | 93% | -0.0% | 2.520 | con |
| 25 | COTI | 2022-10-24 | 2023-01-23 | ema | 81% | +5.1% | 2.522 | con |
| 26 | INJ | 2022-12-12 | 2023-01-23 | ema | 106% | -4.6% | 2.583 | con |
| 27 | KAVA | 2023-02-06 | 2023-03-13 | dist | 77% | -1.2% | 2.505 | contro |
| 28 | HNT | 2023-02-06 | 2023-03-20 | dist | 117% | +9.2% | 2.505 | contro |
| 29 | ROSE | 2023-02-06 | 2023-02-13 | ema | 72% | -14.8% | 2.505 | contro |
| 30 | GMT | 2023-02-13 | 2023-03-13 | dist | 107% | +4.1% | 2.461 | contro |
| 31 | WAVES | 2023-02-13 | 2023-02-20 | ema | 122% | -6.2% | 2.461 | contro |
| 32 | SUSHI | 2023-02-13 | 2023-02-20 | ema | 74% | -4.2% | 2.224 | contro |
| 33 | GALA | 2023-02-27 | 2023-03-13 | dist | 92% | +3.9% | 2.412 | contro |
| 34 | WAVES | 2023-02-27 | 2023-06-24 | trail | 109% | -0.8% | 2.026 | contro |
| 35 | IOST | 2023-03-13 | 2023-03-20 | ema | 59% | -6.5% | 2.455 | contro |
| 36 | SKL | 2023-03-13 | 2023-03-20 | ema | 86% | -3.5% | 2.455 | contro |
| 37 | BNX | 2023-03-13 | 2024-04-29 | ema | 12767% | -0.1% | 2.455 | contro |
| 38 | KAVA | 2023-04-03 | 2023-05-15 | ema | 75% | -7.1% | 2.432 | contro |
| 39 | GALA | 2023-04-10 | 2023-04-17 | ema | 81% | -3.2% | 2.426 | contro |
| 40 | GMT | 2023-04-17 | 2023-11-06 | ema | 83% | +15.3% | 2.390 | contro |
| 41 | OMG | 2023-04-17 | 2023-11-06 | ema | 72% | +20.5% | 2.390 | contro |
| 42 | ANKR | 2023-05-15 | 2023-10-30 | ema | 71% | +4.9% | 2.521 | contro |
| 43 | CKB | 2023-06-26 | 2023-10-30 | ema | 74% | +0.7% | 2.040 | contro |
| 44 | OP | 2023-10-30 | 2023-11-06 | ema | 51% | -4.5% | 2.570 | contro |
| 45 | MAGIC | 2023-11-20 | 2023-11-27 | ema | 67% | -13.0% | 2.535 | contro |
| 46 | ENS | 2023-12-18 | 2023-12-25 | ema | 41% | -5.3% | 2.469 | contro |
| 47 | CVX | 2024-01-01 | 2024-02-12 | dist | 46% | +3.2% | 2.443 | contro |
| 48 | ZEC | 2024-01-01 | 2024-02-22 | trail | 40% | -5.4% | 2.443 | contro |
| 49 | DASH | 2024-01-01 | 2024-02-26 | ema | 38% | +2.6% | 2.443 | contro |
| 50 | ENJ | 2024-01-08 | 2024-02-19 | ema | 54% | -6.6% | 2.428 | flat |
| 51 | GMX | 2024-04-08 | 2024-06-06 | trail | 58% | -4.5% | 2.412 | flat |
| 52 | ZEC | 2024-04-15 | 2024-05-27 | ema | 63% | -8.0% | 2.484 | flat |
| 53 | CVX | 2024-04-15 | 2024-06-17 | ema | 78% | -5.1% | 2.484 | flat |
| 54 | XEM | 2024-06-24 | 2024-07-22 | dist | 145% | -3.4% | 2.324 | flat |
| 55 | GMT | 2024-07-15 | 2024-09-30 | ema | 90% | -2.7% | 2.325 | flat |
| 56 | ZIL | 2024-07-22 | 2024-11-11 | ema | 61% | +5.2% | 2.298 | flat |
| 57 | MAGIC | 2024-07-29 | 2024-11-25 | ema | 99% | -3.8% | 2.318 | flat |
| 58 | LRC | 2024-07-29 | 2024-11-17 | trail | 84% | -7.4% | 2.283 | flat |
| 59 | ENJ | 2024-07-29 | 2024-11-23 | trail | 90% | -6.6% | 2.318 | flat |
| 60 | MEME | 2024-09-30 | 2024-11-25 | ema | 155% | -2.3% | 2.263 | contro |
| 61 | WLD | 2024-11-11 | 2024-11-25 | ema | 96% | -5.2% | 2.363 | contro |
| 62 | ENS | 2024-11-18 | 2024-11-25 | ema | 69% | -5.3% | 2.168 | contro |
| 63 | MEME | 2024-12-16 | 2025-04-21 | dist | 106% | +19.6% | 2.180 | contro |
| 64 | SFP | 2024-12-16 | 2025-01-06 | ema | 40% | -2.0% | 2.180 | contro |
| 65 | WLD | 2024-12-23 | 2025-05-26 | ema | 106% | +8.8% | 2.214 | contro |
| 66 | TRB | 2024-12-23 | 2025-05-27 | trail | 100% | +4.9% | 2.214 | contro |
| 67 | CELO | 2024-12-23 | 2025-01-06 | ema | 72% | -3.8% | 2.110 | contro |
| 68 | AXL | 2025-01-06 | 2025-02-24 | dist | 92% | +8.8% | 2.016 | contro |
| 69 | SATS | 2025-01-06 | 2026-04-17 | trail | 119% | +18.9% | 2.150 | contro |
| 70 | KAVA | 2025-02-24 | 2025-03-17 | ema | 63% | -3.8% | 2.194 | contro |
| 71 | COMP | 2025-03-17 | 2025-04-01 | trail | 93% | -21.0% | 2.110 | flat |
| 72 | CKB | 2025-04-07 | 2025-07-20 | trail | 161% | -12.4% | 1.667 | flat |
| 73 | GLM | 2025-04-21 | 2025-07-14 | dist | 78% | -0.0% | 2.365 | flat |
| 74 | NOT | 2025-05-26 | 2025-11-24 | dist | 180% | +11.2% | 2.313 | contro |
| 75 | ARKM | 2025-06-02 | 2025-09-15 | ema | 120% | -2.4% | 2.319 | contro |
| 76 | JTO | 2025-07-14 | 2026-02-02 | dist | 72% | +29.9% | 2.312 | contro |
| 77 | ZRO | 2025-07-21 | 2025-09-29 | ema | 85% | -0.4% | 1.858 | contro |
| 78 | PNUT | 2025-09-15 | 2026-08-24 | ema | 184% | +10.8% | 2.263 | contro |
| 79 | ARKM | 2025-09-29 | 2026-01-26 | dist | 75% | +23.0% | 1.850 | contro |
| 80 | ETHFI | 2025-11-24 | 2026-08-17 | ema | 145% | +4.9% | 2.548 | flat |
| 81 | ZK | 2026-01-26 | 2026-02-09 | dist | 136% | +1.2% | 2.298 | con |
| 82 | GALA | 2026-02-02 | 2026-05-04 | dist | 134% | +6.3% | 2.593 | con |
| 83 | ZEN | 2026-02-09 | 2026-05-04 | ema | 145% | -3.1% | 2.637 | con |
| 84 | ATH | 2026-04-20 | 2026-09-28 | ema | 160% | -1.4% | 2.652 | con |
| 85 | SNX | 2026-05-04 | 2026-09-28 | ema | 91% | +4.3% | 2.635 | flat |
| 86 | SUPER | 2026-05-04 | 2026-08-31 | dist | 120% | +2.0% | 2.635 | flat |
| 87 | DEXE | 2026-08-17 | aperta | open | 1053% | +0.8% | 2.717 | con |
| 88 | XEC | 2026-08-31 | 2026-09-07 | ema | 56% | -4.7% | 2.706 | contro |
| 89 | APE | 2026-08-31 | 2026-09-28 | ema | 63% | -9.6% | 2.490 | contro |
| 90 | SAND | 2026-09-07 | 2026-10-02 | trail | 78% | -18.1% | 2.580 | contro |
| 91 | B | 2026-09-28 | aperta | open | 118% | +11.5% | 2.559 | contro |
| 92 | FARTCOIN | 2026-10-12 | aperta | open | 77% | +17.5% | 2.511 | contro |
| 93 | XPL | 2026-10-12 | aperta | open | 96% | +13.1% | 2.511 | contro |
| 94 | CHZ | 2026-10-12 | aperta | open | 68% | +16.5% | 2.145 | contro |
