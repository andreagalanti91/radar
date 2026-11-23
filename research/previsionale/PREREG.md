# PREREG · Modello previsionale direzionale di BTC a 7 e 30 giorni (23/11/2026)

Scritto e committato DA SOLO prima di calcolare qualsiasi prestazione. Prima di questo file sono stati guardati soltanto:
colonne e date di inizio dei dati congelati, coerenza f_repo/f_long (prezzi e pf14z identici dove coesistono), copertura di
data/macro.csv. Nessun modello è stato addestrato, nessuna accuratezza calcolata.

## 0. Domanda e cosa NON si ripete
Esiste una probabilità P(rendimento a h giorni > 0), h = 7 e 30, con direzionalità fuori campione, che migliori aggiornandosi
("impara dai propri errori") e che aiuti W3.2? Lezione 97: le probabilità condizionate A CELLE (3.521 celle, 0/5.790 dopo la
correzione) non hanno retto. Qui il disegno è diverso: nessuna ricerca fra celle, pochi modelli additivi con insieme di variabili
fissato prima, giudicati solo in walk-forward. Giro 9: i multivariati non aggiungevano a pf14z e non erano calibrati; lezione 96:
la macro non anticipa. L'attesa a priori è quindi bassa: il risultato negativo è un esito previsto e va scritto così.

## 1. Dati
- Congelati: research/p2_nuovi/data/f_long.csv.gz (prezzi 2014 → 15/11/2026; pf14z = proxy CVD spot dal 11/2017, perp reale dal
  04/2020) e f_repo.csv.gz (2019-09 → 15/11/2026: sf14z, funding_z, oi_chg7); fear&greed da data/fng.csv (dal 02/2018) tagliato
  al 15/11/2026. Solo BTC. Taglio: 15/11/2026.
- Macro (data/macro.csv): storia dal 12/2024 (oro) o 06/2025 (VIX, S&P, dollaro): insufficiente → ESCLUSA (lezione 96).
- Bersaglio: y_h(t) = 1 se close(t+h)/close(t) − 1 > 0, h ∈ {7, 30} giorni di calendario, previsione alla chiusura di t.
- Disponibilità: prezzi fino alla chiusura di t; flussi, funding e OI con ritardo reale di 1 giorno (valore di t−1, come
  radar.weekly.live_flow); fear&greed del giorno t (pubblicato la mattina di t).

## 2. Variabili (12, fissate ora)
| # | Nome | Definizione | Motivo |
|---|---|---|---|
| 1 | r7 | ln(C_t/C_{t−7}) | momentum settimanale / persistenza |
| 2 | r30 | ln(C_t/C_{t−30}) | momentum mensile |
| 3 | r90 | ln(C_t/C_{t−90}) | momentum di fondo (unico effetto robusto, lezione 96) |
| 4 | d50 | ln(C_t/SMA50) | distanza dalla media breve |
| 5 | d200 | ln(C_t/SMA200) | regime di lungo (≈ SMA40 settimanale di W3) |
| 6 | rsi | RSI14/100 − 0,5 | ipercomprato/ipervenduto |
| 7 | vol | ATR14/C | volatilità |
| 8 | pf | media 3 giorni di pf14z, ritardata 1 giorno (= live_flow di W3.2) | unico predittore OOS noto (giro 9) |
| 9 | sf | sf14z(t−1) | flusso spot |
| 10 | fz | funding_z(t−1) | costo del posizionamento |
| 11 | oi | oi_chg7(t−1) (dal 12/2021) | leva in ingresso/uscita |
| 12 | fng | fear&greed/100 − 0,5 | sentiment |
Standardizzazione con media e deviazione standard del solo addestramento, taglio a ±3; variabile mancante (storia più corta) =
0 dopo la standardizzazione (cioè la media): il coefficiente si impara solo dove il dato esiste. Nessun'altra variabile.

