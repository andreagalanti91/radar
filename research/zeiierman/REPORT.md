# Zeiierman Trend Pressure su BTC — report 13/11/2026 ore 08:00

## Conclusione
L'indicatore non migliora il trading su BTC: nessuna delle 31 regole provate (24 nel ciclo 1, 7 nel ciclo 2) batte il buy & hold
in modo affidabile, nessuna si avvicina a W3, e usarlo dentro W3 peggiora i risultati. La revisione critica conferma il verdetto.
Uso consigliato: solo contesto visivo ("quanto è esteso il prezzo nel suo range"). W3 resta invariata.

## Risultati (dal 2021, 10.000 $, leva 1x, costi e funding reali)
| Regola | Finale | Perdita max | Note |
|---|---|---|---|
| W3 (in uso) | 78.474 | −21,1% | riferimento |
| Buy & hold | 25.590 | −76,6% | |
| Compra in zona blu, vendi in rossa (con stop) | 21.137 | −54,5% | migliore del ciclo 1; perde senza i 3 trade migliori |
| Stessa regola senza stop | ~9.600 | | |
| Short in zona rossa (con stop) | 15.299 | −43,3% | funziona solo nel 2021–23 |
| Rilascio blu + trend positivo (P1) | 9.000 | −14,5% | 1 trade in 6 anni |
| Uscita al rilascio rosso, intera o a metà (P2) | 10.054–10.282 | | 1 trade: non giudicabile |
| W3 con esposizione al 50% se indicatore negativo (P3) | 72.241 | −24,2% | peggiora W3 in ogni periodo |

## Coerenza delle zone
- **Zona blu**: dura in mediana 46 giorni (max 103). Dentro, il prezzo è sceso fino a −53% (2022) e −33% (gen–apr 2026).
  A 30 giorni dall'ingresso +1,0% (media di tutti i giorni +2,5%): non anticipa i minimi.
- **Zona rossa**: dopo l'ingresso +12,5% a 60 giorni (media +5%): indica trend forte, non un massimo. Campione piccolo (19 casi).
- Gli screenshot sembrano convincenti perché si guardano gli esiti riusciti; i casi contrari (2022, inizio 2026) sono lunghi e costosi.

## Errori e correzioni
- Perdite tipiche: zona blu lunga in un ribasso (2022), rilasci falsi, mercati laterali.
- Correzione logica (filtro di trend) → quasi nessun segnale: zona blu e trend positivo non coesistono quasi mai.
- Ridurre l'esposizione di W3 in zona rossa sarebbe controproducente (la rossa precede rialzi); la variante "trend negativo"
  taglia i guadagni nelle fasi laterali (es. aprile 2025: da +11,3% a +5,8%).

## Revisione critica
Porting identico al Pine riga per riga; nessun look-ahead; W3 riprodotta esatta. Precisazioni: studio a bassa potenza (7–15 trade per
regola), quindi "nessuna evidenza di vantaggio" più che "nessun vantaggio". Unico residuo: 4h, long al rilascio blu, buono nel 2022–23,
peggiore del buy & hold dal 2024; su ~48 prove è compatibile con il caso.

## Mio giudizio
È un oscillatore ben costruito ma, nella sostanza, un Williams %R a 120 giorni smussato: dice dove sta il prezzo nel range, cioè
un'informazione di trend che W3 ha già e prima. "Compra blu, vendi rossa" compra i ribassi lunghi e vende i trend forti: l'opposto di
ciò che ha reso W3 profittevole. Non lo userei per entrare o uscire; al massimo come colpo d'occhio. Se vuoi insistere, l'unica pista
è un ciclo 3 preregistrato sul 4h quando W3 è senza posizione, con aspettative basse.

File: research/zeiierman/ (PREREG, README, risultati_ciclo1/2, codice). Lezione 91 in RESEARCH.md.
