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

## Variante B · tutte le pagine (`B/`)

Anteprima della variante scelta estesa a tutto il tool: `B/{oggi,posizioni,scanner,grafico,movimenti,notizie}.html`, solo tema
scuro, stessi dati del report pubblicato (riga `const R =` + `scanner.json`, `grafico.json`, `movimenti.json`, `news.json`).
Ogni pagina ha la barra inferiore (telefono) e la barra laterale (desktop ≥ 900 px) con le sei voci reali del tool.
Screenshot: `X_400_top.png` (prima schermata), `X_400.png` (pagina intera, dpr 2; la barra inferiore è riportata in fondo),
`X_1280.png`; `oggi_dettaglio_400.png` (foglio "Dettagli ›" di BTC aperto dal basso) e `oggi_dettaglio_1280.png` (pannello a destra,
Ciclo on-chain). Controllo automatico su tutte: nessuno scorrimento orizzontale a 400 px, nessun elemento fuori pagina, nessun errore JS.
Generatore: scratchpad `ux/gen/b2/` (base.py, p_*.py, build.py, shot.py).

### Regole comuni (linguaggio B)
- **Tessera = una cosa sola**, con **"Dettagli ›" in fondo a destra**, sempre nella stessa posizione (nelle tessere strette dei
  semafori è centrato). Apre un foglio: dal basso sul telefono, pannello a destra su desktop (anteprima: `<details>` + 3 righe di JS
  per "Chiudi"/Esc). Tutto ciò che non serve al primo sguardo sta lì, nulla è stato tolto.
- Etichette **minimo 12 px** (prima 10,5–12): intestazioni tessera 13, testi secondari 12,5–13, valori 15–30. Numeri tabulari.
- **Verde/rosso solo per profitto/perdita** (e per i semafori, che lo sono rispetto alla posizione). Il lato long/short è una
  pillola neutra con freccia (↓ short, ↑ long): prima il badge SHORT era rosso. Candele del grafico in grigio (piene = giù, vuote = su).
  Un solo accento (indaco) per link, interruttori, liquidazioni e "nel verso di BTC". Raggio 14 px ovunque.
- **Niente valori ripetuti nella stessa pagina** (fra pagine diverse sì: Oggi riassume, le altre approfondiscono).

### Oggi (cosa è cambiato rispetto a `oggi_B.html`)
- "Dettagli ›" su tutte le 14 tessere; la riga a tutta larghezza "Perché ogni semaforo" non c'è più: il perché di ciascuno è nel
  suo foglio (con la scala MVRV / DXY / OPEX), l'elenco completo nel foglio della tessera "mercato power".
- Etichette più grandi; conteggio dei semafori su tre colonne (numero sopra, parola sotto) perché "2 contro" andava a capo.
- Telefono: titolo della pagina nella barra in alto (logo + "Oggi" + orario), così la prima schermata mostra totale, semafori e
  tutta la tessera BTC. Foglio della tessera "totale": limiti storici BTC/ETH (dato che il tool ha in Movimenti).
- Desktop 1280: 1.172 px di altezza (prima 1.194), con la barra laterale del tool che prima mancava. Non sta in 900 px.

