# STATO · Sezione Notizie su misura · avviato 25/11/2026

Stato: IN DEPLOY

## Prompt originale
"Nascondi 'opzioni' la riprendiamo successivamente. Realizza meglio la sezione notizie in base a ciò che fa per noi"

## Decisioni
- Opzioni: nascoste dalla dashboard (flag), calcolo e archivio continuano; affidato all'agente dello Scanner.
- Notizie "per noi" = ciò che tocca W3.2 su BTC ed ETH, TRX in osservazione e le preferite: eventi in calendario prima della
  decisione della domenica, notizie che toccano le posizioni aperte, il resto in secondo piano. Nessun avviso Telegram nuovo.
  Moduli: radar/news.py (fetch_news, fetch_calendar, fetch_central_banks), renderNews e todayN in dashboard_template.html.

## Prossima azione
Alla consegna dello Scanner: agente (Opus 5.5 medium) per la sezione Notizie; poi suite, render, deploy, verifica.

## Fatto (25/11)
radar/news.py con punteggio di rilevanza spiegato (asset seguiti, temi, parole forti, doppioni, cache se una fonte non risponde); pagina Notizie: Prima della decisione di domenica, Notizie che toccano le posizioni per tema, Altre notizie chiuse; Oggi con riassunto; report["news_fonti"] in cli.py. Suite 506 test.
