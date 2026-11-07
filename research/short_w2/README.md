# Short W2 · strategia short dedicata su BTC (05–07/11/2026) · ESITO: NON PROMUOVERE — solo TEST/carta

Richiesta: "implementa una strategia SHORT (usa tutti i dati) e analizza se è performante". Per decisione dell'utente la
strategia resta **solo in test**, fuori dal tool. Regole preregistrate in `PREREG.md` (scritte prima dei risultati).

## Dati usati (date di inizio)
spot Binance 1d dal 2019-09-01 · perp/funding dal 2020-01-01 · flusso perp pf14z dal 2020-04-12 · OI e long/short (metrics)
dal 2021-12-01 · F&G dal 2018 · taker_1h e spot_1h dal 2022 (non necessari a livello settimanale) · liquidazioni reali solo
dal 30/10/2026 (inutilizzabili). Storia lunga per il 2018–20: Bitstamp 1d 2014→2017-08 + Binance spot 1d 2017-08→2019-08
(`data/`), flusso = CVD spot z (proxy), funding 0.

## Regole (stessi parametri: SMA40w, EMA20/21w, ATR14w, MACD 8/21/5, stop e trailing 2,5 ATRw, 0,1%/lato, funding reale)
S0 short W2 attuale · S1 regime (close < SMA40, EMA20 in calo, close < EMA21) · S2 S1 + MACD < segnale e < 0 · S3 S2 +
pf14z < 0 + longs affollati (funding_z/ls_z > 0) · S4 ritest fallito di EMA21/SMA40 · S5 top di distribuzione (incrocio MACD
rosso sopra lo zero, close > 1,25·SMA40, funding_z > 1, stop 1,5 ATRw) · S6 S2 con ingresso giornaliero · S7 S2 con uscita su SMA40.
Fuori preregistrazione (diagnostica, `diag.py`): **D1** = regime W2 (SMA40 in calo) + close < EMA21, **senza** filtro pf14z.

## Tabella comparativa dal 01/01/2021 (10.000 $, short 1x, DD giornaliero mark-to-market) — `table1x.txt`
| Strategia | finale $ | rend. | max DD | trade | WR | MAR (CAGR/DD) |
|---|---|---|---|---|---|---|
| **W2 così com'è** (long spot + short R25) | 120.444 | +1.104% | −22,7% | 14 | 93% | 2,34 |
| long W2 + S1 (miglior regola "di regime") | 93.203 | +832% | −37,8% | 17 | 71% | 1,23 |
| S1 da solo | 10.062 | +0,6% | −40,5% | 8 | 50% | 0,00 |
| long W2 + S5 (top di distribuzione) | 110.868 | +1.009% | −24,0% | 12 | 83% | 2,12 |
| S5 da solo | 13.295 | +33% | −14,4% | 1 | 100% | 0,35 |
| long W2 + D1 (esplorativa) | 152.033 | +1.420% | −22,7% | 14 | 93% | 2,62 |
| D1 da solo | 16.347 | +63,5% | −20,9% | 4 | 100% | 0,42 |
Altre a 1x combinate: S0 129,7k (DD −24,9), S2 63,6k, S3 75,2k, S4 99,4k, S6 53,7k, S7 79,1k (tutte sotto W2; `results.txt`).
Con size R25 il quadro non cambia (S1+W2L 96,6k DD −34,8; D1+W2L 131,1k DD −22,7).
Short W2 attuali (baseline da battere): 4 trade 2022-01 +1,0%, 2022-08 +8,3%, 2025-12 +11,9%, 2026-05 +5,7% → +29,5% composto.

## Split (10.000 $ da capo; rend. / DD / MAR)
| | 2018–20 (proxy) | 2021–23 | 2024–oggi |
|---|---|---|---|
| W2 così com'è | +118% / −48,1 / 0,62 | +406% / −22,7 / 3,17 | +138% / −21,6 / 1,65 |
| long W2 + S1 | +68% / −68,7 / 0,27 | +445% / −31,6 / 2,41 | +72% / −37,8 / 0,55 |
| long W2 + S5 | +127% / −47,6 / 0,66 | +451% / −24,0 / 3,20 | +102% / −21,6 / 1,29 |
| long W2 + D1 | +65% / −54,9 / 0,33 | +529% / −22,7 / 3,74 | +142% / −21,9 / 1,67 |

## Robustezza
- **Episodi ribassisti indipendenti** (regime base ≥ 8 settimane): 2018-05→2019-03 (−72%), 2020-03→04 (−47%, crollo covid),
  2021-12→2023-01 (−75%), 2025-11→2026-08 (−52%); più 2014–15 fuori dal periodo di test. Dal 2021 sono **2**, dal 2018 **4**:
  ogni conclusione sugli short poggia su 2–4 episodi.
- Senza il filtro "SMA40 in calo" (S1–S3, S6, S7) gli short entrano nelle correzioni dei bull (2021-06, 2021-09, 2024-09,
  2025-04: −6/−16% ciascuno). Il filtro MACD (S2) peggiora: entra tardi e viene stoppato sui rimbalzi dei bear.
- Placebo (500 prove, ingressi casuali nel regime): solo S0 è vicino alla soglia (p 0,09); S1 p 0,28, S2 0,65, S3 0,60, S4 0,26,
  S6 0,71, S7 0,40 → le regole nuove non battono ingressi casuali nello stesso regime.
- Vicini (SMA 35/45, EMA 18/24, trailing 2/3, MACD 6/18/4 e 10/26/6): nessuna regola nuova supera S0 in nessun vicino.
- Senza il trade migliore: tutte le nuove standalone diventano negative (S1 −34%, S2 −47%); S5 è un solo trade (2021-04, +33%),
  0 segnali nel 2018–20 e nel 2024–oggi.
- D1: guadagno da UN solo trade (rientro 16/05/2022 invece del 15/08/2022: +18% vs +8%); vicini 2021–oggi MAR 1,49–2,71 ma
  2018–20 MAR 0,16–1,02 (W2 0,62), e lo short di marzo 2020 dopo la capitolazione perde −18% (lezione 56). Post-hoc.

## Verdetto
**Respingere** S1–S7: nessuna batte gli short attuali di W2, da sole non guadagnano (WR 29–50%, placebo non superato) e
combinate peggiorano DD e MAR. **D1** (= W2 senza il filtro di flusso sugli short) solo **su carta nel Laboratorio**: migliore dal
2021 in entrambi i sottoperiodi ma deciso dopo i risultati, dipendente da un trade e peggiore nel 2018–20. Gli short di W2 restano
invariati (S0, R25). Lezione: su BTC lo short settimanale paga solo nei bear "maturi" (SMA40 in calo); il vantaggio di W2 resta
evitare i bear, non shortarli.

File: `PREREG.md`, `short_lab.py` (motore, replica esatta di radar/weekly.simulate), `run.py` → `results.txt/json`,
`table1x.py` → `table1x.txt`, `diag.py` → `diag.txt`, `d1_neigh.py` → `d1_neigh.txt`, `trades_S1_1x_2021.csv`, `trades_D1_1x_2021.csv`.
Uso: `python3 research/short_w2/run.py` (≈ 3 min).
