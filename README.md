<p align="center"><img src="brand/banner.png" alt="Radar Signal BTC" width="100%"></p>

# Radar Signal BTC

Segnali swing brevi su Bitcoin (pochi giorni per trade, circa 22 trade l'anno) basati su **order flow** e **posizionamento** dei derivati, con **conferma a 4 ore**. Dal 31/10/2026 i segnali reali usano la strategia **v2**. Dal 31/10/2026 pomeriggio c'è anche un **secondo segnale reale, settimanale (W2)**: circa 3 operazioni l'anno, lunghe settimane o mesi (vedi [Segnale settimanale (W2)](#segnale-settimanale-w2)). Ogni notte il modello legge i dati e decide se c'è un setup; ogni ora controlla se è arrivata la conferma e gestisce il trade. Tutto arriva su **Telegram** con il piano in dollari; la **dashboard** online si aggiorna da sola.

**Dashboard:** https://andreagalanti91.github.io/radar/ · **Bot:** [@CryptoRadarGalaBot](https://t.me/CryptoRadarGalaBot)

## La dashboard

Pensata per il telefono (si installa come app dalla schermata Home), dark-first con tema chiaro. Il prezzo è **live** (Binance in tempo reale, Coinbase come riserva); dati, notizie e dashboard si aggiornano ogni ora. Sezioni:

| Sezione | Cosa trovi |
|---|---|
| **Oggi** | prezzo live, regione prevista a 7 giorni, score di flusso, **stato v2** (nessun segnale / in attesa di conferma 4h con soglia e scadenza / ingresso confermato / trade aperto) con piano, rischio, leva e **calcolatore in dollari sul tuo capitale**, **stato del settimanale W2** (posizione, trailing, EMA 21, distribuzione), stato dei 6 setup, conti **su carta** (H2 e v2), grafico con i trade |
| **Simulatore** | capitale, data di partenza e size (1x = piano v2, 2x, 3x, 5x): quanto varrebbe oggi seguendo i segnali v2; quante volte un obiettivo di capitale è stato raggiunto in passato |
| **Statistiche** | curva di equity v2 contro BTC, esiti (TP, stop, tempo), storico trade per trade (segnale, conferma, limit, uscita), **registro dei segnali reali** dal 31/10/2026, risultati per periodo e per anno, 10.000 $ a 1x/2x/5x, per setup, **storico del settimanale W2** (trade, anni, 10.000 $ a 1x/2x); Laboratorio con v2, W2 e i candidati della ricerca |
| **Notizie** | schede Impatto, Dati macro (con calendario economico della settimana, previsioni, dati precedenti e perché contano per BTC), Bitcoin, ETF e istituzionali, Regole, Derivati e on-chain |
| **Metodo** | regole complete e limiti del sistema |

## Regione prevista

Ogni giorno il modello stima la **regione** in cui il prezzo andrà nei prossimi 7 giorni: una **zona di acquisto** sotto il prezzo (dove piazzare ingressi DCA, spot o a leva) e una **zona di vendita** sopra (target o short). La profondità dei ritracciamenti è misurata in ATR e si usano i quantili storici nello stesso regime di trend e flusso, senza guardare al futuro (`radar/zones.py`).

Validazione 2021–2026 (1857 giorni): la zona di acquisto viene toccata entro 7 giorni nel **65%** dei casi, quella di vendita nel **64%**; comprare al centro della zona ha dato un ingresso in media **4,4%** migliore del prezzo di chiusura. Nel 39% dei casi il prezzo scende sotto la zona: lo stop resta necessario.

## Strategia v2 in parole semplici

1. **Il segnale.** Ogni notte, alla chiusura giornaliera UTC, si controllano i 6 setup qui sotto (flusso dei perp, posizionamento,
   funding, open interest). Se uno scatta, **non si entra subito**.
2. **La conferma a 4 ore.** Si aspetta che una candela a 4 ore chiuda **sopra il massimo delle due candele 4h precedenti**
   (short: sotto il minimo), entro 72 ore. Se non succede, il segnale scade. Su Telegram arriva subito la soglia e la scadenza.
3. **L'ingresso a due livelli.** Alla conferma: **40% a mercato**, **60% con un ordine limite 0,5 ATR più in basso**
   (short: più in alto), valido 7 giorni.
4. **Stop e target.** Stop a **1 ATR dall'ingresso** per tutta la posizione. Un solo **take profit a +1R** dal prezzo medio
   (R = distanza tra medio e stop). Se dopo **14 giorni** non è uscito, si chiude.
5. **Quanto rischiare.** Si parte da un rischio base del **4,3% del capitale** per trade (variabile `RADAR_RISK`).
   Si guarda il **delta taker** della candela 4h di conferma (acquisti aggressivi meno vendite aggressive, media spot e perp):
   più è forte nella direzione del trade, più si rischia, da 0,5× a 2× il rischio base. I long con il prezzo settimanale sotto la
   media a 40 settimane rischiano il 40% in meno. Rischio per trade quindi tra **1,4% e 9,3%**.
6. **La leva** viene di conseguenza: leva = rischio / distanza dello stop, **al massimo 5x**, margine isolato (media storica 1,6x).

Una sola posizione alla volta. Il rischio di ogni trade reale si fissa alla conferma e non cambia più.

### I 6 setup (il segnale giornaliero)

| Setup | Lato | Condizione | Logica |
|---|---|---|---|
| `flow` | long | z(CVD perp 14g) − z(long/short retail) > 1,5 | acquisti aggressivi sui perp + retail scettico |
| `capit` | long | drawdown 30g < −12% e open interest −8% in 7g | flush della leva: le liquidazioni hanno ripulito il mercato |
| `fundneg` | long | funding medio 7g < 0 | short affollati che pagano: carburante per uno squeeze |
| `brk` | long | nuovo massimo 20g, CVD perp > +1σ, trend rialzista | breakout confermato dal flusso |
| `sflow` | short | score < −1,5 in regime ribassista | flusso debole + retail long |
| `sfund` | short | funding 7g > +1σ in regime ribassista | rimbalzo a leva dentro un trend ribassista |

Regime ribassista: prezzo sotto la SMA200 e SMA50 sotto la SMA200. Gli short si fanno solo sui futures.

## Risultati v2 (mar 2022 – ott 2026, candele 4h, commissioni, funding e slippage 0,1% inclusi)

Rischio base dal vivo 4,3% (scelto il 31/10: è il massimo che tiene P(DD>20%) ≤ 15% con dati dal 2021 e slippage 0,2%). Drawdown sull'equity **giornaliera** (non solo trade per trade).

| | 2022–23 (scelta dei parametri) | 2024–25 (verifica) | 2026 (verifica) | **Totale** |
|---|---|---|---|---|
| Trade | 49 | 38 | 18 | **105** |
| Win rate | 77,6% | 78,9% | 83,3% | **79,0%** |
| Rendimento | +27,7% | +52,6% | +38,8% | **+170,5%** |
| Max drawdown giornaliero | −10,6% | −11,1% | −3,6% | **−11,1%** |
| Aspettativa per trade | +0,53% | +1,16% | +1,87% | +0,99% |

Per anno: 2022 +14,2% · 2023 +11,8% · 2024 +9,7% · 2025 +39,2% · 2026 +38,8%.
Win rate sopra +1% sul capitale 63,8%, profit factor 2,43, durata media 3 giorni, leva media 1,4x.

**Walk-forward** (ricerca, notte 01:47): la fonte del delta taker scelta solo sul passato è la stessa in entrambe le finestre e resta
positiva fuori campione: 2024–25 +63,2% (DD −13,4%) contro H2 senza size +37,2%; 2026 +45,9% (DD −4,2%) contro +22,7%.

| 10.000 $ (size del piano v2, esposizione massima 5x) | 1x | 2x | 5x |
|---|---|---|---|
| Capitale finale | **27.056 $** | 55.053 $ | 121.995 $ |
| Max drawdown (giornaliero a 1x, per trade a 2x/5x) | −11,1% | −20,7% | −39,8% |
| Peggior trade | −5,6% | −11,2% | −21,3% |

2x e 5x moltiplicano la size di ogni trade con il tetto di esposizione a 5x del conto (5x solo come confronto: drawdown oltre il 40%).
Registro dei trade in stop con l'analisi di ciascuno: [research/LOSERS.md](research/LOSERS.md).

**Confronto con la strategia precedente** (segnale giornaliero, DCA a 3 tranche, stop 3 ATR, uscite a scaglioni, 49 trade):
+34,9% a 1x con drawdown giornaliero −28,1%. v2: **+170,5% con −11,1%**.

**Con slippage 0,2%** al rischio 4,67% (precedente valore dal vivo): +140,3%, DD −12,8%, WR 76,9%. Dal 2021 con slippage 0,2% il
rischio massimo che tiene la coda è 4,3%: è il valore scelto per il tool.
Al rischio di ricerca 5,24% e slippage 0,1%: +225,8%, DD −13,5%, 10.000 $ → 32.580 $.

### Limiti (onesti)
- **Bootstrap al limite**: al rischio di ricerca la probabilità di un drawdown oltre il 20% nei ricampionamenti è 15,0%, esattamente
  la soglia del criterio. Per questo il rischio dal vivo è più basso (4,67%). Alcuni vicini dei parametri (k 2,0, clip 0,12, W 0,7) la sforano.
- **Dipende dal delta della barra di conferma**: con il delta della barra precedente il vantaggio sparisce (2026 da +48,6% a +11,8%).
  Non è un errore di look-ahead (la barra è chiusa prima dell'ingresso), ma il dato va letto subito.
- **Latenza del perp**: l'archivio dei perp arriva con circa 1 giorno di ritardo; dal vivo il delta è spesso solo spot (regola prudente,
  nella ricerca spot da solo rende meno del mix: +206% contro +226%).
- **~1 ora di ritardo**: il controllo è orario, quindi l'ingresso reale avviene fino a circa un'ora dopo la chiusura 4h di conferma
  (in simulazione: all'apertura della barra successiva). Anche i dati giornalieri dei derivati possono arrivare in ritardo.
- 105 trade in sequenza: un trade spostato cambia il risultato di alcuni punti. Il registro reale parte dal 31/10/2026.
- Con stop vicino e target unico le perdite medie (−3,6% sul capitale) valgono circa una vincita e mezza (+2,3%).

La strategia giornaliera precedente resta nel codice (`radar/backtest.py`, `radar/research.py`) come banco di ricerca.

## Segnale settimanale (W2)

Secondo segnale reale, accanto a v2 (che non cambia). Per chi preferisce **poche operazioni grandi** a tante piccole.
Si guarda solo la **candela settimanale** (da lunedì a domenica, chiusura UTC della domenica); si entra o si esce all'apertura del lunedì.

1. **Il trend.** Long solo se la settimana chiude **sopra la media a 40 settimane** e la EMA 20 settimanale sale. Short solo in
   trend ribassista: chiusura sotto la media a 40 settimane, media a 40 in calo su 4 settimane, EMA 20 in calo.
2. **L'ingresso.** La settimana chiude dal lato giusto della **EMA 21 settimanale** e il flusso dei perp (CVD perp 14 giorni) va
   nella stessa direzione.
3. **Come.** Long in **spot, senza leva** (niente funding). Short in **perp**, con esposizione ridotta quando lo stop è lontano:
   lo stop iniziale non costa mai più del **25% del capitale** dedicato.
4. **L'uscita**, alla prima di tre: **trailing 2,5 ATR settimanali** dalla miglior chiusura giornaliera (controllato ogni ora);
   chiusura settimanale oltre la EMA 21; **distribuzione** (long: funding medio 7 giorni sopra 0,09% al giorno con flusso perp
   negativo; short: funding sotto −0,03% con flusso positivo). Stop iniziale a 2,5 ATR settimanali.

Su Telegram: **SEGNALE SETTIMANALE** con il piano (spot o perp, esposizione, importi, stop, uscite), **trailing aggiornato** quando
si sposta di oltre 1 ATR giornaliero, **allerta distribuzione**, **USCITA SETTIMANALE** con motivo e risultato, allerta in tempo
reale se il trailing viene toccato. Importi su `RADAR_CAPITAL` × `RADAR_WEEKLY_SHARE` (predefinito 1,0 = tutto il capitale:
**decidi tu** quanta parte dedicare al settimanale, ad esempio 0,5 per metà).

| Dal 01/01/2021 al 30/10/2026 (commissioni, funding e slippage 0,1%) | W2 |
|---|---|
| Trade | 19 (3,3 l'anno) |
| Win rate | 68% |
| Guadagno medio per trade | +13,4% sul capitale |
| Peggior trade | −18,3% |
| Rendimento | **+617,6%** (10.000 $ → 71.761 $; a 2x 178.309 $) |
| Max drawdown giornaliero | **−42,6%** (a 2x −70%) |
| MAR (rendimento / DD) | 14,5 |

Per anno: 2021 +135,4% · 2022 +19,4% · 2023 +42,1% · 2024 +54,3% · 2025 +1,9% · 2026 +14,2%.
Posizione al 30/10/2026: long in spot dal 24/08/2026 a 77.812 $.

**Rischio, detto chiaramente.** Il drawdown storico è **−42,6%** e nei ricampionamenti la probabilità di un drawdown oltre il 40% è
di circa **il 50%**: è un rischio da accettare consapevolmente. Prima del 2021 uno short (16/03/2020) senza tetto avrebbe perso
circa **−45%** in un solo trade; con il tetto sugli short la stessa operazione perde circa −18%. Il tetto è stato scelto **dopo** aver
visto i risultati (non era tra le varianti preregistrate), per prudenza sulla coda: non migliora il rendimento, limita il caso peggiore.
Pochi trade (19) vogliono dire statistiche fragili: un singolo trade cambia molto il totale. Il primo giro dal vivo mostra il long già
aperto come "posizione in corso", non come segnale nuovo. Codice: `radar/weekly.py`.

## Brand

<p><img src="brand/brand-board.png" alt="Brand board Radar Signal" width="100%"></p>

Simbolo: un radar ridotto all'essenziale (anello, fascio e blip). Wordmark `radarsignal` in Geist bold. Palette: Signal Blue `#3D5BFF`, Pulse Violet `#8B5CFF`, Blip Mint `#5EF0C4`, Night `#07080C`. Font: Geist, Geist Mono per etichette e chip, Doto per i numeri principali. File in `brand/` (PNG pronti, sorgente HTML in `brand/src/board.html`).

## Ciclo di miglioramento

Due giri al giorno (07:17 e 19:17 ora italiana) di ricerca e verifica, più i giri notturni orari "campione/sfidante" (22:47–06:47): ogni ora una linea di ricerca preregistrata prova a battere il campione (oggi v2) su rendimento a parità di rischio di coda, placebo, walk-forward e vicini dei parametri; un sistema su carta (H2 e v2, `radar/paper.py`) segue i candidati dal vivo. Al mattino un unico resoconto su Telegram. Ogni giro impara (lezioni apprese) e propone nuove idee, ciascuna affidata a un sotto-agente definito in `.claude/agents/`:

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

Alert inviati (tutti "RADAR SIGNAL BTC"): nuovo segnale in attesa di conferma 4h (soglia e scadenza), ingresso confermato con piano completo in dollari e leva sul capitale (`RADAR_CAPITAL`, predefinito 50.000 $; rischio base `RADAR_RISK`, predefinito 0.043), limit DCA eseguito, take profit, stop, uscita a tempo, segnale scaduto, livelli toccati in tempo reale (controllo orario su candele 1h: soglia di conferma, limit, stop, TP), dati non aggiornati da oltre 36 ore, riepilogo giornaliero (disattivabile con `RADAR_DAILY_BRIEF=0`).

## Uso locale

```bash
pip install -r requirements.txt
python -m radar.cli daily          # dati, segnale, alert, dashboard in site/
python -m radar.cli backtest       # strategia giornaliera precedente (ricerca)
python -m radar.research           # scorecard della strategia
python -m radar.cli test-telegram  # verifica il bot
```

## Struttura

```
radar/data.py         download e cache incrementale (data/*.csv)
radar/features.py     CVD spot/perp, funding, OI, long/short, basis, ATR, trend
radar/strategy.py     6 setup, parametri, piano DCA
radar/backtest.py     strategia giornaliera precedente (ricerca)
radar/live.py         segnali reali v2: stato (conferma, ingresso, trade), storico, eventi
radar/paper.py        motore v2/H2 su candele 4h e conti su carta
radar/research.py     scorecard e gate di promozione
radar/telegram.py     messaggi
radar/dashboard*.py   dashboard (dark-first, light/dark, mobile, installabile)
brand/                logo, icona app, banner, social preview, brand board (sorgenti in brand/src)
.claude/agents/       sotto-agenti del ciclo orario (scan, apprendimento, miglioramento)
radar/zones.py        previsione della regione di prezzo a 7 giorni
radar/news.py         notizie RSS classificate per impatto e calendario economico
radar/intraday.py     controllo orario dei livelli v2 (alert in tempo reale)
radar/weekly.py       segnale settimanale W2: storico, stato, eventi, controllo orario del trailing
radar/liquidations.py raccolta delle liquidazioni reali OKX da oggi (data/liquidations.csv)
radar/observe.py      osservazione su carta di altri asset (SOL)
tests/                test del motore di backtest (python -m radar.cli test)
```

Fonti dati: Binance (spot, perp USDT-M, open interest, long/short ratio), OKX per i giorni non ancora archiviati, alternative.me (Fear & Greed).

Strumento di analisi, non consulenza finanziaria.
