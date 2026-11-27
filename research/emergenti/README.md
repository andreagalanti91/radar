# emergenti · W3.2 e varianti sulle monete poco capitalizzate · NESSUNA VARIANTE OPERABILE (0 su 10) · solo short da tenere sulla carta

- **PREREG**: `PREREG.md`, commit **1110e53**, committato da solo prima dei rendimenti.
- **Dati e conteggi**: `DATI.md` (commit c7bd42d, riallineato dopo la revisione).
- **Deviazioni**: `DEVIAZIONI.md`.
- **Motore**: `engine.py`, copia parametrizzata di `radar.weekly.simulate`. Controllo: BTC 84.820 $ ed ETH 39.572 $, trade
  identici.
- **Universo di giudizio**: monete con rank 101–200 nella classifica di inizio anno (punto nel tempo).
- **Regole del conto**: budget 10.000 $ = 1% del capitale; al massimo 5 posizioni con margine pari a 1/5 del budget; tutte in
  perp; costi 0,2% per lato più funding reale.
- **Periodo**: dal 01/01/2021 al 24/11/2026.
- **Numeri**: tutti dopo le correzioni della revisione critica (§8).

**Verdetto per variante** (soglie del PREREG). Criteri: 1 CAGR/DD > buy & hold equipesato · 2 DD ≥ −40% · 3 WR ≥ 50% · 4
positiva in IS, OOS e ultimo anno · 5 ≥ 20 operazioni · 6 conferma · 7 placebo con Holm su m = 10.

- **V1 · W3.2 com'è, long e short: NO** (falliti 2,3,4,6,7). 19.783 $, DD −55%, WR 43%, OOS −19%, placebo p 0,53.
- **V2 · solo long: NO** (2,3,4,6,7). **5.374 $ (−46%)**, DD −81%, WR 28%. Smentisce "i long sono in netto positivo".
- **V3 · solo short: NO, ma è la più vicina** (fallisce solo il 7). 13.905 $, DD −20,7%, WR 52%; placebo p 0,0060 → **0,060
  dopo Holm**. Tre cautele:
  - le 5 posizioni aperte valgono +1.442 $ dei +3.905 $ di guadagno, e l'ultimo anno (+16%) è quasi tutto non realizzato;
  - in OOS fa +9% in circa 3 anni con WR 41%;
  - è negativa nei quattro semestri del 2023–24: guadagna nelle fasi ribassiste delle alt.
- **V4 · leva adattiva 2x: NO** (2,3,4,6,7). 17.601 $ ma DD −97%: ogni stop costa quasi tutta la quota.
- **V5 · leva adattiva 5x: NO** (2,3,4,6,7). 14.113 $, DD −98%.
- **V6 · filtri di qualità: NO** (2,3,4,6,7). 13.172 $, DD −52%; peggiora V1.
- **V7 · solo con BTC: NO** (2,3,4,6,7). 7.994 $, DD −66%.
- **V8 · solo contro BTC: NO** (3,4,6,7). 10.926 $, DD −34%, WR 38%, IS −9%.
- **V9 · trailing 2,0 ATRw: NO** (2,3,4,6,7). 12.427 $, peggio di V1.
- **V10 · uscita EMA 10: NO** (2,3,4,6,7). 19.637 $, DD −60%, OOS −31%.

Nessuna variante migliora W3.2 com'è, cioè nessuna ha un CAGR/DD più alto sia in IS sia in OOS. Il criterio 1 lo passano tutte
solo perché il buy & hold equipesato delle emergenti è disastroso (2.352 $, DD −97%).

