# Famiglia D · Uscite ("la costante") e leva su A1 Ichimoku 4h — FASE ESPLORATIVA

**Esplorativa**: nessun ingresso di A–C ha passato i criteri. Le uscite sono studiate sull'unico ingresso con un vantaggio sul
placebo, A1 (TK cross Ichimoku 4h nel verso della nube, BTC/ETH/SOL, long e short). A1 è stato scelto dopo aver visto il fuori
campione di A e deriva dalla lezione 78, che usava lo stesso periodo 2024–26: il fuori campione qui **non è vergine**.
Preregistrazione: `PREREG.md` (8 politiche + griglia della costante + griglia leva). Codice: `run_d.py is|oos|placebo|neigh|lev`.
Scelta solo sul 2021–23, giudizio 2024→07/11/2026 una volta. Costi, slippage, funding e liquidazione reali; 10.000 $.

## Politiche (sizing di riferimento: rischio 1% a trade, nozionale ≤ 2x per asset; "tutto" = 2021→oggi)
| politica | 10k → $ tutto | rend. | max DD | trade/mese | WR | PF | R/trade | MAR | IC R / PF | FC R / PF / DD | placebo pct FC | mediana placebo R | mediana vicini R FC | criteri 1–7 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 rif. 1,5ATR, ½ a 1,5R, BE, ½ a 3R, 12 barre | 13.171 | +31,7% | −27,1% | 10,8 | 46% | 1,07 | +0,045 | 0,18 | +0,027 / 1,05 | +0,064 / 1,10 / −23,2% | 99,8 | −0,104 | +0,037 | 0011111 |
| E2 lez. 78: 2ATR, tutto a 3R, 48 barre | 23.127 | +131,3% | −23,7% | 8,7 | 38% | 1,21 | +0,165 | 0,65 | +0,143 / 1,17 | +0,191 / 1,24 / −18,9% | 99,6 | −0,029 | +0,170 | 0111111 |
| E3 costante utente +5% / +10%, BE | 16.171 | +61,7% | −19,1% | 9,2 | 53% | 1,15 | +0,093 | 0,45 | +0,067 / 1,11 | +0,125 / 1,19 / −17,0% | 99,0 | −0,054 | +0,112 | 0111111 |
| **E4 ½ a 2R, BE, trailing 3ATR (scelta IC)** | **29.009** | **+190,1%** | **−17,6%** | 8,1 | 40% | 1,31 | +0,224 | 1,13 | +0,202 / 1,27 | **+0,249 / 1,33 / −15,2%** | 99,4 | −0,045 | +0,211 | **1111111** |
| E5 ⅓ a 1R, ⅓ a 2R, ⅓ a 4R, BE | 12.222 | +22,2% | −27,3% | 9,1 | 55% | 1,07 | +0,043 | 0,13 | +0,017 / 1,02 | +0,072 / 1,11 / −21,0% | 99,8 | −0,104 | +0,056 | 0011111 |
| E6 tutto a 2R, 72 barre | 17.472 | +74,7% | −23,9% | 8,6 | 40% | 1,15 | +0,112 | 0,42 | +0,092 / 1,11 | +0,134 / 1,18 / −18,4% | 98,6 | −0,040 | +0,117 | 0111111 |
| E7 solo chandelier 3ATR | 37.220 | +272,2% | −22,7% | 10,0 | 36% | 1,47 | +0,234 | 1,11 | +0,155 / 1,28 | +0,319 / 1,57 / −20,2% | 100,0 | −0,022 | +0,282 | 1011111 |
| E8 E4 + OI in espansione (dal 2021-12) | 9.309 | −6,9% | −16,2% | 2,6 | 32% | 0,93 | −0,027 | −0,09 | +0,124 / 1,14 | −0,144 / 0,80 / −16,2% | 24,6 | −0,025 | −0,132 | 0101000 |
| E3* costante scelta IC: **+8% / +20%**, BE | 29.674 | +196,7% | −20,2% | 8,2 | 46% | 1,35 | +0,230 | 1,01 | +0,177 / 1,28 | +0,294 / 1,39 / −14,5% | 100,0 | −0,035 | +0,253 | 1111111 |
| Buy & hold 1/3 ciascuno, 1x | 206.429 | | −95% | | | | | | | | | | | |
| Buy & hold BTC, 1x | 25.881 | | −77% | | | | | | | | | | | |
| W2 + MACD (Memoria, solo BTC, 1x) | ~122.700 | | −22,7% | 14 trade | 93% | | | | | | | | | |

Criteri (1 = superato): 1 PF ≥ 1,3 e ≥ +0,15R · 2 DD ≤ 20% · 3 positivo IC e FC, ≥ 2/3 asset · 4 2–12 trade/mese · 5 placebo
> 90° pct (500 giri, stesse uscite) · 6 mediana vicini > 0 · 7 senza il trade migliore > 0. E1 riproduce A1 della famiglia A.
Rendimenti annui E4: 2021 +22%, 2022 +22%, 2023 +9%, 2024 +19%, 2025 +36%, 2026 +11% (`yearly.csv`). FC per asset: BTC +3,4k,
ETH +3,8k, SOL +5,7k; long +0,27R, short +0,23R. I 5 trade migliori fanno il 62% del PnL fuori campione (code destre).

