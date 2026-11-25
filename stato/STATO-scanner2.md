# STATO · Scanner top 200 e nuova pagina · avviato 25/11/2026

Stato: FASI 1–2 FATTE (agente), in attesa di revisione, deploy e verifica

## Prompt originale
"Radar strumento super utile, grazie! Ti chiedo di impostare una ricerca settimanale su ingressi di top 200 crypto. Imposta
meglio la pagina, non è capibile bene. Studia la UX/UI migliore. Ipotesi: formato tabellare come è adesso con in cima le
preferite, le selezionate da te. Dimmi anche una cosa, queste dello scanner sono gestibili posizioni con piccole somme?
"Scommesse". Fammi domande se hai dubbi" — poi "Procedi" con le scelte di default.

## Decisioni (default accettati)
- Solo la pagina aggiornata la domenica: nessun messaggio Telegram nuovo.
- Preferite già segnate: SOL e TAO (stella salvata nel browser; l'utente ne aggiunge altre).
- Registro "scommesse" sulla carta: SÌ (correzione dell'utente: "Il registro eseguilo. Procedi inserisci dentro radar"); regole in `research/w32_asset2/REGISTRO-SCOMMESSE.md`.
- "In evidenza": BTC ed ETH (in uso), TRX (osservazione), preferite. Nessuna selezione per rendimento passato (lezione 123);
  unico filtro mostrato: concordanza con BTC (Q4: finale mediano 12.386 contro 10.381 $, DD −39 contro −56%).

## Fasi
1. Universo top 200 settimanale (CoinGecko) + verifica dati OKX per le monete senza Binance. 2. Studio UX e nuovo layout.
3. Test, render 400/1280, deploy, verifica.

## Fatto dall'agente (25/11/2026, nessun commit)
- Universo top 200 settimanale (radar/scanner.py build_universo_top200/aggiorna_universo): 144 incluse, 56 escluse; 107 calcolabili,
  37 dati insufficienti; 4 su OKX (CRO, OKB, PI, DGAI). OKX taker-volume con le pagine copre ~1440 giorni (non 100).
- Registro scommesse (radar/scommesse.py, data/scommesse_carta.json, vuoto fino al 29/11). Opzioni nascosta (OPZIONI_ON = false).
- Nuova pagina Scanner; test tests/test_scanner.py, tests/test_scommesse.py; suite 488 OK; data/scanner.json ricalcolato.

## Prossima azione
Revisione del coordinatore, commit, deploy e verifica sul sito.
