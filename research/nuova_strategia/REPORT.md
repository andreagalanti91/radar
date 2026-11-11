# Report · Nuova strategia settimanale/mensile su BTC con volumi e supporti/resistenze (11/11/2026)

**Esito: la strategia NON funziona fuori campione. Non va adottata né messa nel tool.**
Scelta sul 2014–2020 e provata una sola volta sul 2021 → oggi, trasforma 10.000 $ in 13.234 $ con drawdown −56%;
tenere BTC nello stesso periodo dà 25.159 $; W2 + MACD dà 118.628 $ (103.012 $ "come dal vivo"), drawdown −22,7%.

## Cosa ho costruito
Dati: BTC giornaliero dal 2011 con volume (Bitstamp → Binance → dati del tool), candele settimanali e mensili. Solo long in
spot a 1x, decisione alla chiusura e ingresso all'apertura successiva, stop controllati ogni giorno, costi 0,2% per lato,
tetto di rischio 25% del capitale allo stop iniziale. Quattro mattoni:
- **Struttura (supporti/resistenze)**: si compra alla chiusura sopra l'ultimo massimo swing confermato, si esce sotto l'ultimo minimo swing.
- **Canale**: sopra il massimo di 20 settimane si compra, sotto il minimo di 10 si esce.
- **VWAP**: prezzo sopra il prezzo medio pesato per i volumi a 26 settimane (in salita).
- **Bilancio dei volumi**: volume delle settimane in rialzo / in ribasso su 13 settimane (> 1 accumulo, < 0,8 distribuzione).
Otto varianti preregistrate (PREREG.md), più un trailing a k ATR settimanali aggiunto in fase di scelta perché senza protezione
i drawdown 2014–20 erano −57/−77%.

## Scelta (solo 2014–2020)
Vince **N6 "VWAP 26 settimane + bilancio dei volumi" con trailing 4 ATR**: 10k → 680.807 $, drawdown −39,5%, MAR 2,09,
10 trade (buy & hold: 383.145 $, drawdown −83%). Qui il bilancio dei volumi aiutava a ogni livello di trailing.

## Giudizio (2021-01-01 → 10/11/2026, 10.000 $)
| Strategia | Finale | Rendimento | Max DD | Trade | Vinti | 2021–23 | 2024→oggi |
|---|---|---|---|---|---|---|---|
| **N6 scelta** (VWAP + volumi, trailing 4 ATR) | **13.234 $** | +31,6% | **−56,2%** | 17 | 35% | −14,1% | +46,6% |
| N1 struttura S/R | 7.726 $ | −23,1% | −61,1% | 18 | 22% | +5,3% | −35,9% |
| N2 struttura + volumi | 9.898 $ | −1,5% | −59,6% | 17 | 24% | +41,0% | −38,7% |
| N3/N4 canale 20/10 (± volumi) | 18.029 $ | +79,4% | −38,9% | 17 | 29% | +56,0% | +3,1% |
| N5 VWAP 26 settimane | 13.846 $ | +37,6% | −56,2% | 19 | 26% | +9,6% | +20,1% |
| N7 voto dei tre stati | 16.951 $ | +68,7% | −46,1% | 22 | 23% | +48,7% | +1,7% |
| N8 mensile (VWAP 10 mesi + volumi) | 21.250 $ | +111,4% | −45,2% | 11 | 45% | +37,7% | +41,7% |
| Buy & hold | 25.159 $ | +151,6% | −76,6% | – | – | +44,2% | +67,0% |
| W2 + MACD (in uso) | 118.628 $ | +1.086% | −22,7% | 14 | 93% | +406% | +134% |

Per anno (N6): 2021 −20,7% · 2022 0% · 2023 +8,3% · 2024 +71,6% · 2025 −11,9% · 2026 −4,1%. In posizione il 39% dei giorni.

## Controlli
- **Parametri vicini (81 combinazioni)**: mediana 17.450 $, minimo 8.406 $, massimo 33.112 $; drawdown mediano −52%; solo il 20%
  batte il buy & hold. Non è sfortuna dei parametri: è la famiglia che non regge.
- **Giorno di chiusura della settimana**: da 13.234 $ (domenica) a 20.312 $ (venerdì), drawdown sempre −53/−57%.
- **Senza il trade migliore** (+75%, nov 2023 → mag 2024): 7.559 $, cioè in perdita.
- **Esplorativo, tutte le 8 varianti × 5 trailing (40 combinazioni)**: nessuna batte il buy & hold dal 2021; drawdown migliore −30%.
  La classifica 2014–20 non predice quella 2021→oggi (correlazione di rango 0,16).
- **2018**: −27,3% (drawdown −37%).

## Perché non funziona
1. Dal 2021 BTC ha fatto falsi breakout e discese rapide: comprare la rottura di una resistenza o il ritorno sopra il VWAP
   arriva tardi, e l'uscita (supporto, VWAP, trailing largo) restituisce gran parte del guadagno: 35% di trade vinti, molti
   piccoli stop consecutivi (5 nel solo 2021-10/12, 5 nel 2023).
2. Il volume spot non anticipa la direzione: il bilancio dei volumi è quasi sempre > 1 quando il prezzo rompe al rialzo (non
   filtra) e scende sotto 0,8 quando il calo è già avvenuto. Conferma le lezioni 68 e 75–77 e il test T6 della revisione.
3. Quello che distingue W2 non è nel prezzo né nel volume spot: è il flusso dei perpetual (chi compra e chi vende in leva) più
   un'uscita più rapida (EMA 21, trailing 2,5 ATR, distribuzione). Senza quel dato, le regole "classiche" rendono meno del buy & hold.

## Cosa tenere
- Come CONTESTO in dashboard (non come segnale): VWAP a 26 settimane e bilancio dei volumi a 13 settimane, accanto a media a
  200 giorni, Mayer e stato del MACD già proposti dalla revisione.
- La strategia operativa resta W2 + MACD, con le correzioni proposte nella revisione (flusso disponibile dal vivo, tetto di
  rischio sui long, alert affidabili) — da applicare solo su ordine dell'utente.

## Dove potrei sbagliarmi
- Il motore è nuovo (scritto oggi) e non ha un secondo controllo indipendente: un errore potrebbe peggiorare o migliorare i numeri;
  i trade di N6 sono in trades_N6.csv per la verifica a mano.
- Ho scelto su un periodo (2014–20) dominato dal rialzo parabolico del 2017: il trailing largo (4 ATR) era ottimo lì e pessimo dopo.
  Una scelta su un periodo diverso avrebbe dato un candidato diverso, ma la griglia esplorativa dice che nessuno dei 40 batte il buy & hold.
- Solo long: una versione long/short non è stata provata (gli short dedicati hanno già fallito, lezione 80).

File: PREREG.md, ns.py (mattoni e motore), run1–4.py, scelta_*.csv, giudizio_2021.csv, vicini.csv, giorni.csv,
esplorativo_griglia.csv, trades_N6.csv, equity_N6.csv.
