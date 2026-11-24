# Prompt per la sessione Claude Code del repo `radar`

Incolla tutto il testo qui sotto nella sessione di radar e allega i file di questa cartella (oppure lo zip `radar-opzioni.zip`).

---

Voglio una nuova sezione **"Opzioni"** nella dashboard di Radar, dentro la vista **Oggi**, subito sotto la card di W3.2.
Deve dirmi, a ogni segnale di W3.2 su BTC, **quale opzione comprare, quanti contratti, quanto spendo e quanto posso perdere al
massimo**, e poi seguire quell'opzione fino alla chiusura. Per ora tutto **sulla carta**: Radar non invia ordini.

È un modo diverso di eseguire lo stesso segnale, non una strategia nuova: **W3.2 non cambia**.

## Da dove viene

L'ho studiata in un altro repo (`teststrategy`). Lo studio completo è in `OPZIONI_W32.md`; in breve:

- a ogni segnale di W3.2 si compra **una sola** opzione (call se long, put se short), scadenza il venerdì più vicino a 30
  giorni, prezzo d'esercizio il più vicino al prezzo, spendendo il **5% del capitale di W3.2**;
- si vende quando W3.2 esce; se scade prima, l'incasso è automatico e **non si rinnova**;
- rifatta con i prezzi veri di Deribit sulle 23 operazioni di W3.2 dal 2018: 10.000 $ → 51.000 $, contro 53.000 $ di W3.2 a
  metà dimensione. **Non rende di più**: cambia il profilo di perdita (mai più del 5% per operazione, senza stop e senza leva;
  in cambio perde più spesso, 35% delle operazioni contro 22%).

## Cosa ti allego

| File | A cosa serve |
|---|---|
| `opzioni.py` | Modulo autonomo (solo libreria standard): scarica la catena da OKX, sceglie il contratto, calcola la quantità, tiene il registro su carta, prepara il dizionario per la dashboard (`build`) |
| `test_opzioni.py` | 6 test sulla catena vera del 24/11/2026 |
| `catena_2026-11-24.csv.gz` | La catena OKX usata dai test (1.584 contratti) |
| `esempio_sezione.json`, `esempio_segnale.json`, `esempio_attesa.json` | L'uscita di `build` in tre stati: posizione aperta, giorno del segnale, nessun segnale. È lo schema da mostrare |
| `registro_iniziale.json` | La riga da cui partire per la posizione short aperta il 16/11 |
| `storico_prezzi_veri.json` / `.csv` | Le 23 operazioni del backtest con prezzi veri, per la tabella dello storico |
| `riferimento_sezione.html`, `anteprima_desktop.png`, `anteprima_telefono.png` | Come immagino la sezione. In Radar va rifatta con i componenti e i colori della dashboard |
| `fetch_okx_options.py` | Lo script che ho usato per salvare la catena completa: riferimento per l'archivio giornaliero |
| `OPZIONI_W32.md`, `opzioni_w32.png` | Lo studio, da cui prendere i testi |

## Cosa deve mostrare la sezione

1. **L'azione di oggi**, in una riga con un'etichetta: `COMPRA`, `TIENI`, `VENDI`, `FUORI`, `ATTESA` (campo `azione` di
   `build`, con `titolo` e `testo`).
2. **Se c'è un segnale (`COMPRA`)**: contratto (tipo, prezzo d'esercizio, scadenza e giorni), prezzo lettera e denaro,
   **contratti da comprare**, spesa, **perdita massima** in dollari e in % del capitale, pareggio a scadenza, volatilità
   implicita; sotto, la tabella "cosa succede alla scadenza" (`scenari`).
3. **Se l'opzione è aperta (`TIENI` / `VENDI`)**: contratto, giorni alla scadenza, prezzo d'acquisto, valore di adesso al
   denaro, risultato in dollari e in % del capitale.
4. **`FUORI`**: quando W3.2 è ancora in posizione ma l'opzione è già scaduta o venduta, oppure non è mai stata registrata. Va
   detto chiaramente che non si rinnova.
