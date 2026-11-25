# w32_asset2 · W3.2 su altri asset, ciclo 2 · BOZZA · NON SI TRASFERISCE (un solo candidato: TRX con il cancello di BTC)

PREREG `PREREG.md`, commit **f40f7a6** (da solo, prima di ogni rendimento). Dati congelati in `crypto/` e `azioni/` (`DATI.md`).
Motore: `radar.weekly.simulate` invariato (crypto) e `ma_lib.s1_sim` (azioni). Risultati dal 01/06/2020 (inizio della versione
completa) al 24/11/2026; 10.000 $ per asset, 1x, costi e funding inclusi.

**Verdetto (soglie del PREREG)**
- **Q1 · crypto valutabili, parametri di BTC: NON SI TRASFERISCE.** 0 altcoin su 78 passano davvero. Passano 1–5 e conferma solo
  ETH e STX (con BTC), ma nessuna supera Holm su 79 asset (ETH p = 0,0045, Holm 0,34). Conferma la lezione 111 anche dal 2020.
- **Q2 · top 200 del 2020 (senza bias di sopravvivenza): NON SI TRASFERISCE.** 0 su 54 altcoin; passa 1–5 solo ETH. Conto
  equipesato W3.2: 19.161 $ (valutabili 2020) contro 22.736 $ (valutabili di oggi): il bias vale circa 3.600 $ su 10.000.
- **Q3 · azioni con `cmf20`: AZIONI CHIUSE PER W3.2.** 0 titoli su 124 passano 1–5, sia solo prezzo sia con `cmf20` (mediana
  CAGR/DD −0,06 contro 0,30 del buy & hold; WR mediano 31%). `cmf20` non cambia nulla (differenza mediana +0,01).
- **Q4 · BTC come cancello: SOLO CASI ISOLATI.** 1 altcoin su 78 passa davvero: **TRX** (87.198 $, DD −22,5%, 12 trade, WR 83%,
  p = 0,0005, Holm 0,039; perp su Bitget e OKX). Il cancello riduce il DD mediano (−39% contro −56%) ma non crea un vantaggio diffuso.
- **Q5 · parametri per classe: NON MIGLIORA** né per le altcoin (scelta IS 3,0 ATRw / 25%; in OOS passano 1–5 in 2 contro 3) né per
  le azioni (scelta IS 2,5 / 10%; 1 contro 1). Nessun asset passa davvero in OOS.
- **Q6 · portafoglio: MIGLIORA, ma con un solo candidato e da confermare.** BTC + ETH + TRX(Q4): CAGR/DD 2,49 contro 2,44 dal
  06/2020 (DD −18,9 contro −20,6) e 2,13 contro 1,80 dal 2021 (DD −18,2 contro −20,2). Aggiunge 1,9 operazioni l'anno, 84% delle
  settimane nello stesso verso di BTC.
- **Q7 · SOL e TAO: NON OPERARLE CON W3.2.** SOL rende (80.661 $) ma con DD −39,8% e WR 48%, e dal 2024 perde (−10% in tre anni);
  TAO perde (6.512 $, DD −52%, WR 21%).
- **Q8 · screener all'indietro: NON GIUSTIFICA IL MOTORE NEL TOOL.** Dal 2022 il conto "screener" fa 8.535 $ (DD −30%) contro
  22.762 $ di BTC + ETH e 11.198 $ di "tutte le idonee": gli asset con un buon passato non lo ripetono.

**Controlli**: (a) BTC 2021-01-01 → 2026-11-10 con motore e dati nuovi = **78.474 $** (identico); (b) ETH = 34.758 $ contro 34.760 $
di w32_top100: la differenza di 2 $ è il funding 01–10/11/2026 dello short ETH aperto il 09/11 (w32_top100 aveva il funding fino al
31/10; togliendolo torna 34.760 $; prezzi e taker buy identici); (c) la copia del motore per Q5 (`weekly_q5.py`) a 2,5/0,25 dà
trade e finale identici a `radar.weekly` su BTC, ETH, SOL; (d) `ma_lib.s1_sim` riproduce 864/864 righe di `azioni/counts.csv`.
**Riferimenti**: BTC W3.2 dal 2021 78.474 $ (al 10/11) / 84.820 $ (al 24/11), dal 06/2020 225.069 $ (DD −21,1%); ETH W3.2 dal
2021 39.572 $, dal 06/2020 53.394 $ (DD −27,5%); liquidità 10.000 $.

