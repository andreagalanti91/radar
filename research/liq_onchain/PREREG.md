# Preregistrazione · cluster REALI di liquidazione on-chain (Hyperliquid + Lighter): calamita o supporto? (11/11/2026, scritta PRIMA dei dati)

Da eseguire non prima del 2027-01-15 e comunque solo quando è raggiunto il campione minimo (sotto). Nessuna regola qui si cambia
dopo aver visto i risultati; ogni deviazione si scrive in fondo, datata, PRIMA di guardare gli esiti.

## Dati
- Fotografie orarie di `radar/liqsnap.py` (data/liqsnap/{hl,lighter}_YYYY-MM.csv.gz): fasce k dello 0,25% del prezzo di
  liquidazione relativo al prezzo medio Hyperliquid `mid` dell'ora (k da −60 a 59 = ±15%), $ long (sotto) e short (sopra), n conti.
  Fonti: Hyperliquid (whalebot + 80 conti più grandi ogni ora, tutti i conti ≥ $1M della classifica a rotazione ogni 6 h, i conti
  con ≥ $1M di BTC liquidabile entro ±20% ogni ora; letture tenute al massimo 6,5 h) e Lighter (conti ≥ $1M, stessa logica).
  Analisi principale = somma HL + Lighter; HL da solo come controllo.
- Prezzo: candele orarie BTCUSDT spot Binance (data-api.binance.vision), massimo/minimo dell'ora; riserva OKX BTC-USDT-SWAP.
- Si usano solo le ore con riga di copertura (data/liqsnap/coverage_*.csv) e `read ≥ 0,5 × target` per HL; ore mancanti NON si
  ricostruiscono. Una fotografia al giorno: la prima ora registrata dopo le 00:00 UTC (eventi indipendenti per giorno).

## Definizioni (congelate)
- Cluster = `radar/liqsnap.clusters` con i parametri attuali: picco della somma su 3 fasce adiacenti, ≥ $2M e ≥ 20% del picco più
  grande dello stesso lato entro ±15%. Livello L = prezzo al centro della fascia di picco, distanza d = L/mid − 1.
- Evento T1/T3 = il cluster più vicino per lato (sotto = long da liquidare, sopra = short da liquidare), con |d| fra 1% e 10%.
- Tocco = entro H il minimo orario ≤ L (lato sotto) o il massimo ≥ L (lato sopra), partendo dall'ora dopo la fotografia.
- Orizzonti H = 1, 3, 7 giorni.

## Test
T1 · calamita (6 test: lato × H). Tasso di tocco dei cluster contro il controllo a pari distanza: probabilità di toccare un livello
alla STESSA distanza d sullo stesso lato partendo da un'ora qualsiasi del 2024-01 → oggi (stima empirica sulle candele orarie,
escluse le ore del periodo di test). Effetto = tasso − controllo (punti %). Test binomiale a una coda sul conteggio dei tocchi
con p = media dei controlli degli eventi.
T2 · rimbalzo / rottura (2 test: lato sotto e sopra, solo eventi toccati entro 7 giorni). Rimbalzo = nei 24 h dopo il primo tocco
nessuna chiusura oraria oltre L di più dello 0,5% E il prezzo torna ad almeno +1% da L dal lato di partenza; rottura altrimenti.
Controllo = stesso calcolo sul primo tocco di un livello casuale alla stessa distanza d (per ogni evento 20 date casuali dal
2024-01 in poi, stesso lato). Effetto = tasso di rimbalzo − controllo; test di permutazione (5.000) dell'etichetta cluster/controllo.
T3 · peso (1 test, H = 3 giorni): fra gli eventi, i cluster più grandi (usd sopra la mediana) hanno tasso di tocco − controllo più
alto dei più piccoli? Permutazione (5.000).

## Campione minimo prima di giudicare
- ≥ 60 giorni di fotografie valide e ≥ 40 eventi per lato per T1 (con H = 7 giorni gli eventi sovrapposti contano una volta: si
  scartano gli eventi il cui livello è lo stesso (±0,5%) di quello del giorno prima e non è stato ancora toccato).
- ≥ 30 tocchi per lato per T2. Sotto queste soglie il verdetto è "insufficiente", non "non funziona".

## Criterio
Per ogni test: effetto ≥ 5 punti, p < 0,05 e stesso segno nelle due metà del periodo (prima/seconda metà dei giorni).
Famiglia T1 "funziona" solo se passa ≥ 4/6; T2 se passa ≥ 1/2 col segno "rimbalzo" (supporto) o ≥ 1/2 col segno "rottura"
(la direzione si dichiara come risultato, non si sceglie). Se nulla passa: i livelli reali restano contesto sulla dashboard,
non entrano in W2 + MACD, come la mappa stimata (lezione 81).

## Limiti dichiarati in anticipo
- Copertura parziale: solo conti ≥ $1M (al 11/11/2026: ~23% long / ~34% short dell'OI BTC Hyperliquid, ~50–70% di Lighter);
  i prezzi di liquidazione cross cambiano col PnL degli altri asset del conto; fra due letture (≤ 6 h) una posizione può essere
  chiusa. Le posizioni senza prezzo di liquidazione (conti molto capienti) non entrano nelle fasce.
- Gli eventi di giorni vicini sono correlati (stessi conti): per questo una fotografia al giorno e lo scarto dei livelli ripetuti.
