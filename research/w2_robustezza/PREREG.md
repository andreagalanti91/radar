# W2 + MACD · robustezza statistica · preregistrazione (10/11/2026, scritta PRIMA dei risultati)

Domanda: quanto di "10k → ~119k dal 2021, 14 trade, WR 93%, DD −22,7%" è vantaggio reale e quanto selezione/fortuna?
Nessuna regola nuova: si misura solo la regola in uso (`radar/weekly.py`, importata e mai modificata; i parametri si variano
solo sostituendo le costanti del modulo in memoria). 10.000 $ a 1x, costi del modulo (0,1% + 0,1% slippage spot; perp 0,05% + funding).

## Cosa calcolo
1. **Selezione**. Conteggio delle prove fatte sugli stessi dati BTC 2021–26 prima di arrivare a W2 + F1 (da RESEARCH.md).
   Deflated Sharpe (Bailey–López de Prado) sui rendimenti SETTIMANALI della strategia con N = 31 (prove dirette W2), ~150 (famiglia
   W1+W2+W5+F1) e ~900 (tutta la mappa), varianza fra prove stimata dai vicini del punto 4. Haircut = Sharpe atteso del massimo
   fra N prove senza vantaggio, tolto dallo Sharpe osservato.
2. **Storia lunga**. Bitstamp 2014→08/2017 + Binance spot 08/2017→08/2019 + dati del repo. Proxy dichiarati: flusso = CVD spot z
   (sf14z) prima che esista pf14z (2020-04), nessun flusso prima di 08/2017 (lì solo la versione "senza flusso"); funding 0 prima
   del 2020 (quindi niente uscita su distribuzione). Stesse regole 2015→2020, 4 versioni: {flusso sì/no} × {F1 sì/no}.
   Cicli: 2015–17, 2018, 2019–20. Con B&H accanto.
3. **Trade dal 2021**: bootstrap dei trade (10.000 ricampionamenti con reinserimento, stessa numerosità; CAGR e max DD trade su
   trade); P(WR vero < 70%) con Beta(1,1) e limite inferiore Clopper–Pearson 95%; peso dei 3 trade migliori; risultato togliendo
   ogni singolo trade; block bootstrap (blocchi 8 settimane, 10.000) dei rendimenti settimanali strategia e B&H (CAGR, DD,
   P(strategia > B&H), P(MAR strategia > MAR B&H)); tempo sott'acqua.
4. **Vicini**: SMA 30/35/40/45/50 × EMA (trend e uscita insieme, uscita = trend+1) 15/18/20/23/26; trailing 2/2,5/3/3,5;
   MACD 6/19/4, 8/21/5, 10/24/7, 12/26/9 × OLD_TREND 12/14/16/18/20; soglia flusso −0,5/−0,25/0/0,25/0,5 (solo long).
   Un fattore (o coppia) alla volta attorno alla config in uso. Metriche 2021→oggi: finale, DD, MAR, trade, WR.
5. **Walk-forward** (breve): griglia ridotta SMA{30,40,50} × EMA{15,20,26} × trailing{2,2.5,3} × F1{sì,no} = 54; a ogni 1° gennaio
   2021…2026 scelgo la config con MAR più alto sulla finestra espansa dal 2017-08 (flusso proxy) e la uso per l'anno dopo;
   equity cucita contro config fissa.
6. **Attese**: da (3) block bootstrap a 3 anni + haircut di (1) + cicli di (2): intervallo 10–90% di CAGR e DD; caso peggiore =
   2018 ripetuto e 2022 senza flusso.

## Come giudico (soglie fissate ora)
- Selezione: "regge" se DSR ≥ 0,95 con N ~150; "dubbio" 0,80–0,95; "non regge" < 0,80. Riporto anche N ~900.
- Storia lunga: "regge" se la versione in uso (flusso proxy + F1) nel 2015–20 ha MAR ≥ B&H dello stesso periodo E 2018 ≥ −25%;
  "parziale" se solo una delle due; altrimenti "non regge". Il 2021–26 NON conta come prova.
- Trade: WR "non credibile al 93%" se P(WR < 70%) ≥ 10%; "concentrata" se i 3 migliori fanno > 60% del log-rendimento;
  "fragile" se togliendo un solo trade il finale scende sotto il B&H.
- Vicini: "altopiano" se ≥ 70% dei vicini ha MAR ≥ metà di quello in uso e la config è ≤ 80° percentile; "picco" se ≥ 90° percentile
  o < 50% dei vicini sopra metà MAR.
- Walk-forward: "regge" se l'equity cucita fa ≥ 50% del log-rendimento della config fissa con DD non peggiore di 10 punti.
- Verdetto finale: SOLIDA se ≥ 4 prove su 5 reggono, FRAGILE se ≤ 2, altrimenti MISTA (dico dove).
Limite noto in partenza: prima del 2020 il flusso perp non esiste; il proxy CVD spot è già risultato debole (lezione 43).
