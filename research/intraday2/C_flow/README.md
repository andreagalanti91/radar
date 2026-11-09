# Famiglia C · Flusso e derivati (4h, BTC/ETH/SOL) — esito: NESSUNA VARIANTE PASSA

Preregistrazione: `PREREG.md` (8 varianti, soglie e scelta scritte prima; un emendamento su C5, che dava 0 trade per
costruzione). Codice: `flow.py` (`is`, `oos`, `robust <ID>`, `placebo_all`). Uscite e sizing di riferimento PIANO: stop 1,5 ATR,
TP1 +1,5R metà, pareggio, TP2 +3R, 12 barre; rischio 1% a trade, nozionale ≤ 2x per posizione, esposizione ≤ 5x; costi e funding reali.
Campione: C0, C1, C2, C5 dal 2021-01; C3, C4, C6, C7 (OI o L/S) dal **2021-12** (in campione solo 25 mesi).

| id | idea | 10k → (tutto) | rend. | max DD | trade/mese | WR | PF | R/trade | MAR | R IS → OOS | PF IS → OOS | placebo pct OOS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C0 | momentum 20 barre (controllo) | 5.341 $ | −46,6% | −48,3% | 20,0 | 43% | 0,92 | −0,036 | −0,21 | −0,027 → −0,045 | 0,93 → 0,91 | 85 |
| C1 | funding estremo + prezzo che cede | 9.918 $ | −0,8% | −16,8% | 4,1 | 49% | 0,99 | +0,005 | −0,01 | 0,000 → +0,012 | 0,98 → 1,01 | 85 |
| C2 | momentum con funding non affollato | 5.991 $ | −40,1% | −42,8% | 16,8 | 43% | 0,92 | −0,036 | −0,20 | −0,024 → −0,049 | 0,93 → 0,90 | 79 |
| C3 | rottura + OI in espansione | 11.338 $ | +13,4% | −22,0% | 8,2 | 45% | 1,05 | +0,037 | 0,12 | +0,016 → +0,051 | 1,01 → 1,07 | 99 |
| C4 | flush di OI dopo grande movimento | 9.271 $ | −7,3% | −10,9% | 0,5 | 38% | 0,57 | −0,236 | −0,14 | −0,213 → −0,262 | 0,57 → 0,56 | 17 |
| C5 | divergenza CVD (assorbimento) | 9.040 $ | −9,6% | −14,4% | 1,2 | 40% | 0,78 | −0,124 | −0,12 | −0,011 → −0,305 | 0,97 → 0,46 | 13 |
| C6 | L/S retail affollato + conferma prezzo | 10.321 $ | +3,2% | −24,2% | 6,6 | 45% | 1,02 | +0,017 | 0,03 | +0,079 → −0,017 | 1,14 → 0,96 | 82 |
| C7 | punteggio di flusso su momentum | 7.103 $ | −29,0% | −34,5% | 13,1 | 43% | 0,91 | −0,036 | −0,19 | −0,058 → −0,022 | 0,87 → 0,95 | 92 |

Confronti dal 2021-01: buy & hold a pesi uguali 1x 10k → 181.630 $ (DD −95%, quasi tutto SOL); dal 2024: 11.604 $ (DD −62%).
W2 + MACD (solo BTC, 1x): 10k → ~118.900 $, DD −22,7%, 14 trade.

## Criteri (fuori campione 2024→oggi)
- **Scelta in campione**: nessuna candidata (soglia PF ≥ 1,2 e +0,10R). La più vicina, C6 (+0,079R), fuori campione va a −0,017R,
  PF 0,96, DD −24,2%, 1/3 asset positivi, 2026 −13,4%: fallisce 1, 2, 3, 5 (82° pct), 6 (mediana vicini −2,5%), 7 (−798 $).
- **C3** (la migliore fuori campione, non scelta): PF 1,07 e +0,051R (criterio 1 no), DD −22,0% (2 no), 2023 −2,4% e 2026 −12,5%,
  vicini z 0,8/1,2 → +1,8%/−1,2% (picco isolato), senza il trade migliore +965 $ (ok), placebo 98,6° pct (ok).
- Nessuna variante raggiunge PF 1,3 né +0,15R in nessuna delle due metà.

## Cosa si impara
- Ingressi casuali con queste uscite perdono −10/−47% fuori campione (mediana del placebo): i costi su 4h sono un muro. Battere il
  placebo (C3, C7) non basta per essere redditizi.
- L'**OI in espansione** è l'unico filtro di flusso che migliora il momentum in entrambe le metà (C0 → C3: −0,027 → +0,016R in
  campione, −0,045 → +0,051R fuori), ma il guadagno (~0,05–0,09R) non porta a PF 1,3 ed è sensibile alla soglia.
- Funding come filtro (C2) non serve; funding e L/S contrarian (C1, C6) sono a zero; flush di OI e divergenze CVD (C4, C5) negativi:
  confermano le lezioni 72, 78 e 81 (inversioni intraday e "capitolazioni" senza vantaggio).

## File
`PREREG.md`, `flow.py`, `results.csv` (IS/OOS/ALL di tutte), `placebo.csv`, `rob_C3.txt`, `rob_C6.txt` (placebo, vicini, anni,
asset, lati), `trades_C3.csv` (migliore in assoluto), `trades_C6.csv` (scelta in campione).

## Lezione proposta per RESEARCH.md
**Lezione 8x**: nell'intraday 4h su BTC/ETH/SOL i dati di flusso e derivati (funding, OI, delta taker, L/S retail) non creano un
vantaggio da soli: 8 varianti preregistrate, nessuna con PF ≥ 1,2 in campione; contrarian su funding/L/S a zero, flush di OI e
divergenze CVD negativi. L'unico contributo stabile è l'OI in espansione come filtro delle rotture (+0,05–0,09R su entrambe le
metà), troppo piccolo contro i costi (PF 1,07). Il flusso resta un filtro di scelta dei trade (lezione 57), non un segnale.
