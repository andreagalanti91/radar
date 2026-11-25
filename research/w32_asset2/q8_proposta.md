
Per anno lo screener sceglie da 0 (2022: sulla storia di 1,6 anni nessuna delle 44 idonee passa insieme i criteri 1, 2, 3 e 5) a 8 asset; a parte BTC ed ETH, le scelte
perdono quasi sempre l'anno dopo (2023: BCH −38%, LTC −40%, SNX −40%; 2024: ZRX −46%, REN −38%, WAVES −23%). Dal 2022 il conto
screener chiude a 8.535 $ contro 22.762 $ di BTC + ETH e 11.198 $ di "tutte le idonee". I risultati **non giustificano** uno
screener che sceglie dove mettere capitale.

### Proposta: "motore di ricerca settimanale" (progetto, nulla da costruire ora)
**Cosa calcolerebbe ogni domenica** (dopo la chiusura UTC, stesso giro di W3.2): per ogni perp USDT con storia ≥ 1 anno sulle liste
Bitget/OKX (oggi ~140 crypto con dati Binance; azioni escluse da Q3): le condizioni di W3.2 alla candela chiusa (regime SMA 40/EMA 20,
lato della EMA 21, flusso perp pf14z a 3 giorni, filtro MACD, distribuzione), lo stato di BTC (cancello di Q4), la posizione
simulata, e la scheda storica dell'asset con W3.2 dal suo inizio: CAGR/DD contro il buy & hold, DD, WR, trade, p del placebo.
**Criteri** (gli stessi di questo studio, fissi): 1 CAGR/DD > B&H · 2 DD ≥ −35% · 3 WR ≥ 60% · 4 IS e OOS positivi · 5 ≥ 8 trade,
più conferma e placebo con Holm sul numero di asset nella lista. Un asset "candidato" produce solo un avviso di revisione, mai
un'operazione.
**Cosa mostrerebbe**: una tabella "Asset in condizione W3.2 questa settimana" (lato, nuovo segnale sì/no, concordanza con BTC) e una
"scheda qualità" ordinata per CAGR/DD storico con i criteri superati; in evidenza BTC, ETH e gli eventuali candidati approvati.
**Costo in dati**: archivio pubblico `data.binance.vision` (klines giornaliere spot e perp con taker buy, funding) per ~140 simboli:
~420 file al giorno da pochi kB (~3–5 MB a settimana), scaricabili anche dal runner USA (l'archivio non è bloccato come fapi);
liste strumenti Bitget/OKX una volta a settimana. Calcolo: ~140 simulazioni W3.2 + placebo ≈ 1–2 minuti. Nessun costo monetario.
**Se i risultati lo giustificano**: no per la scelta degli asset (Q8 negativo, Q1–Q5 danno un solo candidato in 79). Al massimo una
pagina informativa di sola lettura ("chi è in condizione W3.2"), utile come contesto e per accumulare un registro dal vivo; da
decidere con l'utente, nessuna modifica al tool senza approvazione.
