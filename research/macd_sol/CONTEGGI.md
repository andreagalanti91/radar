# MACD settimanale su SOL · fase 1: dati e conteggi (nessun rendimento) · 27/11/2026

Script: `conteggi.py` (dalla radice: `python3 -I research/macd_sol/conteggi.py`), stampa completa in `conteggi_output.txt`.
Dati congelati `research/w32_asset2/crypto/data/SOL_spot.csv.gz` (10/04/2020 → 24/11/2026), candele W-SUN come W3.2:
346 chiuse (12/04/2020 → 22/11/2026), utilizzabili dopo il riscaldamento 26 + 9 dal **06/12/2020** (312 settimane).

**Conclusione di fase 1.** Con le soglie dell'utente le regole fanno pochissimi trade: R1 e R2 3 ingressi ciascuna, R3 e R4 uno solo
(e mai un'uscita: di fatto un buy & hold da una data). Il criterio preregistrato "≥ 8 trade" non è raggiungibile da nessuna delle
quattro varianti principali, qualunque sia il rendimento: nessuna può risultare "valida". La fase 2 resta utile solo come descrizione.

## Settimane per anno
| Anno | Sett. | Close mediana $ | Linea in [−50, −3] | Linea ≥ +10 | Ist. in [−50, −3] | Ist. ≥ +10 | Linea norm. in banda (R4) | Linea norm. ≥ +10 | Incroci al rialzo in banda (R2) |
|---|---|---|---|---|---|---|---|---|---|
| 2020 (dic) | 4 | 1,57 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021 | 52 | 38,18 | 0 | 20 | 2 | 9 | 0 | 1 | 0 |
| 2022 | 52 | 40,00 | 45 | 4 | 25 | 0 | 39 | 0 | 1 |
| 2023 | 53 | 21,93 | 15 | 4 | 0 | 0 | 26 | 0 | 0 |
| 2024 | 52 | 148,27 | 0 | 40 | 16 | 0 | 0 | 0 | 0 |
| 2025 | 52 | 170,56 | 24 | 14 | 20 | 0 | 7 | 0 | 1 |
| 2026 | 47 | 85,27 | 36 | 0 | 11 | 0 | 33 | 0 | 1 |
| **Totale** | 312 | 89,03 | **120** | **82** | 74 | 9 | 105 | 1 | **3** |

La soglia −50 non è mai vincolante: il minimo storico della linea è −23,99 $ (settimane sotto −50: 0). La banda equivale a "linea ≤ −3".

## Ingressi e uscite per variante (decisione la domenica, esecuzione il lunedì)
| Variante | Ingressi | Uscite | Aperta oggi | Date di decisione |
|---|---|---|---|---|
| R1 letterale | 3 | 2 | sì | E 20/02/2022 · U 10/12/2023 · E 16/03/2025 · U 14/09/2025 · E 23/11/2025 |
| R2 ripartenza | 3 | 2 | sì | E 31/07/2022 · U 10/12/2023 · E 18/05/2025 · U 14/09/2025 · E 19/04/2026 |
| R3 istogramma | 1 | 0 | sì | E 19/12/2021 (l'istogramma ≥ +10 c'è solo nel 2021, prima dell'ingresso) |
| R4 normalizzata | 1 | 0 | sì | E 06/03/2022 (vendita a linea/close ≥ +31,1%: una sola settimana, nel 2021) |
| Rif. flip solo long (lez. 79) | 8 | 8 | no | 2021 2/2 · 2022 1/0 · 2023 1/1 · 2024 1/1 · 2025 2/3 · 2026 1/1 |
Le varianti con stop (R1s–R4s) hanno più ingressi (rientri dopo lo stop): si contano in fase 2 perché dipendono dal percorso del prezzo.

## Distribuzione (312 settimane)
| | min | p5 | p25 | mediana | p75 | p95 | max |
|---|---|---|---|---|---|---|---|
| Linea MACD $ | −23,99 | −21,09 | −10,70 | 0,11 | 10,90 | 33,28 | 50,86 |
| Istogramma $ | −17,31 | −10,26 | −2,81 | 0,78 | 2,68 | 8,67 | 13,39 |
| Linea in % del prezzo | −122,4 | −56,1 | −14,5 | 0,25 | 12,4 | 21,3 | 38,7 |

Estremi per anno della linea: 2021 da −0,01 a +50,9 $ (fino a +38,7% del prezzo); 2022 da −24,0 a +32,8 $ (fino a −108,9%);
2023 −12,2/+18,1 $ (fino a −122,4%); 2024 +2,7/+36,2 $ (sempre positiva: nessun acquisto possibile); 2025 −15,4/+20,3 $
(−13,6/+8,9%); 2026 −24,0/+4,8 $ (−29,4/+4,4%).

## Perché le soglie assolute pesano diversamente
| Prezzo SOL | −3 $ = % del prezzo | −50 $ = % | +10 $ = % |
|---|---|---|---|
| 2 $ (2020) | −150% | −2.500% | +500% |
| 20 $ (2023) | −15% | −250% | +50% |
| 32,11 $ (mediana IS, R4) | −9,3% | −155,7% | +31,1% |
| 100 $ | −3% | −50% | +10% |
| 200 $ (2024–25) | −1,5% | −25% | +5% |
A 200 $ basta un ritracciamento lieve per "comprare" e +5% di MACD/prezzo per "vendere"; a 20 $ serve un MACD a −15% del prezzo
e la vendita a +50% non arriva quasi mai. Le soglie dell'utente sono di fatto tarate sui prezzi 2024–26: è il rischio di adattamento
dichiarato nel PREREG. R4 (soglie fissate a 32,11 $) compra quasi solo nel 2022–23 e nel 2026 e vende solo in un rialzo parabolico.

## Innesti in W3.2 (estensione del PREREG §7; `conteggi_innesti.py`, `conteggi_innesti.txt`)
Verifica del motore senza innesto (`verifica_motore.txt`): BTC 84.820 $, ETH 39.572 $, SOL 80.661 $ = riferimenti.
| Asset · soglie | Trade W3.2 base | W-F blocca | W-U scatterebbe in |
|---|---|---|---|
| BTC · % prezzo | 9 long + 5 short | 0 long, 1 short | 0 trade |
| ETH · % prezzo | 10 long + 5 short | 0 long, 3 short | 0 trade |
| SOL · % prezzo | 15 long + 8 short | 0 long, 6 short | 0 trade |
| SOL · $ assoluti | 15 long + 8 short | 4 long, 5 short | 8 long su 15 |
Conteggi sui segnali dei trade base (un blocco può spostare i segnali successivi: i numeri esatti in fase 2). In % del prezzo W-U è
inerte (+31,1% mai raggiunto in posizione) e W-F tocca solo short: su BTC ed ETH l'innesto MACD ha poco o nulla da cambiare.
