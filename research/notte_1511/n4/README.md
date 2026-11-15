# N4 · Flussi di denaro, probabilità long/short e range S/R (15/11/2026) · SOLO CONTESTO

**Verdetto.** Nessuna combinazione di regime, flussi perp/spot, funding, OI, liquidazioni e distanza dalle medie dà una probabilità
long/short che regga la correzione per test multipli: 0 celle su 5.790 test passano BH in IS, e il numero di celle "buone in IS e
in OOS" non supera quello che si ottiene sfasando a caso le variabili (placebo). I livelli S/R del tool non tengono più di livelli
casuali alla stessa distanza, né sul giornaliero né sul settimanale (0/72 test). Il quadro di oggi pende leggermente al ribasso,
ma dentro il rumore. Preregistrazione: PREREG.md. Numeri completi: risultati.txt. Stato di oggi: oggi.json.

## A · Probabilità condizionate (dal 01/01/2021, IS 2021–23, OOS 2024→ottobre 2026)
3.521 celle con 1–3 variabili, 965 ammissibili (≥ 40 osservazioni indipendenti a 7 giorni, ≥ 15 per periodo), orizzonti 7/14/30
giorni, bootstrap a blocchi di 30 giorni (corregge la sovrapposizione). Base: P(r>0) 51,1% / 51,6% / 52,9%, media +0,6/+1,1/+2,5%.

| Prova | Reale | Placebo (50 sfasamenti) |
|---|---|---|
| Celle che passano BH q 0,10 in IS (preregistrato) | 0 | mediana 0 |
| Long: p IS < 0,05 e conferma OOS (secondaria) | 22 | mediana 4, 95° perc. 33 (14% ≥ reale) |
| Short: idem | 34 | mediana 18, 95° perc. 62 (26% ≥ reale) |
| Miglior min(z IS, z OOS) long / short | 2,22 / 2,44 | 95° perc. 2,51 / 2,91 |

Vicini (soglie ±0,30 e ±0,60): stesso esito (0 BH; 8–48% dei placebo fanno meglio).
Le combinazioni migliori (descrittive, NON significative; P = P(rendimento > 0) su tutto il periodo, IS/OOS):

| Lato | Cella | h | P (IC 95%) | media | P IS / OOS |
|---|---|---|---|---|---|
| long | regime long & pf14z > 0 & sf14z > 0 | 30 | 74% (60–86) | +12,7% | 76 / 72% |
| long | regime long & pf14z alto & sf14z > 0 | 30 | 78% (64–89) | +12,1% | 80 / 77% |
| long | regime long & pf14z > 0 & sf14z alto | 30 | 76% (62–88) | +12,9% | 74 / 77% |
| long | sf14z alto & 0–20% sopra SMA40w | 30 | 82% (64–93) | +13,6% | 75 / 88% |
| long | pf14z alto & sf14z > 0 & > 5% sopra EMA21w | 7 | 67% (54–77) | +3,2% | 70 / 65% |
| short | pf14z medio & funding medio & nessuna liquidazione | 7 | 34% (25–45) | −2,8% | 35 / 34% |
| short | regime long & pf14z < 0 & OI 7g alto | 7 | 30% (19–43) | −2,3% | 23 / 34% |
| short | pf14z < 0 & OI alto & > 5% sopra EMA21w | 7 | 29% (18–44) | −2,5% | 23 / 33% |
| short | divergenza nulla & OI 7g basso | 30 | 39% (27–54) | −3,4% | 36 / 40% |
| short | pf14z < 0 & OI 7g alto | 7 | 36% (25–48) | −2,1% | 38 / 35% |

