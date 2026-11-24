# STATO · Sezione Opzioni (su carta) · avviato 24/11/2026

Stato: IN DEPLOY

## Richiesta
Sezione "Opzioni" dal modulo dell'utente (`research/opzioni_import/`, specifica in `PROMPT.md`), come voce di menu separata;
spesa per operazione 1.500/2.000 $; simulazione della spesa con budget 50.000 $ dal 2021.

## Fatto
- File dell'utente copiati in `research/opzioni_import/`.
- Simulazione: `research/opzioni_sim/` (README con verdetto, `sim.py`, `risultati.md`).

## Fatto dall'agente (425 test verdi, render 400/1280 chiaro e scuro)
- Agente (Opus 5.5 medium): `radar/opzioni.py`, `tests/test_opzioni.py`, `data/opzioni_carta.json`, `data/opzioni/`, aggancio
  `_soft` in `radar/cli.py`, pagina Opzioni + riga in Oggi, `RADAR_OPZIONI_QUOTA` nel workflow, render 400/1280.

## Da fare
- Suite completa, commit, deploy (procedura standard), verifica sul sito.
- Mostrare all'utente il testo Telegram proposto (NON attivarlo).

## Vincoli
Solo BTC, su carta, nessun ordine, nessuna chiave API, le 7 regole non si cambiano, W3.2 non si tocca.
