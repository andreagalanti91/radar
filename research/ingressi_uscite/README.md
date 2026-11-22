# Ingressi e uscite a scaglioni, stop, distribuzione, giorno di decisione · W3.1 · 22/11/2026

**Verdetto: la nuova strategia NON batte la vecchia.** Nessuna delle 14 varianti preregistrate (PREREG 08da8cc) supera i
criteri; nessuna dimensione promossa, quindi nessuna combinazione. W3.1 resta invariata (10.000 → 27.190 $ dal 2021, DD −9,8%).
L'unico risultato significativo a livello nominale conferma la regola attuale: l'uscita per distribuzione batte uscite
casuali negli stessi trade (placebo p = 0,005), ma non supera la correzione di Holm (soglia 0,0036).

## Metodo
Motore `iu_engine.py`: copia di radar.weekly con posizione a scaglioni. Riproduce W3.1 al centesimo (27.190 $, −9,8%; 2018–20
16.734 $, −19,2%) e supera 7 controlli di invarianza (`conteggi.txt`). Dati congelati p2_nuovi fino al 15/11/2026; 2018–20 su
dati proxy (flusso CVD spot prima del 2019-09, funding assente nel 2018–19). Rischio allo stop 10% (somma degli scaglioni), 1x,
costi W3.1. Una dimensione alla volta contro W3.1. Esecuzione: `python3 iu_run.py` (~1,5 min) → `risultati.txt`, `varianti.csv`,
`trade_delta.csv`, `giorni_g7.csv`, `placebo_pd.csv`.

## Risultati (10.000 $; IS 2021–23 e OOS 2024–26 ripartono da 10.000 $)
| Regola | Finale 2021+ | CAGR | DD | CAGR/DD | Trade | WR | Peggiore | IS fin. / CDD | OOS fin. / CDD | 2018–20 fin. / DD | Senza migliore | P(DD≥20%) | Esito |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **W3.1 (vecchia)** | **27.190** | 18,6 | −9,8 | 1,903 | 13 | 92,3 | −1,9 | 17.879 / 2,558 | 15.228 / 1,615 | 16.734 / −19,2 | 22.064 | 2,2 | — |
| E1 DCA lun/mer/ven | 24.039 | 16,1 | −9,7 | 1,654 | 13 | 84,6 | −2,5 | 16.269 / 2,065 | 14.795 / 1,500 | 15.371 / −21,0 | 19.791 | 2,8 | non batte |
| E2 DCA 3 settimane | 18.092 | 10,6 | −9,1 | 1,167 | 13 | 69,2 | −1,4 | 14.409 / 1,737 | 12.573 / 0,911 | 13.380 / −12,2 | 15.524 | 1,1 | non batte |
| E3 1/2 + ritracc. 0,5 ATR | 21.548 | 14,0 | −12,3 | 1,135 | 13 | 69,2 | −2,9 | 14.824 / 1,437 | 14.555 / 1,134 | 15.450 / −17,5 | 17.701 | 3,3 | non batte |
| U1 1/2 + conferma | 24.401 | 16,4 | −9,9 | 1,657 | 12 | 91,7 | −3,0 | 16.614 / 2,158 | 15.030 / 1,539 | 16.212 / −22,0 | 19.852 | 4,1 | non batte |
| U2 trailing 2,0/3,0 | 25.271 | 17,1 | −9,7 | 1,769 | 13 | 92,3 | −2,0 | 17.120 / 2,397 | 14.780 / 1,507 | 16.741 / −19,2 | 20.602 | 2,3 | non batte |
| T1 1/3 a +3R | 27.190 | 18,6 | −9,8 | 1,903 | 13 | 92,3 | −1,9 | = W3.1 | = W3.1 | 17.123 / −16,0 | 22.064 | 2,2 | senza potenza |
| K 2,25 ATR | 28.242 | 19,3 | −15,7 | 1,234 | 14 | 85,7 | −7,2 | 17.277 / 1,278 | 16.370 / 1,885 | 18.126 / −19,8 | 22.447 | 4,7 | non batte |
| K 2,75 ATR | 24.183 | 16,2 | −9,8 | 1,650 | 13 | 92,3 | −1,8 | 16.884 / 2,360 | 14.340 / 1,359 | 15.650 / −18,7 | 19.966 | 2,2 | non batte |
| K 3,0 ATR | 22.879 | 15,1 | −10,0 | 1,517 | 13 | 92,3 | −1,6 | 16.367 / 2,539 | 13.994 / 1,243 | 14.783 / −18,4 | 19.168 | 2,1 | non batte |
| D1 senza distribuzione | 20.694 | 13,2 | −12,8 | 1,033 | 13 | 92,3 | −1,9 | 15.299 / 1,195 | 14.154 / 1,045 | 16.028 / −23,3 | 17.631 | 6,1 | non batte |
| D2 distribuzione 2 dom. | 23.889 | 16,0 | −10,8 | 1,486 | 13 | 92,3 | −1,9 | 16.501 / 1,877 | 15.149 / 1,594 | 15.948 / −23,3 | 19.486 | 4,5 | non batte |
| D3a soglie ×0,8 | 28.083 | 19,2 | −9,8 | 1,970 | 13 | 92,3 | −1,9 | 18.465 / 2,715 | 15.228 / 1,615 | 16.734 / −19,2 | 22.788 | 2,1 | senza potenza |
| D3b soglie ×1,2 | 26.018 | 17,7 | −10,8 | 1,644 | 13 | 92,3 | −1,9 | 17.879 / 2,558 | 15.228 / 1,615 | 16.617 / −19,2 | 21.113 | 2,2 | senza potenza |
| G7 sette giorni | 23.644 | 15,8 | −11,3 | 1,395 | 106 | 74,5 | −10,2* | 16.181 / 2,066 | 14.522 / 1,222 | 15.863 / −21,4 | 18.937 | n.d. | non batte |
| Buy & hold | 22.549 | 14,9 | −76,6 | 0,194 | — | — | — | 14.590 / 0,175 | 15.425 / 0,307 | 21.046 / −81,2 | — | — | — |

