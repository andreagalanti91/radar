# W3.2 asset ciclo 2 · AZIONI · dati, operabilità e conteggi (25/11/2026)

Solo dati e conteggi: **nessun rendimento** calcolato, letto o riportato (il motore `ma_lib.s1_sim` è stato eseguito per contare gli
ingressi; il suo P&L non è salvato). La definizione del flusso per Q3 la sceglie il PREREG; qui ci sono le serie candidate.

## In breve
- **Universo: 128 titoli** = top 100 per capitalizzazione oggi (25/11/2026) ∪ top 100 a fine 2019 (31/12/2019 = 01/01/2020);
  72 in entrambe, **28 usciti** dalla top 100 dal 2020, 28 entrati (6 non quotati nel 2019).
- **Fonte della classifica: CompaniesMarketcap.com** (pubblica, senza login): classifica di oggi dal CSV offerto dal sito e dalle
  pagine 1–5; capitalizzazione a fine 2019 dalla tabella "end of year" della pagina di ciascuna società (509 pagine lette, 1,5 s di
  pausa, User-Agent generico). Wikipedia era in limite di frequenza (HTTP 429) e ha solo la top 10 storica; Wayback Machine non
  raggiungibile da qui e senza istantanee del sito prima di giugno 2020.
- **Dati**: Yahoo chart API, giornalieri dal 2019-01-02 al 24/25-11-2026, 147 linee (127 primarie + 20 linee USA/ADR); 124 titoli
  contati, 4 esclusi (SpaceX, Anthropic e CXMT con meno di un anno di quotazione; IHC Abu Dhabi senza dati su Yahoo).
- **Operabilità**: perp su azioni su **Bitget per 65** e su **OKX per 51** dei top 100 di oggi (66 su almeno uno); dei top 100 del
  2019, 60 / 39 (61). Tutti quotati nel **2026** (primo 02/02/2026, mediana giugno 2026): **nessun perp su azioni ha più di 10 mesi di
  storia**, quindi il backtest sulle azioni usa per forza la quotazione in borsa e il funding va stimato.
- **Conteggi (W3.2 solo prezzo, W-FRI, dal 2020)**: mediana **29 ingressi per titolo** (mediane 18 long e 10 short), 123 titoli su 124 con ≥ 8
  ingressi (fa eccezione GE Vernova, quotata dal 2024: 3). Con un filtro di flusso gli ingressi scendono del 10–14% (mediana 25–26);
  ≥ 8 ingressi restano 123/124 con ogni filtro, anche separatamente in IS 2020–22 (114–122) e in OOS 2023→ (118–121).

## 1. Universo
Fonte: CompaniesMarketcap.com, letto il 25/11/2026 (`universe.py`). Termini di servizio del sito (10/11/2023): nessun divieto di
lettura automatica; riuso dei contenuti consentito per uso editoriale con attribuzione. robots.txt consente le pagine usate. Nel repo
sono salvati solo i valori estratti (`data/cmc_today.csv`, `data/cmc_2019.csv`, `data/raw/cmc_today_top500.csv`), non le pagine.
La classifica delle società del sito non contiene ETF né fondi (sono in sezioni separate); l'universo quindi è di sole società.

Rank 2019: posizione per capitalizzazione a fine 2019 fra i candidati = prime 500 di oggi + 31 società grandi nel 2019 che potevano
essere scese (Russia, Naspers, Bayer, NTT Docomo, …: lista `EXTRA`). La soglia della top 100 a fine 2019 è circa 103 miliardi $
(n. 100 Starbucks); la prima esclusa fra i candidati fuori lista è NTT Docomo (98 mld, n. 112, delistata nel 2020), Sberbank 89 mld.

Top 10 oggi: Apple, NVIDIA, Microsoft, Alphabet, Amazon, TSMC, SpaceX (quotata dal 12/06/2026), Saudi Aramco, Tesla, Meta.
Top 10 a fine 2019: Saudi Aramco, Apple, Microsoft, Alphabet, Amazon, Meta, Alibaba, Berkshire Hathaway, Tencent, ICBC.

