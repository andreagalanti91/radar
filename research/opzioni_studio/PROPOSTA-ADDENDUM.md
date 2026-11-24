# PROPOSTA di addendum al PREREG · soglie dei segnali F3 (fase 1, solo conteggi)

Proposta, NON committata: la sessione principale la rivede e la committa da sola prima di qualsiasi rendimento F3.
Ogni soglia è motivata solo dai conteggi di `conteggi.txt` (nessun P&L calcolato). Criterio: la soglia scritta nel PREREG
quando c'è; altrimenti la più selettiva che lascia almeno 20 operazioni in IS (2018–21) e in OOS (2022–26). Un segnale che
con nessuna candidata arriva a 20 per metà resta **descrittivo** (non può soddisfare il punto 4 del giudizio).

Regole comuni: decisione alla chiusura UTC della domenica, ingresso lunedì, opzione al venerdì quotato più vicino a 30 giorni,
alla pari, 5% del conto, fino a scadenza o a segnale contrario (solo direzionali), poi si rientra al primo lunedì in cui il
segnale vale ancora; una posizione per volta; ogni segnale su un conto suo (non sommato a B0).

| Segnale | Soglia proposta | Operazioni IS / OOS | Tempo in posizione | Con W3.2 in posizione all'ingresso | Esito del conteggio |
|---|---|---|---|---|---|
| a · tendenza di solo prezzo | chiusura sopra (sotto) la SMA 40 settimane **e EMA 20 settimanale in salita (discesa)** rispetto alla settimana prima | 42 / 52 (call 56, put 38) | 89% | 55% | valutabile |
| b · condizioni d'ingresso di W3.2 ogni settimana | come W3.2 (regime, EMA 21, filtro F1), **flusso perp > 0 (< 0)**: nessun parametro nuovo | 16 / 26 | 41% | 98% | **descrittivo** (IS < 20; con ±0,5σ 12/22, ±1σ 7/14) |
| c · volatilità a buon mercato → straddle | **IV a 30 g < volatilità realizzata a 30 g, oppure IV nel quintile basso (≤ 20%) delle ultime 52 settimane** (testo del PREREG) | 19 / 37 con IV proxy dal 2019 | 56% | 55% | valutabile se con la IV della superficie (anche 2018) IS ≥ 20; altrimenti descrittivo |
| d · compressione → straddle | ampiezza Bollinger 20 settimane (±2σ, (sup−inf)/media) **nel quintile basso delle ultime 52 settimane** | 15 / 15 | 30% | 37% | **descrittivo** (nessuna candidata: 104 sett. 12/16, tutta la storia 5/25) |
| e · dopo una cascata → call | **un giorno con chiusura −10% o peggio** sulla chiusura precedente nella settimana | 12 / 6 | 18% | 44% | **descrittivo** (−8%: 19/8; minimo −10%: 21/11) |
| f · cono contro premio | valore atteso a scadenza secondo il cono **≥ 1,4 × costo** (premio × 1,03 + commissione), call o put; se entrambe la maggiore | 22 / 35 (solo call) | 58% | 61% | valutabile, con la riserva sotto |

Definizioni da fissare con l'addendum:
- **IV a 30 giorni** (c, f): `superficie.iv(domenica, scadenza_vicina(domenica, 30), prezzo d'esercizio più vicino a F, "C")`;
  quintile calcolato sulla serie settimanale della superficie (solo passato, 52 valori). Se la superficie manca quel giorno
  ("mancante") il segnale è 0. I conteggi qui usano una IV proxy (DVOL dal 2021-03-24, prima l'IV alla pari degli scambi
  Deribit della domenica dal 2019-01-06; 2018 senza dato): vanno rifatti con la superficie prima dei rendimenti, senza
  cambiare le soglie.
- **Cono** (f): `radar/cone.py` invariato, storia fino alla domenica compresa, deriva storica, 2.000 cammini, seme del tool,
  orizzonte = giorni alla scadenza reale. La deriva (≈ +0,10–0,15% al giorno) rende la call quasi sempre "conveniente"
  (rapporto mediano 1,40; ≥ 1 nel 98% delle settimane) e la put quasi mai (mediana 0,62): con soglie 1,0–1,2 il segnale è
  una call permanente (80–83% del tempo). La soglia 1,4 è la più alta con almeno 20 operazioni per metà (1,5: 18/26).
- **Cascata** (e): le liquidazioni non sono utilizzabili (data/liquidations.csv parte dal 2026-10-30); con la decisione
  domenicale l'ingresso arriva da 1 a 7 giorni dopo il crollo.

Osservazioni dai soli conteggi:
- b non aggiunge occasioni: il 98% degli ingressi avviene con W3.2 già in posizione dallo stesso lato (correlazione con B0
  prevedibilmente sopra 0,5). È di fatto "B0 con rinnovo condizionato".
- a ed f stanno in posizione l'80–90% del tempo: sono quasi un'esposizione continua, non segnali rari.
- c e d (straddle) sono gli unici in larga parte fuori dai periodi di W3.2 (37–55% di sovrapposizione all'ingresso).

Riscontri della fase 1 utili alla revisione:
- W3.2 ricostruita dal 2018 con `radar.weekly.simulate` (non modificato) sul frame lungo: 23 operazioni, 22 identiche al CSV
  dell'utente per verso, ingresso e uscita. Differenza: n. 9 (long del 2020-12-14) esce il **2021-01-04** (distribuzione) e non
  il 2020-12-31: il CSV la taglia al cambio di dati del 31/12/2020 (lo studio dell'utente lo dichiara). Per B0 si propone
  l'uscita vera (2021-01-04).
- Motore contro le 23 operazioni (prezzatore provvisorio): scarto mediano del moltiplicatore +0,8% (soglia ±15%), casi a
  scadenza entro 0,034.
