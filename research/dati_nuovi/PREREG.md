# PREREG · dati_nuovi · fonti nuove per gli ingressi/uscite di W3.2 (27/11/2026)

Scritto PRIMA di qualsiasi rendimento delle varianti. Fase 1 eseguita: analisi degli errori (descrittiva, trade già noti),
scarico delle fonti, conteggi senza esiti (`conteggi_output.txt`). Da committare da solo prima di eseguire la fase 2.
W3.2 (`radar/weekly.py`) non si tocca: il motore di prova è `motore.py` (avvolge `weekly_bars` durante la simulazione).
Verifica senza regola (`verifica_motore.txt`): BTC dal 01/01/2021 **84.820 $**, BTC dal 01/01/2018 **242.755 $**, ETH dal
11/01/2021 **39.572 $** = riferimenti.

## 1. Base descrittiva (fase 1, `errori/`)
- 11 operazioni in perdita: BTC 5 dal 2018 (01/2018 −25,1%, 04/2018 −3,3%, 02/2020 −2,6%, short 03/2020 −17,9%, 08/2026 −4,1%),
  ETH 6 dal 2021 (03/2022 −5,5%, short 08/2022 −1,9%, short 09/2022 −5,4%, 06/2024 −21,4%, 11/2024 −5,7%, 08/2026 −7,4%).
- Long persi (8): 6 entrati nelle prime 1–3 settimane sopra la SMA40 (vincenti: 9 su 18). Le due perdite grandi sono long in
  trend vecchi e surriscaldati (BTC 01/2018: 2,6 ATR sopra la EMA21, MVRV 3,25; ETH 06/2024: OI +94% in 28 giorni, long/short
  dei top trader al 94° percentile, funding 7 g il più alto). Mediane dal 12/2021: long/short globale 1,59 nei long persi contro
  0,84 nei vincenti, OI a 28 g +31% contro +24% (pochi casi).
- Short persi (3): aperti dal 38% al 43% sotto la SMA40 dopo un crollo, con MVRV basso (2°–18° percentile) e flusso debole.
  Nei vincenti la mediana è −13% (informazione di prezzo, già vista nella lezione sulla capitolazione: non è una fonte nuova).
- DXY, VIX e DVOL non distinguono le perdite dalle vincite.
- Uscite tardive (in guadagno ma con oltre il 50% del guadagno massimo restituito): 12 (BTC 8, ETH 4). Era già noto: è il
  costo dei trend lunghi (lezione 109).
- Movimenti oltre il 30% (zigzag sulle chiusure) presi per meno di un terzo: BTC 12 su 21, ETH 13 su 22. Quasi tutti sono
  movimenti contro il regime (rimbalzi nei bear, cali nei bull), bloccati dalla SMA40 o dalla EMA21. Dove c'è il regime, il blocco
  più frequente è il flusso perp. Sono 66 domeniche da flat con prezzo ok e flusso contrario su BTC e 58 su ETH: è lo spazio
  dell'obiettivo B.

## 2. Fonti (gratuite, API/archivi pubblici, User-Agent dichiarato; `fetch.py`, `fonti.py`)
| Fonte | Periodo usabile | Buchi | Ritardo applicato alla domenica |
|---|---|---|---|
| (a) COT CFTC TFF, CME Bitcoin 133741 / Ether 146021 (asset manager) | BTC 04/2018→, ETH 04/2021→ | salti ≤ 8 gg (festivi) | report del martedì disponibile dal venerdì (+3 gg). Shutdown: report 18/12/2018–01/03/2019 disponibili dall'08/03/2019, report 30/09/2025–13/01/2026 dal 23/01/2026 (prudenziale, date di recupero approssimate) |
| (b) base Deribit: trimestrale più vicina con ≥ 14 gg vs perpetual, annualizzata | BTC 08/2018→ (perp Deribit dal 14/08/2018), ETH 03/2019→ | nessuno | candela 08:00→08:00 UTC: 1 giorno |
| (c) funding medio: Binance, Deribit, Hyperliquid (media semplice delle disponibili) | 05/2019→ (Deribit), Binance 2020→, Hyperliquid 06/2023→ | – | 1 giorno |
| (d) miner: hash rate blockchain.com (hash ribbon SMA30/60) | 2009→ | 1 (4 gg) | 2 giorni |
| (e) CoinMetrics community: FlowInExNtv, FlowOutExNtv, SplyExNtv | 2016→ (BTC, ETH) | – | 1 giorno |

