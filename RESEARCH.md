# Diario di ricerca · Radar Signal BTC

Ciclo di miglioramento automatico: **2 giri approfonditi al giorno** (07:17 e 19:17 ora italiana). Il controllo orario di prezzi, ordini, stop e target gira gratis su GitHub Actions.

**Obiettivo (dal 30/10/2026): rendimento corretto per il rischio** = rendimento totale / |max drawdown| (MAR). Il win rate è un vincolo, non l'obiettivo. Ogni iterazione prova un'idea, la valuta con
`python -m radar.research` e la promuove solo se supera il gate in `radar/research.py`:

- MAR (rendimento / max drawdown) migliore di almeno il 5% (obiettivo principale)
- aspettativa nel test (2024–2025) non peggiore di oltre 0,1 punti
- migliore in almeno il 60% dei semestri dal 2022, nessun semestre peggiore di oltre 1,5 punti per trade
- probabilità ≥ 75% che l'aspettativa superi la base (ricampionamento dei trade)
- win rate pulito non più basso di oltre 3 punti
- su SOL (banco di prova, non operativo) l'aspettativa non peggiora di oltre 0,5 punti
- nessun peggioramento oltre 0,25 punti nel periodo di conferma (2026–oggi)
- non peggiora troppo nel training (2022–23): altrimenti è rumore
- win rate test non più basso di 2 punti, max drawdown non peggiore di 3 punti
- almeno l'80% dei trade attuali
- robustezza: tutte le varianti vicine dei parametri in profitto e con win rate ≥ 70%
- non concentrato: togliendo il trade (o i due trade) che migliorano di più, il candidato deve restare migliore della base (aggiunto dopo l'iterazione 3)
- i nuovi parametri introdotti dal candidato vanno variati anche loro nel test di robustezza: un risultato "a gradino" non si promuove

Regole operative: nessuna promozione mentre un trade è aperto;
ogni promozione viene annunciata su Telegram e annotata qui.

## Studio indicatori tecnici (completato 30/10/2026, iterazione 5)
Esito: nessun indicatore classico migliora la strategia. Su 59 condizioni e 165 incroci, 5 incroci stabili contro 2,9 attesi per caso (p95 7): nessuno significativo. Stabile solo il flusso perp (già nello score). RSI>70 e ADX>25 con DI− hanno edge sul mercato ma non sui trade. MACD, RSI, %B, stocastico, EMA 9/21, OBV sono ridondanti con lo score (ρ 0,6–0,9). Fibonacci, Bollinger/squeeze, proxy liquidazioni, funding/basis/F&G estremi non stabili. Testati in strategia: setup momentum (Donchian 55 + RSI>70) test exp 1,29 vs 1,92; setup short di trend (EMA21×50 + ADX>25 DI−) test exp 1,36 o ridondante: gate NO. Script: indicators.py, evalcand.py (scratchpad di sessione). Piano originale:
1. Calcolare su BTC giornaliero (senza look-ahead): SMA 20/50/100/200 e incroci, EMA 9/21/50/200 e incroci, MACD (12,26,9: linea,
   istogramma, incroci), RSI 14 (zone, divergenze), volume (z-score, OBV, volume relativo, CVD già presente), proxy di
   liquidazioni (crolli dell'open interest insieme a movimenti forti di prezzo e sbilanciamento taker: lo storico delle
   liquidazioni vere non è disponibile gratis), ritracciamenti di Fibonacci (distanza dai livelli 0,382/0,5/0,618 dell'ultimo
   swing a 60–90 giorni), ADX/DI 14 (forza del trend), Bande di Bollinger (posizione %B, ampiezza e squeeze), più altri utili:
   Stocastico, ATR percentuale, Donchian, VWAP ancorato, funding/basis estremi, Fear & Greed.
2. Per ogni indicatore e condizione: potere predittivo sul rendimento a 7/14/30 giorni (correlazione di rango e tasso di
   successo condizionato), separato per periodo 2020–21, 2022–23, 2024–25, 2026, per vedere se è stabile.
3. Incroci: combinazioni di 2–3 condizioni (es. trend ADX forte + RSI in ipervenduto + prezzo sul 0,618 di Fibonacci;
   squeeze di Bollinger + flusso perp positivo). Riportare numero di casi, successo e rendimento medio, sempre per periodo.
   Penalizzare le combinazioni con pochi casi (< 15) e controllare l'effetto "data mining" (quante combinazioni provate).
4. Confrontare con lo score attuale (CVD perp − long/short retail): un indicatore aggiunge informazione nuova o è ridondante?
5. Per i 2–3 risultati più promettenti: test come filtro o come nuovo setup nella strategia con la scorecard e il gate.
6. Conclusione: cosa è favorevole e stabile, cosa no; rapporto in RESEARCH.md e su Telegram come "Giro N · RAPPORTO indicatori".

## Obiettivi e struttura dei giri (dal 30/10/2026)
**Obiettivo principale**: rendimento corretto per il rischio (MAR = rendimento / |max drawdown|), oggi 9,55.
**Vincoli** (una modifica non li deve violare): perdita massima per singolo trade a 1x ≤ 9%; almeno 8 trade l'anno;
win rate ≥ 85% e win rate pulito non in calo; nessun peggioramento su SOL (banco di prova).
**Traguardo a 3 mesi**: MAR ≥ 12 con drawdown a 1x ≤ 12%, e ≥ 5 segnali reali registrati coerenti con il backtest.

**Giro del mattino (07:17) · verifica e operatività** — breve:
dati e test, segnale della notte, ordini toccati, registro dei segnali reali contro il backtest, SOL su carta,
regione prevista del giorno, calendario macro della giornata; una sola idea "veloce" (parametro singolo) se c'è tempo.
**Giro della sera (19:17) · ricerca approfondita** — una famiglia di idee della roadmap, fino a 5–6 varianti, gate completo,
eventuale promozione.
**Domenica sera · revisione settimanale**: riepilogo della settimana, lezioni apprese, riordino della roadmap.
**Ogni giro impara**: aggiorna "Lezioni apprese" (nuova lezione, conferma o correzione con i numeri) prima di chiudere.
**Ogni giro** chiude il messaggio Telegram con 2–3 **idee proposte** per i giri successivi (cosa, perché, impatto atteso):
l'utente sceglie in chat; senza risposta si segue la roadmap.

**Roadmap della ricerca** (ordine per impatto atteso):
1. Gestione del 40% lasciato correre (fonte principale del guadagno): trailing alternativi (chandelier, SMA20, minimo a N giorni),
   durata massima 30/45/60 giorni, uscita parziale sulla zona di vendita prevista.
2. Drawdown di portafoglio: size ridotta dopo uno stop o con capitale sotto il massimo, pausa dopo stop consecutivi.
3. Filtro di "distribuzione": long bloccati quando score negativo e retail long affollato anche con trend rialzista.
4. Ingressi più precisi con candele a 4 ore dentro la regione prevista (anche per avere più trade e un campione più grande).
5. Liquidazioni reali (quando `data/liquidations.csv` avrà almeno 2–3 mesi).

## Lezioni apprese (aggiornare a ogni giro: è la memoria del ciclo)
1. Più tranche riempite nei trade che poi vanno in stop = perdite più grandi: avvicinare i limit DCA peggiora il drawdown (it. 1).
2. Lo stop a pareggio dopo il TP1 protegge più di quanto costa: toglierlo o allargarlo alza il win rate pulito ma fa crollare l'aspettativa (it. 3).
3. Un miglioramento che dipende da 1–2 trade non è un miglioramento: controllare sempre la concentrazione e variare anche i nuovi parametri (it. 3).
4. Uno stop più largo va sempre abbinato a una size più piccola, altrimenti aumenta la perdita reale sul capitale (it. 3).
5. Il vantaggio di un asset va verificato anno per anno: risultati aggregati possono nascondere un edge concentrato in un periodo (SOL 2022–23, it. 2).
7b. Un vantaggio dell'indicatore sul mercato non diventa vantaggio sui trade: la strategia compra apposta nelle condizioni "brutte" (ADX con DI− dominante: 17 trade, 100% vincenti). Giudicare gli indicatori sui trade, non sul mercato (it. 5).
6. Il guadagno vero arriva dal 40% lasciato correre (uscite a tempo +12%, trailing +8,9%): proteggerlo prima di ottimizzare altro.
7. Il sizing a rischio fisso non crea vantaggio da solo; con soli 3 stop in 47 trade ogni confronto stop largo + sizing dipende da 2–3 trade: giudicarlo a parità di perdita massima per stop, non di drawdown (it. 4).

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
3. **Budget per operazione**: sizing a rischio fisso (es. 1–2% del capitale perso se scatta lo stop, con size = rischio / distanza dello stop, leva massima 3x), sizing per setup in base alla sua storia, confronto con l'allocazione fissa attuale (100% del capitale × pesi DCA). Esito it. 4: con rischio 1–2% la leva media sarebbe 0,1–0,2x (rendimento quasi nullo); il budget sensato per questo sistema è intorno al 7–8% di perdita massima per stop sul capitale allocato a 1x.
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
- **2026-10-30 14:05 UTC · Iterazione 4 · NON PROMOSSO** — Stop più largo + budget a rischio fisso (size = rischio % / distanza stop dal medio a DCA completa, leva max 3x). Con rischio 1–2% la leva media è 0,1–0,2x e il rendimento full scende a +12/+24%: per rendimenti paragonabili serve rischio 8–15% per trade. Sizing a rischio fisso con stop 3 ATR a leva media 1x: +161,8% DD −17,8 (base +156,7% DD −16,4), nessun vantaggio. Migliore: stop 4,5 ATR + rischio 15,4% (leva media 1x, max 1,78x): full +205,7% DD −11,6 (obiettivo DD<12% raggiunto), test exp 3,18 vs 1,92, holdout 3,71 vs 2,85, ma train exp 1,56 < soglia 1,61 → gate NO; guadagno quasi tutto da 3 trade (17/12/2024, 06/01/2025, 22/07/2026), perdita per stop −11,6% vs −9,0% max base. Prossimo: priorità 2, drawdown di portafoglio (size ridotta dopo uno stop o con equity sotto il massimo).
- **2026-10-30 15:25 UTC · Iterazione 5 · RAPPORTO** — Studio indicatori tecnici (SMA, EMA, MACD, RSI, volume, proxy liquidazioni, Fibonacci, ADX, Bollinger, stocastico, Donchian, funding/basis, F&G): nessun miglioramento, nessun incrocio significativo oltre il caso; unico segnale stabile il flusso perp già usato. Due setup testati, gate NO. Prossimo: drawdown di portafoglio.
