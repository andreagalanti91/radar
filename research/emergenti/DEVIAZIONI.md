# emergenti · deviazioni dal PREREG (commit 1110e53) e scelte d'implementazione

Il PREREG non è stato modificato. Qui sono elencate le deviazioni e i punti che il PREREG lasciava aperti.

1. **Riferimento del controllo del motore**: 84.820 $ (BTC dal 2021-01-01, dati al 24/11/2026) ed ETH 39.572 $, al posto di
   78.474 $ (era con dati al 10–15/11). Indicazione del coordinatore. `engine.check()` dà BTC 84.820 / 84.820 ed ETH
   39.572 / 39.572, con trade identici a `radar.weekly.simulate`.
2. **Funding di novembre 2026**: dopo i conteggi della fase 1, `build.py` aggiunge per i perp vivi il funding OKX del mese non
   ancora archiviato da Binance, come fa `w32_asset2/build.py` (serve per arrivare a 84.820 $). Il funding entra nella regola di
   distribuzione (fund7), quindi gli ingressi emergenti dal 2021 erano diventati 1.191. Dopo il taglio dei cambi di
   denominazione (punto 12) tornano 1.190 (463 long, 727 short). Per anno: 2023 183 (85 short) e 2026 255 (195 short) invece
   di 184 e 254. `DATI.md` è riallineato. Le 6 monete con abbinamento errato (META, ADI, PURR, LA, NET, BZ) contano come
   "senza dati". I perp vivi senza OKX restano senza funding di novembre.
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
   stesso portafoglio a 5 posizioni. Statistica: CAGR/DD del budget sul periodo intero; 5.000 prove, seme 7; Holm su m = 10. Il placebo esce a tempo senza stop,
   quindi le operazioni a caso tengono anche le perdite che W3.2 avrebbe chiuso: il p è probabilmente un po' ottimistico per le
   varianti (lo stop taglia le code avverse dei casi reali, non quelle del placebo).
9. **Liquidazione nel giorno d'uscita all'apertura** (EMA, distribuzione, uscita a tempo): si controlla solo l'apertura.
10. **Buy & hold equipesato**: le monete della lista dell'anno con versione completa al 1/1 e prezzo al 1/1, comprate
    all'apertura del primo giorno; una serie che finisce resta ferma all'ultimo prezzo. Vendita al 31/12, poi ribilanciamento,
    con 0,2% per lato. Nel 2021 le monete idonee sono solo 4.
11. **Vista "emergenti di oggi"** (descrittiva): stessa regola di V1, ma la lista vale per tutti gli anni (rank CoinGecko
    101–500 del 27/11/2026).
12. **Salti giornalieri e cambi di denominazione** (dopo la revisione critica del 27/11): BNX non era corretto per il cambio
    1:100 del 22/02/2023 e generava uno short artefatto (13/03/2023, d = 12.767%) che occupava una quota fino al 29/04/2024.
    `build.py` ora segnala ogni salto > 3x (`data/salti.csv`). Se l'apertura è la chiusura precedente divisa o moltiplicata per
    10, 100 o 1000 (±3%), la moneta si taglia da quel giorno: BNX, STRAX (28/03/2024, 1:10), BTCST (19/03/2021). DEXE
    (21/07/2026) è un crollo reale (apertura continua, prezzi coerenti con CMC 2025 e CoinGecko di oggi): resta. Cache dei trade
    cancellata e `run.py` rilanciato.
13. **Soglia di riconsiderazione di V3**: non sta nel PREREG. È scritta come proposta in `PREREG-AVANTI-V3.md`, da committare
    prima del 30/11 solo se l'utente vuole il registro sulla carta.
