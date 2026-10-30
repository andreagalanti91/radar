# Radar BTC

Segnali swing su Bitcoin (orizzonte di giorni) basati su **order flow** e **posizionamento** dei derivati, con piano **DCA in entrata e in uscita**, alert su **Telegram** e **dashboard online** aggiornata ogni giorno.

Ispirato ai dati che mostra [FlowX](https://app.flowx.trade/) (CVD spot/perp, liquidazioni, basis, open interest), ma costruito direttamente sulle fonti pubbliche degli exchange.

## Come funziona

**Score = z(CVD perp 14g) − z(long/short ratio retail)**, z-score su 180 giorni.

| Componente | Logica | Evidenza (correlazione con il rendimento a 14–30 gg) |
|---|---|---|
| CVD perp 14g | acquisti aggressivi sui futures → continuazione | positiva sia nel 2022-23 che nel 2024-26 |
| Long/short ratio retail | retail troppo long → carburante per il ribasso (contrarian) | negativa in entrambi i periodi |

- **Long** (spot e futures): lo score supera **+2,0**.
- **Short** (solo futures): lo score scende sotto **−2,0** e il regime è ribassista (prezzo sotto la SMA200 e SMA50 sotto la SMA200). Lo short contro-trend storicamente perde, quindi è filtrato.

### Piano operativo (multipli dell'ATR a 14 giorni)
- **Entrata DCA**: 40% all'apertura successiva al segnale, 30% limit a −1 ATR, 30% limit a −2 ATR (validi 7 giorni).
- **Stop**: −3,5 ATR dal primo ingresso.
- **Uscita DCA**: 35% a +1,5 ATR dal prezzo medio, 35% a +3 ATR, 30% in trailing a 3 ATR. Dopo il TP1 lo stop va a pareggio.
- **Uscita forzata** dopo 30 giorni.

## Risultati del backtest (mar 2022 – ott 2026, commissioni e funding inclusi)

I parametri sono stati scelti **solo** sul periodo mar 2022 – dic 2023 e verificati su gen 2024 – oggi.

| | Futures train | Futures test | Spot train | Spot test |
|---|---|---|---|---|
| Trade | 12 | 19 | 11 | 16 |
| Win rate | 83,3% | 84,2% | 81,8% | 87,5% |
| Profit factor | 1,84 | 1,45 | 2,27 | 1,99 |
| Aspettativa/trade | +1,51% | +0,65% | +1,23% | +1,11% |
| Max drawdown | −20,4% | −11,9% | −10,6% | −12,0% |

Limiti da conoscere:
- Circa 6 trade l'anno: il campione è piccolo, quindi il win rate reale può scostarsi di ±10 punti.
- Il win rate alto viene dalla struttura (TP1 vicino + stop a pareggio). Le perdite, quando arrivano, sono 3–4 volte le vincite medie: rispettare lo stop è essenziale.
- Le metriche long/short di Binance partono da dicembre 2021, quindi lo storico utile parte da marzo 2022.

## Uso

```bash
pip install -r requirements.txt
python -m radar.cli daily          # aggiorna dati, segnale, alert, dashboard in site/index.html
python -m radar.cli backtest       # statistiche e lista trade
python -m radar.cli test-telegram  # verifica il bot
```

## Messa online (GitHub Actions + Pages)

1. **Bot Telegram**: crea un bot con [@BotFather](https://t.me/BotFather) e copia il token. Scrivi un messaggio al bot e ricava il tuo `chat_id` da `https://api.telegram.org/bot<TOKEN>/getUpdates`.
2. Nel repo GitHub: *Settings → Secrets and variables → Actions*, aggiungi `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.
3. *Settings → Pages → Source: GitHub Actions*.
4. *Actions → Radar BTC daily → Run workflow* per il primo avvio. Poi gira da solo ogni giorno alle 00:30 UTC.

Alert inviati: nuovo segnale con piano completo, tranche DCA eseguita, take profit raggiunto, trade chiuso, più un riepilogo giornaliero (disattivabile con la variabile `RADAR_DAILY_BRIEF=0`).

Nota: i runner GitHub sono negli USA, dove l'API futures di Binance è bloccata. Per questo il tool usa l'archivio pubblico `data.binance.vision`, `data-api.binance.vision` e OKX, che funzionano ovunque.

## Struttura

```
radar/data.py         download e cache incrementale (data/*.csv)
radar/features.py     CVD spot/perp, funding, OI, long/short, basis, ATR, trend
radar/strategy.py     score, parametri, piano DCA
radar/backtest.py     simulazione con DCA, commissioni, funding
radar/live.py         stato giornaliero, trade aperto, eventi
radar/telegram.py     messaggi
radar/dashboard.py    generazione della dashboard
```

Strumento di analisi, non consulenza finanziaria.
