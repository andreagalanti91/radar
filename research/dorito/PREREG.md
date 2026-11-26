# Preregistrazione · "Dorito indicator" (Leledc Exhaustion Bar, versione InSilico) su BTC 1D e 3D · 26/11/2026

Scritta il **26/11/2026 alle 21:55 UTC**, PRIMA di calcolare qualsiasi rendimento di questo studio (finora calcolati solo le
date dei triangoli e i conteggi per anno: `z_match.py`, `z_conteggi.py`, `eventi.csv`, `conteggi.txt`). Da committare da sola,
prima di eseguire gli script dei risultati. Richiesta dell'utente: post X di @CryptoJelleNL del 26/11/2026 ("The famous dorito
indicator has flashed again… trend exhaustion… reversal is near", screenshot `post_utente.png`).

## 1. Indicatore (ricostruito da fonti pubbliche, nessuna invenzione)
- Un altro post dello stesso autore lo nomina: "The Dorito indicator (**Insilico Leledc**) flashed on both the weekly & 3d".
  È lo script open source TradingView **"Leledc levels (IS)"** di InSilico (jB2a9GAV), modifica del **"Leledc Exhaustion Bar"** di
  glaz (2rZDPyaC), a sua volta porting di un indicatore MT4. Codice Pine letto da una copia pubblica del sorgente; valori
  predefiniti (lunghezza 40, conteggio 10) letti dai metadati della pagina TradingView. Il Williams %R e il TD Sequential NON
  c'entrano.
- Regola (barra t, solo barre chiuse): `bindex += close > close[4]`, `sindex += close < close[4]` (contatori che si azzerano SOLO al
  segnale del proprio lato). **Rosso** (esaurimento del rialzo) se bindex > 10, candela rossa (close < open) e high = massimo
  delle ultime 40 barre (inclusa t) → bindex = 0. **Nero** (esaurimento del ribasso; verde nello script, nero nel grafico) se
  sindex > 10, candela verde e low = minimo delle ultime 40 barre → sindex = 0. Il segnale non si ridisegna dopo la chiusura.
- Porting: `dorito_lib.lele`. Primaria **IS 40/10**. Secondaria solo descrittiva: glaz "major" 30/6 (if indipendenti).
- **Coincidenza con lo screenshot**: 8 triangoli letti (asse calibrato su 1/1/2025 e 1/1/2026, precisione ±3 giorni):
  R 18/12/24, N 11/03/25, R 22/05/25, R 14/08/25, N 20/11/25, N 07/02/26, N 30/06/26, N ~15/11/26. IS 40/10 su barre **3D
  ricominciate ogni 1 gennaio** (griglia di TradingView: la fase 2025 e la 2026 differiscono) dà esattamente 8 segnali dal
  01/09/2024: R 17/12/24, N 11/03/25, R 22/05/25, R 14/08/25, N 21/11/25, N 06/02/26, N 30/06/26, N 15/11/26 → **8/8, nessun
  segnale in più**. 3D a griglia fissa: 6/8 (fase 1) o 4/8; 1D: 5/8 con 11 in più; settimanale: 2/8. glaz 30/6 su 3D annuale:
  6/8 entro ±4 giorni, 4 in più. Conferme indirette: post "has flashed" del 03/07/2026 (barra 30/06–02/07) e "weekly & 3d" (W:
  N 29/06/2026). Il triangolo dell'ultimo post è sulla barra 15–17/11/2026 (non sulla candela in corso).
- Vicini della coincidenza (3D annuale, dal 09/2024): 40 × 8/10/12 identici (8/8); 50 × 8/10/12 → N 07/04/25 invece di 11/03 e
  N 21/11/26; 30 × 8/10/12 → 9–10 segnali (in più R 26/08/26, N 27/02/25).

