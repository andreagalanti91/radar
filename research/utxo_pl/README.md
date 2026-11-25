# Indicatore "UTXO Block P/L Count Ratio" (sostituto MVRV) come supporto a W3.2 · BTC · 25/11/2026

**Verdetto: no come regola su W3.2; al massimo è contesto da leggere.** Nessuna delle tre regole passa i criteri del PREREG
(bdada1a). Chiudere lo short in capitolazione (H1 b) migliora il finale dal 2018 e dal 2021 e dal 2018 supera i criteri 1–3, ma dal
2021 il guadagno viene da un solo trade (lo short del 2022), il placebo non lo distingue dal caso (p 0,13), le quattro soglie vicine
sono tutte sotto W3.2 e con la soglia fissa a 1,0 perde. Chiudere il long in euforia (H3) è dannoso (−15.000 $ dal 2021). W3.2 resta
invariata; nessuna proposta al tool.

## Dati e metodo
La serie CryptoQuant è a pagamento: si usa come sostituto l'**MVRV di CoinMetrics** (community API, `CapMVRVCur`, giornaliero,
2011 → 24/11/2026, nessun giorno mancante), che misura la stessa idea (monete in guadagno o in perdita rispetto al prezzo
d'acquisto). Zone: capitolazione (a) MVRV < 1,0, (b) MVRV nel 10% più basso dei 1.460 giorni precedenti; euforia (a) > 3,0,
(b) nel 10% più alto. Lettura alla chiusura UTC, azione all'apertura del giorno dopo. Motore: copia di `radar.weekly.simulate`
(`up_engine.py`) con la sola regola aggiunta; senza regola riproduce W3.2 trade per trade (dal 2021 **78.474 $**, dal 2018
224.593 $, dal vivo 84.360 $ con lo short aperto). Prezzi congelati `research/p2_nuovi` al 15/11/2026, 10.000 $, rischio 25%,
costi e funding inclusi. Nessuno sguardo al futuro: il quantile di (b) usa solo i 1.460 giorni precedenti (escluso il giorno
stesso); verificato a mano su 5 date e ricalcolando le zone su dati tagliati al 2019, 2022 e 18/11/2026 (identiche).
Esecuzione: `python3 up_fetch.py` → `mvrv.csv`; `python3 up_coerenza.py` → `coerenza.txt`; `python3 up_run.py` (~20 min con 1.000
placebo) → `risultati.txt`, `varianti.csv`, `trade_cambiati.csv`, `placebo.csv`, `h4_trade.csv`.

## Coerenza del sostituto con il grafico dell'utente
| Finestra del grafico | Capitolazione (a) | Capitolazione (b) |
|---|---|---|
| inizio 2016 | no (MVRV < 1 nel 2015) | no (zona nel 2015) |
| 12/2018–03/2019 | sì (134 g) | sì (60 g) |
| 03/2020 | sì (6 g) | sì (13 g) |
| fine 2022 | sì (129 g) | sì (88 g) |
| 09/2023 | no | no |
| metà 2026 | no (minimo 1,103 il 30/06) | no |
| 11/2026 | no | **sì (dal 14/11 e dal 18/11)** |
| **Coincidono** | **3/7** | **4/7** |

Euforia: 2017 e inizio 2021 sì, fine 2024 no, con entrambe le definizioni (2/3). La definizione (b), quella del verdetto,
coincide con 6 finestre su 10 (più della metà): il sostituto vede i grandi fondi (2018, 2020, 2022) ma non i segnali brevi del
2023 e di metà 2026, che l'indicatore CryptoQuant coglie. Il verdetto vale quindi per il sostituto; sui segnali brevi
l'originale potrebbe comportarsi diversamente.

## Stato attuale: oggi è capitolazione?
**Sì con la definizione (b), no con la (a).** MVRV 1,126 il 24/11 contro una soglia del 10% più basso a 1,202: in zona il 14/11
e dal 18/11 senza interruzioni (8 giorni). Non è sotto 1,0 (il minimo del 2026 è 1,103 a fine giugno). Concorda con la banda
azzurra che il grafico dell'utente mostra a novembre 2026.

## Risultati (sostituto MVRV · 10.000 $ · prezzi al 15/11/2026)
| Regola | Dal 2018: finale · DD · trade · WR | Dal 2021: finale · DD · trade · WR |
|---|---|---|
| **W3.2 (in uso)** | **224.593 · −37,3 · 22 · 77%** | **78.474 · −21,1 · 13 · 92%** |
| Buy & hold | 47.552 · −81,2 | 22.549 · −76,6 |
| H1 chiudi lo short in capitolazione (a) | 231.752 · −32,4 · 42 · 67% | 76.834 · −21,1 · 23 · 74% |
| H1 (b) | 281.256 · −34,2 · 39 · 72% | 82.542 · −21,1 · 19 · 79% |
| H2 niente short in capitolazione (a) | 236.489 · −33,9 · 22 · 77% | 78.474 · −21,1 · 13 · 92% (nessun cambio) |
| H2 (b) | 255.081 · −30,4 · 22 · 77% | 78.474 · −21,1 · 13 · 92% (nessun cambio) |
| H3 chiudi il long in euforia (a) | 150.743 · −37,3 · 25 · 76% | 63.926 · −21,1 · 15 · 87% |
| H3 (b) | 141.453 · −37,3 · 28 · 75% | 63.574 · −21,2 · 17 · 82% |
| H4 long 1x da capitolazione a euforia/365 g (a) | 100.457 · −43,4 · 3 · 100% | 11.131 · −35,4 · 1 · 100% |
| H4 (b) | 100.703 · −47,3 · 3 + 1 aperto · 100% | 11.317 · −35,4 · 1 + 1 aperto · 100% |

H1 e H2 cambiano trade solo in tre episodi (short 10/2018, 03/2020, 08/2022): dal 2021 al massimo un trade. I "trade" in più di H1
sono riaperture di W3.2 il lunedì dopo, richiuse il giorno dopo dalla stessa regola. 2021–23 / 2024–26: H1(b) 35.212 / 23.488
(W3.2 33.477 / 23.488); nel 2024–26 nessuna regola tranne H3(b) cambia nulla.

## Trade cambiati, in parole semplici
- **Short 10/2018 (H1 b)**: W3.2 lo teneva fino ad aprile 2019 (+16,7%); la regola lo chiude il 25/11/2018 a 3.938 $ quasi sul
  minimo (+22,4%). È il guadagno più grande dello studio.
- **Short 03/2020 (H1, H2)**: W3.2 shortava proprio dopo il crollo del Covid e perdeva −17,9%. H1 lo chiude dopo un giorno (+2,3%) ma
  W3.2 lo riapre la settimana dopo e perde comunque (−13%); H2(b) non lo apre per tre domeniche ed entra solo ad aprile (−6,8%).
- **Short 08/2022 (H1)**: W3.2 +8,3% fino a gennaio 2023. H1(b) lo chiude a fine agosto 2022 a 19.575 $ (+10,7%), poi una serie di
  riaperture brevi: in totale +4.068 $. Con (a) la chiusura arriva prima, a 20.855 $, e il totale è −1.640 $.
- **Long 12/2020 e 02/2021 (H3)**: l'euforia scatta all'inizio del rally; la regola esce a +5/+10% e perde il resto (+52%, +71%):
  −15.000 $ dal 2021, −74/−83.000 $ dal 2018. Unico caso favorevole: long 2025 (H3 b, +3.000 $).
- **H4**: tre comprate sui fondi (11/2018, 03/2020, 06/2022), tutte positive (+64/+80%, +394/+450%, +11%), ma da sole rendono meno
  della metà di W3.2 con un DD peggiore; dal 2021 un solo trade (+11%), sotto anche al buy & hold.

## Lo short W3.2 aperto il 16/11/2026 a 65.286 $
- **Con (b) la regola lo avrebbe chiuso**: capitolazione alla chiusura del 18/11 → uscita all'apertura del **19/11 a 63.131 $**
  movimento +3,3% (+3,1% sulla quota, costi inclusi).
- **Tenendolo (W3.2)**: chiusura 21/11 60.216 $ (+7,8%); con i prezzi Coinbase (fuori dai dati del repo) 24/11 59.741 $ (+8,5%) e
  oggi 25/11 ~59.100 $ (+9,5%). Stop/trailing a 75.764 $, mai avvicinato. A oggi, movimento +3,3% con la regola contro +8,5% (24/11) e ~+9,5% (25/11)
  tenendolo: ~5–6 punti a favore di W3.2, su un trade ancora aperto.
- La regola come testata non vieta di riaprire: se il segnale short di W3.2 c'era ancora domenica 22/11, W3.2 avrebbe riaperto
  lunedì 23/11 (~61.200 $) e la regola avrebbe richiuso all'apertura del 24/11 (~61.200 $, circa pari). Non simulabile con il
  motore: `data/` si ferma al 21/11.
- Con (a) nulla: MVRV mai sotto 1,0. Il trade è aperto: il confronto vale solo a oggi.
- **Nessuna azione: W3.2 resta short, uscita automatica a 75.764 $; la regola non è adottata e questo confronto non indica di chiudere.**

## Criteri del PREREG (dal 2018 e dal 2021, definizioni a e b)
| | (1) finale > W3.2, DD ≤ +2 pt | (2) senza il trade più cambiato | (3) placebo p ≤ 0,05 | (4) a e b |
|---|---|---|---|---|
| H1 (a) | no (2021: −1.640 $) | no | no (p 0,23 / 0,39) | — |
| H1 (b) | **sì** (+56.663 / +4.068 $) | sì dal 2018 (247.703); no dal 2021 (un solo trade cambiato → torna a 78.474) | no nel 2021 (p 0,001 / **0,127**) | no |
| H2 (a) | no (2021 identico) | no | no (0,075 / 0,71) | — |
| H2 (b) | no (2021 identico) | no | no nel 2021 (0,034 / 0,80) | no |
| H3 (a) | no | no | no (0,90 / 0,71) | — |
| H3 (b) | no | no | no (0,94 / 0,74) | no |

Parametri vicini di H1(b) (informativi): dal 2021 tutti e quattro sotto W3.2 (quantile 5%: 71.103 · 15%: 73.498 · 730 g: 69.288 ·
1.095 g: 75.499); dal 2018 due sopra e due sotto. Il +4.068 $ dal 2021 non regge al minimo spostamento della soglia.
Controllo 2018–20 (fuori dal verdetto): H1(b) passa 1–3 (29.934 $, p 0,002) grazie ai due short 2018 e 2020, H2(b) passa 1 e 3.

## Limiti
- Sostituto, non l'indicatore originale: coincide con 4/7 finestre di capitolazione, perde i segnali brevi (2023, metà 2026).
- Pochissimi episodi: 3 fondi di ciclo dal 2018, 1 dal 2021 (più quello in corso). Ogni regola cambia 1–3 trade: nessun test può
  distinguere un vantaggio dal caso, come atteso nel PREREG.
- MVRV di CoinMetrics può essere rivisto a posteriori (ricalcolo del realized cap); non verificato su copie storiche.
- Prezzi del 22–25/11 da Coinbase (circa −0,2% rispetto a Binance), solo per lo short in corso.

## Deviazioni dal PREREG e correzioni alla prima esecuzione
1. La prima esecuzione (agente interrotto) giudicava su 2018–20 invece che "dal 2018": corretto in `up_run.py`; 2018–20 resta come
   controllo. L'esito non cambia (nessuna regola passa).
2. Criterio 2: con `round()` l'arrotondamento dava "sì" anche quando togliere il trade riportava esattamente a W3.2; ora
   tolleranza 5 $. Corregge H1(a/b) e H3(a) dal 2021, da "sì" a "no".
3. I placebo della prima `risultati.txt` non erano riproducibili dal codice salvato (es. H1(a) 2021: p 0,0 contro 0,39): tutto
   rieseguito; controllo indipendente con 300 estrazioni e altro seme: mediana 73.072 $, p 0,38.
4. Le finestre del grafico sono state lette a occhio e fissate in `up_coerenza.py` prima di calcolare le zone.
5. Il quantile di (b) esclude il giorno stesso (più prudente del minimo richiesto).
6. Revisione critica (agente separato) eseguita il 25/11: nessun errore bloccante; trade (short 2018, 2022, 16/11/2026) e
   placebo ricalcolati in modo indipendente (H1(b) dal 2021: p 0,11 con altro seme). Il p è calcolato come quota semplice; con
   (k+1)/(N+1) il p dal 2018 è circa 0,003: il verdetto non cambia.

## Lezione proposta per RESEARCH.md
**Lezione 125**: indicatore UTXO P/L Count Ratio (CryptoQuant) come supporto a W3.2, testato con il sostituto MVRV CoinMetrics
(research/utxo_pl, PREREG bdada1a). Il sostituto coincide con 6/10 finestre del grafico (perde i segnali brevi 2023 e metà 2026);
oggi (24/11/2026) è capitolazione con la soglia del 10% a 4 anni (MVRV 1,13 contro 1,20), non sotto 1,0. Nessuna regola passa i
criteri: chiudere lo short in capitolazione fa +4.068 $ dal 2021 (+56.663 dal 2018) ma cambia un solo trade, placebo p 0,13 e i
quattro vicini sono sotto W3.2; non aprire short in capitolazione non cambia nulla dal 2021; chiudere il long in euforia costa
−15.000 $ dal 2021 perché l'euforia arriva all'inizio dei rally. Lo short del 16/11 sarebbe stato chiuso il 19/11 a 63.131 $
(movimento +3,3%) contro +8,5% tenendolo al 24/11. Con 1–3 fondi di ciclo per campione un indicatore di ciclo on-chain non è verificabile
come regola su W3.2: al massimo è contesto da leggere, non un'uscita. Un miglioramento del finale in entrambi i periodi non basta se dal 2021 dipende da un solo episodio e non regge a soglie vicine; i confronti sui trade aperti vanno fatti movimento contro movimento e senza indicazioni sulla posizione.
