# Scanner · "Monete in posizione" — due varianti (SOLO ANTEPRIMA, nulla applicato)

Richiesta: performance di ogni moneta in long/short con data di apertura, dettagli e il perché del verso.
Dati: report pubblicato del 27/11/2026 (riga `const R` di andreagalanti91.github.io/radar + scanner.json, grafico.json,
movimenti.json, news.json pubblicati), settimana chiusa il 22/11/2026: 55 monete in posizione (5 long, 50 short).
Render con `radar.dashboard.render` su una copia del template, Playwright chromium, deviceScaleFactor 2, rete esterna bloccata.

## Cosa hanno in comune
Un blocco nuovo `#scPos` sotto "Ingressi della settimana" (a tutta larghezza anche nel layout desktop A), prima di
"Scommesse sulla carta". Tabella completa, In evidenza, TRX e scommesse restano come sono.

- **Riepilogo**: 4 tessere (Long aperti + nuovi del lunedì e risultato medio; Short aperti idem; quante "con BTC";
  quante "non verificate") e la nota: "Lo scanner mostra lo stato di W3.2, non un segnale provato sulle altcoin
  (lezioni 111 e 123). Risultato = movimento del prezzo nel verso della posizione, senza commissioni, funding né dimensione."
  Oggi: long 3 aperti +13,9% medio (+2 nuovi), short 47 aperti +26,7% medio (+3 nuovi), 49/55 con BTC, 25 non verificati.
- **Per moneta**: data e prezzo d'ingresso, prezzo alla chiusura della domenica, risultato % colorato, giorni e
  chiusure settimanali in posizione, stop mobile con distanza con segno (short `+81,0%` = il prezzo deve salire),
  con/contro BTC, Bitget/OKX, rango. Storia breve -> avviso arancio "segnale non verificato: storia insufficiente"
  ("solo prezzo": "niente storia del flusso perp nello studio"; "nuova": "moneta senza scheda dello studio").
  Ingressi nuovi (segnale di domenica): "apre lun. 23/11", prezzo nel prossimo aggiornamento.
