# PREREG · Indicatore "UTXO Block P/L Count Ratio" (CryptoQuant) come supporto a W3.2 · 25/11/2026

Scritto e committato da solo prima di qualsiasi rendimento. Domanda dell'utente: "Voglio solo sapere se questo indicatore è da
utilizzare con la nostra strategia per dare un supporto." Grafico fornito: `grafico_utente.jpg` (CryptoQuant, Axel Adler).

## Dati
La serie originale è a pagamento (CryptoQuant) e non è ricostruibile qui. Si usa un sostituto pubblico che misura la stessa
idea (mercato in guadagno o in perdita rispetto al prezzo di acquisto delle monete): **MVRV di CoinMetrics** (community API,
`CapMVRVCur`, giornaliero), dichiarato come sostituto in ogni tabella. Controllo di coerenza descrittivo prima dei rendimenti:
le zone segnate dal sostituto devono cadere nelle stesse finestre delle bande azzurre/viola del grafico dell'utente (inizio 2016,
12/2018–03/2019, 03/2020, fine 2022, 09/2023, metà 2026 e 11/2026; euforia 2017, inizio 2021, fine 2024). Se coincidono meno della
metà delle finestre, lo si dichiara e il verdetto riguarda solo il sostituto.

## Zone (fissate ora, solo dati passati)
- **Capitolazione**: (a) MVRV < 1,0; (b) MVRV nel 10% più basso delle ultime 4 anni (1.460 giorni, solo passato). Si riportano
  entrambe; il verdetto usa (b), che si adatta ai livelli del ciclo, e (a) come controllo.
- **Euforia**: (a) MVRV > 3,0; (b) MVRV nel 10% più alto delle ultime 4 anni.
- Lettura alla chiusura giornaliera UTC, azione all'apertura del giorno dopo (come le uscite giornaliere di W3.2).

## Ipotesi (W3.2 invariata in tutto il resto; motore `radar.weekly.simulate`, copia in research solo per la regola aggiunta)
- **H1**: uno short aperto di W3.2 si chiude al primo giorno di capitolazione (presa di profitto anticipata).
- **H2**: non si aprono short di W3.2 se quel giorno è capitolazione.
- **H3**: un long aperto di W3.2 si chiude al primo giorno di euforia.
- **H4** (descrittiva, fuori da W3.2): long a 1x dal primo giorno di capitolazione, uscita al primo giorno di euforia o dopo 365 giorni.

## Periodi, criteri, verdetto
BTC dal 2018-01-01 e dal 2021-01-01, 10.000 $, rischio 25% come W3.2. Una regola è **un supporto utile** se, in entrambi i periodi:
(1) finale > W3.2 e DD non peggiore di oltre 2 punti; (2) vale anche togliendo il trade di W3.2 che la regola cambia di più;
(3) placebo: la stessa regola applicata a date casuali con lo stesso numero di giorni-zona (1.000 estrazioni, blocchi di 30 giorni)
fa peggio nel 95% dei casi; (4) vale con entrambe le definizioni (a) e (b). Con pochi episodi (atteso 4–8 per lato) il risultato
più probabile è "non dimostrabile": lo si scrive così. Revisione critica di un agente separato prima del rapporto.

## Vincoli
W3.2 e il tool non cambiano; l'esito è un verdetto e, se positivo, una proposta all'utente.
