# Stato — W3.2 ovunque, restyling ispirato a CoinTracker, sentiment nella Pre-analisi, README

**Stato:** IN CORSO · 22/11/2026 · Opus 5.5 medium (regia), agenti radar-ui e general-purpose

## Prompt originale
> Ok allora procedi a inserire la W3.2 dappertutto. Modifica readmi, simulatore, tool tutto. Devo vedere solo quella strategia.
> Dobbiamo creare il tool -> Modifica anche brand similare a https://www.cointracker.com/ Cerca immagini della loro piattaforma,
> voglio copiare gli stili, oggetti, font, colori. Tutto. Fammi effettuare login, ho creato un account.
Poi: "Per CoinTracker intendevo prendi ispirazione su tutto, crea una tua analisi per fare un brand migliore, agisci come un brand
designer ux designer ui designer. Posso darti login alla loro piattaforma [...] La login era inerente a quello. Ok w3.2 ovunque.
Procedi e pubblica. Sistema il readme, è importante, voglio i dati di performance reali [...] Ti chiedo anche di approfondire nella
pre analisi in un algoritmo il sentiment di mercato con liquidazioni e orderbook."

## Decisioni
- Niente login con credenziali dell'utente su CoinTracker: analisi solo dalle pagine pubbliche; ispirazione, non copia (nome, logo e asset nostri).
- Tema chiaro principale, scuro come opzione. Deploy autorizzato ("Procedi e pubblica").
- Sentiment nella Pre-analisi come CONTESTO descrittivo (lezione 108), non come segnale.

## Piano
- [ ] A. radar-ui: analisi UX/brand + restyling di dashboard e pagine + solo W3.2 nell'interfaccia (via W2/W3.1/v2/Laboratorio)   ← IN CORSO
- [ ] B. agente: testi W3.2 in weekly.py/telegram.py, riga sentiment nella Pre-analisi (preview.py) con test   ← IN CORSO
- [ ] C. README con performance (regia)
- [ ] D. Suite, render, deploy, verifica

## Come riprendere
**Prossima azione:** raccogliere gli esiti di A e B; poi C e D.
