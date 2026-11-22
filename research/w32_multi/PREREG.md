# w32_multi · W3.2 su ETH, SOL e indici azionari — PREREGISTRAZIONE (22/11/2026)

Scritto e committato da solo PRIMA di scaricare i dati nuovi e di calcolare qualsiasi rendimento. Test di TRASFERIBILITÀ:
nessun parametro si adatta all'asset, si usano gli stessi parametri di BTC (radar/weekly.py, W3.2).

## Regole (nessuna ottimizzazione)
- **W3.2 completa** (ETH, SOL): `radar.weekly.simulate` così com'è (regime SMA40w/EMA20w, ingresso EMA21w + flusso perp pf14z
  medio 3 g ritardato > 0 / < 0, filtro F1 MACD(8,21,5) nei trend ≥ 16 sett., stop e trailing 2,5 ATRw a cricchetto, uscita
  EMA21 settimanale e distribuzione con funding, rischio allo stop R_LONG = R_SHORT = 0,25; W-SUN; costi di weekly.py: spot 0,1%,
  perp 0,05%, slippage 0,1%, funding reale). Dati: Binance spot (data-api.binance.vision) e perp USDT-M 1d con taker buy e funding
  (data.binance.vision), già in research/top10_w3/data (fino al 10/11/2026); pf14z costruito come in top10_w3/run.py. Il flusso
  serve 200 giorni di storia perp: la versione completa parte dal primo giorno disponibile (non prima del 2021 nel test principale).
- **W3.2 solo prezzo** (indici; ETH dal 2018 dove il flusso perp non esiste): `research/multi_asset/ma_lib.s1_sim` (W3.1 senza
  flusso, funding e distribuzione, lezione 104) con rischio 0,25. Indici: settimana W-FRI (decisione all'ultima seduta, esecuzione
  all'apertura della seduta successiva), long e short, costo 0,05% per lato (commissione + slippage su ETF/future) e short 3%
  annuo sul nozionale (come multi_asset). Crypto solo prezzo: W-SUN, costo 0,2% per lato (0,1% + slippage 0,1%), short 10% annuo
  (stima prudente del funding). Indici di prezzo senza dividendi, buy & hold sullo stesso indice di prezzo.
- **Confronto a rischio 10%**: stesse regole con R = 0,10 (solo descrittivo, nessun criterio).
- Riferimento BTC: W3.2 completa sui dati del repo (attesi 78.474 $ dal 2021) e BTC solo prezzo con lo stesso motore degli indici.

## Universo e periodi
ETH, SOL; S&P 500 (^GSPC), Nasdaq 100 (^NDX), Dow Jones (^DJI), DAX (^GDAXI), FTSE MIB (FTSEMIB.MI), Nikkei 225 (^N225),
Russell 2000 (^RUT), Euro Stoxx 50 (^STOXX50E): 10 asset. Fonte indici: Yahoo chart API pubblica (fetch.py di multi_asset, taglio
20/11/2026). Se una fonte non risponde o la storia non copre il 2018 il dato si dichiara mancante e l'asset esce dal denominatore.
Periodo principale: 01/01/2021 → ultimo dato. Secondario: 01/01/2018 (o primo giorno utile) → ultimo dato.
Metriche: finale, CAGR, max DD giornaliero, trade, WR, CAGR/DD; buy & hold (finale, DD, CAGR/DD) dello stesso periodo.

## Criterio "funziona" per asset (rischio 25%, periodo principale dal 2021) — TUTTE le condizioni
1. CAGR/DD > CAGR/DD del buy & hold dello stesso periodo;
2. max DD giornaliero ≥ −35%;
3. win rate ≥ 60%;
4. rendimento positivo in entrambe le metà (2021–23 e 2024→fine, ciascuna simulata da flat);
5. ≥ 8 trade.
**Conferma di robustezza** (solo per chi passa 1–5): senza il trade migliore il finale resta > 10.000 $; con stop/trailing
2,0 e 3,0 ATRw (vicini) CAGR/DD resta > B&H in almeno uno dei due; dal 2018 CAGR/DD > B&H.

## Verdetto complessivo (su 10 asset, meno quelli senza dati)
- "Trasferibile": ≥ 7 asset passano 1–5 e la conferma.
- "Parziale": 3–6 asset passano 1–5.
- "Non trasferibile": ≤ 2 asset passano 1–5.
Un asset che passa resta un candidato da osservare, non un'aggiunta al tool (decisione dell'utente). Nessuna variante oltre a
queste (25% / 10%, vicini 2,0/3,0 per la conferma); nessun placebo se nessun asset passa 1–5.
