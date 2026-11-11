# Report · Sfida a W2 + MACD (11/11/2026)

**Verdetto: sul profitto non l'ho battuta. L'ho resa più solida.**
Nessuna variante rende più di W2 nel backtest dal 2021. Quello che ho ottenuto è una versione ("W3") con lo stesso rendimento
per unità di rischio dal 2021 e un comportamento molto migliore nello scenario peggiore (2018).

## Da dove sono partito
Il vantaggio di W2 è il flusso dei perpetual; la sua debolezza è la fragilità: decide sul flusso di un solo giorno e sulla
chiusura di un solo giorno (domenica 118,6k nel backtest; 103k "come dal vivo"; mediana dei 7 giorni 53,5k; minimo 39k).
Ho provato a stabilizzare il segnale invece di aggiungere indicatori (già falliti: lezioni 83 e 84). Tutto è calcolato con il
flusso davvero disponibile al momento della decisione. Regole scritte prima dei risultati (PREREG.md).

## 1. Stabilizzare il flusso (2021 → oggi, 10.000 $)
| Flusso usato | Domenica | Mediana dei 7 giorni | Minimo | DD peggiore | 2018–20 mediana |
|---|---|---|---|---|---|
| Un giorno (com'è) | 103.012 $ | 53.494 $ | 38.961 $ | −37,5% | 20.836 $ |
| Media di 3 giorni | 100.416 $ | 67.365 $ | 38.776 $ | −39,7% | 19.999 $ |
| Media di 7 giorni | 124.493 $ | 62.589 $ | 35.554 $ | −40,8% | 12.272 $ |
| Flusso a 28 giorni | 59.010 $ | 42.836 $ | 21.387 $ | −39,1% | n.d. |
La media di 3 giorni alza la mediana (+26%) ma non il minimo: miglioria marginale, non una prova. 7 e 28 giorni peggiorano.

## 2. Confronto finale
| Strategia | Finale dal 2021 | CAGR | Max DD | MAR | 2021–23 | 2024→ | 2018–20 (DD) | Solo 2018 |
|---|---|---|---|---|---|---|---|---|
| **W2 dal vivo** (domenica, flusso 1 giorno) | **103.012 $** | 48,9% | −22,7% | **2,16** | 43.952 | 23.484 | 19.999 (−48,1%) | −32,6% |
| W2 "giorno medio" (7 tranche) | 60.688 $ | 36,1% | −23,6% | 1,53 | 27.545 | 20.991 | 21.354 (−45,5%) | −22,8% |
| A · 3 tranche (dom, mer, ven) | 70.343 $ | 39,5% | −22,7% | 1,74 | 31.038 | 21.436 | 22.295 (−47,0%) | −28,0% |
| C · A + flusso 3 giorni + cricchetto + liquidità 3,5% | 78.205 $ | 42,1% | −22,7% | 1,86 | 34.087 | 23.211 | 22.478 (−44,3%) | −24,5% |
| W3 a 3 tranche (C + tetto di rischio long 25%) | 65.207 $ | 37,7% | −22,4% | 1,69 | 29.053 | 22.878 | 25.831 (−40,0%) | −3,1% |
| **W3 domenica** (flusso 3 giorni + cricchetto + liquidità + tetto 25%) | **85.138 $** | 44,2% | **−20,7%** | **2,13** | 35.013 | 24.364 | **26.813 (−35,7%)** | **−7,3%** |
(Le colonne di periodo ripartono da 10.000 $. Buy & hold dal 2021: ~25.000 $, DD −77%.)

## Come leggerlo
- **Profitto**: W2 resta davanti (103k contro 85k). Chi l'ha costruita ha trovato il punto migliore del periodo.
- **Rischio**: W3 domenica ha lo stesso MAR (2,13 contro 2,16) con meno drawdown, e nel 2018–20 fa +168% contro +100% con
  drawdown −36% contro −48%; nel solo 2018 perde il 7% invece del 33%. Rinuncia al 17% del risultato dal 2021 in cambio
  della protezione dal caso peggiore (long comprato vicino a un top).
- **Fortuna della domenica**: dividere il capitale su 3 giorni di chiusura non rende di più; rende il risultato meno dipendente
  da un solo giorno (nel 2018–20 la domenica era quinta su sette). Costa tre decisioni a settimana invece di una.

## Cosa consiglio (da applicare solo su tuo ordine)
1. Tenere W2 come base e adottare "W3 domenica": flusso medio degli ultimi 3 giorni disponibili, trailing che non scende mai,
   liquidità remunerata quando si è fuori, tetto di rischio del 25% sui long. Una decisione a settimana, come oggi.
2. Le 3 tranche solo se accetti più operatività in cambio di meno dipendenza dalla domenica.
3. Attese realistiche: +15/+35% l'anno, drawdown intorno a −25/−30%.

## Dove potrei sbagliarmi
- Il periodo 2021–26 è stato usato moltissime volte: anche queste varianti sono state viste su quei dati. La prova vera sono il
  2018–20 (flusso stimato da un dato sostitutivo, non reale) e i prossimi trade reali.
- Il tasso del 3,5% sulla liquidità è un'ipotesi; senza, W3 domenica scende di circa l'8%.
- Il flusso a 3 giorni è una miglioria debole: se lo togli, il resto di W3 regge comunque.
- Con 13–14 trade ogni differenza sotto il 20% è dentro il rumore.

File: PREREG.md, run.py, run2.py, flussi_giorni.csv, confronto.csv.
