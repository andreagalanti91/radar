# Esportazione della sezione "Opzioni" verso radar

Da dare alla sessione Claude Code del repo `radar`: incolla `PROMPT.md` e allega i file (o lo zip `../radar-opzioni.zip`).

| File | Contenuto |
|---|---|
| `PROMPT.md` | il prompt da incollare nella sessione di radar |
| `opzioni.py` | modulo autonomo: catena OKX, scelta del contratto, quantità, registro su carta, `build()` per la dashboard. Prova: `python opzioni.py catena_2026-11-24.csv.gz registro_iniziale.json` |
| `test_opzioni.py` | 6 test (`python -m pytest test_opzioni.py`) |
| `catena_2026-11-24.csv.gz` | catena OKX delle opzioni su BTC del 24/11/2026, 17:39 UTC |
| `esempio_sezione.json` | uscita di `build()` oggi: W3.2 short dal 16/11, put 65.000 con scadenza 11/12 aperta |
| `esempio_segnale.json`, `esempio_attesa.json` | uscita di `build()` nel giorno di un segnale e senza segnale |
| `registro_iniziale.json` | riga di partenza del registro per la posizione attuale (capitale d'esempio 45.000 $) |
| `storico_prezzi_veri.json`, `.csv` | le 23 operazioni di W3.2 dal 2018 rifatte con gli scambi veri di Deribit |
| `riferimento_sezione.html` | pagina di riferimento della sezione, nei due stati |
| `anteprima_desktop.png`, `anteprima_telefono.png` | come appare la pagina di riferimento |
| `fetch_okx_options.py` | script che salva la catena completa e lo storico dei contratti vivi |
| `OPZIONI_W32.md`, `opzioni_w32.png` | lo studio completo |

Rigenerare i dati: `python backtest/build_export_opzioni.py` dalla radice di `teststrategy`.

Ricerca su dati storici, non una raccomandazione d'investimento.
