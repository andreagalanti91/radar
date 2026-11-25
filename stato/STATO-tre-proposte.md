# STATO · Tre proposte del ciclo 2 approvate · avviato 25/11/2026

Stato: COMPLETATO (25/11/2026, 12:30 UTC)

## Prompt originale
"Ok procedi tutto" — riferito alle tre decisioni proposte dopo il ciclo 2 (research/w32_asset2/README.md):
1. TRX con il cancello di BTC in osservazione sulla carta, come riga nel tool;
2. studio preregistrato sul peso BTC/ETH (2/3–1/3 contro 50/50);
3. pagina informativa del motore di ricerca settimanale (scanner).

## Decisioni
- TRX: regole fissate in `research/w32_asset2/OSSERVAZIONE-TRX.md`; solo carta, niente Telegram.
- Scanner e TRX in un'unica pagina "Scanner" del tool (informativa), dati grezzi fuori da git, solo il risultato compatto in data/.
- Peso BTC/ETH: `research/peso_btc_eth/PREREG.md`; l'esito è solo una proposta (capitali invariati).
- Agenti Opus 5.5 medium: uno per il tool (radar/, tests/, data/, dashboard), uno per lo studio (research/peso_btc_eth/).

## Avanzamento
- Studio peso BTC/ETH: fatto, revisionato, lezione 124. Esito: 50/50 resta; 2/3–1/3 solo come preferenza dell'utente. FATTO.
- Pagina Scanner + TRX sulla carta: suite 443 test verde, render 400/1280, deploy e verifica sul sito (giro 504 ok, passo daily 33 s, 0 errori JS, nessun overflow). FATTO.
- Cache dei dati grezzi dello scanner: al primo giro non salvata (nessun ricalcolo necessario nella stessa settimana/giorno); si popola al prossimo ricalcolo (TRX domani, scanner domenica). Da controllare lunedì.

## Prossima azione
Nessuna. Lunedì 30/11: verificare che il giro della domenica abbia ricalcolato lo scanner e salvato la cache.
