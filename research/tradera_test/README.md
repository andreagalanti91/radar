# tradera_test · il metodo di TraderA tradotto in regole e messo alla prova · 23/11/2026

## Verdetto
- **Replica: PARZIALE.** Su LMT è **fedele** (stessa linea marzo→agosto, ingresso 569,00 contro 567,93, stop 539,46 contro
  539,57, obiettivo 692,00 contro 688,69: scarti −0,02…+0,5%), ma è una calibrazione su un solo esempio. Su NVDA trova 3 zone su
  4 (la quarta, 29–33, esce a 26,9–28,9) più altre 8 che lui non disegna. Su BTC trova la zona del suo acquisto (52.088–56.553)
  ma **nessun segnale**: il suo acquisto a 55.778 non è un "rottura + ritest".
- **Strategia, azioni (20 del Dow 2000 con perpetuo): NON FUNZIONA**, né long né short, in nessuna delle 4 varianti. R medio
  −0,26…−0,51 per trade in entrambi i periodi; il placebo (ingressi a caso con gli stessi stop e obiettivi) fa uguale (p 0,21–0,70).
- **Strategia, crypto (BTC, ETH): NON DIMOSTRABILE** (5–17 trade per periodo; 2018–20 negativo, 2021–26 leggermente positivo,
  tutto dipende da 2–3 trade). Sul 4h di BTC la versione con confluenza è positiva (+0,19/+0,27 R) ma senza i 3 trade migliori
  la somma è negativa.
- **Dentro W3.2: NON MIGLIORA.** WV1 (ingresso al ritest con confluenza) 58,0k $ contro 78,5k $; WV2 (metà all'obiettivo di
  struttura) 67,2k $ con DD −18,0% contro −21,1%: meglio nel 2024–26, peggio nel 2021–23 e nel 2018–20.
- Confluenza EMA e forza relativa migliorano un po' l'R medio (+0,18 e +0,26 R) ma l'intervallo comprende lo zero e il
  risultato resta negativo. Gli short perdono sempre (−0,64…−0,79 R, WR 4–10%).
PREREG `PREREG.md` commit **9da09c8** (da solo, dopo la replica e prima di ogni rendimento). Nessuna modifica a radar/ o tests/.

## Fase 1 · replica (`tt_detect.py`, `tt_replica.py` → `replica.txt`)
| Punto | Trader | Rilevatore | Esito |
|---|---|---|---|
| (1) Linea LMT | massimo mar ~683 → massimo ago ~610 | 02/03 692,00 → 18/08 612,75; rottura 22/10 (balzo a 657 il 30/10) | coincide (lui scrive "inizio novembre": la rottura nei dati è il 22/10) |
| (2) Ritest/ingresso | 567,93 | ritest 05/11 (linea 574,8, EMA50 564 entro 1 ATR) → apertura 06/11 569,00 | coincide (+0,19%) |
| (3) Stop / obiettivo | 539,57 / 688,69 (4,3R) | 539,46 = minimo delle 3 barre prima della rottura −0,1% / 692,00 = punto A (4,2R) | coincide (−0,02% / +0,48%) |
| (3b) Short speculare | 567,65 / 585,13 / 499,69 | scatta solo con chiusura < 549,65 (linea − 1 ATR); stop massimo 3 barre (oggi 586,6); obiettivo 497,00 | vicino (obiettivo −0,5%; ingresso diverso: lui va short appena la linea cede) |
| (4) Zone NVDA | 140–150, 88–95, 44–50, 29–33 | 140,8–153,1 · 86,6–90,7 · 45,0–48,1 · 26,9–28,9 (+ 8 zone che lui non usa) | 3 coincidono, 1 vicina |
| (5) BTC 21/11 | acquisto 55.777,53 vicino al minimo 55.130 | zona 52.088–56.553 (5 tocchi, ultimo 2024); nessun segnale long; stato: short in attesa di ritest a ~73,4k | zona sì, segnale no |
Calibrazione dichiarata: 72 combinazioni su 162 riproducono LMT, ma solo con TOL ≤ 0,5 ATR e BASE ≤ 3; INV e le zone sono stati
scelti guardando gli esempi. Lo stop 539,57 è anche "5% sotto l'ingresso" (567,93 × 0,95 = 539,53): non si può sapere quale
delle due regole usi.