Perdita allo stop pianificata: 10,0–10,1% dell'equity per tutte le varianti (G7: 1,4% del totale, 10% della quota).
*G7: peggior trade in % della quota di 1/7. P(DD≥20%): bootstrap di 13 trade dai trade 2018–26 (DD trade per trade).

## Robustezza
- **Criteri** (dettaglio in `risultati.txt`): nessuna variante migliora sia IS sia OOS (criterio 2). Il criterio 5 (non dipende da
  ≤ 2 trade) fallisce ovunque, perché la differenza è negativa già prima di togliere i trade.
- **Test appaiati** (permutazione dei segni sui Δ dei trade): p 0,39–1,00. Il migliore è K 2,25 (p 0,39). Nessuno è vicino a Holm.
- **Placebo P-D**: le 4 uscite per distribuzione spostate a caso negli stessi trade danno una mediana di 20.604 $
  (5°–95° percentile 16.377–25.416 $) contro i 27.190 $ di W3.1 (p 0,005, non significativo con Holm su 14 test).
- **Vicini**: tutti sotto W3.1 in CAGR/DD, tranne T1 a +2R (27.244 $ / 1,907, cioè 4 prese parziali: lo stesso caso della
  griglia G) e D3a ×0,7/×0,9 (28.195 / 1,893; 28.083 / 1,970).
- **G7**: i 7 giorni singoli vanno da 19.646 $ (mercoledì) a 27.190 $ (domenica), mediana 24.490 $. G7 fa 23.644 $ con DD −11,3%
  e non riduce il DD.

