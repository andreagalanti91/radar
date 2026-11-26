# Divergenza ribassista RSI sul dollaro · controllo descrittivo veloce · 26/11/2026

Non preregistrato: serve a rispondere a una domanda dell'utente su un grafico DXY giornaliero (massimi crescenti del prezzo,
massimi decrescenti dell'RSI). Dati: indice ampio del dollaro della Fed (FRED DTWEXBGS, giornaliero dal 2006, molto simile al
DXY; Yahoo non dava le barre giornaliere da qui), BTC da `data/spot.csv`. `python3 check.py` → `risultati.txt`.

Evento = nuovo massimo di 60 giorni del dollaro con RSI(14) almeno 2 punti sotto il massimo RSI dei 60 giorni (sopra 65);
uno ogni 30 giorni. La regola riconosce anche la divergenza del grafico (evento del 16/11/2026).

- **Sul dollaro non funziona come segnale di inversione**: dopo 50 divergenze dal 2006 il dollaro a 30 giorni sale in
  mediana (+0,3%) e scende solo nel 39% dei casi, meno di un giorno qualsiasi (50%).
- **Su BTC (16 eventi dal 2019)**: a 10–30 giorni mediana −2,5/−4,1% contro +0,7/+1,5% di un giorno qualsiasi, a 60 giorni
  +5,7% contro +4,4%. Pochi casi e segno instabile: nessun vantaggio dimostrabile.
- Correlazione settimanale dollaro–BTC: −0,22 dal 2019, −0,27 nell'ultimo anno (debole, inversa).
- Studi precedenti: dollaro e macro non migliorano W3.2 (lezioni 104, 113). Nessuna modifica a W3.2.