Colonne delle tabelle: finale da 10.000 $, CAGR, DD giornaliero, trade (posizione aperta inclusa), WR, buy & hold (finale · DD ·
CAGR/DD), IS 2020–22 / OOS 2023→ (o le due metà se l'IS o l'OOS è < 6 mesi), criteri falliti (1 CAGR/DD > B&H · 2 DD ≥ −35% · 3 WR
≥ 60% · 4 IS e OOS positivi · 5 ≥ 8 trade), conferma (senza il trade migliore > 10.000 $ e vicini 2,0/3,0 ATRw sopra il B&H in
almeno metà), p del placebo (2.000 prove, seme 7), p aggiustato di Holm sul numero di asset valutati nella domanda, perp Bitget/OKX.

## Q1 · crypto, motore completo, parametri di BTC
{Q1 · top 20 crypto di oggi}

{Q1 · migliori 15 e peggiori 5}

**Universo largo (79 valutabili, 78 altcoin)**: {Q1_SUMMARY}
Rispetto alla lezione 111 (dal 2021, 27 altcoin): aggiungere il 2020 e allargare a 78 altcoin non cambia il quadro. Passano 1–5
ETH e STX (STX era breve nel ciclo 1); TRX e SOL rendono ma falliscono DD e WR; VET fallisce solo il DD (−41%). Con la regola Holm
del ciclo 1 (solo sugli asset che passano 1–5, m = 3) passerebbero ETH e STX (2 su 78 = 2,6%, "casi isolati"): la regola del
PREREG, più severa, li esclude. Brevi e solo prezzo (descrittive): {BREVI}

## Q2 · top 20 del 2020 (CMC 29/12/2019)
{Q2 · top 20 crypto al 29/12/2019}

**Universo largo (55 valutabili del 2020, 54 altcoin)**: {Q2_SUMMARY}
Delle 191 monete del 2020 dopo le esclusioni solo 55 sono valutabili e 101 non hanno alcun dato operabile (token morti o mai
quotati con perp): chi avesse scelto allora la top 200 non avrebbe potuto operarne più di un terzo.

{Q2 · portafogli equipesati dal 01/06/2020}

## Q3 · azioni: solo prezzo contro `cmf20` (124 titoli, dal 2020)
{Q3 · top 10 azioni di oggi}

{Q3 · top 10 azioni a fine 2019}

**Universo largo**: {Q3_SUMMARY}
Nessun titolo passa 1–5 in nessuna variante: il criterio che cade quasi sempre è il WR (2 su 124 ≥ 60%) insieme al DD (7–12 su 124
≥ −35%) e al confronto con il buy & hold (11–12 su 124). Il flusso dai volumi giornalieri non sostituisce il flusso perp.
Per il PREREG le azioni sono chiuse per W3.2.

## Q4 · BTC come cancello (78 altcoin valutabili)
{Q4 · cancello BTC}

{Q4_TXT}
Limite dichiarato: il cancello non aggiunge momenti nuovi; per costruzione l'altcoin è quasi sempre nello stesso verso di BTC
(TRX 84% delle settimane in posizione, 0% opposto).

## Q5 · parametri per classe (scelta sul solo IS)
{Q5_TXT}

## Q6 · portafoglio (capitali uguali e separati)
| Dal | Portafoglio | Finale | CAGR | DD | CAGR/DD | Trade | Trade/anno |
|---|---|---|---|---|---|---|---|
{Q6_TAB}

Unico candidato operabile che passa davvero: TRX con il cancello di BTC (Q4). Migliora CAGR/DD e DD in entrambi i periodi, ma
rende meno di BTC da solo (dal 2021 68.913 $ contro 84.820 $): diversifica poco (84% delle settimane nello stesso verso di BTC).

## Q7 · SOL e TAO, in parole semplici
{Q7_TXT}

