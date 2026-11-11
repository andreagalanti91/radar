# W2 + MACD · migliorie M1–M10 (10–11/11/2026) · ESITO: NESSUNA REGOLA DEL SEGNALE DA ADOTTARE; solo M1 (nota operativa)

Richiesta: "rendere la strategia ancora più redditizia", adottando solo ciò che regge alla robustezza. Regole e soglie in
`PREREG.md` (scritte prima dei risultati; M10 e la baseline "come dal vivo" aggiunte l'11/11, dopo M1–M9 e prima dei loro numeri).
Motore `eng.py` = copia di `radar.weekly.simulate` con opzioni: a opzioni spente replica esattamente trade ed equity (assert).

## Tabella dal 01/01/2021 (10.000 $, 1x, costi inclusi; DD giornaliero; MAR = CAGR/|DD|; dati fino al 09–10/11/2026)
| Variante | finale $ | rend. | max DD | trade | WR | MAR | trade cambiati | a pari DD | 2021–23 MAR | 2024→ MAR | 2018–20 rend/DD | Δ "dal vivo" | Verdetto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Buy & hold | 25.980 | +160% | −76,6 | 1 | – | 0,23 | – | – | 0,17 | 0,42 | +110/−81 | – | – |
| **W2 + MACD com'è** | 118.628 | +1.086% | −22,7 | 14 | 93% | 2,32 | – | – | 3,17 | 1,61 | +118/−48,1 | (103.012, 13 trade) | – |
| M1 liquidità 3,5% (T-bill reali: 126.814) | 128.517 | +1.185% | −22,7 | 14 | 93% | 2,41 | 0 | +8,3% | 3,28 | 1,69 | +132/−47,1 | +8,4% | **adottare (nota operativa)** |
| M2a EMA21: 2 chiusure | 132.974 | +1.230% | −22,7 | 13 | 92% | 2,45 | 6→5 | +12,1% | 3,44 | 1,58–1,63 | +103/−49,8 | +9,8% | respingere |
| M2b EMA21: margine 0,5 ATR | 162.792 | +1.528% | −22,7 | 12 | 92% | 2,69 | 6→4 | +37,2% | 4,08 | 1,56 | +74/−56,1 | +34,4% | respingere |
| M2c EMA21: chiusura giornaliera (più veloce) | 54.165 | +442% | −37,0 | 20 | 55% | 0,91 | 7→13 | −90,8% | 1,04 | 0,95 | +111/−49,7 | n.c. | respingere |
| M3a rientro rapido 6 sett. | 118.628 | = | = | 14 | 93% | 2,32 | 0 | 0 | = | = | = | n.c. | test vuoto |
| M3b pausa 2 sett. | 75.402 | +654% | −22,7 | 14 | 86% | 1,82 | 2 | −36,4% | 2,10 | 1,61 | +122/−48,1 | −36,4% | respingere |
| M4 runner 3 ATR dopo +2R | 112.146 | +1.021% | −25,9 | 14 | 93% | 1,97 | 1 | −32,4% | 3,17 | 1,24 | +88/−48,1 | −5,5% | respingere |
| M5 leva 1,3x nel regime migliore | 131.821 | +1.218% | −27,7 | 14 | 93% | 2,00 | 0 (5 long a leva) | −34,5% | 2,80 | 1,43 | +153/−48,1 | +11,1% | respingere |
| M6 short D1 (senza flusso) | 129.459 | +1.195% | −22,7 | 14 | 93% | 2,42 | 3 | +9,1% | 3,38 | 1,62 | +115/−48,6 | +9,1% | resta su carta |
| M7 R2 no ritest del top 1,5 ATR | 85.671 | +757% | −22,7 | 14 | 93% | 1,96 | 2 | −27,8% | 2,39 | 1,61 | +82/−46,9 | −27,8% | respingere |
| M9 trailing a cricchetto | 121.419 | +1.114% | −22,7 | 14 | 93% | 2,35 | 0 date (1 prezzo) | +2,4% | 3,17 | 1,69 | +119/−47,8 | +2,4% | neutro (non è un miglioramento) |
| M10 tetto di rischio long R25 | 92.128 | +821% | −21,1 | 14 | 93% | 2,18 | 0 (6 long ridotti) | −6,2% | 3,06 | 1,60 | **+170/−32,4** | −22,3% | su carta (scelta di rischio) |
| M10 R20 | 74.890 | +649% | −18,7 | 14 | 93% | 2,19 | 0 (8 ridotti) | +1,3% | 2,97 | 1,65 | +158/−31,1 | −36,8% | come sopra |

"A pari DD" = contro la baseline con leva uniforme scalata allo stesso DD. "Δ dal vivo" = stesso candidato contro la baseline con
il flusso perp del sabato (103.012 $, 13 trade, DD −22,7%, MAR 2,16; 2018–20 +100%/−48,1). Dettagli in `results.txt`, `results2.txt`.

## Cosa dicono i numeri
- **M1**: W2 è senza posizione il 39% dei giorni. Al 3,5% la liquidità aggiunge circa +2,1 punti di CAGR (+1,75 con i tassi T-bill
  storici, quasi zero nel 2021), +8–10k $ sul finale, senza cambiare trade né DD. Regge anche senza il trade migliore e nel 2018–20.
  È l'unico guadagno "gratuito"; non è una regola del segnale e ha il rischio di controparte dello strumento scelto.
- **M2**: i long usciti per EMA21 dal 2021 sono solo 2. Tutto il guadagno di M2a/M2b viene da UN episodio (long 08→11/2021 tenuto
  intero: +58% invece di +7,9% e +30,8%) più uno short 2022 tenuto un anno (M2b, +37%). Nel 2024→oggi non migliora (il segno cambia
  con un giorno di dati) e nel 2018–20 peggiora (+103/+74% contro +118%, DD fino a −56%). L'uscita del 09/11/2026 resta aperta a −3,3%
  invece di −4,1%: nessuna prova che fosse una falsa uscita. L'uscita più veloce (M2c) è un disastro: 13 trade nuovi, WR 55%.
- **M3**: dopo un'uscita EMA21 non esiste un rientro entro 6 settimane che la regola attuale non prenda già (test vuoto, come la
  lezione 44); la pausa toglie i due rientri migliori (10/2021 e 01/2023).