5. **`ATTESA`**: nessun segnale. Mostra in piccolo cosa si comprerebbe oggi (campo `esempio`, long e short), come riferimento.
6. **Registro su carta**: tutte le righe del registro (segnale, contratto, prezzo d'acquisto, chiusura, stato, risultato).
7. **Storico con prezzi veri** (chiuso di default): le 23 operazioni di `storico_prezzi_veri.json` e il totale.
8. **Le 7 regole** (campo `regole`) e la **nota fissa**: "Nel backtest con prezzi veri dal 2018 questa strategia non rende
   più di W3.2: rende circa quanto W3.2 a metà dimensione, con la perdita per operazione fissata al 5%. Perde anche quando
   BTC resta fermo. Sulla carta: Radar non invia ordini."

## Come integrarla

- **Modulo**: porta `opzioni.py` in `radar/opzioni.py` con i suoi test. Usa `_get` e le convenzioni di rete che Radar ha già
  (`radar/data.py` chiama già `www.okx.com`): niente fonti nuove, niente chiavi.
- **Stato di W3.2**: `opzioni.build` e `opzioni.aggiorna_registro` leggono il dizionario di `weekly.evaluate()` per BTC
  (`status`, `side`, `signal_date`, `entry`, `entry_px`, `price`, `capital`). Non duplicare la logica di W3.2.
- **Capitale e quota**: capitale = `weekly.asset_capital("BTC")`; quota = 5%, modificabile con una variabile d'ambiente
  (per esempio `RADAR_OPZIONI_QUOTA`), mai sopra il 10%.
- **A ogni giro orario**: scarica la catena (3 chiamate pubbliche), chiama `aggiorna_registro`, poi `build`, e metti l'uscita
  nel report con `_soft` (un errore qui non deve fermare il giro né toccare W3.2).
- **Registro**: file `data/opzioni_carta.json`, scritto solo quando cambia. `aggiorna_registro` è idempotente: registra
  l'acquisto alla **lettera** al primo giro dopo l'ingresso di W3.2 (entro 36 ore), la vendita al **denaro** quando W3.2
  esce, la scadenza al valore intrinseco. Per il prezzo di regolamento passa a `regolamento=` una funzione che legge
  `public/delivery-exercise-history` di OKX.
- **Posizione di oggi**: W3.2 è short dal 16/11. Parti da `registro_iniziale.json` (put 65.000 con scadenza 11/12, prezzo
  d'ingresso ricostruito dagli scambi OKX di quel giorno) e **ricalcola contratti e spesa con il capitale vero**; nella riga
  resta la nota "ricostruita".
- **Opzioni lineari**: nel SEE OKX offre solo le lineari (`BTC-USD_UM-…`, premio e incasso in dollari), ed è quello che uso
  io. Hanno quotazioni continue ma pochi scambi. Se per il contratto scelto mancano denaro o lettera, mostra il prezzo del
  gemello inverso convertito in dollari e scrivilo accanto ("prezzo indicativo dal contratto inverso").
- **Archivio dei prezzi**: una volta al giorno salva la catena in `data/opzioni/catena_AAAA-MM-GG.csv.gz` (bastano i
  contratti entro ±20% dal prezzo e con almeno 7 giorni alla scadenza). OKX non conserva lo storico dei contratti scaduti:
  questo archivio serve a verificare fra qualche mese il backtest con i prezzi veri.
- **Telegram**: nessun messaggio nuovo. Nei messaggi di **ingresso** e di **uscita** di W3.2 che già esistono aggiungi una riga
  "Opzione (su carta): …" con contratto, prezzo, contratti, spesa = perdita massima (ingresso) o risultato (uscita).
  **Fammi vedere il testo prima di attivarlo.** Se pensi serva un avviso alla scadenza dell'opzione, proponimelo: non
  aggiungerlo da solo.
- **Solo BTC**: lo studio è su BTC. Niente ETH per ora.

## Vincoli

- Segui le regole del progetto: skill gengar, file `stato/STATO-opzioni.md`, test, suite verde, render a 400 e 1280 px con dati
  reali, deploy e verifica sul sito pubblicato.
- **W3.2 non si tocca**: nessuna modifica a `radar/weekly.py`, ai segnali, agli stop o al capitale della strategia.
- **Nessun ordine, nessuna chiave API**: la sezione legge solo prezzi pubblici.
- **Le 7 regole non si ottimizzano**: niente rinnovo, niente quota variabile, niente scelta di scadenze o prezzi d'esercizio
  diversi. Se trovi un motivo per cambiarle, dimmelo prima.
- So che la dashboard oggi mostra solo la strategia in uso e tiene fuori i conti su carta: questa è un'eccezione voluta,
  perché è un modo di eseguire W3.2 e voglio vederla accanto al segnale. Deve però essere chiaro a colpo d'occhio che è
  "sulla carta".
- I testi devono dire che non rende più di W3.2 e che si può perdere tutto il premio. Niente toni promozionali.
- Tema chiaro e scuro; dal telefono nessuno scorrimento orizzontale della pagina (le tabelle scorrono nel loro riquadro).

## Come capisco che è fatto

1. `python -m pytest` verde, con i 6 test di `test_opzioni.py` adattati al modulo in `radar/`: scelta del contratto
   (`BTC-USD_UM-261225-60000-P` per uno short a 60.144 $ il 24/11), quantità (66 contratti e 2.236 $ con 45.000 $ di
   capitale), registro (acquisto alla lettera, vendita al denaro, scadenza, **nessun rinnovo**), tutti gli stati di `build`.
2. Un test che dimostra che un errore di rete di OKX non ferma il giro e non cambia l'uscita di W3.2.
3. Screenshot della sezione a 400 e 1280 px, tema chiaro e scuro, con dati reali, nello stato di oggi (`TIENI`).
4. La sezione è visibile sul sito pubblicato, si aggiorna a ogni giro, e `data/opzioni_carta.json` contiene la riga della
   posizione attuale.
5. Il testo proposto per la riga Telegram, in attesa del mio via libera.
6. Un riepilogo finale: cosa hai cambiato rispetto a `opzioni.py`, dove hai messo la sezione, cosa salva l'archivio.
