# Supertrend di TradingView (ATR 10, fattore 3) su BTC a 4h, 1D, 1W · da solo e dentro W3.2 · 23/11/2026

PREREG: commit `24d63a0` (da solo, prima di ogni rendimento). Parametri 10/3 fissi, mai scelti sui dati.

## Verdetto
**Il Supertrend non è una strategia valida e non migliora W3.2: nessuna modifica.** 0 oggetti su 11 superano i criteri (S1–S4),
0 varianti su 4 migliorano W3.2 (K1–K4), 0 su 7 su ETH; nella mappa dei parametri 0 combinazioni su 176 passano i tre periodi.
- **S1 inversione long/short**: 4h 16.215 $ (DD −61%, 293 trade), 1D **3.477 $** (DD −84%), 1W 24.363 $ (DD −83%) dal 2021,
  contro 78.474 $ (DD −21%) di W3.2 e 22.549 $ (DD −77%) del buy & hold. Non valida.
- **S2 solo long**: 4h 22.653 $ (−46%), 1D 13.807 $ (−54%), 1W 30.642 $ (−63%, 3 trade). È il solito "trend long/flat ≈ buy &
  hold con meno drawdown" (lezioni 83, 117): nessun periodo con DD entro −35%. Non valida.
- **S3 solo short**: perde su tutti gli intervalli (7.158 $, 2.518 $, 7.951 $). Non valida.
- **S4 multi-intervallo**: 1W + 1D 13.727 $ (−57%); 1D + 4h 10.209 $ (−59%). Non valida; il lato short perde in entrambe.
- **K1** (Supertrend 1W al posto del trailing): 73.584 $ (−23%) e 2018–20 a 18.105 $ (−52%) contro 25.142 $ (−37%). Peggiora:
  il cambio 1W non scatta mai prima delle uscite di W3.2 (0 uscite su 22 trade), si perde solo il cricchetto.