## 1. Tabella (budget 10.000 $ = 1% del capitale, max 5 posizioni)
| Variante | Finale | CAGR | DD giorn. | CAGR/DD | Oper. | WR | IS 2021–23 | OOS 2024→ | Ultimo anno | Senza 10% migliore | Vicini (finale) | p · Holm | Sul capitale totale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V1 W3.2 com'è | 19.783 | 12,3% | −55,2 | 0,22 | 209 | 43% | +183% | −19% | −4% | 3.444 | 18.548 · 19.783 | 0,53 · 1 | +0,98%, DD −0,55% |
| V2 solo long | 5.374 | −10,0% | −80,7 | −0,12 | 230 | 28% | +119% | −67% | −2% | 985 | 4.936 · 5.374 | 0,96 · 1 | −0,46%, DD −0,81% |
| **V3 solo short** | **13.905** | 5,8% | **−20,7** | **0,28** | 96 | **52%** | +22% | +9% | +16%* | **12.017** | 13.622 · 13.905 | **0,006 · 0,060** | +0,39%, DD −0,21% |
| V4 leva adattiva 2x | 17.601 | 10,1% | −96,8 | 0,10 | 203 | 43% | +1.454% | −82% | −16% | 122 | 17.418 · 18.306 | 0,49 · 1 | |
| V5 leva adattiva 5x | 14.113 | 6,0% | −98,2 | 0,06 | 203 | 43% | +1.985% | −89% | −17% | 51 | 11.727 · 16.779 | 0,52 · 1 | |
| V6 qualità | 13.172 | 4,8% | −51,5 | 0,09 | 171 | 42% | +110% | −35% | +2% | 4.222 | 13.413 · 4.411 | 0,62 · 1 | |
| V7 con BTC | 7.994 | −3,7% | −66,3 | −0,06 | 163 | 40% | +113% | −50% | −14% | 3.596 | 7.573 · 7.994 | 0,99 · 1 | |
| V8 contro BTC | 10.926 | 1,5% | −33,7 | 0,04 | 77 | 38% | −9% | +15% | +27% | 7.149 | 10.694 · 10.926 | 0,08 · 0,75 | |
| V9 trailing 2,0 | 12.427 | 3,8% | −53,6 | 0,07 | 225 | 40% | +138% | −20% | −5% | 3.513 | 9.750 · 19.783 | 0,74 · 1 | |
| V10 uscita EMA 10 | 19.637 | 12,1% | −59,8 | 0,20 | 295 | 41% | +262% | −31% | +6% | 3.038 | 21.533 · 17.553 | 0,53 · 1 | |
| B&H equipesato emergenti | 2.352 | −21,8% | −97,1 | −0,22 | | | +42% | −83% | −55% | | | | |
| Contesto: W3.2 su BTC | 84.820 | | −21,1 | | | | | | | | | | |
| Contesto: B&H BTC | 20.686 | | −76,6 | | | | | | | | | | |

\* Per V3 nell'ultimo anno pesano le 5 posizioni aperte (non realizzate).

Vicini:
- V1–V3 e V7–V8: costi 0,4% per lato · mantenimento 2,5%.
- V4–V5: margine 0,03 · 0,08.
- V6: (26 sett., 5 M$, 0,25σ) · (104 sett., 20 M$, 1,0σ).
- V9: trailing 1,5 · 2,5.
- V10: EMA 8 · 13.

Placebo: 5.000 prove. Esce a tempo senza stop, quindi il p è leggermente ottimistico (DEVIAZIONI §8). Ogni periodo riparte da
10.000 $.

## 2. Effetto della leva (stessi segnali di V1; liquidazione sui minimi/massimi giornalieri)
| Size per quota (margine = 1/5 del budget) | Finale | DD | Oper. | Liquidazioni |
|---|---|---|---|---|
| Size di W3.2: nozionale = quota × min(1; 0,25/d), in mediana 0,37 | 19.783 | −55% | 209 | 0 |
| 1x a quota piena | 24.401 | −85% | 206 | 1 |
| **2x fisso** | **2.971** | −99% | 206 | **15** |
| **5x fisso** | **0 (budget azzerato)** | −100% | 70 | **40 su 70** |
| Adattiva min(2; 1/(d+0,05)) = V4 | 17.601 | −97% | 203 | 0 |
| Adattiva min(5; 1/(d+0,05)) = V5 | 14.113 | −98% | 203 | 0 |
| Per rischio: 5% del budget allo stop, max 2x | 19.761 | −55% | 209 | 0 |

Lo stop di W3.2 sulle emergenti è in mediana al 50% dall'ingresso sui long e all'83% sugli short (`DATI.md` §6). A 5x è sempre
oltre la liquidazione; a 2x lo è nel 52% dei long e nel 93% degli short. La leva adattiva evita le liquidazioni, ma porta il
rischio per operazione quasi al 100% della quota.

**L'unica size coerente con lo stop è quella di W3.2, con esposizione ≤ 1x della quota. La leva serve solo a impegnare meno
margine, non ad aumentare l'esposizione.**

