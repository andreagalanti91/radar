# Censimento fonti di liquidazioni BTC (gratuite, pubbliche) — verificato 2026-11-11

Legenda raggiungibilità: **SB** = da questo sandbox; **US** = probabile da runner GitHub negli USA.
Tipo: **E** = eventi reali di liquidazione, **A** = aggregati, **P** = posizioni.

| Fonte | Endpoint | Tipo | Storico | Auth / limiti | SB | US | Stato nel radar |
|---|---|---|---|---|---|---|---|
| OKX | `/api/v5/public/liquidation-orders` (paginazione `after`) | E | < 24 h (oltre: vuoto) | nessuna, 20 req/2 s | sì | sì | **raccolta** (`liquidations.csv` + `liq_events/`, paginata fino all'ultimo evento salvato) |
| Gate.io | `/api/v4/futures/usdt/liq_orders` (`from/to` max 1 h) | E | finestre di 1 h, poche ore | nessuna, ~200 req/10 s | sì | sì | **raccolta** (ultime 3 h, 3 chiamate) |
| Deribit | `public/get_last_trades_by_instrument_and_time` campo `liquidation` (M/T/MT) | E | giorni (paginato) | nessuna, limite a crediti | sì | sì | **raccolta** (ultime 2 h, BTC-PERPETUAL) |
| Kraken Futures | `/derivatives/api/v3/history?symbol=PF_XBTUSD` `type=liquidation` | E | solo ultimi 100 trade | nessuna | sì | sì | **raccolta** (copertura scarsa: finestra di minuti) |
| dYdX v4 indexer | `/v4/trades/perpetualMarket/BTC-USD` `type=LIQUIDATED` | E | ultimi 1000 trade (~1 giorno) | nessuna | lento (timeout a volte) | sì | **raccolta** |
| Lighter | `/api/v1/recentTrades?market_id=1` (`type` liquidation) | E | ultimi 100 trade | nessuna | sì | sì | **raccolta** (raramente presenti) |
| Hyperliquid | `info` `recentTrades` | — | ultimi trade, senza flag liquidazione | nessuna | sì | sì | escluso come eventi; posizioni già in `liqsnap` (P) |
| Binance | WS `!forceOrder@arr` (1 evento/s per simbolo, snapshot) | E | nessuno | nessuna | no (451) | **no** | solo browser live (Italia) |
| Binance | REST `allForceOrders` | E | — | dismesso (2021) / 451 | no | no | escluso |
| data.binance.vision | elenco `futures/um/daily/` | — | nessun dataset liquidazioni (`liquidationSnapshot` non più pubblicato) | — | sì | sì | escluso; `metrics` dà OI e long/short (A) |
| Bybit | WS `allLiquidation.BTCUSDT` | E | nessuno | nessuna | no (403 CloudFront) | **no** | solo browser live |
| Bitget | nessun endpoint pubblico di liquidazioni (404); OI pubblico | A | — | — | sì | sì | escluso (solo OI) |
| BitMEX | `/api/v1/liquidation` (ordini di liquidazione attivi) | E | solo attivi | nessuna | no (403 CloudFront) | incerto | escluso per ora |
| Coinglass, Kaiko, CryptoQuant, Hyperdash | — | A | — | a pagamento / termini | — | — | esclusi per regola |

## Proxy (aggregati, non eventi)
- Open interest: OKX `public/open-interest`, Bitget `mix/market/open-interest`, Deribit `get_book_summary_by_currency`, Hyperliquid `metaAndAssetCtxs`, data.binance.vision `metrics` (OI + long/short top trader, giornaliero). Un calo brusco di OI con prezzo in forte movimento è il miglior sostituto delle liquidazioni Binance/Bybit.
- Long/short: OKX `rubik/stat/contracts/long-short-account-ratio`, Binance vision `metrics`.

## Note
- Binance e Bybit sono la quota maggiore delle liquidazioni globali ma non sono raggiungibili via REST dagli USA: i totali del radar sono **parziali** (OKX+Gate+Deribit+Kraken+dYdX+Lighter).
- File: `data/liq_events/YYYY-MM.csv` (ts ms UTC, exchange, id, side = lato liquidato, price, btc, usd), `data/liq_events/coverage.csv` (esito per fonte a ogni giro).