## Trade che cambiano (Δ log-rendimento, punti %; completo in `trade_delta.csv`)
- **DCA E1/E2/E3**: perdono su quasi tutti i 13 trade (E2: 12 su 13 negativi), perché entrare tardi costa prezzo proprio sui
  vincenti (2024-02-11 −7,8, 2021-01-31 −5,3, 2023-10-22 −5,1). Il limite E3 si esegue 1 volta su 13: unico guadagno
  2024-09-22 +4,4.
- **U1**: il mezzo trade rimasto occupa la posizione e fa perdere il rientro del 2021-10-03 (−8,0), più di quanto guadagna il
  2021-08-01 (+5,2).
- **U2**: 2023-01-22 −4,6, 2024-02-11 −4,3, 2025-04-27 +1,6.
- **K 2,25**: un trade in più, 2023-07-02 −7,5, con DD −15,7%. Gli altri trade guadagnano 1–2 punti per la size maggiore.
  K 2,75/3,0: −0,2/−3,7 punti su quasi tutti i trade (size minore, stesse uscite).
- **D1**: 2021-01-31 −8,3, 2024-02-11 −7,3, 2021-10-03 −7,3, 2023-10-22 −4,4.
- **D2**: 2021-01-31 −9,2, 2023-10-22 −4,4.
- **D3a**: solo 2021-08-01 +4,5 e 2021-10-03 −1,3, OOS identico. Un indizio che dipende da 1 trade, non un risultato.

## Deviazioni (dal PREREG)
1. **Motore**: aggiunti dopo il commit due agganci che non cambiano le regole. Il primo registra la perdita pianificata allo
   stop. Il secondo forza le uscite del placebo P-D. Riproduzione e invarianze verificate di nuovo, identiche.
2. **Placebo P-D**: le uscite forzate sono le sole uscite per distribuzione. Se il trade rientra dopo un'uscita anticipata,
   nel rientro la distribuzione non si applica.
3. **G7**:
   - capitale senza il trade migliore calcolato togliendo il trade migliore di ciascun sotto-portafoglio;
   - bootstrap dei trade non calcolato (trade in quote diverse);
   - potenza considerata soddisfatta.
4. **Vicini di K 2,25 e K 2,75**: uno dei due vicini è W3.1 stessa, quindi il criterio 4 ("migliore di W3.1") non poteva mai
   passare. È un difetto del PREREG, ma senza effetto: entrambe falliscono già il criterio 2.

## Lezione proposta per RESEARCH.md
**Lezione 105**: su W3.1 i modi di eseguire gli stessi segnali non migliorano il risultato.
- **Ingressi**: il DCA a tempo dentro la settimana costa 3.000 $ (24.039 contro 27.190), su 3 settimane 9.000 $; il mezzo
  ingresso su ritracciamento ne costa 5.600 (limite eseguito 1 volta su 13). Conferma la lezione 53.
- **Uscite**: a scaglioni (U1) o con trailing doppio (U2) costano 1.900–2.800 $.
- **Take profit**: il TP a +3R non scatta mai dal 2021.
- **Stop**: 2,5 ATRw resta il migliore a rischio 10%. 2,25 rende di più solo con un trade perso in più e DD −15,7%; 2,75 e 3,0
  rendono meno (conferma la lezione 60).
- **Distribuzione**: l'uscita per distribuzione è utile. Toglierla costa 6.500 $ e 3 punti di DD; spostarla a caso costa in
  mediana 6.600 $ (placebo p 0,005). Ma resta fragile ai margini delle soglie: ×0,8 cambia 2 trade, ×1,2 ne cambia 1. Va
  tenuta com'è e i margini vanno registrati (lezione 102).
- **Giorno di decisione**: ripartire la decisione su 7 giorni (G7) dà 23.644 $, vicino alla mediana dei giorni (24.490), senza
  ridurre il DD (−11,3%). È un'attesa realistica, non un miglioramento.
- **Potenza**: con 13 trade nessun test supera Holm. Il verdetto è "nessun miglioramento dimostrabile", non "W3.1 ottimale".
