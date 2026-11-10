# Analisi tecnica settimanale / mensile su BTC · preregistrazione

Scritta il 10/11/2026 PRIMA di calcolare qualunque risultato delle regole (fatto finora: lettura di RESEARCH.md e di
`radar/weekly.py`, verifica che il motore riproduca W2 — 14 trade, 10.000 → 118.628 $, DD −22,7% — e che l'API pubblica
Bitstamp dia lo storico 2011–2013).

Richiesta dell'utente: "analisi tecnica: studiare una strategia a livello settimanale / mensile se può essere utile. Indicatori
come EMA, SMA, supporti/resistenze, volume, liquidazioni, order book. Correlazione fra EMA / SMA 200 giorni e MACD."

## Cosa NON si ritesta (già escluso, nessun motivo nuovo)
- Supporti/resistenze e volume profile come segnale (lezioni 68, 75–77), liquidazioni stimate (72, 81), incroci MACD da soli
  long/short (63–66, 79). Qui il MACD entra solo abbinato alla media 200 giorni o a un filtro mensile (combinazione mai provata
  in forma di regime "entrambi veri"), il volume solo come conferma settimanale degli ingressi W2 (mai provato così).
- Order book: lo storico (`data/orderbook.csv`) parte dal 07/11/2026 → NON è backtestabile. Solo nota di monitoraggio.