Altre prove descrittive:
- tetto di 3 posizioni: 9.458 $ (DD −59%);
- tetto di 10 posizioni: 14.903 $ (DD −45%);
- uscita forzata dopo 4 settimane: 17.464 $; dopo 8 settimane: 18.341 $ (DD −66% in entrambi i casi);
- V3 a posteriori, non giudicata: quota piena 1x 30.579 $ (DD −54%); 2x fisso 13.778 $ con DD −92% e 12 liquidazioni.

## 3. "I long sono in netto positivo": NON VERIFICATA, è vero il contrario
Campione: i 470 segnali long candidati di V1 (tutti i long W3.2 su monete emergenti al segnale dal 2021, prima del tetto di 5
posizioni). Esito per quota con la size di W3.2: **WR 29%, mediana −5,9%, somma −82%**.

Per anno: 2021 +550% (WR 47%), 2022 −93%, 2023 +496%, 2024 −437%, 2025 −341% (WR 7%), 2026 −256% (WR 18%).
**Ultimi 12 mesi: 62 long, WR 18%, media −4,3%.**

Per gruppo:
- contro BTC: 28 segnali, WR 32%, somma +56% (troppo pochi per concludere);
- con BTC: 271 segnali, WR 28%;
- storia inferiore a 52 settimane: 40 segnali, WR 38%, somma −4%.

Gli short sono la parte che funziona: 781 segnali, WR 48%, somma +572%. Sono positivi nel 2021–22 e nel 2025–26, negativi nel
2023–24.

**Long dello scanner al 24/11** (simulazione W3.2 per moneta senza liste, prodotta da `extra.py`; esito per quota):

| Moneta | In posizione dal | Esito per quota |
|---|---|---|
| JST | 13/07 (in posizione W3.2 da luglio: nello scanner del 22/11 non è un ingresso nuovo) | +50% |
| NIGHT | 05/10 | +4,5% |
| SENT | 23/11 | +0,1% |
| PIEVERSE | 23/11 | −11% |
| BEAMX | 09/11 | −10% |

Questo è il campione che l'utente vede, non quello storico (lezione 79).

## 4. Variante migliore: V3 (solo short)
- **Operazioni**: 96 su 72 monete. Per anno: 2021 6 (WR 100%), 2022 20 (65%), 2023 21 (38%), 2024 22 (32%), 2025 13 (54%),
  2026 14 (64%).
- **Uscite**: EMA 47, distribuzione 33, trailing 11, aperte 5. Migliore +29,9%, peggiore −21,0% per quota.
- **Semestri dal 2021** (%): 0,0 · +9,1 · +14,3 · +8,1 · −6,3 · −3,2 · −5,1 · −5,2 · +7,9 · +8,5 · +7,3 · +0,6. Quattro semestri
  negativi di fila nel 2023–24, quando le alt salivano. Il vantaggio sta nelle fasi ribassiste delle alt.
- **Posizioni aperte al 24/11**: 5, correlate (3 entrate il 12/10, una il 28/09, una il 17/08). Valgono +1.442 $ non realizzati
  su +3.905 $.
- **Robustezza**: senza il 10% migliore 12.017 $; senza i 3 migliori 13.134 $; senza il 2021 (dal 2022) 13.064 $.
- **OOS**: +9% in circa 3 anni con WR 41%.

Il p del placebo (0,006) non passa Holm su 10 ipotesi (0,060). Elenco completo in §10 e in `data/trades_V3.csv` (`pnl` =
esito per quota, `m` = margine).

## 5. Cosa significa per l'utente (1% del capitale, Bitget/OKX, leva 2x/5x)
- **Non operare queste monete con capitale reale: nessuna variante passa.** Il budget dell'1% avrebbe reso +0,98% del capitale
  totale in quasi sei anni con W3.2 com'è (DD del budget −55%) e −0,46% con i soli long.
- **Leva**:
  - 5x non è mai coerente con lo stop di W3.2: il 100% degli ingressi è oltre la liquidazione, e 5x fisso azzera il budget;
  - 2x solo se lo stop è entro il 44% (circa metà dei long, quasi nessuno short);
  - se mai si opera: margine isolato pari alla quota, esposizione = size di W3.2 (≤ 1x).
- **Posizioni**: con 5 quote il DD resta oltre il 40% per tutte le varianti tranne V3 e V8.
- **Sulla carta**: V3, cioè gli short di W3.2 sulle monete con rank 101–200 di inizio anno, con size di W3.2, al massimo 5
  posizioni e le uscite di W3.2. Le soglie per riconsiderarla sono una proposta nuova, in `PREREG-AVANTI-V3.md`: si committa
  prima del 30/11 solo se l'utente vuole il registro.
