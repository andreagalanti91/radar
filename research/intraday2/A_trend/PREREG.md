# Famiglia A · Trend e rotture 4h — preregistrazione (09/11/2026, scritta PRIMA di qualsiasi risultato)

Regole comuni: ../PIANO.md. Asset BTC, ETH, SOL (perp Binance), barre 4h da `load_all("4h")`, stessi parametri sui 3 asset.
Segnale deciso alla chiusura della barra, ingresso all'apertura successiva. Long e short simmetrici.

## Uscite e sizing di riferimento (uguali per tutte le varianti, nessuna taratura qui)
- `Exits(stop_atr=1.5, tp=[(1.5, .5), (3, .5)], tp_unit="R", be_after_tp1=True, time_bars=12, reverse_exit=False, reverse_entry=False)`
  (nessuna uscita su segnale: si studiano gli ingressi; segnali con posizione aperta ignorati).
- `Sizing(mode="risk", risk_pct=0.01, leverage=2, allocation="equal", max_exposure=3)`, capitale 10.000 $; `Costs()` di default.

## Definizioni comuni
- ATR = Wilder 14 (engine.atr). Volume relativo `rv = volume / media(volume, 20).shift(1)` (NaN -> nessun segnale).
- Regime giornaliero (solo giorni CHIUSI, allineato alla barra 4h successiva alla chiusura del giorno): EMA50 del close giornaliero;
  rialzo = close_d > EMA50_d e EMA50_d > EMA50_d di 5 giorni prima; ribasso = speculare. (La SMA40w di W2 non è usabile: i dati 1h
  iniziano a 09/2020, 40 settimane di riscaldamento non bastano per il 2021.)
- Donchian N: `hh = high.rolling(N).max().shift(1)`, `ll = low.rolling(N).min().shift(1)`; rottura long = close > hh e close
  precedente <= hh precedente (solo la prima barra di rottura); short speculare.

## Varianti (8)
| id | regola d'ingresso | parametri |
|---|---|---|
| A1 ICHI | Ichimoku TK cross (Tenkan 9, Kijun 26, Senkou B 52, nube spostata 26): long se Tenkan incrocia sopra Kijun e close sopra entrambe le linee della nube; short speculare (base della lezione 78) | tk=9, kj=26, sb=52 |
| A2 DON | rottura Donchian N con conferma di volume rv >= v | N=55, v=1.5 |
| A3 DON_REG | A2 solo nel verso del regime giornaliero | N=55, v=1.5, ema_d=50 |
| A4 SQZ | compressione: percentile della larghezza BB(20,2) sulle ultime 180 barre <= 15 in almeno una delle ultime 6 barre, poi rottura Donchian 20 | bb=20, look=180, pct=15, N=20 |
| A5 SQZ_REG | A4 solo nel verso del regime giornaliero | come A4 + ema_d=50 |
| A6 DON_ADX | A3 + ADX(14) >= 20 alla barra di rottura | N=55, v=1.5, ema_d=50, adx=20 |
| A7 RETEST | dopo una rottura A3 (senza conferma di volume) entro 6 barre: il low (high per short) torna entro 0,25 ATR dal livello rotto e la barra chiude oltre il livello -> ingresso; un solo ingresso per rottura | N=55, ema_d=50, w=6, tol=0.25 |
| A8 ICHI_REG | A1 solo nel verso del regime giornaliero | come A1 + ema_d=50 |

## Scelta (solo 2021-01-01 -> 2023-12-31)
Ammesse le varianti con, in campione: 2–12 trade/mese in totale, PF >= 1,1, aspettativa > 0. Fra le ammesse si sceglie quella con
aspettativa R più alta in campione (a parità entro 0,02R, quella con meno trade). Nessun cambio di parametri dopo questa scelta.

## Giudizio (2024-01-01 -> oggi, una volta sola) — criteri del PIANO
1. PF >= 1,3 e aspettativa >= +0,15R. 2. Max DD giornaliero <= 20%. 3. Positivo in campione e fuori campione e su >= 2/3 asset
(PnL fuori campione per asset). 4. 2–12 trade/mese totali (fuori campione). 5. Placebo 500 giri (engine.placebo, seed 0) sul
fuori campione: percentile di exp_R e di ret_pct > 90. 6. Vicini (one-at-a-time, x0,8 / x1,2 sui parametri numerici della
variante, interi arrotondati): mediana di exp_R fuori campione > 0. 7. PnL fuori campione senza il trade migliore > 0.
Si riportano i numeri fuori campione di TUTTE le varianti per trasparenza; passa solo la variante scelta in campione. Se una non
scelta superasse tutti i criteri, va segnalata come "passa ma non scelta" (rischio di selezione), non promossa.
Confronti: buy & hold 1/3 BTC-ETH-SOL a 1x dal 01/01/2021 e W2 + MACD (dalla Memoria in RESEARCH.md).
