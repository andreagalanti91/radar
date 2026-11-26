# STATO · Controllo "Dollaro" accanto alla posizione · avviato 26/11/2026

Stato: IN CORSO

## Prompt originale
"Ok inseriscilo nella strategia come ulteriore controllo per decidere delle posizioni" (dopo l'analisi della divergenza RSI
sul dollaro, research/dxy_divergenza).

## Decisioni
- Interpretato come: controllo del dollaro (DXY). Come regola automatica di W3.2 no (nessun vantaggio dimostrato: lezioni 104,
  113, research/dxy_divergenza): W3.2 non si tocca. Inserito come controllo di supporto alla decisione nella pagina Posizioni,
  accanto alla posizione aperta (come la scheda Ciclo on-chain). Nessun avviso Telegram nuovo.

## Prossima azione
Agente: modulo dati dollaro + scheda + test + render; poi suite, deploy, verifica.

## Fatto dall'agente (26/11/2026)
- radar/dollaro.py (Yahoo DX-Y.NYB query1→query2 con User-Agent, ripiego FRED DTWEXBGS, poi data/dollaro.csv), _soft in cli.py,
  scheda dxBox/dxSec + pannello nel template, tests/test_dollaro.py (21 test). Suite 585 OK. Render in scratchpad/dollaro_render.
- Da fare: deploy e verifica sul sito (non eseguiti: niente commit né push).
