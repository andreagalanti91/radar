# Vista "Oggi" · 3 varianti (solo tema scuro)

Dati veri del report pubblicato (riga `const R =` di https://andreagalanti91.github.io/radar/), chiusura **25/11/2026**,
aggiornamento **26/11/2026 17:48 UTC**. HTML statici e autonomi (nessuna dipendenza esterna, font Inter di sistema), dettagli
dietro "›" con `<details>` senza JavaScript. Ordine dei contenuti uguale in tutte: posizioni, 30 giorni, pre-analisi, Mercato power,
contesto e notizie.

Screenshot: `oggi_X_400.png` (pagina intera, 400 px, dpr 2), `oggi_X_400_top.png` (prima schermata), `oggi_X_1280.png`.

## A · Minimal neutro (`oggi_A.html`)
- **Idea**: stile Linear/Vercel. Superfici quasi nere, un solo accento (indaco del brand), molta aria; in testa un numero solo
  (+7.140 $ sulle due posizioni), poi card ordinate. Su desktop le sezioni vanno a coppie.
- **Pro**: è la più calma e leggibile; gerarchia netta; si adatta bene a telefono e desktop senza layout diversi.
- **Contro**: va scorsa parecchio (circa 7 schermate a 400 px). Mercato power e contesto si vedono solo in fondo.

## B · Cruscotto a tessere (`oggi_B.html`)
- **Idea**: tessere compatte su una griglia a 2 colonne (telefono) e 6 colonne (desktop). Semafori grandi con glifo + = −,
  conteggio di Mercato power già nella prima schermata, accanto al totale.
- **Pro**: su desktop sta tutto in una schermata; su telefono la prima schermata mostra totale, conteggio dei semafori e
  BTC con la sua barra. Ha l'unico grafico dello storico degli short simili.
- **Contro**: più densa: etichette piccole (10,5–12 px) e le frasi dei semafori sono dietro "›". Meno respiro, rischio di
  "muro di tessere" quando i dati crescono.

## C · Racconto in verticale (`oggi_C.html`)
- **Idea**: una colonna di 5 card grandi in ordine di lettura del mattino. Ognuna ha un titolo-frase, un grafico unico
  (barre di prezzo, cono, linea del tempo fino a domenica, bilancia dei semafori, barre macro a 20 giorni) e una frase.
- **Pro**: si capisce senza conoscere il tool: ogni card dice prima la conclusione ("Due short in utile", "restano aperte",
  "1 a favore · 3 neutri · 2 contro"). È la più vicina al "capire al primo sguardo".
- **Contro**: su desktop resta una colonna stretta (620 px) con molto vuoto ai lati. I numeri di dettaglio (margini delle
  condizioni, valori dei semafori) stanno dietro "›".

## Valori ripetuti oggi nel tool che le varianti eliminano
Nel tool attuale (template + report) questi valori compaiono più volte fra hero, riga posizione, card Posizione, "Quando esce",
pre-analisi, cono e contesto. Nelle varianti ognuno compare **una sola volta**:

| Valore (oggi) | Dove si ripete oggi | Dove resta nelle varianti |
|---|---|---|
| Prezzo BTC 60.458 | hero, riga posizione, card Posizione, cono, pre-analisi | solo sulla barra di BTC (A/B/C); niente hero col prezzo |
| Trailing 75.764 $ | card Posizione, frase "esce…", "Quando esce", pre-analisi (stop), livello "Trailing W3.2" del cono, livelli | solo nei dettagli "›" delle uscite; nel cono la linea si chiama "stop BTC" e mostra solo la probabilità (15%) |
| EMA 21 74.273 $ | frase "esce…", "Quando esce", pre-analisi (condizione e due scenari) | solo sulla barra (con −4.051 $); la pre-analisi mostra il margine (+22,9%), non il livello |
| Flusso −1,01σ e funding 7g | contesto del cono, condizioni e nota della pre-analisi, uscita per distribuzione | solo nel semaforo "Flusso e funding perp" (la pre-analisi rimanda lì) |
| P&L, ingresso, data d'ingresso | riga posizione, card Posizione, blocco posizione della pre-analisi | solo nella testata della posizione |
| VIX 26,4 e FOMC 09/12 | righe del Contesto ("Dati") e dettagli, macro | solo nei semafori VIX e Fed; il Contesto non li ripete |
| Stato di on-chain/dollaro/OPEX | titolo del box e frase con lo stesso concetto ("Dollaro in indebolimento" + "Divergenza ribassista sul dollaro") | un valore + una frase che aggiunge altro (es. "si indebolisce solo sotto 101,51") |

## Note per la scelta
- **Classificazione dei semafori: è una proposta mia per l'anteprima**, non esiste ancora nel codice. Rispetto allo short:
  on-chain in capitolazione = contro (rischio rimbalzo, dalla frase del tool); OPEX max pain 70.000 sopra il prezzo = contro (frase del
  tool); dollaro con divergenza non confermata ma ancora sopra le medie = neutro; VIX 26,4 fra le soglie 15/30 del tool = neutro;
  Fed (FOMC fra 13 giorni) = neutro; flusso in vendita e funding positivo (nessuna uscita per distribuzione) = a favore.
  Le regole vanno decise prima di rifare il tool.
- Il totale +7.140 $ (A, B, C) è la somma di BTC (+2.169 $) ed ETH (+4.971 $) su 30.000 $ ciascuno: oggi il tool non lo mostra.
- Colori: verde/rosso solo per profitto/perdita e per i semafori a favore/contro (che lo sono rispetto alla posizione); neutri in grigio.