**Usciti dalla top 100 (rank fine 2019 → oggi), 28:** AT&T 22→126 · Ping An 34→129 · China Merchants Bank 36→110 · Pfizer 37→118 ·
Comcast 40→253 · Boeing 44→158 · AB InBev 52→125 · Adobe 53→252 · Nike 54→456 · Medtronic 56→176 · Unilever 57→144 ·
Salesforce 61→123 · Bristol-Myers 64→162 · BHP 68→103 · Accenture 70→149 · AIA 77→236 · BP 78→196 · Sanofi 79→166 ·
Honeywell 80→333 · Union Pacific 83→108 · China Life 84→130 · Prosus 88→133 · GSK 92→222 · Airbus 93→112 · TCS 95→226 ·
Lockheed Martin 97→152 · Danaher 98→121 · Starbucks 100→178. Nessuno è stato delistato: tutti hanno dati completi (il bias di
sopravvivenza qui è di "classifica", non di fallimento; l'unico vero caso sarebbe stato NTT Docomo, appena fuori dalla top 100).

**Entrati dopo il 2019, 28** (elenco completo in `tabelle.txt`): fra cui Tesla (147 nel 2019), Micron, AMD, SK Hynix, Palantir, GE,
Applied Materials, Lam Research, CrowdStrike, Arista, Dell, Amphenol, Welltower; non quotati nel 2019: SpaceX, Anthropic (19/11/2026),
Palantir, CXMT, GE Vernova, IHC.

Paesi, top 100 oggi: USA 63, Cina 10, Regno Unito 4, Svizzera, Francia, Germania 3, Corea, Canada, Giappone 2, altri 1.
Fine 2019: USA 55, Cina 12, Regno Unito 7, Francia 4, Olanda, Svizzera 3, …

## 2. Dati (`fetch.py`, `quality.py`)
`data/px/<TICKER>.csv.gz`, stesso formato di `research/multi_asset/data` più colonne:
`open, high, low, close` rettificati per frazionamenti e dividendi (fattore adjclose/close, come multi_asset) · `close_raw` (e
`open_raw/high_raw/low_raw`) = valori Yahoo, rettificati SOLO per i frazionamenti · `close_unadj` = chiusura davvero non rettificata
(frazionamenti rimessi dagli eventi Yahoo; es. NVDA 05/06/2024: 1.224,40) · `volume` (Yahoo, rettificato per frazionamenti).
Valuta locale; `data/meta.csv` (valuta, borsa, fuso, date, sedute, data di download) e cambi in `data/fx/<VAL>.csv.gz`
(USD per unità; GBp diviso 100). Linea: per gli ADR/OTC della classifica si usa la linea primaria locale (TSMC 2330.TW, Tencent
0700.HK, Toyota 7203.T, ASML.AS, Novo NOVO-B.CO, …); la linea USA quotata in borsa (`yahoo_us`: TSM, ASML, TM, NVO, SHEL, …) è
scaricata a parte perché i perp di Bitget/OKX seguono quella. Alphabet: GOOGL. Roche: RO.SW (la linea ROG.SW non esiste su Yahoo
da qui; volume basso, ~24k al giorno; c'è anche l'ADR OTC RHHBY).

Controlli (`quality.csv`): nessun ticker sbagliato (ultima chiusura × cambio = prezzo della classifica, 1,00 ± 0,03, salvo i rapporti
ADR noti: TSM 5, HSBC 5, Shell 2, Toyota 10, BP 6, GSK 2, BHP 2, Sanofi 0,5); buchi > 7 giorni solo per festività (Cina 17,
Arabia Saudita 10, Taiwan 8); sedute a volume 0 in 26 linee (massimo 37, Aramco; Hong Kong/Corea 10–15, tifoni e festività);
13 titoli con salti giornalieri > 25% (eventi veri: risultati di NVDA, META, NFLX, ORCL, INTC, …; non corretti); 17 sedute con OHLC
incoerente di pochi centesimi in 15 linee asiatiche/europee (lasciate, effetto trascurabile). Aramco dal 11/12/2019 (IPO), PLTR dal
30/09/2020, GEV dal 27/03/2024: il test parte un anno dopo il primo dato.

## 3. Flusso dai volumi (`flow.py`, `data/flow/<T>_d.csv.gz` e `_w.csv.gz`)
Serie candidate standard, nessuna scelta: `cmf20` Chaikin Money Flow 20 sedute; `ad` linea Accumulation/Distribution e `ad_slope20`
(pendenza dei minimi quadrati su 20 sedute / volume medio); `obv` On-Balance Volume, `obv_slope20` (stessa pendenza) e `obv_chg20`
(variazione su 20 sedute / volume 20 sedute); settimanali alla chiusura del venerdì (ultima seduta della settimana W-FRI, la stessa
della decisione) più `cmf_w4` (Chaikin sulle candele settimanali, 4 settimane). Nota: la variazione semplice di A/D su 20 sedute
divisa per il volume coincide esattamente con `cmf20`, per questo `ad_slope20` usa la pendenza. Correlazione settimanale su NVDA:
cmf20–obv_slope20 0,52, cmf20–cmf_w4 0,67, obv_slope20–obv_chg20 0,91. Valori mancanti: con meno di 15 sedute valide su 20
(prime settimane dei dati): 8 settimane in tutto nelle finestre di conteggio.

## 4. Operabilità su Bitget e OKX (`exchanges.py`, `data/exchanges/`)
Fonti pubbliche, nessuna chiave: Bitget `/api/v2/mix/market/contracts` (USDT-FUTURES: 430 strumenti con `isRwa = YES` fra azioni,
ETF, indici e materie prime; `openTime` = data dichiarata di apertura), `/api/v2/spot/public/symbols`; OKX `/api/v5/public/instruments`
(`instCategory = 3` = azioni: 241 SWAP, 93 FUTURES "XPERP", 230 token spot "X<ticker>"). Abbinamento solo per codice esatto (ticker USA,
ticker+STOCK su Bitget quando coincide con una crypto: CSTOCK = Citigroup, TSTOCK = AT&T, CVXSTOCK, RTXSTOCK, ACNSTOCK; alias espliciti
per i non USA: SAMSUNG, SKHYNIX, TENCENT, TOYOTA/TM, MUFG, RELIANCE, TCS, BUD, BP, BHP, NVS). Materie prime (CL, BZ, …) mai attribuite.

| | Bitget perp | OKX perp | almeno uno | token OKX (xStocks) |
|---|---|---|---|---|
| Top 100 oggi | 65 | 51 | 66 | 52 nell'universo |
| Top 100 fine 2019 | 60 | 39 | 61 | |

- Top 10 di oggi: tutti su Bitget e OKX tranne Saudi Aramco (nessuno); SpaceX sì ma con 5 mesi di dati. Top 10 2019: mancano Aramco e
  ICBC; Alibaba solo Bitget; Tencent Bitget dal 01/07/2026, OKX dal 25/11/2026.
- **Non operabili** fra i top 100 di oggi (34): Aramco, CCB, ABC, Bank of China, ICBC, Moutai, PetroChina, China Mobile, Roche, Nestlé,
  AstraZeneca, HSBC, Shell, Philip Morris, Royal Bank, TD, Thermo Fisher, L'Oréal, Wells Fargo, SAP, Siemens, LVMH, Disney, American
  Express, Inditex, Verizon, CBA, TotalEnergies, IHC, Allianz, Abbott, Amphenol, Welltower, NextEra. Solo OKX: Novo Nordisk (NVO).
- **Da quando**: Bitget primo 02/02/2026 (28 contratti con la stessa data: probabile migrazione/riquotazione, la data è quella
  dichiarata dall'API), OKX primo 25/02/2026; mediana giugno 2026. Il prompt chiede "da quando": **meno di 10 mesi per tutti**.
- **Funding**: le API pubbliche danno solo gli ultimi ~3 mesi (Bitget dal 27/08/2026, OKX dal 24/08/2026; 3 pagamenti al giorno).
  Media annualizzata: Bitget mediana +1,0% (da −18% a +12%), OKX +0,8% (da −16% a +12%) (`funding_summary.csv`, file per strumento).
  Per il backtest 2020–2026 il funding non esiste: va usata la stima del PREREG (azioni: short 3% annuo) o questa media, dichiarandolo.
- I contratti Bitget su azioni hanno `fundInterval` e leva massima nell'elenco; le ore di negoziazione fuori sessione USA non sono
  nelle API: non verificato.
- Bitget spot ha simboli "R<ticker>" (es. RAAPLUSDT) senza un campo che li classifichi come azioni: non attribuiti. I futures OKX
  "XPERP" con scadenza 2031 non sono contati come perp.

## 5. Conteggi (`count.py`, `counts.csv`, `counts_by_year.csv`)
Motore `research/multi_asset/ma_lib.py`: `s1_weekly` (regime SMA40/EMA20, ingresso EMA21, filtro MACD nei trend ≥ 16 settimane) e
`s1_sim` (esecuzione all'apertura successiva, stop/trailing 2,5 ATR, uscita EMA21), rischio 25% (il numero di ingressi non dipende
dal rischio). W-FRI, taglio venerdì 20/11/2026, dal 2020-01-01 (o un anno dopo il primo dato). Controllo: dal 2021 con i dati di qui
gli ingressi di NVDA, AAPL, MSFT, META, TSLA (15, 23, 22, 21, 31) sono **identici** per data e lato a quelli di `multi_asset`.
Filtro di flusso: long solo con flusso > 0, short solo con flusso < 0, letto alla seduta della decisione; "ingressi" = ingressi
effettivi della simulazione (in posizione non si rientra), "grezzi" = settimane con condizione vera.

124 titoli (linea primaria), dal 2020:

| Variante | Ingressi totali (L / S) | Mediana per titolo | Titoli ≥ 8 | ≥ 8 in IS 2020–22 | ≥ 8 in OOS 2023→ | Settimane grezze L / S |
|---|---|---|---|---|---|---|
| solo prezzo | 3.593 (2.259 / 1.334) | 29 | 123 | 122 | 121 | 18.980 / 9.272 |
| cmf20 | 3.112 (1.998 / 1.114) | 25 | 123 | 114 | 120 | 14.014 / 6.092 |
| cmf_w4 | 3.233 (2.072 / 1.161) | 26 | 123 | 118 | 120 | 14.930 / 6.185 |
| obv_slope20 | 3.188 (2.060 / 1.128) | 26 | 123 | 119 | 118 | 14.644 / 6.201 |
| obv_chg20 | 3.226 (2.086 / 1.140) | 26 | 123 | 122 | 118 | 14.991 / 6.355 |
| ad_slope20 | 3.094 (1.986 / 1.108) | 25 | 123 | 115 | 119 | 13.755 / 6.017 |

Solo prezzo per anno (124 titoli, long / short): 2020 404/296 · 2021 280/81 · 2022 315/304 · 2023 351/190 · 2024 274/119 ·
2025 338/189 · 2026 297/155
(dettaglio per titolo, anno, lato e variante in `counts_by_year.csv`). Top 100 oggi (96 contati): 2.693 ingressi, mediana 28;
top 100 2019 (100 contati): 2.968, mediana 29. Ingressi solo prezzo **dopo la quotazione del perp** (linea USA dove esiste): 146 in
tutto su 79 titoli, massimo 9 per titolo: non bastano per nessuna statistica sul perp.

### Top 10 oggi (rank oggi / fine 2019; ingressi dal 2020: totale (long/short))
| # | Titolo | Bitget perp (dal) | OKX perp (dal) | Solo prezzo | cmf20 | cmf_w4 | obv_slope20 | obv_chg20 | ad_slope20 | Per anno 2020…2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1/2 | Apple AAPL | 02/02/26 | 04/03/26 | 25 (18/7) | 25 (18/7) | 24 (18/6) | 22 (16/6) | 23 (16/7) | 24 (18/6) | 3·3·6·2·5·4·2 |
| 2/62 | NVIDIA NVDA | 02/02/26 | 04/03/26 | 18 (14/4) | 17 (14/3) | 18 (14/4) | 18 (14/4) | 18 (14/4) | 18 (14/4) | 4·1·4·2·2·3·2 |
| 3/3 | Microsoft MSFT | 02/02/26 | 04/03/26 | 24 (17/7) | 20 (15/5) | 23 (17/6) | 22 (16/6) | 22 (16/6) | 20 (15/5) | 3·1·5·3·5·3·4 |
| 4/4 | Alphabet GOOGL | 02/02/26 | 04/03/26 | 25 (20/5) | 20 (15/5) | 22 (17/5) | 23 (18/5) | 23 (18/5) | 19 (14/5) | 3·1·4·4·4·3·6 |
| 5/5 | Amazon AMZN | 02/02/26 | 26/02/26 | 33 (23/10) | 23 (16/7) | 28 (19/9) | 27 (19/8) | 30 (20/10) | 25 (19/6) | 2·7·5·4·2·5·8 |
| 6/21 | TSMC 2330.TW (TWD) | 02/03/26 (TSM) | 11/03/26 | 22 (17/5) | 18 (14/4) | 19 (15/4) | 19 (15/4) | 20 (16/4) | 20 (16/4) | 4·3·4·4·2·2·3 |
| 7/– | SpaceX SPCX | 09/06/26 | 07/05/26 | dati dal 12/06/2026: non contato | | | | | | |
| 8/1 | Saudi Aramco 2222.SR (SAR) | no | no | 19 (13/6) | 19 (13/6) | 19 (13/6) | 17 (11/6) | 18 (12/6) | 19 (13/6) | 1·3·4·1·3·5·2 |
| 9/147 | Tesla TSLA | 02/02/26 | 25/02/26 | 35 (25/10) | 33 (23/10) | 29 (20/9) | 31 (22/9) | 30 (21/9) | 31 (22/9) | 5·3·5·6·6·4·6 |
| 10/6 | Meta META | 02/02/26 | 04/03/26 | 25 (15/10) | 20 (13/7) | 21 (14/7) | 21 (13/8) | 24 (15/9) | 18 (11/7) | 4·3·1·3·2·3·9 |

### Top 10 a fine 2019 (oltre a quelli sopra: Aramco, Apple, Microsoft, Alphabet, Amazon, Meta)
| # | Titolo | Bitget perp (dal) | OKX perp (dal) | Solo prezzo | cmf20 | cmf_w4 | obv_slope20 | obv_chg20 | ad_slope20 | Per anno 2020…2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| 80/7 | Alibaba BABA | 02/02/26 | no | 33 (21/12) | 28 (16/12) | 30 (18/12) | 26 (16/10) | 27 (17/10) | 28 (17/11) | 5·4·4·8·4·5·3 |
| 13/8 | Berkshire BRK-B | 25/05/26 | 06/08/26 | 27 (19/8) | 25 (19/6) | 25 (18/7) | 25 (18/7) | 26 (19/7) | 24 (18/6) | 6·2·4·4·2·5·4 |
| 33/9 | Tencent 0700.HK (HKD) | 01/07/26 | 25/11/26 | 22 (12/10) | 18 (10/8) | 18 (10/8) | 19 (11/8) | 19 (11/8) | 17 (9/8) | 2·3·6·5·2·2·2 |
| 41/10 | ICBC 1398.HK (HKD) | no | no | 27 (18/9) | 24 (15/9) | 25 (17/8) | 24 (17/7) | 23 (16/7) | 24 (16/8) | 6·2·6·6·4·2·1 |

## 6. Limiti
- Classifica 2019 da una sola fonte (CompaniesMarketcap, valori di fine anno arrotondati a 4 cifre, società con più classi contate
  una volta). Candidati 2019 = prime 500 di oggi + 31 aggiunte: una società grande nel 2019 e oggi sotto i ~50 mld $ non in lista
  sfuggirebbe (nessuna nota oltre a NTT Docomo, n. 112). Il sito tratta Alphabet, Berkshire, ecc. come una società; il valore per
  le società cinesi A/H è quello del sito.
- Yahoo: dati di un servizio non ufficiale; volume delle borse non USA non comparabile fra mercati (Roche RO.SW poco liquida);
  il flusso dai volumi giornalieri vede solo la borsa primaria (niente dark pool, niente volume consolidato fuori USA).
- Perp su azioni: tutti nati nel 2026 (≤ 10 mesi), funding pubblico solo per ~3 mesi, orari fuori sessione e tracciamento del prezzo
  (perp vs titolo) non verificati. Lo studio 2020–2026 è quindi sul titolo in borsa, non sul perp: l'operabilità vale solo da oggi.
- Nucleo "top 10": SpaceX (7ª oggi) non ha un anno di dati; Aramco è nella top 10 di entrambe ma non è operabile su Bitget/OKX;
  ICBC (10ª nel 2019) nemmeno.
- I conteggi includono la posizione aperta al 20/11/2026 come ingresso.

## File (tutti in `research/w32_asset2/azioni/`)
`universe.py` (classifiche) → `build_universe.py` (universe.csv base) → `fetch.py` (prezzi, cambi) → `quality.py` → `exchanges.py`
(strumenti, funding) → `count.py` (flusso e conteggi) → `finalize.py` (universe.csv completo, `tabelle.txt`). `flow.py` = formule.
`universe.csv`: yahoo, yahoo_us, nome, paese, valuta, borsa, rank oggi, rank 2020, capitalizzazioni, dati da/a, anni, bitget/okx
(sì/no, simbolo, da quando), token OKX, perp_since, ingressi per variante.
