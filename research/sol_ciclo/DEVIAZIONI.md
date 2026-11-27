# DEVIAZIONI dal PREREG (d38c760) · fase 2

Nessuna. Varianti, criteri, soglie, periodi e verdetti applicati come scritti (`varianti.py`).

Note di esecuzione (non cambiano alcun verdetto):
- Il confronto di CAGR/DD in V3 usa i valori arrotondati a due decimali (come `w32_asset2/q6.py`). Controllo sui valori non
  arrotondati per V3a sul periodo intero: A 1,8104, B 1,8063 → "non migliora" anche così.
- V3c/V3d non calcolate perché né V1 né V2 sono operabili, come previsto dal PREREG.
- Le righe "2021–23" e "2024→" di V3 sono descrittive (il PREREG chiede intero, IS, OOS e senza il trade migliore).