## Dati
- Prezzi giornalieri BTC: Bitstamp 2011-09 → 2017-08-16 (2011–13 scaricati dall'API pubblica), Binance spot dal 2017-08-17,
  repo dal 2019-09. Flusso perp `pf14z` reale dal 2020; nel 2018–20 proxy CVD spot (come in research/short_w2), funding 0 prima del 2020.
- Indicatori giornalieri (SMA/EMA 200g, SMA 50g, Mayer = chiusura / SMA200g) letti alla chiusura della domenica; MACD sulle
  chiusure settimanali W-SUN; indicatori mensili sull'ultimo mese SOLARE CHIUSO (mai il mese in corso).
- Finestre: principale 01/01/2021 → oggi (10.000 $, 1x); split 2021–23 / 2024→oggi; pre-2021 = 01/01/2014 → 31/12/2020 per le
  regole autonome (T1–T4), 01/01/2018 → 31/12/2020 per le regole sopra W2 (T5–T8: prima manca il flusso).

## Parte 1 · descrittiva (nessuna regola, nessuna scelta di parametri)
Su settimane 2012→oggi, e separatamente pre-2021 / dal 2021:
1. Accordo fra "prezzo sopra/sotto MA200g" (SMA ed EMA) e MACD settimanale (12/26/9 e 8/21/5) sopra/sotto segnale e sopra/sotto
   zero: % settimane concordi e correlazione phi; correlazione fra distanza dalla MA200g e MACD/prezzo.
2. Anticipo/ritardo ai massimi e minimi: zigzag sulle chiusure settimanali (massimo = seguito da −30%; minimo = seguito da
   +50%). Per ogni svolta: settimane fino a MACD sotto/sopra segnale, MACD sotto/sopra zero, chiusura sotto/sopra SMA200g,
   pendenza SMA200g (4 sett.) che cambia segno, death/golden cross 50/200g; mediana e prezzo perso/recuperato a quel punto.
3. Rendimenti futuri a 4/12/26 settimane nei 4 stati (MA200g × MACD-segnale; MA200g × MACD-zero), con n, media, mediana,
   % positivi; significatività = differenza dalla media incondizionata con permutazione a slittamento circolare dello stato
   (2.000 prove, conserva autocorrelazione e sovrapposizione).
4. Pendenza SMA200g (su/giù a 4 settimane) come variabile di regime; fasce del Mayer (<0,8 · 0,8–1 · 1–1,5 · 1,5–2,4 · >2,4);
   prezzo sotto la media a 200 SETTIMANE; golden/death cross 50/200g (eventi giornalieri, rendimenti a 28/84/182 giorni e
   rendimento fino all'incrocio opposto).

## Parte 2 · regole (8 in tutto, parametri "da manuale" fissati qui, nessuna ottimizzazione)
Decisione alla chiusura della domenica, esecuzione all'apertura del lunedì (T4 puro: fine mese → primo giorno del mese).
Costi come `radar/weekly.py`: long spot 0,1%/lato, short perp 0,05%/lato + funding reale, slippage 0,1%. MACD = 12/26/9
(quello che guarda l'utente) salvo dove indicato.

Regole autonome (nessuno stop: lo stato della regola è l'uscita):
- **T1** long se chiusura > SMA200g E MACD > segnale; flat appena una delle due cade.
- **T2** come T1 con EMA200g.
- **T3** long se SMA200g in salita (oggi > 28 giorni fa) E MACD > 0; flat appena una cade.
- **T4** Faber: chiusura mensile > SMA 10 mesi → long il mese dopo. **T4m** = stato Faber E MACD settimanale > segnale.
- Versione long/short di T1–T4 (secondaria): short perp 1x quando valgono entrambe le condizioni speculari, flat altrimenti.

Regole sopra W2 (motore W2 identico, cambia solo quanto scritto):
- **T5** uscita Mayer: in long, se Mayer > 2,4 alla chiusura della domenica → uscita lunedì; nuovi long bloccati finché
  Mayer non torna < 2,0.
- **T6** conferma di volume: un long W2 entra solo se il volume spot della settimana del segnale è > media delle 20 settimane
  precedenti (altrimenti si rivaluta la settimana dopo).
- **T7** filtro mensile sui nuovi long W2: **T7a** istogramma MACD mensile (12/26/9) > 0; **T7b** RSI mensile (14) > 50.
- **T8** (mia scelta) filtro 200g sui nuovi long W2: chiusura > SMA200g E SMA200g in salita su 28 giorni.

Conteggio onesto delle prove: 10 configurazioni long (T1, T2, T3, T4, T4m, T5, T6, T7a, T7b, T8) + 4 long/short = 14.
Con 14 prove, una che "vince" per caso è attesa: si giudica la famiglia, non il massimo.

## Parametri vicini (robustezza, non selezione)
MA 150/200/250 giorni; MACD 12/26/9 ↔ 8/21/5; pendenza 14/28/56 giorni; Faber 8/10/12 mesi; Mayer 2,2/2,4/2,6 e rientro
1,8/2,0; volume 10/20/30 settimane e soglia 1,0/1,2; RSI mensile 45/50/55; MACD mensile 12/26/9 ↔ 8/21/5.
Per T5 l'unico parametro senza valore da manuale univoco (soglia Mayer): si guarda quale soglia va meglio nel pre-2021 e la si
giudica solo dal 2021.

## Controlli
Senza il trade migliore; placebo (stessa serie di stato/filtro slittata circolarmente di ≥ 26 settimane, 500 prove: quota di
prove con MAR ≥ regola); numero di trade W2 CAMBIATI (entrati/saltati/usciti in date diverse) per T5–T8; tabella diagnostica
dei trade W2 (2018→oggi) con lo stato di ogni indicatore al segnale — in particolare il long 24/08→09/11/2026 (−4%).

## Soglie di verdetto (fissate ora)
Regola sopra W2 (T5–T8) → **adottare** solo se: MAR ≥ W2 in ENTRAMBI 2021–23 e 2024→oggi, non peggiore nel 2018–20,
almeno 3 trade W2 cambiati dal 2021, regge senza il trade migliore, mediana dei vicini ≥ W2, placebo p < 0,10.
**Su carta** se migliora 2 periodi su 3 con ≥ 3 trade cambiati. Con < 3 trade cambiati: "senza potenza" = respinta
(un miglioramento che cambia 1 trade non è un miglioramento, lezione 3). In tutti gli altri casi **respinta**.

Regola autonoma (T1–T4) → **affiancare** solo se MAR > W2 in entrambi i sottoperiodi dal 2021 e MAR > buy & hold nel
pre-2021 e i vicini lo confermano. **Su carta** se MAR > buy & hold in tutti e 3 i periodi (pre-2021, 2021–23, 2024→) con
DD dal 2021 non peggiore di −40% e placebo p < 0,10. Altrimenti **respinta** come regola; i fatti descrittivi robusti
(stesso segno pre-2021 e dal 2021) possono andare in dashboard come contesto.
