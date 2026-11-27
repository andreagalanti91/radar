# macd_sol · deviazioni ed esplicitazioni tecniche rispetto a PREREG.md (commit a5f2206)
Nessuna soglia, variante o criterio cambiato. Punti che il PREREG non specificava e come sono stati risolti in `fase2.py`:
1. **Inizio del periodo intero**: la corsa parte il 06/12/2020 (domenica della prima decisione) per poter eseguire il lunedì
   07/12/2020; il conto resta flat fino all'esecuzione. Il B&H parte all'open del 07/12/2020. Nessun segnale cade in dicembre 2020.
2. **Trade**: il conteggio "trade" include la posizione aperta a fine dati (come sol_ciclo); il WR è solo sulle chiuse.
3. **Senza il trade migliore**: prodotto dei risultati di tutti i trade (aperta valutata alla close del 24/11/2026 con costi di
   uscita) togliendo il migliore (= `lib.met`). Il "conto dopo" nella lista dell'aperta include i costi d'uscita: differisce di
   pochi dollari dal capitale finale della curva (che non li sottrae).
4. **Placebo R e candidato B**: durate arrotondate per eccesso a settimane intere, uscita all'open del lunedì (o alla close finale);
   stessa esposizione e stesso lato del trade reale; costi 0,2% per lato. p = (n. prove ≥ reale + 1) / (2.000 + 1).
5. **Placebo innesti**: W-F = blocco casuale degli ingressi per tutta la durata di k trade base scelti a caso (k = trade base che
   spariscono con il filtro); W-U = uscita forzata a una domenica casuale dentro k trade base (k = uscite "dist" in più rispetto
   alla base). Statistica: CAGR/DD. Se l'innesto è identico alla base (W-U% su tutti gli asset) p = 1 senza simulazione.
6. **IS/OOS degli innesti su BTC/ETH**: corse separate che partono flat il 01/01/2021 (BTC) o 11/01/2021 (ETH) fino al 31/12/2022 e
   dal 01/01/2023 alla fine dei dati, come scritto nel PREREG.
7. **Candidato B, parità e "≥ 1 trade in IS"**: nessuna parità. C3 escluso perché DD IS −35,2% < −35% (regola applicata alla lettera).
8. **Descrittivo extra** (`descrittivi.py`, fuori dal giudizio): C1 e C3 in OOS e dal 2021, solo per trasparenza.
