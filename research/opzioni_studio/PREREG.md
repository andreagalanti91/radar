# PREREG · Opzioni su BTC: struttura, uscite e segnali · ciclo notturno 24–25/11/2026

Scritto e committato da solo PRIMA di calcolare qualsiasi rendimento nuovo. Già visto (dichiarato): lo studio dell'utente
`../opzioni_import/OPZIONI_W32.md` (23 operazioni di W3.2 con prezzi veri Deribit; 30/60/90 giorni e rinnovo a modello) e
`../opzioni_sim/` (spesa per operazione). Tutto il resto è nuovo.

## Domanda
Esiste una regola per operare in opzioni su BTC (solo acquisto di call e put) migliore della regola in uso sulla carta
(B0), e un segnale che dia più occasioni dei 2–3 segnali l'anno di W3.2, senza perdere rendimento?

## Riferimento B0 (le 7 regole, non modificate)
Segnale W3.2 · call se long, put se short · venerdì più vicino a 30 giorni · prezzo d'esercizio più vicino al prezzo · 5% del
conto in premio · si vende quando W3.2 esce, se scade prima si resta fuori · mai rinnovare.
Altri riferimenti: W3.2 intera, W3.2 a metà dimensione, liquidità.

## Dati e prezzi
BTC 2018-01-01 → 2026-11-23. Prezzi delle opzioni: scambi veri di Deribit (API pubblica `history.deribit.com`), superficie
giornaliera di volatilità implicita ricostruita dagli scambi; dove manca lo scambio, Black-76 con la volatilità della
superficie. Costi: 3% del premio per lato (denaro-lettera), commissione 0,03% del controvalore con tetto 12,5% del premio,
esercizio 0,02%. Solo scadenze realmente quotate quel giorno. Il motore deve prima riprodurre le 23 operazioni di
`storico_prezzi_veri.csv` (scarto mediano del moltiplicatore entro ±15%): se non ci riesce, lo si dichiara e ci si ferma.
Conto di 10.000 $; ogni risultato è riportato dal 2018 e dal 2021 con finale, DD (giornaliero, opzioni valutate ogni giorno),
operazioni, quota in guadagno, perdita peggiore, serie peggiore.

## Famiglie (fissate ora; i parametri numerici dei segnali F3 si fissano sui soli conteggi, con addendum prima dei rendimenti)
**F1 · Struttura sul segnale di W3.2** (23 operazioni): scadenza {≈14, ≈30, ≈60, ≈90 giorni} × prezzo d'esercizio
{alla pari, 5% fuori, 10% fuori, 5% dentro}. Spesa 5%, uscita come B0. 16 celle.
**F2 · Uscita sul segnale di W3.2** (contratto di B0): U0 come B0 · U1 vendita a 2× il premio · U2 vendita a 3× · U3 metà a 2×
e metà come B0 · U4 vendita a 7 giorni dalla scadenza se ancora aperta · U5 un solo rinnovo se W3.2 è ancora in posizione
e l'opzione scaduta ha chiuso in guadagno. 6 celle.
**F3 · Segnali indipendenti da W3.2** (decisione settimanale, domenica; ingresso lunedì; opzione ≈30 giorni alla pari, 5%, fino
a scadenza o a segnale contrario; una posizione per volta):
 a. tendenza di solo prezzo (chiusura sopra/sotto SMA40w con EMA20 concorde): call/put al primo segnale e a ogni scadenza finché vale;
 b. flusso perp (le condizioni d'ingresso di W3.2 valutate ogni settimana, non solo al primo segnale);
 c. volatilità a buon mercato: implicita a 30 giorni sotto la realizzata a 30 giorni, o nel quintile basso a un anno → call + put (straddle);
 d. compressione: ampiezza delle bande settimanali nel quintile basso → straddle;
 e. dopo una cascata (giorno con −10% o peggio, o liquidazioni estreme): call a 30 giorni;
 f. cono del tool contro mercato: opzione comprata solo se il valore atteso secondo il cono (bootstrap, deriva storica) supera il premio di una soglia.
**F4 · Opzione al posto dello stop** (W3.2 su perp alla dimensione di W3.2 a metà, senza trailing, con put/call di
protezione a 30 giorni 10% fuori, rinnovata finché la posizione è aperta). 1 cella, descrittiva.
Esclusi: vendita di opzioni scoperte (regola 7, studio precedente dell'utente). Gli spread a debito (comprare alla pari e
vendere 15–20% fuori) si riportano solo come descrittivi: richiedono di vendere una gamba.

## Scelta e giudizio
Scelta dei parametri solo sul 2018-01 → 2021-12 (IS). Giudizio una volta sul 2022-01 → 2026-11 (OOS). Una candidata è
**migliore di B0** solo se, in OOS: (1) finale > B0 e DD non peggiore di B0 di oltre 3 punti; (2) resta sopra B0 togliendo le sue
2 operazioni migliori (e le 2 migliori di B0); (3) almeno 3 vicini su 4 nella griglia restano sopra B0; (4) per F3: almeno 20
operazioni in ciascuna metà e placebo p ≤ 0,05 (1.000 estrazioni di date d'ingresso a caso, stesso numero e stesso lato);
(5) correzione di Holm sul numero di celle provate nella famiglia. Con 23 operazioni F1 e F2 difficilmente possono superare
il punto 5: in tal caso il verdetto è "nessun vantaggio dimostrabile" e B0 resta.
Un segnale F3 è **utile** anche senza battere B0 se da solo, in OOS, chiude sopra il conto iniziale con PF ≥ 1,2, supera i punti
2–5 e ha correlazione settimanale con B0 sotto 0,5 (occasioni aggiuntive vere).

## Secondo ciclo
Ammesso una volta, dopo la revisione critica di un agente separato, per un errore del motore o per una ipotesi nata dalla
diagnosi delle operazioni perdenti. Addendum committato prima dell'esecuzione; i suoi risultati sono esplorativi.

## Cosa NON cambia senza approvazione dell'utente
W3.2, le 7 regole, la pagina Opzioni, gli avvisi Telegram. Lo studio produce un rapporto e una proposta.
