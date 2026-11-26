# STATO · Piano di miglioria del 26/11 · avviato 26/11/2026

Stato: IN CORSO

## Prompt originale
"Procedi con tutto, apprendi e migliora" — sul piano `stato/PIANO-UPGRADE-26-11.md`.

## Decisioni
- A1 (dati provvisori OKX del flusso e del funding): tocca i dati con cui W3.2 decide → studio, misura dell'impatto e patch
  PROPOSTA, NON applicata: va presentata all'utente prima (CLAUDE.md).
- A2 diario operazioni vere: il bot ha già /trade, confronto e slittamento (radar/journal.py) → verifica per W3.2 + vista
  "Reale contro modello" in Movimenti.
- A3 prova Telegram: il riepilogo «Oggi» del 26/11 col nuovo formato è già partito (marker daily_brief): niente invio extra.
- A4 promemoria del lunedì: non modificabile da qui (conversazione originale) → resta all'utente.
- B1 allarme "fuori dal backtest": approvato con "tutto" (nuovo avviso Telegram).
- B2/B3: promemoria programmati (revisione semestrale, studi da rifare).
- C1 pagina più leggera, C2 legenda del Grafico: dopo B (stesso file della dashboard). C3 (vista v1) e C4 (opzioni): no.

## Prossima azione
Agenti in parallelo: A1 (research/dati_provvisori/) e A2+B1 (journal, nuovo modulo allarme, Movimenti); poi C1+C2.

## A1 (26/11)
Studio fatto: research/dati_provvisori/ (0 decisioni cambiate dai provvisori; rischio reale = funding OKX). Patch F1+P1 proposta, NON applicata: in attesa dell'ok dell'utente.
## A2+B1 (26/11)
Diario W3.2 BTC/ETH, Reale contro modello, allarme Fuori dal backtest (radar/limiti.py): suite 541, deploy fatto. Da confermare: limiti propri per ETH.

## C1+C2 e verifica (26/11, 08:33 UTC)
Pagina leggera (index 653 KB; grafico/scanner/movimenti/news.json con versione, tutti 200) e legenda su telefono: suite 554, deploy fatto. Sito: 5 pagine a 400/1280 senza errori JS né overflow, nessun messaggio "non arrivati", Movimenti con i limiti storici. In attesa dell'utente: "applica A1" e limiti di ETH.
