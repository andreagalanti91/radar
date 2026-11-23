# Modello previsionale direzionale di BTC a 7 e 30 giorni (23/11/2026) · NON FUNZIONA

**Verdetto (preregistrato, PREREG.md, commit f656594).**
- **7 giorni: NON FUNZIONA.** Modello primario (media di 3 modelli): direzioni corrette fuori dalla fascia incerta 49,0% nel
  2021–23 e 51,4% nel 2024–26 (soglia 55%), AUC 0,48 / 0,49, uguale o peggio di "sale sempre" (50,9% / 51,4%).
- **30 giorni: NON FUNZIONA.** 50,5% / 55,4%, ma è esattamente "sale sempre" (50,5% / 55,4%): il modello non dice mai "giù"
  (0 previsioni ribassiste su 2.115 giorni), AUC 0,38 / 0,46 (sotto il caso), p = 0,60.
- Nessuno degli 8 test (2 orizzonti × 4 modelli) è significativo (p minimo 0,24; Holm 1,00). Brier skill ≈ 0 (−0,6% … +0,7%).
- **Non impara dai propri errori** in modo misurabile: aggiornato e statico sono indistinguibili; la ricalibrazione non migliora.
- **W3.2: nessuna delle 8 varianti passa.** W3.2 resta com'è.
- In dashboard NON va mostrato come previsione. Il registro delle previsioni (forecast_log.py) è pronto se si vuole misurarlo dal vivo.

Metodo: 12 variabili fissate prima (momentum 7/30/90 g, distanza da SMA50/200, RSI, volatilità, flusso perp e spot, funding, OI,
fear&greed; flussi con ritardo di 1 giorno), 3 modelli solo numpy (M1 logistica L2 sui prezzi, M2 logistica L2 su tutte, M3 ceppi
a terzili) + media M4; walk-forward espansivo dal 2015, riaddestramento mensile, embargo = orizzonte, iperparametri scelti
dentro l'addestramento; fascia incerta 45–55%. Osservazioni indipendenti: ~150 per periodo a 7 giorni, ~35 a 30 giorni
(accuratezza minima distinguibile dal 50%: ~60% e ~71% per periodo): a 30 giorni solo un effetto molto grande sarebbe visibile.

## Direzioni corrette fuori dalla fascia incerta (copertura) · AUC · Brier skill
| h | Modello | 2021–23 | 2024–26 | 2021–26 (IC 95% a blocchi) | p sfasamento | 2018–20* |
|---|---|---|---|---|---|---|
| 7 | M1 LOGIT-P | 48,3% (72%) · 0,46 · −0,8% | 49,9% (69%) · 0,49 · −0,3% | 49,1% (43–54) | 0,95 | 53,6% · 0,41 |
| 7 | M2 LOGIT-T | 52,2% (87%) · 0,50 · −0,5% | 50,0% (58%) · 0,49 · −0,8% | 51,3% (46–56) | 0,42 | 50,6% · 0,42 |
| 7 | M3 CEPPI | 52,3% (56%) · 0,51 · +0,7% | 53,5% (33%) · 0,50 · +0,3% | 52,7% (46–59) | 0,24 | 53,4% · 0,48 |
| 7 | **M4 MEDIA** | **49,0%** (67%) · 0,48 · 0,0% | **51,4%** (49%) · 0,49 · −0,2% | 50,0% (44–56) | 0,74 | 52,6% · 0,44 |
| 7 | R1 sale sempre | 50,9% | 51,4% | 51,1% | – | 53,6% |
| 7 | R2 persistenza | 46,9% | 49,2% | 48,0% | – | 50,8% |
| 7 | R3 regime W3.2 (in posizione) | 49,8% | 51,0% | 50,4% | – | 51,7% |
| 30 | M1 LOGIT-P | 50,5% (100%) · 0,36 · −0,1% | 54,9% (99%) · 0,40 · −2,0% | 52,6% (44–62) | 0,75 | 55,2% · 0,28 |
| 30 | M2 LOGIT-T | 50,5% (100%) · 0,38 · −0,4% | 55,5% (87%) · 0,52 · −0,7% | 52,7% (44–62) | 0,58 | 55,2% · 0,28 |
| 30 | M3 CEPPI | 50,6% (86%) · 0,42 · +0,3% | 55,3% (100%) · 0,43 · −0,1% | 53,0% (43–62) | 0,46 | 55,5% · 0,33 |
| 30 | **M4 MEDIA** | **50,5%** (100%) · 0,38 · 0,0% | **55,4%** (96%) · 0,46 · −0,6% | 52,8% (44–61) | 0,60 | 55,2% · 0,30 |
| 30 | R1 sale sempre | 50,5% | 55,4% | 52,9% | – | 55,2% |
| 30 | R2 persistenza | 55,3% | 47,2% | 51,4% | – | 50,9% |
| 30 | R3 regime W3.2 | 49,0% | 49,3% | 49,2% | – | 51,4% |

