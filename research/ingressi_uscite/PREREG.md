# Preregistrazione · Ingressi e uscite a scaglioni, stop, distribuzione, giorno di decisione (W3.1, BTC settimanale) · 22/11/2026

Scritta PRIMA di qualsiasi backtest delle varianti. In fase 1 il motore è stato solo verificato (deve riprodurre W3.1) e gli
eventi sono stati CONTATI (lezione 98): `iu_count.py` non stampa rendimenti, P&L, DD o esiti dei trade delle varianti.
Va committata da sola prima della fase 2. Regole, parametri, vicini, soglie e regole di decisione non si cambiano dopo:
ogni idea emersa dai risultati va in una nuova preregistrazione.

## 1. Domanda dell'utente e cosa c'è già nel diario
"Ingresso e uscita a scaglioni (DCA), take profit e stop loss migliori: la nuova strategia batte la vecchia?"
- DCA in entrata su W2: lezione 53 (2 tranche con limite a −k·ATRw per 5 giorni: 12/12 perdenti sul 2021–26; i trend migliori
  non ritracciano). Ingressi solo-limite: lezione 92 (comprano più caro). E2/E3 sono quindi controlli con aspettativa negativa;
  E1 (DCA a tempo dentro la settimana) e la finestra di 2 settimane con ripiego a mercato (E3) non sono mai stati provati.
- Uscite parziali: lezione 73 (tagliano le code destre). TP 1/3 a +2R/+3R già perdente (griglia G, p2_nuovi): T1 è solo controllo.
- Stop: 2,0 / 2,5 / 3,0 ATRw al 10% già nella griglia G (2,0 gradino negativo; lezione 60). Nuovi: 2,25 e 2,75.
- Distribuzione: lezione 102 (vale ~¼ del profitto, margini 0,02–0,11σ, funding provvisorio OKX). Mai testata come dimensione.
- Giorno di decisione: lezione 94 (domenica migliore dei 7 dal 2021 per caso). G7 = proposta della revisione Fable.
- Deroga dichiarata al limite di 8 varianti del metodo: l'utente ha chiesto 5 dimensioni; si testano 14 varianti principali,
  una dimensione alla volta contro W3.1 (niente prodotto cartesiano), più al massimo 1 combinazione (sezione 7).

## 2. Riferimento e dati
- W3.1 (radar/weekly.py): stessi segnali di W3, rischio allo stop iniziale 10% (long e short), stop e trailing 2,5 ATRw a
  cricchetto, nessun TP, uscite EMA21 settimanale e distribuzione. Long spot 1x, short perp; spot 0,1%/lato, perp 0,05%/lato +
  funding reale, slippage 0,1%. Nessun rendimento della liquidità.
- Dati congelati di research/p2_nuovi (`p2_data.load`): `f_repo` 2019-09 → 15/11/2026 per il 2021+; `f_long` per il 2018–20
  (PROXY: flusso = CVD spot prima del 2019-09; funding assente nel 2018–19, quindi la distribuzione può scattare solo nel 2020).
- Motore `iu_engine.py`: copia di radar.weekly.simulate con posizione a lotti. Controllo superato (fase 1, `conteggi.txt`):
  equity identica a radar.weekly (tolleranza 1e-6) in tutti i periodi; 2021+ 10.000 → **27.190 $, DD −9,8%**, 13 trade;
  IS 2021–23 17.879 $ (DD −8,4%, 7 trade); OOS 2024–26 15.228 $ (−9,8%, 6); 2018–20 16.734 $ (**−19,2%**, 9).
  Invarianze superate (configurazioni degeneri = W3.1): E1 una parte, E2 n=1, U1 a=1, U2 2,5/2,5, D3 ×1, D2 n=1, TP a +99R.

