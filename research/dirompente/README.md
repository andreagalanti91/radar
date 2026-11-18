# Pensiero dirompente su W3 — 18/11/2026 (avvocato del diavolo, sola lettura; script a1–a4.py)
Conclusione: nessun bug, ma un problema serio di dimensione della posizione e di comunicazione.
1. Rischio allo stop iniziale 25% della quota in 11/14 trade dal 2021 (minimo 17,9%): 1 stop −25%, 2 consecutivi −44%, 3 −58%.
   Il vincolo dichiarato (DD ≤ 15–20%) è violato. Stessa logica a rischio minore, dal 2021: 5% → 16,8k (DD −5,4%), 10% → 27,2k
   (−9,8%), 15% → 42,8k (−13,9%), 25% → 78,8k (−21,1%); 2018–20 DD −10,7/−19/−26/−37%. CAGR/DD quasi uguale (1,7–2,0): il 25%
   aggiunge leva, non efficienza. Il "MAR" di metrics() è rendimento totale/DD e cresce con il rischio (fuorviante).
2. Short: 6 chiusi 2018–26, media +4,3%, dev. 12,1, t 0,87; peggiore −17,9%, migliore +16,7%. Oggi rischio allo stop 25,2%.
3. Dipendenza: dal 2021 ×7,88; senza il migliore ×5,18, senza i 2 migliori ×3,64, senza i 3 migliori ×2,59 (54% del log-rendimento).
   2018–20 ×2,51, senza i 3 migliori ×0,78.
4. Selezione: >15.000 configurazioni provate nel progetto; Sharpe settimanale 1,23 (2021+); Deflated Sharpe 0,98 (prove simili) →
   0,28–0,47 (100–300 prove indipendenti). Lezione 58: SPA vs buy&hold p 0,44.
5. 2018–20: pf14z reale solo dal 12/04/2020 (prima proxy CVD spot), funding dal 01/2020.
6. Bootstrap dei trade: CAGR 5–95% 25–68% (2021+), 15–58% (2018–26). Dal 01/2025 ×1,15 in 22 mesi; 2019-07→2020-09 −7,2%.
7. Operativi: slippage 0,5% → 72,1k, 1% → 64,5k; gap oltre lo stop sul perp non modellati; dati provvisori OKX da quantificare.
8. Comunicazione: 78k = massimo dei 7 giorni (mediana 62,7k); WR 92% su 13 trade (76% sul 2018–26); DD −21% < perdita di uno stop.
Proposte: rischio allo stop 10–15%; per lo short aperto esposizione dimezzata (decisione dell'utente); comunicare attesa CAGR
25–35%, DD probabile −30/−40%, perdita per stop; soglie d'allarme preregistrate (equity −30%, 2 stop consecutivi, 18 mesi senza
nuovo massimo, CAGR 24 mesi < 10%); CAGR/DD accanto al "MAR".
