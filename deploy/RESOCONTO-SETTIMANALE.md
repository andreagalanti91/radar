# Resoconto settimanale del lunedì (attività pianificata di Claude)

Dove vive: NON è nel repository. È un'attività pianificata di Claude ("Radar Signal BTC: resoconto settimanale leggero (lunedì)",
lunedì 08:41 ora italiana) legata alla conversazione principale del progetto. Il testo si può cambiare solo da quella
conversazione: aprirla e chiedere "aggiorna il promemoria del resoconto settimanale con il testo di deploy/RESOCONTO-SETTIMANALE.md".
Al 22/11/2026 il testo attivo è ancora quello vecchio (strategia W2 + MACD, token del bot "fornito in conversazione").

Segreti: il token del bot e il chat_id stanno SOLO nei GitHub Secrets (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID). Nel testo del
promemoria non va scritto nessun token; il resoconto va su Telegram solo se la sessione ha già quelle variabili d'ambiente,
altrimenti resta in chat e in RESEARCH.md. Gli avvisi di W3.1 e il riepilogo quotidiano partono comunque dal giro orario.

## Testo aggiornato a W3.1 (da incollare)

Resoconto SETTIMANALE LEGGERO di Radar Signal BTC (lunedì dopo la chiusura settimanale). L'utente ha chiesto di PRESERVARE i
token: niente sotto-agenti, niente ricerca nuova, poche chiamate. Si opera con CAPITALE REALE su UNA sola strategia: W3.1
settimanale (radar/weekly.py; W3 dal 12/11/2026, rischio allo stop iniziale 10% dal 19/11/2026); v2 è spenta, W2 è superata.
Prima leggi memoria/01-strategia/W3.1.md e CLAUDE.md. Regola dell'utente: i risultati si riportano sempre dal 01/01/2021
(10.000 $ a 1x, DD, WR, trade) più la perdita allo stop. W3.1 non si modifica: questo resoconto è di sola lettura sulla
strategia. Repo /home/user/radar, branch predefinito del progetto. git pull --rebase (se ci sono modifiche locali ai dati:
tieni la versione del remoto; niente stash o rebase su file che un altro lavoro sta modificando).
1. Leggi data/state.json (chiavi weekly, guard, coherence), data/journal.json (trade reali registrati con /entrato /uscito)
   e, se esiste, data/provlog.csv (registro domenicale provvisori vs definitivi). Lancia
   python3 -m unittest discover -s tests -q (unittest, non pytest).
2. Stato della settimana chiusa con radar.weekly.evaluate: posizione, esposizione, trailing, eventuale nuovo segnale o uscita,
   filtro MACD (trend_age, f1_ok); soglie d'allarme (radar/guard.py: equity −15% dal massimo, 2 stop consecutivi); controlli di
   coerenza (radar/coherence.py); ultima riga del registro provvisori/definitivi (fonte okx o binance, scarti, decisione
   cambiata sì/no); confronto dei trade reali del registro con il segnale (prezzo, slippage, aderenza al piano). Se un trade
   reale chiuso è uno stop, aggiungi una riga in research/LOSERS.md.
3. UN solo resoconto "RADAR SIGNAL BTC · Settimana" (max 12 righe): prezzo BTC, W3.1 (stato, esposizione, trailing, perdita
   allo stop), risultato reale secondo il registro, 10.000 $ dal 2021 aggiornati con DD, WR e numero di trade, soglie
   d'allarme, eventuali problemi. Telegram: i segreti del bot stanno SOLO nei GitHub Secrets; non usare, cercare né chiedere
   token in conversazione (quelli vecchi non sono più validi) e non scriverne mai nel repo. Invia su Telegram solo se
   TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID sono già variabili d'ambiente della sessione; altrimenti il resoconto resta nella
   risposta in chat e in RESEARCH.md.
4. Riga breve in RESEARCH.md, sezione "Resoconti settimanali"; commit e push. Non proporre nuove ricerche se non richiesto.
