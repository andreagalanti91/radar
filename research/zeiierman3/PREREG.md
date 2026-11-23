# Zeiierman Trend Pressure · ciclo 3 — "compra a −90, vendi a −20" · preregistrazione

Scritta il 23/11/2026 alle 19:30 UTC, PRIMA di eseguire qualsiasi backtest o di calcolare qualsiasi rendimento di questo ciclo.
Si committa da sola. Richiesta dell'utente: "buy quando l'indicatore è a −90, sell quando è a −20".

## Dichiarazione (asticella alzata)
L'indicatore è già stato guardato due volte sul 2021–26 (cicli 1 e 2, lezione 91: 31 regole, nessuna regge; la migliore, "compra
blu vendi rossa" con stop, 21,1k contro 25,6k del buy & hold e 78,5k di W3). Le soglie −90/−20 vengono dall'utente, che ha visto i
grafici 2021–26: quel periodo NON è fuori campione. Per questo: tre periodi separati (2018–20 è l'unico mai guardato), tutte le
condizioni in tutti e tre, correzione di Holm sul numero di configurazioni giudicate.

## Indicatore e dati
- Porting `research/zeiierman/ztp.py` (verificato riga per riga il 13/11) IMPORTATO, non riscritto. Parametri predefiniti dello
  script dell'utente (`zeiierman_trend_pressure.pine`): Pulse 21/9/7, Trend 55/120/5/9, zona 20, sensibilità 7, Core 16/0,65
  (soglie di esaurimento dell'autore −12/−88; qui NON usate: le soglie sono quelle dell'utente, −90 e −20).
- "Indicatore" = **Z-Trend** (`tz`, la linea principale; primaria). Alternative: **Z-Pulse** (`pz`) e **Pressure Core** (`cz` =
  c0 − 100, scala −100…0). Nessun'altra linea.
- Giornaliero: candele UTC ricostruite dal 4h Binance BTCUSDT (`research/ema_sma/data/BTCUSDT_4h.csv.gz`, dal 17/08/2017) con la
  storia del repo prima (dal 2014) per il riscaldamento (`es_lib.daily_from`). 4h: stesse candele Binance. Ultimo dato: giorno
  22/11/2026 (ultima candela 4h aperta alle 20:00 UTC del 22/11). Indicatore calcolato su tutta la storia, poi tagliato ai periodi.

## Regole (long salvo R4; segnale alla chiusura della barra t, esecuzione all'apertura di t+1)
Sia x la linea (tz salvo dove indicato), "scende sotto −90" = x[t] < −90 e x[t−1] ≥ −90; "risale sopra −90" = x[t] > −90 e
x[t−1] ≤ −90; uscita "sopra −20" = x[t] > −20 (prima barra dopo l'ingresso in cui vale).
- **R1** long quando x scende sotto −90; uscita quando x > −20. Nessuno stop. Rientro solo a un nuovo attraversamento.
- **R2** long quando x risale sopra −90 dopo esserci stata sotto (conferma); uscita quando x > −20. Nessuno stop.
- **R3** = R1 con stop di protezione fisso a 2 × ATR(14) (RMA, come Pine) della barra del segnale sotto il prezzo d'ingresso;
  stop intrabarra (uscita a min(apertura, stop)); rientro al successivo attraversamento sotto −90. Si sceglie l'ATR (non il
  minimo precedente); il "minimo delle 10 barre precedenti" è solo un vicino.
- **R4** speculare short: short quando x sale sopra −20 (x[t] > −20 e x[t−1] ≤ −20), copertura quando x < −90. SOLO
  descrittivo (non giudicato, non nel conteggio di Holm).
- **R5** "spiraglio" del ciclo 1, solo 4h su tz: long al rilascio della zona blu (tz > −70 con tz[−1] ≤ −70) SOLO se W3.2 è
  senza posizione; uscita al rilascio rosso (tz < −30 con tz[−1] ≥ −30), allo stop 2,5 ATR(14) 4h (come il ciclo 1), oppure
  all'apertura in cui W3.2 apre una posizione (W3.2 ha la precedenza sul capitale). Stato di W3.2: simulazione congelata
  (f_long per il 2018–20, f_repo dal 2021, fino al 15/11) e, dal 16/11, lo short reale di W3.2 (segnale del 15/11).

## Configurazioni giudicate (m = 13 per Holm)
Indipendenti (11): V1 R1 tz 1D · V2 R2 tz 1D · V3 R3 tz 1D · V4 R1 tz 4h · V5 R2 tz 4h · V6 R3 tz 4h · V7 R5 4h ·
A1 R1 pz 1D · A2 R2 pz 1D · A3 R1 cz 1D · A4 R2 cz 1D (alternative, stesse soglie).
Dentro W3.2 (2): **W1** = R2 (tz 1D) come long aggiuntivo solo quando W3.2 è flat: 100% del capitale in spot all'apertura dopo il
segnale, uscita quando tz > −20 oppure all'apertura in cui W3.2 entra (si chiude e W3.2 entra con le sue regole); **W2** =
uscita parziale: con W3.2 long aperto, al primo attraversamento di tz sopra −20 (tz[t] > −20, tz[t−1] ≤ −20) dopo l'ingresso si
vende il 50% della quantità all'apertura dopo; con W3.2 short, al primo attraversamento di tz sotto −90 si copre il 50%. Una
volta per trade; il resto segue W3.2 (stop, trailing, EMA21, distribuzione) invariato.
Il metodo prevede ≤ 8 varianti: qui 13 per richiesta esplicita dell'utente (R1–R5, due intervalli, due alternative, due varianti
dentro W3.2); la correzione di Holm sulle 13 compensa.

