# VIX > 30 "buy", VIX < 15 "sell" · controllo descrittivo veloce · 25/11/2026

Non preregistrato, solo per tarare l'avviso richiesto dall'utente (nessuna regola di W3.2 cambia). Eventi = prima chiusura
giornaliera del VIX oltre la soglia, con riarmo (sopra 30 → si riarma sotto 25; sotto 15 → si riarma sopra 17). Rendimenti
successivi mediani e quota positiva contro tutti i giorni. `python3 check.py` → `risultati.txt`.

- **VIX > 30**: dal 1990 43 eventi; S&P 500 +2,5% a 30 giorni (contro +1,2% di un giorno qualsiasi), +5,5% a 90 (contro +3,1%).
  BTC dal 2019 (13 eventi utili): +4,0% a 30 giorni contro +1,5%, ma a 90 giorni +4,3% contro +6,2%: misto. Segnale debole ma
  nella direzione giusta per le azioni.
- **VIX < 15**: dal 1990 87 eventi; S&P 500 +6,2% a 180 giorni con il 76% di casi positivi (contro +5,6% e 74%): **dopo un VIX
  basso il mercato ha continuato a salire**. Come "sell" non funziona; su BTC −3,4% a 90 giorni contro +6,2%, ma con pochi casi.
- Studi precedenti: EMA200D + VIX (research/multi_asset, lezione 104): l'aggiunta del VIX non è dimostrata; su BTC peggiora.
- Oggi: il VIX ha chiuso sopra 30 il 20/11/2026 (ultimo evento).
