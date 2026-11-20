# Operazioni
- daily.yml: giro orario (cron :07/:37 + avvio ogni ora dalla catena liqsnap.yml), deploy Pages con secondo tentativo, stato in data/state.json.
- liqsnap.yml: catena oraria di ~5,5 h che si riavvia (fermare con `gh workflow disable liqsnap.yml`). wallets.yml ogni 5 min.
- Segreti: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID solo in GitHub Secrets; mai nel repo né in chat.
- Server USA: Binance fapi e Bybit bloccati (451/403); usare archivio data.binance.vision, OKX, Hyperliquid.
- Aperti: attivare liqstream su VM europea (deploy/LIQSTREAM.md); dati provvisori OKX nel flusso/funding (decisione dell'utente);
  promemoria "resoconto settimanale" ancora scritto per W2 e con vecchio token: da aggiornare.
