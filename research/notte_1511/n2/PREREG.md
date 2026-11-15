# N2 · Swing BTC 2–3 giorni (notte 15/11/2026) · PREREGISTRAZIONE
Scritta prima di eseguire qualsiasi backtest. Nessuna regola, soglia o criterio verrà cambiato dopo i risultati.

## Cosa è già stato bocciato (non si ripete, si costruisce sopra)
- Intraday 1h/4h su BTC/ETH/SOL (lezioni 78, 82): su 1h i costi mangiano tutto; inversione (RSI/Bollinger/funding contrarian)
  negativa ovunque; su 4h sopravvive solo il momentum, sottile (PF 1,10–1,23). OI in aumento "aiuta un po'" il momentum.
- S/R, volume profile, confluenze al tocco (68, 75–77): nessun vantaggio su barre giornaliere. Qui niente S/R.
- Divergenza perp in vendita / spot che assorbe a 7 giorni (89): segno positivo ma 2/8 varianti, vicini incoerenti.
  Qui il flusso si usa su 1 giorno con tenuta 2–3 giorni (orizzonte diverso), non si ripete lo stato A.
- Squilibrio delle liquidazioni (81): vale 12–24 ore ed è in gran parte momentum di breve → motiva la famiglia (a).
- H2/v2 (micro-breakout 4h + delta taker, tenuta fino a 14 g, TP 1R): spento; qui niente DCA, niente TP, solo tempo + stop.
- Donchian 55 + RSI>70 come setup (iterazione 5): gate NO. Qui Donchian 10/20 con tenuta fissa breve.

## Dati e convenzioni
- Barre giornaliere UTC. Prezzi di esecuzione e ATR: perp Binance BTCUSDT (data/perp.csv). Taker spot: data/spot.csv.
  Taker perp: data/perp.csv. OI: data/metrics.csv (dal 2021-12: la regola C2 parte di fatto dal 2022-03). Funding: data/funding.csv
  (somma giornaliera).
- Disponibilità dal vivo: decisione alla chiusura del giorno t; prezzo, taker spot e funding del giorno t sono noti; taker perp
  e OI (archivio Binance con ~1 giorno di ritardo) si usano al giorno t−1. Regime W3 = ultima candela settimanale chiusa (≤ t):
  long se chiusura > SMA40w ed EMA20w in salita; short se chiusura < SMA40w, SMA40w in calo su 4 settimane ed EMA20w in calo;
  altrimenti neutro (stesse definizioni di radar/weekly.py).
- Esecuzione: ingresso all'apertura di t+1 (barra successiva). Uscita a tempo all'apertura di t+1+H (H = 2 o 3 giorni),
  oppure stop a 1,5 × ATR14 giornaliero (del giorno t) dal prezzo d'ingresso, controllato su massimi/minimi da t+1 in poi;
  se l'apertura è già oltre lo stop si esce all'apertura.
- Costi: 0,08% per lato (perp) + slippage 0,05% per lato + funding reale per ogni giorno di tenuta (il long paga se positivo).
- 10.000 $ a 1x, una posizione alla volta per regola e lato, nessun reinvestimento parziale (tutto il capitale a ogni trade).
  Long e short sono due conti separati. Dal 01/01/2021 alla fine dei dati.

## Le 8 regole (long e short speculari; parametro principale in grassetto, vicini fra parentesi)
**(a) Momentum / breakout di breve**
- A1 · chiusura > massimo dei **10** (7, 15) giorni precedenti E delta taker spot del giorno t > 0 E delta taker perp di t−1 > 0.
  Short: chiusura < minimo dei 10 giorni precedenti, deltas < 0.
- A2 · chiusura > massimo dei **20** (15, 30) giorni precedenti, solo nel verso del regime W3 (long in regime long, short in
  regime short), senza flussi.
**(b) Ritorno alla media**
- B1 · RSI(2) < **10** → long, > **90** → short (5/95, 15/85), SOLO nel verso del regime W3 (long in regime long, short in short).
- B2 · stesso RSI(2), SOLO fuori dal verso del regime (regime neutro o contrario): il "contro regime".
- B3 · movimento di 3 giorni (chiusura t − chiusura t−3) oltre **2,5** ATR14 → posizione opposta (k 2,0/3,0; finestra 2/4 giorni),
  qualunque regime.
**(c) Flussi**
- C1 · funding: somma 3 giorni, z-score 180 g. z < −**1,5** → long (short pagati), z > +1,5 → short (1,0 / 2,0).
- C2 · OI + prezzo: variazione OI di 1 giorno (t−1) con z90 > **1,5** (1,0 / 2,0) e rendimento del giorno t e delta taker spot di t
  entrambi > 0 → long; entrambi < 0 → short (nuova leva che segue il movimento).
- C3 · aggressione spot: quota taker spot del giorno t con z90 > **2,0** (1,5 / 2,5) e delta taker perp di t−1 > 0 → long;
  z < −2,0 e delta perp < 0 → short.

Vicini comuni a tutte: stop 1,0 e 2,0 ATR. H = 2 e H = 3 sono entrambe primarie.
Configurazioni giudicate: 8 regole × 2 lati × 2 tenute = **32**.

## Metriche
Capitale finale, rendimento, max DD giornaliero (mark-to-market), trade, trade/anno, % vincenti, PF, MAR; per metà IS 2021–23 e
OOS 2024→: n, PF, rendimento composto; senza i 5 trade migliori; placebo; vicini; correlazione dei rendimenti giornalieri con W3;
combinazione con W3 (la regola opera solo quando W3 è flat, chiusura forzata se W3 entra). Riferimenti: W3 (radar/weekly.py
simulate, sola lettura) e buy & hold dal 01/01/2021.

## Placebo
Per ogni configurazione: 5.000 serie di ingressi a date casuali (giorni dal 2021 ai dati disponibili per la regola), stesso lato,
stesso numero di trade, stessa tenuta e stesso stop, stessi costi. Statistica: rendimento netto medio per trade.
p = (#placebo ≥ osservato + 1)/(5.001). Correzione di Bonferroni per 32 prove: p_corr = min(1, 32·p).

## Criterio di accettazione (tutti obbligatori)
1. OOS 2024→ con rendimento composto > 0;
2. PF > 1,2 sia in IS 2021–23 sia in OOS 2024→;
3. placebo p_corr < 0,05;
4. vicini stabili: ≥ 75% dei vicini (parametro ±, stop 1,0/2,0, stessa tenuta) con PF > 1 in entrambe le metà e nessun vicino
   con rendimento totale di segno opposto;
5. potenza minima: ≥ 20 trade in ciascuna metà (altrimenti "senza potenza", non accettabile).
Informativi (non decidono): senza top 5, correlazione con W3, beneficio della combinazione con W3 (MAR combinato > MAR W3).
Una configurazione accettata si annuncia come "candidata su carta", non come regola: il 2024→ è dati già visti in altri studi.