## 3. Modelli (3 + media), solo numpy/pandas
- **M1 LOGIT-P**: logistica L2 (IRLS, intercetta non penalizzata) sulle 7 variabili di prezzo (1–7).
- **M2 LOGIT-T**: logistica L2 su tutte le 12.
- **M3 CEPPI**: per ciascuna delle 12 variabili, terzili dell'addestramento, P(su | terzile) ristretta verso la frequenza base
  con k pseudo-osservazioni; combinazione: logit(p) = logit(base) + media_j [logit(p_j) − logit(base)] sulle variabili presenti.
- **M4 MEDIA** (modello PRIMARIO): media aritmetica di p1, p2, p3.
Iperparametri scelti SOLO dentro l'addestramento a ogni riaddestramento: λ ∈ {1, 10, 100, 1.000, 10.000} (penalità λ‖β‖² sulla
log-verosimiglianza sommata), k ∈ {20, 100, 500}; scelta = minima log-loss sull'ultimo 30% dell'addestramento, con modello
stimato sul primo 70% e embargo di h giorni; poi stima finale su tutto l'addestramento.

## 4. Validazione
- Walk-forward espansivo: addestramento dal 01/01/2015; riaddestramento il primo giorno di ogni mese D; entrano solo le righe t
  con t + h ≤ D − 1 (etichetta già nota: embargo = h); il modello vale per tutte le previsioni del mese.
- Giudizio (vincolante): **2021–23** e **2024–26** (previsioni dal 01/01/2021 al 15/11/2026 − h). Secondario, solo informativo:
  2018–20 (variabili 9–12 in gran parte assenti, pf = proxy spot).
- Fascia incerta: 45% ≤ p ≤ 55% = nessuna previsione. Fuori: p > 55% "su", p < 45% "giù".
- Metriche per periodo: % direzioni corrette fuori fascia, copertura, AUC (su tutte le p), Brier e Brier skill rispetto alla
  frequenza base dell'addestramento, calibrazione per decili di p.
- Riferimenti: (R1) sale sempre; (R2) persistenza = segno del rendimento degli ultimi h giorni; (R3) regime W3.2 = lato della
  posizione aperta di radar.weekly.simulate alla chiusura di t (long → su, short → giù, flat → nessuna previsione).
