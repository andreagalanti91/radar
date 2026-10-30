# Diario di ricerca · Radar Signal BTC

Ciclo di miglioramento automatico (ogni ora). Ogni iterazione prova un'idea, la valuta con
`python -m radar.research` e la promuove solo se supera il gate in `radar/research.py`:

- aspettativa nel test (2024–2025) migliore della versione attuale
- nessun peggioramento oltre 0,25 punti nel periodo di conferma (2026–oggi)
- non peggiora troppo nel training (2022–23): altrimenti è rumore
- win rate test non più basso di 2 punti, max drawdown non peggiore di 3 punti
- rendimento totale almeno +5%
- almeno l'80% dei trade attuali
- robustezza: tutte le varianti vicine dei parametri in profitto e con win rate ≥ 70%
- non concentrato: togliendo il trade (o i due trade) che migliorano di più, il candidato deve restare migliore della base (aggiunto dopo l'iterazione 3)
- i nuovi parametri introdotti dal candidato vanno variati anche loro nel test di robustezza: un risultato "a gradino" non si promuove

Regole operative: nessuna promozione mentre un trade è aperto;
ogni promozione viene annunciata su Telegram e annotata qui.

## Lezioni apprese (aggiornare a ogni giro: è la memoria del ciclo)
1. Più tranche riempite nei trade che poi vanno in stop = perdite più grandi: avvicinare i limit DCA peggiora il drawdown (it. 1).
2. Lo stop a pareggio dopo il TP1 protegge più di quanto costa: toglierlo o allargarlo alza il win rate pulito ma fa crollare l'aspettativa (it. 3).
3. Un miglioramento che dipende da 1–2 trade non è un miglioramento: controllare sempre la concentrazione e variare anche i nuovi parametri (it. 3).
4. Uno stop più largo va sempre abbinato a una size più piccola, altrimenti aumenta la perdita reale sul capitale (it. 3).
5. Il vantaggio di un asset va verificato anno per anno: risultati aggregati possono nascondere un edge concentrato in un periodo (SOL 2022–23, it. 2).
6. Il guadagno vero arriva dal 40% lasciato correre (uscite a tempo +12%, trailing +8,9%): proteggerlo prima di ottimizzare altro.

## Osservazione SOL (dal 30/10/2026, decisione dell'utente)
SOL viene seguito a ogni giro con `python -m radar.observe SOLUSDT` (stessa strategia e parametri di BTC,
dati in `data/SOLUSDT/`, trade solo su carta). Non entra nel tool operativo: niente alert di trading, niente dashboard.
Lo stato è riportato nel messaggio Telegram di ogni giro. Rivalutazione dopo 10 trade chiusi fuori campione o 6 mesi
(criteri: aspettativa > +1%, drawdown del portafoglio non peggiore di BTC da solo, nessun trade < −12%).

## Valutazione ETH e SOL (completata 30/10/2026, iterazione 2)
**Raccomandazione: ETH non aggiungere; SOL solo osservazione; BTC unico operativo.**

Futures 1x, parametri di default (trade / WR / WR>1% / WR pulito / exp % / rend % / maxDD %):

| Periodo | BTC | ETH | SOL |
|---|---|---|---|
| Train 22-23 | 20/90,0/60,0/25,0/+2,01/+46,9/−4,4 | 22/68,2/59,1/22,7/−0,78/−21,5/−45,5 | 20/95,0/95,0/45,0/+7,57/+293,8/−15,2 |
| Test 24-25 | 19/84,2/73,7/42,1/+1,92/+40,2/−16,4 | 23/78,3/73,9/26,1/−0,03/−8,7/−35,1 | 24/75,0/70,8/33,3/+0,54/+2,2/−25,1 |
| Holdout 2026 | 8/100/100/37,5/+2,85/+24,6/0 | 7/85,7/85,7/57,1/+3,77/+28,4/−5,8 | 12/91,7/91,7/25,0/+1,50/+17,7/−10,9 |
| Full | 47/89,4/72,3/34,0/+2,12/+156,7/−16,4 | 52/75,0/69,2/28,8/+0,17/−8,0/−60,5 | 56/85,7/83,9/35,7/+3,26/+373,9/−31,1 |

PnL per anno (% capitale, 2022→2026):

| Asset | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|
| BTC | +14,9 | +25,3 | +25,3 | +11,1 | +22,8 |
| ETH | −14,4 | −2,7 | +2,2 | −2,8 | +26,4 |
| SOL | +89,6 | +61,9 | +27,7 | −14,8 | +18,0 |

Zone previste (`radar/zones.py`):

| | BTC | ETH | SOL |
|---|---|---|---|
| Tocco zona acquisto | 64,9% | 66,1% | 65,9% |
| Sotto la zona | 38,7% | 39,2% | 37,5% |
| Tocco zona vendita | 64,1% | 62,3% | 62,6% |

Portafoglio (rend / maxDD %):

| Mix | Full 1x | Test 24-25 |
|---|---|---|
| Solo BTC | +156,7 / −16,4 | +40,2 / −16,4 |
| 50/25/25 | +154,4 / −17,9 | +21,4 / −17,9 |
| 34/33/33 | +149,4 / −19,3 | +15,1 / −19,3 |
| 70/30 BTC/SOL | +229,5 / −16,1 | +31,1 / −16,1 |

Correlazione pnl mensile dei trade BTC–ETH 0,31, BTC–SOL 0,07. Approssimazione: trade ordinati per data di uscita, niente mark-to-market delle posizioni simultanee.

Rischi:

| | BTC | ETH | SOL |
|---|---|---|---|
| ATR medio dal 2022 | 3,8% | 5,2% | 7,4% |
| Giorni < −20% dal 2020 | 1 | 2 | 7 |
| Funding max \|giornaliero\| | 0,25% | 0,53% | 17,2% |
| Peggior trade 1x | −9,0% | −16,8% | −21,9% |

Piano osservazione SOL: parametrizzare `radar/data.py` per simbolo (cache `data/<SYMBOL>/`, instId OKX dal simbolo), segnali SOL in carta su dashboard/Telegram con size ~0,5x, rivalutare dopo 10 trade fuori campione o 6 mesi (criteri: exp > +1%, DD portafoglio non peggiore di BTC solo, nessun trade < −12%). Il sizing a rischio fisso (priorità "budget per operazione") potrebbe rendere SOL integrabile.

Script e dati della valutazione nella scratchpad di sessione (fetch.py, evalx.py, eval_eth_sol.json).

## Priorità dell'utente (30/10/2026, dopo l'iterazione 1) — affrontare per prime
1. **Stop calcolato**: stop non fisso a 3 ATR dal primo ingresso ma derivato da struttura/volatilità (es. sotto il bordo profondo della zona prevista − k·ATR, minimo a 20 giorni, stop sul prezzo medio dopo ogni tranche, stop a scaglioni). Misurare perdita media e massima per trade.
2. **Drawdown calcolato e limitato**: regole di rischio a livello di portafoglio, es. riduzione della size dopo una perdita o quando l'equity è sotto il massimo di X%, stop di sistema temporaneo dopo N stop consecutivi. Obiettivo: max drawdown a 1x sotto il 12% senza perdere più del 10% di rendimento.
3. **Budget per operazione**: sizing a rischio fisso (es. 1–2% del capitale perso se scatta lo stop, con size = rischio / distanza dello stop, leva massima 3x), sizing per setup in base alla sua storia, confronto con l'allocazione fissa attuale (100% del capitale × pesi DCA).
4. **Win rate pulito**: riportare sempre, accanto al win rate standard, `win_rate_clean` (solo trade chiusi da target, trailing o tempo in profitto; stop e pareggi esclusi dalle vincite) e `win_rate_1pct` (trade sopra +1%). Un candidato non deve peggiorarli in modo sensibile.

## Backlog prioritario (richiesto dall'utente, 30/10/2026)
Studiare a fondo la gestione a scaglioni, una variante per iterazione:
1. **DCA in entrata**: numero di tranche (2–5), pesi (piramide crescente/decrescente/uguale), distanza tra le tranche in ATR, validità dei limit, ingresso condizionato (tranche solo se il setup resta attivo).
2. **TP in DCA**: numero di target, distanze in ATR o in % del rischio (R multipli), pesi, target su livelli di struttura (massimi a 20g), trailing sul residuo (ATR, chandelier, SMA20).
3. **Stop loss in DCA**: uscita a scaglioni invece di uno stop unico (es. 1/3 a −2 ATR, 1/3 a −2,5, 1/3 a −3), stop per singola tranche, stop temporale parziale, stop che segue il prezzo medio dopo ogni tranche.
4. **Regione prevista** (`radar/zones.py`): posizionare le tranche DCA dentro la zona di acquisto invece che a distanze fisse in ATR; target dentro la zona di vendita.
Ogni variante va confrontata con il gate standard (`radar/research.py`) e riportata qui con i numeri del test.

## Baseline v2 (30/10/2026)
47 trade futures da mar 2022, win rate 89,4%, +157% a 1x, max DD −16,4%. Test 2024–26: 27 trade, 88,9%, aspettativa +2,19%.

## Iterazioni
- **2026-10-30 10:40 UTC · Iterazione 1 · SCARTATO** — Idea: tranche DCA 2 e 3 ai bordi della zona prevista (`radar/zones.py`: buy_hi/buy_lo long, sell_lo/sell_hi short) invece di −0,75/−1,5 ATR fissi, stop invariato. Test 2024–25: aspettativa +1,92% → +1,50%, rendimento +40,2% → +24,8%, max DD −16,4% → −25,4% (train exp +2,01 → +1,94; holdout 2026 +2,85 → +3,16; full 1x +156,7% → +130,3%, 2x +498,9% → +372,1%). Motivo: aspettativa test e drawdown peggiori — la zona è più vicina (0,66/1,33 ATR) e riempie più tranche nei trade stoppati (stop pieno −10,8% a mar 2025). Prossime: tranche più profonde (buy_lo e buy_lo − 0,5 ATR) o peso ridotto nella zona, combinare con stop sul prezzo medio (backlog 3).
- **2026-10-30 11:40 UTC · Iterazione 2 · RAPPORTO** — Valutazione ETH/SOL con parametri invariati: ETH non aggiungere (full −8%, DD −60%, exp test −0,03%), SOL solo osservazione (full +374% ma edge concentrato nel 2022–23, test exp +0,54%, 2025 negativo, peggior trade −21,9%); nessun mix batte BTC da solo nel test. Dettagli nella sezione Valutazione ETH e SOL.
- **2026-10-30 13:05 UTC · Iterazione 3 · NON PROMOSSO (gate superato ma fragile)** — Stop calcolato. (a) stop sul prezzo medio avg − k·ATR: test exp 0,67–1,42 vs 1,92, scartato; (c) pareggio con margine 0,5/1 ATR o solo dopo TP2: test exp 0,85–1,16, DD −25/−28%, scartato (il pareggio dopo TP1 protegge più di quanto costa; WR pulito sale a 61% ma l'aspettativa crolla); (b) stop di struttura sotto il minimo a 20g − 0,5 ATR, limitato 3–5 ATR: test exp 1,92 → 2,95, full +156,7% → +194,9%, DD −16,4 → −7,7, gate formalmente superato. Non promosso: identico a uno stop fisso a 5 ATR, il guadagno dipende da un solo trade (17/12/2024 da −8,96% a −0,52%, che fa sparire anche lo stop del 06/01/2025), risultato a gradino (3,5 ATR peggiora, ≥4,5 migliora) e perdita potenziale per stop +67%. Gate rafforzato con il controllo di concentrazione. Prossimo: stop 3–5 ATR insieme al sizing a rischio fisso (size = rischio / distanza stop, leva max 3x), così uno stop più largo non aumenta la perdita in % del capitale.

