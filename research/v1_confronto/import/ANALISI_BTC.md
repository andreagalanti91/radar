# BTC · analisi tecnica, sentiment e algoritmo long/short

Fondamenti dell'analisi tecnica, lettura tecnica e di sentiment di BTC al 22/11/2026, e un algoritmo long/short costruito
sugli indicatori e testato dal 2018. Data del report: 23/11/2026.

> Ricerca su dati storici, non una raccomandazione d'investimento.

## 1. Sintesi

**BTC è in trend ribassista su tutte le scale e l'algoritmo oggi è fuori dal mercato: né long né short.**

| | |
|---|---|
| Prezzo | 61.271 $, a −51% dal massimo storico di 126.200 $ (06/10/2025) |
| Trend | 15 indicatori su 17 sono short; prezzo sotto le medie a 50 e 200 giorni e a 40 e 200 settimane |
| Momentum | RSI giornaliero 27 (ipervenduto), settimanale 35; MACD sotto il segnale su entrambe le scale |
| Supporti | 60.000, 57.800 (con Fibonacci 61,8%), 56.550; sotto, 49.000 |
| Resistenze | 63.000–69.000 (nodi di volume e massimo del 2021), poi 71.000–72.400 (medie a 200 giorni e 40 settimane) |
| Sentiment | paura estrema (Fear & Greed 11), ma i conti retail sono più long del solito |
| Algoritmo | fuori dal 29/10/2026; il segnale short non è scattato perché manca l'ultimo consenso |

L'algoritmo, in tre righe:

1. **Regola**: voto di 17 indicatori di trend; long con voto ≥ 0,50, short con voto ≤ −0,90, uscita quando il voto rientra.
2. **Risultato dal 2018**: 10.000 $ → 184.406 $, +38,8% annuo, drawdown −49,4%, 30 operazioni, 47% vincenti. Nel periodo di
   verifica 2022–26, mai usato per scegliere i parametri: +17% annuo con drawdown −34%, contro +5% e −67% di BTC tenuto.
3. **Limite principale**: gli short non rendono. I 7 short fatti dal 2018 hanno composto x0,97; tutto il guadagno viene dai
   long. Per restare entro −35% di drawdown su tutto lo storico serve usare metà capitale (0,5x: +21% annuo, −27%).

Rispetto ai tuoi obiettivi: il 70% di operazioni vincenti non è raggiunto (47%), e la leva peggiora il risultato già da 2x.

![BTC settimanale](results/btc/btc_tecnica.png)

## 2. Fondamenti dell'analisi tecnica

**I principi** (teoria di Dow, sistematizzata da Edwards, Magee e Murphy):

| Principio | Significato operativo |
|---|---|
| Il prezzo sconta tutto | si analizza il prezzo, non le notizie |
| I prezzi si muovono in trend | tre scale: primario (mesi-anni), secondario (settimane), minore (giorni) |
| Un trend vale fino a prova contraria | si segue finché non compare un segnale di inversione, non si anticipa |
| Il volume conferma il trend | un movimento senza volume è sospetto |
| Le medie si confermano a vicenda | un segnale conta di più se più indicatori indipendenti concordano |
| Supporti e resistenze | livelli dove in passato domanda o offerta hanno fermato il prezzo; un supporto rotto diventa resistenza |

**Le famiglie di indicatori** e a cosa servono:

| Famiglia | Esempi | Domanda a cui risponde | Debolezza |
|---|---|---|---|
| Trend | medie mobili, Ichimoku, Supertrend, ADX | in che direzione va il mercato? | arriva in ritardo, soffre nei mercati laterali |
| Momentum | MACD, RSI rispetto a 50, variazione a N giorni | il trend accelera o rallenta? | molti falsi segnali sulle scale corte |
| Rottura | canali di Donchian, bande di Bollinger | il prezzo esce da un intervallo? | le false rotture sono frequenti |
| Volume | OBV | i volumi accompagnano il movimento? | i volumi delle borse crypto sono rumorosi |
| Oscillatori contrarian | RSI 30/70, ritorno alle bande | il movimento è eccessivo? | in un trend forte restano "estremi" a lungo |
| Sentiment | Fear & Greed, funding, long/short | la folla è tutta da una parte? | descrive, raramente anticipa |

**Cosa dice la ricerca**:

- Park e Irwin (2007) hanno passato in rassegna 95 studi moderni: 56 trovano risultati positivi per le regole tecniche, 20
  negativi, 19 misti. Segnalano però che molti studi soffrono di selezione a posteriori delle regole.
