# Diario di ricerca · Radar Signal BTC

Ciclo di miglioramento automatico (ogni ora). Ogni iterazione prova un'idea, la valuta con
`python -m radar.research` e la promuove solo se supera il gate in `radar/research.py`:

- aspettativa nel test (2024–2025) migliore della versione attuale
- nessun peggioramento oltre 0,25 punti nel periodo di conferma (2026–oggi)
- non peggiora troppo nel training (2022–23): altrimenti è rumore
- win rate test non più basso di 2 punti, max drawdown non peggiore di 3 punti
- rendimento totale almeno +5%
- almeno l'80% dei trade attuali
- robustezza: tutte le varianti vicine dei parametri in profitto e con win rate ≥ 70%

Regole operative: nessuna promozione mentre un trade è aperto;
ogni promozione viene annunciata su Telegram e annotata qui.

## PROSSIMO GIRO (richiesta dell'utente, 30/10/2026): valutazione profonda ETH e SOL
Iterazione dedicata, al posto della singola idea. Non promuove nulla in automatico: produce un rapporto.
1. Scaricare per ETHUSDT e SOLUSDT gli stessi dati di BTC (spot e perp da data.binance.vision, funding, metrics
   OI/long-short, ultimi giorni da OKX): `radar/data.py` oggi ha `SYMBOL` fisso, va parametrizzato senza
   rompere BTC (cache separata per simbolo, es. `data/ETHUSDT/`). SOL perp USDT-M esiste dal 2020, metrics da fine 2021.
2. Applicare la strategia attuale **senza ritoccare i parametri** (test fuori campione puro): trade, win rate,
   win rate pulito, aspettativa, max drawdown, rendimento 1x/2x per train 2022–23, test 2024–25, holdout 2026.
3. Verificare la regione prevista (`radar/zones.py`) su ETH e SOL: tassi di tocco delle zone.
4. Valutare il portafoglio: correlazione dei rendimenti dei trade e delle date di segnale con BTC; equity combinata
   BTC+ETH+SOL con capitale diviso (es. 50/25/25) contro solo BTC: rendimento, drawdown, trade/anno.
5. Rischi specifici: liquidità e slippage (SOL più volatile, ATR più alto), code di rischio (crolli > 20% in un giorno),
   funding più estremi.
6. Conclusione con raccomandazione chiara (aggiungere / non aggiungere / solo in osservazione) e, se positiva,
   piano di integrazione (alert Telegram, dashboard multi-asset). Registrare qui il rapporto e inviarlo su Telegram
   come "RADAR SIGNAL BTC · Valutazione ETH e SOL".

## Priorità dell'utente (30/10/2026, dopo l'iterazione 1) — affrontare per prime
1. **Stop calcolato**: stop non fisso a 3 ATR dal primo ingresso ma derivato da struttura/volatilità (es. sotto il bordo profondo della zona prevista − k·ATR, minimo a 20 giorni, stop sul prezzo medio dopo ogni tranche, stop a scaglioni). Misurare perdita media e massima per trade.
2. **Drawdown calcolato e limitato**: regole di rischio a livello di portafoglio, es. riduzione della size dopo una perdita o quando l'equity è sotto il massimo di X%, stop di sistema temporaneo dopo N stop consecutivi. Obiettivo: max drawdown a 1x sotto il 12% senza perdere più del 10% di rendimento.
3. **Budget per operazione**: sizing a rischio fisso (es. 1–2% del capitale perso se scatta lo stop, con size = rischio / distanza dello stop, leva massima 3x), sizing per setup in base alla sua storia, confronto con l'allocazione fissa attuale (100% del capitale × pesi DCA).
4. **Win rate pulito**: riportare sempre, accanto al win rate standard, `win_rate_clean` (solo trade chiusi da target, trailing o tempo in profitto; stop e pareggi esclusi dalle vincite) e `win_rate_1pct` (trade sopra +1%). Un candidato non deve peggiorarli in modo sensibile.

## Backlog prioritario (richiesto dall'utente, 30/10/2026)
Studiare a fondo la gestione a scaglioni, una variante per iterazione:
1. **DCA in entrata**: numero di tranche (2–5), pesi (piramide crescente/decrescente/uguale), distanza tra le tranche in ATR, validità dei limit, ingresso condizionato (tranche solo se il setup resta attivo).
2. **TP in DCA**: numero di target, distanze in ATR o in % del rischio (R multipli), pesi, target su livelli di struttura (massimi a 20g), trailing sul residuo (ATR, chandelier, SMA20).
3. **Stop loss in DCA**: uscita a scaglioni invece di uno stop unico (es. 1/3 a −2 ATR, 1/3 a −2,5, 1/3 a −3), stop per singola tranche, stop temporale parziale, stop che segue il prezzo medio dopo ogni tranche.
4. **Regione prevista** (`radar/zones.py`): posizionare le tranche DCA dentro la zona di acquisto invece che a distanze fisse in ATR; target dentro la zona di vendita.
Ogni variante va confrontata con il gate standard (`radar/research.py`) e riportata qui con i numeri del test.

## Baseline v2 (30/10/2026)
47 trade futures da mar 2022, win rate 89,4%, +157% a 1x, max DD −16,4%. Test 2024–26: 27 trade, 88,9%, aspettativa +2,19%.

## Iterazioni
- **2026-10-30 10:40 UTC · Iterazione 1 · SCARTATO** — Idea: tranche DCA 2 e 3 ai bordi della zona prevista (`radar/zones.py`: buy_hi/buy_lo long, sell_lo/sell_hi short) invece di −0,75/−1,5 ATR fissi, stop invariato. Test 2024–25: aspettativa +1,92% → +1,50%, rendimento +40,2% → +24,8%, max DD −16,4% → −25,4% (train exp +2,01 → +1,94; holdout 2026 +2,85 → +3,16; full 1x +156,7% → +130,3%, 2x +498,9% → +372,1%). Motivo: aspettativa test e drawdown peggiori — la zona è più vicina (0,66/1,33 ATR) e riempie più tranche nei trade stoppati (stop pieno −10,8% a mar 2025). Prossime: tranche più profonde (buy_lo e buy_lo − 0,5 ATR) o peso ridotto nella zona, combinare con stop sul prezzo medio (backlog 3).