### Valori ripetuti eliminati, pagina per pagina
| Pagina | Oggi nel tool si ripete | In B resta solo |
|---|---|---|
| Posizioni | P&L e % (titolo, riga "sul capitale", pre-analisi); ingresso (riga, barra, "Quando esce"); trailing ed EMA 21 (barra, "Quando esce", pre-analisi, scenari); flusso e funding (Distribuzione e pre-analisi); prezzo (barra "Ora", OPEX "oggi") | P&L nel titolo; ingresso nella riga sotto; uscite in **$** solo sulla barra; livelli e margini % solo nei semafori delle uscite; flusso e funding solo nel semaforo "Distribuzione" (per questo nel Mercato power della pagina non c'è la tessera flusso: 5 semafori) |
| Scanner | BTC, ETH, SOL, TAO, TRX e i 5 ingressi nuovi sia nelle tessere sia nella tabella; numeri dello studio (12.386 $ contro 10.381 $) sotto gli ingressi e nelle scommesse; "ingresso lunedì all'apertura" su ogni riga | tabella "altre monete" (134) senza quelle già in evidenza o nuove; studio solo nella tessera scommesse; data d'ingresso una volta nel titolo della sezione |
| Grafico | ogni livello sia nella tabella "Tutti i livelli" sia nella legenda/interruttori; prezzo live nel titolo della tabella | ogni livello compare una volta, nella tessera del suo gruppo (interruttore + elenco); niente tabella separata |
| Movimenti | "14 chiuse + 1 aperta" nel sottotitolo della sezione e di nuovo nella tessera "Trade"; numero di trade anche nel titolo della lista | conteggio una volta nella mini-tessera "operazioni"; sottotitolo e lista senza conteggio |
| Notizie | orario delle fonti (riga in testa e orario della pagina); conteggi per tema e "Altre N" | orario solo nella testata; conteggio una volta per tema in alto a destra; il resto nel foglio |

### Le altre pagine in breve
- **Posizioni**: selettore BTC/ETH sul telefono (affiancate su desktop). In cima la **barra delle uscite in dollari**: a sinistra
  le uscite in perdita (trailing −4.718 $, EMA 21 −4.051 $), "ingresso" a 0, il punto "oggi". Sotto, **5 semafori delle uscite**:
  chiusura sopra EMA 21, trailing (verdi: oltre il 10% di margine), distribuzione (grigio, non attiva), utile bloccato da ~47.800,
  EMA 21 sotto l'ingresso (grigi: non ancora). Pre-analisi solo per BTC (come nel tool). **Mercato power della posizione** al posto
  delle schede on-chain/dollaro/OPEX impilate: on-chain, dollaro, OPEX, VIX, Fed; il contenuto delle vecchie schede è nei fogli.
  "Perché è aperta e quando si chiude" è il foglio della tessera in cima.
- **Scanner**: avviso "solo informativa", conteggi (barra impilata: short in indaco perché è il verso di BTC), uscite della
  settimana, In evidenza (BTC, ETH, TRX sulla carta, SOL e TAO preferite), ingressi della settimana, scommesse sulla carta, tabella
  con filtri e ricerca.
- **Grafico**: candele giornaliere vere (120 giorni) con i livelli accesi di default nel tool (resistenze, supporti, medie,
  liquidazioni, trailing, zone; Fibonacci e livello storico spenti), etichette a destra senza sovrapposizioni; 6 tessere-interruttore.
- **Movimenti**: reale contro modello (limiti BTC ed ETH come barre di consumo, registro vuoto), storico BTC/ETH con curva
  (solo BTC: `movimenti.json` non ha l'equity di ETH), anno per anno, 13 chiuse + 1 aperta, simulatore nel foglio.
- **Notizie**: prima della decisione di domenica (nessun dato ad alto impatto, poi FOMC 9/12), 5 temi con le 3 più rilevanti,
  altre notizie, il filtro in fondo (sul telefono).

### Decisioni aperte per l'utente
1. **Regole dei semafori** (Mercato power e uscite): sono una proposta dell'anteprima, non esistono nel codice.
2. **Scommesse sulla carta e TRX sulla carta** sono nel tool oggi e restano nell'anteprima; la regola "ciò che è solo testato non va
   nel tool" suggerirebbe di toglierle o spostarle: da decidere.
3. Candele grigie e lato long/short neutro (regola verde/rosso solo per profitto/perdita): confermare o tornare ai colori classici.
4. Tabella dello Scanner senza le monete già mostrate sopra (filtro "Altre" predefinito) o con tutte come oggi.
5. Desktop "in una schermata": Oggi è alto 1.172 px a 1280; per stare in 900 px servirebbe togliere contesto e notizie da Oggi.
