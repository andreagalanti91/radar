# Modello del file di stato

Copia questa struttura in `STATO-<argomento>.md` e tienila aggiornata. Sostituisci tutto ciò che è tra `< >`.

```markdown
# Stato — <titolo del lavoro>

**Stato:** IN CORSO            <!-- IN CORSO | IN ATTESA DELL'UTENTE | COMPLETATO -->
**Ultimo aggiornamento:** <AAAA-MM-GG HH:MM>
**Modello / effort usati:** <es. Sonnet · medium>

## Prompt originale
> <il prompt dell'utente, riportato PER INTERO, con eventuali allegati descritti>

## Scelte dell'utente
- Sottoagenti: <sì/no, quali fasi>
- Autonomia: <es. punto 1 = A, punto 2 = B>
- Altre risposte date nella scheda di avvio: <...>

## Piano
- [x] 1. <fase> — <risultato in una riga>
- [ ] 2. <fase>   ← IN CORSO
- [ ] 3. <fase>

## Risultati e file prodotti
- Step 1: <cosa è stato fatto, numeri/risultati chiave>
  - `<percorso/file>` — <cosa contiene>

## Decisioni prese
- <decisione> — <motivo> (<presa da me in autonomia | indicata dall'utente>)

## Problemi aperti
- <problema, cosa è stato provato, cosa manca>

## Come riprendere
**Prossima azione:** <azione precisa e concreta, es. "scrivere la sezione 3 di `report.md` usando i dati in `dati/vendite.csv`">
<Eventuali avvertenze: comandi da rilanciare, file da non toccare, domande in attesa di risposta.>
```

## Buone pratiche

- Aggiorna lo stato **prima** di passare allo step successivo.
- Nei risultati scrivi l'essenziale, non copiare interi output: i dettagli stanno nei file prodotti.
- Se aspetti una risposta dell'utente, imposta lo stato su **IN ATTESA DELL'UTENTE** e scrivi la domanda in "Come riprendere".
- A lavoro finito: **Stato: COMPLETATO**, un riepilogo finale in "Risultati", e non cancellare il file.
