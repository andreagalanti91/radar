# Prompt per la sessione Claude Code del repo `radar`

Incolla tutto il testo qui sotto nella sessione di radar e allega i file di questa cartella
(`livelli.py`, `oggi.json`, `rotture.csv`, `LIVELLI_BTC.md`, `anteprima_desktop.png`, `anteprima_telefono.png`,
`riferimento_pagina.html`, `btc_giornaliero.csv`).

---

Voglio portare nella dashboard di Radar una sezione **"Livelli"** dentro la vista **Oggi**: una mappa unica e chiara di
supporti, resistenze, medie, Fibonacci e liquidazioni di BTC rispetto al prezzo, con le zone dove più livelli coincidono.
È contesto per leggere il mercato e per decidere stop e dimensione, **non un segnale**: W3.2 non cambia.

## Da dove viene

L'ho sviluppata in un altro repo (`teststrategy`). Ti allego:

- `livelli.py`: modulo autonomo (solo pandas/numpy) che calcola i livelli da un giornaliero open/high/low/close. La funzione
  `build(d, liq_long, liq_short, liq_fonte, storici)` ritorna il dizionario da mostrare.
- `oggi.json`: l'uscita di `build` sui dati al 23/11/2026, come esempio dello schema (`prezzo`, `atr`, `livelli[]`, `zone[]`,
  `candele[]`).
- `anteprima_desktop.png` e `anteprima_telefono.png`: come appare oggi la sezione; `riferimento_pagina.html`: la pagina da cui
  è presa (funzione `oggi()` e stili collegati). Usa Chart.js: in Radar va rifatta con `lightweight-charts`, già caricato.
- `LIVELLI_BTC.md` e `rotture.csv`: lo studio che giustifica i testi (cosa succede quando un livello viene rotto).
- `btc_giornaliero.csv`: il giornaliero usato, per riprodurre `oggi.json` con `python livelli.py btc_giornaliero.csv`.

## Cosa deve mostrare

1. **Riepilogo in alto**: prezzo, primo supporto e prima resistenza con la distanza in %, prime liquidazioni di long (sotto)
   e di short (sopra), movimento medio giornaliero (ATR 14).
2. **Grafico** del prezzo dell'ultimo anno con una linea orizzontale per ogni livello, colore per tipo e prezzo a destra:
   supporto, resistenza, liquidazioni di long, liquidazioni di short, media mobile, Fibonacci, livello storico.
3. **Scala dei livelli**: tabella dal più alto al più basso con livello, distanza dal prezzo, tipo, descrizione e fonte; la
   riga del prezzo evidenziata nel punto giusto.
4. **Zone dove più livelli coincidono**: livelli consecutivi a meno del 3,2% l'uno dall'altro, almeno due; per ogni zona
   estremi, distanza, numero e tipi dei livelli, liquidazioni stimate nella zona.
5. **Nota fissa** sotto la sezione, con questo senso: i livelli descrivono il mercato ma non danno un segnale; dopo la
   rottura di un supporto (15 casi dal 2018) il prezzo è sceso ancora di circa l'11% nel punto peggiore dei 14 giorni
   successivi, più o meno quanto dopo un qualsiasi forte calo, e in 6 casi su 15 è rientrato sopra il livello entro 5 giorni.

## Come si calcolano i livelli

Le definizioni sono nel docstring di `livelli.py`; in breve:

- **Supporto / resistenza**: minimo / massimo di swing settimanale (estremo delle 5 settimane prima e dopo, noto 5 settimane
  dopo), attivo 3 anni e finché una chiusura giornaliera non lo rompe. In più il minimo delle ultime 5 settimane, segnato
  come "non ancora confermato".
- **Medie**: SMA 50 e 200 giorni, SMA 40 e 200 settimane.
- **Fibonacci**: 50%, 61,8%, 78,6% fra il minimo del ciclo (giugno 2022 – marzo 2023) e il massimo storico.
- **Livello storico**: il massimo del ciclo 2021 (69.000 $), già superato nel 2024: va mostrato come riferimento, **non** come
  resistenza attiva.
- **Liquidazioni**: `build` le riceve come liste `(prezzo, miliardi di $)`.

## Come integrarla in Radar

- **Dati di prezzo**: usa il giornaliero che Radar ha già (`data/spot.csv` tramite i caricatori esistenti), fino all'ultima
  chiusura giornaliera completa. Non aggiungere nuove fonti.
- **Liquidazioni**: usa prima di tutto quello che Radar già calcola: i cluster della mappa stimata (`radar/liqmap.py`,
  funzione `clusters`) e i livelli reali on-chain di Hyperliquid e Lighter (chiave `onchain`), con la fonte scritta nella
  riga. In più, prevedi un file facoltativo `data/coinglass_levels.json` che compilo a mano quando leggo la mappa di
  Coinglass (data e ora, lista di livelli long e short in miliardi): se c'è, quei livelli entrano con fonte "Coinglass, data".
  Niente scraping di Coinglass.
- **Supporti e resistenze esistenti**: Radar ha già `radar/levels.py` (zone con forza 1–5) e la card "Supporti e resistenze".
  Valuta tu se unire le due logiche o affiancarle; la mia richiesta è che in Oggi ci sia **una sola** mappa dei livelli, senza
  due elenchi che dicono cose diverse. Se le definizioni danno livelli diversi, dimmelo prima di scegliere.
- **Dove**: nuova card nella vista Oggi, sotto il grafico settimanale; dal telefono deve essere leggibile senza scorrimento
  orizzontale della pagina (la tabella può scorrere dentro il suo contenitore).
- **Codice**: metti il calcolo in un modulo di `radar/` con i suoi test, e l'uscita nel report del giro orario come le altre
  sezioni (con `_soft`, così un errore qui non ferma il giro).

## Vincoli

- Segui le regole del progetto: skill gengar, file `STATO-livelli.md`, test che riproduce il comportamento, suite verde,
  render a 400 e 1280 px con dati reali, deploy e verifica sul sito pubblicato.
- **W3.2 non si tocca**: nessuna modifica a `radar/weekly.py`, ai segnali o agli avvisi della strategia.
- Nessun avviso Telegram nuovo senza chiedermelo.
- I testi devono dire che è contesto e non un segnale, e che le liquidazioni sono stime (tranne quelle on-chain).
- Tema chiaro e scuro, stessi colori e componenti della dashboard.

## Come capisco che è fatto

1. `python -m pytest` verde, con un test che su `btc_giornaliero.csv` riproduce i supporti e le resistenze di `oggi.json`
   (38.555, 49.000, 55.130 non confermato, 57.800; 87.396, 97.924) e le zone.
2. Un test che verifica che un livello rotto in chiusura non compaia più fra quelli attivi, e che nessun livello usi dati
   successivi alla sua data di conferma.
3. Screenshot della card a 400 e 1280 px, tema chiaro e scuro, con dati reali.
4. La sezione è visibile sul sito pubblicato e si aggiorna a ogni giro.
5. Un riepilogo finale: cosa hai unito o lasciato separato rispetto a `radar/levels.py`, e quali fonti di liquidazione
   compaiono.
