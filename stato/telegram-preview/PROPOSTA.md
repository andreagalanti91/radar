# Messaggi Telegram più chiari · proposta (solo anteprima)

Stato: **da approvare**. Nessun file di `radar/`, `tests/` o dei workflow è stato toccato; nessun messaggio inviato.

- Anteprime: `stato/telegram-preview/index.html` (attuale a sinistra, proposta a destra, tema scuro/chiaro, anteprima notifica).
- Immagini: `tutti_scuro.png`, `tutti_chiaro.png` (citazioni chiuse come in Telegram) e `NN_<stato>.png` (tema scuro, citazioni aperte).
- Codice di riferimento dei nuovi testi: `stato/telegram-preview/nuovo_formati.py` (funzioni con gli stessi argomenti di quelle di oggi).
- Dati: cache di `data/` (fino al 21/11/2026), W3.2 valutato davvero anche su date passate (dati troncati). Per questo l'EMA 21
  di BTC è $75.574 e non $74.273 (valore con i dati più recenti del sito). Valori «d'esempio» solo dove indicato nella pagina.

## 1. Inventario: 27 tipi di messaggio attivi (+1 alternativa proposta)

| n | Stato | Quando parte | Funzione |
|---|---|---|---|
| 01 | Nuovo segnale settimanale (entrata lunedì) | Domenica dopo la chiusura settimanale UTC, quando W3.2 dà un segnale (circa 2 volte l'anno per asset) | `weekly.format_event · w_signal (status segnale)` |
| 02 | Segnale arrivato a posizione già aperta | Raro: giri saltati durante il segnale, la posizione risulta già aperta senza annuncio | `weekly.format_event · w_signal (status aperto)` |
| 03 | Ingresso eseguito (prezzo reale) | Lunedì dopo l'apertura, al primo giro con la candela del lunedì | `weekly.format_event · w_entry` |
| 04 | Posizione in corso al primo avvio (non è un segnale nuovo) | Una sola volta, al primo giro di un asset nuovo (ETH il 22/11) con una posizione già aperta | `weekly.format_event · w_info` |
| 05 | Uscita automatica (trailing) aggiornata | A ogni giro, quando il livello migliora di almeno lo 0,5% del prezzo | `weekly.format_event · w_trail` |
| 06 | Anteprima: possibile uscita per distribuzione | A metà settimana, una volta per settimana, se la regola di distribuzione sarebbe attiva | `weekly.format_event · w_dist` |
| 07 | Uscita decisa: chiudi lunedì all'apertura | Domenica dopo la chiusura settimanale (media a 21 settimane o distribuzione) | `weekly.format_event · w_exit_next` |
| 08 | Uscita eseguita in perdita | Dopo l'uscita (lunedì all'apertura, o il giorno in cui scatta lo stop) | `weekly.format_event · w_exit` |
| 09 | Uscita eseguita in profitto | Come sopra, con risultato positivo | `weekly.format_event · w_exit` |
| 10 | Stop toccato in tempo reale | Ogni ora: se una candela oraria tocca lo stop (una sola volta per livello) | `weekly.format_intraday (da cli.weekly_alerts)` |
| 11 | Segnale ritirato (dati rivisti) | Raro: tra domenica e lunedì i dati definitivi non confermano più il segnale | `weekly.format_event · w_retract (signal)` |
| 12 | Uscita ritirata (dati rivisti) | Raro: l'uscita annunciata non è più confermata dai dati definitivi | `weekly.format_event · w_retract (exit)` |
| 13 | Stato degli avvisi ripristinato | Raro: data/state.json mancante o illeggibile con il radar già in funzione | `weekly.format_event · w_restore` |
| 14 | Riepilogo giornaliero «Oggi» (in posizione) | Una volta al giorno, al primo giro dopo la chiusura giornaliera (entro le 06:00 UTC) | `telegram.today_brief (da cli.daily_brief)` |
| 15 | Riepilogo giornaliero «Oggi» (nessuna posizione) | Come sopra, quando W3.2 è flat: indica le chiusure di domenica che darebbero un segnale | `telegram.today_brief` |
| 16 | Messaggio di salute quotidiano (tutto ok) | Una volta al giorno, al primo giro dopo le 07:00 UTC | `weekly.format_heartbeat (da cli.heartbeat)` |
| 17 | Messaggio di salute con problemi | Come sopra, se il giro ha avuto problemi | `weekly.format_heartbeat` |
| 18 | Alternativa: riepilogo e salute in un solo messaggio | Proposta: il riepilogo «Oggi» porta la riga di salute; il messaggio di salute separato parte solo se ci sono problemi | `telegram.today_brief + weekly.format_heartbeat` |
| 19 | Soglia d'allarme W3.2 (drawdown o stop consecutivi) | Una volta per evento: equity dal vivo −15% dal massimo o 2 stop consecutivi in perdita | `guard.format_alarm` |
| 20 | Controllo di coerenza dei dati | Una volta per evento: buchi nei dati, storico riscritto, decisione cambiata con i dati definitivi | `coherence.format_alert` |
| 21 | Fonte dati non disponibile | Al massimo una volta al giorno, se una fonte di W3.2 non si scarica (si usa l'ultima cache) | `cli.source_alerts` |
| 22 | Dati fermi da oltre 36 ore | Al massimo una volta al giorno | `cli.source_alerts` |
| 23 | Giro interrotto: nessun dato W3.2 | Se nessuna fonte di W3.2 ha dati né cache (giro fermato) | `cli.daily (testo in linea)` |
| 24 | W3.2 non calcolato | Una volta al giorno, se la valutazione di W3.2 va in errore | `cli.daily (testo in linea)` |
| 25 | Workflow: salvataggio (push) fallito | daily.yml, se il push dei dati fallisce 5 volte | `.github/workflows/daily.yml · «Avviso push fallito» (curl, testo semplice)` |
| 26 | Workflow: test falliti | daily.yml, se la suite di test fallisce (gli avvisi partono comunque) | `.github/workflows/daily.yml · «Avviso test falliti»` |
| 27 | Workflow: giro fallito | daily.yml e liqsnap.yml, se il job fallisce (daily: anche il secondo tentativo) | `daily.yml / liqsnap.yml · «Avviso workflow fallito»` |
| 28 | Test di connessione | Solo a mano: python -m radar.cli test-telegram | `cli.main · test-telegram` |

Messaggi presenti nel codice ma **spenti** (non ridisegnati, da decidere se eliminarli):
- v2 (`telegram.format_event`: signal, entry, dca_fill, tp/stop/time, expired; `intraday.format_events`): spenti dal 12/11/2026 (`RADAR_V2_ALERTS=0`).
- `telegram.daily_brief` (riepilogo v2): non più chiamato, sostituito da `today_brief`.
- Wallet (`wallets.py` sentinella, `scout.py`): in pausa dal 22/11/2026 (`RADAR_WALLETS=0`).
- Risposte ai comandi del registro (`journal.handle`: /entrato, /limit, /uscito, /registro, /aiuto; `xinbox`): sono risposte a un
  comando dell'utente, non avvisi; fuori da questa proposta.
- Opzioni su carta (`opzioni.py`) e Scanner: nessuna riga Telegram.

## 2. Regole del nuovo formato

1. **Riga 1 = cosa fare**, in grassetto, con un'icona di stato: è l'unica riga sicura nell'anteprima della notifica.
   Forma: `<icona> <b>ASSET · azione</b>` (es. «🔴 BTC · Nuovo SHORT: entra lunedì all'apertura», «📋 Oggi 25/11 · nessuna azione»).
2. **Icone fisse**: 🟢 long · 🔴 short · ⚪ fuori/annullato · 🎯 profitto · 🛑 perdita o stop · 🔔 uscita automatica spostata ·
   ⏳ decisione in sospeso · ⚠️ problema tecnico · 📋 riepilogo · ✅ tutto ok. Al massimo un'icona per riga.
3. **3–6 righe di numeri**, una informazione per riga, sempre nello stesso ordine: entrata → importo → prezzo ora e risultato
   (% sul capitale e $) → uscita in perdita / uscita automatica (e cosa succede se scatta).
4. **Dettagli** (perché, mercato, regole d'uscita, note storiche) in `<blockquote expandable>`: Telegram li mostra chiusi su 3 righe.
5. **Link** «Apri la dashboard» in fondo ai messaggi di trading (anteprima link già disattivata da `send`).
6. **Niente gergo in vista**: trailing → «uscita automatica (si sposta solo a tuo favore)»; EMA 21 → «media a 21 settimane»;
   flusso perp → «flusso dei futures»; ATR e σ solo nei dettagli. «RADAR SIGNAL» e «W3.2» tolti dalla riga 1 (il nome del bot
   è già nella notifica).
7. **Formati unici**: date `lun 16/11`, numeri all'italiana (`0,97x`, `+7,50%`, `−$4.745` con segno meno vero), un solo
   risultato principale (% sul capitale + $), la % sul prezzo resta come dato secondario.
8. **Righe corte** (≤ ~40 caratteri dove possibile) per non andare a capo sul telefono.
9. Contenuti invariati: entrata, importo e quantità, capitale, stop iniziale e perdita stimata, uscita automatica, soglia della
   media a 21 settimane, regola di distribuzione, conferme «ti confermo il prezzo eseguito». Aggiunto solo l'esito in $ se scatta
   l'uscita automatica, che il codice calcola già per la dashboard (`cur["uscite"]["trail"]`).

## 3. Messaggi oggi confusi o doppi, e cosa propongo

- **Due notifiche al giorno sullo stesso stato**: riepilogo «Oggi» (00–06 UTC) e messaggio di salute (dopo le 07 UTC) ripetono
  posizione e stop. Proposta (n. 18): una riga «✅ Sistema ok · dati fino al … · decisione dom …» in fondo al riepilogo; il messaggio
  di salute separato parte solo se ci sono problemi.
- **Messaggio di salute illeggibile**: una sola riga lunga, date ISO, «W3.2 short aperto, stop $75.764, ETH …». Proposta: 3 righe.
- **Tre avvisi sovrapposti sui problemi delle fonti**: «Fonte non disponibile», «Dati vecchi» e la salute «attenzione: …» dicono la
  stessa cosa lo stesso giorno. Proposta: tenerli ma con riga 1 «⚠️ Problema tecnico: …»; in alternativa accorparli nella salute.
- **Avvisi tecnici intestati sempre «BTC»** anche quando la fonte è di ETH (`eth_funding`): nella proposta «ETH funding».
- **Due percentuali** («+7,77% sul prezzo», «+7,50% sul capitale dedicato») senza dire quale conta: in vista solo quella sul capitale con i $.
- **Stop toccato**: «stop comunicato / del modello» è difficile da capire; la proposta mette solo il livello e l'azione, la spiegazione nei dettagli.
- **«Stop/trailing $75.764 (+25,8%)»** nel riepilogo: il +25,8% (distanza dal prezzo) sembra un guadagno. Proposta: «uscita $75.764».
- **Workflow** (push, test, giro fallito): testo semplice con URL nudo, prefisso diverso («Radar ·»). Proposta: stesso formato, link «Dettagli del giro».
- **Segnale nuovo**: 10 righe, il piano operativo è a metà messaggio. Proposta: 6 righe in vista, il resto nei dettagli.

## 5. Cosa cambierebbe nel codice (non fatto)

| File | Funzione | Modifica |
|---|---|---|
| `radar/weekly.py` | `format_event`, `format_intraday`, `format_heartbeat`, `_exits_text`, `_mkt`, `_state_word` | corpi sostituiti con quelli di `nuovo_formati.py`; `format_intraday` riceve anche `cur` (esito in $) da `cli.weekly_alerts` |
| `radar/telegram.py` | `today_brief`, `_w3_lines`, `_asset_line` (+ helper `head`, `details`, `foot`, `money`) | nuovo riepilogo; contesto e mercati in blockquote; parametro `health` se si accorpa la salute |
| `radar/cli.py` | `source_alerts`, `daily` (testi in linea «giro interrotto», «W3.2 non calcolato»), `heartbeat`, `daily_brief`, `test-telegram` | testi nuovi; con l'accorpamento: `daily_brief` passa la riga di salute e `heartbeat` invia solo se `problems` |
| `radar/guard.py` | `format_alarm` | testo nuovo |
| `radar/coherence.py` | `format_alert` | testo nuovo |
| `.github/workflows/daily.yml`, `liqsnap.yml` | passi «Avviso …» | testo HTML + `--data-urlencode "parse_mode=HTML"` |

Logica, eventi, dedupe e marcature dello stato non cambiano: cambia solo il testo. Test da aggiornare (asserzioni sul testo):
`tests/test_weekly.py`, `tests/test_alerts.py`, `tests/test_eth.py`, `tests/test_uscite.py`, `tests/test_preview_today.py`,
`tests/test_brief_taker.py`, `tests/test_macro.py` (riga Mercati), `tests/test_guard.py`, `tests/test_coherence.py`,
`tests/test_workflows.py`, `tests/test_live.py` (da verificare con `grep` su «RADAR SIGNAL», «trailing», «Stop/trailing»).
Nuovi test: riga 1 di ogni tipo (icona + azione), nessun tag fuori dalla lista di Telegram, blockquote bilanciati, lunghezza < 4096.
Prima del deploy: invio di prova di ciascun tipo con `test-telegram` sulla chat (dopo l'approvazione) per vedere la resa reale.

## 6. Scelte per l'utente

1. Togliere «RADAR SIGNAL» e «W3.2» dalla riga 1? (proposta: sì, il bot ha già il nome nella notifica)
2. Accorpare salute e riepilogo in un messaggio solo (n. 18)? (proposta: sì; salute separata solo con problemi)
3. Dettagli in citazione espandibile (chiusa su 3 righe)? Le app Telegram vecchie la mostrano aperta.
4. Numeri come righe «etichetta: valore» (proposta) oppure tabellina monospazio `<pre>` allineata (più tecnica, con tasto «Copia»)?
5. Link alla dashboard in ogni messaggio di trading o solo nel riepilogo?
6. Mostrare l'esito in $ «se scatta l'uscita automatica» (nuovo dato in vista, già calcolato per la dashboard)?
7. Avvisi sulle fonti: tenerli separati (proposta) o solo dentro il messaggio di salute?
8. Eliminare dal codice i messaggi spenti di v2 e `telegram.daily_brief`?

## 4. Testi nuovi completi (HTML Telegram, copiabili)
Generati da `nuovo_formati.py` sui dati indicati. Gli invii da workflow (24–26) richiedono `parse_mode=HTML` nel curl.

### 01 · Nuovo segnale settimanale (entrata lunedì)

```html
🔴 <b>BTC · Nuovo SHORT: entra lunedì all'apertura</b>
Entrata: ~<b>$65.351</b> a mercato, lun 16/11
Importo: $29.153 = 0,4461 BTC su $30.000
🛑 Uscita in perdita: $82.163 (circa −$7.558)
🎯 Profitto: l'uscita segue il prezzo
Lunedì ti confermo il prezzo eseguito.
<blockquote expandable><b>Stop iniziale</b> $82.163 = +25,7% dal prezzo; perdita stimata allo stop ~$7.558 (costi inclusi).
<b>Perché</b>: chiusura settimanale del 15/11 a $65.351, tendenza ribassista, flusso dei futures −0,93σ.
<b>Mercato</b>: perp, margine isolato, esposizione 0,97x del capitale.
<b>Come si esce</b> (alla prima delle tre): uscita automatica a $16.812 dalla miglior chiusura giornaliera, si sposta solo a tuo favore e ti avviso a ogni passo; chiusura settimanale sopra la media a 21 settimane ($75.574); distribuzione (funding medio 7 giorni &lt; −0,03%/giorno con flusso dei futures positivo).
Uscita automatica = 2,5 volte la volatilità media settimanale (ATR) dalla miglior chiusura.
Operazioni rare (13 dal 2021, circa 2 l'anno) e lunghe · calo massimo storico −21% · al massimo il 25% del capitale a rischio allo stop iniziale.</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 02 · Segnale arrivato a posizione già aperta

```html
🔴 <b>BTC · SHORT già aperto dal 16/11 (segnale in ritardo)</b>
Entrata lun 16/11 a <b>$65.286</b> · ora $60.216
Risultato: <b>+7,50%</b> (+$2.250)
🛑 Uscita automatica: <b>$75.764</b>
Media a 21 settimane: $75.574
<blockquote expandable>Segnale del 15/11: i giri precedenti non l'avevano comunicato. Se entri ora, entri a un prezzo diverso.
<b>Mercato</b>: perp, margine isolato, esposizione 0,97x del capitale.
<b>Come si esce</b> (alla prima delle tre): uscita automatica (si sposta solo a tuo favore); chiusura settimanale sopra la media a 21 settimane; distribuzione (funding medio 7 giorni &lt; −0,03%/giorno con flusso dei futures positivo).</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 03 · Ingresso eseguito (prezzo reale)

```html
🔴 <b>BTC · SHORT aperto a $65.286</b>
Entrata lun 16/11 all'apertura (segnale del 15/11)
Importo: $29.160 = 0,4467 BTC su $30.000
Prezzo ora: $64.883 · <b>+0,56%</b> (+$168)
🛑 Uscita automatica: <b>$81.695</b>
<blockquote expandable>Stop iniziale $82.163. <b>Mercato</b>: perp, margine isolato, esposizione 0,97x del capitale.</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 04 · Posizione in corso al primo avvio (non è un segnale nuovo)

```html
🔴 <b>ETH · SHORT in corso dal 09/11: non è un segnale nuovo</b>
Da oggi il radar segue anche ETH.
Entrata lun 09/11 a <b>$2.125</b> · ora $1.686
Risultato: <b>+16,74%</b> (+$5.022) · +20,69% sul prezzo
Importo: $24.390 = 11,4759 ETH su $30.000
🛑 Uscita automatica: <b>$2.311</b>
Media a 21 settimane: $2.258
<blockquote expandable>Se decidi di seguirla ora, entri a un prezzo diverso.
<b>Mercato</b>: perp, margine isolato, esposizione 0,81x del capitale.
<b>Come si esce</b> (alla prima delle tre): uscita automatica (si sposta solo a tuo favore); chiusura settimanale sopra la media a 21 settimane; distribuzione (funding medio 7 giorni &lt; −0,03%/giorno con flusso dei futures positivo).</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 05 · Uscita automatica (trailing) aggiornata

```html
🔔 <b>BTC · Uscita automatica abbassata a $75.764</b>
Era $78.799 · si sposta solo a tuo favore
SHORT da $65.286 · ora $58.952 · <b>+9,39%</b> (+$2.817)
🛑 Se scatta: <b>−15,81%</b> (−$4.743)
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 06 · Anteprima: possibile uscita per distribuzione

```html
⏳ <b>BTC · Possibile uscita dallo SHORT: decide domenica</b>
Se la settimana chiudesse oggi si uscirebbe lunedì per distribuzione.
Funding medio 7g −0,0410%/giorno · flusso futures +0,38σ
<b>Nessuna azione ora</b>: decide la chiusura di dom 22/11 (UTC).
🛑 Uscita automatica: $75.764
<blockquote expandable>Distribuzione = funding e flusso dei futures contrari alla posizione: funding medio 7g sotto −0,03%/giorno con flusso positivo.</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 07 · Uscita decisa: chiudi lunedì all'apertura

```html
🛑 <b>BTC · Chiudi il LONG lunedì all'apertura</b>
Motivo: settimana chiusa sotto la media a 21 settimane (dom 08/11)
Entrata 24/08 a $77.812 · ora $74.851
Risultato stimato: <b>−3,90%</b> (−$1.170)
Lunedì ti confermo prezzo eseguito e risultato.
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 08 · Uscita eseguita in perdita

```html
🛑 <b>BTC · LONG chiuso in perdita: −4,10%</b>
Uscita lun 09/11 a <b>$74.777</b> · settimana chiusa sotto la media a 21 settimane
Entrata lun 24/08 a $77.812 · −3,90% sul prezzo
Risultato: <b>−4,10%</b> (−$1.230) del capitale
Ora nessuna posizione: si attende il prossimo segnale.
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 09 · Uscita eseguita in profitto

```html
🎯 <b>BTC · SHORT chiuso in profitto: +5,73%</b>
Uscita gio 20/08 a <b>$73.287</b> · uscita automatica
Entrata lun 25/05 a $76.988 · +4,81% sul prezzo
Risultato: <b>+5,73%</b> (+$1.719) del capitale
Ora nessuna posizione: si attende il prossimo segnale.
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 10 · Stop toccato in tempo reale

```html
🛑 <b>BTC · Stop toccato: chiudi lo SHORT</b>
Livello <b>$75.764</b> · prezzo ora $75.912 (14:07 UTC)
Risultato a questo livello: <b>−15,82%</b> (−$4.745)
<blockquote expandable>Lo stop scatta al tocco. L'uscita ufficiale si registra alla chiusura giornaliera.</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 11 · Segnale ritirato (dati rivisti)

```html
⚪ <b>BTC · Segnale SHORT annullato: non entrare</b>
Il segnale del 15/11 non è più valido dopo l'aggiornamento dei dati:
<i>regime settimanale ora neutro; flusso perp ora +0.12σ</i>
<b>Se sei già entrato, valuta di chiudere.</b>
Stato attuale: nessuna posizione.
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 12 · Uscita ritirata (dati rivisti)

```html
🔴 <b>BTC · Uscita annullata: tieni lo SHORT</b>
L'uscita annunciata per lunedì non è più valida:
<i>la posizione resta aperta: la chiusura settimanale non conferma più l'uscita</i>
🛑 Uscita automatica: $75.764 · media 21 sett. $75.574
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 13 · Stato degli avvisi ripristinato

```html
⚠️ <b>BTC · Avvisi ripristinati: nessuna azione</b>
Lo stato degli avvisi mancava: ricostruito dalla simulazione.
🔴 SHORT dal 16/11 a $65.286 · <b>+7,50%</b> (+$2.250)
🛑 Uscita automatica: $75.764 · media 21 sett. $75.574
<blockquote expandable>Ultima chiusa: long dal 24/08 a $77.812, uscita 09/11 a $74.777 (settimana chiusa sotto la media a 21 settimane), −4,10% sul capitale.
Dati fino al 21/11. Ingressi e uscite degli ultimi 7 giorni seguono in messaggi separati.</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 14 · Riepilogo giornaliero «Oggi» (in posizione)

```html
📋 <b>Oggi 25/11 · nessuna azione</b>
🔴 <b>BTC short</b> · <b>+7,50%</b> (+$2.250)
da $65.286 (16/11) · ora $60.216
uscita $75.764 · o domenica sopra $75.574
🔴 <b>ETH short</b> · <b>+16,74%</b> (+$5.022)
da $2.125 (09/11) · ora $1.686
uscita $2.311
<blockquote expandable>Flussi: perp −1,41σ (in vendita) · spot −0,90σ (in vendita)
Derivati: funding −0,04%/anno · OI 7g −6,7% · liquidazioni 24h long 0,0 M$ / short 0,0 M$
Storico simile (pf14z basso · sf14z basso, 70 casi): 50% di rialzo a 7 g, 45% a 30 g · non significativo
Mercati: S&P 7.201 (−0,5%) · Nasdaq 23.734 (−1,5%) · oro 3.542 (−2,1%) · dollaro 123,6 (+0,1%) · VIX 26,4 (−0,3)
Da rivedere: S&P 500 sotto la media a 200 giorni
Prezzi alla chiusura del 21/11. Contesto, non segnale: decide W3.2.</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 15 · Riepilogo giornaliero «Oggi» (nessuna posizione)

```html
📋 <b>Oggi 14/11 · fuori dal mercato, nessuna azione</b>
⚪ <b>BTC</b>: nessuna posizione · $64.150
Dom 15/11: short se chiude sotto $72.334
<blockquote expandable>Flussi: perp −1,28σ (in vendita) · spot +0,39σ (quasi neutro)
Derivati: funding 5,9%/anno · OI 7g +2,2% · liquidazioni 24h long 0,0 M$ / short 0,0 M$
Storico simile (pf14z basso · sf14z medio, 50 casi): 52% di rialzo a 7 g, 36% a 30 g · non significativo
Mercati: S&P 7.201 (−0,5%) · Nasdaq 23.734 (−1,5%) · oro 3.542 (−2,1%) · dollaro 123,6 (+0,1%) · VIX 26,4 (−0,3)
Da rivedere: S&P 500 sotto la media a 200 giorni
Prezzi alla chiusura del 14/11. Contesto, non segnale: decide W3.2.</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 16 · Messaggio di salute quotidiano (tutto ok)

```html
✅ <b>Radar attivo · tutto ok</b>
Dati fino al 21/11 · ultimo giro 25/11 07:10 UTC
🔴 BTC short · 🔴 ETH short · prossima decisione dom 29/11
```

### 17 · Messaggio di salute con problemi

```html
⚠️ <b>Radar · 2 problemi tecnici</b>
• fonte metrics non disponibile
• dati funding vecchi
Dati fino al 21/11 · ultimo giro 25/11 07:10 UTC
🔴 BTC short · 🔴 ETH short · prossima decisione dom 29/11
```

### 18 · Alternativa: riepilogo e salute in un solo messaggio

```html
📋 <b>Oggi 25/11 · nessuna azione</b>
🔴 <b>BTC short</b> · <b>+7,50%</b> (+$2.250)
da $65.286 (16/11) · ora $60.216
uscita $75.764 · o domenica sopra $75.574
🔴 <b>ETH short</b> · <b>+16,74%</b> (+$5.022)
da $2.125 (09/11) · ora $1.686
uscita $2.311
<blockquote expandable>Flussi: perp −1,41σ (in vendita) · spot −0,90σ (in vendita)
Derivati: funding −0,04%/anno · OI 7g −6,7% · liquidazioni 24h long 0,0 M$ / short 0,0 M$
Storico simile (pf14z basso · sf14z basso, 70 casi): 50% di rialzo a 7 g, 45% a 30 g · non significativo
Mercati: S&P 7.201 (−0,5%) · Nasdaq 23.734 (−1,5%) · oro 3.542 (−2,1%) · dollaro 123,6 (+0,1%) · VIX 26,4 (−0,3)
Da rivedere: S&P 500 sotto la media a 200 giorni
Prezzi alla chiusura del 21/11. Contesto, non segnale: decide W3.2.</blockquote>
✅ Sistema ok · dati fino al 21/11 · decisione dom 29/11
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 19 · Soglia d'allarme W3.2 (drawdown o stop consecutivi)

```html
⚠️ <b>BTC · Soglia d'allarme: rivedi la strategia</b>
• equity −16,2% dal massimo del 2026-11-10 (soglia −15%)
• 2 stop consecutivi in perdita (ultimo: segnale del 2026-11-15; soglia 2)
Consigliato: revisione e rischio dimezzato (decidi tu).
<blockquote expandable>Storico dal vivo dal 31/10. Nessuna azione automatica: segnali e posizione non cambiano.</blockquote>
<a href="https://andreagalanti91.github.io/radar/">Apri la dashboard</a>
```

### 20 · Controllo di coerenza dei dati

```html
⚠️ <b>BTC · Dati da verificare prima della prossima decisione</b>
• dati spot: 2 giorni mancanti negli ultimi 60 (2026-11-03, 2026-11-04)
• decisione del 2026-11-15: con i dati provvisori «short», con i definitivi «nessuna»
Nessuna azione automatica.
```

### 21 · Fonte dati non disponibile

```html
⚠️ <b>Problema tecnico: fonte dati non disponibile</b>
• perp: HTTPError 503
• ETH funding: Timeout
Segnali calcolati sui dati fino al 21/11: decisioni possibili in ritardo.
```

### 22 · Dati fermi da oltre 36 ore

```html
⚠️ <b>Problema tecnico: dati fermi da oltre 36 ore</b>
• funding: ultimo giorno 19/11
• ETH spot: ultimo giorno 19/11
Segnali calcolati sui dati fino al 21/11: decisioni possibili in ritardo.
```

### 23 · Giro interrotto: nessun dato W3.2

```html
⚠️ <b>Problema tecnico: giro interrotto</b>
Dati di W3.2 assenti (ConnectionError): nessun segnale calcolato in questo giro.
```

### 24 · W3.2 non calcolato

```html
⚠️ <b>BTC · Segnale non calcolato in questo giro</b>
<code>KeyError: 'close'</code>
Il prossimo giro riprova; posizione e livelli comunicati restano validi.
```

### 25 · Workflow: salvataggio (push) fallito

```html
⚠️ <b>Radar · salvataggio dei dati non riuscito</b>
5 tentativi falliti: stato in cache, ripristinato al prossimo giro.
<a href="https://github.com/andreagalanti91/radar/actions/runs/123456789">Dettagli del giro</a>
```

### 26 · Workflow: test falliti

```html
⚠️ <b>Radar · test falliti</b>
Gli avvisi sono partiti comunque.
<a href="https://github.com/andreagalanti91/radar/actions/runs/123456789">Dettagli del giro</a>
```

### 27 · Workflow: giro fallito

```html
⚠️ <b>Radar · giro non completato (radar)</b>
<a href="https://github.com/andreagalanti91/radar/actions/runs/123456789">Dettagli del giro</a>
```

### 28 · Test di connessione

```html
✅ <b>Radar · connessione riuscita</b>
```
