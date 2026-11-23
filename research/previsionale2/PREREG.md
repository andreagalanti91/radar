# PREREG · Previsionale 2 · regimi di mercato e politica economica (BTC a 7 e 30 giorni) · 23/11/2026

Scritto e committato DA SOLO prima di calcolare qualsiasi prestazione di questo ciclo.

**Cosa è già stato guardato (dichiarazione).** Il periodo di giudizio 2021–26 NON è vergine: il primo ciclo
(research/previsionale/, PREREG f656594, lezione 112) e la sua revisione critica lo hanno già guardato, e da lì vengono la
diagnosi e la scelta delle quattro variabili "a segno stabile" (pf, sf, rsi, vol: stabilità misurata sui riaddestramenti
2021–26, quindi selezione contaminata). Sono noti anche gli esiti di research/notte_1511/n3 (lezione 96: liquidità netta a 28
giorni, FOMC, stablecoin, premio Coinbase: non anticipano) e della lezione 97 (probabilità a celle per regime: 0/5.790).
Per questo ciclo, prima di questo file: verificata la raggiungibilità di FRED (scaricata DGS10, viste le prime e ultime
righe) e delle pagine FOMC della Fed; nessuna serie macro è stata incrociata con BTC, nessun modello addestrato.
Conseguenza: asticella più alta (§5) e correzione di Holm sul totale dei test dei DUE cicli (8 + 8 = 16).
Attesa a priori: bassa. L'esito negativo è previsto e va scritto così.

## 1. Dati
- BTC: gli stessi dati congelati del primo ciclo (fc_data.dataset(), taglio 15/11/2026), bersaglio y_h(t) = 1 se
  close(t+h)/close(t) − 1 > 0, h ∈ {7, 30}; previsione alla chiusura di t (24:00 UTC). Codice del primo ciclo importato, non riscritto.
- Politica economica: FRED fredgraph.csv (pubblico, senza chiave), salvato in research/previsionale2/data/. Valori di oggi
  (ultima revisione), usati solo dopo il ritardo di disponibilità sotto: "valore con data di osservazione d utilizzabile dalla
  chiusura BTC del giorno d + L" (poi portato in avanti).

| Serie | Frequenza | Ritardo L applicato | Motivo |
|---|---|---|---|
| DFF (tasso effettivo Fed) | giornaliera | 2 giorni | pubblicato il giorno lavorativo dopo |
| WALCL (bilancio), WTREGEN (conto del Tesoro) | settimanale (mercoledì) | 2 giorni (dal venerdì) | H.4.1 il giovedì sera USA |
| RRPONTSYD (reverse repo) | giornaliera | 1 giorno | pubblicato il pomeriggio stesso |
| DGS10, DGS2, DFII10 | giornaliera | 1 giorno | dati di mercato, H.15 il giorno dopo |
| VIXCLS | giornaliera | 1 giorno | chiusura USA 21:00 UTC; margine di un giorno |
| DTWEXBGS (dollaro ampio) | giornaliera, pubblicata a settimana | 8 giorni | H.10 il lunedì per la settimana prima |
| CPIAUCNS (CPI non destagionalizzato: la variazione annua non viene rivista) | mensile | dal giorno 25 del mese successivo | uscita di norma il 10–15; il 25 copre i ritardi noti (10/2025) |
| FOMC | date ufficiali | nota in anticipo | solo riunioni in calendario (quelle straordinarie non erano note prima) |
  M2SL: non usata nei modelli (mensile, rivista, lezione 96); solo citata. S&P 500 e VIX del repo
  (research/multi_asset/data): solo nella parte descrittiva. Limite dichiarato: senza ALFRED non si usano le annate
  originali; WALCL/WTREGEN/DFF/rendimenti/VIX non hanno revisioni rilevanti, il dollaro ampio sì ma minime.
  Se una serie non è scaricabile: dichiarato nel README, variabile = mancante (0 dopo la standardizzazione).

## 2. Regimi di mercato (2 definizioni, solo dati fino alla chiusura di t)
- **T (trend, 3 stati)**: SMA200 = media a 200 giorni. U (rialzo) se close > SMA200 e SMA200(t) > SMA200(t−30);
  D (ribasso) se close < SMA200 e SMA200(t) < SMA200(t−30); M (misto) altrimenti.
- **V (volatilità, 2 stati)**: vol30 = deviazione standard dei rendimenti log giornalieri su 30 giorni; A (alta) se
  vol30(t) > mediana di vol30 sui 365 giorni precedenti (t−365 … t−1), B (bassa) altrimenti.
Nessun'altra definizione; nessun parametro (200, 30, 365) verrà variato per il giudizio.

