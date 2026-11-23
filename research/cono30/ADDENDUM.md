# Addendum · variante (d): deriva del cono condizionata al flusso perp · 23/11/2026 · ESPLORATIVO

Scritto e committato da solo PRIMA di eseguire la variante (d). **Esplorativo**: i risultati dei metodi base (a, b, c) sono già
stati visti (b è l'unico che passa il criterio della PREREG ed è il metodo base della card). Richiesta della regia dopo la
conferma dell'utente ("fai ciò che è prevedibile con afflussi, liquidazioni e altro"). Regole fissate qui, non ritoccabili dopo.

## Perché
Il flusso perp (pf14z) è l'unica variabile con un po' di ordine a 30 giorni nei nostri studi (AUC 0,56–0,58, p 0,09,
esplorativo: previsionale2). Domanda: usarlo per la deriva del cono migliora le probabilità di tocco senza rovinare la calibrazione?

## Dati
Flusso: colonna `pf14z` di `f_long.csv.gz` (valida dal 27/11/2017; identica a `f_repo.csv.gz` nei giorni comuni, ma con più
storia per la stima walk-forward: f_repo ha solo 264 giorni validi prima del 2021). Flusso disponibile al giorno t =
media del pf14z dei giorni t−3..t−1 (`radar.weekly.live_flow`: 3 giorni, ritardo reale di 1 giorno, almeno 2 valori).
Valutazione: previsioni dal 01/01/2021 al 16/10/2026, periodi 2021–23 e 2024–26.

## Varianti (2)
Stesso bootstrap del metodo (a) (rendimenti standardizzati centrati, stessa σ_t, blocchi di 10 giorni, 2.000 cammini) con
deriva giornaliera = media condizionata allo stato del flusso, stimata walk-forward: media di ln(C_{s+30}/C_s)/30 sui giorni s
passati (s+30 ≤ t, flusso definito) nello stesso stato di t. Se lo stato ha meno di 60 giorni passati o il flusso manca: deriva
storica del metodo (b).
- **d1 · segno**: 2 stati (flusso > 0, flusso ≤ 0).
- **d2 · segno e forza**: 3 stati (flusso > +0,5; |flusso| ≤ 0,5; flusso < −0,5).
Confronto con (b) ricalcolato con le STESSE estrazioni casuali (seme 20261123), stessi giorni.

## Criterio (vincolante)
Una variante si adotta nella card solo se, rispetto a (b):
1. il Brier medio dei 6 eventi di tocco è più basso SIA nel 2021–23 SIA nel 2024–26;
2. resta calibrata in entrambi i periodi: copertura 80% fra 74% e 86%, copertura 50% fra 44% e 56%, ed errore di calibrazione
   medio del tocco sul 2021–26 ≤ 5 punti.
Se passano entrambe: quella con il Brier 2021–26 più basso. Riportato anche (non vincolante): differenza di Brier 2021–26 con
intervallo al 95% a blocchi di 60 giorni; se comprende lo zero lo si scrive nel README e nella relazione.
**Se nessuna passa**: la card usa il metodo base (b) e mostra il flusso solo come riga descrittiva ("flusso perp: in vendita / in
acquisto"), senza effetto sulle probabilità.

## Liquidazioni
Non testabili (dati reali: 16 mesi su un mercato minore; lezioni 92, 93, 108): NON entrano nel calcolo. Nella card al massimo una
riga descrittiva con la fascia di liquidazione stimata più vicina già calcolata dal tool (radar/liqmap), marcata come stima.
