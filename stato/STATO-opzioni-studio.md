# STATO · Studio notturno sulle opzioni BTC · avviato 24/11/2026 21:50 UTC · termine 25/11 07:00 UTC (8:00 italiane)

Stato: IN CORSO

## Prompt originale (per intero)
"Avvia un ciclo di studio e approfondimento sulle opzioni BTC. Analizza con ciclo di auto-apprendimento notturno (fino alle
8.00) la strategia migliore per le opzioni. Backtesta sempre la strategia dal 2018 su BTC. Voglio segnali per operare sulle
opzioni BTC, trova coerenza, analizza tutti i dati in tuo possesso. Avvia ciclo notturno, organizza te."

## Decisioni
- "Avvia… organizza te" letto come comando d'avvio con piena autonomia (l'utente dorme: niente attesa di "procedi").
- Agenti: Opus 5.5, effort medium. Solo ricerca in `research/opzioni_studio/`; nessuna modifica a tool, W3.2, 7 regole, Telegram.
- Deribit (API pubblica, storico scambi dal 2018 con volatilità implicita) è raggiungibile dal contenitore: prezzi veri.

## Piano
1. PREREG committato da solo (`research/opzioni_studio/PREREG.md`). FATTO.
2. In parallelo: agente dati (superficie di volatilità giornaliera Deribit 2018–26, modulo `superficie.py`) e agente
   ricerca (motore, catalogo dei segnali F3, conteggi senza rendimenti).
3. Addendum al PREREG con i parametri di F3 fissati sui conteggi; poi esecuzione F1–F4.
4. Revisione critica (radar-review). 5. Eventuale secondo ciclo. 6. README con verdetto, lezione in RESEARCH.md, indici,
   commit e push sul branch di lavoro, riepilogo all'utente entro le 07:00 UTC.

## Prossima azione
Fase 1 del motore consegnata e committata; ADDENDUM-1 committato. Attendere l'agente dati (superficie Deribit), poi riprova del motore sulle 23 operazioni con superficie.py ed esecuzione F1–F4 (agente ricerca), poi revisione critica.