Non usabili per il backtest: OKX e Bitget (le API pubbliche danno solo gli ultimi 3 mesi), Bybit e BitMEX (bloccati da qui), OI
aggregato (gratis c'è solo Binance dal 12/2021, già nei dati), CME basis (non gratuito). Binance coin-M trimestrali (dal 2020) e
hash rate CoinMetrics (correlazione 1,000) servono solo da controllo. **Le metriche di flusso CoinMetrics sono tutte "flash",
anche nel passato**: lo storico è ricalcolato (etichette degli indirizzi aggiornate dopo), quindi non è point-in-time. Un buon
risultato con (e) è un limite superiore e non si adotta senza registro dal vivo.

## 3. Varianti (9; definizioni fissate qui; Holm con m = 9)
s ∈ {+1, 0, −1}, letto alla domenica della decisione con i ritardi del §2. **A** = filtro d'ingresso: nuovo long solo se s ≠ −1,
nuovo short solo se s ≠ +1; uscite invariate. **B** = ingresso aggiuntivo: da flat si entra anche se tutte le condizioni di prezzo
di W3.2 sono vere (regime, EMA21, F1 per i long) ma il flusso perp ha il segno sbagliato, e s conferma il verso. **E** = ingresso
anticipato long: da flat, chiusura sopra la EMA21 e EMA20 in salita, senza SMA40 né flusso, con s = +1. Dimensione, stop, trailing
e uscite sempre di W3.2.

| # | Variante | Definizione di s | Vicini |
|---|---|---|---|
| V1 | COT-A | segno della variazione della posizione netta degli asset manager (lunghi − corti)/OI rispetto a 4 report prima | 3, 6 report |
| V2 | COT-B | come V1 | 3, 6 |
| V3 | BASE-A | segno della variazione a 28 giorni della base annualizzata (media 7 giorni) | 21, 42 gg |
| V4 | BASE-B | come V3 | 21, 42 |
| V5 | FUNDING-A | −1 se il funding medio a 7 g è ≥ 90° percentile dei 365 g precedenti (long affollati), +1 se ≤ 10°, 0 altrimenti | 85/15, 95/5 |
| V6 | MINER-A | −1 durante la capitolazione (SMA30 < SMA60 dell'hash rate), 0 altrimenti: blocca solo i long | 25/50, 35/70 |
| V7 | MINER-E | +1 nelle 8 settimane dopo la fine di una capitolazione (ribbon da −1 a +1) | 6, 12 settimane |
| V8 | FLUSSI-A | −segno della somma a 7 g dei flussi netti verso gli exchange (entrate − uscite) | 5, 14 gg |
| V9 | SALDO-B | −segno della variazione a 28 g del saldo sugli exchange (saldo in calo = accumulo) | 21, 42 gg |

Escluse ora per mancanza di potenza nei conteggi (meno di 3 episodi per asset): FUNDING-B (BTC 2 episodi, ETH 0) e MINER-B
nella forma B (0 domeniche long). Escluse le uscite anticipate: le lezioni 88, 109, 125 e 130 dicono che un'uscita aggiunta taglia
i trend lunghi o crea trade di una settimana. Per ETH il miner usa l'hash rate di BTC (segnale di mercato; ETH non ha miner dal
09/2022). Quando la fonte manca, s = 0 e la regola non agisce (BTC 01/2018 e 04/2018 senza COT né base).

## 4. Periodi e metriche
10.000 $, 1x, costi e funding del motore, partenza da flat in ogni periodo, fine 24/11/2026, posizione aperta valutata
all'ultima chiusura. Metriche: capitale finale, rendimento, CAGR, DD massimo giornaliero, CAGR/DD, operazioni (chiuse + aperta),
WR delle chiuse, finale senza l'operazione migliore. Confronto con W3.2 e con il buy & hold.
- BTC: dal 2018 (serie continua, frame lungo); dal 2021 (frame del tool); IS 2018–2022; OOS 2023→; 2024→ a parte.
- ETH: dal 11/01/2021; IS 2021–2022; OOS 2023→; 2024→ a parte.
- "Insieme": BTC + ETH con capitali separati da 10.000 $ ciascuno dal 11/01/2021.

## 5. Criteri (tutti; su BTC ed ETH separatamente e poi insieme)
**A (V1, V3, V5, V6, V8)**: dal 2021 CAGR/DD > W3.2, DD non peggiore di 2 punti, WR delle chiuse ≥ W3.2; BTC dal 2018 CAGR/DD ≥
W3.2; IS e OOS CAGR/DD ≥ W3.2; senza l'operazione migliore finale ≥ W3.2 senza la sua migliore; entrambi i vicini con CAGR/DD dal
2021 ≥ W3.2; insieme CAGR/DD > W3.2 insieme.
**B/E (V2, V4, V7, V9)**: più operazioni di W3.2; CAGR/DD dal 2021 ≥ W3.2 e BTC dal 2018 ≥ W3.2; DD non peggiore di 2 punti; WR
delle chiuse non più basso di 5 punti; IS e OOS CAGR/DD ≥ W3.2; entrambi i vicini con CAGR/DD ≥ W3.2; insieme CAGR/DD ≥ W3.2.
**Placebo** (per tutte): slittamento circolare della serie s di k settimane, per tutti i k distinti da 26 a N−26. Statistica:
CAGR/DD insieme dal 2021. p esatto = (numero di slittamenti con statistica ≥ reale + 1) / (slittamenti + 1). **Holm** al 5% su m = 9.
**Scelta finale**: fra le varianti che passano tutto, la più profittevole, cioè il capitale finale insieme più alto dal 2021.
Se nessuna passa, W3.2 resta invariata. Una combinazione A+B si descrive soltanto: per adottarla serve un nuovo PREREG.
**Scanner altcoin**: solo per una variante che passa su BTC ed ETH. Si usa l'universo di `research/w32_asset2` (crypto con
almeno 3 anni). COT, base e miner usano il segnale di BTC; funding e flussi quello dell'asset se c'è, altrimenti quello di BTC.
Passa se la mediana del CAGR/DD non peggiora e almeno il 60% delle monete non peggiora. Solo descrittivo, nessuna modifica al tool.

## 6. Limiti e rischio di adattamento
- Pochi trade: 14 su BTC dal 2021 (13 + 1 aperta), 23 dal 2018, 15 su ETH. Una variante che cambia 1–2 trade può superare i
  criteri per caso: per questo servono placebo, Holm e vicini.
- L'analisi degli errori ha visto i trade persi prima delle definizioni: è un rischio di adattamento dichiarato. Le definizioni
  sono generiche, da manuale, e uguali per BTC ed ETH; nessuna soglia è stata scelta sui trade persi.
- Fonti corte: COT ETH dal 04/2021, Hyperliquid dal 2023. Prima del 2019 il funding è nullo e il flusso BTC è stimato dal CVD spot.
- COT durante gli shutdown: date di pubblicazione approssimate per prudenza. CoinMetrics "flash": storico non point-in-time.
- W3.2 è stata costruita guardando il 2018–26: gli unici dati fuori campione veri sono quelli dal vivo, dal 02/11/2026.
