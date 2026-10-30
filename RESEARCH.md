# Diario di ricerca

Ciclo di miglioramento automatico (ogni ora). Ogni iterazione prova un'idea, la valuta con
`python -m radar.research` e la promuove solo se supera il gate in `radar/research.py`:

- aspettativa nel test (2024–oggi) migliore della versione attuale
- non peggiora troppo nel training (2022–23): altrimenti è rumore
- win rate test non più basso di 2 punti, max drawdown non peggiore di 3 punti
- rendimento totale almeno +5%
- almeno l'80% dei trade attuali
- robustezza: tutte le varianti vicine dei parametri in profitto e con win rate ≥ 70%

Regole operative: nessuna promozione mentre un trade è aperto; al massimo una promozione al giorno;
ogni promozione viene annunciata su Telegram e annotata qui.

## Baseline v2 (30/10/2026)
47 trade futures da mar 2022, win rate 89,4%, +157% a 1x, max DD −16,4%. Test 2024–26: 27 trade, 88,9%, aspettativa +2,19%.

## Iterazioni