\* 2018–20 solo informativo (variabili di flusso in gran parte assenti). Il controllo a blocchi non sovrapposti (una previsione
ogni h giorni, media sulle fasi) dà gli stessi numeri al decimo di punto. Brier di M4: 0,253 a 7 g e 0,257 a 30 g (0,25 = "50% sempre").
R3 (lato della posizione W3.2) non prevede il SEGNO a 7–30 giorni meglio del caso: W3.2 guadagna con l'asimmetria dei
movimenti (pochi trend lunghi), non con la frequenza delle direzioni giuste.

**Perché fallisce.** Con la regolarizzazione scelta dentro l'addestramento i coefficienti vanno quasi a zero: la previsione è
la frequenza storica di rialzo (55–63%) più un piccolo scarto, quindi quasi sempre "su" (a 7 g: 1.242 "su", 0 "giù"; a 30 g:
2.072 "su", 0 "giù"). La frequenza base aggiornata arriva in ritardo sul ciclo (alta dopo i rialzi, cioè prima dei ribassi):
da sola ha AUC 0,46 (7 g) e 0,38 (30 g). **Calibrazione** (M4, 2021–26, decili): a 7 g piatta (p 52–60% → frequenze 41–57%
senza ordine); a 30 g rovesciata (decile più basso p 56% → 62% di rialzi; più alto p 63% → 35%).

**Variabili (coefficienti standardizzati di M2, 71 riaddestramenti dal 2021).** Segno stabile al 100% a entrambi gli orizzonti:
flusso perp (+), flusso spot (+), RSI (+), volatilità (−); tutti piccoli (ultimo: pf +0,04 / +0,07, gli altri ≤ 0,03). Instabili:
distanza dalle medie (segno stabile nel 37–68% dei casi), OI, funding a 7 g, momentum. Esplorativo, NON preregistrato
(auc_univariata_esplorativa.csv): da sola, la variabile pf ha AUC 0,54 / 0,53 a 7 g e 0,62 / 0,59 a 30 g nei due periodi — è il
dato del giro 9 e l'informazione che W3.2 usa già; le altre 11 stanno fra 0,42 e 0,57 e cambiano lato fra i periodi.

## "Imparare dai propri errori"
| Prova | 7 giorni | 30 giorni |
|---|---|---|
| (b) M4 aggiornato ogni mese contro addestrato una volta (31/12/2020), Brier 2021–26 | 0,2531 contro 0,2545 (diff −0,0014, IC −0,0040/+0,0012) | 0,2568 contro 0,2579 (diff −0,0011, IC −0,0076/+0,0054) |
| idem, AUC (aggiornato / statico) | 0,49 / 0,52 | 0,42 / 0,53 |
| (c) Platt espansiva C1, Brier contro grezzo | −0,0006 (IC −0,0055/+0,0035) | −0,0003 (IC −0,0104/+0,0110) |
| (c) Platt ultimi 730 giorni C2 | +0,0022 (peggio) | +0,0213 (peggio) |

Aggiornare non migliora in modo distinguibile dallo zero e l'ordinamento (AUC) peggiora; ricalibrare sugli errori recenti (C2)
peggiora: gli errori recenti non anticipano quelli futuri. (d) Registro: forecast_log.py (schema di data/forecast_log.csv,
`add`, `score`, `summary`; righe solo aggiunte, esito scritto una volta a scadenza, previsione dopo la scadenza rifiutata).

## Uso su W3.2 (dal 01/01/2021, 10.000 $, 1x, costi; motore = radar.weekly.simulate, verificato identico)
| Variante | Finale | Rend. | DD giorn. | Trade | WR | MAR | MAR 2021–23 / 2024–26 | Δ senza i 2 trade migliori | Placebo | Passa |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy & hold | 22.280 $ | +123% | −76,6% | 1 | – | 0,19 | | | | |
| **W3.2** | **78.474 $** | +685% | −21,1% | 13 | 92% | 1,99 | 2,57 / 1,63 | | | |
| F7a blocca se p7 discorda | 68.389 $ | +584% | −22,1% | 13 | 85% | 1,75 | 1,94 / 1,63 | negativo | 76° | no |
| F7b solo se p7 concorda | 56.224 $ | +462% | −19,9% | 10 | 80% | 1,72 | 2,09 / 1,38 | negativo | 99° | no |
| F30a blocca se p30 discorda | 56.932 $ | +469% | −19,9% | 11 | 82% | 1,73 | 2,09 / 1,41 | negativo | 93° | no |
| F30b solo se p30 concorda | 56.224 $ | +462% | −19,9% | 10 | 80% | 1,72 | 2,09 / 1,38 | negativo | 20° | no |
| D7 dimensione su p7 | 77.286 $ | +673% | −21,1% | 13 | 92% | 1,97 | 2,59 / 1,63 | negativo | 26° | no |
| D30 dimensione su p30 | 84.411 $ | +744% | −19,9% | 13 | 92% | 2,20 | 3,08 / 1,64 | negativo | 90° | no |
| U7 uscita se p7 contro 2 sett. | 75.602 $ | +656% | −18,7% | 13 | 85% | 2,20 | 3,01 / 1,55 | negativo | 35° | no |
| U30 uscita se p30 contro 2 sett. | 81.152 $ | +712% | −18,7% | 13 | 85% | 2,29 | 2,88 / 1,83 | negativo | 99° | no |

