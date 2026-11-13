# liqmap v2 · preregistrazione (13/11/2026, scritta prima di guardare i risultati)

**Domanda**: attribuire ogni aumento di OI a long o short con il flusso taker dell'ora (invece del 50/50) rende la mappa stimata
più vicina alle liquidazioni REALI?

**Varianti** (stessa funzione `radar/liqmap.build`, cambia solo la quota long dei nuovi contratti, per ora, nota alla chiusura):
- v1: 50/50 (com'è oggi).
- v2 (PRINCIPALE): quota long = quota di volume taker in acquisto dell'ora, b = media sui 5 minuti di r/(1+r) con
  r = sum_taker_long_short_vol_ratio (archivio metrics Binance USDT-M); limitata a [0,1; 0,9].
- v2k (secondaria): 0,5 + 3·(b − 0,5), limitata a [0,1; 0,9] (effetto amplificato).
- v2t (secondaria): media fra b e la quota long dei top trader per posizione, R/(1+R) con R = sum_toptrader_long_short_ratio.

**Dati reali**: liquidazioni Binance coin-margined BTCUSD_PERP (archivio liquidationSnapshot, 2023-06-25 → 2024-10-14, righe
doppie tolte, 100 $ per contratto, SELL = long liquidato); controllo extra su novembre 2026 (data/liquidations.csv OKX e
data/liq_events multi-exchange: pochi giorni, solo indicativo).
**Mappa della vigilia**: ogni giorno alle 00:00 UTC con le 504 ore precedenti (niente look-ahead), finestra ±10%.

**Misure**
- M1 (fasce dense): per lato, le 8 fasce da 0,25% con più $ stimati entro 10% (long sotto, short sopra) = "dense". Quota dei $
  liquidati realmente nel giorno successivo (long sotto il prezzo della vigilia, short sopra, entro 10%) che cade in quelle fasce.
  Media pesata sui $ e media dei giorni.
- M2 (rapporto): correlazione di Spearman fra log(short sopra / long sotto entro ±5%) previsto e log(short / long liquidati)
  realizzato nel giorno successivo e nei 3 giorni successivi; anche al netto del rendimento delle 24 ore precedenti (momentum,
  lezione 81: correlazione parziale sui ranghi).

**Criterio di adozione di v2 nel tool** (fissato ora): M1 migliora di almeno 2 punti in aggregato, per entrambi i lati e in
entrambe le metà (H1 2023-06-25 → 2024-02-15, H2 2024-02-16 → 2024-10-14), e M2 a 1 giorno non peggiora di oltre 0,02 in
nessuna metà. Le varianti secondarie si adottano solo se passano lo stesso criterio e la principale no (3 prove: dichiararlo).
Controlli descrittivi (non decidono): forma sopra/sotto rispetto ai livelli on-chain Hyperliquid (data/liqsnap) e caso del 13/11
rispetto a Coinglass.