- **Long sulle emergenti**: da non seguire, nemmeno "contro BTC".

## 6. Proposte per lo scanner (solo proposte, nulla è stato toccato)
1. Per ogni posizione mostrare la distanza dello stop in % e la leva massima compatibile 1/(d+0,05), con l'avviso "oltre la
   liquidazione a 2x/5x".
2. Accanto ai long sulle monete fuori dalla top 100: "storico: WR 29%, mediana −6% per operazione".
3. Distinguere i veri ingressi dalle posizioni già aperte (es. JST in posizione da luglio). Non evidenziare i "nuovi long" sulle
   emergenti.
4. Registro sulla carta solo per gli short (V3), come per TRX, se l'utente lo vuole.
5. Calcolare il verso di BTC alla data del segnale, non nella settimana corrente: NIGHT e BEAMX erano "con BTC" al segnale.

## 7. Limiti
- Classifiche storiche solo fino al 200° posto. La vista "di oggi" 101–500 fa 9.698 $ con OOS −27%, ed è ottimistica perché
  contiene solo le sopravvissute.
- Liste annuali; l'istantanea per il 2026 è del 16/11/2025.
- Delisting: la posizione si chiude all'ultimo prezzo scambiato.
- Cambi di denominazione: corretti solo quelli riconoscibili in automatico (BNX, STRAX, BTCST).
- Operabilità storica su Bitget/OKX ignota.
- Funding di novembre 2026 mancante sui perp senza OKX.
- Liquidazione semplificata: mantenimento fisso, nessuna commissione di liquidazione, candele giornaliere.
- Un segnale scartato per quote piene non cambia la simulazione della moneta.
- Placebo senza stop.
- W3.2 è stata sviluppata su BTC.

## 8. Revisione critica (27/11): confermato
La revisione di un agente separato conferma nella sostanza: nessun verdetto cambia. Correzioni applicate:
1. **BNX**: il cambio di denominazione 1:100 del 22/02/2023 non era corretto. Creava uno short artefatto (13/03/2023, d =
   12.767%) che occupava una quota fino al 29/04/2024. Ora `build.py` segnala tutti i salti giornalieri > 3x
   (`data/salti.csv`) e taglia le monete con apertura = chiusura precedente diviso o moltiplicato per 10, 100 o 1000: BNX,
   STRAX, BTCST.
2. **DEXE** (21/07/2026) verificato: è un crollo reale e resta. Lo short con d = 1.053% è il comportamento di W3.2 dopo un
   crollo. Dopo il rilancio: V1 18.733 → 19.783 $; V3 13.883 → 13.905 $.
3. **`out_extra.txt`** ora è interamente prodotto da `extra.py`, compreso il blocco dei long dello scanner. Annotato che JST è
   in posizione da luglio.
4. **V3** descritta per quello che è: guadagno dell'ultimo anno soprattutto non realizzato, semestri negativi nel 2023–24, OOS
   debole, robustezza senza i 3 migliori e senza il 2021.
5. **Altre correzioni**: specificato che il p del placebo è leggermente ottimistico; i 470 long sono i candidati di V1; la
   soglia per V3 spostata nella proposta `PREREG-AVANTI-V3.md`; `DATI.md` riallineato (1.191 ingressi dopo il funding, 1.190
   dopo il taglio dei cambi di denominazione); le 6 monete con abbinamento errato contano come "senza dati".

## 9. Lezione 131 proposta
**Lezione 131**: monete emergenti (rank 101–200 alla classifica di inizio anno, punto nel tempo; budget 1%, 5 posizioni, 0,2%
per lato; research/emergenti, PREREG 1110e53): 0 varianti operabili su 10.
- W3.2 com'è: 19,8k $ su 10k di budget (DD −55%, OOS −19%).
- **Solo long: 5,4k $ (DD −81%, WR 28%; ultimi 12 mesi WR 18%)**: "i long sono in netto positivo" è falso.
- Solo short: 13,9k $, DD −21%, WR 52%, ma il placebo non passa Holm (0,060). Inoltre:
  - il vantaggio sta nelle fasi ribassiste delle alt (quattro semestri negativi nel 2023–24, OOS +9% in tre anni con WR 41%);
  - il guadagno dell'ultimo anno è soprattutto non realizzato (5 posizioni aperte e correlate valgono +1,4k $ dei +3,9k $);
  - da tenere solo sulla carta.
