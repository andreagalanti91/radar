# STATO · Ciclo opzioni 27/11/2026
Stato: COMPLETATO (salvo scelta utente % BTC)

Richiesta: desktop senza spazi (card full width); riattivare Opzioni; scadenze maggiori Deribit e impatti; analisi scadenza vicina
e movimento atteso; studio "le opzioni danno la direzione di BTC? il prezzo ha seguito le scadenze?"; quando put o call.

## Fasi
1. Desktop: anteprima (radar-ui) → attesa scelta utente. [ ]
2. Riattivare Opzioni + scadenze maggiori Deribit → immagini all'utente prima di pubblicare. [ ]
3. Rapporto scadenza 27/11 (mensile, 08:00 UTC) e 25/12 (trimestrale): research/opzioni_scadenze/. [ ]
4. Studio preregistrato direzione dalle opzioni (radar-ricerca): research/opzioni_direzione/. PREREG committato da solo. [ ]
5. Risposta put/call basata sui dati. [ ]

## Vincoli
W3.2 non si tocca; indicatori solo supporto; nessun avviso Telegram nuovo; niente pubblicazione senza test, suite, render, verifica.

## Prossima azione
Fase 3 dati dal vivo (Deribit raggiungibile dal contenitore), agenti fasi 1 e 4 avviati.

## Aggiornamento 27/11 08:10 UTC
- F1 anteprima desktop A/B: stato/ux-varianti/desktop (commit). Attesa scelta utente. Patch in LEGGIMI.md/css_A.css/css_B.css/js_A.py.
- F2 Opzioni riattivata + Scadenze maggiori: commit 2cbcdbd sul branch di lavoro, NON pubblicata (attesa "pubblica Opzioni").
- F3 rapporto: research/opzioni_scadenze/README.md (regolamento 61.600, max pain 70k non raggiunto).
- F4 studio: PREREG 14cadc0, risultati committati; revisione radar-review in corso. Poi lezione 128 e indice.
- F5 risposta put/call: dalla sezione del README dello studio, dopo la revisione.
- 27/11 ~08:40: revisione critica fatta (confermato nella sostanza; V6 p esatto 0,007/Holm ≈0,06, V2 = −V1), correzioni applicate,
  lezione 128 e indici. F5 risposta consegnata. Restano solo le decisioni utente: desktop A/B, "pubblica Opzioni", % BTC.
## Prossima azione
Alla scelta dell'utente: applicare patch desktop (A: css_A.css + js_A.py; B: css_B.css) con test, suite, render, deploy unico con Opzioni.
- 27/11 08:42 UTC: pubblicati layout desktop A e Opzioni con Scadenze maggiori e La nostra analisi; verifica sito OK (12 colonne a 1280, 1 a 400, muri e movimento atteso valorizzati, 0 errori JS).
