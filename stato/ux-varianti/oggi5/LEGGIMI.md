# Vista Oggi: 5 varianti (anteprima, 26/11/2026)

Solo anteprima: nessun file di radar/, tests/, data/ è cambiato. Dati veri del report pubblicato del 26/11 19:20 UTC
(posizioni, uscite, cono a 30 giorni, livelli e probabilità di tocco, pre-analisi, R.mercato per i 6 semafori, notizie).
Studio e principi: `STUDIO.md`. Confronto: `ATTUALE_400.png` (vista Oggi del template attuale, chiaro) e
`ATTUALE_400_top_scuro.png`.

File per ogni variante: `V{n}.html` (autonomo, tema scuro; `?theme=light` per il chiaro), `V{n}_400_top.png` (prima
schermata, dpr 2), `V{n}_400.png` (pagina intera), `V{n}_1280.png`. V1 anche in chiaro: `V1_400_top_chiaro.png`,
`V1_400_chiaro.png`, `V1_1280_chiaro.png`.
Verifica: 360, 400 e 1280 px senza scorrimento orizzontale né testi tagliati (controllo automatico + lettura degli screenshot),
nessun errore JS, testi ≥ 13 px nel contenuto, righe e "Dettagli ›" alti almeno 44 px.

Contenuti uguali in tutte: posizioni (+7.140 $; BTC +2.169 $, ETH +4.971 $), quando escono in perdita/profitto e quanto vale,
intervallo a 30 giorni (52.100–74.800 $) con i livelli, pre-analisi di domenica 29/11 ("restano aperte", 4 short simili su 4
in utile), Mercato power (1 a favore · 3 neutri · 2 contro), notizie. Il Contesto non è più una scheda a sé: trend e
volatilità sono una riga del Mercato power; Fed, VIX e scadenza opzioni sono già tre dei suoi semafori.

## V1 · Attuale riordinata
- Idea: stessa grafica di oggi; cambiano ordine e gerarchia. Posizioni con il totale in grande, poi "Quando escono"
  (barra di uscita + righe "In perdita se / In profitto se" con il risultato in $), Livelli a 30 giorni, Pre-analisi,
  Mercato power come le schede on-chain/dollaro (stato in grande + striscia di 6 caselle + una riga), Notizie.
- In 5 secondi: "sono in utile di 7.140 $; BTC esce in perdita sopra 74.273 $ domenica o a 75.764 $".
- Pro: l'utente la riconosce subito; nessuna informazione ripetuta; le uscite finalmente in chiaro con i $.
- Contro: è la più lunga sul telefono (le uscite di BTC ed ETH occupano una schermata intera); niente di nuovo come lettura.

## V2 · Una domanda per scheda
- Idea: ogni scheda è una domanda in italiano con la risposta in una frase grande ("Bene: +7.140 $ in tutto", "Non prima di
  domenica 29/11, a meno che BTC salga del 25%", "Probabilmente fra 52.100 e 74.800 $", "Domenica restano aperte",
  "Non del tutto: 1 a favore, 2 contro"); sotto, i numeri e il grafico che la sostengono.
- In 5 secondi: le risposte, anche senza leggere i numeri.
- Pro: la più comprensibile per chi non conosce il tool; ottima al mattino; i testi si possono generare dalle regole.
- Contro: lunga quasi quanto V1; le frasi vanno scritte con cura per ogni stato (long, short, nessuna posizione, uscita in
  arrivo) e non devono sembrare consigli.

## V3 · Hero + dettagli
- Idea: una scheda grande in alto con la cosa più importante: utile totale, BTC/ETH affiancati, "Prossimo controllo:
  domenica 29/11", e per ogni asset il margine prima dell'uscita in perdita (+22,9% / +30,5%). Sotto, quattro schede compatte
  (30 giorni, pre-analisi, Mercato power, notizie), in griglia 2×2 su desktop.
- In 5 secondi: "+7.140 $, nulla succede prima di domenica, c'è un margine del 23%".
- Pro: tutto il necessario in una schermata di telefono; gerarchia netta; la più corta.
- Contro: le uscite in profitto sono solo in una frase; per i dettagli bisogna toccare (Posizioni).

## V4 · Grafico al centro
- Idea: un grafico del prezzo BTC (ultimi 45 giorni) con il cono a 30 giorni, l'ingresso, le due uscite in perdita e la soglia
  dell'utile bloccato come linee; etichette a destra senza sovrapposizioni; sotto, la legenda spiega ogni linea con il
  risultato in $. In alto tre pillole (BTC, ETH, totale); ETH ha la sua barra di uscita.
- In 5 secondi: "il prezzo è sceso lontano dall'ingresso; le uscite in perdita sono sopra il bordo del cono".
- Pro: rende evidente il legame fra uscite e probabilità; la più "da trader"; bella su desktop.
- Contro: ETH resta secondario; a 400 px il grafico è denso (6 etichette); chi non legge grafici deve passare dalla legenda.

## V5 · Lista operativa
- Idea: stile app bancaria (Revolut, Apple Stocks): totale in grande, poi gruppi di righe con icona, titolo breve, valore a
  destra e "›": Posizioni, Quando escono in perdita, Quando escono in profitto, Domenica (pre-analisi), BTC fra 30 giorni,
  Mercato (6 righe), Oggi.
- In 5 secondi: il totale e le righe rosse delle uscite con il loro valore.
- Pro: lettura a scansione, nessun grafico da interpretare; ogni riga è un tocco verso i dettagli; facile da mantenere.
- Contro: niente visualizzazione (si perde il "dove siamo" fra ingresso e uscite); molte righe simili; meno carattere.

## Raccomandazione
**V3 (Hero + dettagli) come base, con le frasi-risposta di V2 nell'hero e la barra di uscita di V1 nel dettaglio.**
Motivo: l'utente ha rifiutato B perché troppo denso e astratto; V3 dà in una sola schermata le sue prime due priorità
(come vanno e quando escono) con numeri grandi e una frase, e lascia il resto in schede compatte e riconoscibili (stessa
grafica di oggi). Se si preferisce cambiare il meno possibile, V1 è la scelta sicura. V4 è la migliore come pagina Grafico o
come scheda "30 giorni" espansa, non come prima vista: a 400 px chiede più attenzione di quanta ne serva al mattino.

Problemi aperti: il dettaglio Mercato power ("Dettagli ›") e i pannelli delle regole non sono disegnati qui; le frasi di V2/V3
vanno definite anche per long, nessuna posizione e uscita imminente; il cono di V4 tra oggi e il 25/12 è interpolato
(√tempo) dagli estremi 50%/80% del report, nel tool andrebbe usato il percorso giornaliero di radar/cone.py.
