# STATO · Avviso VIX nel bot · avviato 25/11/2026

Stato: IN CORSO (in coda dopo l'agente dello Scanner: tocca radar/cli.py)

## Prompt originale
"Implementa nel bot: VIX > 30 alert Buy; VIX < 15 alert Sell. Ogni quanto conviene fare un check per dare alert?"

## Decisioni
- Controllo una volta al giorno sulla CHIUSURA ufficiale del VIX (fonte: Yahoo ^VIX, ripiego FRED VIXCLS), nel primo giro
  orario dopo la chiusura USA; avviso solo all'attraversamento, con riarmo (sopra 30 → riarmo sotto 25; sotto 15 → riarmo
  sopra 17): nessun avviso ripetuto ogni giorno.
- Etichette come chieste dall'utente (Buy / Sell), con una riga di dati storici onesta (research/vix_alert/README.md: il "sell"
  sotto 15 storicamente non ha funzionato sulle azioni).
- Primo avvio: si registra lo stato attuale senza inviare (il VIX ha già chiuso sopra 30 il 20/11: l'utente lo sa dalla chat).
- Riga del VIX nel riepilogo «Oggi»? Solo se già presente il contesto macro; nessun altro messaggio nuovo.

## Prossima azione
Agente (Opus 5.5 medium): radar/vix.py, aggancio in cli.py, testo Telegram nel nuovo formato, stato in data/state.json, test;
poi suite, deploy, verifica.
