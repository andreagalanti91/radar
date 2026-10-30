# Radar BTC

Segnali swing su Bitcoin (orizzonte di giorni, ~10 trade l'anno) basati su **order flow** e **posizionamento** dei derivati, con piano **DCA in entrata e in uscita**, alert su **Telegram** e **dashboard online** aggiornata ogni giorno.

Ispirato ai dati che mostra [FlowX](https://app.flowx.trade/) (CVD spot/perp, liquidazioni, basis, open interest), ma costruito direttamente sulle fonti pubbliche degli exchange.

## Come funziona

Sei setup indipendenti, una sola posizione alla volta (il long ha priorità). Tutti usano dati giornalieri a chiusura UTC.

| Setup | Lato | Condizione | Logica |
|---|---|---|---|
| `flow` | long | z(CVD perp 14g) − z(long/short retail) > 1,5 | acquisti aggressivi sui perp + retail scettico |
| `capit` | long | drawdown 30g < −12% e open interest −8% in 7g | flush della leva: liquidazioni hanno ripulito il mercato |
| `fundneg` | long | funding medio 7g < 0 | short affollati che pagano: carburante per uno squeeze |
| `brk` | long | nuovo massimo 20g, CVD perp > +1σ, trend rialzista | breakout confermato dal flusso |
| `sflow` | short | score < −1,5 in regime ribassista | flusso debole + retail long |
| `sfund` | short | funding 7g > +1σ in regime ribassista | rimbalzo a leva dentro un trend ribassista |

Regime ribassista = prezzo sotto SMA200 e SMA50 sotto SMA200. Gli short contro-trend storicamente perdono, quindi sono filtrati. Gli short si fanno solo sui futures.

### Piano operativo (multipli dell'ATR a 14 giorni)
- **Entrata DCA**: 40% all'apertura successiva al segnale, 30% limit a −0,75 ATR, 30% limit a −1,5 ATR (validi 7 giorni).
- **Stop**: −3 ATR dal primo ingresso.
- **Uscita DCA**: 30% a +1 ATR dal prezzo medio, 30% a +3 ATR, 40% in trailing a 3 ATR. Dopo il TP1 lo stop va a pareggio.
- **Uscita forzata** dopo 45 giorni.
- **Leva consigliata sui futures: 2x**, margine isolato. Con lo stop a circa 6–9% dal prezzo medio, a 2x la perdita massima è circa il 18% del capitale allocato, mentre la liquidazione è a circa −45%: lo stop scatta molto prima.

## Risultati del backtest (mar 2022 – ott 2026, commissioni e funding inclusi)

| | Futures train (2022–23) | Futures test (2024–26) | Spot train | Spot test |
|---|---|---|---|---|
| Trade | 20 | 27 | 23 | 26 |
| Win rate | 90% | 88,9% | 91,3% | 84,6% |
| Profit factor | 9,9 | 4,36 | 75,7 | 2,16 |
| Aspettativa/trade | +2,01% | +2,19% | +1,83% | +1,43% |
| Max drawdown | −4,4% | −16,4% | −0,4% | −16,5% |

Futures sull'intero periodo, con leva (BTC buy & hold nello stesso periodo: +76%, max drawdown −67%):

| Leva | Rendimento | CAGR | Max drawdown | Peggior trade |
|---|---|---|---|---|
| 1x | +157% | +22% | −16% | −9% |
| **2x** | **+499%** | **+47%** | **−31%** | **−18%** |
| 3x | +1181% | +73% | −45% | −27% |

Circa 10 trade l'anno.

### Robustezza
- Test di sensibilità su 21 varianti dei parametri, cambiandone uno alla volta: tutte in profitto, win rate tra 75% e 94%, rendimento a 1x tra +65% e +163%. Il set scelto è nella parte alta della distribuzione: **un'aspettativa realistica è inferiore al backtest**, nell'ordine di +80–120% a 1x sullo stesso periodo.
- Periodo 2020–21 (mai usato, solo i setup che non richiedono le metrics di Binance): 6 trade su 6 in profitto.
- Limite: la scelta dei setup ha guardato anche i dati 2024–26, quindi il test non è del tutto "cieco". Il miglior test sarà il trading reale.
- Le barre giornaliere non dicono cosa succede prima tra stop e target nello stesso giorno: il backtest assume sempre il caso peggiore (prima lo stop).

## Uso

```bash
pip install -r requirements.txt
python -m radar.cli daily          # aggiorna dati, segnale, alert, dashboard in site/index.html
python -m radar.cli backtest       # statistiche e lista trade
python -m radar.cli test-telegram  # verifica il bot
```

## Messa online (GitHub Actions + Pages)

1. **Bot Telegram**: crea un bot con [@BotFather](https://t.me/BotFather) e copia il token. Scrivi un messaggio al bot e ricava il tuo `chat_id` da `https://api.telegram.org/bot<TOKEN>/getUpdates`. Il token non va mai scritto nel codice.
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
