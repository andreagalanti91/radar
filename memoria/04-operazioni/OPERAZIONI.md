# Operazioni
- daily.yml: giro orario (cron :07/:37 + avvio ogni ora dalla catena liqsnap.yml), deploy Pages con secondo tentativo, stato in data/state.json.
- liqsnap.yml: catena oraria di ~5,5 h che si riavvia (fermare con `gh workflow disable liqsnap.yml`). wallets.yml ogni 5 min.
- Segreti: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID solo in GitHub Secrets; mai nel repo né in chat.
- Server USA: Binance fapi e Bybit bloccati (451/403); usare archivio data.binance.vision, OKX, Hyperliquid.
- Aperti: attivare liqstream su VM europea (deploy/LIQSTREAM.md); dati provvisori OKX nel flusso/funding (decisione dell'utente);
  promemoria "resoconto settimanale" ancora scritto per W2 e con vecchio token: da aggiornare.
- Proposte aperte dalla revisione Fable (serve approvazione): registrare ogni domenica flusso/funding provvisori vs definitivi; decisione ripartita su 7 giorni; studio dell'uscita 'distribuzione'; soglie d'allarme (equity −15%, 2 stop consecutivi). Da fare: accorciare la Pre-analisi su telefono; verificare la vista Book con Binance reale dal browser dell'utente; confronto muri del book vs liquidazioni/S&R quando il registro è popolato.
