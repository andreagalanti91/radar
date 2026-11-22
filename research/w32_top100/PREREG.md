# w32_top100 · W3.2 sulle prime 100 crypto per capitalizzazione — PREREGISTRAZIONE (22/11/2026)

Scritto e committato da solo PRIMA di scaricare i prezzi e di calcolare qualsiasi rendimento. Finora è stata verificata solo la
DISPONIBILITÀ dei simboli su Binance (`universe.py`, nessun prezzo letto). Test di TRASFERIBILITÀ: stessi parametri di BTC
ovunque, nessun adattamento per moneta.

## Universo (fonte e data)
- Fonte: API pubblica CoinGecko `/coins/markets?vs_currency=usd&order=market_cap_desc`, scaricata il 22/11/2026 (file
  `data/raw/cg_top.json`), prime 100 per capitalizzazione.
- Esclusi (28): stablecoin della categoria CoinGecko `stablecoins` (19: USDT, USDC, USDS, USDE, DAI, RLUSD, USD1, USDG, PYUSD,
  USDF, U, USDD, BFUSD, USDGO, OUSD, GHO, USD0, EURC, TUSD), oro tokenizzato (XAUT, PAXG), fondi tokenizzati/RWA a valore quasi
  costante (FIGR_HELOC, USDY, EURSAFO, USYC, BUIDL, USTB, JAAA). Token wrapped/staked/bridged (WBTC, stETH, weETH…): verificate le
  categorie CoinGecko `wrapped-tokens`, `liquid-staking-tokens`, `liquid-restaking-tokens`, `bridged-tokens`: nessuno nelle prime
  100 di oggi. Nessun rimpiazzo: restano 72 monete.
- Binance (coppia `<TICKER>USDT`): 57 hanno perp USDT-M nell'archivio data.binance.vision (1000SHIB, 1000PEPE con prezzi /1000;
  CC, M, VVV, BTW, PIEVERSE, KAS senza spot → prezzo dal perp); 1 solo spot (NEXO); 14 senza dati Binance (LEO, WBT, RAIN, CRO,
  OKB, HTX, MNT, BGB, KCS, PEARL, GT, PI, BDX, XDC: token di exchange o non quotati) → esclusi come dato mancante.
- Ticker: GRAM (Toncoin) = TON su Binance; POL e RENDER si raccordano 1:1 con i vecchi ticker MATIC e RNDR (storia precedente
  dal vecchio simbolo, solo per le date che il nuovo non copre).
- **Bias di sopravvivenza**: la top 100 di oggi contiene per costruzione le monete sopravvissute e cresciute; i buy & hold sono
  gonfiati e le monete morte dal 2021 (LUNA, FTT…) mancano. Il test misura se W3.2 batte il B&H SULLE STESSE monete, non se
  avrebbe guadagnato su un universo scelto nel 2021.

## Regole (nessuna ottimizzazione)
- **W3.2 completa** (57 con perp): `radar.weekly.simulate` invariato, R_LONG = R_SHORT = 0,25, stop/trailing 2,5 ATRw, W-SUN,
  costi e funding di weekly.py. Dati: spot 1d da data-api.binance.vision (dal 01/09/2019), perp 1d con taker buy e funding
  dall'archivio data.binance.vision (mensile fino a 10/2026 + giornaliero 1–10/11/2026); prezzo = spot, perp dove manca lo spot;
  pf14z = z-score 180 g di Σ(2·taker_buy − vol)/Σvol su 14 g (identico a top10_w3/run.py `feats`). Inizio =
  max(01/01/2021, primo pf14z valido + 200 g). Fine **10/11/2026** (come w32_multi). Verifica: BTC con questi dati = 78.474 $.
- **W3.2 solo prezzo** (solo spot, NEXO): `ma_lib.s1_sim`, W-SUN, rischio 0,25, 0,2% per lato, short 10%/anno; inizio =
  max(01/01/2021, primo dato + 300 g per le medie settimanali). Riportata in una tabella separata.
- Buy & hold: apertura del primo giorno di test → chiusura del 10/11/2026, costo 0,2% per lato.

## Criterio "passa" per moneta (dal suo inizio, rischio 25%) — TUTTE le condizioni (= w32_multi)
1. CAGR/DD > CAGR/DD del buy & hold dello stesso periodo; 2. max DD giornaliero ≥ −35%; 3. win rate ≥ 60%;
4. rendimento positivo in entrambe le metà (ciascuna simulata da flat): 2021–23 e 2024→fine se l'inizio è ≤ 31/12/2022,
   altrimenti metà del periodo di test; 5. ≥ 8 trade (posizione aperta inclusa, valutata alla chiusura).
- **Valutabili**: solo le monete con almeno 3 anni di test (inizio ≤ 10/11/2023). Le altre si riportano a parte, fuori dai conteggi.
- **Conferma di robustezza** (per chi passa 1–5): senza il trade migliore finale > 10.000 $; con stop/trailing 2,0 o 3,0 ATRw
  CAGR/DD > B&H in almeno uno dei due.
- **Placebo** (per chi passa 1–5): stesso metodo di w32_multi/placebo.py (stessi trade per durata, lato, esposizione, in date
  casuali non sovrapposte, 2000 prove, seme 7), p = (k+1)/(2000+1); **correzione di Holm** a α = 0,05 sul gruppo delle monete
  che passano 1–5. "Passa davvero" = 1–5 + conferma + placebo significativo dopo Holm.

## Verdetto (fissato prima) — altcoin valutabili con perp, BTC escluso dal denominatore (N)
- **"Si trasferisce alle altcoin"**: passano davvero ≥ 50% di N.
- **"Parziale"**: passano davvero tra il 20% e il 50% di N.
- **"Non si trasferisce"**: passano davvero < 20% di N.
La versione solo prezzo (1 moneta) è solo descrittiva. Una moneta che passa è un candidato da osservare, non un'aggiunta al tool.

## Rapporto
Conteggi (testate, con perp, valutabili, passano 1–5, conferma, Holm); migliori 15 e peggiori 5 per CAGR/DD (finale su 10k, DD,
trade, WR, B&H); distribuzione (quantili di finale e di CAGR/DD − B&H, quante battono il B&H). Portafogli equipesati (quote
indipendenti, senza ribilanciamento, liquidità prima dell'inizio, dal 01/01/2021): (a) tutte le valutabili con perp — onesto;
(b) solo quelle che passano — SCELTO A POSTERIORI, distorto; confronto con BTC da solo e con il B&H equipesato delle stesse.
Nessuna variante oltre a queste (rischio 25%, vicini 2,0/3,0 solo per la conferma).
