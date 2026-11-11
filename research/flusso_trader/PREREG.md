# PREREG · flusso perp vs spot "lo spot assorbe" (11/11/2026, scritto prima dei risultati)
Dati: data/perp.csv e data/spot.csv (Binance BTCUSDT giornaliero, taker_buy_volume). Quota taker buy = taker_buy/volume.
Flusso N giorni: pfN = sum(2·tb−vol)/sum(vol) (perp), sfN idem spot; z su 180 giorni (come radar/features.py).
Campione eventi: dal 01/01/2021 a oggi. Ingresso alla chiusura del giorno evento t (nessun look-ahead).
Stato A (giorno t−k, k=1..5): pfNz < Z_A e sfNz ≥ 0 ("perp vende, spot assorbe").
Evento "riequilibrio": dopo A, primo giorno con quota perp giornaliera in [49,5%; 50,5%] oppure pfNz > −0,25. Pausa 7 giorni.
Evento "presa di controllo" (versione severa): dopo A, primo giorno con quota perp > 50,5%.
Varianti (8): V1 N=5 Z_A=−1 riequilibrio · V2 N=3 · V3 N=7 · V4 N=5 Z_A=−0,75 · V5 N=5 Z_A=−1,25 ·
V6 N=5 severa · V7 N=3 severa · V8 N=7 severa.
Misure: rendimento a 1/3/7/14 g contro media incondizionata; placebo = 2000 insiemi di giorni casuali stessa numerosità (p
unilaterale); split 2021–23 / 2024→; trade long 7 g, 1x, 10k, costi 0,1% a giro, contro buy & hold e W3.
Soglia "utile": eccesso a 7 g ≥ +1 pp, placebo p < 0,05, stesso segno nei due periodi, V1–V5 coerenti (no gradino), ≥ 15 eventi.
Altrimenti "solo contesto" (segno coerente ma non significativo) o "nessun vantaggio".
Rapporto con W3: eventi nei 14 giorni prima di un ingresso W3 (research/weekly_w3_trades.csv) contro attesa casuale.
