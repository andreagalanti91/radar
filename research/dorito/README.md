# "Dorito indicator" (Leledc Exhaustion Bar, InSilico 40/10) su BTC 1D e 3D · 26/11/2026

**Verdetto: da usare nella strategia? NO.** Il "dorito" disegna bene i minimi e i massimi scelti per i post, ma come segnale perde
contro il buy & hold. Come uscita o come filtro peggiora W3.2. Nessuna delle 8 configurazioni preregistrate supera i criteri e
nessun placebo è significativo (p da 0,44 a 1,00).

PREREG: `PREREG.md`, commit 5c92dc0, prima di ogni rendimento. Script: `dz_engine.py`, `dz_run.py` (gira in circa 50 s).
Output: `risultati.csv`, `criteri.csv`, `studio_evento.csv`, `w32_trade.csv`, `risultati.txt`. Ricostruzione e coincidenza con lo
screenshot (8/8 sul 3D che riparte ogni 1 gennaio): `dorito_lib.py`, `z_match.py`, `eventi.csv`, `conteggi.txt`.

## Come funziona l'indicatore
Si tratta dello script open source TradingView "Leledc levels (IS)" di InSilico, una modifica del "Leledc Exhaustion Bar" di glaz.
- **Rosso:** più di 10 chiusure sopra la chiusura di 4 barre prima (contate dall'ultimo rosso), poi una candela rossa che tocca
  il massimo delle ultime 40 barre.
- **Nero:** è il caso speculare.

Non usa il Williams %R né il TD Sequential.

## Risultati (10.000 $, 1x, costi inclusi; W3.2 fino al 15/11, il resto fino al 25/11/2026)
S = CAGR/|DD|. "Senza 2" = capitale togliendo i 2 trade migliori (per W1–W4 sono i trade dell'intera simulazione).

| Dal 01/01/2021 | Finale | Rend. | Max DD | S | MAR | Trade | WR | Senza 2 |
|---|---|---|---|---|---|---|---|---|
| Buy & hold | 20.840 | +108% | −76,6% | 0,17 | 1,4 | – | – | – |
| **W3.2** | **78.474** | +685% | −21,1% | 1,99 | 32,4 | 13 | 92% | 36.250 |
| S1 3D solo long | 5.155 | −48% | −66,8% | <0 | <0 | 3 | 33% | 5.613 |
| S2 3D long/short | 0 | −100% | −100% | – | – | 3 | 33% | 0 |
| S3 1D solo long | 3.876 | −61% | −72,7% | <0 | <0 | 11 | 55% | 2.396 |
| S4 1D long/short | 1.122 | −89% | −92,4% | <0 | <0 | 22 | 45% | 693 |
| W1 W3.2 + uscita al triangolo 3D contrario | 68.804 | +588% | −28,2% | 1,38 | 20,9 | 21 | 67% | 30.521 |
| W2 W3.2 + uscita al triangolo 1D contrario | 46.429 | +364% | −24,0% | 1,24 | 15,2 | 31 | 71% | 27.648 |
| W3 W3.2 + filtro 3D (30 giorni) | 52.845 | +428% | −18,9% | 1,73 | 22,7 | 12 | 83% | 24.411 |
| W4 W3.2 + filtro 1D (30 giorni) | 37.622 | +276% | −22,5% | 1,13 | 12,3 | 11 | 73% | 17.379 |

**S per periodo**

| Configurazione | P1 2018–20 | P2 2021–23 | P3 2024–26 |
|---|---|---|---|
| Buy & hold | 0,35 | 0,17 | 0,25 |
| W3.2 | 0,96 | 2,57 | 1,64 |
| S1 | 0,57 | <0 | <0 |
| S2 | azzerata | azzerata | azzerata |
| S3 | <0 | <0 | 0,02 |
| S4 | azzerata | <0 | <0 |
| W1 | 0,76 | 1,93 | 0,99 |
| W2 | 0,79 | 2,04 | 0,72 |
| W3 | 0,96 | 1,91 | 1,57 |
| W4 | <0 | 0,96 | 1,57 |

- **IS e OOS:** S1 è a +0% nel 2018–22 e a −8% nel 2023–oggi.
- **Dal 2018:** W3.2 arriva a 224.593 $; W1 a 166.041 $, W3 a 151.242 $.
- **Variante glaz 30/6:** stesso quadro (`risultati.csv`).

## Criteri uno per uno (tutti richiesti)

**S1–S4: tutte NON VALIDE.**
- **Finale > 10.000 $ in P1, P2 e P3:** no per tutte. S1 passa solo in P1, con 2 trade.
- **S migliore del buy & hold in tutti i periodi:** no.
- **DD ≥ −35%:** no, si va da −40% a −100%.
- **Senza i 2 trade migliori sopra 10.000 $:** no.
- **Almeno 8 trade dal 2018:** solo S3 (17). Sul 3D S1 ne fa 5 e S2 2.
- **Placebo:** p 0,81 / 1,00 / 0,96 / 1,00, quindi Holm non passa.
- **Vicini in profitto in tutti i periodi:** 0/8 per tutte.
- **Competitiva con W3.2:** no.

**W1–W4: tutte NON MIGLIORANO.**
- **S migliore di W3.2 in P2 e P3, non peggiore in P1:** no per tutte.
- **DD entro 1 punto da W3.2:** solo W3.
- **Finale o DD dal 2021:** no. Il DD di W3 è migliore di 2,2 punti, ma il finale scende al 67%.
- **Win rate ≥ 70%:** sì per W2, W3 e W4; no per W1 (67%).
- **Migliore anche togliendo i 2 trade che migliorano di più:** no.
- **Vicini che migliorano S:** W1 0/8, W2 0/8, W3 3/11, W4 0/11.
- **Placebo:** p 0,67 / 0,47 / 0,44 / 0,55.

Trade di W3.2 toccati (`w32_trade.csv`):
- **W1:** tocca 8 trade su 13. Aiuta poco nel 2021, 2022 e 2023 (rapporti da 1,04 a 1,13). Taglia i trend 2024–26 (da 0,93 a
  0,96) e il trade del 15/08/2022 (0,89).
- **W3:** blocca o rimanda 3 ingressi e peggiora tutti e 3: il long del 23/01/2023 (0,82), quello del 01/12/2025 (0,89) e uno
  del 2021 (0,92).

## Studio d'evento (descrittivo, BTC dal 2018; rendimento dall'apertura del giorno dopo la barra; Holm su 12)

| Segnale | n | 7 giorni | 30 giorni | 90 giorni | Media di tutti i giorni (7/30/90) | p placebo (7/30/90) |
|---|---|---|---|---|---|---|
| 3D nero | 10/9/9 | +2,5% | +5,2% | +12,4% | +0,7 / +3,5 / +13,4% | 0,26 / 0,39 / 0,48 |
| 3D rosso | 15 | +0,5% | +9,3% | +22,0% | uguale | 0,44 / 0,85 / 0,77 |
| 1D nero | 31/29/29 | −2,3% | −0,1% | +5,8% | uguale | 0,97 / 0,84 / 0,81 |
| 1D rosso | 41 | +2,4% | +7,2% | +21,9% | uguale | 0,88 / 0,87 / 0,86 |

- **3D nero:** è vicino ai minimi, perché solo l'11% dei neri è seguito da un minimo più basso entro 30 giorni. Il rendimento
  successivo però non supera quello di un giorno qualsiasi.
- **Rossi:** dopo un rosso BTC in media sale più del solito, cioè l'"esaurimento" del rialzo non si vede.
- **Giornaliero:** il 76% dei neri è seguito da un minimo più basso.
- **ETH, stessi parametri:**
  - S1 3D chiude dal 2021 a 34.974 $, contro 23.322 $ del buy & hold, ma con soli 3 trade e DD −44%.
  - S2 viene azzerata nel 2021–23.
  - Nero a 30 giorni: +23%, p 0,03 non corretto, su 8 eventi.

  Non basta a salvare BTC.

## Lo short di W3.2 del 16/11/2026
- **Il segnale:** il nero 3D è sulla barra 15–17/11 (chiude il 17/11).
- **W1:** avrebbe coperto lo short all'apertura del 18/11, a circa 64.947 $. Risultato: +0,4% di prezzo, circa +0,3% sul
  capitale con esposizione 0,97.
- **Short tenuto:** al 25/11 (60.458 $) vale circa +7,2% sul capitale. Con W1 lo short avrebbe reso circa 7 punti in meno.
- **W4 (filtro 1D):** avrebbe bloccato lo short, per i neri giornalieri del 04/11 e del 15/11.
- **W2 e W3:** nessun effetto.

Solo descrizione: nessuna indicazione operativa.

## Limiti
- **Pochi eventi:** sul 3D ci sono 25 triangoli dal 2018 (9 neri). S1 fa 2–3 trade per periodo e un periodo pesa quanto un trade.
  Questo però non salva l'idea: perde anche sul giornaliero (72 segnali) e i placebo sono lontanissimi dalla soglia.
- **Coincidenza con il grafico:** gli 8/8 riguardano il 2024–26 sui dati Binance. Che TradingView ricominci le barre 3D ogni
  1 gennaio l'ho dedotto dai dati, non l'ho trovato documentato.
- **Bias dei post:** i grafici condivisi mostrano i triangoli riusciti. Nel 2022 tre neri, a 36,6k, 20,6k e 16,6k: i primi due
  sono caduti dentro il bear.

## Deviazioni dal PREREG
1. **Short azzerati:** gli short 1x senza stop di S2/S4 hanno portato il capitale sotto zero (rialzi 2019–21). Si chiude a 0
   (liquidazione) e il periodo finisce lì.
2. **Posizioni aperte a fine periodo:** sono valutate al netto della commissione d'uscita anche in W3.2. Per questo P1 di W3.2 è
   25.117 $ invece di 25.142 $ (copia identica al dollaro prima di quella commissione: 78.474 $ e 25.142 $).
3. **Funding dopo il 21/11/2026:** posto a 0, cioè 4 giorni.
4. **p del placebo:** calcolato come quota (numero di placebo ≥ reale)/1.000; nello studio d'evento le date sono estratte con
   ripetizione.

## Lezione 127 proposta per RESEARCH.md
"Dorito" (@CryptoJelleNL) = Leledc Exhaustion Bar, versione InSilico 40/10. Ricostruito dal sorgente pubblico: riproduce 8/8 i
triangoli del post sul 3D, con barre che ripartono ogni 1 gennaio. Su BTC dal 2018 non funziona:
- **Da solo:** sotto il buy & hold in ogni periodo (S1 3D dal 2021: 5,2k contro 20,8k); gli short a 1x si azzerano.
- **Dentro W3.2:** come uscita peggiora (W1 68,8k e DD −28% contro 78,5k e −21%); come filtro anche (W3 52,8k).
- **Placebo:** p 0,44–1,00.

I neri 3D cadono vicino ai minimi, ma il rendimento dopo non batte un giorno qualsiasi; dopo i rossi BTC sale più del solito.
I grafici dei post mostrano solo i triangoli riusciti. Non riproporre il Leledc o sue varianti di conteggio senza un'ipotesi
nuova.
