# Prompt per la sessione Claude Code del repo `radar`

Incolla tutto il testo qui sotto nella sessione di radar e allega i file di questa cartella (oppure lo zip `radar-v1.zip`).

---

Voglio aggiungere alla dashboard di Radar uno **switch fra due strategie: W3.2 e la "v1 · voto di 17 indicatori"**, più una
terza posizione **"Confronto"** per confrontarle in modo approfondito. W3.2 resta la strategia in uso e **non cambia**: la v1
si mostra solo per confronto, senza avvisi e senza ordini.

## Cos'è la v1

L'ho sviluppata e verificata in un altro repo (`teststrategy`). Lo studio è in `ANALISI_BTC.md` e `CONFRONTO_W32.md`. In breve:

- ogni giorno, alla chiusura UTC, **17 indicatori che seguono il trend** votano +1 (long), −1 (short) o 0 (neutro): 7 di trend
  (prezzo vs SMA 200, SMA 50 vs 200, EMA 20 vs 50, prezzo vs SMA 40 settimane, Supertrend, Ichimoku, ADX), 5 di momentum
  (MACD giornaliero e settimanale, RSI giornaliero e settimanale vs 50, momentum a 90 giorni), 4 di rottura (Donchian 20 e
  55 giorni, Donchian 20 settimane, bande di Bollinger), 1 di volume (OBV vs la sua media a 100 giorni);
- **voto** = media dei 17, da −1 a +1;
- **long** se voto ≥ +0,50; **short** se voto ≤ −0,90; si esce dal long sotto +0,25 e dallo short sopra −0,25; fra le soglie
  si mantiene la posizione;
- esecuzione alla chiusura giornaliera, esposizione 1x (long in spot, short sul perp con il funding reale), costi 0,10% per lato.

Dal 2018: 10.000 $ → 184.406 $ (+38,8% annuo, drawdown −49,4%, 30 operazioni, 47% in guadagno). W3.2 nello stesso periodo:
209.002 $ (+40,8%, −37,3%). Le soglie sono state scelte sul 2018–2021; il 2022–2026 è l'unico periodo mai visto.

## Cosa ti allego

| File | A cosa serve |
|---|---|
| `v1.py` | Modulo autonomo (pandas/numpy): indicatori, voto, decisione, backtest (`simulate`), stato di oggi (`evaluate`) e confronto con W3.2 (`confronto`) |
| `test_v1.py` | 5 test: riproduce lo studio, nessun dato futuro, soglie, stato di oggi, confronto |
| `btc_giornaliero.csv` | Giornaliero BTC dal 2014 (Bitstamp fino al 17/08/2017, poi Binance spot) con volume e funding. Dal 01/09/2019 coincide con `data/spot.csv` di radar (prezzi identici) |
| `w32_equity_2018_2026.csv`, `w32_operazioni_2018_2026.csv` | W3.2 dal 2018 come l'ho usata nel confronto: 2018–2020 con il flusso stimato, poi dati reali |
| `v1_operazioni_2018_2026.csv` | Le 30 operazioni della v1 |
| `esempio_v1.json`, `esempio_confronto.json` | L'uscita di `evaluate` e di `confronto` al 22/11/2026: lo schema da mostrare |
| `riferimento_sezione.html` e le 4 anteprime `anteprima_*.png` | Come immagino le viste (computer e telefono). In radar vanno rifatte con i componenti, i colori e `lightweight-charts` della dashboard |
| `ANALISI_BTC.md`, `CONFRONTO_W32.md` | Lo studio, da cui prendere i testi |

## Lo switch

Un controllo a tre posizioni **W3.2 · v1 · Confronto**, in alto nella vista **Oggi** e ripetuto nella vista **Storico**.
Predefinito **W3.2**; la scelta si ricorda nel browser (`localStorage`, con try/catch). Il link `#confronto` apre direttamente il
confronto.

### Posizione "W3.2"
La dashboard di oggi, **identica**. Nessun cambiamento.

### Posizione "v1"
Card con l'etichetta ben visibile "**confronto, non in uso**":

1. **Stato**: LONG / SHORT / FUORI, da quanti giorni, eventuale ingresso o uscita decisi alla chiusura di oggi.
2. **Il voto**: valore di oggi e di ieri, conteggio long / short / neutri, e una barra da −1 a +1 con le quattro soglie
   (−0,90 · −0,25 · +0,25 · +0,50) e il punto attuale.
