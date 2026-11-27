# Bot Telegram · inventario e lista definitiva proposta · 27/11/2026

Inventario completo (sola lettura) di tutti i messaggi e comandi; proposta di lista definitiva da approvare. Nessuna modifica al bot
prima dell'ok dell'utente ("nessun avviso Telegram nuovo senza chiedermelo").

## Lista definitiva proposta (19 stati)

### 1 · Strategia W3.2 (BTC ed ETH) — tengo tutti
| # | Stato | Quando | Icona |
|---|---|---|---|
| 1 | Nuovo segnale long/short | domenica dopo la chiusura | 🟢/🔴 |
| 2 | Segnale annullato | raro, fra domenica e lunedì | ⚪ |
| 3 | Ingresso eseguito | lunedì | 🟢/🔴 |
| 4 | Uscita automatica spostata (trailing) | al massimo una volta al giorno | 🔔 |
| 5 | Possibile uscita per distribuzione | una volta a settimana | ⏳ |
| 6 | Uscita decisa per lunedì | domenica | 🎯/🛑 |
| 7 | Uscita annullata | raro | 🔴/🟢 |
| 8 | Stop toccato | qualsiasi ora | 🛑 |
| 9 | Uscita eseguita (profitto/perdita) | dopo l'uscita | 🎯/🛑 |
Uniti: "segnale in ritardo", "posizione in corso al primo avvio" e "avvisi ripristinati" diventano varianti di 1 e 3 (stessa struttura).

### 2 · Riepilogo e contesto
| 10 | Riepilogo "Oggi" | una volta al giorno | 📋 |
| 11 | VIX in zona alta (> 30) o bassa (< 15) | primo controllo di ogni 4 ore, con isteresi | 📊 |
Proposta: VIX senza "Buy/Sell" e senza la parola "segnale" ("Paura alta sulle borse · solo contesto").

### 3 · Rischio della strategia
| 12 | Allarme strategia (unico) | ogni giro, una volta per evento | 🚨 |
Proposta: unire "Soglia d'allarme" (guard) e "Fuori dal backtest" (limiti) in un solo allarme a due livelli: attenzione (−15% dal
massimo, 2 stop di fila) e fuori dal backtest (oltre i limiti storici).

### 4 · Salute del sistema
| 13 | Problemi tecnici del giorno (con il dettaglio) | una volta al giorno | ⚠️ |
| 14 | Dati da verificare prima della decisione (coerenza) | una volta per evento | ⚠️ |
| 15 | Fonte critica ferma / dati vecchi | una volta al giorno per fonte | ⚠️ |
| 16 | Segnale non calcolato (BTC o ETH) | una volta al giorno | ⚠️ |
| 17 | Giro non completato (workflow: dati, test, salvataggio) | una volta ogni 6 ore per tipo | ⚠️ |
Uniti: "giro interrotto", "test falliti", "push fallito", "workflow fallito" diventano il 17, con anti-duplicato.

### 5 · Diario (comandi) — risposte
| 18 | Conferme dei comandi /entrato, /aggiungi, /uscito, /registro (e in futuro il Wallet) | subito al giro | ✅ |
| 19 | Errore di comando / comando sconosciuto | subito | ❔ |

### Da togliere (morti o spenti)
Salute "tutto ok" (dormiente), comandi /limit e "v2", eventi v2 calcolati e mai inviati, comandi wallet "in pausa", sentinella e
scout Hyperliquid (spenti), chiavi vecchie in state.json, alias inutilizzati. Resoconto del lunedì: riscriverlo in formato W3.2 o
toglierlo (è fuori dal repository, attività pianificata della conversazione originale).

## Problemi da correggere (in ordine di gravità)
1. Raffiche: "giro interrotto" e i 3 avvisi del workflow non hanno anti-duplicato (fino a 24–48 messaggi al giorno se un problema dura).
2. Comandi del diario ripetuti o persi: se il giro fallisce il diario non viene salvato e lo stesso comando riceve una risposta ogni
   ora; con il push fallito il comando si perde in silenzio; le risposte non controllano l'esito dell'invio.
3. Stessi problemi annunciati fino a 3 volte (coerenza + salute + riga in "Oggi").
4. Due giri l'ora possibili (cron :37 troppo vicino al giro delle :02).
5. Chiave dei buchi di coerenza che cambia con la finestra di 60 giorni (avviso ripetuto sullo stesso buco).
6. Formati incoerenti: date ISO in guard/coerenza, punto decimale in guard e xinbox, prefissi diversi, link alla dashboard mancante in
   coerenza, salute, VIX ed errori; ETH in uscita senza motivo nel riepilogo.
7. xinbox salva come post del trader qualsiasi messaggio inoltrato o foto.

## Domande per l'utente
1. Approvi la lista dei 19 stati e l'unione guard + limiti in un solo allarme a due livelli?
2. VIX: va bene togliere "Buy/Sell" e "segnale"?
3. Resoconto del lunedì: riscriverlo in formato W3.2 (BTC, ETH, scanner, registro su carta) o toglierlo?
4. xinbox (post del trader seguito): serve ancora o si toglie?
