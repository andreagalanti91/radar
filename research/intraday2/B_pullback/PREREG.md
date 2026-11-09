# Famiglia B · Pullback nel trend 1h — preregistrazione (09/11/2026, scritta PRIMA di qualsiasi risultato)

Regole comuni: research/intraday2/PIANO.md. Asset BTC, ETH, SOL perp 1h, stessi parametri su tutti, dal 2021-01-01.

## Impostazione comune (fissa)
- Segnale alla CHIUSURA della barra 1h, ingresso all'apertura successiva (motore `engine.py`).
- Dati di timeframe superiore (4h, giorno) costruiti dal 1h e usati solo dopo la chiusura della loro barra (niente look-ahead).
- **Trend su (T↑)**: 4h EMA20 > EMA50 > EMA200, EMA50 4h più alta di 6 barre 4h prima, chiusura giornaliera > EMA50 giornaliera.
  **Trend giù (T↓)**: specchio. Gli short sono lo specchio esatto dei long in tutte le varianti.
- **ADX**: ADX(14) di Wilder sul 4h.
- **Raffreddamento**: dopo un segnale sullo stesso asset, nessun nuovo segnale per 24 barre 1h (un ingresso per pullback).
- **Uscite di riferimento (PIANO)**: stop 1,5 ATR(14) 1h, TP1 +1,5R metà, stop a pareggio dopo TP1, TP2 +3R sul resto,
  uscita a tempo 48 barre; nessuna uscita/inversione su segnale opposto.
- **Sizing**: rischio 1% dell'equity per trade, leva di margine 2x (isolata, per la liquidazione), allocazione "shared",
  esposizione totale max 5x l'equity. Capitale 10.000 $. Costi del motore (0,05% + 0,02% slip, 0,05% sugli stop, funding reale).

## Varianti (8)
| id | regola d'ingresso long (short = specchio) | parametri (vicini) |
|---|---|---|
| B1 | T↑, ADX4h > 20; la barra 1h tocca la EMA20 4h (low ≤ EMA) e chiude sopra, candela rialzista (close > open) con ombra inferiore ≥ 40% del range | ema 20, adx 20, wick 0,4 |
| B2 | come B1 ma ritest della EMA50 4h (pullback profondo) | ema 50, adx 20, wick 0,4 |
| B3 | T↑, ADX4h > 20, RSI(2) 1h < 10 con chiusura 1h ancora sopra la EMA50 4h | rsi_lvl 10, adx 20 |
| B4 | T↑, ADX4h > 20, RSI(14) 1h che incrocia al rialzo 40 dopo un minimo < 32 nelle ultime 6 barre | lo 32, hi 40, adx 20 |
| B5 | T↑, VWAP di sessione (ancorato 00:00 UTC, prezzo tipico × volume); 3 chiusure precedenti sopra il VWAP, la barra tocca il VWAP e chiude sopra, rialzista; solo barre con ora UTC 12–20 (sessione USA) | n_above 3 |
| B6 | 4h: chiusura sopra il massimo Donchian 20 barre 4h → livello L; nelle 24 barre 1h successive primo ritest: low ≤ L + 0,25 ATR1h e close > L; chiusura giornaliera > EMA50 giornaliera | don 20, window 24 |
| B7 | B1 + filtri severi: ADX4h > 25, ATR% 1h tra il 20° e l'80° percentile dei 90 giorni precedenti, ora UTC 7–21 | adx 25 |
| B8 | B3 + gli stessi filtri severi di B7 | rsi_lvl 10, adx 25 |

## Scelta (solo 2021–23) e giudizio (2024→oggi, una volta)
- Sul 2021–23 si scarta ogni variante con trade/mese totali fuori da 2–12, PF < 1,2 o aspettativa ≤ 0R.
  Fra le rimaste si sceglie quella con aspettativa R più alta (a parità ±0,02R: MAR più alto). Nessun ritocco dopo.
- Se nessuna resta, il verdetto è "nessuna variante scelta" e il fuori campione si riporta solo a titolo informativo.
- La variante scelta passa se sul 2024→oggi soddisfa TUTTI i criteri del PIANO:
  PF ≥ 1,3 e aspettativa ≥ +0,15R; DD giornaliero ≤ 20%; positiva nel 2021–23 e nel 2024→oggi e su ≥ 2/3 asset (OOS);
  2–12 trade/mese totali; placebo (500 giri, OOS) sopra il 90° percentile del rendimento;
  mediana del rendimento dei vicini (OOS, un parametro alla volta, ±20%/±10%) > 0; OOS senza il trade migliore > 0.
- Confronti: buy & hold 1x a pesi uguali BTC/ETH/SOL e W2 + MACD (dal registro di RESEARCH.md).