- **Perché è long/short**: una frase semplice + 5 semafori (verde = sostiene la posizione, arancio = non la sostiene ma
  non basta per uscire, rosso = porta all'uscita, grigio = dato assente): media lunga (40 settimane, distanza %),
  media veloce (EMA 21), flusso dei perpetual (chi compra/vende), funding/distribuzione, regime. Riga dello stop mobile
  e la precisazione "condizioni alla chiusura del 22/11, non quelle del giorno d'ingresso". Sotto, `Dettagli ›` con il
  dettaglio completo esistente (chip tecnici, MACD/F1, scheda dello studio, fonte dei dati).
- Filtro Tutte/Long/Short e ordine Risultato / Più recenti / Più grandi (capitalizzazione).
- Oggi lo scanner non pubblica il funding: il semaforo "Funding" è grigio ("non presente nei dati"); vedi sotto.

## Differenze
| | Variante 1 · righe | Variante 2 · tessere |
|---|---|---|
| Telefono | riga da 52 px: verso, ticker, "dal 09/11 · 18 g · con BTC", risultato grande, stop con segno | tessera: risultato grande, date e prezzi, mini-barra, 5 pallini, BTC e borse |
| Desktop 1280 | tabella a colonne (Moneta, Apertura, Chiusura, Risultato, Stop, BTC · operabile) | griglia 3 colonne; la tessera aperta va a tutta larghezza su 2 colonne |
| Mostrate subito | 15 (poi "Mostra tutte (55)") | 9 |
| Espansione | dati + mini-barra + perché, nella riga | "Perché è short ›" nella tessera |
| Mini-barra stop -> ingresso -> chiusura | solo nella riga aperta | sempre visibile |
| Densità | alta: 55 righe leggibili in uno scorrimento | più visiva, più lunga (9 tessere ≈ 3 schermate a 400 px) |

Mini-barra: a destra = a favore della posizione; trattino rosso = stop, cerchio vuoto = ingresso, pallino = chiusura.
Se lo stop ha già superato l'ingresso compare "stop oltre l'ingresso: guadagno protetto" (es. PI, JST).

Consiglio: **variante 1** per lo scopo dichiarato ("capire la posizione al primo sguardo" su 55 monete): ordinare e
scorrere è più rapido; la 2 è più piacevole ma su 55 monete diventa lunga sul telefono.

## Immagini (stato/ux-varianti/scanner/)
- pagina intera: `v1_400_dark.png`, `v1_400_light.png`, `v1_1280_dark.png`, `v1_1280_light.png`, idem `v2_*`
- blocco con la prima moneta aperta: `v1_dettagli_{400,1280}_{dark,light}.png`, `v2_dettagli_*`
- filtro Long, ingresso nuovo (SENT) aperto con `Dettagli` aperto: `v1long_dettagli_*`, `v2long_dettagli_*`
Verifiche: 0 errori JS (8 render), nessuno scorrimento orizzontale a 400 e 1280. A 360 px il blocco nuovo non sborda;
sborda la tabella esistente `table.scT` (anche sul template attuale, non toccata qui).

## Modifiche da applicare dopo la scelta
1. `radar/dashboard_template.html`: applicare `patch_variante1.diff` oppure `patch_variante2.diff` (diff unificato sul
   template di oggi; le due differiscono solo per `const VAR = 1|2`, il CSS è comune). Tre punti:
   - HTML: `<div id="scPos"></div>` dopo `<div id="scIng"></div>` in `#scSec`;
   - CSS: il blocco "Scanner · monete in posizione" prima di `</style>` (classi `pz*`, nessuna classe globale nuova);
   - JS: funzione `drawPos()` dentro `renderScanner()` subito dopo `drawIng();` (usa gli helper locali `dettaglio`,
     `oper`, `tag`, `tile`, `p5`, `dIt`, `cls`). Applicando, conviene togliere il ramo della variante non scelta.
   Sorgenti: `sorgenti/pos.js`, `sorgenti/pos.css`, `sorgenti/build.py` (genera le copie), `sorgenti/shot.py` (scatti).
2. `radar/scanner.py` (facoltativo ma consigliato, per il semaforo Funding): in `condizioni()` aggiungere
   ```python
   fu = wk["fund7"]
   ... "fund7": None if pd.isna(fu) else round(float(fu), 6),
       "dist": {"long": bool(wk["dist_long"]), "short": bool(wk["dist_short"])},
   ```
   (stesse formule di `weekly_bars`: soglie FUND_HOT 0,0009 e FUND_COLD −0,0003). La pagina usa `cond.dist` se c'è,
   altrimenti le soglie su `fund7`; senza i campi mostra il semaforo grigio. Monete OKX: funding solo da `fq`.
   Peso: ~40 byte per riga (~6 KB su 144). Test da aggiungere: `cond` contiene `fund7` e `dist` e `dist.long`
   coincide con `weekly_bars(...)["dist_long"].iloc[-1]`. Verificato in locale con valori finti: semaforo verde/rosso e
   testo "Funding medio 7 giorni −0,050% al giorno" corretti (immagine di prova non salvata qui).
   Nessun motivo testuale serve dallo scanner: la frase si costruisce dai campi `cond` già pubblicati.
3. Facoltativo: `ult` è la chiusura della domenica (scanner tagliato a `dom`); la pagina lo dice ("Chiusura 22/11").
   Un prezzo "di oggi" richiederebbe un campo nuovo (es. `ult_oggi`, `ult_d`) e cambierebbe il significato di `mv`:
   non proposto.
4. Dopo l'applicazione: test che riproduce (render con scanner.json di oggi -> `#scPos` con 55 righe/tessere), suite
   completa, render 400/1280 chiaro/scuro, deploy e verifica sul sito (regole di CLAUDE.md).
