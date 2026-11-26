# STATO · Applicazione della variante B "Cruscotto a tessere" a tutto il tool · avviato 26/11/2026

Stato: IN CORSO

## Prompt originale
"Ottimizza la UX UI" (Oggi: posizioni in sintesi, livelli e probabilità a 30 giorni, pre-analisi; posizione aperta: quando esce
in profitto/perdita; valori ripetuti o mal organizzati) → anteprime A/B/C → scelta "Cruscotto a tessere"; "Per ogni card voglio
link Dettagli ›"; anteprime di tutte le pagine (stato/ux-varianti/B/) → "Procedi".

## Decisioni (proposte accettate con "Procedi")
- Variante B su tutte le pagine; "Dettagli ›" su ogni tessera (pannello dal basso su telefono, a destra su desktop, con i <dialog> già esistenti).
- Mercato power: 6 semafori in Oggi, regole scritte in un modulo (radar/mercato.py) e registro giornaliero per verifiche future; nessun punteggio unico; non entra in W3.2.
- Long/short come pillola neutra; candele grigie; verde/rosso solo profitto/perdita e semafori.
- Scanner: tabella con "altre monete" prima, filtro "Tutte" a un tocco. Oggi su desktop ~1.170 px (contesto e notizie restano).
- TRX e scommesse sulla carta restano. Pagine spente (Book, Wallet, Liquidazioni, Opzioni) restano spente.
- W3.2, dati e numeri invariati: nessuna informazione operativa tolta (al massimo dentro Dettagli ›).

## Prossima azione
Agente (Opus 5.5 medium) sull'intera implementazione; poi suite, render, deploy, verifica.
