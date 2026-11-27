# PREREG · emergenti · W3.2 e varianti sulle monete poco capitalizzate, long e short, leva 2x/5x, budget 1% · 27/11/2026

Scritto dopo i soli conteggi di struttura (`DATI.md`: universo, storia, segnali, distanza dello stop; nessun P&L, equity, win
rate o esito di un trade è stato calcolato o guardato) e **prima di qualsiasi rendimento**. Va committato da solo prima della
fase 2. Già noto e dichiarato: lezioni 104, 110, 111, 123, 129 (W3.2 con i parametri di BTC non si trasferisce: 0/78 altcoin
della top 200; cancello di BTC: solo TRX; screener all'indietro Q8 perde contro BTC + ETH). Questo studio non cambia W3.2,
`radar/weekly.py`, lo scanner o i capitali di BTC ed ETH: un risultato positivo produce solo una proposta all'utente.

## Domanda dell'utente
Monete emergenti, long e short, trade speculativi a 2x o 5x su Bitget/OKX con **budget totale dell'1% del capitale** per tutte
le operazioni; capire quando entrare long o short e se l'algoritmo dello scanner si può rendere più profittevole. Ipotesi
dell'utente da verificare senza bias: "i long sono in netto positivo".

## Universo e ammissione (in avanti, senza sguardo al futuro)
- Universo e dati congelati in `data/` (`DATI.md`). **Universo di giudizio = emergenti punto nel tempo**: per l'anno Y la lista
  è fissata al 1° gennaio con l'istantanea CMC più recente prima del 1/1/Y (20201227, 20220102, 20230101, 20231231, 20241228,
  20251116), rank 101–200 dopo le esclusioni. Un ingresso nell'anno Y è ammesso solo su monete della lista di Y; la versione
  completa W3.2 deve esistere alla domenica del segnale; le uscite seguono le regole anche dopo il cambio d'anno.
- Ogni trimestre (1/1, 1/4, 1/7, 1/10) si ricalcolano solo i filtri basati sui dati (H-b) con la storia precedente; la lista
  dei rank cambia una volta l'anno (le istantanee storiche sono annuali).
- La vista "emergenti di oggi" (CoinGecko 101–500) è **descrittiva** (sopravvivenza) e non decide nulla.
- **Il filtro "quotata su Bitget/OKX" non si usa nel giudizio storico**: le liste esistono solo per gli strumenti vivi oggi, quindi
  premierebbe le sopravvissute. Vale solo nel periodo in avanti (registro sulla carta dal 30/11/2026).

## Motore, costi, leva (fase 2)
- Copia di `radar.weekly.simulate` in `research/emergenti/engine.py` con parametri esposti (costi, trailing, uscita EMA, leva,
  liquidazione, cancello). **Controllo obbligatorio**: con i parametri di default riproduce BTC 2021-01-01 → 2026-11-10 = 78.474 $.
- Segnali, regime, flusso perp, filtro F1, trailing a cricchetto, distribuzione: invariati (parametri di BTC).
- Tutte le posizioni in perp (anche i long). **Costi 0,2% per lato** (0,1% commissione + 0,1% slittamento), **funding reale**
  dall'archivio Binance (OKX dove manca; zero dove non esiste: dichiarato per moneta), sensibilità a 0,4% per lato.
- **Liquidazione simulata** su minimo/massimo giornaliero, margine isolato: prezzo di liquidazione long = ingresso × (1 − 1/L +
  0,01), short = ingresso × (1 + 1/L − 0,01) (mantenimento 1%; sensibilità 2,5%); alla liquidazione si perde tutto il margine
  della posizione. Nello stesso giorno vale il livello più vicino all'apertura; apertura già oltre la liquidazione = liquidazione.
- **Cornice del budget (uguale per tutte le varianti)**: budget = 10.000 $ che rappresentano l'1% del capitale; massimo **5
  posizioni simultanee**, margine per posizione = 1/5 del budget corrente; segnali in eccesso scartati (priorità al volume perp a
  90 giorni più alto). Senza leva la posizione segue la size di W3.2 dentro la quota: nozionale = quota × min(1, 0,25/d), d =
  distanza dello stop. Si riportano rendimento e DD sul budget e sul capitale totale (= 1% del budget).
- Periodi: intero 2021-01-01 → 2026-11-24; **IS 2021–2023**, **OOS 2024-01-01 → 2026-11-24**, ultimo anno 2025-11-24 →
  2026-11-24; ogni periodo riparte da 10.000 $ e da flat.

