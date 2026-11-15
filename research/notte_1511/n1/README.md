# N1 · Perché W3 decide di domenica? (15/11/2026)

**Verdetto.** La domenica non è stata scelta perché rende di più: è la convenzione delle candele settimanali. Dal 2021 però
è il migliore dei 7 giorni possibili (78,5k contro una mediana di 62,7k, +25%), mentre nel 2018–20 è solo quarta. Il rischio
di ancoraggio c'è e va messo nelle attese: il risultato che ci si può aspettare davvero sta intorno alla mediana (circa 60k,
MAR ~1,3–1,5), non a 78k. Il giorno non decide se la strategia funziona: tutti e 7 i giorni battono nettamente il buy & hold.
Proposta: nessuna modifica a W3 (cambiare giorno vorrebbe dire scegliere di nuovo sugli stessi dati); attese ridimensionate.

## Perché proprio la domenica (in parole semplici)
Binance, TradingView e quasi tutte le piattaforme disegnano la candela settimanale dal lunedì 00:00 alla domenica 23:59 UTC
(settimana ISO); anche pandas chiama "W" la settimana che chiude la domenica (`W-SUN`). W2 è nata leggendo i grafici
settimanali come li vede l'utente, quindi decide quando la candela chiude: domenica a mezzanotte UTC (01:00 in Italia),
con esecuzione all'apertura del lunedì. Per il mercato BTC, aperto 7 giorni su 7, la domenica non ha nulla di speciale:
qualunque giorno può chiudere una "settimana".

## Metodo
Copia fedele di `radar/weekly.py` con il solo giorno di ancoraggio come parametro (`run.py`): candele `W-LUN … W-DOM`,
decisione alla chiusura UTC di quel giorno, esecuzione all'apertura del giorno dopo; flusso = media dei 3 giorni di pf14z
precedenti la decisione (stesso ritardo di un giorno di oggi), funding a 7 giorni letto al giorno di decisione, trailing e
funding giornalieri invariati. 10.000 $ a 1x, costi inclusi, dal 01/01/2021 (dati fino al 14/11/2026). Controllo preliminare
superato: la domenica riproduce esattamente `radar.weekly.simulate` (78.474 $, DD −21,1%, 13 trade, equity identica).
Soglie in `PREREG.md`, scritte prima.

## Risultati (MAR = CAGR / |DD giornaliero|; IS, OOS e 2018–20 ripartono da 10.000 $)
| Ancoraggio | Finale 2021→ | DD | MAR | Trade | WR | IS 2021–23 | OOS 2024→ | 2018–20 (DD) | Senza trade migliore |
|---|---|---|---|---|---|---|---|---|---|
| lunedì | 62.728 | −27,5% | 1,34 | 15 | 67% | 28.235 | 21.305 | 27.423 (−38,8%) | 39.180 |
| martedì | 48.763 | −25,2% | 1,23 | 13 | 77% | 20.246 | 22.703 | 29.413 (−35,0%) | 34.043 |
| mercoledì | 38.564 | −28,9% | 0,90 | 15 | 73% | 17.997 | 21.189 | 32.682 (−39,1%) | 25.584 |
| giovedì | 40.948 | −39,4% | 0,69 | 17 | 65% | 20.879 | 18.820 | 14.155 (−55,9%) | 26.728 |
| venerdì | 68.218 | −25,5% | 1,52 | 17 | 76% | 32.247 | 22.835 | 15.071 (−49,0%) | 45.860 |
| sabato | 70.104 | −25,8% | 1,52 | 15 | 80% | 32.067 | 21.862 | 20.210 (−35,3%) | 47.836 |
| **domenica (W3)** | **78.474** | **−21,1%** | **1,99** | 13 | 92% | 33.477 | 23.488 | 25.142 (−37,3%) | 51.561 |
| Media dei 7 ancoraggi (1/7 ciascuno) | 58.257 | −23,5% | 1,49 | 105 | 75% | 26.450 | 21.743 | 23.442 (−41,3%) | – |
| Buy & hold | 21.783 | −76,6% | 0,19 | 1 | – | 14.358 | 14.462 | 21.531 (−81,2%) | – |