## Le uscite non creano un vantaggio
Con ingressi casuali (stesse uscite, stessi stop) **tutte** le politiche perdono: mediana −0,02/−0,11R, −11/−31% sul fuori
campione, 2–32% dei giri in utile (`placebo.csv`). Il vantaggio viene da A1; le uscite decidono quanto se ne incassa. Le uscite
che tagliano presto (TP vicini, tempo 12 barre, ⅓ a 1R) alzano il WR (53–56%) ma dimezzano il vantaggio; quelle che lasciano
correre il resto (trailing, target lontani) lo raddoppiano: è un trend-following, il guadagno sta nelle code.

## La "costante" (TP1/TP2 in % del prezzo, 50/50, pareggio dopo TP1, stop 2 ATR)
- Esempio dell'utente **+5% / +10%**: positivo ma sotto soglia (FC +0,125R, PF 1,19; 10k → 16.171 $, DD −19%).
- Griglia in campione (`const_grid_is.csv`): TP1 3% è negativo, 4–6% marginale, **8% / 20%** la migliore (IC +0,177R): fuori
  campione +0,294R, PF 1,39, DD −14,5%, 10k → 29.674 $. Attenzione: è sul **bordo** della griglia (target più lontani = più simile
  a un trailing) e una % fissa non scala con la volatilità (8% su BTC è ~2–3 volte più lontano in R che su SOL).
- Alternativa in R equivalente e più semplice: **metà a +2R, pareggio, resto con trailing 3 ATR** (E4).

## Leva (`leverage.csv`, E4, 2021→oggi)
| sizing | 10k → $ | max DD | liquidazioni |
|---|---|---|---|
| rischio 0,5%, leva max 2x / 3x / 5x | 17.658 / 17.658 / 17.450 | −9,1% | 0 / 0 / 3 |
| rischio 1%, leva max 2x / 3x / 5x | 29.417 / 29.417 / 28.728 | −17,6% | 0 / 0 / 3 |
| rischio 1,5%, leva max 2x / 3x / 5x | 46.438 / 46.390 / 44.770 | −25,5% | 0 / 0 / 3 |
| nozionale fisso 2x / 3x / 5x il capitale (⅓ per asset) | 63.057 / 79.640 / 17.407 | −66% / −82% / −96% | 0 / 0 / 3 |
Con sizing al rischio la leva **non cambia nulla** (nozionale reale ≤ 0,8x a 1%): serve solo a ridurre il margine. A 5x il
prezzo di liquidazione (−19,5%) sta prima di alcuni stop larghi di SOL 2021 (fino al 30%): 3 liquidazioni. Il rischio del conto
lo decide la % a trade: 1% → DD −18%, 1,5% → −26% (oltre il limite di 20%). La leva piena sul capitale porta DD −66/−96%.

## Verdetto
- **E4 (scelta in campione) supera tutti e 7 i criteri** fuori campione: PF 1,33, +0,249R, DD −15,2%, 3/3 asset, 8,3 trade/mese,
  placebo 99,4° pct, vicini mediana +0,21R, senza il trade migliore +6.554 $. Anche E3* (8%/20%) li supera; E7 li sfiora (DD −20,2%).
- Ma il risultato è **esplorativo e fragile**: ingresso scelto dopo aver visto il 2024–26 (A e lezione 78); PF in campione 1,27;
  5 vicini su 12 con PF < 1,3 (tk/kj ±20%: PF 1,21–1,22, DD fino a −23%); il 62% del PnL in 5 trade. Il filtro OI peggiora (E8).
- Contro W2 + MACD resta piccolo: 10k → ~29k in quasi 6 anni con DD −18% (W2 ~123k con DD −23%, poche decisioni); sopra il B&H
  di BTC a pari periodo ma con ~8 alert al mese da eseguire a mano. Al massimo: **su carta** (alert Telegram, rischio 1%, leva ≤ 3x,
  metà a +2R, pareggio, trailing 3 ATR) con revisione critica (radar-review) prima; niente capitale reale, niente nel tool ora.

## Lezione proposta per RESEARCH.md
**Lezione 82** (ciclo intraday 2, A–D, 4h BTC/ETH/SOL): 24 ingressi preregistrati (rotture, pullback, flusso/derivati) non
passano: solo il TK cross Ichimoku nel verso della nube batte il placebo, e con le uscite corte di riferimento vale +0,06R.
Le uscite non creano un vantaggio (su ingressi casuali tutte perdono) ma decidono quanto se ne prende: tagliare presto (TP vicini,
12 barre, ⅓ a 1R) alza il WR e dimezza il guadagno; incassare metà a +2R, pareggio e trailing 3 ATR sul resto porta A1 a +0,25R,
PF 1,33, DD −15% fuori campione (10k → 29k dal 2021 a rischio 1%) e supera i 7 criteri, ma è esplorativo (fuori campione già
visto). La "costante" in % dell'utente (5%/10%) è troppo corta (+0,13R); 8%/20% funziona ma non scala con la volatilità. Con il
sizing al rischio la leva 2–5x non cambia il DD (serve solo al margine; a 5x liquida gli stop larghi); la leva piena sul capitale
porta il DD a −66/−96%. Il rischio a trade (1%) decide il DD. Il filtro OI che aiutava le rotture peggiora A1. Prima di usarlo:
solo carta e revisione critica; resta molto sotto W2 in rendimento per fatica.