## Varianti giudicate (10; Holm su m = 10)
| # | Ipotesi | Regola |
|---|---|---|
| V1 | H-base | W3.2 com'è, long e short, 1x (riferimento) |
| V2 | H-base | solo long (verifica dell'ipotesi dell'utente) |
| V3 | H-base | solo short |
| V4 | H-a | leva adattiva 2x: L = min(2; 1/(d + 0,05)), nozionale = quota × L |
| V5 | H-a | leva adattiva 5x: L = min(5; 1/(d + 0,05)) (dai conteggi: nessun ingresso ammette 5x pieno) |
| V6 | H-b | qualità: storia ≥ 52 settimane, volume perp medio a 90 giorni ≥ 10 M$/giorno, flusso al segnale ≥ +0,5σ (long) / ≤ −0,5σ (short) |
| V7 | H-c | solo nel verso di W3.2 su BTC alla domenica del segnale (cancello di Q4) |
| V8 | H-c | solo contro W3.2 su BTC (BTC nel verso opposto) |
| V9 | H-d | trailing 2,0 ATRw (stop iniziale 2,5 ATRw invariato) |
| V10 | H-d | uscita alla chiusura settimanale oltre la EMA 10 invece della EMA 21 |

**Descrittive, non giudicate**: 2x e 5x fissi senza tetto (nozionale = quota × L: quante liquidazioni e quanto costano); 1x a
quota piena; long/short per gruppo "con BTC / contro BTC / BTC flat"; ingressi con storia < 52 settimane; portafoglio per
rischio (perdita allo stop = 5% del budget, nozionale ≤ quota × 2) e tetti di 3 e 10 posizioni; uscita fissa a 4/8 settimane
per misurare la durata utile; vista "emergenti di oggi"; i 5 long dello scanner del 22/11 seguiti in avanti.
**Vicini (solo per la conferma)**: V4/V5 margine 0,03/0,08; V6 (26 sett., 5 M$, 0,25σ) e (104 sett., 20 M$, 1,0σ); V9 1,5 e 2,5
ATRw; V10 EMA 8 e 13. V1–V3 e V7–V8 non hanno parametri: vicini = costi 0,4% per lato e mantenimento 2,5%.

## Criteri di "operabile" (tutti, sul periodo intero salvo indicazione)
1. CAGR/DD del budget > CAGR/DD del **buy & hold equipesato delle emergenti idonee** (stessa lista annuale, ribilanciato al 1/1,
   stessi costi).
2. DD giornaliero del budget ≥ −40%.
3. Win rate ≥ 50% (operazioni chiuse + aperta valutata all'ultima chiusura).
4. Rendimento positivo in IS, in OOS e nell'ultimo anno.
5. ≥ 20 operazioni nel periodo intero e ≥ 10 in OOS.
6. Conferma: senza il 10% migliore delle operazioni il budget finale resta > 10.000 $; i vicini battono il criterio 1 in
   almeno metà dei casi.
7. Placebo: stesso numero di ingressi, stesso lato, stessa durata e stessa size, date e monete estratte a caso fra le
   monete-giorno idonee (5.000 prove, seme 7); p unilaterale sul CAGR/DD del budget, **Holm α = 0,05 su m = 10**.
Una variante H-a…H-d **migliora** W3.2 com'è solo se, oltre a 1–7, il suo CAGR/DD supera quello di V1 (V2 o V3 se è a un lato)
sia in IS sia in OOS. Contesto (non criterio): W3.2 su BTC, buy & hold di BTC, BTC + ETH come in uso.
**Ipotesi dell'utente**: "i long sono in netto positivo" è confermata solo se V2 passa 3–5 e 7; altrimenti si riporta con i
numeri (anche per anno e per gruppo con/contro BTC) e la frase si considera non verificata.

## Esiti previsti dalla struttura (scritti ora, per non adattarli dopo)
- V5 a 5x pieno non è realizzabile con lo stop di W3.2 (0 ingressi su 1.190): V5 coincide quasi sempre con "liquidazione al
  posto dello stop" e rischia quasi tutta la quota per operazione.
- Con 2x fisso circa metà dei long e quasi tutti gli short finiscono in liquidazione prima dello stop (52% e 93%).
- Il 2021 ha 4 monete idonee al 1/1: l'IS dipende dal 2022–23.

## Limiti dichiarati
Classifiche storiche solo top 200 (una moneta scesa sotto il 200 diventa invisibile: la fascia 201–500 storica manca); lista
annuale (non trimestrale) dei rank; istantanea 2026 del 16/11/2025; monete senza perp Binance quasi tutte senza dati (166 delle
503 emergenti); delisting: le serie finiscono all'ultimo giorno scambiato e la posizione si chiude all'ultima chiusura (può essere
ottimistico); operabilità storica su Bitget/OKX ignota; funding mancante per le serie OKX e per novembre 2026 sulle monete nuove;
slittamento reale sulle monete piccole forse > 0,1% (sensibilità 0,4%); liquidazione semplificata (mantenimento fisso, nessuna
commissione di liquidazione, candele giornaliere); W3.2 è stata sviluppata su BTC.

## Revisione
Revisione critica di un agente separato (sola lettura) con 5 operazioni ricalcolate a mano. Un solo secondo ciclo, solo per
errore del motore o ipotesi motivata dalla diagnosi, con addendum committato prima; risultati del secondo ciclo esplorativi.
