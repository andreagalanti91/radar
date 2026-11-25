# STATO · Studio notturno sulle opzioni BTC · avviato 24/11/2026 21:50 UTC · termine 25/11 07:00 UTC (8:00 italiane)

Stato: COMPLETATO (24/11/2026, 23:10 UTC) · in attesa dell'utente per le proposte

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

## Avanzamento (24/11, 22:30 UTC)
- Fase 1: motore, segnali, conteggi; ADDENDUM-1 committato da solo. FATTO.
- Dati: superficie Deribit 2018–26 da scambi veri, validata (premio −3,1% mediano sulle 23 operazioni). FATTO.
- Fase 2: cancello superato; F1–F4 eseguiti. Esito provvisorio: niente batte B0 (dal 2018 10.000 → 49.712 $, DD −12,8%);
  nessun segnale F3 utile. Bozza in `research/opzioni_studio/README.md`. FATTO, committato.
- Guida OKX: `guida/OPZIONI-OKX.md`. FATTA, committata (29 passaggi "[da verificare sull'app]").
- Revisione critica (radar-review): IN CORSO.

- Revisione critica: nessun errore di calcolo; errore di specifica su B0 (finestra 20–50 giorni) → ADDENDUM-2. FATTO.
- Secondo ciclo (B0r, prezzi veri Deribit, descrittivi per chi opera a mano) e verifica finale indipendente; 8 correzioni al
  README applicate. FATTO.
- Lezione 122 in RESEARCH.md, indici aggiornati, guida aggiornata. FATTO, committato sul branch di lavoro.

## Esito
Niente batte le 7 regole sul segnale di W3.2 (B0r: 45–48k $ dal 2018 su 10k, operazioni chiuse; perdita massima 5% per
operazione). Nessun segnale indipendente utile. Nessuna modifica al tool.

## Proposte in attesa dell'utente (nessuna applicata)
1. Riga Telegram "Opzione (su carta): …" (testi nel messaggio del 24/11).
2. Registro sulla carta del segnale F3d (compressione → straddle), solo osservazione.
3. Screenshot dell'app OKX per togliere i "[da verificare sull'app]" dalla guida.
4. Confronto dal vivo OKX contro Deribit sulle prossime operazioni (l'archivio giornaliero della catena lo consente già).

## Aggiunta dell'utente (24/11, 21:50 UTC)
"Includi anche la creazione di una guida dettagliata su come inserire operazioni su OKX." (con screenshot della catena
opzioni dell'app: `guida/img/okx-catena-opzioni.png`). Agente dedicato in corso → `guida/OPZIONI-OKX.md`; i passaggi non
verificabili vanno marcati "[da verificare sull'app]". Da committare alla consegna e includere nel riepilogo del mattino.
