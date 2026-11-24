<p align="center"><img src="brand/banner.png" alt="Radar Signal BTC" width="100%"></p>

# Radar Signal BTC

Segnali di trading su **Bitcoin** con **una sola strategia: W3.2 settimanale**, in uso con capitale reale. Poche operazioni
grandi (2–3 l'anno, da settimane a mesi): long in **spot senza leva**, short in perp solo in trend ribassista confermato,
**perdita allo stop iniziale al massimo del 25%** della quota. Intorno alla strategia: dashboard aggiornata ogni ora, order book
multi-borsa, liquidazioni, notizie e calendario, avvisi su Telegram.
Dal 22/11/2026 W3.2 gira anche su **ETH** con le stesse regole: con **capitale separato**: 10.000 $ su BTC e 10.000 $ su ETH nei backtest; dal vivo BTC usa `RADAR_CAPITAL`, ETH `RADAR_ETH_CAPITAL` (predefinito 30.000 $).

## Performance di W3.2

Backtest su dati reali di mercato (archivio Binance), BTC, 10.000 $ a 1x, commissioni, slippage e funding inclusi, decisione solo
su candele settimanali chiuse. Dati congelati al 15/11/2026; il valore aggiornato ogni ora è sulla dashboard.

| Strategia | In uso | Rischio allo stop | 10.000 $ dal 2021 → | Max drawdown | Trade | Win rate | 2018–20 (DD) |
|---|---|---|---|---|---|---|---|
| **W3.2** | **dal 22/11/2026** | **25%** | **78.474 $ (x7,8)** | **−21,1%** | **13** | **92%** | **25.142 $ (−37,3%)** |
| **W3.2 su ETH** (capitale separato) | **dal 22/11/2026** | **25%** | **34.760 $ (x3,5)** al 10/11 | **−27,5%** | **15** | **60%** | — |
| Tenere BTC | — | — | 22.594 $ (x2,3) | −76,6% | — | — | — |

ETH: stesse regole e parametri di BTC, flusso e funding dei perp ETH (archivio Binance + OKX provvisorio), 10.000 $ dal 2021 al
10/11/2026 (numeri di [`research/w32_multi`](research/w32_multi/README.md), riprodotti dal tool in `tests/test_eth.py`; 37.575 $
al 15/11). ETH vale meno di BTC per unità di drawdown (CAGR/DD 0,86 contro 2,00, WR al limite del 60%). Capitale separato da
quello di BTC (10.000 $ ciascuno): scelta dell'utente del 22/11/2026.
Anni ETH: 2021 +104,3% · 2022 −3,9% · 2023 +21,7% · 2024 +27,9% · 2025 +14,0% · 2026 +7,9% (al 15/11).

| Anno | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (al 15/11) |
|---|---|---|---|---|---|---|
| Rendimento W3.2 | +91,9% | +19,4% | +46,1% | +102,7% | +4,9% | +10,2% |
| Drawdown nell'anno | −13,8% | −13,4% | −18,1% | −11,9% | −18,7% | −18,3% |

<details><summary>I 13 trade dal 2021</summary>

| Ingresso | Lato | Prezzo | Uscita | Prezzo | Motivo | Esposizione | Risultato sul capitale |
|---|---|---|---|---|---|---|---|
| 01/02/2021 | long | 33.126 | 22/02/2021 | 57.355 | distribuzione | 0,72 | +52,2% |
| 02/08/2021 | long | 39.890 | 27/09/2021 | 43.118 | EMA 21 | 0,54 | +4,3% |
| 04/10/2021 | long | 48.248 | 08/11/2021 | 63.210 | distribuzione | 0,68 | +20,9% |
| 03/01/2022 | short | 47.239 | 28/03/2022 | 46.875 | EMA 21 | 0,64 | +1,0% |
| 15/08/2022 | short | 24.281 | 16/01/2023 | 20.894 | EMA 21 | 0,56 | +8,3% |
| 23/01/2023 | long | 22.729 | 17/08/2023 | 25.966 | trailing | 0,95 | +13,3% |
| 23/10/2023 | long | 30.022 | 01/01/2024 | 42.241 | distribuzione | 1,00 | +40,5% |
| 12/02/2024 | long | 48.348 | 11/03/2024 | 68.887 | distribuzione | 1,00 | +42,2% |
| 23/09/2024 | long | 63.642 | 26/02/2025 | 85.256 | trailing | 0,91 | +30,8% |
| 28/04/2025 | long | 93.843 | 10/10/2025 | 104.715 | trailing | 0,99 | +11,3% |
| 01/12/2025 | short | 90.270 | 27/04/2026 | 78.736 | EMA 21 | 0,89 | +11,9% |
| 25/05/2026 | short | 76.988 | 20/08/2026 | 73.287 | trailing | 1,00 | +5,7% |
| 24/08/2026 | long | 77.812 | 09/11/2026 | 74.777 | EMA 21 | 1,00 | −4,1% |

Short in corso dal 16/11/2026 a 65.286 $ (esposizione circa 0,97).
</details>

**Risultati dal vivo:** il registro dei trade reali (`/entrato`, `/uscito`) non contiene ancora operazioni registrate; quando ci
saranno, la dashboard mostra il confronto esecuzione/segnale.

**Come leggere questi numeri.** Sono il miglior risultato fra le versioni testate, non una promessa:
- 13 trade in 6 anni, e 3 fanno il 59% del rendimento;
- la domenica è stata il giorno di decisione più fortunato: con gli altri giorni la mediana è circa x6;
- dal 2021 nessuno stop pieno, che con il 25% costerebbe un quarto della quota; nel 2018–20 il drawdown è stato −37%.

Attesa ragionevole su un periodo simile: circa x4–x6, con drawdown fino a −35/−40%. Altre versioni e studi:
[`memoria/01-strategia/STRATEGIE.md`](memoria/01-strategia/STRATEGIE.md).

**Dashboard:** https://andreagalanti91.github.io/radar/ · **Bot Telegram:** [@CryptoRadarGalaBot](https://t.me/CryptoRadarGalaBot)

## Indice

- [Performance](#performance-di-w32) · [Strategia W3.2](#strategia-w32) · [Dashboard](#dashboard) · [Automazioni e avvisi](#automazioni-e-avvisi)
- [Order book e liquidazioni](#order-book-e-liquidazioni) · [Ricerca](#ricerca) · [Come lavora Claude](#come-lavora-claude)
- [Configurazione](#configurazione) · [Uso locale](#uso-locale) · [Struttura del repository](#struttura-del-repository) · [Brand](#brand)

## Strategia W3.2

Codice: [`radar/weekly.py`](radar/weekly.py) · scheda: [`memoria/01-strategia/W3.2.md`](memoria/01-strategia/W3.2.md).
Si guarda solo la **candela settimanale** chiusa la domenica alle 00:00 UTC; si esegue il lunedì all'apertura.

| | Long | Short |
|---|---|---|
| Trend | chiusura > SMA 40 settimanale, EMA 20 in salita | chiusura < SMA 40 in calo su 4 settimane, EMA 20 in calo |
| Ingresso | chiusura > EMA 21 e flusso perp > 0; nei trend vecchi (≥ 16 settimane) MACD 8/21/5 sopra segnale e zero | chiusura < EMA 21 e flusso perp < 0 |
| Mercato | spot 1x | perp 1x |
| Uscita (la prima) | trailing 2,5 ATR settimanali a cricchetto · chiusura settimanale oltre la EMA 21 · distribuzione (funding 7 giorni alto con flusso contrario) | stesse regole, specchiate |

Dimensione: esposizione = min(1, 25% / distanza dello stop iniziale). Flusso = media degli ultimi 3 giorni disponibili di pf14z,
identico dal vivo e nel backtest.

**Asset e capitale** (dal 22/11/2026): le stesse regole girano su BTC ed ETH (`weekly.evaluate(f, asset=...)`, `ASSET_LIST`).
Capitale BTC = `RADAR_CAPITAL` × `RADAR_WEEKLY_SHARE`; capitale ETH = `RADAR_ETH_CAPITAL` (predefinito 30.000 $), separato
(0,70). Ciascun asset ha il suo tetto di rischio 25% allo stop **sulla propria quota** (con 50.000 $: BTC 35.000 $, ETH 15.000 $;
uno stop pieno costa al massimo ~8.750 $ su BTC e ~3.750 $ su ETH). Dati ETH: `data/eth_spot.csv`, `eth_perp.csv`, `eth_funding.csv`,
`eth_metrics.csv`, dalle stesse fonti di BTC (spot data-api.binance.vision, perp e funding archivio data.binance.vision, giorni
non ancora archiviati da OKX con `source = okx`); Binance fapi resta bloccato dagli USA. Report: `report["weekly"]` = BTC
(invariato), `report["weekly_eth"]` = ETH. Avvisi Telegram separati con l'asset nel titolo ("RADAR SIGNAL ETH · …": segnale,
ingresso, trailing, uscita, stop in tempo reale, soglie d'allarme, coerenza), stato in `state.json` sotto `weekly_eth`; una riga
ETH nel riepilogo "Oggi" e nel messaggio di salute. Se i dati ETH mancano il giro di BTC prosegue e arriva l'avviso sulla fonte.

Cosa fare con gli avvisi:
1. **Segnale settimanale**: entra lunedì all'apertura con l'importo indicato e metti lo stop iniziale.
2. **Trailing aggiornato**: sposta lo stop al nuovo livello.
3. **Uscita settimanale**: chiudi lunedì all'apertura; se il trailing viene toccato l'avviso arriva entro l'ora.
4. Registra ogni operazione con `/entrato` e `/uscito`: il registro confronta l'esecuzione con il segnale.

W3.2 non si cambia senza approvazione esplicita dell'utente ([`memoria/05-regole`](memoria/05-regole/REGOLE.md)).

## Dashboard

Pensata per il telefono (installabile dalla schermata Home), tema scuro e chiaro, prezzo live.

| Sezione | Contenuto |
|---|---|
| **Oggi** | panoramica: prezzo, riga di stato delle posizioni (BTC ed ETH, porta a Posizioni), card "Livelli e probabilità a 30 giorni" ridotta alla forbice (intervalli 80% e 50%, primo supporto, prima resistenza, liquidazioni long e short più vicine stimate e on-chain, trailing W3.2; "Apri nel Grafico" per tutto il resto), riquadro Contesto in tre tessere (Mercato, Fed, Dati), notizie del giorno |
| **Posizioni** | posizione W3.2 BTC, card compatta ETH (stato, P&L sulla quota, stop/trailing, esposizione), Pre-analisi (solo BTC) della prossima chiusura (soglie, stop, flusso, funding); da qui "Regole complete" apre la pagina *Metodo* |
| **Grafico** | solo BTC: candele e volumi a 4h, 1D, 1W, 1M; livelli della mappa unica come linee con interruttori (supporti, resistenze, liquidazioni long e short stimate/on-chain, medie, Fibonacci, storico, trailing W3.2, zone come fasce; scelte salvate sul dispositivo), mirino con OHLC e volume, marcatori dei trade W3.2 su 1D/1W, ultimo prezzo, schermo intero; sotto la tabella completa di livelli e zone (clic su una riga → il grafico la mostra) |
| **Movimenti** | trade di W3 con curva di equity contro BTC, storico W3.2 su ETH (riassunto e trade), registro dei trade reali, simulatore del capitale |
| **Notizie** | calendario economico, riunioni FOMC e BCE, notizie classificate per impatto |
| *Liquidazioni (spenta)* | la pagina resta in `radar/pages/liquidazioni.html` ma non ha voce di menu, non si inizializza e non apre connessioni; `#liquidazioni` porta a Grafico; si riaccende con `LIQ_ON = true` in `radar/dashboard_template.html` |
| *Book (spento)* | heatmap dell'order book: la pagina resta in `radar/pages/book.html` ma non ha voce di menu né apre connessioni; si riaccende con `BOOK_ON = true` in `radar/dashboard_template.html` |

Il riquadro **Contesto** ([`radar/context.py`](radar/context.py), `report["context"]`) descrive in tre righe lo stato del mercato
(trend rispetto alla media a 200 giorni, volatilità) e della politica economica (tasso Fed e ultima mossa, bilancio e liquidità
netta, CPI annuo, VIX, prossima riunione FOMC); il dettaglio con le date dei dati è dietro "Dettagli". È contesto, non segnale: non
mostra probabilità né medie storiche, perché nei test regimi e politica economica non hanno anticipato la direzione
([`research/previsionale2`](research/previsionale2/README.md), lezione 113); non entra in W3.2. Dati Fed da FRED al massimo una
volta al giorno, cache in `data/context.csv`: se la fonte non risponde resta l'ultimo dato con la sua data.

**Motore unico.** `report["livelli"]` ([`radar/livelli.py`](radar/livelli.py)) è la sola fonte di supporti, resistenze, medie,
Fibonacci, livello storico, liquidazioni (stima e on-chain, separate) e zone per Oggi, Grafico (linee e tabella), Pre-analisi
(`radar/preview.py`: righe S/R e "Liquidazioni più vicine") e riepilogo Telegram "Oggi" (R1/S1): nessun ricalcolo dei cluster nel
browser. Il browser ricalcola solo distanze, probabilità di tocco e intervalli sul prezzo mostrato in testa alla pagina (live, o
l'ultima chiusura dichiarata se il live manca) con `report["livelli"]["tocco"]`: quantili dei cammini del cono
(`cone.touch_grid`; stessa funzione in Python `cone.grid_touch_prob` e in JS `lvTouch`, confrontate in `tests/test_grafico.py`).
Il grafico usa `report["livelli"]["serie"]` (giornaliero completo con volumi; 1W e 1M aggregati nel browser); il 4h si scarica
dal browser da Binance (`api.binance.com`, poi `data-api.binance.vision`) o, in riserva, da Coinbase (orarie aggregate a 4 ore).
`radar/levels.py` resta interno: confluenza della mappa liquidazioni (liqmap), liqcascade e livelli della card storica del cono.

La card **Livelli e probabilità a 30 giorni** (dal 24/11 la scala completa, le zone e il grafico sono nel Grafico) unisce la mappa dei livelli ([`radar/livelli.py`](radar/livelli.py),
`report["livelli"]`) e il cono ([`radar/cone.py`](radar/cone.py), `report["cone"]`), solo BTC. In alto: prezzo (ultima chiusura
giornaliera completa), intervallo probabile all'80% e al 50% fra 30 giorni, primo supporto e prima resistenza, prime liquidazioni
di long sotto e di short sopra, ATR 14 giornaliero. Poi la scala dei livelli dal più alto al più basso (in vista il più vicino di
ogni tipo, gli altri con "Mostra tutti"): supporti e resistenze (minimi e massimi di swing settimanali a 5 settimane, attivi 3 anni e
finché una chiusura giornaliera non li rompe, più il minimo delle ultime 5 settimane non confermato), medie a 50/200 giorni e
40/200 settimane, Fibonacci 50/61,8/78,6% fra minimo del ciclo 2022–23 e massimo storico, livello storico 69.000 $ (riferimento,
non resistenza), liquidazioni e trailing della posizione W3.2 aperta; per ognuno la **probabilità di toccarlo entro 30 giorni**,
calcolata con gli stessi cammini del cono. Infine le zone dove più livelli coincidono (a meno del 3,2%), con le liquidazioni nella
zona e la probabilità di raggiungerne il bordo più vicino. Nei Dettagli: grafico dell'ultimo anno con una linea per livello, fonti
delle liquidazioni, nota fissa e affidabilità del cono. Definizioni e numeri della nota da
[`research/livelli_import`](research/livelli_import/LIVELLI_BTC.md).

Il cono è calcolato dalla volatilità attuale, **non è una previsione di direzione** (lezioni 112–113): bootstrap a blocchi dei
rendimenti storici riscalati alla volatilità di oggi, con la sola crescita media storica; nello studio di calibrazione
([`research/cono30`](research/cono30/README.md)) l'intervallo 80% ha contenuto il prezzo nel 78% dei casi (2018–26). I livelli
sono contesto, non segnali. Né cono né livelli entrano in W3.2. Ogni previsione del cono è registrata in `data/cone_log.csv` e
confrontata con il prezzo dopo 30 giorni (copertura dal vivo).

Liquidazioni nella mappa, con la fonte su ogni riga: i 3 cluster significativi più vicini per lato della mappa **stimata** del tool
(`radar/liqmap.py`, "stima Radar (OI Binance+OKX)"), i 3 livelli **reali** on-chain più vicini per lato di Hyperliquid e Lighter
(`report["liqmap"]["onchain"]`) e, se presente, il file facoltativo `data/coinglass_levels.json`, compilato a mano leggendo la mappa
di Coinglass (nessuno scraping):

```json
{"data": "2026-11-24 09:01", "long": [[54145, 0.7487], [51368, 1.18]], "short": [[76915, 0.7208], [91076, 0.8396]]}
```

`data` è l'ora italiana della lettura (AAAA-MM-GG HH:MM); `long` sono le liquidazioni di long (sotto il prezzo) e `short` quelle di
short (sopra), come coppie [prezzo in $, miliardi di $]. Le righe compaiono con fonte "Coinglass, GG/MM/AAAA HH:MM" (stime). Un file
più vecchio di 7 giorni è **ignorato** e la card lo dice nei Dettagli; un file illeggibile è ignorato allo stesso modo.

La pagina *Metodo* (regole complete e limiti) si apre dalla card della posizione. La sezione Wallet è in pausa dal 22/11/2026
(`RADAR_WALLETS=0`). Le pagine stanno in [`radar/pages/`](radar/pages/) e sono incluse da [`radar/dashboard.py`](radar/dashboard.py).

## Automazioni e avvisi

| Quando | Dove | Cosa fa |
|---|---|---|
| Ogni ora | [`daily.yml`](.github/workflows/daily.yml) → `python -m radar.cli daily` | dati, segnale W3.2, controlli di coerenza, soglie d'allarme, order book, liquidazioni, notizie, avvisi, dashboard su Pages |
| Ogni ora, catena di ~5 ore | [`liqsnap.yml`](.github/workflows/liqsnap.yml) | livelli di liquidazione on-chain e avvio affidabile di `daily.yml` (il cron di GitHub è best-effort) |
| Ogni 5 minuti | [`wallets.yml`](.github/workflows/wallets.yml) | sentinella wallet Hyperliquid (in pausa) |
| 00:00 UTC | dentro il giro orario | riepilogo giornaliero "Oggi" su Telegram |
| Lunedì 08:41 | attività pianificata di Claude, testo in [`deploy/RESOCONTO-SETTIMANALE.md`](deploy/RESOCONTO-SETTIMANALE.md) | resoconto della settimana chiusa |

Avvisi della strategia: segnale settimanale con piano in dollari, trailing aggiornato, allerta distribuzione, uscita, trailing
toccato in tempo reale. Avvisi di salute: dati fermi, buchi nei dati di W3.2, storico riscritto, decisione cambiata con i dati
definitivi ([`radar/coherence.py`](radar/coherence.py)), equity −15% dal massimo o 2 stop consecutivi ([`radar/guard.py`](radar/guard.py)).

**Comandi del bot** ([`radar/journal.py`](radar/journal.py)), accettati solo dalla chat `TELEGRAM_CHAT_ID`, risposta entro un'ora:

| Comando | Esempio | Cosa registra |
|---|---|---|
| `/entrato <prezzo> [quantità_btc] [long\|short]` | `/entrato 65286 0,3 short` | ingresso |
| `/uscito <prezzo> [motivo]` | `/uscito 60000 trailing` | uscita e risultato |
| `/exchange bybit\|okx` | `/exchange okx` | exchange usato |
| `/registro` · `/aiuto` | | ultimi trade con slippage e ritardo · elenco comandi |

## Order book e liquidazioni

- **Pagina Book (nel browser)**: Binance futures e spot, OKX, Bybit, Coinbase, Hyperliquid in WebSocket; storia dall'apertura
  della pagina. Muro = fascia con almeno 3 volte la liquidità media e il doppio delle fasce vicine; "ritirato" se scompare con il
  prezzo entro lo 0,3% senza attraversarlo (possibile spoofing), "eseguito" se il prezzo lo attraversa.
- **Registro lato server** ([`radar/orderbook.py`](radar/orderbook.py), ogni ora): muri di sei borse con l'esito al giro
  successivo (`data/book_walls.csv`) e una riga di sentiment per giro (`data/book_sentiment.csv`).
- **Sentiment** S = 0,5 · squilibrio del book entro ±1% + 0,5 · sbilancio delle liquidazioni a 30 minuti; non calcolato sotto
  250.000 $ di liquidazioni. **È descrittivo, non un segnale**: nei test non ha anticipato il prezzo a 1, 4 o 24 ore
  ([`research/book_sentiment`](research/book_sentiment/README.md), lezione 108). Prossima verifica: febbraio 2027.
- **Mappa delle liquidazioni** ([`radar/liqmap.py`](radar/liqmap.py)): STIMA da open interest; reali solo gli eventi raccolti e i
  prezzi di liquidazione dei conti Hyperliquid.

Server negli USA: Binance futures e Bybit rispondono 451/403, si usano archivio Binance, OKX, Coinbase, Kraken, Hyperliquid.

## Ricerca

Ogni idea si preregistra (PREREG committato da solo prima dei risultati), si testa dal 01/01/2021 su 10.000 $ con periodi
separati, placebo, vicini e correzione per test multipli, poi passa da una revisione critica separata.
**Indice di tutti gli studi: [`research/README.md`](research/README.md).** Diario completo e lezioni: [`RESEARCH.md`](RESEARCH.md).

Conclusione generale: dal 2021 solo il trend settimanale regge; tutto il resto è contesto. Ultimi studi (22/11/2026):

| Studio | Esito | Lezione |
|---|---|---|
| Swing brevi su S/R settimanali, stop 5–10%, TP 10–15% su BTC | 10.000 → 5.626 $; 0/405 configurazioni battono la strategia in uso; il 70/30 peggiora la strategia in uso | 106 |
| Stessa strategia su 15 asset (indici, oro, argento, petrolio, azioni) | 0/15 validi, nessuno sopra il buy & hold | 107 |
| Sentiment da order book e liquidazioni | 0/14 test significativi; descrittivo | 108 |
| Ingressi e uscite a scaglioni, TP, stop, distribuzione sulla strategia in uso | nessuna delle 14 varianti la batte | 105 |

## Come lavora Claude

- Istruzioni del progetto: [`CLAUDE.md`](CLAUDE.md). Memoria per una nuova sessione: [`memoria/`](memoria/00-inizia-qui/README.md),
  da leggere in ordine 00 → 05.
- Ogni richiesta passa dalla skill **gengar** ([`.claude/skills/gengar`](.claude/skills/gengar/SKILL.md)); i lavori lunghi tengono un
  file `stato/STATO-<argomento>.md` (cartella stato/) per riprendere dopo un'interruzione.
- Agenti per mansione in [`.claude/agents/`](.claude/agents/), ognuno con file suoi; il commit lo fa la sessione principale.

| Agente | Ruolo |
|---|---|
| `radar-ui` | dashboard e pagine, verifica a 400 e 1280 px, tema chiaro e scuro |
| `radar-dati` | fonti dati e raccoglitori |
| `radar-ricerca` | backtest in `research/`, mai nel tool |
| `radar-review` | revisione critica (avvocato del diavolo) |
| `radar-verifica` | controllo del sito pubblicato dopo ogni deploy |
| `radar-wallet` | Hyperliquid: sentinella e balene |
| `radar-plan` · `radar-scan` · `radar-learn` · `radar-improve` | ciclo di ricerca automatico (non attivo) |

Prima di pubblicare: test che riproduce il problema, suite verde, render a 400 e 1280 px con dati reali, deploy, verifica sul sito.

## Configurazione

*Settings → Secrets and variables → Actions*. I valori dei secret non vanno mai scritti nel codice né in chat.

| Nome | Tipo | Predefinito | Uso |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | secret | – | token del bot |
| `TELEGRAM_CHAT_ID` | secret | – | chat che riceve gli avvisi e da cui si accettano i comandi |
| `RADAR_CAPITAL` | variabile | 30000 | capitale su cui si calcolano i piani in dollari |
| `RADAR_WEEKLY_SHARE` | variabile | 1.0 | quota del capitale dedicata a W3.2 |
| `RADAR_ETH_SHARE` | variabile | 0.30 | quota del capitale W3.2 su ETH (0 = ETH escluso dai piani in dollari); BTC = 1 − quota |
| `RADAR_WALLETS` | variabile | 0 | `1` riaccende la sezione Wallet e la sentinella |
| `RADAR_V2_ALERTS` | variabile | 0 | `1` riaccende gli avvisi della vecchia strategia giornaliera v2 |

GitHub Pages: *Settings → Pages → Source: GitHub Actions*. Il sito si pubblica dal branch predefinito.

## Uso locale

```bash
pip install -r requirements.txt
python -m radar.cli daily                    # dati, segnale, avvisi, dashboard in site/
python3 -m unittest discover -s tests -q     # test (unittest, non pytest)
python -m radar.cli test-telegram            # verifica il bot
```

## Struttura del repository

```
radar/                 il tool
  cli.py               giro orario: orchestra tutti i moduli
  weekly.py            W3.2: storico, stato, avvisi, controllo orario del trailing
  preview.py           Pre-analisi della prossima chiusura
  data.py, features.py dati (archivio Binance, OKX provvisorio) e indicatori (flusso pf14z, funding, ATR)
  guard.py, coherence.py, provlog.py   soglie d'allarme, controlli di coerenza, registro provvisori/definitivi
  orderbook.py         registro dei muri e del sentiment, previsione 1h/4h
  liqmap.py, liqsnap.py, liqsources.py, liqcascade.py, liquidations.py   liquidazioni (stime e reali)
  news.py, macro.py, context.py   notizie, calendario, chiusure multi-asset, riquadro Contesto (mercato e Fed)
  telegram.py, journal.py, xinbox.py    messaggi, registro dei trade reali, post del trader seguito
  dashboard.py, dashboard_template.html, pages/   dashboard
  wallets.py, scout.py sentinella e balene Hyperliquid (in pausa)
  live.py, strategy.py, backtest.py, paper.py, lab.py, …   strategia v2 e banco di ricerca (spenti)
research/              studi: un cartella per studio con PREREG, script, risultati e README (indice in research/README.md)
memoria/               memoria del progetto per nuove sessioni (00 → 05)
tests/                 test unittest
data/                  dati e stato aggiornati dal giro orario (non modificare a mano)
deploy/                istruzioni operative (liqstream su VM europea, resoconto del lunedì)
brand/                 logo, icone, banner (sorgenti in brand/src)
.claude/               agenti e skill di Claude
.github/workflows/     daily.yml, liqsnap.yml, wallets.yml
RESEARCH.md            diario della ricerca, lezioni numerate, errori operativi da non ripetere
stato/                 file di stato dei lavori lunghi di Claude
```

## Brand

<p><img src="brand/brand-board.png" alt="Brand board Radar Signal" width="100%"></p>

Simbolo: un radar essenziale (anello, fascio, blip) in una tile indaco. Wordmark `radar` + `signal` in Inter, con `signal` in
indaco `#2f4cf0`; blip menta. Ispirazione: il linguaggio pulito delle piattaforme fintech, senza riprendere marchi altrui.
Regole, palette, area di rispetto e misure minime: [`brand/DESIGN.md`](brand/DESIGN.md); sorgente unica `brand/src/brand.html`.

Strumento di analisi, non consulenza finanziaria. I risultati passati non garantiscono quelli futuri.
