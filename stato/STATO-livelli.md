# Stato — Card unica "Livelli e probabilità a 30 giorni" in Oggi

**Stato:** IN CORSO · 24/11/2026 · Opus 5.5 medium (regia), agente radar-ui

## Prompt originale
> Prompt allegato (research/livelli_import/PROMPT.md): sezione "Livelli" in Oggi — mappa di supporti, resistenze, medie, Fibonacci,
> liquidazioni e zone di confluenza da livelli.py (repo teststrategy), contesto e non segnale; una sola mappa; test; render; deploy.
> Poi: "Nel radar in oggi ho già una card dove abbiamo la probabilità che il prezzo tocchi determinati prezzi. Andrei a sostituire o
> fare merge valuta te, con questi livelli." · "Ok mi torna, valuta te la migliore soluzione. Procedi"

## Decisioni
- Definizione A: livelli del nuovo modulo come unica mappa (anche "Livelli vicini" in Grafico). Differenza con radar/levels.py
  mostrata all'utente prima (resistenze 65–70k e 72–76k del vecchio calcolo spariscono perché rotte in chiusura).
- Unione con la card del cono: una card "Livelli e probabilità a 30 giorni" al posto di "Fra 30 giorni", prima di Contesto;
  probabilità di tocco del cono (radar/cone.py, invariato) applicate a ogni livello e zona; grafico e note nei Dettagli.
- Test in unittest (pytest non installato). W3.2 intatta; nessun avviso Telegram nuovo.
- File originali copiati in research/livelli_import/ (fonte, riproducibilità).

## Piano
- [x] 1. radar/livelli.py, report["livelli"], card unica in Oggi, Livelli vicini/S-R del Grafico/Liquidazioni sulla nuova mappa, 22 test (381 totali verdi), render 360/400/1280
  Restano su radar/levels.py: liqmap (confluenza), liqcascade, preview sr_rows (Pre-analisi in Posizioni + Telegram), cone.pick_levels
- [ ] 2. Regia: commit, deploy, verifica sul sito   ← IN CORSO

## Come riprendere
**Prossima azione:** attendere l'agente; poi suite, render, deploy.
