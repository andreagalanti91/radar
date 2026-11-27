# emergenti · deviazioni dal PREREG (commit 1110e53) e scelte d'implementazione

Il PREREG non è stato modificato. Qui sono elencate le deviazioni e i punti che il PREREG lasciava aperti.

1. **Riferimento del controllo del motore**: 84.820 $ (BTC dal 2021-01-01, dati al 24/11/2026) ed ETH 39.572 $, al posto di
   78.474 $ (era con dati al 10–15/11). Indicazione del coordinatore. `engine.check()` dà BTC 84.820 / 84.820 ed ETH
   39.572 / 39.572, con trade identici a `radar.weekly.simulate`.
2. **Funding di novembre 2026**: dopo i conteggi della fase 1, `build.py` aggiunge per i perp vivi il funding OKX del mese non
   ancora archiviato da Binance, come fa `w32_asset2/build.py` (serve per arrivare a 84.820 $). Il funding entra nella regola di
   distribuzione (fund7): i conteggi di `DATI.md` cambiano di poco (ingressi emergenti dal 2021: 1.191 invece di 1.190). I
   file `data/counts_*.csv`, `segnali.csv` e `summary.txt` sono stati rigenerati. I perp vivi senza OKX restano senza funding
   di novembre.
3. **Costi**: 0,2% per lato = 0,1% di slittamento (già nel prezzo del motore, come in W3.2) + 0,1% di commissione su
   ingresso e uscita. Tutte le posizioni sono in perp.
4. **Portafoglio e motore per moneta**: ogni moneta si simula da sola con le sue maschere d'ingresso: lista dell'anno, lato,
   filtri, cancello BTC. Il tetto di 5 posizioni si applica dopo. Un segnale scartato perché le quote sono piene non cambia la
   simulazione della moneta (approssimazione).
5. **Priorità** fra segnali dello stesso giorno: media a 90 giorni del controvalore del perp (chiusura × volume, almeno 30
   giorni). Uno slot liberato da un'uscita all'apertura (EMA o distribuzione) è riutilizzabile lo stesso lunedì; uno liberato
   da stop, trailing o liquidazione solo dal giorno dopo.
6. **Margine per posizione** = min(equity del budget / 5, cassa libera). Se le posizioni aperte valgono più dei 4/5
   dell'equity, il margine è la cassa rimasta.
7. **Senza il 10% migliore**: si tolgono dai candidati le operazioni eseguite migliori (10%, arrotondato per eccesso) e si
   rifà il portafoglio. Altri segnali possono prenderne il posto.
8. **Placebo**: per ogni segnale candidato della variante si estrae una moneta-giorno a caso nello stesso anno d'ingresso,
   fra le monete della lista di quell'anno con versione completa iniziata. Lato, durata in giorni, nozionale per 1 $ di
   margine, costi e liquidazione restano gli stessi. L'uscita è all'apertura dopo la stessa durata, senza stop; si applica lo
   stesso portafoglio a 5 posizioni. Statistica: CAGR/DD del budget sul periodo intero; 5.000 prove, seme 7; Holm su m = 10.
9. **Liquidazione nel giorno d'uscita all'apertura** (EMA, distribuzione, uscita a tempo): si controlla solo l'apertura.
10. **Buy & hold equipesato**: le monete della lista dell'anno con versione completa al 1/1 e prezzo al 1/1, comprate
    all'apertura del primo giorno; una serie che finisce resta ferma all'ultimo prezzo. Vendita al 31/12, poi ribilanciamento,
    con 0,2% per lato. Nel 2021 le monete idonee sono solo 4.
11. **Vista "emergenti di oggi"** (descrittiva): stessa regola di V1, ma la lista vale per tutti gli anni (rank CoinGecko
    101–500 del 27/11/2026).