## 2. Dati e barre
- Giornaliero UTC: `f_long` (dal 2014, riscaldamento) fino al 31/08/2019, `data/spot.csv` (Binance BTCUSDT) fino al 21/11/2026,
  poi Binance pubblico (data-api.binance.vision, scaricato il 26/11/2026 21:51 UTC, `data/binance_1d_nov2026.json`) fino al
  25/11/2026 (ultimo giorno chiuso). 3D = 3 giorni ricominciati ogni 1 gennaio (ultima barra dell'anno di 1–2 giorni).
- Esecuzione: segnale alla chiusura dell'ultimo giorno della barra, eseguito all'apertura del giorno successivo.
- W3.2: copia di `radar.weekly.simulate` (non modificato, R_LONG = R_SHORT = 0,25), dati congelati `research/p2_nuovi/data`
  (f_long 2018–20, f_repo dal 2021, fino al 15/11/2026), da verificare al dollaro prima di ogni risultato: dal 2021 78.474 $, DD −21,1%; 2018–20
  25.142 $, DD −37,3%. L'indicatore si calcola sulla serie del §2 (stessi prezzi Binance dal 2019).
- Costi: long spot 0,1% + 0,1% di slippage per lato; short perp 0,05% + 0,1% per lato + funding reale (f_long/f_repo; prima del
  2020 zero, dichiarato). 10.000 $, 1x, tutto il capitale. Posizione aperta a fine periodo valutata all'ultima chiusura al netto
  dell'uscita.

## 3. Periodi
P1 2018-01-01→2020-12-31 (mai guardato per i triangoli) · P2 2021-01-01→2023-12-31 · P3 2024-01-01→2026-11-25 (W3.2: →15/11).
Totali dal 2018 e dal 2021. IS = 2018–2022, OOS = 2023–oggi (nessun parametro si sceglie sui dati: i parametri sono i predefiniti
dello script; la divisione misura solo la stabilità). Dichiarato: le date 09/2024–11/2026 sono state viste (screenshot e
coincidenza), i rendimenti no. Ogni periodo parte flat con 10.000 $; riferimenti: buy & hold (apertura del primo giorno, stessi
costi) e W3.2.

## 4. H1 · il segnale da solo
**Descrittivo (studio d'evento, 1D e 3D, IS 40/10)**: per ogni triangolo dal 2018, rendimento a 7/30/90 giorni dall'apertura del
giorno dopo la chiusura della barra; confronto con la media di tutti i giorni dello stesso periodo. Placebo: 2.000 estrazioni dello
stesso numero di date casuali (giorni di chiusura di barra dello stesso intervallo, dal 2018, esclusi gli ultimi 90 giorni); p a
una coda nel verso dell'ipotesi (nero → rendimento maggiore, rosso → minore). 12 test (2 intervalli × 2 lati × 3 orizzonti),
Holm a 0,05. Anche: quota di neri seguiti da un minimo più basso entro 30 giorni ("il fondo era già dentro?").
**Strategie giudicate** (4):
- **S1** 3D solo long: nero → long all'apertura successiva; uscita al primo rosso; poi flat fino al nero successivo.
- **S2** 3D long/short: nero → long, rosso → short (perp), sempre in posizione dopo il primo segnale (inversione al segnale opposto).
- **S3** = S1 su 1D. **S4** = S2 su 1D.
**VALIDA** solo se, in P1, P2 e P3: finale > 10.000 $; CAGR/|DD| > buy & hold; max DD giornaliero ≥ −35%; finale senza i 2 trade
migliori del periodo > 10.000 $ (periodo senza trade = fallisce). In più: ≥ 8 trade 2018–26; placebo (1.000 traslazioni circolari
della serie dei segnali di almeno 60 giorni sull'intero 2018–26, p = quota con finale ≥ reale) entro Holm sulle 8 configurazioni
(S1–S4, W1–W4: p minimo ≤ 0,05/8, poi 0,05/7, …); vicini (lunghezza 30/40/50 × conteggio 8/10/12, 8 oltre la base): ≥ 75% in
profitto in tutti e tre i periodi. Manca solo placebo/Holm → "su carta". Si riportano sempre finale e DD dal 2021 contro W3.2:
"competitiva" solo se finale ≥ W3.2 E DD non peggiore di W3.2 dal 2021.

## 5. H2 · uscita / presa di profitto su W3.2 (2)
- **W1** con W3.2 in posizione, triangolo 3D CONTRARIO (rosso con long, nero con short) apparso dopo l'ingresso → chiusura totale
  all'apertura del giorno dopo la chiusura della barra. Rientro solo a una nuova decisione domenicale valida di W3.2.
- **W2** = W1 con i triangoli 1D.

## 6. H3 · filtro d'ingresso su W3.2 (2)
- **W3** alla decisione domenicale di W3.2, un nuovo ingresso long è bloccato se nei 30 giorni fino alla chiusura della domenica
  c'è un rosso 3D; uno short è bloccato se c'è un nero 3D. Il segnale bloccato si rivaluta la domenica dopo (regole W3.2).
- **W4** = W3 con i triangoli 1D.
**"Migliora W3.2"** solo se: CAGR/|DD| > W3.2 in P2 e in P3 e non inferiore in P1; DD non peggiore di oltre 1 punto in nessun
periodo; finale dal 2021 ≥ W3.2 oppure DD dal 2021 migliore di almeno 3 punti con finale ≥ 90% di W3.2; win rate dal 2021 ≥ 70%;
ancora migliore togliendo i 2 trade W3.2 che migliorano di più; ≥ 75% dei vicini (30/40/50 × 8/10/12; per W3/W4 anche finestra
15/45/60 giorni) migliora CAGR/|DD| dal 2021; placebo (1.000 traslazioni circolari della serie dei triangoli, p = quota con
CAGR/|DD| dal 2021 ≥ reale) entro Holm sulle 8. Elenco dei trade W3.2 toccati.

## 7. Altro (descrittivo, non giudicato)
glaz 30/6 su S1–S4 e W1–W4; settimanale (lunedì–domenica) solo nello studio d'evento; ETH (research/w32_multi, stessi parametri)
solo per S1–S2 3D e lo studio d'evento: una configurazione BTC "valida" conta solo se su ETH non perde contro il buy & hold.
Caso di oggi: nero 3D sulla barra 15–17/11/2026 contro lo short W3.2 aperto dal 16/11 (W1 lo avrebbe chiuso all'apertura del
18/11): solo descritto, nessuna raccomandazione operativa.

## 8. Cosa NON si fa
Nessuna modifica a radar/, data/, tests/ o al tool; nessun commit da parte dell'agente. Nessuna ricerca dei parametri: 40/10 si
giudica com'è, i vicini sono solo robustezza. Potenza: sul 3D ci sono 25 triangoli dal 2018 (9 neri, 16 rossi), 19 dal 2021: un
esito positivo con così pochi eventi resta al più "su carta".
