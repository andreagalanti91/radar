# A1 · Dati provvisori OKX nel flusso perp e nel funding di W3.2 (26/11/2026)

## Verdetto

- **Flusso perp: il problema CRITICO del 13/11 oggi non tocca più le decisioni.** Il flusso di W3.2 (`weekly.live_flow`) usa
  i pf14z di giovedì, venerdì e sabato, e il file giornaliero Binance del sabato esce la domenica verso le 08:30 UTC
  (130 sabati su 130 dal giugno 2024, ritardo massimo 10,3 ore). Al giro del lunedì alle 00:03 la finestra è sempre già
  definitiva: lo confermano la storia del ramo dati (23/11: 19, 20 e 21/11 già "binance", solo la domenica era OKX) e il
  registro `data/provlog.csv`. **Decisioni cambiate nella realtà: 0.** Il rischio resta solo se l'archivio si blocca per più
  di circa 38 ore. È successo per giorni infrastettimanali (11–12/06/2024 per 7 giorni, 28/10/2026 riscritto 13 giorni dopo),
  mai per un sabato.
- **Funding: è questo il rischio reale di oggi.** L'archivio Binance del funding è solo mensile (esce il 1° del mese verso
  le 08:30), quindi il funding medio a 7 giorni della domenica è quasi sempre OKX (12 domeniche su 12, con 1–7 giorni OKX).
  Errore misurato sulle ultime 12 domeniche: BTC p95 5,7e-5, ETH p95 9,5e-5 (massimo −1,06e-4 il 22/11). Nessuna decisione è
  cambiata, perché il funding era lontano dalle soglie (0,0009 / −0,0003). In questo periodo però OKX legge **più basso** di
  Binance (BTC −6e-5, ETH −1,1e-4 il 22/11), mentre **BTC ed ETH sono entrambi in short**. Uno scarto in quella direzione
  avvicina l'uscita falsa per "distribuzione" (che scatta con funding < −0,0003 e flusso > 0). Sullo storico 2021–2026,
  spostando il funding dell'errore osservato cambiano **2 decisioni su 308 domeniche** (24 e 31/10/2021: funding 0,000896
  contro la soglia 0,0009, uscita "dist" falsa; rendimento 741,5% → 717,8%). Con il doppio dell'errore ne cambiano 3–4.
- **Correzione consigliata (patch proposta, NON applicata): F1, funding Binance ricostruito dall'indice di premio
  pubblico** (`premiumIndexKlines` giornalieri di data.binance.vision, raggiungibile dai runner USA, formula pubblica di Binance).
  Per i 2 pagamenti della domenica che al lunedì alle 00:07 non hanno ancora il file di premio si usa OKX. L'errore p95 del
  funding a 7 giorni passa da 5,7e-5 a 0,9e-5 su BTC (6 volte meno) e da 9,5e-5 a 1,5e-5 su ETH. Lo scarto dello z del funding
  passa da 0,29σ medio (massimo 0,93σ) a 0,04σ (massimo 0,12σ). Insieme si propone **P1** per il perp: il volume OKX
  dei giorni provvisori si riscala con la mediana Binance/OKX di 28 giorni. Costa poco e toglie la decisione cambiata nello
  scenario "2 giorni in ritardo". Le regole di W3.2 non cambiano.
- Anche con F1 i due casi del 2021 (a 4e-6 dalla soglia) restano sul filo: nessuna fonte provvisoria li salva. Sono casi in
  cui decide il rumore, e vanno letti così.

File della patch: `research/dati_provvisori/patch_A1_funding_premio_volume_okx.diff` (radar/data.py + nuovo
tests/test_dati_provvisori.py; si applica con `git apply`; sulla copia del repo la suite completa passa: 551 test).

## Come si è misurato

Gli script sono in questa cartella. I dati grezzi stanno fuori dal repo (cartella passata come argomento). Tutte le fonti sono
pubbliche, senza chiavi. La preregistrazione è in `PREREG.md`, scritta prima degli script ma non committata (vincolo del compito).

