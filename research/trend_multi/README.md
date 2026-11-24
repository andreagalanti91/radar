# trend_multi · portafoglio di trend-following su molti mercati (ETF "da manuale" e U2 su perpetui OKX/Bitget) · 23/11/2026

## Verdetto
- **ETF, riferimento da manuale (19 ETF, 5 classi): NON FUNZIONA secondo i criteri.** In giudizio (2016 → 20/11/2026) la versione
  primaria long/flat V1 rende **4,5% l'anno con DD −11,7%** (CAGR/DD 0,39): meno del 60/40 (8,9%, −21,2%, 0,42), poco più
  dell'equipesato in rapporto (0,34) ma con metà del rendimento; l'eccesso sul T-bill (+2,3 punti l'anno) non è significativo
  (p = 0,096, soglia 0,025). La versione long/short V2 perde (−0,3% l'anno, DD −25,9%). Non vale la pena rispetto al 60/40
  (differenza di Sharpe −0,30) né rispetto a W3.2.
- **U2, operativo (20 azioni del Dow 2000 con perpetuo oggi + 6 materie prime, funding ipotizzato 5%): NON FUNZIONA.** U2-V1
  rende **5,1% l'anno con DD −26,4%** (0,19) contro l'equipesato dello stesso universo con lo stesso funding (7,8%, −34,5%, 0,23) e
  l'S&P 500 (13,8%, −33,7%, 0,41); p = 0,13. U2-V2 long/short perde (−2,4% l'anno, DD −36,8%). Con funding al 10% U2-V1 scende
  a +0,7% l'anno: sotto la liquidità.
- **Cosa regge**: il trend long/flat taglia circa metà del drawdown (2022: ETF −6,0% contro −16,6% del 60/40) ma taglia in
  proporzione anche il rendimento; nel crollo rapido di febbraio–marzo 2020 il ribilanciamento mensile non protegge (U2-V1 −25,8%
  in cinque settimane). Gli short sui mercati che salgono nel lungo periodo costano in tutte le varianti.
- **"Più opportunità" a queste condizioni non c'è**: 150–180 ordini l'anno per un rendimento atteso di 2–3 punti sopra la
  liquidità, non distinguibile da zero. Nessuna modifica al tool.

PREREG `PREREG.md` (commit **3ca3620**, da solo prima di ogni dato); ADDENDUM U2 `ADDENDUM.md` (commit **4b8f2fc**, da solo prima
dei dati e dei risultati di U2). Giudizio calcolato una sola volta. Codice: `fetch.py`, `fetch_u2.py`, `tm_lib.py` (motore),
`tm_study.py`, `run_etf.py`, `run_u2.py`, `run_oggi.py`, `run_w32.py`; uscite `risultati_*.txt`, `etf_*.csv`, `u2_*.csv`.

## Regole (fissate prima, nessuna ottimizzazione)
Segnale per mercato: quota degli orizzonti 1, 3, 12 mesi con rendimento sopra il T-bill (long/flat 0…1; long/short −1…+1).
Peso ∝ segnale/volatilità a 60 sedute (rischio uguale per mercato), scalato a volatilità 10% del portafoglio, tetto Σ|w| ≤ 1
(nessuna leva: il tetto è quasi sempre attivo, lordo medio 0,99, volatilità realizzata 6,7%). Ribilanciamento a fine mese,
esecuzione alla chiusura successiva. Costi 0,10% per lato; short 1% annuo. ETF: liquidità al T-bill. U2: funding 5% annuo sui
long, collaterale a 0%. Dati Yahoo rettificati, taglio 20/11/2026; tutti gli ETF partono nelle date attese (ultimo: HYG 04/2007).

## ETF · giudizio 2016-01 → 2026-11 (10.000 $)
| | Finale | CAGR | Vol | Max DD | CAGR/DD | Sharpe | Peggior anno | 2016–20 | 2021–26 |
|---|---|---|---|---|---|---|---|---|---|
| **V1 long/flat 1/3/12** | 16.132 | 4,5% | 6,7% | −11,7% | 0,39 | 0,35 | −6,0% (2022) | +27,9% | +26,4% |
| V2 long/short 1/3/12 | 9.679 | −0,3% | 6,2% | −25,9% | −0,01 | −0,39 | −15,0% (2023) | +1,0% | −3,9% |
| V3 LF 3/6/12 | 16.138 | 4,5% | 7,1% | −12,1% | 0,37 | 0,33 | −6,1% | | |
| V4 LF 12 mesi | 14.085 | 3,2% | 7,6% | −17,1% | 0,19 | 0,15 | −10,2% | | |
| V5 LF media 10 mesi | 15.422 | 4,1% | 6,9% | −13,7% | 0,30 | 0,28 | −7,0% | | |
| V6 LF settimanale | 13.149 | 2,5% | 6,5% | −17,0% | 0,15 | 0,07 | −12,5% | | |
| V7 LF tetto 2x (descrittiva) | 18.654 | 5,9% | 10,9% | −21,9% | 0,27 | 0,37 | −13,3% | | |
| V8 LS 3/6/12 | 11.101 | 1,0% | 5,8% | −22,4% | 0,04 | −0,20 | −13,4% | | |
| 60/40 SPY/IEF | 25.222 | 8,9% | 10,5% | −21,2% | 0,42 | 0,65 | −16,6% (2022) | +71,6% | +48,2% |
| Equipesato dei 19 | 21.929 | 7,5% | 10,0% | −22,0% | 0,34 | 0,55 | −10,7% (2022) | +49,5% | +47,0% |
| Liquidità (T-bill) | 12.816 | 2,3% | | | | | | +5,7% | +21,3% |

Criteri V1: 1 ✗ (0,39 < 0,42 del 60/40; > 0,34 equipesato) · 2 ✓ · 3 ✓ · 4 ✗ (p 0,096). V2: tutti ✗.
Sviluppo 2007–15 (descrittivo): V1 4,0%, DD −11,8% (0,33) contro 60/40 6,6%, −32,2% (0,21): il vantaggio del 2008 non si è ripetuto.
Crisi: 2018 Q4 V1 −6,2% (60/40 −6,7%); 19/02–23/03/2020 −6,6% (−18,7%); 2022 −6,0% (−16,6%). V2: −2,2%, +7,6%, +6,0%, ma −15% nel 2023.
Robustezza (`etf_robustezza.csv`): V1 batte il 60/40 in CAGR/DD in 3 controlli su 15 (vol 90, senza obbligazioni, senza
immobiliare); costi doppi 3,8%; settimanale 2,5% (420 ordini l'anno); V2 in 0 su 15.
Operazioni V1: 46 cambi di stato l'anno (un mercato entra o esce), **~150 ordini l'anno ≥ 1% del capitale (12–13 al mese)**,
rotazione 6,5 volte il capitale, sempre investita, ~16 posizioni.

## U2 · giudizio 2016-01 → 2026-11 (10.000 $, funding 5% sui long, collaterale 0%)
| | Finale | CAGR | Vol | Max DD | CAGR/DD | Sharpe | Peggior anno | 2016–20 | 2021–26 |
|---|---|---|---|---|---|---|---|---|---|
| **U2-V1 long/flat** | 17.261 | 5,1% | 11,2% | −26,4% | 0,19 | 0,30 | −11,0% (2020) | +13,9% | +52,4% |
| U2-V2 long/short | 7.718 | −2,4% | 8,9% | −36,8% | −0,06 | −0,48 | −19,8% (2023) | −3,6% | −19,2% |
| Equipesato U2, funding 5% | 22.598 | 7,8% | 15,0% | −34,5% | 0,23 | 0,42 | −12,0% | +26,6% | +80,0% |
| Equipesato U2, senza funding | 38.856 | 13,3% | 15,0% | −34,0% | 0,39 | 0,76 | −7,5% | | |
| S&P 500 (SPY, senza funding) | 40.805 | 13,8% | 17,8% | −33,7% | 0,41 | 0,69 | −18,2% | | |
| Liquidità (T-bill) | 12.816 | 2,3% | | | | | | | |

Criteri U2-V1: 1 ✗ · 2 ✗ (−26,4%) · 3 ✓ · 4 ✗ (p 0,13). U2-V2: tutti ✗.
Sensibilità di U2-V1 (`u2_robustezza.csv`): funding 0% → 9,8%, DD −25,8% (0,38; equipesato 13,3%, 0,39); funding 10% → 0,7%,
DD −33,1%; costi doppi 4,6%; settimanale 4,0% (437 ordini); future al posto degli ETF-serie 5,3%; senza materie prime 5,8%;
solo materie prime 2,7% (DD −26,3%); rischio uguale per classe 4,5%. Batte l'equipesato in 2 controlli su 16, l'S&P in nessuno.
Il rendimento lordo viene dalle azioni (+8,9 punti l'anno prima del funding) più che dalle materie prime (+1,5, quasi solo oro).
Crisi: 2018 Q4 −7,7%; 19/02–23/03/2020 **−25,8%**; 2022 −3,0%. Operazioni: 58 cambi di stato e **~180 ordini l'anno (15 al mese)**, ~22 posizioni.
**Elenco di oggi (ottimistico, `risultati_oggi.txt`)**: con le 10 maggiori capitalizzazioni attuali (NVDA, AAPL, MSFT, GOOGL, AMZN,
META, AVGO, TSLA, BRK-B, LLY) + materie prime, V1 fa 10,1% con DD −18,1% (0,56) ma l'equipesato degli stessi titoli fa 17,0% con
DD −30,1% (0,56): anche scegliendo i vincitori a posteriori il trend non aggiunge nulla, dimezza rendimento e drawdown.

## Combinazione con W3.2 BTC (descrittiva: W3.2 ha già visto tutto il 2021–26; dal 01/2021 al 10/11/2026)
| Portafoglio | Finale | CAGR | DD | CAGR/DD |
|---|---|---|---|---|
| W3.2 da sola | 78.474 | 42,2% | −21,1% | 2,00 |
| 70% W3.2 + 30% ETF V1 | 48.959 | 31,2% | −14,9% | 2,10 |
| 50% W3.2 + 50% ETF V1 | 34.679 | 23,7% | −12,3% | 1,92 |
| 70% W3.2 + 30% U2-V1 | 51.694 | 32,4% | −14,7% | 2,20 |
| 50% W3.2 + 50% U2-V1 | 38.035 | 25,6% | −12,2% | 2,09 |
| 70% W3.2 + 30% T-bill | 47.983 | 30,7% | −15,0% | 2,05 |
| 50% W3.2 + 50% T-bill | 33.523 | 22,9% | −10,6% | 2,16 |
Correlazione mensile con W3.2: ETF V1 +0,12, U2-V1 +0,27 (70 mesi). Il trend è poco correlato, ma affiancarlo a W3.2 dà lo
stesso risultato di affiancare liquidità: riduce il drawdown perché diluisce, non perché diversifica. Il 2021–26 è la metà
migliore di U2-V1 (+52%): il dato è favorevole.

## Stato attuale (chiusura 20/11/2026; posizioni in essere dal ribilanciamento di fine ottobre, su 60.000 $)
- **U2-V1**: KO 7,0k · PG 6,2k · JNJ 5,1k · MO 4,6k · JPM 4,5k · XOM 4,4k · WMT 4,1k · MSFT 3,6k · RTX 3,5k · MRK 2,9k ·
  petrolio 2,8k · IBM 2,5k · MCD 2,0k · HD 1,5k · C 1,5k · rame 1,5k · HPQ 1,4k · CAT 0,9k · INTC 0,4k. Fuori: BA, GE, T, oro,
  argento, gas, platino. A fine novembre la regola uscirebbe da IBM, MSFT, CAT ed entrerebbe in GE e gas (`u2_posizioni_oggi_V1.csv`).
- **ETF V1**: UUP 11,1k · HYG 7,4k · IEF 4,6k · EFA 4,5k · VGK 4,4k · DBC 4,2k · LQD 4,2k · VNQ 3,9k · FXY 3,2k · SPY 2,4k ·
  TLT 2,4k · USO 1,9k · IWM 1,8k · EWJ 1,5k · QQQ 1,3k · EEM 1,1k; fuori oro, argento, euro (`etf_posizioni_oggi.csv`).
- In pratica: 16–22 posizioni da 400 a 11.000 $ (media ~2.500–3.500 $), 12–15 ordini al mese concentrati in un giorno.

## Prima di operare: cosa NON è verificato
- **Funding reale dei perpetui azionari**: nessuno storico; il 5% è un'ipotesi e decide il risultato (0% → 9,8%, 10% → 0,7%).
- Il backtest usa il sottostante (azione con dividendi, ETF-serie per le materie prime): i perpetui azionari hanno mesi di storia;
  scostamento dal sottostante, orari (fine settimana, borsa chiusa), liquidità e spread per ordini da 2–7k $ non misurati.
- Dividendi: il perpetuo non li paga; qui sono nel rendimento del sottostante (ottimistico se il funding non li compensa).
- Rischio di controparte (capitale in USDT sull'exchange), liquidazioni anche a 1x in caso di picchi di prezzo.
- Restrizioni sui derivati per residenti UE/Italia su OKX e Bitget: non verificate. Trattamento fiscale: non esaminato.
- ETF USA: non acquistabili dai clienti al dettaglio UE (PRIIPs, manca il KID); servirebbero equivalenti UCITS o future/CFD,
  qui non indicati né testati. OKX e Bitget elencano anche perpetui su ETF, indici e valute (SPY, QQQ, IWM, TLT, EWJ, EUR/USD,
  USD/JPY, DXY): non usati per il vincolo dell'utente ("solo azioni").

## Limiti e deviazioni
- Bias di selezione: ETF sopravvissuti scelti oggi; U2 = titoli del Dow 2000 ancora quotati e con perpetuo oggi (a favore della strategia e ancor più dell'equipesato).
- Tetto 1x: il portafoglio non raggiunge il 10% di volatilità obiettivo (6,7%); la versione 2x (V7) non cambia il rapporto (0,27).
- Deviazioni: (1) "elenco di oggi" ridotto alle 10 maggiori capitalizzazioni già in cache (i 211 ticker comuni a OKX e Bitget non
  erano scaricabili per il limite di frequenza di Yahoo); (2) SLV e i future di oro, argento e Brent presi dalle cache di
  multi_asset/swing_sr_multi (stessa fonte e stesso taglio); (3) aggiunta descrittiva "W3.2 + T-bill" nella combinazione;
  (4) W3.2 disponibile fino al 10/11/2026; (5) file di stato in `stato/` non aggiornato (vincolo: nulla fuori da questa cartella).
- Un solo giudizio di 10,9 anni dominato da un mercato azionario in salita: è il contesto peggiore per il trend, ma è quello osservato.

## Lezione proposta (118)
**Lezione 118**: un portafoglio di trend-following (momentum 1/3/12 mesi, rischio uguale per mercato, senza leva, mensile) giudicato
come portafoglio non regge né su 19 ETF di 5 classi né sull'universo negoziabile con perpetui OKX/Bitget (20 azioni del Dow 2000 +
6 materie prime). Giudizio 2016–26: ETF long/flat 4,5% l'anno, DD −11,7% (60/40 8,9%, −21,2%; p 0,096); U2 long/flat 5,1%, DD
−26,4% con funding 5% (equipesato 7,8%; S&P 13,8%; 0,7% con funding 10%); long/short in perdita ovunque; ribilanciamento
settimanale peggiore; 150–180 ordini l'anno. Dimezza drawdown e rendimento insieme: accanto a W3.2 vale quanto la liquidità
(70/30: CAGR/DD 2,10–2,20 contro 2,05 con T-bill). Anche sulle 10 maggiori capitalizzazioni di oggi il trend eguaglia soltanto
il buy & hold (0,56). research/trend_multi/README.md (PREREG 3ca3620, ADDENDUM 4b8f2fc).

## Raccomandazione operativa
Non adottare. Attesa realistica del trend multi-mercato senza leva: 2–3 punti l'anno sopra la liquidità, incerti, con DD 12–26%
e 12–15 ordini al mese; su perpetui azionari il funding non noto può azzerarla. Per "più opportunità" l'alternativa onesta oggi
è nessuna: capitale non impegnato da W3.2 in liquidità remunerata. Se l'obiettivo è esposizione azionaria, il confronto corretto
è il semplice possesso (S&P 13,8% l'anno con DD −34% nel periodo), non una regola di trend. Eventuale seguito solo dopo aver
misurato per qualche mese il funding reale dei perpetui azionari.