- **M4**: cambia un solo trade (uscita del 02/2025 più bassa) e peggiora in tutti i vicini: i long escono per distribuzione/EMA21
  prima che il trailing largo serva. La lezione 82 (intraday) non si trasferisce al settimanale.
- **M5**: a pari DD perde il 34,5%; il placebo (leva su 5 long a caso, 1.000 prove) fa meglio nel 98,7% dei casi. Il "regime migliore"
  non seleziona i trade migliori: i grandi vincenti sono nei trend vecchi con MACD in salita (lezione 61). Leva su tutti i long =
  baseline scalata (−7% a pari DD).
- **M6**: nessun trade D1 nuovo dal 07/11; vantaggio +9,1% (sotto la soglia del 10%), per due terzi da un trade (short 05/2022);
  2018–20 appena peggiore. Resta su carta, com'era.
- **M7**: con l'F1 attuale il 2018–20 fa +118%, DD −48,1%, ma il long dell'08/01/2018 (trend di 118 settimane, MACD sopra lo zero:
  F1 non lo blocca) perde −41% in 8 giorni. Senza F1: +10%, DD −72%. R2 non lo evita (lo sposta di una settimana: −39,6%), costa il
  28% dal 2021 e i vicini cambiano segno (2,0 ATR: +202% nel 2018–20). Nessuna protezione dal top passa.
- **M8 (attenzione)**: la domenica è il MIGLIOR giorno di chiusura su 7 dal 2021: 118,6k contro una mediana di 55,5k (min 42,4k,
  MAR mediano 1,26, DD fino a −39%, WR 62–85%). Nel 2024→oggi i sette giorni sono vicini (15,7–23,5k) e nel 2018–20 la domenica è
  quinta su sette: il vantaggio della domenica è quasi tutto nel 2021–23. Tutti i giorni battono il B&H (26k, DD −77%), quindi la
  famiglia regge, ma l'attesa onesta è più vicina alla mediana che ai 118k (WR 93% compreso).
- **M9**: lo stop non si allenta più quando l'ATR sale; effetto +2,4% (un prezzo di uscita nel 2025, stesse date), DD 2024→ −21,2
  contro −21,6. Innocuo, ma non è un miglioramento misurabile.
- **M10**: il tetto R25 riduce 6 long su 10 dal 2021 (anche i migliori: 01/2021 a 0,76x, 08/2021 a 0,54x) e costa il 22% del finale
  (−6% a pari DD); nel 2018–20 dimezza il danno (peggior trade −41% → −25%, DD −48% → −32%, rendimento +118% → +170%). Non supera
  la soglia preregistrata (costo < 5%): è un'assicurazione, non un guadagno. Equivale quasi a ridurre la quota di capitale (lezione 60)
  ma concentra la riduzione dove lo stop è lontano.

## Verdetto
Nessun candidato rende W2 più redditizia in modo robusto. **Adottare solo M1** come nota operativa (non tocca il segnale). **Su
carta**: M6 (già lì) e M10 R25 come scelta di rischio dell'utente. **Respingere** M2, M3, M4, M5, M7; M9 neutro. Da comunicare:
M8 (dipendenza dal giorno) e la baseline "come dal vivo" a 103k riducono l'attesa realistica.

File: `PREREG.md`, `eng.py`, `run.py` → `results.txt` (≈ 2 min), `run2.py` → `results2.txt`.
