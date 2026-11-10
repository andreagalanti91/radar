# W2 + MACD · migliorie — PREREGISTRAZIONE (10/11/2026, scritta PRIMA dei risultati)

Obiettivo dell'utente: "rendere la strategia ancora più redditizia". Si adotta solo ciò che regge alla robustezza.
Visto prima di scrivere: solo la baseline (`radar.weekly.simulate`, 14 trade, 10k → 118.628 $, DD −22,7%) e l'elenco dei suoi
trade (motivi di uscita dei long: 5 distribuzione, 3 trailing, 2 EMA21). Nessun risultato delle varianti.
Nota: il mandato chiede ≤ 8 candidati; il coordinatore ha aggiunto M9. M6 e M7 sono controlli di stato di regole già
note (nessun parametro nuovo), quindi le regole NUOVE sono 7 (M1–M5, M8, M9).

## Motore, dati, costi
- `eng.py` = copia di `radar.weekly.simulate` con opzioni; a opzioni spente deve riprodurre ESATTAMENTE i trade e l'equity della
  baseline (assert in `run.py`), altrimenti il giro si ferma.
- Dati: `build_features(load_all())` dal 01/01/2021, 10.000 $, 1x, commissioni e slippage del tool (spot 0,1%/lato, perp 0,05%,
  slippage 0,1%, funding reale sulla parte perp). Extra: 2018–2020 con i proxy di `research/short_w2/short_lab.load_long`
  (Bitstamp/Binance, flusso = CVD spot z, funding 0).
- Metriche: capitale finale, rendimento, max DD giornaliero, trade, WR, MAR = CAGR/|DD|. Confronto con W2 com'è e con B&H.
- Split 2021–23 / 2024→oggi (10k da capo in ciascuno), senza il trade migliore, vicini, n. di trade cambiati rispetto alla
  baseline, confronto a pari DD (baseline con leva uniforme x tale che DD = DD della variante; lezione 41).

## Candidati (parametro principale fissato qui; i "vicini" servono solo alla robustezza)
- **M1 rendimento della liquidità**: da flat il capitale rende un tasso da T-bill/stablecoin. Logica: W2 è fuori mercato circa metà
  del tempo. Principale: **3,5%/anno fisso**, capitalizzato ogni giorno solo nei giorni senza posizione (né long né short). Vicini 3% e
  4%. Controllo prudente "tassi reali": 2021 0,05% · 2022 2,0% · 2023 5,0% · 2024 5,0% · 2025 4,2% · 2026 3,7% (T-bill 3 mesi,
  valori medi approssimati a memoria, dichiarati come ipotesi). Non cambia alcun trade: si giudica solo la materialità.
- **M2 uscita EMA21 meno nervosa**: (a) uscita solo dopo **2 chiusure settimanali consecutive** oltre la EMA21; (b) uscita solo se la
  chiusura è oltre la EMA21 di più di **0,5 ATRw**. Vale per long e short. Logica: l'uscita del 09/11/2026 è avvenuta a −4% appena
  sotto la EMA21; costo temuto: uscire più tardi nei veri cambi di trend. Vicini: 3 chiusure; margine 0,25 e 1,0 ATRw. Contro-prova
  "più veloce": (c) uscita alla prima chiusura GIORNALIERA sotto la EMA21 settimanale dell'ultima settimana chiusa.
- **M3 rientro dopo un'uscita EMA21**: (a) rientro rapido: nelle **6 settimane** dopo un'uscita EMA21 di un long, nuovo long con
  regime long + chiusura > EMA21 + F1, **senza** chiedere flusso > 0; (b) pausa: nessun nuovo ingresso nelle **2 settimane** dopo
  un'uscita EMA21. Vicini: 4 e 8 settimane; pausa 1 e 4. Logica: le false uscite sono seguite da ripartenze; il contrario se sono vere.
- **M4 runner**: quando la miglior chiusura giornaliera supera ingresso + **2R** (R = 2,5 ATRw del segnale) il trailing passa da 2,5 a
  **3,0 ATRw**; niente parziali; le altre uscite restano. Vicini: 3,5 e 4,0 ATRw; soglia 1R e 3R. Logica: lezione 82 (trailing largo
  dopo +2R raccoglie le code). Diverso da "trailing 3 ovunque" (già nella mappa, lezione 62) perché lo stop iniziale non si allarga.
- **M5 leva moderata solo nel regime migliore**: long a **1,3x** (1x spot + 0,3x perp con funding reale) se al segnale: trend giovane
  (età < 16 settimane sopra la SMA40) + flusso > 0 (già richiesto) + MACD(8,21,5) > linea di segnale; altrimenti 1x. Leva fissata
  all'ingresso. Vicino: 1,5x; varianti di definizione: solo "trend giovane"; solo "MACD in salita". Giudizio SOLO a pari DD contro
  la baseline con leva uniforme, e contro un placebo (stessa leva su un sottoinsieme casuale di long di pari numerosità, 2.000 prove).
- **M6 short D1 (controllo di stato)**: short W2 senza filtro di flusso (lezione 80, su carta dal 07/11). Si aggiorna la tabella e si
  conta se dal 07/11 ci sono trade nuovi rispetto a W2. Nessuna promozione possibile senza trade nuovi dal vivo.
- **M7 protezione "2018" (controllo di stato, lezione 62)**: con l'F1 attuale, quanto costa il 2018–2020 sui proxy; e R2 = nessun
  nuovo long se la chiusura è entro **1,5 ATRw** sotto il massimo delle chiusure settimanali delle ultime 52 settimane in un trend
  ≥ 16 settimane (nuovo test del top). Vicini 1,0 e 2,0 ATRw.
- **M8 giorno di chiusura della candela settimanale**: stesse regole con settimane che chiudono lun…sab (7 ancoraggi; esecuzione
  all'apertura del giorno dopo). Non è un candidato da adottare ma una prova: un vantaggio vero non dipende dal giorno. Si riporta
  la dispersione (min/mediana/max) e la posizione della domenica.
- **M9 trailing a cricchetto** (aggiunto dal coordinatore): lo stop può solo muoversi a favore: stop_t = max(stop_{t−1},
  best − 2,5·ATRw) per i long (min per gli short). Oggi può allentarsi quando l'ATR settimanale sale. Nessun parametro.

## Soglie (fissate ora)
**Adottare** solo se TUTTE: (1) cambia ≥ 3 trade rispetto alla baseline, oppure non ne cambia nessuno ed è contabile/gratuita (M1);
(2) MAR ≥ baseline in 2021–23 E in 2024→oggi; (3) 2018–20 non peggiore (rendimento ≥ baseline −5 punti e DD non peggiore di 3 punti);
(4) a pari DD capitale finale ≥ baseline +10%; (5) ≥ 2/3 dei vicini migliorano anch'essi il MAR; (6) senza il trade migliore
resta ≥ baseline senza il trade migliore; (7) per M5 placebo p < 0,10.
**Su carta**: passa (2) e (4) ma cade su (1), (3) o (5). **Respingere**: tutto il resto. M1: "materiale" se aggiunge ≥ 0,5 punti
di CAGR senza cambiare DD in peggio; è una nota operativa (dove tenere la liquidità), non una regola del segnale.
Nessuna soglia verrà spostata dopo aver visto i risultati; ogni analisi aggiunta dopo sarà marcata "post-hoc".
