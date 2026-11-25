# Esportazione dello switch W3.2 · v1 · Confronto verso radar

Da dare alla sessione Claude Code del repo `radar`: incolla `PROMPT.md` e allega i file (o lo zip `../radar-v1.zip`).

| File | Contenuto |
|---|---|
| `PROMPT.md` | il prompt da incollare nella sessione di radar |
| `v1.py` | modulo autonomo: indicatori, voto, backtest, stato di oggi, confronto con W3.2. Prova: `python v1.py btc_giornaliero.csv` |
| `test_v1.py` | 5 test (`python -m pytest test_v1.py`) |
| `btc_giornaliero.csv` | giornaliero BTC dal 2014 con volume e funding |
| `w32_equity_2018_2026.csv`, `w32_operazioni_2018_2026.csv` | W3.2 dal 2018 usata nel confronto |
| `v1_operazioni_2018_2026.csv` | le 30 operazioni della v1 |
| `esempio_v1.json`, `esempio_confronto.json` | uscita di `evaluate()` e `confronto()` al 22/11/2026 |
| `riferimento_sezione.html` | pagina di riferimento con lo switch a tre posizioni |
| `anteprima_v1_*.png`, `anteprima_confronto_*.png` | come appare la pagina di riferimento, computer e telefono |
| `ANALISI_BTC.md`, `CONFRONTO_W32.md` | lo studio |

Rigenerare: `python backtest/build_export_v1.py` dalla radice di `teststrategy`.

Ricerca su dati storici, non una raccomandazione d'investimento.
