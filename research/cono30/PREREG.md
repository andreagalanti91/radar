# Preregistrazione · cono di probabilità a 30 giorni per BTC (volatilità, non direzione) · 23/11/2026

Scritta PRIMA di qualsiasi risultato: non è stato eseguito nessun calcolo di copertura, di tocco o di Brier. Va committata da sola.
Metodi, parametri, soglie e criterio non si cambiano dopo; un'idea nata dai risultati va in una nuova preregistrazione.

## 1. Domanda
L'utente chiede in dashboard "una previsione sui 30 giorni" (esempio suo: "BTC andrà a 50k, probabilità del 50%"). La DIREZIONE a
30 giorni non è prevedibile (lezioni 112, 113: due cicli, AUC ≈ 0,5). La volatilità invece è persistente. Domanda: un cono di
probabilità costruito solo dalla volatilità corrente (senza opinione sulla direzione) è CALIBRATO fuori campione? Cioè: gli
intervalli al 50% e all'80% contengono la chiusura a 30 giorni nel 50% e nell'80% dei casi, e le probabilità di "toccare un
livello entro 30 giorni" corrispondono alle frequenze osservate? Se sì, card "Fra 30 giorni" in dashboard; se no, niente card.

## 2. Dati
`research/p2_nuovi/data/f_long.csv.gz`: BTC giornaliero OHLC 01/01/2014 → 15/11/2026 (congelato). Solo open/high/low/close.
Giorni di previsione t: dal 01/01/2018 all'ultimo con 30 giorni successivi disponibili (16/10/2026). Periodi per data di
previsione: 2018–20, 2021–23, 2024–26. Walk-forward: per ogni t si usano solo righe con data ≤ t.

## 3. Definizioni comuni
- r_s = ln(C_s / C_{s−1}); u_s = ln(H_s / C_{s−1}); d_s = ln(L_s / C_{s−1}).
- **Volatilità corrente** σ_t (giornaliera), unica per tutti i metodi: σ_t² = ½ · media(r² ultimi 30 giorni) + ½ · media(r²
  ultimi 365 giorni), giorni fino a t compreso, media non centrata. Motivo fissato a priori: su un orizzonte di 30 giorni la
  volatilità rientra in parte verso il livello di lungo periodo; la sola realizzata a 30 giorni esagera negli estremi.
- Orizzonte H = 30 giorni di calendario (BTC è scambiato ogni giorno). Esito chiusura: C_{t+30}. Esito tocco: verso l'alto se
  max(H_{t+1..t+30}) ≥ C_t·(1+x); verso il basso se min(L_{t+1..t+30}) ≤ C_t·(1−x); x = 10%, 20%, 30% (6 eventi per giorno).
- Intervalli centrali: 50% = quantili 25–75%, 80% = quantili 10–90% della distribuzione prevista di C_{t+30}.

## 4. Metodi (3, solo numpy/pandas)
- **(a) Bootstrap a blocchi senza deriva.** Storia = tutti i giorni s ≤ t con σ_{s−1} definita (dal 2015). Terne standardizzate
  (r_s, u_s, d_s)/σ_{s−1}; alla componente r si toglie la propria media storica (stessa costante tolta a u e d). 2.000 cammini
  di 30 giorni = 3 blocchi contigui di 10 giorni estratti con reinserimento (inizio uniforme fra i blocchi interamente dentro
  la storia), riscalati per σ_t. Chiusura simulata = C_t·exp(Σ r); massimo/minimo simulati dai u, d giornalieri sul cammino.
- **(b) Bootstrap a blocchi con deriva storica.** Come (a), ma a ogni giorno simulato si aggiunge la media storica di r_s
  (tutti i giorni dal 2014 fino a t) invece di zero.
- **(c) Lognormale.** ln(C_{t+30}/C_t) ~ N(0, 30·σ_t²) (deriva logaritmica nulla). Quantili in forma chiusa; probabilità di
  tocco con il principio di riflessione: P = 2·(1 − Φ(|ln(1±x)| / (σ_t·√30))).
Seme 20261123 (generatore numpy `default_rng`, un flusso per tutta la corsa, stesso ordine dei giorni).

## 5. Misure
- **Copertura** degli intervalli 50% e 80% per periodo e sull'intero 2018–26, su tutti i giorni; errore standard binomiale con il
  numero di osservazioni NON sovrapposte (un giorno ogni 30, sfasamento 0); riportata anche la copertura sulle sole osservazioni
  non sovrapposte e la quota di esiti sotto/sopra l'intervallo.
- **Affidabilità del tocco**: per ogni metodo, le probabilità dei 6 eventi su tutti i giorni 2018–26 messe insieme e divise in
  decili di probabilità prevista; **errore di calibrazione medio** = media pesata (per numerosità) di |probabilità media prevista
  − frequenza osservata| nei 10 decili. Riportato anche per periodo e per livello (descrittivo).
- **Brier** dei 6 eventi (media) contro il riferimento "frequenza storica incondizionata": per ogni t e livello, la frequenza
  dell'evento su tutte le finestre di 30 giorni concluse entro t (dal 2014). Brier skill = 1 − Brier/Brier del riferimento, per
  periodo e totale; intervallo con bootstrap a blocchi di 60 giorni (1.000 ricampionamenti) sul totale.

## 6. Criterio (vincolante)
Un metodo è **calibrato** se, in CIASCUNO dei tre periodi, la copertura dell'intervallo 80% è fra 74% e 86% e quella del 50% fra
44% e 56% (su tutti i giorni del periodo), E l'errore di calibrazione medio del tocco (sezione 5, intero 2018–26) è ≤ 5 punti.
Fra i metodi calibrati si sceglie quello con il Brier medio più basso sull'intero 2018–26 (a parità entro 0,001: il più semplice,
c poi a poi b). **Se nessuno è calibrato: lo si dichiara e la card non si fa.** Nessun ritocco di σ, blocchi o soglie dopo i
risultati.

## 7. Limiti noti in anticipo
- ~36 osservazioni indipendenti per periodo: l'errore standard della copertura è ≈ 7–8 punti, più largo della fascia di ±6
  del criterio. Un metodo corretto può fallire per caso e uno sbagliato passare: il criterio resta quello, lo dichiaro.
- Code grasse e salti: la lognormale le ignora; il bootstrap le eredita dalla storia ma non prevede salti mai visti.
- Cambi di regime della volatilità dentro i 30 giorni (crolli, eventi) non sono previsti da nessun metodo: σ_t è fissata a t.
- Il tocco è misurato su massimi/minimi giornalieri di una sola fonte; spike di singole borse possono differire.
- Il cono non dice nulla sulla direzione: mediana ≈ prezzo attuale per (a) e (c). Nessun uso su W3.2.

## 8. Uso se un metodo passa
Modulo `radar/cone.py` (funzioni pure, seme fisso), `report["cone"]`, card "Fra 30 giorni" in Oggi (solo BTC: la calibrazione è
fatta su BTC), con la copertura reale dello studio scritta nella card e un registro `data/cone_log.csv` per misurare la copertura
dal vivo. Nessun effetto su W3.2, nessuna frase di direzione.