| Script | Cosa fa |
|---|---|
| `archive_timing.py` | elenco pubblico del bucket data.binance.vision: ora di pubblicazione (LastModified) di ogni file giornaliero dal 06/2024 → `timing.csv`, `timing_summary.csv` |
| `collect.py` | candele 1D OKX BTC-USDT-SWAP (dal 2020), funding OKX pagato (l'API dà solo ~3 mesi: dal 24/08/2026), premio Binance 1m (dal 2021) |
| `funding_rebuild.py` | funding Binance ricostruito dal premio e confronto con l'archivio mensile → `funding_rebuild_check.csv` |
| `analysis.py` | scenari del flusso, funding alle domeniche, decisioni W3.2 puntuali e simulazione completa (radar.weekly in sola lettura, iniezione di flow/fund7 alle domeniche) |
| `eth_check.py` | stesso controllo del funding per ETH (secondo asset di W3.2) |

Uso: `python3 -I collect.py RAW && python3 -I funding_rebuild.py RAW REPO && python3 -I analysis.py RAW REPO`. REPO contiene i
CSV del tool (spot, perp, funding, metrics, fng, eth_funding) presi dal ramo dati `claude/vibrant-brahmagupta-fvv2gh` del
26/11 07:21. Controllo di riproduzione: il pf14z ricostruito coincide con `features.build_features` (scarto 0). W3.2 sui dati
definitivi dà 14 trade, rendimento 741,5% e DD −21,1%.

## 1. Quando arrivano i file Binance (ore dopo la fine del giorno, giugno 2024 – novembre 2026, 130 settimane)

| File giornaliero | mediana | p95 | max (sab) | pronto al lunedì 00:07 |
|---|---|---|---|---|
| klines 1d perp, sabato | 8,2 h | 9,5 h | 10,3 h | **100%** |
| klines 1d perp, domenica | 8,5 h | 10,4 h | 39 h | 0% (pronto entro le 12:00 del lunedì nel 97,7%) |
| premiumIndexKlines, sabato | 8,4 h | 9,9 h | 13,5 h | **100%** |
| premiumIndexKlines, domenica | 8,6 h | 10,9 h | 12,9 h | 0% (entro le 12:00: 98,5%) |
| funding mensile | — | — | — | esce il 1° del mese tra le 07:59 e le 09:42 UTC |

Le metrics sono state ricaricate in blocco (LastModified non utile per lo storico). Dal 21/11 escono verso le 07:00 del
giorno dopo. LastModified è l'ultima scrittura del file, quindi i ritardi sono limiti superiori.

## 2. Flusso perp: scenari di archivio in ritardo (237 domeniche dal 15/05/2022)

k = giorni finali (sab, ven, gio) ancora OKX al lunedì; la domenica è sempre OKX ma non entra nel flusso. Nella realtà k = 0.
Errore = |flow provvisorio − definitivo| in σ di pf14z.

| k | variante | err p95 | err max | segno diverso | decisioni cambiate | trade diversi |
|---|---|---|---|---|---|---|
| 1 | P0 attuale | 0,084 | 0,20 | 1 | 0 | 0 |
| 1 | **P1 volume ×(Binance/OKX 28g)** | 0,070 | 0,21 | 2 | 0 | 0 |
| 1 | P2 P1 + taker corretto | 0,071 | 0,20 | 2 | 0 | 0 |
| 2 | P0 attuale | 0,312 | 0,67 | 9 | **1** (15/05/2022: nessuna → ingresso short) | 2 |
| 2 | **P1** | 0,336 | 0,51 | 10 | 0 | 0 |
| 2 | P2 | 0,335 | 0,63 | 10 | 0 | 0 |
| 3 | P0 attuale | 0,622 | 1,54 | 16 | 1 (stesso caso) | 2 |
| 3 | **P1** | 0,537 | 1,10 | 19 | 1 | 2 |
| 3 | P2 | 0,591 | 1,01 | 17 | 2 | 4 |
| 1–3 | P3 "solo definitivi" (pf14z vuoti) | — | — | — | 1 / 12 / 12 | fino a 9 (rend. 741% → 94%) |

- Volume OKX / Binance (mediana per anno): 0,11 (2021), 0,24 (2022), 0,34 (2023), 0,45 (2024), 0,49 (2025), 0,55 (2026).
  Il rapporto cambia molto nel tempo, quindi serve stimarlo su una finestra recente, non usare una costante.
- Taker share delle metrics (media non pesata dei 5 minuti) contro la share vera pesata: scarto mediano 0,007, p95 0,023,
  quasi senza distorsione (media −0,001). Correggerla (P2) non aiuta.
- P3, cioè non decidere senza definitivi, è la scelta peggiore: ogni pf14z ha una finestra di 14 giorni, quindi un solo giorno
  OKX svuota tutti e tre i valori e salta le decisioni.
- Il caso del 15/05/2022 ha flusso definitivo +0,063, cioè sul filo dello zero.

## 3. Funding a 7 giorni alle domeniche (BTC; il definitivo di novembre è la ricostruzione dal premio, err p95 1e-5)

| Domenica | giorni OKX | definitivo | F0 OKX (oggi) | F1 premio + OKX dom. | F1b attesa file dom. | F2 OKX + scarto 28g |
|---|---|---|---|---|---|---|
| 06/09 | 6 | 1,75e-4 | 1,40e-4 | 1,80e-4 | 1,77e-4 | 2,16e-4 |
| 13/09 | 7 | 1,60e-4 | 1,64e-4 | 1,64e-4 | 1,61e-4 | 2,31e-4 |
| 20/09 | 7 | 2,13e-4 | 2,06e-4 | 2,15e-4 | 2,14e-4 | 2,36e-4 |
| 27/09 | 7 | 0,92e-4 | 1,07e-4 | 0,81e-4 | 0,89e-4 | 1,19e-4 |
| 04/10 | 4 | 1,15e-4 | 1,04e-4 | 1,13e-4 | 1,14e-4 | 1,05e-4 |
| 11/10 | 7 | 0,25e-4 | 0,77e-4 | 0,21e-4 | 0,23e-4 | 0,76e-4 |
| 18/10 | 7 | 1,12e-4 | 1,39e-4 | 1,11e-4 | 1,15e-4 | 1,30e-4 |
| 25/10 | 7 | 1,74e-4 | 1,84e-4 | 1,77e-4 | 1,75e-4 | 1,60e-4 |
| 01/11 | 1 | 2,41e-4 | 2,36e-4 | 2,36e-4 | 2,41e-4 | 2,34e-4 |
| 08/11 | 7 | 2,32e-4 | 2,15e-4 | 2,24e-4 | 2,32e-4 | 1,99e-4 |
| 15/11 | 7 | 1,86e-4 | 1,37e-4 | 1,85e-4 | 1,86e-4 | 1,35e-4 |
| 22/11 | 7 | 0,69e-4 | 0,06e-4 | 0,71e-4 | 0,69e-4 | 0,07e-4 |

| Variante | err mediana | err p95 | err max | Δz funding medio / max | decisioni cambiate (12 dom.) |
|---|---|---|---|---|---|
| F0 OKX (oggi) | 1,6e-5 | 5,7e-5 | 6,4e-5 | 0,29σ / 0,93σ | 0 |
| **F1 premio Binance + OKX per 2 pagamenti** | 0,3e-5 | 0,9e-5 | 1,1e-5 | 0,04σ / 0,12σ | 0 |
| F1b come F1 ma decisione dopo le ~11:00 del lunedì | 0,1e-5 | 0,3e-5 | 0,3e-5 | — | 0 |
| F2 OKX + scarto mediano 28g | 3,0e-5 | 6,6e-5 | 7,1e-5 | — | 0 |

- ETH (`eth_funding_sundays.csv`): F0 p95 9,5e-5 (max 1,06e-4), F1 p95 1,5e-5. La ricostruzione ETH contro l'archivio ha
  p95 7,7e-6.
- La ricostruzione Binance dal premio contro l'archivio 2021–2026 (2109 giorni) ha errore sul funding a 7 giorni: mediana 2,2e-6,
  p95 1,0e-5, massimo 5,1e-5 (nel 2021; 5,7e-6 di p95 nel 2026).
- F1b è escluso dalla regola preregistrata: sposterebbe la decisione dopo l'apertura del lunedì, che è una regola di W3.2.
  F2 non migliora: lo scarto OKX/Binance cambia segno da una settimana all'altra.
- Lo "z 1,11 contro 0,60" del 13/11 è `funding_z` (z a 180 giorni), che W3.2 non usa. W3.2 confronta solo `fund7` con
  0,0009 / −0,0003. Lo z amplifica scarti piccoli in valore assoluto.

Sullo storico 2021–2026 (simulazione completa, scarto costante su tutte le 308 domeniche, `funding_history_path.csv`):

| Scarto applicato | decisioni cambiate | trade diversi | rendimento (def. 741,5%) |
|---|---|---|---|
| F0 minimo −6,4e-5 | 0 | 0 | 741,5% |
| F0 massimo +5,2e-5 | 2 (24 e 31/10/2021, uscita "dist" falsa) | 2 | 717,8% |
| 2× F0 −1,3e-4 | 1 (31/12/2023, uscita "dist" mancata) | 2 | 684,9% |
| 2× F0 +1,0e-4 | 3 (05/09, 24/10, 31/10/2021) | 4 | 809,4% |
| F1 minimo −1,1e-5 | 0 | 0 | 741,5% |
| F1 massimo +0,5e-5 | 2 (gli stessi del 2021, a 4e-6 dalla soglia) | 2 | 717,8% |

Nelle 116 domeniche in cui il flusso era contrario alla posizione (cioè dove il funding decide l'uscita), la distanza mediana
dalla soglia è −5,4e-4: di solito c'è molto margine.

## Limiti

- Il funding OKX pubblico copre solo ~3 mesi (dal 24/08/2026): l'errore F0 è misurato su 12 domeniche di funding calmo
  (1–2e-4 al giorno). Nei periodi caldi (2021, inizio 2024), quando il funding è vicino a 0,0009, la differenza fra le formule
  OKX e Binance può essere più grande. Per questo la tabella storica usa anche il doppio dell'errore. È un argomento in più per
  F1, che usa la formula di Binance ed è stato verificato su tutto il 2021–2026.
- Il funding "definitivo" di novembre 2026 è la ricostruzione F1b, perché l'archivio mensile arriva il 01/12. La conferma va
  fatta a dicembre: `provlog` lo fa da solo (fund7_d).
- Gli scenari del flusso con k ≥ 1 sono ipotetici: nella realtà non si sono mai verificati per un sabato. La simulazione
  sostituisce il dato alla domenica tenendo il resto definitivo.
- La formula usa il premio a 1 minuto (chiusura del minuto) e non i campioni ogni 5 secondi di Binance: da qui l'errore
  residuo di ~1e-5.
- `provlog.csv` ha 1 sola riga (22/11) e registra solo BTC: il confronto "registro dal vivo" è minimo. ETH non ha un registro
  provvisori/definitivi.

## Patch proposta (da approvare: tocca i dati con cui decide W3.2)

`patch_A1_funding_premio_volume_okx.diff`:
1. `fetch_funding`: per i giorni dopo l'ultimo mese archiviato si calcola il funding Binance dai file giornalieri di premio
   (`_premium_day`, `premium_funding_8h`); i pagamenti senza file usano OKX (`provisional_funding`). Le etichette di `source`
   sono "premio" (3 pagamenti dal premio) e "okx" (almeno 1 pagamento OKX); per provlog restano provvisorie. Le righe
   provvisorie si ricalcolano a ogni giro e l'archivio mensile le sovrascrive. Se un pagamento manca sia nel premio sia in OKX,
   il giorno non si scrive (nessun dato inventato). Se OKX e premio cadono entrambi, resta la cache, con un log chiaro.
2. `fetch_perp`: `okx_volume_ratio`, mediana Binance/OKX degli ultimi 28 giorni in comune (minimo 10), applicata a volume e
   quote_volume delle righe OKX, con un log del fattore. Con meno di 10 giorni in comune il volume resta com'è, con un log.
3. Test (`tests/test_dati_provvisori.py`, 10 test senza rete): formula (fascia ±0,05%, pesi 1..n, minuto 23:59 al pagamento
   delle 00:00, periodo incompleto escluso); domenica al lunedì mattina (problema riprodotto: sabato tutto dal premio,
   domenica 1 pagamento dal premio e 2 da OKX); pagamento assente ovunque senza riga; fetch_funding senza rete che lascia la
   cache intatta; rapporto di volume mediano e caso con pochi giorni.

Costo di rete: fino a ~32 file di premio da ~25 kB per giro orario (si potrebbero mettere in cache, come miglioria successiva).
Prima di pubblicare (CLAUDE.md): approvazione dell'utente, suite completa, giro di prova con il confronto F0/F1 nel log, poi
verifica di `fund7` nel registro alla prima domenica (29/11) e conferma con l'archivio del 01/12.

## Nota per la sessione principale

La suite completa eseguita nel repo riscrive `data/macro.csv`: `tests/test_eth.py::test_giro_btc_prosegue` chiama `cli.daily()`
senza simulare `macro.build`, che va in rete e salva il file. Il file è stato riportato allo stato committato
(`git checkout data/macro.csv`). Attenzione a non committarlo per errore dopo aver lanciato i test.
