# Studio della vista Oggi (26/11/2026) — base per le 5 varianti

Anteprima: nessun cambio a radar/, tests/, data/. Dati: report pubblicato del 26/11 19:20 UTC (riga `const R =` del sito,
R.mercato per i 6 semafori, grafico.json per la serie dei prezzi del grafico V4).

Metodo. Nell'ambiente di questo agente lo strumento Skill non c'è (nessuna skill "design:design-critique", "dataviz",
"design:ux-copy", "design:accessibility-review" installata: in `.claude/skills` ci sono solo gengar, session-start-hook, synced).
Ho applicato i loro principi a mano: critica di gerarchia e focus (test dei 5 secondi), scelta del grafico per la domanda
(dataviz), testi brevi orientati all'azione (ux-copy), contrasti WCAG AA e aree di tocco (accessibility). Riferimento visivo
attuale: `ATTUALE_400.png` (template corrente renderizzato con il report del giorno; il sito pubblicato mostra ancora la
variante B annullata, quindi non l'ho usato come base).

## 1. Cosa deve vedere l'utente per primo (ordine delle priorità)

1. **Come vanno le posizioni**: due righe, BTC e ETH, lato e risultato in $ e % (+ totale). Oggi: BTC short +7,2% (+2.169 $),
   ETH short +16,6% (+4.971 $), totale +7.140 $.
2. **Quando escono, in profitto o in perdita**: il prezzo che le chiude e quanto si incassa/perde lì. Oggi BTC esce in
   perdita sopra 74.273 $ (chiusura settimanale, −4.051 $) o a 75.764 $ (stop mobile, −4.718 $); in profitto solo con
   l'uscita per distribuzione della domenica (oggi no, varrebbe +2.128 $) o se BTC scende sotto ~47.800 $ (lo stop passa in utile).
3. **Dove può andare BTC in 30 giorni**: intervallo 80% 52.100–74.800 $ al 25/12 e i 4–5 livelli che contano con la
   probabilità di toccarli. Il dato chiave da collegare al punto 2: l'uscita in perdita (75.764 $) ha il 15% di probabilità
   di essere toccata entro 30 giorni.
4. **Pre-analisi della domenica**: "con i dati di oggi restano aperte" + quanto manca a ogni condizione di uscita
   (BTC +22,9%, ETH +30,5%) + i 4 short simili dal 2022 tutti chiusi in utile.
5. **Mercato power**: il conteggio (1 a favore · 3 neutri · 2 contro) e i 6 motivi in parole semplici. È contesto, non decide.
6. Notizie del giorno (1 evento + 1 notizia).

## 2. Problemi della vista attuale (test dei 5 secondi)

Cosa si capisce in 5 secondi oggi: "BTC 60.447, short aperto, BTC +7,4% ETH +16,6%". Non si capisce: quanto valgono in $,
quando escono (è nella riga piccola in grigio, 0,8 rem, una frase lunga con 4 numeri), se il mercato è a favore.

- **Gerarchia piatta**: la riga posizioni (la cosa più importante) è più piccola della scheda livelli; l'intervallo
  52.100–74.800 è il numero più grande della pagina dopo il prezzo.
- **Valori ripetuti**: il prezzo compare 4 volte (hero, "chiusura 60.447" nel righello, "da chiusura 1h 60.447" nell'intro
  della tabella, linea "chiusura 60.447" fra i livelli); il trailing 75.764 compare nella riga posizioni e fra i livelli;
  VIX e FOMC sia nel Contesto sia nelle notizie/Mercato power; "Short aperto" nella barra e nella riga.
- **Ordine**: pre-analisi e Mercato power non sono in Oggi (sono in Posizioni o mancano); il Contesto (che per le regole non
  conta, lezione 113) occupa più spazio della pre-analisi, che invece dice se domenica si esce.
- **Gergo**: "Trailing W3.2", "Liq. short on-chain", "EMA21", "distribuzione", "σ", "resist." senza spiegazione.
- **Tabella livelli densa**: 4 colonne su 360 px, testi a 0,78 rem in grigio chiaro, la linea del prezzo a metà tabella è
  difficile da leggere; 6 livelli di cui 3 sono liquidazioni quasi coincidenti (61.731 / 61.426, 59.613).
- **Colore**: rosso usato per il nome "Prima resistenza" e arancio per il trailing: il rosso non significa perdita.
- **Accessibilità**: --label3 (#717884 su #15171c, contrasto 4,0:1; in chiaro #878e99 su bianco 3,3:1) è sotto AA per testi
  sotto i 18 px; diverse etichette sono a 11–12 px (0,62–0,74 rem); i "Dettagli ›" sono link di testo con area di tocco < 44 px.

## 3. Principi comuni alle 5 varianti

1. **Ordine fisso per priorità**: posizioni → uscite → 30 giorni → pre-analisi → Mercato power → notizie.
2. **Un dato una volta sola**: il prezzo solo in alto; le uscite solo nel blocco uscite (nel grafico/righello a 30 giorni
   compaiono come segni, senza ripetere i $); niente scheda Contesto separata: trend e volatilità diventano una riga del
   Mercato power, Fed/VIX/scadenza opzioni sono già tre dei suoi semafori.
3. **Parole al posto delle sigle**: "stop mobile" (trailing), "media a 21 settimane" (EMA21), "uscita per distribuzione
   (i perp vendono e il funding diventa negativo)", "scadenza opzioni" (OPEX), "paura sulle borse (VIX)", "posizioni a leva
   chiuse forzatamente" (liquidazioni). W3.2 = "la strategia".
4. **Numeri**: grandi, cifre tabellari, sempre con $ e segno (+/−), formato italiano.
5. **Colore con un solo significato**: verde = profitto, rosso = perdita. Mercato power usa blu (a favore), arancio (contro),
   grigio (neutro) con simbolo + / − / = (leggibile anche senza colore). Le probabilità usano il colore del tema (indaco).
6. **Grafici solo dove rispondono a una domanda**: barra di uscita (dove sono prezzo, ingresso e uscite su una sola retta),
   cono/intervallo a 30 giorni, barrette delle operazioni simili, striscia dei 6 semafori. Etichette fuori dai segni, mai
   sovrapposte (righe sotto il grafico invece di etichette appese quando i segni sono vicini, come 74.273 e 75.764).
7. **Accessibilità**: testi secondari in --label2 (≥ 7:1), mai --label3 per informazioni; etichette ≥ 13 px su telefono;
   righe e "Dettagli ›" con altezza ≥ 44 px; focus visibile.
8. **Telefono prima**: nessuno scorrimento orizzontale a 360–400 px; su desktop le schede vanno in due colonne.
9. **"Dettagli ›"** dove c'è altro da vedere (porta alla pagina Posizioni, Grafico, Notizie o apre il pannello delle regole).