## Q8 · screener all'indietro (ogni 1° gennaio, dal 2022)
| Anno | Idonee | Scelte (risultato dell'anno) | Screener | BTC + ETH | Tutte le idonee | Solo BTC |
|---|---|---|---|---|---|---|
{Q8_TAB}

{Q8_TXT}

## Cosa dicono i dati
1. Fuori da BTC ed ETH il problema resta il **drawdown**: le altcoin valutabili hanno DD mediano −56% e WR mediano 40%; battono il
   buy & hold in CAGR/DD (64 su 78) solo perché i buy & hold crollano (finale mediano 2.096 $). Il ciclo 1 (lezione 111) è confermato
   su un universo tre volte più grande, dal 2020 e senza bias di sopravvivenza.
2. Senza bias di sopravvivenza (top 200 del 2020) va peggio: 0 su 54, e il conto equipesato perde 3.600 $ rispetto a quello costruito
   con la classifica di oggi.
3. Sulle azioni W3.2 non funziona nemmeno con un flusso dai volumi: `cmf20` lascia i risultati dove sono (lezioni 104 e 110).
4. Il cancello di BTC è l'unica idea nuova che sposta i numeri: dimezza i trade, alza il WR mediano da 40% a 50% e porta il DD
   mediano da −56% a −39%. Basta per un solo asset (TRX).
5. Cambiare trailing e rischio per classe non aiuta: il CAGR/DD non dipende dal rischio (lezione 101) e la cella migliore in IS
   non è la migliore in OOS.
6. Scegliere ogni anno "chi è andato bene" (Q8) peggiora: le altcoin con un buon passato (BCH, LTC, SNX nel 2023; ZRX, REN, WAVES
   nel 2024) perdono 23–46% l'anno dopo.

## Cosa significa per l'operatività
- **Nessun asset si aggiunge automaticamente.** BTC ed ETH restano come sono.
- **Proposta all'utente (da decidere, nulla attivato)**: TRX con il cancello di BTC (entra solo nello stesso verso di W3.2 su BTC),
  perp su Bitget e OKX. Se approvata: capitale separato e piccolo (per esempio 10.000 $, un terzo della quota di ETH), rischio 25%
  come BTC/ETH (DD storico −22,5%) oppure 10–15% per i primi mesi (DD −14/−17%), almeno 3–6 mesi su carta. Motivi di prudenza: è un
  solo asset su 78 tentativi; due trade (06/2023–03/2024 +96%, 09–12/2024 +161%) fanno quasi tutto il guadagno; 1,9 operazioni
  l'anno; TRX è una moneta molto centralizzata. Prima serve la revisione critica (`radar-review`) prevista dal PREREG.
- **SOL e TAO: no** con W3.2 (sezione Q7). **Azioni: no** (Q3). **Screener: no** per ora (Q8); al più una pagina informativa.

## Limiti
- **Bias di sopravvivenza**: l'universo di oggi esclude le monete morte; quello del 2020 le include, ma 101 su 191 non hanno dati
  operabili e restano fuori (non sostituite). Anche Q8 usa un universo che contiene la classifica di oggi (sguardo al futuro nella
  scelta dell'universo, non nelle regole).
- **Classifica 2020 da una sola fonte** (istantanea CoinMarketCap 29/12/2019 via Common Crawl; controlli con CMC 05/01/2020 e
  CoinGecko 24/01/2020); per le azioni CompaniesMarketcap (fine 2019).
- **Perp su azioni solo dal 2026** (≤ 10 mesi): lo studio azioni è sui titoli in borsa, in valuta locale, con short al 3% annuo
  (stima prudente; funding osservato ≈ +1%).
- **Costi stimati**: crypto come W3.2 (0,1%/0,05% per lato, slippage 0,1%, funding reale; novembre 2026 da OKX), azioni 0,05% per
  lato; B&H 0,2% (crypto) e 0,05% (azioni) per lato.
- **Placebo a 2.000 prove**: il p minimo è 0,0005; con Holm su 79 asset la soglia del primo è 0,00063, quindi passa solo chi ha il
  p minimo. Con questa regola nemmeno BTC passerebbe (p 0,0015, Holm 0,12): la severità dichiarata nel PREREG pesa molto.
- La versione completa non parte prima del 01/06/2020 (archivio perp dal 01/2020).

## Deviazioni dal PREREG (dichiarate)
1. IS/OOS: per gli asset con IS o OOS < 6 mesi (inizio dopo il 30/06/2022 o serie finita prima del 30/06/2023) si usano le due metà
   del periodo (come w32_top100).
2. Placebo: durate in sedute dell'indice (per le crypto = giorni; per le azioni evita di contare i giorni di borsa chiusa); CAGR
   annualizzato sugli anni di calendario.
3. Q5: CAGR/DD **non arrotondato** per la scelta della cella (arrotondato a 2 decimali dava mediane a pari merito: altcoin
   3,0/0,10–0,25 tutte 0,48). Per le azioni la scelta (2,5/0,10, mediana −0,1065) è quasi a pari merito con 3,0/0,10 (−0,1078),
   che avrebbe dato formalmente "migliora" (OOS 0,06 contro 0,01; 2 titoli contro 1: Saudi Aramco, non operabile, e Netflix, p 0,019,
   non significativo con Holm); nessun asset passa davvero in nessuna delle due. In OOS: criterio 4 = rendimento OOS positivo,
   criterio 5 = ≥ 8 trade nell'OOS, vicini = gli altri due trailing allo stesso rischio. Classe IS = valutabili con IS ≥ 6 mesi (66
   altcoin, 123 azioni). Azioni in solo prezzo perché `cmf20` non passa su nessun titolo.
4. Q4: BTC "in posizione" alla domenica = entrata ≤ domenica < uscita (un'uscita decisa quella domenica conta ancora); nei vicini
   (2,0/3,0) cambia solo il trailing dell'altcoin, BTC resta a 2,5.
5. Q8: idonee = classi "valutabile" e "breve" con versione completa iniziata prima del 1° gennaio, serie viva e primo prezzo ≥ 2
   anni prima (la classe finale non si usa perché dipende dal futuro); BTC è fra le idonee; ogni anno si riparte da flat il 1°
   gennaio, anche per BTC + ETH e "tutte le idonee".
6. Crypto solo prezzo: inizio = max(01/06/2020, primo dato + 300 giorni). Brevi simulate solo con ≥ 180 giorni di test (54 su 74).
7. Azioni: fine = ultimo dato (24–25/11/2026); l'eventuale settimana incompleta finale produce solo una decisione in sospeso.

## Lezione 123 proposta per RESEARCH.md
**Lezione 123**: W3.2 su 79 crypto valutabili (top 200 di oggi e del 2020, dal 06/2020) e 124 azioni (top 100 di oggi e del 2019,
dal 2020): con i parametri di BTC nessuna altcoin passa criteri, conferma e placebo con Holm (ETH e STX passano 1–5 ma non Holm su 79);
top 200 del 2020 0 su 54; azioni 0 su 124 anche con il flusso Chaikin 20 sedute. Il cancello "solo nel verso di W3.2 su BTC" porta
il DD mediano delle altcoin da −56% a −39% e fa passare solo TRX (87,2k $, DD −22,5%, WR 83%, 12 trade, p 0,0005; due trade fanno
quasi tutto); BTC + ETH + TRX: CAGR/DD 2,13 contro 1,80 dal 2021. Trailing e rischio per classe non migliorano in OOS. Uno screener
annuale "chi ha passato i criteri" perde contro BTC + ETH (8,5k contro 22,8k dal 2022). SOL (DD −40%, WR 48%, −10% dal 2024) e TAO
(−35%) non vanno operati con W3.2. research/w32_asset2/README.md (PREREG f40f7a6).

## File
`lib.py` (motore comune), `checks.py` → `out_checks.txt`; `run_crypto.py` → `risultati_crypto.csv`, `trades_crypto.csv`,
`eq_crypto.csv.gz`; `run_azioni.py` → `risultati_azioni.csv`, `trades_azioni.csv`, `eq_azioni.csv.gz`; `q4.py` → `risultati_q4.csv`,
`out_q4.txt`; `q5.py` (+ `weekly_q5.py`) → `q5_griglia.csv`, `risultati_q5.csv`, `out_q5.txt`; `q6.py` → `risultati_q6.csv`,
`out_q6.txt`; `q7_sol_tao.py` → `out_q7.txt`, `trades_q7.csv`; `q8_screener.py` → `risultati_q8.csv`, `out_q8.txt`; `tabelle.py` →
`out_tabelle.txt`; `build_readme.py` compone questo file. Ordine: checks → run_crypto → run_azioni → q4 → q5 → q6 → q7 → q8 →
tabelle → build_readme (circa 6 minuti con 4 processi).