- Lo stop di W3.2 sulle emergenti è al 50% (long) e all'83% (short) dall'ingresso. A 5x è sempre oltre la liquidazione (5x
  fisso azzera il budget); a 2x lo è per metà dei long. La leva adattiva evita le liquidazioni ma porta il DD a −97%. Sulle
  monete piccole si usa la size di W3.2 (≤ 1x) oppure nulla.
- Filtri di qualità, cancello BTC (con o contro), trailing 2,0 e uscita EMA 10 non migliorano.
- Nei dati delle monete piccole vanno controllati in automatico i cambi di denominazione (salti > 3x con apertura = chiusura
  precedente / 10ⁿ): un solo cambio non corretto (BNX 1:100) bloccava una quota per 13 mesi.

## 10. V3 · elenco delle operazioni
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
| 35 | QTUM | 2023-03-13 | 2023-03-20 | ema | 58% | -13.8% | 2.455 | contro |
| 36 | IOST | 2023-03-13 | 2023-03-20 | ema | 59% | -6.5% | 2.455 | contro |
| 37 | SKL | 2023-03-13 | 2023-03-20 | ema | 86% | -3.5% | 2.455 | contro |
| 38 | KAVA | 2023-04-03 | 2023-05-15 | ema | 75% | -7.1% | 2.364 | contro |
| 39 | GALA | 2023-04-10 | 2023-04-17 | ema | 81% | -3.2% | 2.358 | contro |
| 40 | GMT | 2023-04-17 | 2023-11-06 | ema | 83% | +15.3% | 2.323 | contro |
| 41 | OMG | 2023-04-17 | 2023-11-06 | ema | 72% | +20.5% | 2.323 | contro |
| 42 | GALA | 2023-04-24 | 2023-10-30 | ema | 77% | +16.0% | 2.426 | contro |
| 43 | ANKR | 2023-05-15 | 2023-10-30 | ema | 71% | +4.9% | 2.383 | contro |
| 44 | CKB | 2023-06-26 | 2023-10-30 | ema | 74% | +0.7% | 2.009 | contro |
| 45 | OP | 2023-10-30 | 2023-11-06 | ema | 51% | -4.5% | 2.575 | contro |
| 46 | MAGIC | 2023-11-20 | 2023-11-27 | ema | 67% | -13.0% | 2.540 | contro |
| 47 | ENS | 2023-12-18 | 2023-12-25 | ema | 41% | -5.3% | 2.474 | contro |
| 48 | CVX | 2024-01-01 | 2024-02-12 | dist | 46% | +3.2% | 2.447 | contro |
| 49 | ZEC | 2024-01-01 | 2024-02-22 | trail | 40% | -5.4% | 2.447 | contro |
| 50 | DASH | 2024-01-01 | 2024-02-26 | ema | 38% | +2.6% | 2.447 | contro |
| 51 | ENJ | 2024-01-08 | 2024-02-19 | ema | 54% | -6.6% | 2.579 | flat |
| 52 | SXP | 2024-01-08 | 2024-02-19 | ema | 49% | +0.1% | 2.315 | flat |
| 53 | GMX | 2024-04-08 | 2024-06-06 | trail | 58% | -4.5% | 2.415 | flat |
| 54 | ZEC | 2024-04-15 | 2024-05-27 | ema | 63% | -8.0% | 2.488 | flat |
| 55 | CVX | 2024-04-15 | 2024-06-17 | ema | 78% | -5.1% | 2.488 | flat |
| 56 | XEM | 2024-06-24 | 2024-07-22 | dist | 145% | -3.4% | 2.328 | flat |
| 57 | GMT | 2024-07-15 | 2024-09-30 | ema | 90% | -2.7% | 2.328 | flat |
| 58 | ZIL | 2024-07-22 | 2024-11-11 | ema | 61% | +5.2% | 2.301 | flat |
| 59 | LRC | 2024-07-29 | 2024-11-17 | trail | 84% | -7.4% | 2.287 | flat |
| 60 | ENJ | 2024-07-29 | 2024-11-23 | trail | 90% | -6.6% | 2.321 | flat |
| 61 | MAGIC | 2024-07-29 | 2024-11-25 | ema | 99% | -3.8% | 2.321 | flat |
| 62 | MEME | 2024-09-30 | 2024-11-25 | ema | 155% | -2.3% | 2.266 | contro |
| 63 | WLD | 2024-11-11 | 2024-11-25 | ema | 96% | -5.2% | 2.367 | contro |
| 64 | ENS | 2024-11-18 | 2024-11-25 | ema | 69% | -5.3% | 2.171 | contro |
| 65 | MEME | 2024-12-16 | 2025-04-21 | dist | 106% | +19.6% | 2.183 | contro |
| 66 | SFP | 2024-12-16 | 2025-01-06 | ema | 40% | -2.0% | 2.183 | contro |
| 67 | TRB | 2024-12-23 | 2025-05-27 | trail | 100% | +4.9% | 2.218 | contro |
| 68 | WLD | 2024-12-23 | 2025-05-26 | ema | 106% | +8.8% | 2.218 | contro |
| 69 | CELO | 2024-12-23 | 2025-01-06 | ema | 72% | -3.8% | 2.114 | contro |
| 70 | AXL | 2025-01-06 | 2025-02-24 | dist | 92% | +8.8% | 2.019 | contro |
| 71 | SATS | 2025-01-06 | 2026-04-17 | trail | 119% | +18.9% | 2.154 | contro |
| 72 | KAVA | 2025-02-24 | 2025-03-17 | ema | 63% | -3.8% | 2.197 | contro |
| 73 | COMP | 2025-03-17 | 2025-04-01 | trail | 93% | -21.0% | 2.113 | flat |
| 74 | CKB | 2025-04-07 | 2025-07-20 | trail | 161% | -12.4% | 1.670 | flat |
| 75 | GLM | 2025-04-21 | 2025-07-14 | dist | 78% | -0.0% | 2.368 | flat |
| 76 | NOT | 2025-05-26 | 2025-11-24 | dist | 180% | +11.2% | 2.316 | contro |
| 77 | ARKM | 2025-06-02 | 2025-09-15 | ema | 120% | -2.4% | 2.323 | contro |
| 78 | JTO | 2025-07-14 | 2026-02-02 | dist | 72% | +29.9% | 2.315 | contro |
| 79 | ZRO | 2025-07-21 | 2025-09-29 | ema | 85% | -0.4% | 1.861 | contro |
| 80 | PNUT | 2025-09-15 | 2026-08-24 | ema | 184% | +10.8% | 2.267 | contro |
| 81 | ARKM | 2025-09-29 | 2026-01-26 | dist | 75% | +23.0% | 1.853 | contro |
| 82 | ETHFI | 2025-11-24 | 2026-08-17 | ema | 145% | +4.9% | 2.552 | flat |
| 83 | ZK | 2026-01-26 | 2026-02-09 | dist | 136% | +1.2% | 2.302 | con |
| 84 | GALA | 2026-02-02 | 2026-05-04 | dist | 134% | +6.3% | 2.597 | con |
| 85 | ZEN | 2026-02-09 | 2026-05-04 | ema | 145% | -3.1% | 2.641 | con |
| 86 | ATH | 2026-04-20 | 2026-09-28 | ema | 160% | -1.4% | 2.657 | con |
| 87 | SNX | 2026-05-04 | 2026-09-28 | ema | 91% | +4.3% | 2.639 | flat |
| 88 | SUPER | 2026-05-04 | 2026-08-31 | dist | 120% | +2.0% | 2.639 | flat |
| 89 | DEXE | 2026-08-17 | aperta | open | 1053% | +0.8% | 2.721 | con |
| 90 | XEC | 2026-08-31 | 2026-09-07 | ema | 56% | -4.7% | 2.710 | contro |
| 91 | APE | 2026-08-31 | 2026-09-28 | ema | 63% | -9.6% | 2.494 | contro |
| 92 | SAND | 2026-09-07 | 2026-10-02 | trail | 78% | -18.1% | 2.584 | contro |
| 93 | B | 2026-09-28 | aperta | open | 118% | +11.5% | 2.563 | contro |
| 94 | FARTCOIN | 2026-10-12 | aperta | open | 77% | +17.5% | 2.515 | contro |
| 95 | XPL | 2026-10-12 | aperta | open | 96% | +13.1% | 2.515 | contro |
| 96 | CHZ | 2026-10-12 | aperta | open | 68% | +16.5% | 2.148 | contro |
