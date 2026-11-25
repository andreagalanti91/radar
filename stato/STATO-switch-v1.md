# STATO · Strategia v1 (voto di 17 indicatori): confronto con W3.2, poi eventuale switch · avviato 25/11/2026

Stato: IN ATTESA DELL'UTENTE (confronto fatto; switch solo se l'utente lo vuole come confronto informativo)

## Prompt originale
Prompt completo dell'utente in `research/v1_confronto/import/PROMPT_utente.md` (file allegati nella stessa cartella).
Messaggi: "Aggiornamento del tool con versione strategia mediante switch. Rendi anche la card ciclo on chain più chiara con meno
informazioni. Al tap inserisci lì tutte le informazioni con ux ui chiara. Suddividi bene le informazioni. Utilizza grafici ed
elementi più visivi per la facile comprensione. Meno testi." Poi: "Ok mi torna tutto. La W3.2 non la toccare. Prima di fare le
modifiche compara la nuova strategia, dimmi se vale la pena fare la modifica oppure è meglio la nostra W3.2. Ok per la card on
chain." Poi "Procedi".

## Decisioni
- W3.2 non si tocca. Le regole della v1 non si ottimizzano.
- Fase 1: confronto indipendente v1 contro W3.2 (research/v1_confronto/); lo switch nel tool si costruisce SOLO dopo il verdetto
  e l'ok dell'utente.
- In parallelo: riprogetto della scheda Ciclo on-chain (chiusa = stato + termometro + una riga; al tocco = pannello a sezioni).
- Se W3.2 dal 2018 non torna con i 209.002 $ dell'utente: fermarsi e spiegare (autonomia B).

## Prossima azione
Due agenti (Opus 5.5 medium): confronto v1 (research/v1_confronto/) e scheda on-chain (radar/onchain.py, template, test).

## Confronto fatto (25/11)
research/v1_confronto/README.md: v1 riprodotta (184.406 $, 30 op.) anche con i dati di Radar; W3.2 dal 2018 241.439 $ (Radar) contro 212.098 $ (utente: chiusura d'ufficio del long al 31/12/2020); 2022–26 W3.2 43.970 $ DD −21,1% contro v1 21.826 $ DD −34,3%; 50/50 peggiora. Verdetto: v1 non operativa né affiancata; al massimo confronto informativo. Revisione critica separata non eseguita (nessuna variante promossa). Lezione 126.