Il modello dice sempre "su" (p30 > 55% nel 98% delle domeniche, mai < 45%): "discorda" significa soltanto "il trade è uno short".
I filtri tolgono gli short (tutti vincenti dal 2021), D30 e U30 li riducono o li chiudono presto: il piccolo vantaggio di D30/U30
viene da 1–2 short e sparisce togliendo i 2 trade più favorevoli; nel 2018–20 (informativo) D30 e U30 fanno peggio di W3.2
(24,0k e 24,7k contro 25,1k). Il solo trade perso (23/08/2026, −4,1%) aveva p7 57% e p30 63%: non sarebbe stato evitato.
Potenza: 13 trade, 1 perdente — nessuna variante poteva essere dimostrata; qui nessuna supera nemmeno i criteri descrittivi.

## Probabilità attuali (solo esempio; dati data/ al 21/11/2026, chiusura 60.216 $)
7 giorni: **52%** (M1 54, M2 50, M3 52) → incerto. 30 giorni: **56%** (57, 55, 55) → formalmente "su", ma è sotto la frequenza
storica di rialzo a 30 giorni (58%): il modello sta dicendo "un po' meno del solito", senza capacità dimostrata.
Quadro: −30% in 30 giorni, flusso perp −1,6, funding z −1,8, fear&greed 12, W3.2 short dal 16/11.

## Limiti e deviazioni dal PREREG
- Potenza bassa a 30 giorni (~35 osservazioni indipendenti per periodo): l'esito non è "non dimostrabile" ma "non funziona"
  perché il modello coincide con "sale sempre" e ordina peggio del caso (AUC < 0,5), non perché manchi di poco la soglia.
- Deviazioni: (1) AUC univariata per variabile e controllo di sanità con segnale iniettato (il walk-forward lo trova: AUC 0,64–0,66)
  aggiunti dopo, dichiarati esplorativi; (2) bootstrap della tabella con 1.000 ricampionamenti invece di 2.000 e test di
  sfasamento dell'AUC con uno sfasamento ogni 3 (tempo di calcolo); (3) la ricalibrazione usa le previsioni walk-forward dal
  2018 come "errori passati" (non precisato nel PREREG); (4) U è realizzata portando l'esposizione a zero: il trade resta
  formalmente aperto fino all'uscita di W3.2 (come preregistrato: nessun rientro); (5) vicini non eseguiti: nessuna variante
  passa. Nessuna variabile, soglia o modello cambiato dopo i risultati; nessun modello "solo pf" è stato provato per salvare l'esito.
- Macro esclusa per storia insufficiente (data/macro.csv parte da 12/2024–06/2025). Solo BTC. Fear&greed da data/fng.csv.

## Lezione proposta (112)
**Lezione 112**: un modello previsionale direzionale a 7 e 30 giorni (12 variabili fissate prima, logistiche L2 e ceppi, media,
walk-forward mensile dal 2015 con embargo) non ha direzionalità fuori campione: 49–51% a 7 giorni e 50–55% a 30 giorni, cioè
"sale sempre" (non dice mai "giù"), AUC 0,38–0,49, 0/8 test significativi; riaddestrarlo o ricalibrarlo sugli errori non
migliora il Brier; come filtro, dimensione o uscita di W3.2 0/8 varianti (toglie o accorcia gli short vincenti). Anche il regime
W3.2 azzecca il segno a 7–30 giorni solo nel 49–51% dei casi: W3.2 guadagna con l'ampiezza dei trend, non con la frequenza. Con
~35 osservazioni indipendenti per periodo a 30 giorni servirebbe il 71% per dimostrare qualcosa. Unico segnale stabile: il flusso
perp (AUC 0,59–0,62 a 30 giorni da solo), già dentro W3.2. Non riproporre modelli multivariati di direzione su questi dati;
un'eventuale probabilità va prima misurata dal vivo con il registro delle previsioni. research/previsionale/ (PREREG f656594).

## Raccomandazione operativa
1. Non mostrare in dashboard una "probabilità a 7/30 giorni" come previsione, e non usarla in W3.2.
2. Se l'utente vuole comunque un numero di contesto, l'unica dicitura onesta è la frequenza storica: "Dal 2015 BTC è salito a 7
   giorni nel 55% dei casi e a 30 giorni nel 58%. Il modello non ha dimostrato di saper fare meglio (test del 23/11/2026):
   non è un segnale." In alternativa il solo stato del flusso perp, che è già la base di W3.2.
3. Opzione a costo zero: adottare forecast_log.py, registrare ogni domenica le probabilità di M4 PRIMA dell'esito e rivalutare
   dopo ≥ 100 previsioni settimanali risolte (~2 anni); fino ad allora nessuna esposizione in dashboard se non come "esperimento".

File: PREREG.md, fc_data.py, fc_models.py, fc_run.py, fc_w32.py, fc_oggi.py, forecast_log.py, risultati.txt, risultati_w32.txt,
tabella.csv, w32_varianti.csv, prob_h7.csv, prob_h30.csv, coef_h*.csv, calibrazione_h*.csv, oggi.json.
