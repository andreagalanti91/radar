# PREREG · W3 sulle top 10 crypto (11/11/2026, scritto prima dei risultati)

**Domanda dell'utente**: confrontare la strategia con le top 10 crypto per capitalizzazione.

**Universo** (CoinGecko /coins/markets, 11/11/2026, esclusi stablecoin USDT/USDC/USDS/USDe/DAI e il token RWA FIGR_HELOC):
BTC, ETH, BNB, XRP, SOL, TRX, HYPE, ZEC, XMR, DOGE. Coppie Binance `<SYM>USDT` spot e perp USDT-M.
HYPE: spot Binance solo dal 24/09/2026 → prezzo dal perp; XMR: spot delistato il 20/02/2024 → prezzo dal perp dopo quella data.
Nessuna sostituzione: si testano tutte e 10 come sono (LINK/ADA solo se una delle 10 non ha dati, non serve).

**Strategie (nessun tuning, stessi parametri ovunque)** — motore `research/w2_migliorie/eng.py`, ancora SUN:
1. **W3**: pf14z = media degli ultimi 3 valori giornalieri disponibili (`rolling(3).mean().shift(1)`), cricchetto,
   tetto di rischio long `min(1, 0,25 / (2,5·ATRw/close))`, niente rendimento della liquidità.
2. **W2** com'è (pf14z del giorno, niente cricchetto, niente tetto).
3. **Buy & hold** (apertura del primo giorno, costi spot).

**Feature**: logica di `radar/features.py` (perp_flow14 = Σ(2·taker_buy − vol)/Σvol su 14 g, z-score 180 g min 90; funding
giornaliero = somma dei tassi, ffill ≤ 3 g). Inizio = max(01/01/2021, primo pf14z valido + 200 giorni).
Verifica: BTC con questi dati deve dare W2 ≈ il risultato del repo (tolleranza ±3% sul capitale finale).

**Metriche**: capitale finale, rendimento, DD giornaliero, trade, WR, MAR, tempo a mercato; split 2021–23 / 2024→oggi
(motore riavviato a 10k a inizio periodo). Robustezza: senza il trade migliore; vicini (trailing 2,0/3,0 ATRw) solo su W3.

**Portafogli** (10% ciascuno, indipendenti, senza ribilanciamento; asset che partono tardi = liquidità finché non partono):
(i) W3 solo BTC; (ii) W3 equal-weight sulle 10; (iii) W3 su BTC + asset che battono il B&H in ENTRAMBE le metà (SELEZIONE
A POSTERIORI, distorta); (iv) B&H equal-weight sulle 10.

**Soglie decise prima**: "generalizza" se W3 batte il B&H sul MAR in ≥ 7/10 asset E in entrambe le metà in ≥ 5/10, e
il portafoglio (ii) ha MAR ≥ (iv) e DD ≤ (iv). Un asset "aggiunge valore" se W3 ha MAR > B&H in entrambe le metà e
aggiungendolo a BTC (50/50) il DD del portafoglio non supera quello di W3 solo BTC di più di 2 punti.
