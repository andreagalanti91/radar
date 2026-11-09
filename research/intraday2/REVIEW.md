# Revisione critica del ciclo intraday 2 (09/11/2026) — verdetto: NON PROMUOVERE

Candidata E4: incrocio Ichimoku TK 4h (9/26/52, sopra/sotto la nube) su BTC, ETH, SOL; stop 2 ATR, metà a +2R, pareggio,
trailing 3 ATR sul resto; rischio 1% a trade. Criteri del piano 7 su 7, ma i controlli decisivi la bocciano.

1. Motore corretto: nessun look-ahead (nube con shift(26) su dati passati, ATR noto alla chiusura, ingresso alla barra dopo,
   stop prima del TP nella barra). Numeri riprodotti: dal 2021 PF 1,31, +0,224R, DD −17,6%; 2024→oggi PF 1,33, +0,249R, DD −15,2%.
2. Prove multiple: ciclo 1 ≈ 2.640 configurazioni, ciclo 2 decine di ingressi/uscite/griglie. t per trade 2,32 fuori campione
   (284 trade): con ~100–1.000 prove il massimo atteso per caso è 2,5–3,2 → non significativo dopo la correzione.
3. Robustezza: positiva su 3 asset, long e short, ogni anno; ma 2023 (PF 1,16), 2026 (1,17) ed ETH (1,26) sotto soglia.
4. Esecuzione manuale (decisiva): slippage +0,10%/lato → PF 1,24; +0,20% → PF 1,15, DD −20,3%; ingresso 1h dopo l'alert →
   PF 1,17, DD −25,8%; 2h dopo → PF 1,13, DD −27,7%. Con ritardo realistico da Telegram non passa.
5. Dati mai visti: 2020 su BNB, XRP, LINK, ADA, DOGE → PF 0,97 (4 su 5 negative). Alt 2021→oggi: panieri PF 1,20–1,21.
6. Rispetto a W2: ~8 alert al mese a mano per 10k → 29k contro W2 10k → ~120k con 14 trade in 6 anni.
Idee: se l'intraday riparte, preregistrarlo con costi da esecuzione manuale (+0,10%/lato, ingresso 1h dopo) e controllo finale
su dati mai visti; provare il trailing 3 ATR come uscita del "runner" su W2; E4 solo con ordini automatici, non da Telegram.