## 3. Regole comuni
- Segnali W3.1 invariati (decisione alla chiusura settimanale, esecuzione all'apertura del giorno dopo). Un solo trade alla volta.
- Rischio allo stop 10% dell'equity come SOMMA degli scaglioni, esposizione mai oltre 1x. Scaglione j: esposizione
  w_j · min(1, 0,10 · ref_j / |ref_j − stop_j|) × equity al primo ingresso; primo scaglione ref = chiusura del segnale, stop =
  stop iniziale (identico a W3.1); scaglioni successivi ref = chiusura del giorno prima (o prezzo limite), stop = stop in vigore.
- Ordine nel giorno: ordini all'apertura → limite E3 (prima dello stop, prudente) → stop per lotto (il giorno dello stop niente
  TP) → TP → funding. Scaglioni non ancora eseguiti si annullano se il trade esce.
- Solo BTC (lezioni 87, 104: il vantaggio non si trasferisce; nessun altro asset come criterio).

## 4. Varianti (14 principali, una dimensione alla volta; vicini fissati ora)
| Dim. | Variante principale | Regola meccanica | Vicini |
|---|---|---|---|
| E | E1 DCA a tempo | 3 parti uguali alle aperture di lun/mer/ven della settimana dopo il segnale | 2 parti lun/gio; 5 parti lun–ven |
| E | E2 DCA settimanale | 1/3 al lunedì; 1/3 ai 2 lunedì successivi se alla domenica il segnale d'ingresso dello stesso lato è ancora vero (sennò lo scaglione si salta, senza recupero) | 2 settimane (1/2+1/2); 4 settimane (1/4) |
| E | E3 mezzo + ritracciamento | 1/2 al lunedì; 1/2 con limite a prezzo d'ingresso − 0,5 ATRw (segnale) per 14 giorni; se non eseguito, a mercato all'apertura del 15° giorno | 0,25 e 0,75 ATRw |
| U | U1 uscita in due tempi | 1/2 all'apertura dopo la prima condizione d'uscita settimanale (EMA21 o distribuzione); 1/2 dopo la decisione successiva se una condizione è ancora vera, altrimenti il resto continua e la prossima condizione lo chiude; stop/trailing chiudono tutto | 1/3 + 2/3; 2/3 + 1/3 |
| U | U2 trailing in due parti | lotti uguali con stop iniziale e trailing a 2,0 e 3,0 ATRw (dimensione con k medio 2,5) | 2,25/2,75; 1,75/3,25 |
| T | T1 TP parziale (controllo) | 1/3 della quantità iniziale con limite a +3R (R = 2,5 ATRw del segnale), resto in trailing | +2R; +4R |
| K | K 2,25 | stop iniziale e trailing 2,25 ATRw, rischio 10% | 2,0 (griglia G); 2,5 (W3.1) |
| K | K 2,75 | 2,75 ATRw | 2,5; 3,0 |
| K | K 3,0 | 3,0 ATRw | 2,75; 3,25 |
| D | D1 senza distribuzione | nessuna uscita per distribuzione | — (nessun parametro) |
| D | D2 con conferma | condizione di distribuzione vera per 2 decisioni consecutive | 3 decisioni |
| D | D3a soglie −20% | FUND_HOT 0,00072, FUND_COLD −0,00024 (uscita più facile) | ×0,7; ×0,9 |
| D | D3b soglie +20% | FUND_HOT 0,00108, FUND_COLD −0,00036 (uscita più difficile) | ×1,1; ×1,3 |
| G | G7 sette giorni | 7 sotto-portafogli da 1/7, uno per giorno di chiusura settimanale (lun…dom), mai ribilanciati | — (confronto informativo anche con la mediana dei 7 giorni) |

## 5. Metriche (per ogni variante, vicino e W3.1; buy & hold spot con costi come riferimento)
Capitale finale da 10.000 $ dal 01/01/2021, rendimento, CAGR, DD giornaliero (mark-to-market), CAGR/DD, trade, WR, peggior
trade, perdita allo stop (massima perdita pianificata all'ingresso = somma degli scaglioni allo stop in vigore; e peggior trade
realizzato), esposizione media; IS 2021–23 e OOS 2024–26 ripartendo da 10.000 $; 2018–20 su f_long (dati proxy); capitale
senza il trade migliore (pnl del trade migliore posto a 0); bootstrap dei trade: 10.000 percorsi di 13 trade estratti con
reinserimento dai trade 2018–26 della variante (f_long 2018–20 + f_repo 2021+), seme 20261122, P(DD trade per trade ≥ 20%)
(informativo; il DD trade per trade sottostima il giornaliero, lezione 8). La posizione aperta a fine periodo si chiude
all'ultima chiusura con commissione.

