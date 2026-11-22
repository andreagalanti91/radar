# Indicatore "EMA200D combined VIX" — logica estratta dal codice Pine fornito dall'utente il 22/11/2026
Fonte: https://it.tradingview.com/script/Qg7LvpxB (solo ricerca interna; qui la logica, non la grafica).
Parametri di default: EMA 200 giornaliera; soglia VIX 34; orizzonte 60 giorni di calendario; stop VIX spento (25% se acceso).
Solo long, una posizione alla volta, segnali e prezzi alla CHIUSURA della barra.
- Ingresso trend: close incrocia sopra EMA200D (crossover).
- Ingresso VIX (eccezione, anche sotto la EMA): VIX incrocia sopra 34 (crossover), solo se flat.
- Uscita trend: close incrocia sotto EMA200D (crossunder).
- Trade VIX: dopo 60 giorni di calendario, se close > EMA200D diventa trade di trend (resta dentro), altrimenti esce;
  stop opzionale: close <= ingresso·(1 − 25%).
- Statistiche: rendimento per trade, equity = prodotto dei rendimenti di barra quando in posizione (stato PRIMA del segnale).
Note: nessun costo, nessuno short; pensato per indici azionari (VIX = volatilità implicita dell'S&P 500).
