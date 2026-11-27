# Layout desktop · 2 varianti (solo anteprima)

Dati reali: il report pubblicato su https://andreagalanti91.github.io/radar/ (riga `const R =` più i file grafico/scanner/movimenti/news.json),
renderizzato con `radar.dashboard.render` sul template attuale (commit 2cbcdbd, Opzioni riattivata). Immagini a 1280 px, tema scuro,
risoluzione doppia. Le regole nuove valgono solo da 1100 px in su: su telefono e tablet la pagina resta identica
(confronto pixel per pixel a 400 px, chiaro e scuro, tutte le viste).

File: `attuale_*.png`, `A_*.png`, `B_*.png` (oggi, posizioni, movimenti; per A anche scanner e notizie).
Template: `dashboard_preview.html` (copia dell'attuale), `dashboard_preview_A.html`, `dashboard_preview_B.html`; regole in `css_A.css`,
`css_B.css`, piccola correzione JS di A in `js_A.py`.

## Cosa non va oggi a 1280 px
- Oggi: schede affiancate di altezza diversa. Vuoti di circa 390 px sotto "Come vanno le posizioni?", 230 px sotto "Cosa dice la
  pre-analisi?", 325 px sotto "Cosa succede oggi?".
- Posizioni: termometri di ciclo on-chain, dollaro e OPEX larghi al massimo 560 px, con mezza scheda vuota a destra.
- Movimenti: elenchi dei trade a tutta larghezza (data a sinistra, risultato a destra, 700 px vuoti nel mezzo).
- Scanner: "In evidenza" e "Ingressi della settimana" uno sotto l'altro pur avendo la stessa altezza. Notizie: il quinto gruppo
  resta solo, con mezza riga vuota accanto.

## A · Schede a tutta larghezza (griglia a 12 colonne)
Ogni scheda di Oggi occupa tutta la riga e dentro divide il contenuto in colonne: posizioni BTC | ETH | Opzioni; uscite BTC | ETH;
livelli sopra | sotto il prezzo; condizioni | short simili; semafori su due colonne; notizie affiancate.
Posizioni: i tre termometri di contesto in fila. Movimenti: storico e trade BTC | ETH affiancati (altezze simili).
Scanner: "In evidenza" | "Ingressi della settimana". Notizie: l'ultimo gruppo dispari a tutta larghezza.
- Pro: nessun vuoto fra le schede; ordine di lettura invariato (dall'alto in basso); grafici più larghi e più leggibili.
- Contro: Oggi resta lunga come adesso (circa 2.450 px contro 2.390), perché le schede sono una per riga. Nella riga Opzioni il testo va a capo
  su più righe. Nello Scanner la scheda TRX si allunga per pareggiare la colonna accanto.

## B · Due colonne lette dall'alto in basso
Oggi: colonna sinistra posizioni, uscite, 30 giorni; colonna destra pre-analisi, mercato, notizie. Le schede non sono più legate
in righe, quindi niente vuoti fra una scheda e l'altra. Posizioni: scheda BTC con prezzo e uscite a sinistra, contesto a destra.
Movimenti: ogni elenco dei trade su due colonne.
- Pro: Oggi più corta (circa 2.100 px contro 2.390), quasi tutto in due schermate; cambia solo il CSS.
- Contro: resta un vuoto in fondo alla colonna destra (circa 270 px su Oggi, 140 px nella scheda BTC); si legge prima tutta la
  colonna sinistra, poi la destra. Nello Scanner e nelle Notizie non cambia nulla.
