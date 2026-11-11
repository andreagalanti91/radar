# Lezione dal trade perso 24/08 → 09/11/2026 (−4,1%) — preregistrazione (12/11/2026)

Diagnosi: ingresso dopo UNA sola settimana esplosiva (+23,6%, da 62,9k a 77,7k: da −8,6% sotto la EMA21 a +11,7% sopra, trend di
1 settimana, MACD ancora sotto zero). Dopo l'ingresso il flusso perp è stato NEGATIVO per 10 settimane di fila (da −0,3 a −1,6)
mentre il prezzo saliva fino a +11,3%: nessuno comprava davvero, ma l'uscita "distribuzione" non è scattata perché il funding era
freddo. Il guadagno massimo (+11%) era metà del rischio iniziale (stop a −21%), quindi il trailing non poteva proteggerlo.

Regole candidate (giudicate su TUTTO lo storico, non su questo trade):
- P1 "non inseguire": niente ingresso se la settimana del segnale ha fatto più di k ATR (k = 1,5 · 2 · 2,5).
- P2 "flusso persistente contro": uscita se il flusso settimanale è negativo (per i long) per n settimane di fila (n = 2 · 3 · 4).
- P3 "pareggio": dopo un guadagno di m ATR settimanali dal prezzo d'ingresso, lo stop sale all'ingresso (m = 1 · 1,5 · 2).
Base: W3 (in uso). Periodi: 2021→oggi e 2018–20 (flusso stimato). Una regola si adotta solo se migliora (o non peggiora)
ENTRAMBI i periodi, cambia più di 1 trade e la mediana dei suoi 3 valori fa lo stesso. Altrimenti si annota e non si cambia nulla.

## Risultato (12/11/2026)
| Regola | 2021→oggi | DD | trade cambiati | 2018–20 | DD | trade ago 2026 |
|---|---|---|---|---|---|---|
| W3 (base) | 78.474 | −21,1% | – | 25.142 | −37,3% | −4,1% |
| P1 non inseguire k=1,5 / 2 / 2,5 | 72.742 / 78.527 / 78.474 | −21,1% | 4 / 2 / 0 | 21.137 / 25.142 / 25.142 | −33,9 / −37,3 / −37,3% | evitato / evitato / −4,1% |
| P2 flusso contro n=2 / 3 / 4 | 44.726 / 64.837 / 55.057 | −33 / −29 / −25% | 36 / 31 / 24 | 25.726 / 23.667 / 24.942 | −37,3% | −1,5% / +4,0% / +8,2% |
| P3 pareggio m=1 / 1,5 / 2 | 78.345 / 75.211 / 78.474 | −21,1% | 4 / 2 / 0 | 19.918 / 20.054 / 25.142 | −37,3% | −0,1% / −4,1% / −4,1% |
Nessuna regola passa: P1 con k=2 evita il trade e non costa nulla, ma cambia solo questo trade e i vicini (1,5 / 2,5) peggiorano o
non cambiano nulla: è la correzione "su misura" di un solo caso (lezione 3). P2 avrebbe trasformato questo trade in un guadagno ma
taglia i grandi trend (−14/−34k dal 2021): il flusso negativo con prezzo in salita è normale nei rialzi. P3 salva il trade ma costa
il 21% nel 2018–20. Decisione: nessuna modifica alle regole; la perdita (−4,1% con rischio iniziale del 21%) è il costo normale.
