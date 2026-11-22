# Preregistrazione · order book e liquidazioni come supporto a W3.1 (22/11/2026)

Scritta PRIMA di calcolare qualsiasi rendimento o esito. Prima della stesura sono stati contati solo gli eventi prodotti dalle
definizioni (lezione 98), senza guardare prezzi successivi.

## Dichiarazione: studio INDICATIVO
Le fotografie del book (data/orderbook.csv) partono il 07/11/2026 08:53 UTC: 274 righe fino al 22/11 12:02, circa 8 al giorno fino
al 13/11 e 24 al giorno dal 14/11. Sono ~15 giorni: a 24 ore ci sono ~15 osservazioni indipendenti, a 1 ora alcune centinaia
autocorrelate. Il periodo contiene un solo regime (ribasso da 76k a 55k con cascata e squeeze). Nessun esito di questo studio può
diventare una regola o modificare W3.1: al massimo indica cosa registrare e come rifare il test in avanti.

## Dati e vincoli noti prima dei risultati
- Book: profondità aggregata di 5 exchange (Coinbase, Kraken, OKX perp e spot, Binance spot) entro ±0,25/0,5/1/2%; muro = solo la
  fascia dello 0,05% più grande per lato fra ±0,1% e ±2%. La fascia ±3% richiesta NON esiste nel registro: si usa ±2% (a ±2% in
  media solo ~1,9 fonti coprono entrambi i lati: lettura dominata da una o due fonti). Il book grezzo non è salvato: un solo muro
  per lato e per ora.
- Prezzi: candele 1 minuto BTCUSDT spot (data-api.binance.vision), dal 07/11 alle ore recenti; prezzo a t = chiusura del minuto
  della foto.
- Liquidazioni stimate: radar/liqmap.build con 504 ore di OI Binance (archivio data.binance.vision) e candele orarie PRIMA di t
  (nessun dato dal futuro); fascia densa = cluster con rel ≥ 0,30 (liqmap.SIG) entro ±10%.
- Livelli reali on-chain: data/liqsnap (Hyperliquid e Lighter, dal 11/11), ultima fotografia ≤ t, cluster di liqsnap.clusters.
- S/R: radar/levels.compute sulle candele giornaliere chiuse fino al giorno prima di t.
- Liquidazioni reali: data/liq_events (OKX, Gate, dYdX, … dal 10–11/11) e data/liquidations.csv (OKX dal 30/10): solo H4.

## Ipotesi e misure (8 celle principali)
**H1 squilibrio** imb = (bid − ask)/(bid + ask) a ±1% (H1a) e ±2% (H1b, sostituto di ±3%) → rendimento a 1, 4, 24 ore.
Misure: correlazione di Spearman; rendimento medio per quintile e spread Q5 − Q1; p da permutazione a blocchi (spostamento
circolare dei rendimenti rispetto al segnale a blocchi di 24 ore, 2.000 ripetizioni); IC 95% della correlazione da bootstrap a
blocchi giornalieri; stesso segno nelle due metà (07–15/11 e 16–22/11). Controllo: correlazione dello squilibrio con il rendimento
delle 24 ore precedenti (lezione 81: lo squilibrio può essere solo momentum).
**H2 muro vicino**: muro con dimensione ≥ 3× la fascia media entro ±1% (proxy: profondità ±1% del lato / 20 fasce) e distanza
≥ 0,3% (i muri a 0,1–0,15% vengono toccati comunque). Eventi deduplicati in episodi (stesso muro entro 0,25% e meno di 6 ore
dall'evento precedente). Esiti entro 24 ore (candele 1m): raggiunto (il prezzo tocca il livello), superato (va oltre di ≥ 0,3%),
rimbalzo (dopo il primo tocco torna di ≥ 1% dal lato di partenza prima di superarlo). Confronto: livelli casuali alla stessa
distanza e dallo stesso lato in tutte le altre foto (stesso esito calcolato), differenza in punti, p per permutazione delle
etichette per episodio.
**H3 confluenza**: muro di H2 con, entro 0,5%, (a) una fascia densa stimata, (b) un cluster reale on-chain, (c) una zona S/R
(lo/hi allargati dello 0,5%). Stesse misure di H2, confluenza contro muro senza confluenza e contro livelli casuali.
**H4 descrittivo**: giorni 13/11 (cascata), 15/11 (squeeze), 16–22/11 (short W3.1 aperto il 16/11 a 65.286): squilibrio, muri,
liquidazioni reali per lato, mappa stimata e livelli on-chain sopra/sotto. Nessun test.

## Soglie (fissate ora)
- H1 "indizio": |ρ| ≥ 0,10, p a blocchi < 0,05, stesso segno nelle due metà, |Q5 − Q1| > 0,30% (costi andata e ritorno di W3:
  commissione perp 0,05% + slippage 0,10% per lato). Celle: 2 fasce × 3 orizzonti = 6; Bonferroni informale: p < 0,0083 per
  parlare di indizio "forte".
- H2/H3 "indizio": differenza ≥ 10 punti contro i livelli casuali con p < 0,05 e almeno 10 episodi; altrimenti "nessuna evidenza".
- Robustezza (solo se c'è un indizio): soglia muro 2,5× e 4×, distanza ≥ 0,2% e ≥ 0,5%; senza l'episodio migliore.
- Potenza: si riporta l'n indipendente necessario per vedere ρ = 0,05 / 0,10 e differenze di 10 punti con potenza 80%, α 0,05.

## Cosa NON si fa
Nessuna strategia, nessun ottimo di parametri, nessuna modifica a radar/, tests/ o al tool. La tabella standard 10.000 $ dal 2021
non è applicabile (il book esiste da 15 giorni): si riportano solo W3.1 e buy & hold nella stessa finestra come contesto.