## Fase 2 · backtest (`tt_run.py` → `risultati.txt`, `varianti.csv`, `trade.csv`; `tt_w32.py` → `w32.txt`)
Azioni U2, rischio 2% per trade, funding long 5%, costi 0,10% per lato; 10.000 $ per periodo.
| Variante | 2016–20 finale / DD | 2021–26 finale / DD | Trade | WR | R medio A / B | Placebo R A / B | p | Esito |
|---|---|---|---|---|---|---|---|---|
| V1 base | 7.381 / −39,7% | 7.256 / −36,6% | 118 / 134 | 14–16% | −0,51 / −0,45 | −0,37 / −0,35 | 0,70 | non funziona |
| V2 + confluenza | 8.097 / −24,5% | 7.457 / −37,0% | 89 / 94 | 14–16% | −0,40 / −0,32 | −0,37 / −0,33 | 0,49 | non funziona |
| V3 + forza relativa | 11.091 / −17,3% | 5.752 / −47,0% | 70 / 65 | 14% | −0,31 / −0,29 | −0,43 / −0,45 | 0,21 | non funziona |
| V4 + piano speculare | 8.487 / −28,0% | 7.688 / −36,9% | 105 / 107 | 15–19% | −0,30 / −0,26 | −0,30 / −0,33 | 0,40 | non funziona |
| V2 solo long (descr.) | 11.145 / −28,4% | 13.590 / −20,1% | 35 / 42 | 20–33% | +0,03 / +0,40 | +0,30 / +0,11 | 0,43 | non funziona |
| V2 solo short (descr.) | 6.389 / −39,7% | 5.225 / −51,9% | 58 / 56 | 4–10% | −0,64 / −0,79 | −0,78 / −0,66 | 0,42 | non funziona |
| Flip lezione 114 | 4.800 / −60,7% | 5.602 / −54,8% | 2.180 / 2.681 | 55% | −0,14 / −0,10 | | | non funziona |
| Buy & hold (funding 5%) | 14.399 / −35,6% | 17.970 / −21,5% | | | | | | |