- Le regole a medie mobili di Brock, Lakonishok e LeBaron (1992) funzionavano sul Dow Jones fino al 1986; Sullivan, Timmermann
  e White hanno mostrato che nei dieci anni successivi il vantaggio era sparito.
- Su Bitcoin, Detzel e coautori trovano potere predittivo nelle medie mobili da 5 a 100 giorni; uno studio su circa 15.000
  regole riporta rendimenti corretti per il rischio superiori al comprare e tenere, soprattutto per la riduzione dei
  drawdown. Gli studi che correggono per i test multipli trovano risultati più deboli, e gli indicatori contrarian (RSI,
  Bollinger) in genere sotto il comprare e tenere.

In breve: le regole che seguono il trend hanno un fondamento empirico, soprattutto come protezione dai ribassi; gli
oscillatori usati contro il trend no; e qualunque risultato va verificato su dati non usati per sceglierlo. Il censimento
qui sotto conferma tutti e tre i punti su BTC.

## 3. Censimento di 20 indicatori su BTC

Ogni indicatore usato da solo: long quando è rialzista, short quando è ribassista. Long in spot, short in perp con funding
reale, costi 0,10% per lato. Due periodi separati.

| Indicatore | Famiglia | Long/short 2018–21 | DD | Long/short 2022–26 | DD | Solo long 2018–21 | Solo long 2022–26 | Trade | Vincenti | Regge in entrambi? |
|---|---|---|---|---|---|---|---|---|---|---|
| Prezzo vs SMA 200 giorni | trend | -29% | -86% | +31% | -52% | +11% | +25% | 68 | 19% | solo long |
| SMA 50 vs SMA 200 (golden/death cross) | trend | -4% | -76% | -6% | -66% | +22% | +6% | 19 | 37% | no |
| EMA 20 vs EMA 50 | trend | +46% | -74% | +3% | -64% | +62% | +11% | 52 | 35% | solo long |
| Prezzo vs SMA 40 settimane | trend | -6% | -77% | +35% | -40% | +24% | +26% | 26 | 42% | solo long |
| Supertrend (10, 3) | trend | +23% | -72% | -12% | -76% | +52% | +2% | 77 | 35% | no |
| Ichimoku: sopra/sotto la nuvola | trend | +42% | -74% | +14% | -64% | +69% | +24% | 143 | 22% | sì |
| ADX > 25 con +DI/−DI | trend | +21% | -54% | +6% | -54% | +54% | +15% | 118 | 33% | solo long |
| MACD giornaliero vs segnale | momentum | +28% | -58% | -0% | -54% | +51% | +8% | 235 | 34% | no |
| MACD settimanale vs segnale | momentum | +8% | -79% | +9% | -52% | +36% | +13% | 32 | 38% | solo long |
| RSI giornaliero vs 50 | momentum | +49% | -56% | +9% | -61% | +66% | +14% | 305 | 23% | solo long |
| RSI settimanale vs 50 | momentum | -10% | -85% | +17% | -56% | +25% | +18% | 40 | 32% | solo long |
| Momentum a 90 giorni | momentum | +2% | -89% | +3% | -58% | +31% | +11% | 120 | 35% | solo long |
| Donchian 20 giorni | rottura | +59% | -62% | -6% | -75% | +69% | +5% | 68 | 41% | no |
| Donchian 55 giorni | rottura | +5% | -82% | +5% | -50% | +36% | +12% | 30 | 40% | solo long |
| Donchian 20 settimane | rottura | -6% | -87% | +18% | -53% | +21% | +17% | 9 | 44% | solo long |
| Bollinger: rottura delle bande | rottura | +77% | -58% | -1% | -69% | +79% | +8% | 64 | 41% | no |
| OBV vs sua SMA 100 | volume | +75% | -79% | +17% | -51% | +76% | +19% | 159 | 21% | sì |
| RSI 30/70 contrarian | contrarian | -35% | -95% | -11% | -77% | +6% | -0% | 28 | 54% | no |
| Bollinger contrarian | contrarian | -64% | -99% | -19% | -69% | -24% | -4% | 64 | 52% | no |
| Fear & Greed contrarian (<25 long, >75 short) | sentiment | -44% | -95% | -6% | -67% | -3% | +1% | 17 | 41% | no |
| *BTC comprato e tenuto (spot)* | – | +37% | -81% | +5% | -67% | – | – | – | – | – |