## Esecuzione e costi
10.000 $ per periodo, 1x, posizione intera. Costi come W3.2 spot: commissione 0,1% + slippage 0,1% per lato (acquisto a
apertura × 1,001, vendita × 0,999, commissione sul nozionale). Short R4 e short di W3.2: in più il funding (f_long, poi
data/funding.csv; 1/6 per barra sul 4h). Posizione aperta a fine periodo valutata all'ultima chiusura al netto dell'uscita.
DD = massimo drawdown dell'equity giornaliera (chiusure UTC; sul 4h l'ultima candela del giorno). W3.2 dentro: copia di
`radar.weekly.simulate` (non modificato), dati congelati `research/p2_nuovi/data` fino al 15/11, verificata prima: dal 2021
78.474 $, DD −21,1%; 2018–20 25.142 $, DD −37,3%.

## Periodi e metriche
P1 2018-01-01→2020-12-31 · P2 2021-01-01→2023-12-31 · P3 2024-01-01→2026-11-22 (W3.2 al 15/11); ognuno parte flat con 10.000 $.
Anche il totale dal 01/01/2021 (richiesta di metodo). Metriche: finale, rendimento, CAGR, max DD giornaliero, CAGR/|DD|, MAR
(rend./|DD|), trade, win rate, esposizione. Riferimenti: buy & hold (dall'apertura del primo giorno) e W3.2 per periodo.

## Criteri (scritti ora; tutti richiesti)
Una configurazione indipendente è **VALIDA** solo se:
1. finale > 10.000 $ in P1, P2 e P3;
2. CAGR/|DD| superiore al buy & hold in P1, P2 e P3;
3. max DD giornaliero ≥ −35% in ogni periodo;
4. non dipendente da ≤ 2 trade: ≥ 8 trade in totale 2018–26 e, in ogni periodo, il composto senza i 2 trade migliori resta
   > 10.000 $;
5. placebo: sull'intero 2018-01-01→2026-11-22, 2000 sequenze con le stesse durate dei trade e degli intervalli flat in ordine
   casuale (stesso numero di trade, stessi costi, senza stop), p = (1 + #finale placebo ≥ reale)/2001; Holm su m = 13 (p minimo
   ≤ 0,05/13 ≈ 0,0038, poi 0,05/12, …);
6. vicini: soglie d'ingresso −85/−95 × uscita −15/−20/−25/−30 (11 combinazioni oltre la base; per R5 nessuna soglia utente:
   vicini −65/−75 × −25/−35, 4 combinazioni; per R3 anche stop 1,5/2,5 ATR e minimo delle 10 barre precedenti): almeno il 75%
   in profitto in tutti e tre i periodi. I vicini servono solo per la robustezza, NON per scegliere.
Se manca anche una condizione: NON VALIDA. Se manca solo il placebo/Holm: "su carta, nessuna adozione".

**Dentro W3.2 "migliora"** solo se: CAGR/|DD| superiore a W3.2 in P2 e in P3, e in P1 CAGR/|DD| non inferiore a W3.2; DD non
peggiore di oltre 1 punto in nessun periodo; placebo (W1: ingressi casuali da flat con le stesse durate; W2: giorno della
vendita parziale estratto a caso dentro gli stessi trade W3.2, 2000 estrazioni) con p entro Holm; elenco dei trade toccati.

## Descrittivo (nessun giudizio)
Dal 2018 sul giornaliero (tz primaria; pz e cz in sintesi): per ogni attraversamento di −90 (discesa sotto, risalita sopra) e di
−20 (salita sopra, discesa sotto): data, prezzo, rendimento a 7/30/60 giorni dall'apertura successiva, minimo successivo (minimo
dei minimi fino all'uscita dalla zona, al massimo 60 giorni, rispetto all'apertura d'ingresso: "quanto scende ancora dopo il
buy"), durata in zona (barre fino al ritorno oltre la soglia). Base: media di tutti i giorni dal 2018. Stessa tabella sul 4h solo
in sintesi. Short R4: tabella dei trade.

## Caso di oggi
Valori di tz, pz, cz al 22/11/2026 (1D) e all'ultima candela 4h; se R1/R2/R3/R5 danno un segnale ora o quanto manca; confronto con
lo short di W3.2 aperto dal 16/11 (segnale del 15/11).

## Note
Solo BTC (richiesta). Niente modifiche a radar/ e tests/. Codice e output in research/zeiierman3/.
