# Scadenze delle opzioni BTC su Deribit · 27/11/2026 · rapporto descrittivo

**In sintesi:** la scadenza mensile di oggi (6,8 mld $) si è chiusa a **61.600 $**, lontanissima dal massimo dolore (70.000 $):
nessun effetto calamita, come già nello studio storico. La prossima scadenza grande è la **trimestrale del 25/12 (10,1 mld $,
la più grande in calendario)**. Le opzioni prezzano per BTC **circa ±6,6% entro il 04/12** e **±13% entro il 25/12** (2 volte
su 3). Le put costano più delle call: il mercato paga protezione dal ribasso, ma questo dato non predice la direzione
(`research/opzioni_direzione`). Per le posizioni short di W3.2 l'uscita in perdita di domenica (sopra 74.273 $, +20%) è fuori
da qualsiasi intervallo che le opzioni considerino probabile in 2 giorni. Solo contesto: W3.2 non cambia.

Fonte: API pubblica Deribit (`snap.py`, istantanea `dati/snap_20261127_0738.json`, 22 minuti prima della scadenza; regolamento da
`get_delivery_prices`). Calibrazione: `calib.py` → `calib.txt` (DVOL giornaliero dal 24/03/2021 contro `data/spot.csv`).

## Scadenze maggiori (≥ 0,7 mld $) alle 07:38 UTC, indice 61.527 $, DVOL 49

| Scadenza | Giorni | Valore | Put/call | Massimo dolore | Muri call | Muri put | IV ATM | Movimento atteso (1σ) | Skew put−call |
|---|---|---|---|---|---|---|---|---|---|
| ven 27/11 mensile | 0 | 6,8 mld $ | 0,79 | 70.000 (+13,8%) | 90k, 85k, 65k | 63k, 70k, 69k | — | — | — |
| ven 04/12 | 7 | 1,7 mld $ | 1,44 | 63.000 (+2,4%) | 75k, 70k | **58k (6.352 BTC)**, 60k | 47,7% | ±6,6% | +14 |
| ven 11/12 | 14 | 0,75 mld $ | 1,31 | 62.000 | 66k | 58k, 60k | 51,0% | ±10,0% | +12,5 |
| **ven 25/12 trimestrale** | 28 | **10,1 mld $** | 0,69 | 70.000 (+13,8%) | **80k (8.425)**, 100k, 90k | **60k (7.015)**, 40k, 55k | 47,6% | ±13,2% | +8 |
| ven 29/01 mensile | 63 | 1,8 mld $ | 1,10 | 67.000 | 70k | 58k, 40k | 45,7% | ±19,0% | +6 |
| ven 26/03 trimestrale | 119 | 3,5 mld $ | 0,67 | 70.000 | 80k, 150k | 50k, 55k | 45,8% | ±26,2% | +4,5 |

## Scadenza di oggi: cosa è successo
- Regolamento Deribit 08:00 UTC: **61.600 $** (media dell'indice nei 30 minuti prima). Indice alle 07:38: 61.527 $.
- Massimo dolore 70.000 $: il prezzo non si è avvicinato (−12% di distanza a scadenza). Delle call aperte, il grosso (90k, 85k)
  scade senza valore; delle put, gran parte degli strike 63–70k scade in guadagno per chi le aveva comprate.
- Lo studio storico (`research/opzioni_direzione`, 70 scadenze dal 2021): il prezzo si è avvicinato al massimo dolore nel 31%
  (2021–23) e 44% (2024–26) dei casi, non meglio di uno strike a caso (p 0,64). Oggi è un caso in più nella stessa direzione.

## Come si può muovere il prezzo nei prossimi giorni
Intervalli dalla volatilità implicita (prezzo di partenza 61.527 $). "Storico" = stesso calcolo corretto con quanto BTC si è
mosso davvero rispetto alla volatilità implicita dal 2021 (le code reali sono un po' diverse dalla curva teorica).

| Entro | 2 volte su 3 | 95 volte su 100 | storico 68% | storico 95% |
|---|---|---|---|---|
| ven 04/12 (7 g) | 57.600 – 65.700 | 53.900 – 70.200 | 58.500 – 64.800 | 53.400 – 70.700 |
| ven 25/12 (28 g) | 53.900 – 70.200 | 47.300 – 80.100 | 55.100 – 69.500 | 46.300 – 82.300 |
| dom 29/11 (2 g, chiusura W3.2) | circa ±3,6%: 59.300 – 63.800 | 57.100 – 66.100 | | |

**Quanto è affidabile il "movimento atteso"** (`calib.txt`, 2.062 settimane dal 2021):
- a 7 giorni BTC è rimasto dentro ±1σ nel **78%** dei casi (teoria 68%) e dentro ±2σ nel **94%** (teoria 95%);
- a 28 giorni: 72% e 92%;
- cioè le opzioni sopravvalutano di solito il movimento normale (sono "care": DVOL sopra la volatilità poi realizzata nel 72%
  delle settimane) ma le code estreme capitano un po' più spesso del previsto. Rialzo e ribasso sono equiprobabili (50–51%):
  **l'ampiezza è stimata bene, la direzione no.**

## Cosa significa per le posizioni di W3.2 (short BTC dal 16/11, short ETH dal 09/11)
- Uscita in perdita domenica 29/11 se BTC chiude sopra 74.273 $ (+20,7%): con ±3,6% di movimento atteso in 2 giorni è oltre 5
  deviazioni; le opzioni la considerano di fatto improbabile. Lo stop mobile (75.764 $) è ancora più lontano.
- Il muro di put a **58–60k** (04/12 e 25/12) e il massimo dolore del 04/12 a 63k sono livelli dove si concentrano posizioni,
  non bersagli: lo studio non trova che il prezzo ci vada.
- Skew positivo (+8/+14 punti): chi opera paga per proteggersi dal ribasso. È coerente con il clima ribassista, ma non è un
  segnale (H1 dello studio: nessun potere predittivo, segno instabile fra 2021–23 e 2024–26).

## Limiti
Istantanea unica; IV ATM = mark IV dello strike più vicino al future; skew = IV put ~10% fuori − IV call ~10% fuori (non
25-delta); intervalli simmetrici in logaritmo. Non è un segnale e non cambia W3.2.