Cosa si impara:

1. **Nessun indicatore da solo è affidabile come long/short.** Solo due (Ichimoku e OBV) guadagnano oltre il 10% annuo in
   entrambi i periodi, con drawdown oltre −50%.
2. **Il lato short è il problema.** Usati solo long, tutti e 17 gli indicatori di trend chiudono in guadagno in entrambi i
   periodi.
3. **I contrarian perdono sempre**: RSI 30/70, ritorno alle bande di Bollinger e Fear & Greed al contrario perdono in
   entrambi i periodi. Comprare l'ipervenduto e vendere l'ipercomprato su BTC non ha funzionato.
4. **I risultati cambiano molto fra i due periodi.** Gli indicatori veloci (Donchian 20 giorni, Bollinger, Supertrend)
   brillano nel 2018–21 e si spengono dopo; quelli lenti (medie a 200 giorni e 40 settimane) fanno il contrario.
5. **Le percentuali di vincenti sono basse** (19–44% per le regole di trend): guadagnano con poche operazioni grandi.

Per questo l'algoritmo non sceglie l'indicatore migliore: usa il voto di tutti.

## 4. BTC oggi: analisi tecnica

| Misura | Valore | Lettura |
|---|---|---|
| Prezzo (chiusura del 2026-11-22) | 61.271 $ |  |
| Massimo storico | 126.200 $ il 2025-10-06 | prezzo a -51% dal massimo |
| SMA 50 giorni | 76.762 $ | prezzo -20% |
| SMA 200 giorni | 72.385 $ | prezzo -15%; SMA 50 sopra la SMA 200 |
| SMA 40 settimane | 71.971 $ | chiusura settimanale -15% |
| SMA 200 settimane | 68.176 $ | prezzo -10% |
| RSI 14 giornaliero / settimanale | 27 / 35 | sotto 30 = ipervenduto |
| MACD giornaliero / settimanale | sotto / sotto il segnale | MACD settimanale negativo |
| ADX 14 con +DI / −DI | 49 (6 / 40) | sopra 25 = trend forte; −DI sopra +DI = ribassista |
| ATR 14 giornaliero | 3.011 $ | 4,9% del prezzo |
| Bande di Bollinger (20, 2) | 55.913 – 82.925 $ | prezzo dentro le bande |
| Canale di Donchian a 20 settimane | 55.130 – 87.396 $ |  |
| Variazione a 7 / 30 / 90 giorni | -6% / -25% / -22% |  |

Lettura:

- **Trend primario ribassista.** Il prezzo è sotto tutte le medie principali, compresa quella a 200 settimane (68.176 $), un
  livello raggiunto in passato solo nelle fasi avanzate dei mercati ribassisti (2018–19 e 2022). L'ADX a 49 con −DI molto sopra +DI indica un ribasso forte, non
  un mercato laterale.
- **Ipervenduto di breve.** RSI giornaliero a 27 e −25% in 30 giorni. Nei dati questo non è un segnale d'acquisto (capitolo
  3), ma rende probabile un rimbalzo tecnico verso le resistenze.
- **La media a 50 giorni è ancora sopra quella a 200**: con il prezzo a −20% dalla prima, l'incrocio al ribasso ("death
  cross") è vicino.

Livelli, dal più alto al più basso:

| Livello | Distanza dal prezzo | Che cos'è | Ruolo |
|---|---|---|---|
| 87.396 $ | +43% | massimo di swing settimanale (2026-09-27) | resistenza |
| 83.903 $ | +37% | ritracciamento di Fibonacci 38,2% del ciclo | resistenza |
| 82.850 $ | +35% | massimo di swing settimanale (2026-05-10) | resistenza |
| 80.600 $ | +32% | minimo di swing settimanale (2025-11-23) | resistenza |
| 74.508 $ | +22% | minimo di swing settimanale (2025-04-13) | resistenza |
| 73.777 $ | +20% | massimo di swing settimanale (2024-03-17) | resistenza |
| 72.385 $ | +18% | SMA 200 giorni | resistenza |
| 71.997 $ | +18% | massimo di swing settimanale (2024-06-09) | resistenza |
| 71.971 $ | +17% | SMA 40 settimane | resistenza |
| 70.838 $ | +16% | ritracciamento di Fibonacci 50,0% del ciclo | resistenza |
| 70.080 $ | +14% | massimo di swing settimanale (2024-08-04) | resistenza |
| 69.000 $ | +13% | nodo di volume dal 2024 (fascia 68.000–70.000) | resistenza |
| 69.000 $ | +13% | massimo del ciclo 2021 | resistenza |
| 68.176 $ | +11% | SMA 200 settimane | resistenza |
| 67.000 $ | +9% | nodo di volume dal 2024 (fascia 66.000–68.000) | resistenza |
| 65.000 $ | +6% | nodo di volume dal 2024 (fascia 64.000–66.000) | resistenza |
| 63.000 $ | +3% | nodo di volume dal 2024 (fascia 62.000–64.000) | resistenza |
| **61.271 $** | – | **prezzo attuale** | – |
| 60.000 $ | -2% | minimo di swing settimanale (2026-02-08) | supporto |
| 57.800 $ | -6% | minimo di swing settimanale (2026-07-05) | supporto |
| 57.772 $ | -6% | ritracciamento di Fibonacci 61,8% del ciclo | supporto |
| 56.553 $ | -8% | minimo di swing settimanale (2024-05-05) | supporto |
| 49.000 $ | -20% | minimo di swing settimanale (2024-08-11) | supporto |
| 39.171 $ | -36% | ritracciamento di Fibonacci 78,6% del ciclo | supporto |
| 38.555 $ | -37% | minimo di swing settimanale (2024-01-28) | supporto |

- **Supporto decisivo: 55.000–58.000 $.** Qui cadono il ritracciamento del 61,8% del ciclo, i minimi di luglio 2026 e di
  maggio 2024 e il minimo del canale a 20 settimane (55.130 $). Una chiusura settimanale sotto apre lo spazio fino a 49.000 $.
- **Prima resistenza: 63.000–69.000 $**, la fascia più scambiata dal 2024, chiusa in alto dal massimo del 2021.
- **Resistenza di trend: 71.000–72.400 $** (medie a 200 giorni e 40 settimane, Fibonacci 50%). Finché il prezzo resta sotto,
  ogni rialzo è un rimbalzo dentro un trend ribassista.

Il voto dei singoli indicatori oggi:

| Indicatore | Famiglia | Oggi |
|---|---|---|
| Prezzo vs SMA 200 giorni | trend | short |
| SMA 50 vs SMA 200 (golden/death cross) | trend | long |
| EMA 20 vs EMA 50 | trend | short |
| Prezzo vs SMA 40 settimane | trend | short |
| Supertrend (10, 3) | trend | short |
| Ichimoku: sopra/sotto la nuvola | trend | short |
| ADX > 25 con +DI/−DI | trend | short |
| MACD giornaliero vs segnale | momentum | short |
| MACD settimanale vs segnale | momentum | short |
| RSI giornaliero vs 50 | momentum | short |
| RSI settimanale vs 50 | momentum | short |
| Momentum a 90 giorni | momentum | short |
| Donchian 20 giorni | rottura | short |
| Donchian 55 giorni | rottura | short |
| Donchian 20 settimane | rottura | long |
| Bollinger: rottura delle bande | rottura | short |
| OBV vs sua SMA 100 | volume | short |
| RSI 30/70 contrarian | contrarian | long |
| Bollinger contrarian | contrarian | long |
| Fear & Greed contrarian (<25 long, >75 short) | sentiment | long |

Voto degli indicatori di trend: 2 long, 15 short su 17: punteggio -0,76. Posizione dell'algoritmo long/short: **fuori** dal 2026-10-29. Versione solo long: **fuori**.

## 5. Sentiment

| Misura | Valore | Lettura |
|---|---|---|
| Fear & Greed (alternative.me) | 11 | paura estrema; più basso solo nel 2,2% dei giorni dal 2018; sotto 25 da 10 giorni |
| Fear & Greed, media a 30 giorni | 29 | un anno fa 26 |
| Funding del perp, media 7 / 30 giorni | -0,0% / +5,7% annuo | intorno a zero: nessun eccesso da una parte |
| Rapporto long/short dei conti (Binance) | 2,63 | media a un anno 1,66; sopra 1 = più conti long che short |
| Rapporto long/short dei grandi conti, per posizione | 1,72 | media a un anno 1,58 |
| Open interest (BTC, Binance) | 91.560 | -5% in 30 giorni, -7% in un anno |
| Volatilità realizzata a 30 giorni | 46% annua | media a un anno 42% |

