# Famiglia A · Trend e rotture 4h (BTC, ETH, SOL) — esito: NESSUNA VARIANTE PASSA

Preregistrazione: `PREREG.md` (8 varianti, scritta prima dei risultati). Codice: `strategies_a.py` (segnali), `run_a.py` (tutto).
Uscite e sizing di riferimento del PIANO: stop 1,5 ATR, TP1 +1,5R (metà), pareggio, TP2 +3R, uscita a 12 barre; rischio 1%,
leva 2x, capitale 10.000 $, costi e funding reali. Scelta solo sul 2021–23, giudizio sul 2024→07/11/2026 (capitale fresco).
Placebo 500 giri, vicini ±20% one-at-a-time. Dati grezzi: `results_a.csv`, `neigh_A*.csv`.

## Tabella (FC = fuori campione 2024→oggi; IC = in campione 2021–23)
| variante | $ finali FC | rend. FC | DD FC | trade/mese | WR | PF | exp R | MAR | IC: rend. / PF / R | 2021→oggi $ (DD) | placebo pct R | vicini mediana R | criteri 1–7 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 ICHI (TK cross, lez. 78) | 12.044 | +20,4% | −23,2% | 10,7 | 45% | 1,10 | +0,064 | 0,29 | +9,4% / 1,05 / +0,027 | 13.171 (−27%) | **99,8** | +0,036 | 0011111 |
| A2 DON 55 + volume | 8.266 | −17,3% | −33,3% | 11,8 | 44% | 0,91 | −0,041 | −0,19 | +6,2% / 1,04 / +0,030 | 8.780 (−33%) | 85 | −0,029 | 0001000 |
| A3 DON + regime giorn. | 7.785 | −22,1% | −34,6% | 7,7 | 41% | 0,83 | −0,091 | −0,24 | +12,9% / 1,10 / +0,060 | 8.788 (−35%) | 49 | −0,074 | 0001000 |
| A4 SQZ (compressione BB) | 7.864 | −21,4% | −40,8% | 10,6 | 41% | 0,90 | −0,058 | −0,20 | −3,2% / 0,98 / +0,002 | 7.611 (−41%) | 81 | −0,061 | 0001000 |
| **A5 SQZ + regime (scelta IC)** | 8.171 | −18,3% | −31,3% | 5,2 | 37% | 0,82 | −0,117 | −0,22 | +29,2% / 1,30 / +0,155 | 10.553 (−31%) | 44 | −0,123 | 0001000 |
| A6 DON + regime + ADX≥20 | 7.637 | −23,6% | −33,5% | 6,7 | 40% | 0,78 | −0,116 | −0,27 | +8,6% / 1,08 / +0,055 | 8.291 (−34%) | 33 | −0,108 | 0001000 |
| A7 RETEST dopo rottura | 9.117 | −8,8% | −14,0% | 5,9 | 43% | 0,91 | −0,039 | −0,23 | −25,8% / 0,76 / −0,123 | 6.767 (−35%) | 75 | −0,045 | 0101000 |
| A8 ICHI + regime giorn. | 9.427 | −5,7% | −17,3% | 6,7 | 43% | 0,95 | −0,019 | −0,12 | +14,7% / 1,11 / +0,059 | 10.812 (−18%) | 86 | −0,015 | 0101000 |
| Buy & hold 1/3 ciascuno, 1x | — | — | — | — | — | — | — | — | — | 206.429 (−95%) | | | |
| Buy & hold BTC, 1x | — | — | — | — | — | — | — | — | — | 25.881 (−77%) | | | |
| W2 + MACD (Memoria) | — | — | — | — | — | — | — | — | — | ~118.900 (−22,7%), 14 trade | | | |

Criteri (1 = superato): 1 PF ≥ 1,3 e ≥ +0,15R · 2 DD ≤ 20% · 3 positivo in IC e FC e su ≥ 2/3 asset · 4 2–12 trade/mese ·
5 placebo > 90° pct · 6 mediana vicini > 0 · 7 senza il trade migliore > 0.

## Verdetto
- **La variante scelta in campione (A5, compressione + regime giornaliero: +0,155R, PF 1,30 nel 2021–23) crolla fuori campione**
  (−0,117R, PF 0,82, −18%, 0/3 asset positivi, sotto la mediana del placebo). Classico sovradattamento: 2026 −24% (WR 19%).
- Tutte le rotture Donchian/compressione, con o senza regime giornaliero, ADX o ritest, sono negative fuori campione.
- **Solo A1 (Ichimoku TK cross nel verso della nube) mostra un vantaggio reale ma piccolo**: placebo 99,8° pct, vicini positivi
  (71% con PF > 1), positivo in entrambe le metà; però +0,064R e PF 1,10 (soglia +0,15R / 1,3) e DD −23%. Non era nemmeno
  ammessa in campione (PF 1,05). Il risultato viene quasi tutto da SOL (+5.895 $; BTC −2.984 $), con il 2023 e il 2026 negativi.
  Conferma la lezione 78 (solo il momentum sopravvive, ma il bordo è sottile); con le uscite di riferimento (12 barre) è più
  debole del +0,14R della lezione 78 (stop 2 ATR, target 3R, 48 barre).
- Il filtro di regime giornaliero aiuta in campione e peggiora fuori campione su tutte le famiglie di rottura (A3, A5, A6, A8).
- Nessuna variante va in D come "approvata". Unico candidato per uno studio delle uscite, dichiarato come esplorativo: A1
  (`trades_A1.csv`); i trade della scelta ufficiale sono in `trades_A5.csv`.

## Lezione proposta per RESEARCH.md
**Lezione (intraday2 A)**: su 4h le rotture di range (Donchian 55 + volume, compressione BB, ritest, ADX, regime giornaliero EMA50)
non reggono i costi fuori campione (−0,02/−0,12R); la migliore in campione (compressione + regime, +0,155R) è la peggiore fuori
(−0,117R). Solo il TK cross Ichimoku nel verso della nube batte il placebo (99,8° pct, vicini positivi) ma vale +0,06R, PF 1,10,
DD −23% con uscite a 12 barre, e quasi tutto da SOL: momentum reale ma troppo sottile per un conto da 10.000 $ a mano.