- Osservazioni indipendenti: le previsioni giornaliere a h giorni sono sovrapposte. Circa: h=7 → ~150 per periodo, ~306 in
  totale; h=30 → ~36 per periodo, ~71 in totale (meno, in proporzione alla copertura). Perciò: (a) significatività con
  permutazione per sfasamento circolare degli esiti rispetto alle previsioni (tutti gli sfasamenti fra 2h e N − 2h giorni:
  conserva l'autocorrelazione di entrambe le serie e la frequenza base); (b) intervalli con bootstrap a blocchi circolari
  (blocco = max(30, 2h) giorni, 2.000 ricampionamenti); (c) controllo a blocchi non sovrapposti: accuratezza campionando una
  previsione ogni h giorni, media sulle h fasi.
- Potenza (unilaterale 5%, potenza 80%; accuratezza minima distinguibile dal 50% ≈ 0,5 + 1,24/√n; con Holm su 8 test
  ≈ 0,5 + 1,67/√n): h=7, n≈306 → 57% (60% con Holm); per periodo n≈150 → 60%; h=30, n≈71 → 65% (70% con Holm); per periodo
  n≈36 → 71%. A 30 giorni un'accuratezza vera del 55–60% NON è distinguibile dal caso: lì l'esito migliore possibile è
  "non dimostrabile" salvo effetti molto grandi.

## 5. Soglia di successo (per orizzonte, sul modello primario M4; M1–M3 riportati)
"FUNZIONA" se tutte: (a) direzioni corrette fuori fascia ≥ 55% sia in 2021–23 sia in 2024–26; (b) copertura ≥ 25% in ciascun
periodo; (c) accuratezza superiore a R1, R2 e R3 (ciascuno sulla propria copertura) in entrambi i periodi; (d) p della
permutazione per sfasamento sull'intero 2021–26 < 0,05 dopo Holm sugli 8 test (2 orizzonti × 4 modelli); (e) AUC > 0,50 in
entrambi i periodi. "NON DIMOSTRABILE" se (a), (b) ed (e) sono vere ma (c) o (d) no. Altrimenti "NON FUNZIONA".
Nessuna scelta a posteriori di modello, soglia o variabili; ogni deviazione va dichiarata nel README.

## 6. "Imparare dai propri errori"
- (a) Il walk-forward mensile del punto 4.
- (b) Aggiornato contro statico: stesso modello addestrato UNA volta (dati con etichetta nota al 31/12/2020) e mai più
  aggiornato. Conta come "impara" se Brier e accuratezza sono migliori in entrambi i periodi e la differenza di Brier ha IC 95%
  (bootstrap a blocchi) che esclude lo zero sull'intero 2021–26.
- (c) Ricalibrazione sugli errori passati: Platt (logistica a 2 parametri su logit(p)) stimata a ogni riaddestramento sulle
  previsioni fuori campione già risolte; C1 = finestra espansiva, C2 = ultimi 730 giorni; minimo 365 giorni risolti, prima p
  resta invariata. Giudizio sulle date in cui la ricalibrazione è attiva: migliora se il Brier scende in entrambi i periodi e
  l'IC 95% della differenza esclude lo zero.
- (d) Registro delle previsioni: schema di data/forecast_log.csv e funzioni pure in research/previsionale/forecast_log.py
  (riga scritta con data e probabilità PRIMA dell'esito, mai riscritta; punteggio aggiunto a scadenza). Non si tocca radar/.

## 7. Utilità per W3.2 (motore research/p2_nuovi/p2_engine.simulate, che riproduce radar.weekly.simulate; nessuna modifica)
Probabilità usate: M4 in walk-forward, non ricalibrate, alla chiusura della domenica di decisione. "Concorda" = p fuori fascia
dal lato del trade (long: p > 55%; short: p < 45%); "discorda" = fuori fascia dal lato opposto; "concorda forte" = p ≥ 60%
(long) o ≤ 40% (short). Dal 01/01/2021, 10.000 $, 1x, costi del motore. 8 varianti:
| Variante | Regola |
|---|---|
| F7a / F30a | l'ingresso W3.2 è bloccato quella settimana se p7 / p30 discorda |
| F7b / F30b | ingresso solo se p7 / p30 concorda |
| D7 / D30 | esposizione all'ingresso = min(1, m × esposizione W3.2), m = 1,25 se p7 / p30 concorda forte, 0,75 se discorda, 1 altrimenti |
| U7 / U30 | uscita all'apertura del lunedì se p7 / p30 discorda per 2 domeniche consecutive a trade aperto; nessun rientro finché W3.2 non chiude quel trade |
Criteri (tutti): CAGR/|DD| migliore di W3.2 sia in 2021–23 sia in 2024–26 (tratti della stessa curva) e sull'intero periodo;
DD giornaliero ≥ −30%; WR ≥ 70%; capitale finale ≥ W3.2; il vantaggio resta togliendo i 2 trade che contribuiscono di più alla
differenza; placebo: MAR sopra il 95° percentile di 200 sfasamenti circolari della serie di probabilità. Vicini (soglie
50/60%, N = 1/3, m = 1,5/0,5) solo per le varianti che passano. Controllo 2018–20 informativo.
Potenza: 13 trade, 12 vincenti e 1 perdente (−4,1%). Un filtro può quasi solo togliere vincenti; il miglioramento massimo
possibile passa da 1–2 trade e quindi per costruzione difficilmente supera il criterio "non dipende da ≤ 2 trade". Esito atteso:
al più "non dimostrabile". Nessuna modifica a W3.2 senza il sì dell'utente.

## 8. Uscite
fc_data.py (dataset), fc_models.py (modelli), fc_run.py (walk-forward, metriche, test), fc_w32.py (W3.2), fc_oggi.py
(probabilità attuali con data/ del repo: solo esempio, non entra nel giudizio), forecast_log.py, risultati.txt, README.md.
