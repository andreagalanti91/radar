# Zeiierman Trend Pressure · proposte per il ciclo 2 (scritte il 12/11/2026, nessuna testata)

Al massimo 3 modifiche, motivate dagli errori del ciclo 1 (README.md §5) e dalla coerenza delle zone (§4), non dal risultato.
Valgono le stesse regole del ciclo 1: dati, costi, esecuzione, periodi IS/OOS, soglie, placebo, vicini e "senza top 3" di
PREREG.md, più i vicini dei nuovi parametri. Indicatore con parametri di default; zona = sola Z-Trend (tz ≤ −70 blu, ≥ −30 rossa).

## P1 · Zona blu solo con filtro di regime, ingresso al rilascio con conferma del Core (long)
Errori che la motivano: R1v long perde 3 volte su 6 per "zona lunga in trend forte", tutte nel 2022 (zona blu di 103 giorni con
−53%); altri 2 sono rilasci falsi. La zona blu da sola compra anche nei bear.
Regola: long quando tz risale sopra −70 dopo una zona blu (rilascio visivo) **e** la chiusura è sopra la SMA 200 giorni **e** il
Core non è rosso; uscita: stop 2,5 ATR(14) oppure tz < −50 con Core rosso (stato R3 short). Varianti preregistrate: filtro SMA 200
giorni oppure regime di W3 (SMA40w/EMA20w non ribassista); vicini SMA 150/250.
Rischio noto: SMA 200 e regime W3 sono la stessa informazione del trend (lezione 83, accordo 86–94%): se P1 passa, va verificato
che non sia un W3 più lento (correlazione dell'esposizione con W3).

## P2 · Non uscire in zona rossa: uscita al rilascio rosso, con variante "parziale"
Errore che la motiva: R1v esce all'ingresso in rossa, ma dopo quell'ingresso BTC sale in media +12,5% a 60 giorni (base +5%) e
dopo l'inizio dell'esaurimento rosso +10,1% a 30 giorni (6 volte su 7): l'uscita totale in rossa taglia le code destre (lezioni 58,
73). Regola: per i long di P1 l'uscita in profitto avviene al rilascio rosso visivo (tz scende sotto −30 dopo essere stata ≥ −30),
non all'ingresso. Variante richiesta dall'utente: metà all'ingresso in rossa e metà al rilascio. Nota a priori: le uscite parziali
hanno già perso in W2 (lezione 73); la variante parziale si accetta solo se batte l'uscita totale al rilascio in entrambe le metà.

## P3 · Dentro W3 come gestione del rischio: ridurre l'esposizione nello stato "trend negativo", non in zona rossa
Motivazione: la proposta "ridurre l'esposizione in zona rossa" è contraddetta dai dati (la rossa precede rialzi: ridurla taglierebbe
i grandi trend da cui W3 prende il rendimento). L'informazione che ha mostrato qualcosa è lo stato R3 short (tz < −50 e Core rosso:
PF 2,47–2,70 nel 2021–23, ma 0,58 nel 2024–26 come trade short), che segnala il deterioramento prima della chiusura settimanale sotto la EMA21 di W3.
Regola: con W3 long aperto, esposizione al 50% mentre tz < −50 e Core rosso (valutato alla chiusura giornaliera, esecuzione il giorno
dopo), di nuovo al 100% quando lo stato finisce; ingressi e uscite di W3 invariati. Giudizio: MAR di W3 dal 2021 e nel 2018–20, a pari
o migliore DD, senza peggiorare i 3 trade migliori di W3 di oltre il 10% (rischio di tagliare le code, lezione 88: un singolo trade
perso non è un motivo).