## 6. Criteri (scritti ora)
Una variante **"batte W3.1"** solo se TUTTE:
1. Potenza: almeno 3 trade cambiati dal 2021 (tolti, nuovi, uscita o riempimenti diversi, o, per K, dimensione diversa) e
   almeno 1 per metà. Sennò "senza potenza" (non è una bocciatura della regola, ma non può battere W3.1).
2. CAGR/DD e capitale finale migliori di W3.1 sia nel 2021–23 (17.879 $, 2,558) sia nel 2024–26 (15.228 $, 1,615).
3. DD giornaliero 2018–20 non peggiore di W3.1 (−19,2%, confronto al decimo).
4. Vicini stabili: entrambi i vicini (dove esistono) con CAGR/DD dal 2021 e capitale finale dal 2021 migliori di W3.1
   (1,903; 27.190 $).
5. Non dipende da ≤ 2 trade: Δ_j = log(1+pnl variante) − log(1+pnl W3.1) per trade appaiato sulla data del segnale (trade
   tolti o nuovi con l'altro lato a 0); se togliendo i 2 Δ_j positivi più grandi la somma diventa ≤ 0, fallisce. Si elencano
   tutti i trade con |Δ_j| > 0,1 punti.
6. Senza il trade migliore: capitale ≥ W3.1 senza il suo trade migliore.
Il rischio non si sceglie qui (è fisso al 10%): CAGR/DD si usa solo a parità di rischio e sempre insieme al capitale finale
(lezione 101). Con 13 trade (7 + 6) la potenza è bassa: un "batte" è un'indicazione, non una prova.
**Test con p-value e correzione** (lezione 104: la famiglia conta solo i test con p-value): per le 13 varianti appaiate (E1,
E2, E3, U1, U2, T1, K 2,25/2,75/3,0, D1, D2, D3a, D3b) test di permutazione dei segni su Δ_j (esatto se m ≤ 20 trade con
Δ ≠ 0, sennò 100.000 estrazioni), statistica ΣΔ_j, unilaterale; più 1 placebo per il valore della distribuzione (P-D: le 4
uscite per distribuzione di W3.1 dal 2021 spostate a domeniche casuali dentro gli stessi trade, fra l'ingresso e l'uscita
reale, 2.000 estrazioni, metrica capitale finale; p = (k+1)/2.001). Famiglia = 14, Holm al 5% (soglia minima 0,0036).
p minimo raggiungibile con m trade cambiati = 2^−m: con m ≤ 8 nessuna variante può essere significativa (dichiarato ora).
G7 non ha test appaiato: solo criteri 2–6 (vicini non applicabili) e confronto con la mediana dei 7 giorni.
**Esiti**: "proponibile per il tool" = batte W3.1 e Holm significativo; "batte W3.1, su carta" = criteri 1–6 senza
significatività; altrimenti "non batte W3.1". Nessuna modifica a radar/: ogni proposta va prima all'utente (decisione D1).

## 7. Combinazione (al massimo 1 configurazione)
Solo se almeno 2 dimensioni hanno una variante che "batte W3.1". Da ciascuna di queste dimensioni si prende la variante con
il massimo di min(CAGR/DD IS, CAGR/DD OOS); la combinazione applica tutte le scelte insieme (U2 con K: lotti a k−0,5 e k+0,5;
G7 avvolge il resto). Criteri 2, 3, 5, 6 contro W3.1 e contro la migliore variante singola; se non batte la migliore singola,
la risposta resta la variante singola. Con una sola dimensione promossa non si combina nulla.

## 8. Eventi contati in fase 1 (solo conteggi, `iu_count.py` → `conteggi.txt`)
W3.1: 13 trade dal 2021 (7 IS + 6 OOS; il trade a cavallo è aperto a fine IS), uscite dist 4 / EMA 5 / trailing 4; 2018–20: 9.
"Cambiati" = tolti/nuovi/modificati rispetto a W3.1 (date e motivi d'uscita, riempimenti, prese parziali; esclusa la sola dimensione).

| Variante (vicini) | 2021+ cambiati | IS | OOS | 2018–20 | Eventi |
|---|---|---|---|---|---|
| E1 lun/mer/ven (2; 5 parti) | 13 | 7 | 6 | 9 | 26 scaglioni aggiunti; nessun trade fermato prima del 3° |
| E2 3 sett. (2; 4) | 12 | 7 | 5 | 6 | 19 aggiunti, 7 saltati (segnale non più valido); vicini 12/1 e 24/14 |
| E3 0,5 ATR (0,25; 0,75) | 13 | 7 | 6 | 8 | limite eseguito 1/13 (0,25: 3/13; 0,75: 0/13), resto a mercato al 15° giorno; 2018–20 5/9 |
| U1 1/2+1/2 (1/3; 2/3) | 1 tolto + 8 | 1+4 | 3 | 5 | 8 prime uscite parziali, 8 non confermate; il resto occupa la posizione e toglie il trade 2021-10-03 |
| U2 2,0/3,0 (2,25/2,75; 1,75/3,25) | 4 | 1 | 3 | 2 | 8 lotti chiusi separatamente; vicino 2,25/2,75: 1 solo trade (0 IS) |
| T1 +3R (+2R; +4R) | **0** | 0 | 0 | 1 | nessun +3R toccato dal 2021 (+2R: 4; +4R: 0) → senza potenza |
| K 2,25 | 1 nuovo + 3 (+ dimensione su tutti) | 1+2 | 1 | 0 | vicino 2,0: 2 nuovi + 6 |
| K 2,75 | 1 (+ dimensione) | 0 | 1 | 2 | |
| K 3,0 (3,25) | 4 (+ dimensione) | 1 | 3 | 2 | 3,25: stessi 4 trade |
| D1 senza | 4 | 2 | 1 | 2 tolti + 2 | 4 uscite per distribuzione sostituite |
| D2 2 dom. (3) | 4 | 2 | 1 | 1 tolto + 2 | restano 3 uscite dist (3 dom.: 1) |
| D3a ×0,8 (0,7; 0,9) | 2 | 2 | **0** | 0 | 5 uscite dist; ×0,7: 1 nuovo + 3 |
| D3b ×1,2 (1,1; 1,3) | 1 | **0** | **0** | 1 | ×1,1: 0 cambiati |
| G7 7 giorni | 106 trade (lun 15, mar 13, mer 15, gio 17, ven 17, sab 16, dom 13) | 57 | 49 | 70 | |
Lettura (senza rendimenti): T1 a +3R, D3a (0 trade OOS) e D3b (1 trade) falliranno il criterio di potenza; K 2,75 e U2v
2,25/2,75 cambiano 1 sola uscita; E3 è quasi sempre "1/2 subito + 1/2 a mercato dopo 2 settimane" (i trend non ritracciano,
come nella lezione 53); il p minimo è 2^−12/2^−13 per E1–E3, 2^−9 per U1, ≥ 2^−4 per U2, K (uscite) e D: queste ultime non possono superare Holm.

## 9. Fase 2 (dopo il commit di questo file da solo)
`iu_run.py` esegue tutto alla lettera; `README.md` in italiano: tabella dal 2021 (W3.1, buy & hold, 14 varianti), IS/OOS,
2018–20, vicini, senza il trade migliore, bootstrap, elenco dei trade che cambiano, p-value con Holm, verdetto per variante,
risposta "la nuova batte la vecchia?" e testo della lezione per RESEARCH.md.
