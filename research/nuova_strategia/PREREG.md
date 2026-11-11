# Nuova strategia settimanale/mensile su BTC — preregistrazione (11/11/2026, prima di qualsiasi risultato)

Richiesta: settimanale o mensile, controllo dei volumi, supporti e resistenze, massimo profitto con minimo drawdown,
capire la direzione del mercato; backtest dal 2021; report su file.

## Dati
BTC giornaliero dal 2011 (Bitstamp → Binance spot → dati del tool), con volume. Candele settimanali (chiusura domenica UTC).
Nessun dato di flusso perp (quindi nessuna dipendenza dal "flusso del sabato/domenica" trovata nella revisione).

## Metodo (per non ingannarsi)
- SCELTA delle regole e dei parametri solo sul 2014-01-01 → 2020-12-31. GIUDIZIO sul 2021-01-01 → oggi, una volta sola.
- Decisione alla chiusura settimanale, esecuzione all'apertura del lunedì; stop controllati ogni giorno sui minimi (gap = apertura).
- Costi 0,1% commissione + 0,1% slippage per lato. Solo long in spot (gli short dedicati hanno già fallito, lezione 80), 1x.
- Tetto di rischio R = 25% del capitale allo stop iniziale: esposizione = min(1, 0,25 / distanza dello stop) (rischio scoperto
  trovato dalla revisione: long vicino a un top).
- Controlli obbligatori sul candidato scelto: parametri vicini, i 7 giorni di chiusura della settimana (la revisione ha mostrato
  che W2 dipende dalla domenica), senza il trade migliore, confronto con buy & hold e con W2 (118,6k; "come dal vivo" 103k).

## Mattoni (stati long/flat settimanali)
- **S · Struttura (supporti e resistenze)**: massimi e minimi swing settimanali confermati (frattale k=3). Long quando la chiusura
  supera l'ultima resistenza confermata (ultimo massimo swing); uscita quando la chiusura rompe l'ultimo supporto confermato
  (ultimo minimo swing). Lo stop iniziale è il supporto.
- **D · Canale (resistenza/supporto a N settimane)**: long alla chiusura sopra il massimo delle 20 settimane precedenti; uscita
  alla chiusura sotto il minimo delle 10 settimane precedenti.
- **V · Volume (prezzo medio pesato per i volumi)**: long quando la chiusura è sopra il VWAP a 26 settimane e il VWAP sale;
  uscita alla chiusura sotto il VWAP.
- **B · Bilancio dei volumi**: volume delle settimane in rialzo / volume delle settimane in ribasso sulle ultime 13 settimane.
  > 1 = accumulo, < 1 = distribuzione. Usato come filtro d'ingresso e come uscita se scende sotto 0,8.

## Le 8 varianti
- N1 = S (struttura pura) · N2 = S con filtro B all'ingresso · N3 = D (canale 20/10) · N4 = D con filtro B
- N5 = V (VWAP 26 settimane) · N6 = V con uscita anche su B < 0,8
- N7 = voto: esposizione = (numero di stati long fra S, D, V) / 3 (ingresso e uscita graduali, nessun parametro in più)
- N8 = mensile: chiusura mensile sopra il VWAP a 10 mesi e bilancio dei volumi a 6 mesi > 1; uscita alla chiusura mensile sotto.

## Criterio di scelta (sul 2014–2020) e di giudizio (2021→oggi)
Scelta: MAR (rendimento annuo / max drawdown giornaliero) più alto con almeno 6 trade e drawdown ≤ 45% nel 2014–20.
Giudizio: nel 2021→oggi MAR > buy & hold, drawdown ≤ 30%, positiva nelle due metà (2021–23, 2024→oggi), mediana dei vicini
e dei 7 giorni di chiusura almeno al 60% del risultato scelto, positiva senza il trade migliore.
Se non passa, lo si dice: niente va nel tool senza un ordine dell'utente (ha chiesto di non eseguire modifiche).
