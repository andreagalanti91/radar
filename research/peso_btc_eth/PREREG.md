# PREREG · Peso del capitale fra BTC ed ETH con W3.2 · 25/11/2026

Scritto e committato da solo prima di qualsiasi rendimento di questo studio. **Già visto e dichiarato** (revisione critica di
`research/w32_asset2`, non preregistrato): dal 06/2020 il conto unico BTC 2/3 – ETH 1/3 ha CAGR/DD 2,62 contro 2,44 del 50/50
attuale; dal 2021 1,90 contro 1,80; dal 2023 1,21 contro 1,13. Questo studio serve a capire se quel risultato regge o è un
effetto del periodo scelto.

## Domanda
Con W3.2 invariata su ciascun asset, conviene dividere il capitale crypto in modo diverso dal 50/50 attuale (30.000 + 30.000 $)?

## Regole
- Trade di W3.2 da `radar.weekly.simulate` invariato su BTC ed ETH, dati di `research/w32_asset2/crypto/data` (gli stessi del
  ciclo 2), dal 2020-06-01 al 2026-11-24. Ogni asset ha il suo conto, come oggi.
- Pesi: BTC {50, 60, 2/3, 75, 100}% e il resto su ETH.
- Due modi: A senza ribilanciamento (capitali separati che crescono da soli, come oggi); B ribilanciamento al peso a ogni 1°
  gennaio.
- Metriche del conto unico: finale da 10.000 $, CAGR, DD giornaliero, CAGR/DD, anno peggiore.

## Scelta e giudizio
- Scelta sul solo IS 2020-06 → 2022-12: la combinazione (peso, modo) con il CAGR/DD più alto fra quelle con DD ≥ −30%.
- Il cambio si **propone** all'utente solo se, in OOS 2023-01 → 2026-11: (1) CAGR/DD della scelta > 50/50 senza ribilanciamento;
  (2) vale anche togliendo il trade migliore di BTC e quello di ETH; (3) vale per almeno 4 delle 6 date di partenza 2020-06,
  2020-09, 2021-01, 2021-06, 2022-01, 2023-01 (periodo intero fino a oggi); (4) il DD del conto unico non peggiora di oltre 3 punti.
- Altrimenti il 50/50 resta. Descrittivo: ricampionamento a blocchi dei rendimenti settimanali dei due conti (5.000 estrazioni,
  blocchi di 13 settimane) per la probabilità che la scelta batta il 50/50 su 3 anni.

## Vincoli
Nessuna modifica a `radar/weekly.py`, ai capitali (`RADAR_CAPITAL`, `RADAR_ETH_CAPITAL`) o al tool: l'esito è una proposta.