- **K2** (uscita al cambio 1D): 36.604 $ (−38%), WR 52%. Peggiora molto (placebo p 0,93: peggio di un'uscita a caso).
- **K3** (filtro d'ingresso 1D): 62.660 $ (−22%). Peggiora: ritarda 3 ingressi buoni.
- **K4** (uscita al cambio 4h): 45.154 $ (−26%), 40 trade, WR 48%. Peggiora (meglio solo nel 2024–26: non basta).

## Come strategia a sé (10.000 $ per periodo, 1x, costi e funding inclusi; fra parentesi il drawdown)
| 10/3 | 2018–20 | 2021–23 | 2024–26 | Intero 2021–26 | Trade (WR) 2021–26 | p sfasati | p blocchi |
|---|---|---|---|---|---|---|---|
| S1 inversione 4h | 28.599 $ (−47%) | 21.061 $ (−61%) | 7.699 $ (−53%) | 16.215 $ (−61%) | 293 (38%) | 0,003 | 0,10 |
| S2 solo long 4h | 33.384 $ (−44%) | 20.263 $ (−46%) | 11.180 $ (−41%) | 22.653 $ (−46%) | 146 (38%) | 0,005 | 0,02 |
| S3 solo short 4h | 8.567 $ (−55%) | 10.394 $ (−43%) | 6.887 $ (−42%) | 7.158 $ (−63%) | 147 (38%) | 0,006 | 0,24 |
| S1 inversione 1D | 58.522 $ (−52%) | 5.938 $ (−78%) | 5.856 $ (−71%) | 3.477 $ (−84%) | 55 (35%) | 0,050 | 0,82 |
| S2 solo long 1D | 40.658 $ (−46%) | 13.456 $ (−54%) | 10.261 $ (−47%) | 13.807 $ (−54%) | 27 (41%) | 0,052 | 0,72 |
| S3 solo short 1D | 14.394 $ (−41%) | 4.413 $ (−67%) | 5.707 $ (−64%) | 2.518 $ (−84%) | 28 (29%) | 0,057 | 0,76 |
| S1 inversione 1W | 23.430 $ (−72%) | 11.581 $ (−83%) | 21.037 $ (−33%) | 24.363 $ (−83%) | 6 (50%) | 0,066 | 0,14 |
| S2 solo long 1W | 23.366 $ (−53%) | 16.966 $ (−63%) | 18.061 $ (−40%) | 30.642 $ (−63%) | 3 (33%) | 0,102 | 0,16 |
| S3 solo short 1W | 10.027 $ (−56%) | 6.826 $ (−65%) | 11.648 $ (−17%) | 7.951 $ (−65%) | 3 (67%) | 0,110 | 0,12 |
| S4a regime 1W + 1D | 30.277 $ (−50%) | 11.960 $ (−57%) | 11.477 $ (−41%) | 13.727 $ (−57%) | 30 (37%) | 0,077 | 0,40 |
| S4b regime 1D + 4h | 38.037 $ (−39%) | 14.765 $ (−51%) | 6.914 $ (−59%) | 10.209 $ (−59%) | 174 (39%) | 0,018 | 0,66 |
| Buy & hold | 21.046 $ (−81%) | 14.590 $ (−77%) | 15.425 $ (−53%) | 22.549 $ (−77%) | 1 | | |
| **W3.2** (ha visto tutto il 2021–26) | 25.142 $ (−37%) | 33.477 $ (−19%) | 23.488 $ (−21%) | **78.474 $ (−21%)** | 13 (92%) | | |

- **Criteri** (CAGR > 0, CAGR/DD sopra il buy & hold, DD ≥ −35%, positivo senza i 2 trade migliori, in tutti e tre i periodi):
  nessun oggetto passa nemmeno un periodo intero, salvo S1 1W nel solo 2024–26 (2 trade). Il DD ≥ −35% manca in 31 casi su 33;
  senza i 2 trade migliori restano positivi solo 5 casi su 33 (il guadagno sta in 1–2 trend per periodo).
- **Il 2018–20 inganna**: tutte le versioni long battono il buy & hold in quel periodo (S1 1D 58.522 $), poi dal 2021 l'inversione
  giornaliera perde il 65% del capitale. Stesso schema dello studio sulle medie (lezione 117).
- **Placebo**. Cambi sfasati (1.000 traslazioni; soglia 0,0045): passa solo S1 4h (p 0,003), che però fallisce tutti gli altri
  criteri; S2 4h 0,005; 1D e 1W 0,05–0,11. Prezzi rimescolati a blocchi di 20 giorni (300 serie): il Supertrend 1D fa PEGGIO che
  sulle serie rimescolate (p 0,72–0,82), 1W p 0,12–0,16, solo S2 4h 0,02. La direzione segue il trend (vantaggio generico), il
  momento del cambio non aggiunge nulla.
- **Con il tetto di rischio 25%** (esposizione e stop di protezione come W3.2): 2021–26 S1 20.368 / 7.061 / 36.084 $ (4h/1D/1W, DD
  −46/−70/−67%), S2 24.201 / 15.376 / 30.968 $ (−38/−45/−60%), S3 8.416 / 4.592 / 11.652 $, S4a 16.435 $ (−47%), S4b 12.916 $
  (−53%). Nessuna passa i tre periodi (S2 4h ne passa due: 2018–20 e 2021–23; nel 2024–26 fa 11.608 $ contro 15.425 $).

### Mappa dei parametri (ATR 7/10/14/21 × fattore 2/2,5/3/4; S = CAGR/DD sull'intero 2018–26; buy & hold 0,24)
| | S di 10/3 | Rango su 16 | Min–max dei vicini | Mediana griglia | Sopra il b&h (su 16) | Zona stabile | Passano i 3 periodi |
|---|---|---|---|---|---|---|---|
| S1 4h | 0,31 | 6° | 0,05–0,38 | 0,18 | 8 | sì | 0 |
| S2 4h | 0,55 | 6° | 0,27–0,63 | 0,41 | 12 | sì | 0 |
| S3 4h | −0,07 | 7° | −0,13–−0,02 | −0,10 | 0 | sì (sempre negativa) | 0 |
| S1 1D | 0,10 | **16°** | 0,18–0,64 | 0,38 | 11 | **no** | 0 |
| S2 1D | 0,40 | 14° | 0,43–0,83 | 0,56 | 16 | no (sotto tutti i vicini) | 0 |
| S3 1D | −0,12 | 16° | −0,08–0,04 | −0,02 | 0 | no | 0 |
| S1 1W | 0,26 | 2° | −0,55–0,34 | 0,01 | 4 | **no** (picco isolato) | 0 |
| S2 1W | 0,39 | 4° | 0,21–0,44 | 0,30 | 12 | sì | 0 |
| S3 1W | −0,03 | 3° | −0,88–0,00 | −0,16 | 0 | sì (sempre negativa) | 0 |
| S4a | 0,30 | 9° | 0,16–0,51 | 0,31 | 11 | sì | 0 |
| S4b | 0,28 | 10° | 0,34–0,57 | 0,34 | 11 | no | 0 |

Sul giornaliero 10/3 è per caso la cella PEGGIORE della griglia (S1 1D: 20.349 $ sull'intero 2018–26 contro 35.000–212.000 $ dei
vicini): il risultato dipende dal parametro, in entrambi i versi, e nessuna cella regge i tre periodi. Sul settimanale l'inversione
con fattore 4 azzera il capitale (short tenuto per tutto il 2020–21). Gli short non stanno mai sopra il buy & hold (0 celle su 48).
L'unica zona coerente è il solo long (sopra il buy & hold in 40 celle su 48), ma con DD entro −35% solo in 8 celle-periodo su 144.

### ETH (conferma esterna, stessi parametri; solo 1D e 1W: nel repo non ci sono candele 4h di ETH)
| 10/3 su ETH | 2018–20 | 2021–23 | 2024–26 | 2021–26 |
|---|---|---|---|---|
| S1 inversione 1D | 145.348 $ (−56%) | 28.410 $ (−55%) | 9.813 $ (−72%) | 27.878 $ (−77%) |
| S2 solo long 1D | 63.715 $ (−47%) | 39.049 $ (−42%) | 11.208 $ (−54%) | 43.767 $ (−54%) |
| S3 solo short 1D | 22.812 $ (−50%) | 7.275 $ (−47%) | 8.755 $ (−63%) | 6.370 $ (−78%) |
| S1 inversione 1W | azzerato | 4.650 $ (−97%) | 1.499 $ (−92%) | 697 $ (−99%) |
| S2 solo long 1W | 6.670 $ (−87%) | 22.284 $ (−73%) | 4.236 $ (−77%) | 9.439 $ (−84%) |
| S3 solo short 1W | azzerato | 2.087 $ (−91%) | 3.539 $ (−78%) | 739 $ (−95%) |
| S4a regime 1W + 1D | 14.475 $ (−76%) | 17.267 $ (−74%) | 4.721 $ (−79%) | 8.151 $ (−87%) |
| Buy & hold ETH | 10.026 $ (−94%) | 30.924 $ (−79%) | 8.027 $ (−68%) | 24.873 $ (−79%) |
0 su 7 passano. Il giornaliero long va bene fino al 2023 e si ferma nel 2024–26 (11.208 $); il settimanale su ETH è un disastro.
W3.2 ETH 2021–26: 34.760 $ (−27,5%); K1 29.604 $ (−32%), K2 27.886 $ (−30%), K3 31.660 $ (−27,5%): tutte peggiori.

## Dentro W3.2 (ogni periodo da 10.000 $; S = CAGR/DD)
| | 2018–20 | 2021–23 | 2024–26 | 2021–26 | Trade (WR) | Placebo p |
|---|---|---|---|---|---|---|
| **W3.2** | 25.142 $ (−37%; 0,97) | 33.477 $ (−19%; 2,57) | 23.488 $ (−21%; 1,64) | **78.474 $ (−21%; 1,99)** | 13 (92%) | |
| K1 Supertrend 1W al posto del trailing | 18.105 $ (−52%; 0,42) | 33.720 $ (−19%; 2,59) | 21.866 $ (−23%; 1,37) | 73.584 $ (−23%; 1,78) | 13 (85%) | 0,46 |
| K2 uscita al cambio 1D contro | 26.365 $ (−36%; 1,06) | 24.908 $ (−25%; 1,42) | 14.725 $ (−38%; 0,38) | 36.604 $ (−38%; 0,65) | 23 (52%) | 0,93 |
| K3 filtro d'ingresso 1D concorde | 27.128 $ (−37%; 1,06) | 26.731 $ (−22%; 1,73) | 23.488 $ (−21%; 1,64) | 62.660 $ (−22%; 1,64) | 13 (92%) | 0,11 |
| K4 uscita al cambio 4h contro | 22.751 $ (−29%; 1,07) | 20.048 $ (−26%; 0,99) | 22.523 $ (−13%; 2,56) | 45.154 $ (−26%; 1,11) | 40 (48%) | 0,08 |

La copia del motore riproduce radar.weekly al centesimo (78.473,92 $, 13 trade). Criteri: nessuna variante batte W3.2 in entrambi i
periodi 2021–23 e 2024–26 (K1 solo il primo, di 0,02; K4 solo il secondo).
- **K1**: il Supertrend 1W non chiude mai un trade (sta a 30–40% dal prezzo: EMA21, distribuzione e stop arrivano sempre prima).
  Togliendo il cricchetto si perdono le uscite in profitto del 2019 (+51% → +15%) e del 2024–25 (+31% → +24%).
- **K2**: 23 trade invece di 13; i rientri dopo l'uscita comprano più in alto e subiscono 3 stop pieni (−9%, −15%, −22%).
- **K3**: cambia 3 trade su 13 (02/2021 +52% → +38%, 10/2021 +21% → +15%, 08/2022 +8% → +0,4%): aspettare il giornaliero costa.
- **K4**: 40 trade, WR 48%; taglia i trend (come le lezioni 109, 114, 116, 117).
- Descrizione (non preregistrata): sui 22 ingressi di W3.2 dal 2018 il Supertrend 1D era già concorde in 18, il 1W in 15.

## Descrittivo (10/3; 2018 → 22/11/2026)
| | Cambi l'anno (2018–20 / 2021–23 / 2024–26) | Durata mediana di un trend | Invertiti entro 10 barre | Tempo in rialzo |
|---|---|---|---|---|
| 4h | 46 / 48 / 52 | 6 giorni (37 barre) | 11% (entro 3 barre: 0,7%) | 51% / 49% / 50% |
| 1D | 7,0 / 8,7 / 10,0 | 38 giorni | 12% (entro 20 barre: 31%) | 51% / 47% / 52% |
| 1W | 1,3 / 1,3 / 1,0 | 42 settimane (11 cambi in 9 anni) | 1 su 10 | 31% / 53% / 71% |

- I cambi non sono "falsi" a breve (il Supertrend ha un'isteresi larga: 3 ATR), ma arrivano tardi: win rate 35–40% su 4h e 1D.
- **Dopo un cambio il rendimento non differisce dalla media** (eccesso sull'intero 2018–26, p del placebo; soglia 0,0042 su 12 test):
  4h al rialzo −0,05 punti a 7 giorni (p 0,92) e −0,8 a 30 (0,36); 4h al ribasso −1,3 (0,021) e −1,2 (0,17); 1D al rialzo −0,3
  (0,82) e −0,4 (0,88); 1D al ribasso +0,8 (0,55) e −1,5 (0,59); 1W al rialzo +4,7 (0,23) e +18,0 (0,04; 5 casi); 1W al ribasso
  −2,7 (0,43) e +4,3 (0,66). Nessuno supera la soglia. A 1 e 3 giorni, su 4h e 1D, l'eccesso è entro ±3 punti con segno instabile.
- **Lo stato conta un po' più del cambio** (rendimento medio a 30 giorni in rialzo / in ribasso; media del periodo 5,6 / 2,3 / 2,5%):
  1W 13,2 / 2,3 · 2,9 / 1,7 · 3,6 / 0,0; 4h 7,4 / 3,7 · 2,5 / 2,2 · 3,9 / 1,1; 1D 10,6 / 0,5 · **1,9 / 2,7** · 3,0 / 2,1 (segno
  rovesciato nel 2021–23). Differenze piccole, non testate: è lo stesso effetto "sopra la media lenta" della lezione 117.

## Stato attuale (chiusure al 22/11/2026, BTC 61.271 $)
| | Direzione | Linea | Distanza dal prezzo | Ultimo cambio |
|---|---|---|---|---|
| 4h | ribasso | 61.910 $ | +1,0% | candela del 05/11 12:00 UTC a 76.030 $ (−19% da allora) |
| 1D | ribasso | 67.790 $ | +10,6% | 29/10 a 77.992 $ (−21%) |
| 1W | ribasso | 81.980 $ | +33,8% | settimana chiusa il 15/11 a 65.351 $ (−6%) |

I tre intervalli sono al ribasso: **in accordo con lo short di W3.2 aperto il 16/11** (il cambio 1W è arrivato nella stessa
chiusura settimanale del segnale di W3.2). Il 4h è a 1% dalla linea: un cambio al rialzo a 4h è probabile a breve e, per quanto
misurato qui, non dice nulla sullo short (K4: uscire sul 4h rende 45.154 $ contro 78.474 $).

## Il Supertrend serve? Come usarlo?
- **Come segnale: no.** Né inversione, né solo long, né solo short, né multi-intervallo; non come uscita né come filtro di W3.2.
- **Come lettura del grafico: sì, con un limite chiaro.** È un trailing ATR disegnato: dice da che parte sta il trend e dove
  sarebbe lo stop "a 3 ATR". W3.2 ha già la stessa idea, calibrata meglio (2,5 ATR settimanali a cricchetto + EMA21 + flusso).
  Utile solo sul settimanale come conferma visiva del regime; sul 4h cambia una volta a settimana e non va seguito.
- **Avvisi di TradingView sul cambio di direzione**: non usarli per operare. Se si vogliono tenere, solo sul settimanale (1 l'anno).
- **Riga di contesto per la dashboard (facoltativa)**: "Supertrend 10/3 · 4h ribasso · 1D ribasso · 1W ribasso (linea 81.980 $)".
  Dicitura: "Contesto, non segnale. Dal 2018 seguire i cambi del Supertrend ha reso meno di W3.2 con un drawdown da due a
  quattro volte più ampio (win rate 35–40%); dopo un cambio il rendimento non differisce dalla media." Nessuna freccia, nessun avviso.

## Replica dell'indicatore (`st_lib.supertrend`)
TR = max(H − L, |H − C₋₁|, |L − C₋₁|); ATR = RMA di Wilder: alla barra n media semplice delle prime n TR, poi ATR = (ATR₋₁·(n − 1)
+ TR)/n; bande di base hl2 ± fattore·ATR; **banda inferiore finale** = quella di base se è più alta della precedente oppure se la
chiusura precedente era sotto la banda precedente, altrimenti resta la precedente (specchio per la superiore); **direzione**: se
la linea precedente era la banda superiore, −1 (rialzo) quando la chiusura supera la banda superiore, altrimenti +1; se era
l'inferiore, +1 (ribasso) quando la chiusura scende sotto la banda inferiore; linea = banda inferiore in rialzo, superiore in ribasso.
- Controlli (4h, 1D, 1W × 16 combinazioni): seconda implementazione indipendente identica; ATR = ricorsione di Wilder con seme
  SMA; in rialzo la linea non scende e la chiusura le sta sopra (specchio in ribasso); il cambio avviene solo con chiusura oltre
  la banda. Unica eccezione, propria del codice Pine: 2 barre di cambio su 8.362 a 4h (nessuna con 10/3) in cui una candela con
  ombra enorme (16/10/2023, massimo 30.000 $) fa saltare la banda oltre la chiusura e la linea resta una barra dal lato sbagliato.
- Verifica a mano (1D, 29–30/10/2026): 29/10 TR = 81.971 − 77.910 = 4.061; ATR = (1.899,8·9 + 4.061)/10 = 2.115,9; hl2 = 79.940,5;
  bande di base 86.288,3 e 73.592,7; la superiore resta 86.016,9 (86.288 non è più bassa), l'inferiore resta 79.663,5; chiusura
  77.991,9 < 79.663,5 → ribasso, linea 86.016,9. 30/10: superiore 84.021,4 (più bassa → aggiornata), inferiore 71.108,6 (la
  chiusura precedente era sotto → riparte). Coincide con il codice; tabella di 16 barre con `st_lib.hand_table()`.
- **Non confrontato con TradingView dal vivo** (non raggiungibile da qui). Dati Binance spot BTCUSDT; su un altro simbolo o exchange
  i valori differiscono di poco. La linea dipende da dove comincia il grafico finché non avviene un cambio: storia dal 2014 e
  storia solo Binance (dal 08/2017) coincidono sul giornaliero dal 10/10/2017 e sul settimanale dal 13/01/2019 (nel 2018 cambia il
  livello della linea, non la direzione: risultati 2018–20 identici).

## Limiti e deviazioni
- 11 + 4 oggetti e commit della preregistrazione: richiesti dall'incarico (oltre le 8 varianti abituali).
- Nessun confronto dal vivo con TradingView. Short a prezzo spot, funding zero prima del 2020 (favorisce gli short nel 2018–19).
- Periodi come fette di una curva continua (S) o simulazioni separate (W3.2 e K). Settimanale: 11 trade in 9 anni, non
  giudicabile statisticamente. Short a quantità fissa: in 2 celle della mappa e su ETH 1W il capitale va sotto zero ("azzerato").
- K: "cambio contro" è un evento dopo l'ingresso; se si entra con il Supertrend già contrario l'uscita non scatta finché non gira
  due volte (dichiarato prima). K3 "a scadenza" = nuova decisione domenicale (entra solo se il segnale è ancora valido). K4: stop
  controllato sulle candele 4h precedenti dello stesso giorno, funding del giorno d'uscita ignorato.
- ETH: solo 1D e 1W (nessuna candela 4h nel repo), storia dal 08/2017 (settimanale 2018 non a regime); W3.2 ETH fino al 10/11.
- Non preregistrati (solo descrizione): accordo del Supertrend con i 22 ingressi di W3.2; rendimento per stato senza placebo.
- W3.2 non è fuori campione sul 2021–26; il Supertrend 10/3 sì, ed è comunque molto sotto.

## File
`PREREG.md` · `st_lib.py` (indicatore, controlli) · `st_engine.py` (motore; S2 1D verificata con un ciclo indipendente: 56.137,54 $
in entrambi) · `st_run.py` → `risultati.csv/.txt`, `criteri*.csv`, `mappa.csv`, `placebo_p1.csv`, `placebo_p2*.csv`,
`storia_corta.csv`, `buyhold.csv` · `st_desc.py` → `descrittivo*.csv/.txt`, `cambi.csv`, `stato_attuale.csv` · `st_w32.py` →
`w32_k*.csv/.txt` · `st_eth.py` → `eth*.csv/.txt` · `st_sintesi.py` → `mappa_sintesi.csv`, `accordo_w32.csv`.

## Lezione proposta (119)
**Lezione 119**: il Supertrend di TradingView (ATR 10, fattore 3; replica esatta di ta.supertrend, research/supertrend, PREREG
24d63a0) non è un segnale. Dal 2021 su BTC: inversione long/short 16.215 $ (4h, DD −61%, 293 trade), 3.477 $ (1D, DD −84%),
24.363 $ (1W, DD −83%); solo long 22.653 / 13.807 / 30.642 $ con DD −46/−54/−63%; solo short sempre in perdita; multi-intervallo
13.727 $ e 10.209 $; contro 78.474 $ (DD −21%) di W3.2 e 22.549 $ del buy & hold. 0 oggetti su 11 validi, 0 celle su 176 nella
mappa ATR 7–21 × fattore 2–4 (sul giornaliero 10/3 è la cella peggiore: il risultato dipende dal parametro), 0 su 7 su ETH; il
2018–20 brillante (58.522 $) non si ripete. Win rate 35–40%, un cambio a settimana sul 4h, uno ogni 38 giorni sul giornaliero,
uno l'anno sul settimanale; dopo un cambio il rendimento a 1–30 giorni non differisce dalla media (12 test, nessuno sotto 0,0042).
Dentro W3.2: al posto del trailing 73.584 $ (il cambio 1W non scatta mai prima di EMA21/distribuzione/stop; 2018–20 18.105 $, DD
−52%), uscita al cambio 1D 36.604 $, filtro d'ingresso 1D 62.660 $, uscita al cambio 4h 45.154 $: tutte peggiori. Il Supertrend è
un trailing ATR disegnato: W3.2 ne ha già uno calibrato meglio. Resta contesto visivo (meglio il settimanale), non segnale; non
operare sugli avvisi di cambio direzione.