Crypto BTC+ETH (rischio 2%): V2 9.013 $ (2018–20, 5 trade) e 10.998 $ (2021–26, 7 trade); V1 7.777 / 10.230 $ (17/14 trade);
buy & hold 15.686 $ (DD −88%) e 22.273 $ (DD −77%); flip 9.373 / 16.025 $ (241 trade, R +0,11 nel 2021–26, ΣR senza i 3 migliori
+0,8). W3.2 BTC dal 2021 78.474 $ (DD −21,1%).
Capitale pieno (1x per asset, quote 1/20): DD −6…−11% solo perché ogni azione è in posizione per pochi giorni l'anno; finali
9.006–9.962 $. Robustezza: funding 0% e 10% sempre negativo; 11 vicini su 11 negativi sulle azioni nel 2016–20 e 10 su 11 nel
2021–26 (solo BASE 2 +0,20); 2021–23 −0,14 R, 2024–26 −0,43 R. Esempi: LMT 10 trade WR 0% (−1,16 R), NVDA 9 trade +2,2 R
(l'esempio di calibrazione vincente, non trasferibile).

W3.2 (10.000 $ per periodo, CAGR/DD): BTC 2021–23 2,57 · WV1 1,90 · WV2 2,21; 2024–26 1,64 · 1,57 · **2,63**; 2018–20 0,97 · 1,09 ·
0,86. ETH 2021–23 1,48 · 1,45 · 1,18; 2024–26 0,62 · 0,49 · 0,86. Nessuna variante passa (serve batterla in tutti e due i periodi).

Perché non regge: l'obiettivo "struttura precedente" è lontano (mediana +13% per i long, +23% per gli short, 4–7 volte il rischio)
e lo stop sotto la base della rottura è vicino (mediana 3%): l'85% dei trade finisce allo stop. Con WR 15% servono 6R medi per
pareggiare; il mercato ne dà quanti ne dà un ingresso a caso con le stesse distanze.

## Dove il rilevatore e il trader divergono
1. **Scelta dei casi.** La regola prende ogni rottura (252 setup azionari in 11 anni, ~1 per titolo l'anno); lui mostra quelli che
   sceglie. Su LMT stessa regola, 10 trade dal 2016: tutti stop. Il vantaggio, se c'è, sta nella selezione, che non è osservabile.
2. **Ritest già avvenuto.** Il 13/11 (prezzo 595) lui aspetta il ritorno a 567,93 come limite; per la regola il ritest c'è stato
   il 05/11 e il trade è già aperto da 569. Stesso prezzo, letture diverse.
3. **Short speculare.** Lui entra appena la linea cede con stop stretto (+3%); la regola chiede una chiusura 1 ATR sotto la linea.
4. **NVDA.** Lui legge 140–150 come supporto (19/11, 145,98); la regola era short dal 03/11 (rottura della linea rialzista
   164→190, ritest da sotto a 211, obiettivo 164 preso il 12/11) e il giorno dopo il suo grafico NVDA ha chiuso a 125,5 (−14%).
5. **BTC.** Il suo acquisto del 21/11 è "compra la paura sulla zona" (rimbalzo), non rottura + ritest: è la regola già respinta
   nelle lezioni 75–77 e 106. La regola vede la zona ma non dà ingresso.

## Stato al 22/11 (crypto) e al 20/11 (azioni) — `oggi.txt`
- **LMT**: long aperto dal 06/11 a 569,00, stop 539,46, obiettivo 692,00 (= il suo piano); ultima 565,50. Speculare short solo con
  chiusura < ~550.
- **NVDA**: nessun setup aperto; short del 03/11 chiuso all'obiettivo; prezzo 125,5 sotto la zona 140,8–153,1, vicino a 126,9–131,3.
- **BTC**: nessun long; short in attesa di ritest della linea rotta a ~73,4k (stop 75,7k, obiettivo 57,8k); linea ribassista
  sopra a ~84,7k. Prezzo 61,3k nella zona 57,8–61,8k.
- **ETH**: nessun segnale; linee attive a ~2.657 (sopra) e ~1.559 (sotto); prezzo 1.724 nella zona 1.680–1.751.

## Confronto in avanti (`confronto.py`, `confronto.csv`)
A ogni nuovo grafico: leggere asset, data, lato, ingresso, stop, obiettivo; `python3 fetch.py`; poi
`K.aggiungi(K.confronta(K.dati(asset), data, dict(lato=..., ingresso=..., stop=..., obiettivo=..., fonte=...), asset))`.
`confronta()` è pura e usa solo le barre fino alla data; a piano chiuso si compilano `esito_trader` ed `esito_rilevatore`.
Il registro parte con 4 righe (LMT long e short del 13/11, NVDA 19/11, BTC 21/11). Dopo 20–30 piani con esito si potrà dire se la
sua selezione batte la regola.

## Lezione proposta (120)
**Lezione 120**: il metodo di TraderA (linea su due massimi/minimi, rottura con slancio, ritest con confluenza EMA, stop sotto la
base della rottura, obiettivo alla struttura precedente) si riproduce con una regola: su LMT stessi numeri entro lo 0,5%
(calibrazione su un esempio), su NVDA 3 zone su 4. Applicata a tutti i casi non funziona: 20 azioni del Dow 2000 dal 2016, R medio
−0,3…−0,5 per trade in entrambi i periodi, WR 14–16%, uguale al placebo con gli stessi stop e obiettivi (p 0,21–0,70); short
sempre in perdita; confluenza e forza relativa non cambiano il segno; crypto con troppi pochi trade; dentro W3.2 né il ritest
come ingresso (58k $ contro 78,5k $) né metà all'obiettivo di struttura (67k $) migliorano. Il rapporto 3–4R mostrato nei suoi
piani si paga con l'85% di stop. Il suo eventuale vantaggio sta nella scelta dei casi: si misura solo in avanti (confronto.csv),
non con un backtest. research/tradera_test/README.md (PREREG 9da09c8; revisione critica separata non eseguita).

## Limiti
Calibrazione su 3 esempi; azioni come perpetui con funding ipotizzato (5%); crypto short senza funding; universo con bias residuo
("ha un perpetuo oggi"); BTC/ETH dal 2018 con pochi segnali; il rilevatore non legge volumi né altri strumenti che il trader
usa "a seconda del caso".