Sintesi sui 7 giorni (2021→): finale medio 58,3k, mediana 62,7k, min 38,6k, max 78,5k, dev. st. 15,5k (CV 27%);
DD medio −27,6% (da −21,1% a −39,4%); MAR medio 1,31. Domenica: 1ª su 7 (percentile 100) per finale, DD, MAR, IS, OOS e anche
senza il trade migliore; nel 2018–20 4ª su 7 (percentile 50). Rapporto domenica/mediana 1,25; minimo/mediana 0,61.
Classifica dei giorni: stabile fra IS e OOS (Spearman 0,71) ma rovesciata fra 2021→ e 2018–20 (−0,32). La dispersione viene
quasi tutta dal 2021–23 (CV 25%); nel 2024→ i giorni sono vicini (18,8–23,5k, CV 7%). Per anno la domenica non è mai prima
né ultima (2ª–4ª ogni anno): vince per regolarità, non per un singolo anno (`anni_giorni.csv`). I trade dei 7 giorni sono in
gran parte gli stessi spostati di qualche giorno (10–12 su 13–17 entro 6 giorni da un ingresso della domenica).

## Lettura con le soglie preregistrate
- "Ancoraggio irrilevante": NO (minimo = 61% della mediana, soglia 70%; domenica 1ª).
- "Domenica fortunata": SÌ dal 2021, al limite (1ª e +25,1% sulla mediana, soglia +25%); NON confermata nel 2018–20 (4ª).
  Le regole di W2 e le modifiche di W3 sono state sviluppate e scelte guardando la domenica: parte del suo primato è
  selezione, non un vantaggio del giorno.
- Media dei 7 ancoraggi: NON preferibile secondo la soglia (MAR 1,49 = 75% della domenica, DD −23,5% contro −21,1%). È però la
  stima più onesta di cosa vale W3 senza la fortuna del calendario, e costa 7 decisioni a settimana.

## È un rischio?
Sì, ma di misura, non di segno: dal vivo W3 si comporterà più probabilmente come un giorno "medio" (CAGR ~31–39%, DD fino a
−25/−30%) che come la domenica del backtest. Non è un motivo per cambiare giorno: nessun altro giorno è migliore in modo
coerente fra 2021→ e 2018–20, e la domenica coincide con la candela che l'utente vede su TradingView.

## Proposta (nessuna modifica a W3)
1. Tenere la domenica. 2. Nelle attese e in dashboard citare accanto al backtest la mediana dei 7 ancoraggi (~63k, MAR ~1,3)
e il peggiore (38,6k, DD −39%). 3. La media dei 7 ancoraggi resta un'opzione di riduzione del rischio di calendario solo se
l'utente accetta l'operatività quotidiana.

Testo proposto per RESEARCH.md:
> **Lezione 94** (15/11/2026, N1): W3 decide di domenica per convenzione (candela settimanale ISO lun–dom UTC di Binance e
> TradingView, `W-SUN` in pandas), non per ottimizzazione. Ancorata agli altri 6 giorni con regole identiche fa 38,6–70,1k dal
> 2021 (mediana 62,7k, MAR 0,69–1,52) contro 78,5k (MAR 1,99) della domenica, che è 1ª su 7 dal 2021 ma 4ª nel 2018–20: parte
> del primato è selezione. Tutti i giorni battono il buy & hold (21,8k, DD −77%). La media dei 7 ancoraggi fa 58,3k, DD −23,5%,
> MAR 1,49: non migliora la domenica. Attese realistiche di W3 = mediana dei giorni, non il backtest della domenica.
> File: research/notte_1511/n1/.

File: `PREREG.md`, `run.py`, `risultati.txt`, `giorni.csv`, `anni_giorni.csv`, `trade_giorni.csv`, `equity_giorni.csv`,
`equity_media7.csv`.