Dalle notizie degli ultimi giorni: il Fear & Greed è sceso fino a 9 il 20/11 (6 sull'indice di CoinMarketCap il 21/11); il
20/11 sono state liquidate posizioni per circa 1,5 miliardi di dollari; il 19/11 gli ETF spot su Bitcoin hanno registrato
deflussi per 582 milioni di dollari. Anche l'indice di paura sulle azioni (CNN) è a 14.

Lettura:

- **Paura estrema, ma senza capitolazione dei conti retail.** Il rapporto long/short dei conti è a 2,63 contro una media di
  1,66: molti piccoli conti stanno comprando il ribasso a leva. È carburante per altre liquidazioni se il supporto cede.
- **Funding intorno a zero**: non c'è l'eccesso di short che di solito precede un rimbalzo violento.
- **Open interest in calo moderato** (−5% in 30 giorni): la leva si sta riducendo, ma non è stata azzerata.

Che cosa è successo in passato dopo letture simili, dal 2018:

| Condizione (primo giorno dell'episodio) | Episodi | Dopo 7 giorni: media / mediana / positivi | Dopo 30 giorni | Dopo 90 giorni |
|---|---|---|---|---|
| Tutti i giorni dal 02/2018 | 3217 | +1% / +0% / 52% | +4% / +2% / 54% | +14% / +4% / 54% |
| Fear & Greed ≤ 25 (paura estrema) | 130 | -1% / -1% / 46% | -1% / -2% / 46% | -0% / -8% / 45% |
| Fear & Greed ≤ 15 | 61 | +1% / -0% / 49% | +7% / +3% / 63% | +5% / -6% / 47% |
| Fear & Greed ≤ 10 | 42 | +3% / +0% / 51% | +3% / +3% / 55% | +11% / +4% / 57% |
| Fear & Greed ≤ 15 con prezzo sotto la SMA 200 | 54 | +1% / +1% / 54% | +8% / +5% / 66% | +5% / -6% / 45% |
| Fear & Greed ≤ 15 con prezzo sopra la SMA 200 | 8 | -1% / -2% / 25% | +2% / -0% / 50% | +1% / -1% / 50% |
| Fear & Greed ≥ 75 (avidità estrema) | 60 | +2% / +1% / 55% | +4% / -2% / 45% | +6% / -6% / 44% |
| Fear & Greed ≥ 90 | 18 | +8% / +7% / 72% | +30% / +24% / 89% | +113% / +145% / 89% |
| Funding medio a 7 giorni negativo (dal 2020) | 31 | +3% / +2% / 60% | +8% / +6% / 67% | +24% / +18% / 60% |

- **La paura estrema non è un segnale d'acquisto.** Dopo un Fear & Greed sotto 25 i rendimenti a 30 e 90 giorni sono stati
  uguali o peggiori della media. Sotto 10, come oggi, sono nella media: +3% a 30 giorni, positivi nel 55% dei casi.
- **Il sentiment su BTC segue il trend, non lo anticipa**: i rendimenti migliori sono arrivati dopo l'avidità estrema
  (sopra 90), non dopo la paura.
- **Il funding negativo è l'unico segnale contrarian con qualche valore** (+8% medio a 30 giorni, 67% positivi, 31 episodi).
  Oggi è a zero, non negativo.

Conclusione sul sentiment: descrive bene la situazione, ma da solo non giustifica un acquisto. Un filtro che vieta nuovi
short con Fear & Greed sotto 20 migliora l'algoritmo di meno di un punto l'anno: non l'ho incluso.

## 6. L'algoritmo long/short

### 6.1 Regole

| | Regola |
|---|---|
| **Voto** | 17 indicatori di trend, momentum, rottura e volume (tutti quelli del censimento tranne i contrarian e il sentiment). Ognuno vale +1 se rialzista, −1 se ribassista, 0 se neutro. Voto = media, da −1 a +1. |
| **Long** | voto ≥ 0,50: almeno 13 indicatori rialzisti su 17 quando gli altri sono ribassisti. Acquisto spot. |
| **Short** | voto ≤ −0,90: almeno 16 ribassisti su 17 e nessuno rialzista. Vendita sul perp. |
| **Uscita** | long: voto sotto 0,25. Short: voto sopra −0,25. |
| **Frequenza** | controllo alla chiusura giornaliera (00:00 UTC), operazione all'apertura successiva |
| **Dimensione** | 1x del capitale dedicato; nessuna leva |

Parametri scelti sul 2018–21 (miglior rapporto rendimento/drawdown fra 104 combinazioni): long con voto ≥ 0,50, short con voto ≤ −0,90, uscita quando il voto torna oltre 0,25, decisione giornaliera. Versione solo long: voto ≥ 0,50, uscita sotto 0,25, decisione giornaliera.

| Versione | 10.000 $ → (2018–2026) | CAGR | Max DD | Sharpe | Trade | Vincenti | Vincita / perdita media | 2018–21: CAGR / DD | 2022–26: CAGR / DD | Tempo a mercato |
|---|---|---|---|---|---|---|---|---|---|---|
| Long/short (scelto sul 2018–21) | 184.406 | +38,8% | -49,4% | 0,95 | 30 | 47% | +51% / -9% | +70% / -49% | +17% / -34% | 54% |
| Solo long (scelto sul 2018–21) | 190.653 | +39,3% | -41,2% | 1,04 | 23 | 48% | +60% / -7% | +68% / -41% | +19% / -32% | 42% |
| BTC comprato e tenuto | 45.793 | +18,7% | -81,2% | 0,59 | 1 | 100% | +346% / n/d | +37% / -81% | +5% / -67% | 100% |
| Long/short con volatilità obiettivo 50% | 117.983 | +32,0% | -38,1% | 0,96 | 30 | 47% | +38% / -7% | +55% / -38% | +16% / -33% | 54% |
| Long/short, senza nuovi short con Fear & Greed < 20 | 192.141 | +39,4% | -49,4% | 0,96 | 29 | 48% | +51% / -9% | +70% / -49% | +18% / -33% | 52% |

Robustezza: delle 104 combinazioni di soglie, il 95% guadagna nel 2022–26; rendimento mediano 2022–26 +11,4% annuo con drawdown mediano -45,8%. Con gli short ammessi a soglia bassa (≤ 0,75) il rendimento mediano 2018–21 è +9,2% annuo; senza short +47,7%.

- **Tutti e 17 gli indicatori entrano nel voto**: non ho scelto i migliori, per non adattare la regola al passato.
- **La soglia short è molto più severa di quella long**: l'ha scelta il periodo 2018–21, e riflette il censimento.
- **La volatilità obiettivo riduce il drawdown** da −49% a −38% togliendo 7 punti di rendimento annuo.

![Algoritmo](results/btc/btc_algoritmo.png)

### 6.2 Anno per anno

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| Long/short (scelto sul 2018–21) | +3% | +61% | +136% | +115% | +3% | +40% | +65% | +16% | -21% |
| Solo long (scelto sul 2018–21) | -25% | +83% | +172% | +115% | +0% | +40% | +65% | +10% | -7% |
| BTC comprato e tenuto | -72% | +94% | +302% | +60% | -64% | +156% | +121% | -6% | -30% |
| Solo i trade long del long/short | -27% | +84% | +388% | +20% | – | +94% | +24% | +7% | -6% |
| Solo i trade short del long/short | +28% | -18% | – | – | +3% | – | – | -3% | -8% |

- Gli short hanno aiutato solo nel 2018 (+28%); nel 2022 il contributo è stato +3% e dal 2025 è negativo.
- Il 2026 è l'anno peggiore (−21%): cinque operazioni, nessuna oltre il +2%, in un mercato senza direzione chiara fino a
  novembre.

### 6.3 Tutte le operazioni

| Verso | Dal | Al | Giorni | Risultato |
|---|---|---|---|---|
| Long | 2018-01-01 | 2018-01-16 | 16 | -20,6% |
| Long | 2018-05-04 | 2018-05-10 | 7 | -7,8% |
| Short | 2018-11-19 | 2019-02-18 | 92 | +28,4% |
| Long | 2019-04-05 | 2019-07-24 | 111 | +99,1% |
| Long | 2019-08-03 | 2019-08-28 | 26 | -7,7% |
| Short | 2019-11-25 | 2020-01-12 | 49 | -17,9% |
| Long | 2020-01-29 | 2020-02-26 | 29 | -6,4% |
| Long | 2020-05-04 | 2020-09-03 | 123 | +13,9% |
| Long | 2020-10-11 | 2021-04-22 | 194 | +357,3% |
| Long | 2021-08-02 | 2021-09-21 | 51 | +2,1% |
| Long | 2021-10-04 | 2021-11-18 | 46 | +17,9% |
| Short | 2022-01-24 | 2022-02-08 | 16 | -19,2% |
| Short | 2022-05-08 | 2022-08-14 | 99 | +27,6% |
| Long | 2023-01-14 | 2023-03-08 | 54 | +8,8% |
| Long | 2023-03-15 | 2023-05-24 | 71 | +6,6% |
| Long | 2023-05-29 | 2023-06-05 | 8 | -8,4% |
| Long | 2023-06-21 | 2023-08-17 | 58 | -6,0% |
| Long | 2023-10-23 | 2024-05-01 | 192 | +94,4% |
| Long | 2024-05-19 | 2024-06-11 | 24 | +0,5% |
| Long | 2024-07-20 | 2024-08-02 | 14 | -7,8% |
| Long | 2024-09-27 | 2024-10-01 | 5 | -6,8% |
| Long | 2024-10-16 | 2025-02-09 | 117 | +43,7% |
| Long | 2025-04-28 | 2025-08-25 | 120 | +17,3% |
| Long | 2025-09-17 | 2025-09-23 | 7 | -4,2% |
| Long | 2025-10-02 | 2025-10-10 | 9 | -5,0% |
| Short | 2025-11-17 | 2026-01-13 | 58 | -2,7% |
| Short | 2026-02-01 | 2026-03-15 | 43 | +1,5% |
| Long | 2026-05-11 | 2026-05-17 | 7 | -5,9% |
| Short | 2026-06-29 | 2026-07-26 | 28 | -9,2% |
| Long | 2026-08-22 | 2026-10-29 | 69 | -0,5% |

Long: 23 trade, 48% vincenti, composto x19,0. Short: 7 trade, 43% vincenti, composto x0,97.

Tre long (2019, 2020–21, 2023–24) fanno la gran parte del risultato; 16 operazioni su 30 chiudono in perdita, quasi tutte
sotto il 10%.

### 6.4 Leva e drawdown

| Leva | 10.000 $ → | CAGR | Max DD | 2018–21: CAGR / DD | 2022–26: CAGR / DD | Anno peggiore | DD entro −35%? |
|---|---|---|---|---|---|---|---|
| 0,5x | 53.716 | +20,8% | -26,8% | +35% / -27% | +10% / -18% | -10% | sì |
| 0,75x | 105.254 | +30,3% | -38,6% | +53% / -39% | +14% / -26% | -16% | no |
| 1x | 184.406 | +38,8% | -49,4% | +70% / -49% | +17% / -34% | -21% | no |
| 1,5x | 287.599 | +45,9% | -68,2% | +89% / -68% | +18% / -49% | -33% | no |
| 2x | 284.035 | +45,7% | -81,2% | +95% / -81% | +15% / -62% | -45% | no |
| 3x | 65.757 | +23,6% | -94,7% | +63% / -95% | -2% / -81% | -65% | no |
| 5x | 1 | -64,2% | -100,0% | -74% / -100% | -54% / -99% | -99% | no |

- **Il rendimento massimo è intorno a 1,5–2x**; oltre, la leva lo riduce, e a 5x il capitale si azzera.
- **Per restare entro −35% su tutto lo storico serve 0,5x**: +21% annuo con drawdown −27%.

### 6.5 Confronto con W3 del repo radar

| Dal 01/2021 al 10/11/2026 | CAGR | Max DD | Trade | Vincenti |
|---|---|---|---|---|
| Long/short (scelto sul 2018–21) | +29,9% | -34,3% | 21 | 48% |
| Solo long (scelto sul 2018–21) | +31,7% | -31,8% | 16 | 50% |
| W3 del repo radar, rischio 25% | +42,2% | −21,1% | 13 | 92% |
| W3.1 del repo radar, rischio 10% | +18,6% | −9,8% | 13 | 92% |

Sullo stesso periodo W3 resta migliore per rendimento, drawdown e percentuale di vincenti. W3 usa un dato in più, il flusso
sul perp, che nei tuoi test è ciò che fa la differenza su BTC. L'algoritmo tecnico ha due vantaggi: si può testare dal 2018 e
usa solo il prezzo.

## 7. Cosa fare adesso secondo l'algoritmo

| Scenario | Condizione | Azione |
|---|---|---|
| Oggi | voto −0,76: 15 short, 2 long | fuori dal mercato |
| Segnale short | voto ≤ −0,90: devono girare anche gli ultimi due indicatori. In pratica una chiusura sotto 55.130 $ (minimo a 20 settimane) insieme all'incrocio al ribasso delle medie a 50 e 200 giorni | short sul perp, 1x |
| Rimbalzo | prezzo verso 63.000–69.000 $ con voto ancora negativo | nessuna azione: è un rimbalzo dentro il trend ribassista |
| Segnale long | voto ≥ 0,50: richiede in pratica il prezzo stabilmente sopra 72.000 $ (medie a 200 giorni e 40 settimane) | acquisto spot |

Questo coincide con W3.1 di radar, che è short dal 16/11, e con l'algoritmo sulle altcoin di `ALGORITMO.md`, che non
ammette acquisti finché BTC è sotto la media a 40 settimane.

## 8. Limiti

- **Parametri scelti su quattro anni** (2018–21) e verificati su cinque: la verifica è reale, ma il periodo è uno solo e il
  rendimento è sceso dal 70% al 17% annuo.
- **30 operazioni in nove anni**: poche per stimare con precisione la percentuale di vincenti o il valore degli short (7).
- **Dati**: prezzi Binance spot; funding reale dal 2020 e fisso (0,01% ogni 8 ore) prima; nessun dato OKX prima del 12/2019.
- **Esecuzione** alla chiusura giornaliera, con slippage fisso: nei movimenti violenti l'esecuzione reale è peggiore.
- **Il sentiment** usa l'indice Fear & Greed, il funding e i rapporti long/short di Binance raccolti dal repo radar; i dati
  sulle notizie degli ultimi giorni vengono da fonti di settore non verificate una per una.
- I livelli di supporto e resistenza sono descrittivi: nel repo radar le strategie costruite sui livelli non hanno funzionato.
- Tasse non considerate.

## 9. Riproducibilità

```bash
python backtest/fetch_intraday.py binance
```

```bash
python backtest/btc_report.py
```

```bash
python backtest/build_report.py
```

Codice: `backtest/btc_ta.py` (dati, indicatori, voto, motore), `backtest/btc_report.py` (tabelle e grafici). Risultati in
`results/btc/`: `censimento_indicatori.csv`, `griglia_composito.csv` (le 104 combinazioni di soglie), `trade_long_short.csv`,
`livelli.csv`.

## Fonti

- [Park, Irwin — What do we know about the profitability of technical analysis? (Journal of Economic Surveys, 2007)](https://econpapers.repec.org/RePEc:bla:jecsur:v:21:y:2007:i:4:p:786-826) · [versione di lavoro](https://farmdoc.illinois.edu/publications/the-profitability-of-technical-analysis-a-review)
- [Park, Irwin — technical trading rules in US futures markets, con correzione per data snooping](https://ageconsearch.umn.edu/record/19039/files/cp05pa01.pdf)
- [Federal Reserve Bank of St. Louis — rassegna sulle regole tecniche (2011)](https://fraser.stlouisfed.org/docs/publications/frbsl_wp/2011-001.pdf)
- [Technical trading in cryptocurrency markets, circa 15.000 regole (Annals of Operations Research)](https://link.springer.com/article/10.1007/s10479-019-03357-1)
- [Technical trading rules' profitability and dynamic risk premiums of cryptocurrency exchange rates](https://emerald.com/insight/content/doi/10.1108/JCMS-10-2021-0030) · [studio su 12 criptovalute con controllo del data snooping](https://eprints.gla.ac.uk/302711/1/302711.pdf)
- [Bitcoin Magazine Pro — How good is the Bitcoin Fear & Greed Index](https://bmpro.substack.com/p/how-good-is-the-bitcoin-fear-and) · [KuCoin — what happens when the index hits extreme fear](https://www.kucoin.com/blog/what-happens-when-the-crypto-fear-greed-index-hits-extreme-fear)
- Notizie del 19–22/11/2026: [KuCoin — Bitcoin falls below $56,000, index at 6](https://www.kucoin.com/news/flash/bitcoin-falls-below-56-000-as-fear-and-greed-index-hits-6) · [Crypto Briefing — index falls to 14](https://cryptobriefing.com/fear-greed-index-falls-to-14-extreme-fear/) · [Bitcoin World — Bitcoin slips under $60,000](https://bitcoinworld.co.in/bitcoin-below-60k-extreme-fear/) · [Bitcoin.com — fear hits extreme levels](https://news.bitcoin.com/market-updates/bitcoin-fear-hits-extreme-levels-analyst-sees-contrarian-signal/) · [TokenPost — price recovers $61,000](https://www.tokenpost.com/news/investing/62408)
