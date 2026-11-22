# Operazioni
- daily.yml: giro orario (cron :07/:37 + avvio ogni ora dalla catena liqsnap.yml), deploy Pages con secondo tentativo, stato in data/state.json.
- liqsnap.yml: catena oraria di ~5,5 h che si riavvia (fermare con `gh workflow disable liqsnap.yml`). wallets.yml ogni 5 min.
- Segreti: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID solo in GitHub Secrets; mai nel repo né in chat.
- Server USA: Binance fapi e Bybit bloccati (451/403); usare archivio data.binance.vision, OKX, Hyperliquid.
- Aperti: attivare liqstream su VM europea (deploy/LIQSTREAM.md); dati provvisori OKX nel flusso/funding (decisione dell'utente);
  promemoria "resoconto settimanale": è un'attività pianificata di Claude (lunedì 08:41) legata alla conversazione principale, ancora
  col testo W2; il testo W3.1 senza token è pronto in deploy/RESOCONTO-SETTIMANALE.md e va applicato DA QUELLA conversazione.
- Protezioni orarie (solo avviso, W3.1 non cambia): fonti/dati vecchi e messaggio di salute (cli.py), soglie d'allarme (guard.py),
  registro provvisori/definitivi (provlog.py), controlli di coerenza dal 22/11 (coherence.py: buchi nei dati, storico riscritto,
  decisione cambiata con i definitivi), avvisi di workflow/test/push falliti (daily.yml).
- Proposte aperte dalla revisione Fable (serve approvazione): registrare ogni domenica flusso/funding provvisori vs definitivi; decisione ripartita su 7 giorni; studio dell'uscita 'distribuzione'; soglie d'allarme (equity −15%, 2 stop consecutivi). Fatto 22/11 (da pubblicare): Pre-analisi su telefono da 1.126 a 706 px. Da fare: verificare la vista Book con Binance reale dal browser dell'utente; confronto muri del book vs liquidazioni/S&R quando il registro è popolato.