3. **Distanza dalle soglie**: "per il long servono N indicatori che cambiano verso; per lo short M" (campo `distanze`).
4. **I 17 indicatori** divisi per famiglia: nome, voto (LONG / SHORT / 0), cosa significa il voto long, da quando ha quel voto.
5. **Voto nel tempo**: grafico dal 2018 con le soglie.
6. **Metriche** dal 2018 e dal 2021, e **tabella delle operazioni** (verso, date, prezzi, voto all'ingresso, risultato, motivo
   dell'uscita).

### Posizione "Confronto"
Tutto quello che c'è in `esempio_confronto.json`:

1. **Metriche affiancate** di W3.2, v1, 50% W3.2 + 50% v1 e BTC comprato e tenuto, con selettore del periodo: tutto,
   2018–2021, 2022–2026, dal 2021, ultimi 12 mesi.
2. **Capitale** (scala logaritmica) e **drawdown** sovrapposti, più una striscia con la posizione di ognuna nel tempo.
3. **Anno per anno**.
4. **Quando sono d'accordo**: giorni in cui sono entrambe long, entrambe short, entrambe fuori, solo una in posizione, versi
   opposti; per ogni situazione il rendimento di BTC, di W3.2 e della v1 in quei giorni. È la tabella che spiega da dove
   viene la differenza: per esempio, nei giorni in cui è in posizione solo W3.2, W3.2 ha reso +52% annuo; nei giorni in cui è
   in posizione solo la v1, la v1 ha reso +11%.
5. **Operazioni incrociate**: per ogni operazione di W3.2, cosa diceva la v1 (voto, posizione all'ingresso, quota di giorni
   nello stesso verso, cosa ha fatto nel periodo); e viceversa per ogni operazione della v1.
6. **I 17 indicatori**: quanto spesso ognuno è stato d'accordo con W3.2 quando W3.2 era in posizione, e cosa avrebbe fatto da
   solo.
7. **Quanto ci si può fidare**: Sharpe, probabilità che sia sopra zero, Sharpe deflazionato a 10 e 100 tentativi, capitale
   con tutte le operazioni e senza le tre migliori (W3.2 ×20,9 → ×6,0; v1 ×18,5 → ×1,0: la v1 dipende quasi tutta da tre
   operazioni).
8. Le tre righe di `lettura` sotto il titolo.

## Come integrarla

- **Modulo**: porta `v1.py` in `radar/v1.py` con i suoi test. Non dipende da nulla di radar.
- **Dati**: usa il giornaliero che Radar ha già (`data/spot.csv`, solo giorni **chiusi**) con il funding di `data/funding.csv`.
  `data/spot.csv` parte dal 01/09/2019, ma la v1 ha bisogno di circa 300 giorni prima del 2018 per scaldare gli indicatori:
  aggiungi `btc_giornaliero.csv` come `data/btc_daily_hist.csv` e usalo solo per i giorni prima dell'inizio di
  `data/spot.csv`. Ho verificato che unendo i due file si ottengono esattamente gli stessi risultati (184.406 $, 30 operazioni).
- **W3.2 per il confronto**: dal 2021 usa la curva e le operazioni che `weekly.evaluate()` calcola già (`history.eq1`,
  `history.trades`). Per il 2018–2020, se Radar riesce a ricostruirli con `weekly.simulate` sui dati lunghi della ricerca
  (`research/p2_nuovi/data/f_long.csv.gz`), usa quelli e controlla che tornino con `w32_operazioni_2018_2026.csv`; altrimenti
  usa i due file allegati per quel periodo. Il risultato atteso dal 2018 è 209.002 $ con drawdown −37,3%. Se non torna,
  fermati e dimmelo.
- **Dove calcolare**: nel giro orario, come le altre sezioni, con `_soft` (un errore qui non deve fermare il giro né toccare
  W3.2). `evaluate` e `confronto` insieme richiedono circa un secondo; il confronto basta ricalcolarlo una volta al giorno,
  dopo la chiusura UTC.
- **Report**: chiavi nuove `v1` e `confronto_v1` nel report che alimenta la dashboard. La riga che oggi esclude dalla pagina
  i conti su carta e i candidati della ricerca (`paper`, `lab`) resta com'è: la v1 è un'eccezione voluta, perché la chiedo
  esplicitamente come confronto.
- **Telegram**: nessun messaggio per la v1. Mai.

## Vincoli

- Segui le regole del progetto: skill gengar, file `stato/STATO-switch-v1.md`, test, suite verde, render a 400 e 1280 px
  con dati reali, deploy e verifica sul sito pubblicato.
- **W3.2 non si tocca**: nessuna modifica a `radar/weekly.py`, ai segnali, agli stop, al capitale o agli avvisi.
- **Le regole della v1 non si ottimizzano**: stesse soglie, stessi indicatori, stessi costi. Se vedi un motivo per cambiarle,
  dimmelo prima.
- In ogni vista della v1 deve essere chiaro che è un confronto e non la strategia in uso.
- Tema chiaro e scuro, stessi componenti della dashboard; dal telefono nessuno scorrimento orizzontale della pagina (le
  tabelle scorrono nel loro riquadro; le due tabelle delle operazioni incrociate vanno una sotto l'altra).

## Come capisco che è fatto

1. `python -m pytest` verde, con i 5 test di `test_v1.py` adattati a `radar/v1.py`: riproduzione dello studio (184.406 $, 30
   operazioni, 7 short, +38,8% annuo, −49,4%), nessun dato futuro (gli indicatori calcolati su dati tagliati a una data sono
   identici a quelli calcolati su tutto), soglie e isteresi, stato del 22/11/2026 (fuori, voto −0,76, 2 long e 15 short,
   11 indicatori per il long e 2 per lo short), confronto (W3.2 209.002 $).
2. Un test che riproduce gli stessi risultati usando `data/spot.csv` + `data/btc_daily_hist.csv` invece del file allegato.
3. Un test che dimostra che un errore nella v1 non ferma il giro e non cambia l'uscita di W3.2.
4. Screenshot a 400 e 1280 px, tema chiaro e scuro, con dati reali, delle tre posizioni dello switch.
5. Lo switch è sul sito pubblicato, si aggiorna a ogni giro, e il link `#confronto` funziona.
6. Un riepilogo finale: da dove prende W3.2 2018–2020, cosa hai cambiato rispetto a `v1.py`, dove hai messo lo switch.

Nota: la prima operazione della v1 (01/01/2018) è una posizione long già aperta a fine 2017; per questo il suo voto
all'ingresso (+0,41) è sotto la soglia. È corretto così: il backtest parte il 01/01/2018 con la posizione che la regola aveva.
