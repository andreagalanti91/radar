# Deviazioni dal PREREG (commit ba77738)

Nessuna deviazione sostanziale: definizioni, parametri, vicini, periodi, criteri e Holm sono quelli del PREREG. Restano da
dichiarare tre precisazioni di esecuzione, decise prima di guardare i rendimenti:

1. **Placebo.** La serie giornaliera di s copre dal 01/01/2016 al 30/11/2026 (569 settimane). Lo slittamento circolare è di 7·k
   giorni, con k da 26 a 543: 518 slittamenti. La statistica è il CAGR/DD insieme dal 11/01/2021.
2. **BTC nella colonna "insieme".** BTC parte da flat il 11/01/2021 sul frame del tool, come ETH: capitali separati da
   10.000 $ ciascuno, come prevede il PREREG §4. Il "BTC dal 2021" delle tabelle parte invece il 01/01/2021 (84.820 $).
3. **Metriche.** Il DD è calcolato sulla chiusura giornaliera, con il massimo di partenza uguale al capitale iniziale (come in
   `w32_ufficiale`). Il WR è quello delle operazioni chiuse. Il conteggio "op." include la posizione aperta, e il calcolo
   "senza la migliore" include la posizione aperta valutata all'ultima chiusura.

Scanner altcoin non eseguito: nessuna variante passa su BTC/ETH (PREREG §5).
