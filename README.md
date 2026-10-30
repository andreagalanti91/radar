<p align="center"><img src="brand/banner.png" alt="Radar Signal BTC" width="100%"></p>

# Radar Signal BTC

Segnali swing su Bitcoin (orizzonte di giorni, circa 10 trade l'anno) basati su **order flow** e **posizionamento** dei derivati. Ogni notte il modello legge i dati, decide se c'è un setup e invia il piano operativo su **Telegram** con entrata e uscita a scaglioni (DCA). La **dashboard** online si aggiorna da sola.

**Dashboard:** https://andreagalanti91.github.io/radar/ · **Bot:** [@CryptoRadarGalaBot](https://t.me/CryptoRadarGalaBot)

## La dashboard

Pensata per il telefono (si installa come app dalla schermata Home), dark-first con tema chiaro. Il prezzo è **live** (Binance in tempo reale, Coinbase come riserva); dati, notizie e dashboard si aggiornano ogni ora. Sezioni:

| Sezione | Cosa trovi |
|---|---|
| **Oggi** | prezzo live, regione prevista a 7 giorni, score di flusso, piano operativo o trade aperto con timeline e **calcolatore in dollari sul tuo capitale**, stato dei 6 setup, grafico con i trade |
| **Simulatore** | inserisci capitale, data di partenza, leva e mercato e vedi quanto varrebbe oggi seguendo i segnali; calcolo di quante volte un obiettivo di capitale è stato raggiunto in passato |
| **Statistiche** | curva di equity contro BTC, anatomia del win rate (standard, sopra +1%, pulito), storico operativo trade per trade (segnale, ingressi, uscite), **registro dei segnali reali** dal 30/10/2026, backtest per periodo, leva e setup |
| **Notizie** | schede Impatto, Dati macro (con calendario economico della settimana, previsioni, dati precedenti e perché contano per BTC), Bitcoin, ETF e istituzionali, Regole, Derivati e on-chain |
| **Metodo** | regole complete e limiti del sistema |

## Regione prevista

Ogni giorno il modello stima la **regione** in cui il prezzo andrà nei prossimi 7 giorni: una **zona di acquisto** sotto il prezzo (dove piazzare ingressi DCA, spot o a leva) e una **zona di vendita** sopra (target o short). La profondità dei ritracciamenti è misurata in ATR e si usano i quantili storici nello stesso regime di trend e flusso, senza guardare al futuro (`radar/zones.py`).

Validazione 2021–2026 (1857 giorni): la zona di acquisto viene toccata entro 7 giorni nel **65%** dei casi, quella di vendita nel **64%**; comprare al centro della zona ha dato un ingresso in media **4,4%** migliore del prezzo di chiusura. Nel 39% dei casi il prezzo scende sotto la zona: lo stop resta necessario.

## I 6 setup

Una sola posizione alla volta (il long ha priorità). Dati giornalieri a chiusura UTC.

| Setup | Lato | Condizione | Logica |
|---|---|---|---|
| `flow` | long | z(CVD perp 14g) − z(long/short retail) > 1,5 | acquisti aggressivi sui perp + retail scettico |
| `capit` | long | drawdown 30g < −12% e open interest −8% in 7g | flush della leva: le liquidazioni hanno ripulito il mercato |
| `fundneg` | long | funding medio 7g < 0 | short affollati che pagano: carburante per uno squeeze |
| `brk` | long | nuovo massimo 20g, CVD perp > +1σ, trend rialzista | breakout confermato dal flusso |
| `sflow` | short | score < −1,5 in regime ribassista | flusso debole + retail long |
| `sfund` | short | funding 7g > +1σ in regime ribassista | rimbalzo a leva dentro un trend ribassista |

Regime ribassista: prezzo sotto la SMA200 e SMA50 sotto la SMA200. Gli short si fanno solo sui futures.

### Gestione della posizione (multipli dell'ATR a 14 giorni)
- **Entrata DCA**: 40% all'apertura dopo il segnale, 30% limit a −0,75 ATR, 30% limit a −1,5 ATR (validi 7 giorni).
- **Stop**: −3 ATR dal primo ingresso.
- **Uscita DCA**: 30% a +1 ATR dal prezzo medio, 30% a +3 ATR, 40% in trailing a 3 ATR. Dopo il primo target lo stop va a pareggio.
- **Uscita forzata** dopo 45 giorni.
- **Leva consigliata sui futures: 2x**, margine isolato.

## Risultati del backtest (mar 2022 – ott 2026)

Commissioni e funding inclusi. Parametri scelti su mar 2022 – dic 2023, verificati su gen 2024 – oggi.

| | Futures train | Futures test | Spot train | Spot test |
|---|---|---|---|---|
| Trade | 20 | 27 | 23 | 26 |
| Win rate | 90% | 88,9% | 91,3% | 84,6% |
| Aspettativa/trade | +2,01% | +2,19% | +1,83% | +1,43% |
| Max drawdown | −4,4% | −16,4% | −0,4% | −16,5% |

| Leva (futures) | Rendimento | CAGR | Max drawdown | Peggior trade |
|---|---|---|---|---|
| 1x | +157% | +22% | −16% | −9% |
| **2x** | **+499%** | **+47%** | **−31%** | **−18%** |
| 3x | +1181% | +73% | −45% | −27% |

BTC buy & hold nello stesso periodo: +76%, max drawdown −67%.

### Win rate: come leggerlo

| | Standard | Sopra +1% | Pulito (senza stop e pareggi) |
|---|---|---|---|
| Futures mar 2022 – ott 2026 | 89,4% | 72,3% | 34,0% |

25 trade su 47 incassano solo il primo target e chiudono il resto a pareggio (+1,25% medio): il guadagno vero arriva dal 40% lasciato correre.

### Limiti
- Il campione è di circa 50 trade: il win rate reale può scostarsi di diversi punti.
- Test di sensibilità su 21 varianti dei parametri: tutte in profitto (win rate 75–94%), ma il set scelto è nella parte alta. Un'aspettativa realistica è sotto il backtest.
- Su orizzonti brevi il sistema rende poco: in finestre di 2 mesi il raddoppio del capitale non è mai avvenuto con leva fino a 3x. Il simulatore della dashboard mostra questo calcolo per qualsiasi obiettivo.
- Con barre giornaliere il backtest assume sempre il caso peggiore tra stop e target nello stesso giorno.

## Brand

<p><img src="brand/brand-board.png" alt="Brand board Radar Signal" width="100%"></p>

Simbolo: un radar ridotto all'essenziale (anello, fascio e blip). Wordmark `radarsignal` in Geist bold. Palette: Signal Blue `#3D5BFF`, Pulse Violet `#8B5CFF`, Blip Mint `#5EF0C4`, Night `#07080C`. Font: Geist, Geist Mono per etichette e chip, Doto per i numeri principali. File in `brand/` (PNG pronti, sorgente HTML in `brand/src/board.html`).

## Ciclo di miglioramento

Due volte al giorno: alle 07:17 un giro di verifica, alle 19:17 un giro di ricerca approfondita con due agenti di ricerca in parallelo; la domenica sera anche la revisione settimanale. Ogni giro impara (lezioni apprese) e propone nuove idee, ciascuna affidata a un sotto-agente definito in `.claude/agents/`:

| Fase | Agente | Cosa fa |
|---|---|---|
| Pianificazione | `radar-plan` | legge obiettivi, roadmap, lezioni e scelte dell'utente e decide cosa studiare |
| Scan | `radar-scan` | aggiorna i dati, controlla la salute del sistema, fotografa mercato e prestazioni recenti |
| Apprendimento | `radar-learn` | prova una sola idea (DCA, take profit e stop a scaglioni, uso della regione prevista, nuovi setup) su una copia di lavoro e la valuta |
| Revisione | `radar-review` | avvocato del diavolo sui candidati: overfitting, dipendenza da pochi trade, errori |
| Miglioramento | `radar-improve` | se il gate è superato la pubblica e invia l'alert Telegram con la performance prima/dopo, altrimenti la scarta |

Obiettivo: rendimento corretto per il rischio (rendimento / max drawdown). Il gate (`radar/research.py`) richiede: MAR migliore del 5%, nessun peggioramento nel test 2024–25, nel training 2022–23 e nel 2026, miglioramento nella maggior parte dei semestri, probabilità ≥ 75% al ricampionamento, nessuna dipendenza da 1–2 trade, nessun peggioramento su SOL (banco di prova), robustezza, test automatici superati, nessun trade aperto. Il diario è in [`RESEARCH.md`](RESEARCH.md).

## Messa online

1. Bot Telegram da [@BotFather](https://t.me/BotFather); il token non va mai scritto nel codice.
2. *Settings → Secrets and variables → Actions*: `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.
3. *Settings → Pages → Source: GitHub Actions*.
4. Il workflow `Radar Signal BTC daily` gira ogni ora (notizie, calendario, dashboard, alert sui trade aperti) e alle 00:30 UTC calcola il segnale sulla candela chiusa e invia il riepilogo giornaliero.

Alert inviati: nuovo segnale con piano completo e importi in dollari sul capitale (`RADAR_CAPITAL`, predefinito 50.000 $), ordini toccati in tempo reale (controllo orario su candele orarie: limit DCA, stop, target), dati non aggiornati da oltre 36 ore, tranche DCA eseguita, target raggiunto, trade chiuso, riepilogo giornaliero (disattivabile con la variabile `RADAR_DAILY_BRIEF=0`).

## Uso locale

```bash
pip install -r requirements.txt
python -m radar.cli daily          # dati, segnale, alert, dashboard in site/
python -m radar.cli backtest       # statistiche e lista trade
python -m radar.research           # scorecard della strategia
python -m radar.cli test-telegram  # verifica il bot
```

## Struttura

```
radar/data.py         download e cache incrementale (data/*.csv)
radar/features.py     CVD spot/perp, funding, OI, long/short, basis, ATR, trend
radar/strategy.py     6 setup, parametri, piano DCA
radar/backtest.py     simulazione con DCA, commissioni, funding
radar/live.py         stato giornaliero, trade aperto, eventi
radar/research.py     scorecard e gate di promozione
radar/telegram.py     messaggi
radar/dashboard*.py   dashboard (dark-first, light/dark, mobile, installabile)
brand/                logo, icona app, banner, social preview, brand board (sorgenti in brand/src)
.claude/agents/       sotto-agenti del ciclo orario (scan, apprendimento, miglioramento)
radar/zones.py        previsione della regione di prezzo a 7 giorni
radar/news.py         notizie RSS classificate per impatto e calendario economico
radar/intraday.py     controllo orario degli ordini del piano (alert in tempo reale)
radar/liquidations.py raccolta delle liquidazioni reali OKX da oggi (data/liquidations.csv)
radar/observe.py      osservazione su carta di altri asset (SOL)
tests/                test del motore di backtest (python -m radar.cli test)
```

Fonti dati: Binance (spot, perp USDT-M, open interest, long/short ratio), OKX per i giorni non ancora archiviati, alternative.me (Fear & Greed).

Strumento di analisi, non consulenza finanziaria.
