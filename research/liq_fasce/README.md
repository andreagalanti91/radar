# Fasce di liquidazione + S/R come zone d'ingresso · studio del 13/11/2026 · NON ADOTTARE

**Domanda dell'utente**: il prezzo va verso le liquidazioni e le attraversa: si possono usare le fasce di liquidazione (da sole o
insieme a supporti/resistenze) come zone d'ingresso per W3 e per l'intraday? Spunto: cascata del 13/11 (Coinglass 1h $550M,
24h $1,25B, quasi tutti long).

**Verdetto**: no. Le fasce descrivono bene DOVE è passata la cascata, ma non danno un vantaggio d'ingresso. Sui long W3 un
limit sulla fascia peggiora tutto (59k contro 78k): dopo un segnale W3 il prezzo di solito sale e il limit si riempie solo 3
volte su 9. La presa di metà sulla fascia di short sopra taglia le code destre (40k). Dopo una cascata oraria né la
continuazione fino alla fascia successiva né il rimbalzo su fascia+supporto battono il caso dopo i costi. Il "tocco" più
frequente delle fasce dopo una cascata dipende solo dalla volatilità: a pari volatilità è identico a una distanza qualsiasi.
W3 invariata. Preregistrazione: PREREG.md (6 regole, soglie scritte prima).

## 1 · La cascata del 12–13/11 (descrittivo, mappa ricalcolata alla vigilia con radar/liqmap)
- **Fase A** 12/11 11:00–15:00 UTC: da 73.464 a 71.255 (−3,0%). Alla vigilia la mappa aveva il cluster long più grande a
  72.243 ($138M, dentro la R1 71.997–76.000): attraversato. La discesa si ferma prima della fascia successiva (70.992).
- **Fase B** 13/11 00:00–05:00: da 71.460 a **67.568** (−5,4%), ore peggiori 03:00 (−1,8%) e 05:00. Squilibrio alla vigilia
  −75% entro ±5% (long sotto $390M, short sopra $54M). Attraversate tutte e quattro le fasce dense sotto: 70.499 ($102M),
  69.624 ($65M), 68.932 ($81M), 67.907 ($63M), circa $310M stimati (solo Binance USDT-M). Si ferma nella metà bassa del supporto
  S1 66.956–70.080, sopra la fascia successiva 66.731 ($49M), che non viene toccata.
- **Dopo** (ultima ora chiusa 06:00, prezzo 69.074): sotto restano 66.817 (−3,3%, $53M) e 66.153; sotto la S1 c'è la S2
  62.275–65.000. Sopra la mappa è quasi vuota fino a 74.000–75.500 (+7/+9%, dentro la R1). Squilibrio ±5% −94%: quasi
  niente short da liquidare vicino.
- Eventi reali registrati dal radar (OKX, Gate, dYdX, Deribit; mancano Binance/Bybit/Hyperliquid): $74M long in 6 ore, circa due terzi
  sotto 69.000 e $26M nella fascia 67.500–68.000 (il minimo). Ora peggiore 05:00 con $42M contro $484M di Coinglass: il radar
  vede meno del 10% del totale, la parte mancante è soprattutto Binance/Bybit.

## 4 · Livelli reali on-chain (Hyperliquid + Lighter, conti ≥ $1M; descrittivo)
- Fotografia 13/11 00:11 (mid 71.372): $247M di long liquidabili entro −15%; **$143M nelle fasce poi attraversate** (13
  posizioni, tutte Hyperliquid), la più grande 68.750 ($67M). Alle 07:02 fra 67.500 e 71.500 restano $2,5M: circa $128M sono
  spariti (liquidati, chiusi o con margine aggiunto: la fotografia non distingue).
- Fase A: $84M nelle fasce 71.250–71.750, toccate appena (minimo 71.255).
- Ora entro −5% restano $22M, entro −10% $68M; sopra, entro +10%, nessuno short liquidabile dei grandi conti.
- Limite: le fotografie arrivano ogni 2–5 ore e non ogni ora (12 in due giorni): servono più fotografie per il test di
  research/liq_onchain (gennaio 2027).