Ricorrenti anche nei vicini: long "regime long + perp e spot in acquisto" (è l'informazione di W3) e short a 7 giorni "perp in
vendita con OI in aumento" (nuovi short aperti). Le singole variabili sono deboli: pf14z terzile alto/basso a 30 g 63% contro 39%.

**Traduzione in trade** (10.000 $, 1x, costi; in cella → posizione per h giorni, prolungata se si resta nella cella; MAR = CAGR/|DD|):

| Regola | Finale | DD giorn. | Trade | WR | MAR | 2021–23 / 2024– | Senza migliore |
|---|---|---|---|---|---|---|---|
| Buy & hold | 21.871 $ | −76,6% | 1 | – | 0,19 | +44% / +45% | – |
| W3 (in uso) | 78.474 $ | −21,1% | 13 | 92% | 1,99 | – | 51.561 $ |
| Long top (h30) | 65.813 $ | −38,1% | 16 | 69% | 0,99 | +167% / +133% | 42.066 $ |
| idem h15 / h60 | 30,9k / 29,6k | −38% / −63% | 23 / 15 | 52 / 60% | 0,56 / 0,32 | | |
| Short top (h7) | 31.202 $ | −43,1% | 50 | 58% | 0,50 | +99% / +57% | 23.795 $ |
| idem soglie ±0,60 | 12.271 $ | −62,0% | 60 | 55% | 0,06 | −8% / +33% | |

Il long batte il buy & hold ma resta sotto W3 (metà MAR, DD quasi doppio) e il placebo nello stesso regime lo mette al 97°
percentile dopo una selezione fra 965 celle; lo short crolla con i vicini. Diagnostica: regime long da solo 29k, + pf14z > 0 45k,
+ sf14z > 0 66k: i flussi aggiungono al regime, ma è l'informazione che W3 usa già (lezioni 57, 86, 89).

**Stato di oggi** (chiusura 14/11, 64.150 $; 63.715 $ alle 00:20 UTC del 15/11): regime neutro (W3 flat), pf14z −0,91 (basso),
sf14z +1,25 (alto: perp vende, spot compra), funding medio, OI 7g in calo, cascata di liquidazioni long il 13/11, prezzo −11% sotto
la SMA40w e −16% sotto la EMA21w. Cella REG×PFt×SFt troppo rara (< 40 casi): la più ricca è "pf14z basso & sf14z alto" (48 casi):
P(r>0) 39% a 7 g (IC 28–52, media −2,1%), 45% a 14 g, 29% a 30 g (IC 15–46); IS/OOS 7 g 46/30%. Delle 61 celle che contengono oggi
il 34% / 13% / 5% sta sopra la base a 7/14/30 g: inclinazione ribassista, non significativa. Nessun segnale W3 (regime neutro).

## B · Supporti e resistenze (radar/levels.compute settimana per settimana, 743 zone reali, 14.860 casuali)
Tenuta = rimbalzo di x% oltre la zona prima di una chiusura x% oltre il lato opposto, dopo il primo tocco.

| Scala | Lato | Tocchi | Tenuta reale | Casuale | Diff (IC 95%) | 2021–23 / 2024–26 (reale−casuale) |
|---|---|---|---|---|---|---|
| D3 giornaliero ±3% | supporti | 264 | 72,0% | 70,7% | +1,2 (−3,6/+5,8) | −0,7 / +2,7 |
| D3 | resistenze | 260 | 66,5% | 64,9% | +1,6 (−2,1/+5,2) | +0,6 / +2,7 |
| D6 giornaliero ±6% | supporti | 264 | 60,6% | 61,1% | −0,5 (−3,5/+2,4) | +0,6 / −1,4 |
| D6 | resistenze | 260 | 56,2% | 53,3% | +2,9 (−0,7/+6,6) | −0,1 / +6,0 |
| W10 settimanale ±10% | supporti | 258 | 66,3% | 66,1% | +0,2 (−3,3/+3,6) | +1,9 / −1,2 |
| W10 | resistenze | 245 | 59,2% | 58,2% | +1,0 (−2,2/+4,4) | +2,3 / −0,5 |

Per tipo (giornaliero, settimanale, nodo di volume, forza ≥ 4) e distanza (0–3, 3–8, 8–15%): 0/72 passano BH; il migliore
(resistenze settimanali a 8–15%, D3) +7,2 punti, p 0,02 non corretto. Anche la probabilità di tocco è uguale al caso.

**Range di oggi** (fascia = zona del tool ± 0,25 ATR; ATR giornaliero 2.617 $; tenuta storica D3 del tipo e della distanza):

| Livello | Fascia | Distanza | Tipo, forza | Tenuta D3 (casuale) |
|---|---|---|---|---|
| R2 | 69.426–75.162 | +14,0% | settimanale, 5 | 70% (63%) |
| R1 | 64.200–69.654 | +3,9% | settimanale, 3 | 64% (66%) |
| S1 | 58.477–63.189 | −4,6% | settimanale, 5 | 71% (74%) |
| S2 | 52.832–58.454 | −12,1% | settimanale, 2 | 73% (68%) |
| oltre | R 74.314–77.260 (g.), 79.946–85.552, 86.742–91.885; S 45.167–49.654, 37.901–42.654 | > 15% | | non testati |

Le percentuali di tenuta sono quasi tutte "volatilità + larghezza della zona": un livello casuale largo uguale tiene uguale.

## Lezione proposta per RESEARCH.md
**Lezione 97** (N4, 15/11): probabilità di rialzo/ribasso a 7–30 giorni condizionate a regime W3, flussi perp/spot, divergenza,
funding, OI, liquidazioni e distanza dalle medie (965 celle ammissibili dal 2021, bootstrap a blocchi, BH, IS/OOS, placebo a
sfasamento): nessuna cella supera la correzione e il numero di celle "buone in IS e OOS" è quello del caso. Le combinazioni migliori
sono la versione descrittiva di W3 (regime long + perp e spot in acquisto: 74% a 30 g) e "perp in vendita con OI in aumento" a
7 g (36%); come trade restano sotto W3. I supporti e le resistenze del tool non tengono più di livelli casuali alla stessa distanza
e larghezza, né sul giornaliero né sul settimanale (0/72). Le probabilità condizionate si mostrano come contesto con l'intervallo
di confidenza; i range S/R restano mappa (conferma lezioni 75–77, 81, 84, 89).

File: PREREG.md, n4_data.py, a_scan.py (a_celle*.csv, a_top*.csv, a_placebo*.csv), a_trade.py (a_trade*.csv), a_oggi.py
(a_oggi_celle.csv, a_oggi.json), b_sr.py (b_eventi.csv, b_tenuta.csv), b_oggi.py (b_oggi_livelli.csv, oggi.json), risultati.txt.
