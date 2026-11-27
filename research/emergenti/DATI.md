# emergenti · fase 1 · DATI E CONTEGGI (nessun rendimento) · 27/11/2026

**Sintesi.** Universo = top 500 CoinGecko di oggi ∪ top 200 CoinMarketCap a ogni inizio d'anno 2020–2026 (Common Crawl):
819 monete, 158 escluse, **661 incluse**; **emergenti 503** (330 "storiche" punto nel tempo, 290 "di oggi"); 337 con dati,
304 con perp e taker buy, **288 con la versione completa W3.2**, 285 con almeno un ingresso. Dal 2021 W3.2 (com'è) dà **1.190
ingressi su monete emergenti al momento del segnale** (463 long, 727 short). **Conflitto stop/liquidazione: lo stop di W3.2 è
oltre la liquidazione a 5x nel 100% degli ingressi e a 2x nel 52% dei long e nel 93% degli short** (distanza mediana dello
stop 50% sui long, 83% sugli short; BTC 21–28%). Con le monete di oggi 101–500 (vista con sopravvivenza) i numeri sono uguali.

## 1. Fonti (tutte pubbliche, User-Agent `radar-research-script/1.0`, pause rispettate)
- **Oggi**: CoinGecko `/api/v3/coins/markets` (vs_currency=usd, order=market_cap_desc, per_page=250, pagine 1–2), 27/11/2026
  09:28 UTC (`cg_fetch.py`, `data/raw/cg/top500.json`). Categorie d'esclusione dalla stessa API (pagine 1–3); `tokenized-products`
  e `real-world-assets-rwa` non scaricate (429): per la prima vale il file di w32_asset2 (pagina 1, 25/11).
- **Storiche (contro la sopravvivenza)**: istantanee CoinMarketCap `/historical/<data>/` lette da **Common Crawl**
  (`data.commoncrawl.org`, indice CDX con richieste Range, codice `w32_asset2/crypto/cc.py`; non dal sito CMC):
  20191229 (CC-MAIN-2021-04, già in w32_asset2), **20201227** (CC-MAIN-2021-04), **20220102** (CC-MAIN-2022-49), **20230101**
  (CC-MAIN-2023-50), **20231231** (CC-MAIN-2024-42), **20241228** (CC-MAIN-2026-43), **20251116** (CC-MAIN-2026-08; nessuna
  istantanea fra il 17/11/2025 e il 01/01/2026 nell'archivio). Ogni pagina ha **solo 200 righe**: la classifica storica 201–500
  non è ottenibile (le pagine CoinGecko `?page=N` archiviate sono sporadiche). `snapshots.py`, `data/snapshots.csv`.
- **Operabilità**: Bitget `/api/v2/mix/market/contracts?productType=USDT-FUTURES` (898 contratti, `launchTime`) e spot; OKX
  `/api/v5/public/instruments` SWAP (554, `listTime`) e SPOT; elenco dell'archivio Binance dal listing S3 pubblico (anche i
  delistati: 1.092 perp, 3.769 spot). `ops_fetch.py`, `data/raw/ops/`. Le date sono quelle dichiarate (possono essere riaperture)
  e **solo per gli strumenti vivi oggi**: per il passato l'operabilità su Bitget/OKX non è ricostruibile.
- **Prezzi**: archivio `data.binance.vision` (spot 1d e perp USDT-M 1d con taker buy, funding mensile), fine 24/11/2026, codice di
  `w32_asset2/crypto/fetch.py`; riusate le 497 serie già scaricate da w32_asset2 (stessa fonte e fine), scaricate qui 573 serie
  nuove senza errori. Perp OKX (candele + volumi taker rubik, funding ~3 mesi) solo per 12 monete senza perp Binance, con le
  funzioni di `radar/scanner.py` (sola lettura). Cache dello scanner non necessaria (sottoinsieme di w32_asset2).
- Composizione per moneta (`build.py`, funzioni di `w32_asset2/crypto/build.py`: catene di ticker, riscalature 1000x, giorni a
  volume zero tolti): `data/coins/` (26 MB, fuori da git come `data/raw/`; si rigenerano con gli script).

## 2. Universo ed esclusioni (`universe.py`, `finalize.py`, `data/universe.csv`)
- Top 500 di oggi: 139 escluse (72 stablecoin, 40 RWA/fondi, 16 azioni tokenizzate, 8 oro/argento, 3 wrapped/bridged), 361
  incluse. Istantanee: tag CMC, simboli e categorie CoinGecko (stablecoin, wrapped, oro). Lasciati dentro (governance, non
  derivati): LDO, JTO, LISTA, ANKR, FXS, RPL, TRIBE, STAKE, BTG, SPX.
- **Controllo dell'abbinamento per prezzo** (nuovo rispetto a w32_asset2): prezzo CoinGecko di oggi e prezzo CMC di ogni
  istantanea contro la chiusura Binance dello stesso giorno, rapporto in [0,5; 2] (con le catene BTT→BTTC e NPXS→PUNDIX
  riscalate): 383 verificate, 14 non verificabili (nessun prezzo di confronto o quotazione Binance successiva all'ultima classifica:
  STEEM, SNT, ARK, QKC, MLN, ADX, ORBS, METIS, CFG, EWT; tenute), **6 abbinamenti errati, dati tolti**: META (MetaDAO ≠ META
  Binance), ADI e PURR (perp OKX di altre monete), LA, NET, BZ (ticker riusati). ONE: il rank di oggi è di ONEchain, i dati
  sono di Harmony (rank di oggi tolto).

## 3. Definizione di "emergente" (fissata qui, prima dei rendimenti)
**Emergente alla data D = rank 101–200 nell'istantanea CMC più recente prima del 1° gennaio dell'anno di D** (punto nel tempo,
senza sopravvivenza). Motivo: è misurabile alla data senza futuro, coincide con "poco capitalizzata ma quotata", e l'età si usa
come filtro separato (H-b) perché W3.2 richiede comunque 40 settimane di prezzi (le monete quotate da meno di ~10 mesi non hanno
segnali). Il limite 200 viene dalle fonti storiche. "Emergente di oggi" = CoinGecko 101–500 del 27/11/2026: serve per il periodo
in avanti e come vista descrittiva (contiene solo le sopravvissute).

| | monete | con dati | perp+taker | versione completa | storia prezzi mediana (anni) | versione completa mediana | stop mediano per moneta | monete con stop mediano oltre liq. 2x / 5x | perp oggi Bitget / OKX |
|---|---|---|---|---|---|---|---|---|---|
| Emergenti storiche | 330 | 257 | 226 | 221 | 4,73 | 2,76 | 72% | 207 / 220 su 220 | 177 / 114 |
| Emergenti di oggi 101–500 | 290 | 187 | 179 | 166 | 2,74 | 1,99 | 76% | 157 / 163 su 163 | 166 / 116 |
| Unione | 503 | 337 | 304 | 288 | 3,61 | 2,32 | 75% | 272 / 285 su 285 | 250 / 161 |
| Top 100 di oggi (confronto) | 70 | 59 | 58 | 57 | 5,47 | 3,45 | 54% | 34 / 56 su 56 | 57 / 52 |

Senza dati: 166 delle 503 emergenti (soprattutto token del 2020–21 mai quotati con perp Binance o morti; 73 delle storiche).

## 4. Per anno · idonee in avanti al 1° gennaio e ingressi W3.2 (emergenti al segnale)
"Idonee" = rank 101–200 nella classifica dell'anno, dati vivi al 1/1 e versione completa W3.2 prima del 1/1. Gli ingressi
contano anche le monete diventate complete durante l'anno (ammissibili nella valutazione se erano nella lista del 1/1).

| Anno | 101–200 incluse | dati vivi 1/1 | idonee (completa) | ≥ 52 sett. | ingressi | long | short | long con / contro BTC | short con / contro BTC | stop mediano | oltre liq. 2x | oltre liq. 5x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2021 | 98 | 43 | 4 | 17 | 79 | 73 | 6 | 27 / 0 | 0 / 0 | 66% | 62 | 79 |
| 2022 | 95 | 69 | 30 | 45 | 119 | 9 | 110 | 0 / 6 | 60 / 0 | 121% | 119 | 119 |
| 2023 | 98 | 74 | 43 | 64 | 184 | 98 | 86 | 87 / 4 | 5 / 70 | 58% | 133 | 184 |
| 2024 | 96 | 76 | 47 | 61 | 281 | 166 | 115 | 70 / 0 | 0 / 63 | 53% | 163 | 281 |
| 2025 | 94 | 84 | 54 | 57 | 273 | 57 | 216 | 44 / 1 | 16 / 148 | 76% | 242 | 273 |
| 2026* | 95 | 81 | 62 | 61 | 254 | 60 | 194 | 38 / 16 | 119 / 55 | 72% | 199 | 253 |

\* fino al 24/11. Il resto rispetto a "con/contro" è BTC flat (W3.2 su BTC né long né short alla domenica del segnale).
La prima metà del 2021 ha pochissime idonee al 1/1 (4): il test utile parte di fatto dal 2022 per la selezione annuale.

## 5. Conflitto stop/liquidazione (struttura, non esito)
Distanza dello stop iniziale W3.2 = |prezzo d'ingresso − (chiusura del segnale ∓ 2,5 ATRw)| / prezzo d'ingresso. Liquidazione a
margine isolato pieno ≈ 1/L − mantenimento: 2x ≈ 49%, 5x ≈ 19% (con mantenimento 2,5%: 47,5% e 17,5%).

| Ingressi dal 2021 (emergenti al segnale) | n | stop mediano (10°–90°) | oltre liq. 2x | oltre liq. 5x | esposizione W3.2 a 1x mediana | leva max compatibile 1/(d+0,05) |
|---|---|---|---|---|---|---|
| Long | 463 | 50% (36–75%) | 242 (52%; 57% con mant. 2,5%) | 463 (100%) | 0,50 | |
| Short | 727 | 83% (54–161%) | 676 (93%) | 726 (100%) | 0,30 | |
| Entrambi | 1.190 | 69% | 918 (77%) | 1.189 (100%) | 0,36 | <1x 293 · 1–2x 701 · 2–5x 196 · ≥5x 0 |

Lettura: **a 5x lo stop di W3.2 non esiste mai** (la liquidazione arriva prima in tutti i casi); a 2x circa metà dei long e quasi
tutti gli short verrebbero liquidati prima dello stop. 277 short su 727 hanno lo stop oltre +95%, cioè oltre la liquidazione
anche a 1x se il margine è solo il nozionale. Le distanze così grandi vengono dall'ATR settimanale in valore assoluto che resta
alto dopo un crollo (gli short arrivano dopo grandi cadute). W3.2 compensa riducendo l'esposizione (0,25/d); la leva la annulla.
Volume medio del perp nei 90 giorni prima del segnale: mediana 24 M$/giorno (quartili 11/51); 264 ingressi sotto 10 M$; 101
con meno di 52 settimane di storia. Ingressi nella stessa settimana: mediana 4, massimo 27 (serve un tetto di posizioni).

**Long dello scanner di questa settimana (struttura)**: JST stop −25% (segnale 12/07, BTC contro), PIEVERSE −38% (22/11, contro,
53 settimane di storia), NIGHT −56% (04/10, con: BTC era long al segnale; lo scanner mostra "opposto" perché guarda BTC di oggi),
BEAMX −49% (08/11, con), SENT −70% (22/11, contro, volume 6,6 M$/giorno). A 5x tutti e cinque sono oltre la liquidazione; a
2x NIGHT e SENT (BEAMX al limite).

## 6. File
`cg_fetch.py`, `ops_fetch.py`, `snapshots.py`, `universe.py`, `fetch.py`, `build.py`, `finalize.py`, `counts.py`, `summary.py`;
`data/universe_raw.csv`, `data/universe.csv`, `data/snapshots.csv`, `data/sources.csv`, `data/match_raw.csv`,
`data/counts_moneta.csv`, `data/segnali.csv` (un ingresso per riga: data, lato, distanza dello stop, BTC, rank, volume, storia;
nessun esito), `data/counts_anno.csv`, `data/summary.txt`. Ordine: cg_fetch → ops_fetch → snapshots → universe → fetch → build →
finalize → counts → summary.