## 2 e 3 · Regole testate (10k, 1x, costi inclusi; IS 2021–23, OOS 2024→)
| Regola | 2021→ capitale | DD | MAR | 2021–23 | 2024→ | Placebo / caso | Esito |
|---|---|---|---|---|---|---|---|
| **W3 com'è** (riprodotta: 13 trade, WR 92%) | **78.474** | −21,1% | 32,4 | 33.477 | 23.488 | — | riferimento |
| Buy & hold | 24.314 | −76,6% | 1,9 | 14.387 | 16.143 | — | — |
| R1 limit su prima fascia long sotto, 3 giorni | 59.158 | −21,1% | 23,3 | 27.057 | 21.908 | 63° perc. su distanze casuali | no |
| R1 vicini (N 1/7 giorni; sig 0,2/0,5) | 54.722–69.433 | −21/−23% | 19,8–28,1 | tutti < W3 | tutti < W3 | 0/4 sopra W3 | no |
| R2 limit su fascia + supporto | 61.882 | −21,1% | 24,6 | 28.729 | 21.583 | riempito 0/9 | no |
| R3 metà venduta sulla fascia short sopra | 39.739 | −15,0% | 19,8 | 21.918 | 18.150 | 100° perc. su livelli casuali | no (taglia le code) |
| R4 continuazione dopo cascata long, H 24 h (proxy, 345) | 3.074 | −74,5% | <0 | −0,37%/trade | −0,23%/trade | caso −0,20%, p 0,78 | no |
| R5 rimbalzo su fascia + supporto, H 24 h (33) | 9.513 | −20,5% | <0 | −0,58%/trade | +0,57%/trade | caso p 0,50; livelli casuali p 0,68 | no |

Dettagli:
- **R1/R2**: prezzo d'ingresso medio +3,4% (R1) e +2,8% (R2) PEGGIORE di W3: 6 limit su 9 scadono e si compra più in alto (2021-02
  +13,7%, 2023-10 +15,0%, 2024-02 +7,2%). Nessun trade perso. Senza il trade migliore: R1 43.091 contro 51.561 di W3.
  Placebo (a) su tutti i 2.116 giorni: il limit in fascia compra in media +0,13% meglio del mercato contro +0,07% a distanze casuali
  (97° percentile; 82° nel 2021–23, 99° dal 2024): effetto di 6 centesimi di punto, sotto la soglia nel 2021–23. Riempiti +2,5%,
  non riempiti −2,7%: il limit guadagna quando il prezzo scende e perde quando sale, cioè proprio sui segnali W3.
- **R3**: la fascia short più vicina è a pochi punti percentuali e si riempie entro 1–3 giorni in 9 long su 9: equivale a
  dimezzare la posizione quasi subito. DD più basso ma MAR 19,8 contro 32,4 (lezione 73). Diversa da d2 (studio 03/11, metà
  venduta vicino a un grande cluster LONG sotto, cioè gestione del rischio: 142k contro 122k su W2+MACD, su carta): R3 non la
  sostituisce e non la conferma.
- **R4**: 0/2 metà positive, 0/4 orizzonti positivi sulla cascata long; vicini k 2/4: k 4 appena positivo (+0,05%), k 2 negativo.
  Liquidazioni reali Binance coin-margined (31 cascate long 2023-06→2024-10): −0,53%/trade a 24 h. Tocco della fascia entro 4 h
  25,5% contro 14,3% di un'ora qualsiasi alla stessa distanza, ma 25,7% alla stessa distanza dopo ALTRE cascate: la "calamita"
  è solo volatilità (conferma la lezione 81 anche a 1 ora). Cascate short: n 53, segni opposti fra le metà.
- **R5**: le cascate esaurite SENZA confluenza rendono di più (+0,47%, n 105) di quelle su fascia+supporto (−0,09%):
  la confluenza non aggiunge nulla (conferma lezioni 77 e 81). Lato short: 5 eventi, insufficiente.

## Proposta (solo ciò che regge)
- Nessuna regola nuova per W3 né per l'intraday; W3 resta com'è, con ingresso a mercato il lunedì.
- Dashboard (pagina Liquidazioni, solo contesto): dopo una cascata mostrare "fasce attraversate" e "prossima fascia densa
  sotto/sopra con S/R vicino", come lettura descrittiva di quanta leva è stata pulita (lezione 90), con la scritta che non è
  un segnale. Utile anche il confronto con i livelli reali Hyperliquid spariti (oggi $128M).
- Dati: portare il registratore on-chain (radar/liqsnap.py) a una fotografia davvero oraria, altrimenti il test di gennaio
  2027 non raggiungerà il campione minimo.

## Limiti
- 9 long W3 dal 2021: per D2 la potenza è bassissima; il risultato contrario è però coerente in tutti i vicini e nel placebo (a).
- Mappa = stima su Binance USDT-M (leve e lati supposti); riempimenti su candele 1h perp per un'esecuzione spot (base ~0,05%).
- Proxy delle cascate validato a ρ 0,61 (giornaliero); liquidazioni reali solo coin-margined 2023-06→2024-10 (31+9 eventi).

## File
`PREREG.md` · `lf_data.py` (candele + OI, mappe giornaliere, cache in /tmp/radar-work/liqfasce) · `q1_q4_evento.py` ·
`q2_w3.py` · `q3_cascate.py` · `risultati.txt` (output dei tre script uniti) · `evento_fasce_A.csv`, `evento_fasce_B.csv` ·
`q2_varianti.csv`, `q2_trades.csv`, `q2_giorni.csv` (placebo a) · `q3_sintesi.csv`, `q3_eventi.csv`.
