# STATO · Avviso VIX nel bot · avviato 25/11/2026

Stato: COMPLETATO (25/11/2026)

## Prompt originale
"Implementa nel bot: VIX > 30 alert Buy; VIX < 15 alert Sell. Ogni quanto conviene fare un check per dare alert?"

## Decisioni
- CORREZIONE DELL'UTENTE (25/11): "Ok produci questo alert, mi serve per capire la condizione di mercato. Fai check ogni 4h però."
  → controllo ogni 4 ore (00, 04, 08, 12, 16, 20 UTC) sull'ultimo valore del VIX (Yahoo ^VIX, ripiego FRED VIXCLS); avviso solo all'attraversamento, con riarmo (sopra 30 → riarmo sotto 25; sotto 15 → riarmo
  sopra 17): nessun avviso ripetuto ogni giorno.
- Etichette come chieste dall'utente (Buy / Sell), con una riga di dati storici onesta (research/vix_alert/README.md: il "sell"
  sotto 15 storicamente non ha funzionato sulle azioni).
- Primo avvio: si invia UNA volta lo stato attuale della condizione di mercato (l'utente vuole l'avviso), poi solo attraversamenti.
- Riga del VIX nel riepilogo «Oggi»? Solo se già presente il contesto macro; nessun altro messaggio nuovo.

## Prossima azione
Agente (Opus 5.5 medium): radar/vix.py, aggancio in cli.py, testo Telegram nel nuovo formato, stato in data/state.json, test;
poi suite, deploy, verifica.

## Deploy e verifica (25/11, 17:08 UTC)
Agganciato in cli.py dopo le soglie ETH; giro 510 riuscito; state["vix"] creato: zona alta, VIX 33,66 (Yahoo), messaggio iniziale inviato e confermato (marcatore scritto solo a invio riuscito); prossimo controllo nella fascia delle 20 UTC; Buy riarmato solo dopo un ritorno sotto 25. FATTO.
