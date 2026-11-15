# Ciclo notturno 15/11/2026 — report

## Conclusione
Nessuna delle idee studiate stanotte migliora W3 in modo dimostrabile: W3 resta invariata. La domenica è una convenzione e oggi è
il giorno migliore dal 2021, ma l'attesa realistica di W3 è la mediana dei 7 giorni (~63k, non 78k). Swing di 2–3 giorni, politica
monetaria, ETF, stablecoin, flussi e supporti/resistenze descrivono il mercato ma non lo anticipano a 7–30 giorni. La revisione
critica conferma tutti i verdetti; ha ridimensionato i due indizi rimasti (premio Coinbase e short di flusso) a rumore.

## 1. Perché si decide di domenica (N1)
Convenzione: la candela settimanale di Binance/TradingView va da lunedì a domenica UTC e W2/W3 sono nate su quei grafici.
| Chiusura | 10k dal 2021 | DD | 2018–20 |
|---|---|---|---|
| lun | 62.728 | −27,5% | 27.423 |
| mar | 48.763 | −25,2% | 29.413 |
| mer | 38.564 | −28,9% | 32.682 |
| gio | 40.948 | −39,4% | 14.155 |
| ven | 68.218 | −25,5% | 15.071 |
| sab | 70.104 | −25,8% | 20.210 |
| **dom (W3)** | **78.474** | **−21,1%** | 25.142 |
| media dei 7 (1/7 ciascuno) | 58.257 | −23,5% | 23.442 |
| buy & hold | 21.783 | −76,6% | 21.531 |
Domenica prima dal 2021, quarta nel 2018–20; tutti i giorni battono il buy & hold. Proposta: tenere la domenica (cambiare giorno
sarebbe scegliere di nuovo sugli stessi dati) e dichiarare come attesa la mediana dei giorni.

## 2. Swing di 2–3 giorni (N2)
8 regole preregistrate (breakout, RSI(2), ritorno alla media, funding, OI, flussi taker), long/short, costi reali: 0/32 accettabili.
Momentum e RSI(2) vanno nel 2021–23 e si invertono dal 2024; ritorno alla media e fade perdono. La traccia "short di flusso quando
W3 è flat" dipende da 2–3 crash (maggio 2021, LUNA 2022, agosto 2023/24): rumore, archiviata.

## 3. Internet: momentum, politica monetaria, flussi (N3)
28 fonti. Unico effetto robusto: momentum/trend (Liu–Tsyvinski 2021; Zarattini et al. 2025), già alla base di W3. Fed/FOMC: più
volatilità che direzione; M2 globale: correlazione alta solo sui livelli; ETF: i flussi seguono il prezzo; stablecoin e funding: nessuna
previsione settimanale. Test sui nostri dati: stablecoin nessun effetto; liquidità netta Fed solo 2021–23 (come filtro W3 → 42,6k);
FOMC nessuna deriva; premio Coinbase: dopo revisione è quasi tutto rumore della quotazione USDT-USD → non va in dashboard.

## 4. Flussi, probabilità long/short e range S/R (N4)
5.790 test su combinazioni di regime, flusso perp/spot, funding, OI, liquidazioni: 0 superano la correzione per test multipli; le celle
migliori ripetono W3 (regime long con perp e spot in acquisto). Oggi (chiusura 14/11, 64.150): perp vende (−0,91σ), spot compra
(+1,25σ); nei 48 casi simili P(salita a 7 giorni) 39% (IC 28–52), media −2,1%: lieve inclinazione ribassista, non significativa.
Supporti/resistenze del tool ricalcolati ogni settimana dal 2021: tengono come livelli casuali (0/72 test).
| Livello | Fascia | Distanza | Tenuta storica (casuale) |
|---|---|---|---|
| R2 | 69.426–75.162 | +14% | 70% (63%) |
| R1 | 64.200–69.654 | +4% | 64% (66%) |
| S1 | 58.477–63.189 | −5% | 71% (74%) |
| S2 | 52.832–58.454 | −12% | 73% (68%) |

## 5. Revisione critica (N5)
Nessun look-ahead; tutti i verdetti confermati. Ridimensionati: premio Coinbase (rumore USDT) e short di flusso (2–3 crash).
Regola di processo nuova: committare il PREREG da solo prima di eseguire gli script (l'ordine si prova con git).

## Proposte
1. W3 invariata; domenica confermata; attese di W3 comunicate come mediana dei giorni (~63k) e caso peggiore (38,6k, DD −39%).
2. Nessuna nuova regola (swing, macro, flussi, S/R): restano contesto.
3. Dashboard: i range S/R con la loro tenuta storica e quella casuale accanto (onestà sull'affidabilità).
Lezioni 94–97 in RESEARCH.md.