## 3. Variabili
- **Stabili del primo ciclo (4)**: pf, sf, rsi, vol, definite come in fc_data.features (flussi ritardati di 1 giorno).
- **Politica economica (8, fissate ora)**; tutte dopo il ritardo L di §1:
| # | Nome | Definizione |
|---|---|---|
| 1 | pol | DFF(t) − DFF(t−126 giorni), punti percentuali: direzione della politica (su/giù/fermo su ~6 mesi) |
| 2 | nl13 | variazione % a 91 giorni della liquidità netta = WALCL − WTREGEN − RRPONTSYD×1000 (milioni $) |
| 3 | dry | DFII10(t) − DFII10(t−63 giorni): variazione del rendimento reale a 10 anni |
| 4 | curva | DGS10 − DGS2 (livello, punti) |
| 5 | usd | variazione % a 63 giorni di DTWEXBGS |
| 6 | vix | ln(VIXCLS) |
| 7 | fomc | 1 se una riunione FOMC in calendario cade in (t, t+7], altrimenti 0 |
| 8 | cpi | segno (+1/0/−1) di [CPI annuo dell'ultimo mese pubblicato − CPI annuo del mese prima], arrotondati a 0,1 punti |
  Escluse per restare a 8 e non ripetere test: variazione della liquidità netta a 4 settimane (è H2 di n3: nulla a 30 giorni,
  instabile a 7), livello del rendimento reale (non stazionario: negativo nel 2020–21, positivo dal 2022, equivale a una
  variabile di periodo), variazione del VIX, M2. La finestra FOMC resta (in n3 era uno studio a eventi, qui è una covariata).
Standardizzazione sul solo addestramento, taglio ±3, mancante = 0 (fc_models.scaler/scale).

## 4. Modelli (3) e validazione
Tutti logistiche L2 (fc_models.fit_logit, intercetta libera), λ ∈ {1, 10, 100, 1.000, 10.000} scelto dentro l'addestramento
(ultimo 30%, embargo h) come nel primo ciclo; walk-forward espansivo dal 01/01/2015, riaddestramento il primo del mese,
entrano solo le righe con etichetta nota (embargo = h); previsioni dal 2018 (2018–20 = rodaggio per le soglie relative).
- **R (regimi + stabili)**: indicatori 1[U], 1[D] (intercetta per regime; M = riferimento), 1[A], pf, sf, rsi, vol,
  interazioni pf×1[U], pf×1[D]. 9 coefficienti.
- **P (politica)**: le 8 variabili di §3. 8 coefficienti.
- **RP**: R + P. 17 coefficienti.
- Ausiliari per la domanda "la politica aggiunge al flusso?": **PF** (solo pf) e **PF+P** (pf + 8 variabili di politica),
  stessa procedura.
- **Base rate condizionata** p0c(t): frequenza di rialzo nell'addestramento del mese (etichette note) fra i giorni nello
  stesso stato T di t (se < 60 giorni: frequenza complessiva). È il riferimento del Brier skill.
- **Soglia relativa** (al posto della fascia 45–55%): alla data t, con stato T = s, si confronta p(t) con le previsioni fuori
  campione dello stesso modello nei giorni precedenti (< t) con lo stesso stato s (minimo 180; altrimenti tutti gli stati):
  "su" se p(t) ≥ 67° percentile, "giù" se p(t) ≤ 33° percentile, altrimenti "incerto". Solo previsioni passate, nessun esito.
- Periodi di giudizio: 2021–23 e 2024–26 (fino al 15/11/2026 − h). 2018–20 solo informativo.
- Riferimenti sugli STESSI giorni delle chiamate: R1 sale sempre, R2 persistenza (segno del rendimento a h giorni passato),
  R3 lato della posizione W3.2 (fc_run.w32_regime; flat = nessuna previsione, confronto sui giorni comuni).
- Test: (a) sfasamento circolare degli esiti (sfasamenti fra 2h e N − 2h, passo 3) sull'AUC 2021–26, p unilaterale;
  (b) bootstrap a blocchi circolari (blocco max(30, 2h), 1.000 ricampionamenti) per gli intervalli di AUC, Brier skill e
  differenze; (c) accuratezza a blocchi non sovrapposti (una previsione ogni h giorni, media sulle fasi).
- **Holm su 16 test**: gli 8 p del primo ciclo (risultati.txt: 0,947 0,420 0,235 0,738 0,752 0,583 0,460 0,597) + 6 di questo
  (R, P, RP × 2 orizzonti, p dello sfasamento sull'AUC) + 2 (PF+P contro PF per orizzonte: quota di ricampionamenti a blocchi
  con ΔAUC ≤ 0 sul 2021–26).
- Potenza: osservazioni indipendenti ≈ 150 per periodo e 306 in totale a 7 giorni; ≈ 36 e 71 a 30 giorni. Errore standard
  dell'AUC sotto il caso ≈ 0,29/√n: AUC minima distinguibile da 0,50 (5% unilaterale, potenza 80%) ≈ 0,58 a 7 g sul totale
  (0,62 per periodo; 0,61 con Holm a 16) e ≈ 0,67 a 30 g sul totale (0,74 per periodo; 0,75 con Holm). Una AUC vera di
  0,55–0,60 a 30 giorni NON è dimostrabile con questi dati: lì l'esito migliore possibile è "non dimostrabile".

## 5. Soglia di successo (per orizzonte e per modello R, P, RP)
"FUNZIONA" se tutte: (a) AUC ≥ 0,55 sia in 2021–23 sia in 2024–26; (b) Brier skill rispetto a p0c > 0 in entrambi i periodi;
(c) direzioni corrette con soglia relativa superiori a R1, R2 e R3 sugli stessi giorni in entrambi i periodi, con copertura
≥ 25%; (d) p dello sfasamento sull'AUC 2021–26 < 0,05 dopo Holm sui 16 test. "NON DIMOSTRABILE" se (a), (b), (c) ma non (d).
Altrimenti "NON FUNZIONA". Il solo confronto con "sale sempre" non basta.
**La politica aggiunge al flusso?** Sì solo se ΔAUC (PF+P − PF) > 0 in entrambi i periodi e l'intervallo al 95% a blocchi sul
2021–26 esclude lo zero (e p di Holm < 0,05); altrimenti "non aggiunge" (o "non dimostrabile" se Δ > 0 in entrambi i periodi).
Nessuna scelta a posteriori di modello, soglia, regime o variabile; ogni deviazione dichiarata nel README.

## 6. Utilità per W3.2 (3 varianti; motore research/p2_nuovi/p2_engine.simulate; dal 01/01/2021, 10.000 $, 1x, costi)
Condizioni lette alla domenica del segnale (dati con i ritardi di §1):
| Variante | Regola |
|---|---|
| A · politica | nessun nuovo LONG se pol > 0 (tasso più alto di 6 mesi prima) e nl13 < 0 (liquidità netta in calo); short invariati |
| B · volatilità | esposizione all'ingresso × 0,5 se lo stato V è A (alta volatilità); il resto invariato |
| C · modello | ingresso bloccato se la chiamata relativa a 30 giorni di RP è contraria al lato del trade (long con "giù", short con "su") |
Criteri (tutti, come nel primo ciclo): CAGR/|DD| migliore di W3.2 in 2021–23, in 2024–26 e sull'intero periodo; DD giornaliero
≥ −30%; WR ≥ 70%; capitale finale ≥ W3.2 (per B, che riduce l'esposizione: MAR migliore e capitale finale riportato; conta
come "passa" solo con tutti i criteri); il vantaggio resta togliendo i 2 trade più favorevoli; placebo: MAR sopra il 95°
percentile di 200 sfasamenti circolari della serie-condizione. Vicini solo per chi passa. 2018–20 informativo.
Potenza: 13 trade, 1 perdente: esito atteso al più "non dimostrabile". Nessuna modifica a W3.2 senza il sì dell'utente.

## 7. Parte descrittiva ("studiale"), separata dalla previsione
Dal 01/01/2015 al 15/11/2026. Fasi di politica economica definite in modo meccanico e conoscibile in tempo reale:
tasso = RIALZO se pol > +0,125, TAGLIO se pol < −0,125, FERMO altrimenti; bilancio = ESPANSIONE (QE) se WALCL a 91 giorni
> +1%, RIDUZIONE (QT) se < −1%, STABILE altrimenti; più le fasi storiche con le date dei cambi di tasso lette da DFF
(rialzi 2015–18, pausa e tagli 2019, emergenza e QE 2020–21, rialzi 2022–23, plateau e QT, tagli dal 2024, fase attuale).
Per ogni fase e per ogni regime di mercato (T, V, T×V): giorni, numero di EPISODI indipendenti (tratti contigui), finestre
di 30 giorni non sovrapposte, rendimento medio e mediano a 30 giorni, frequenza di rialzo a 7 e 30 giorni, drawdown massimo
di BTC dentro la fase. È descrizione: nessuna soglia di successo, nessuna promozione; va dichiarato il numero di episodi.

## 8. Uscite
p2_fetch.py (scarico FRED e date FOMC), p2_data.py (regimi, variabili con ritardi), p2_run.py (walk-forward, metriche, test,
Holm), p2_descr.py (parte descrittiva), p2_w32.py (varianti), p2_oggi.py (stato e probabilità attuali con data/ del repo: solo
esempio), risultati*.txt, csv, README.md con verdetto, tabelle, deviazioni, lezione proposta (113), raccomandazione dashboard.
