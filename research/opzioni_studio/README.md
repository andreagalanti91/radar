# Opzioni su BTC: struttura, uscite e segnali · ciclo notturno 24–25/11/2026 · BOZZA

**Verdetto: niente batte B0, che resta la regola sulla carta.** Le 7 regole (segnale di W3.2, call o put alla pari a circa 30
giorni, 5% del conto, vendita all'uscita di W3.2, mai rinnovare) restano invariate. Nessuna struttura (F1), nessuna uscita (F2) e
nessun segnale indipendente (F3) supera i criteri preregistrati (PREREG + ADDENDUM-1). Nessun segnale F3 risulta nemmeno "utile"
come fonte di occasioni in più: le operazioni aumentano, il vantaggio no (placebo p da 0,14 a 0,41). Con i prezzi della superficie Deribit, B0 porta 10.000 $ a
**49.712 $ dal 2018** (DD −12,8%) e a **21.695 $ in OOS 2022–26** (DD −9,8%). Sono valori vicini a W3.2 a metà dimensione
(57.961 $ / 21.951 $), con perdita massima per operazione del 5%.

## Cosa è stato provato
- **Cancello** (PREREG, ADDENDUM-1 punto 6): il motore con `superficie.py` rifà le 23 operazioni di `storico_prezzi_veri.csv`.
  Scarto mediano del moltiplicatore +4,9% con il contratto del CSV e +0,0% con il contratto scelto dal motore, contro una
  soglia di ±15%: **superato**. Il singolo caso però è disperso (scarto mediano assoluto 0,2–0,3 sul moltiplicatore), perché in 6
  operazioni su 23 il venerdì più vicino a 30 giorni ne dista solo 18, mentre lo studio dell'utente usava quello a 46.
- **F1**: scadenza 14/30/60/90 giorni × prezzo d'esercizio 5% dentro, alla pari, 5% e 10% fuori (16 celle).
- **F2**: uscite U0–U5 sul contratto di B0 (6 celle).
- **F3**: segnali a–f con le soglie dell'ADDENDUM-1, più "call sempre" e "straddle sempre" come riferimenti.
- **F4 e spread a debito**: descrittivi.
- **Riferimenti**: W3.2 intera, W3.2 a metà, liquidità, buy & hold.
- **Regole comuni**: 10.000 $, ogni periodo simulato da solo partendo da 10.000 $ e senza posizioni; costi del PREREG; valutazione
  giornaliera al valore di liquidazione.
- **Esecuzione**: `python3 op_fase2.py` (circa 15 minuti, di cui 4 × 1.000 placebo), poi `python3 op_extra.py`. Uscite:
  `risultati.txt`, `griglia_F1.csv`, `uscite_F2.csv`, `segnali_F3.csv`, `verdetti.csv`, `operazioni_*.csv`, `placebo.csv`,
  `equity.csv`, `cache/cancello_23.csv`. Il motore ha i test in `op_test.py` (9 test, verdi).

## Risultati (10.000 $; finale e DD giornaliero)
| Strategia | Dal 2018 | DD | Dal 2021 | DD | IS 2018–21 | DD | OOS 2022–26 | DD | Op. IS/OOS | PF OOS |
|---|---|---|---|---|---|---|---|---|---|---|
| W3.2 intera | 241.439 | −37,3 | 84.330 | −21,1 | 54.910 | −37,3 | 43.970 | −21,1 | 12/10 | 40,3 |
| W3.2 a metà | 57.961 | −22,6 | 31.218 | −11,9 | 26.404 | −22,6 | 21.951 | −11,9 | 12/10 | 40,3 |
| Buy & hold | 43.903 | −81,2 | 20.819 | −76,6 | 33.696 | −81,2 | 13.029 | −66,9 | — | — |
| **B0** | **49.712** | −12,8 | **31.134** | −9,8 | **22.914** | −12,8 | **21.695** | −9,8 | 12/10 | 11,6 |
| F1 scelta su IS: 14 g alla pari | 47.572 | −13,7 | 31.896 | −12,7 | 23.726 | −13,7 | 20.050 | −12,7 | 12/10 | 6,3 |
| F2 scelta su IS: U0 (= B0) | = B0 | | | | | | | | | |
| F3a tendenza | 18.626 | −34,9 | 13.051 | −33,6 | 12.860 | −34,9 | 14.947 | −31,6 | 47/57 | 1,35 |
| F3b flusso W3.2 ogni settimana (descr.) | 54.486 | −20,6 | 25.092 | −20,4 | 28.326 | −20,6 | 19.236 | −20,4 | 18/25 | 2,31 |
| F3c volatilità bassa → straddle | 13.661 | −29,3 | 10.387 | −29,3 | 12.690 | −15,3 | 10.801 | −29,3 | 30/45 | 1,16 |
| F3d compressione → straddle (descr.) | 14.614 | −16,8 | 14.870 | −9,5 | 10.032 | −16,8 | 14.568 | −9,5 | 16/17 | 3,79 |
| F3e dopo cascata → call (descr.) | 9.891 | −29,8 | 8.669 | −29,8 | 11.560 | −20,1 | 8.556 | −25,4 | 14/5 | 0,18 |
| F3f cono ≥ 1,4 × costo | 45.072 | −41,6 | 16.982 | −41,6 | 26.814 | −23,2 | 16.809 | −41,6 | 39/48 | 1,66 |
| Rif. call sempre | 42.225 | −43,9 | 18.471 | −43,9 | 22.620 | −31,1 | 18.667 | −35,9 | 48/58 | 1,65 |
| Rif. straddle sempre | 16.601 | −23,5 | 12.971 | −23,5 | 11.769 | −15,6 | 14.106 | −23,5 | 48/58 | 1,38 |
| F4 W3.2 metà su perp + protezione (descr.) | 29.829 | −33,6 | 21.195 | −13,4 | 17.710 | −33,6 | 16.843 | −13,4 | 12/10 | 9,0 |
| Spread a debito alla pari − 20% (descr.) | 36.872 | −11,2 | 28.369 | −9,2 | 16.953 | −11,2 | 21.749 | −9,2 | 12/10 | 12,9 |

Le griglie complete, con CAGR, quota in guadagno, perdita peggiore, serie peggiore e risultato senza le 2 migliori operazioni,
sono in `risultati.txt` e nei CSV. Riconteggio con la IV della superficie: c 25/37 operazioni (giudicabile, IS ≥ 20); f 35/44.

## Criteri, uno per uno (OOS 2022–26 contro B0 21.695 $, DD −9,8%)
| Cella | (1) finale > B0 e DD ≤ +3 punti | (2) senza le 2 migliori | (3) vicini | (4) ≥ 20 per metà e placebo | (5) Holm | Esito |
|---|---|---|---|---|---|---|
| F1 14 g alla pari | no (20.050; −12,7%) | no (11.298 contro 13.656) | 1/3 | — | p 0,71 → 1,00 | non migliore |
| F2 U0 | scelta IS = B0 | | | | | nessun cambio |
| F3a | no (14.947; −31,6%) | no (9.302) | 0/4 | 47/57, p 0,41 | 1,00 | non migliore, non utile |
| F3c | no (10.801; −29,3%) | no (8.112) | 0/4 | 30/45, p 0,34 | 1,00 | non migliore, non utile |
| F3f | no (16.809; −41,6%) | no (8.869) | 0/4 | 39/48, p 0,14 | 0,82 | non migliore, non utile; non batte "call sempre" (18.667) |

Criterio "utile" (OOS sopra 10.000 $, PF ≥ 1,2, punti 2–5, correlazione settimanale con B0 < 0,5): nessuno lo soddisfa.
- **F3a**: PF 1,35, correlazione 0,45, ma placebo p 0,41.
- **F3c**: PF 1,16.
- **F3f**: PF 1,66, correlazione 0,10, ma placebo p 0,14 e scende a 8.869 $ senza le 2 migliori.
- **Rif. call sempre**: placebo p 0,07.

## Cosa dicono i dati
- **Il guadagno di B0 viene dai segnali di W3.2, non dall'opzione.** Le 3 operazioni migliori di B0 (12/2020 +39%, 02/2024 +26%,
  10/2020 +26% sul conto) sono le stesse di W3.2. Per anno: 2018 −7%, 2025 −1%, gli altri anni positivi. Call +257% su 16 operazioni, put +32% su 6.
- **Le varianti che sembrano migliori lo sembrano solo guardando l'OOS.**
  - Struttura: in OOS fanno più di B0 "30 g 5% fuori" (25.134 $) e "14 g 5% fuori" (27.232 $), ma con DD fra −13% e −21%. In IS le
    stesse celle superano il limite di DD e la regola preregistrata non le sceglie.
  - Uscite: "U5 un rinnovo" fa 23.922 $ in OOS (DD −12,8%), ma in IS aveva DD −16,9% contro −12,8%. Togliendo le 2 operazioni migliori
    nessuna resta chiaramente sopra B0.
- **Più occasioni = esposizione quasi continua, non un vantaggio.** a ed f stanno in posizione l'80–90% del tempo e somigliano a
  "compra una call ogni mese" (f contro call sempre in OOS: 16.809 contro 18.667 $). Il placebo con date a caso fa quasi
  altrettanto: è la deriva di BTC, pagata con DD del 35–44%.
- **La volatilità implicita "bassa" non paga lo straddle** (F3c 10.801 $ in OOS, PF 1,16, placebo p 0,34). La compressione delle
  bande (d) va meglio (14.568 $, DD −9,5%, PF 3,8) ma con 16/17 operazioni resta descrittiva.
- **Le perdite delle opzioni direzionali mensili si concentrano nei momenti di IV alta.** Composto per terzile di IV
  all'ingresso: F3a −26% (alta) contro +60% (bassa) e +49% (media); F3f −37% contro +192% e +160%. B0 invece è positivo in tutti
  e tre i terzili (+31%, +79%, +100%). I terzili sono calcolati su tutto il 2018–26: è una diagnosi, non una regola.
- **La scadenza conta molto più di quanto pensassimo.** Con il venerdì più vicino a 30 giorni, nel 2018–20 e in 6 operazioni su
  23 la scadenza è a 11–18 giorni. Imponendo almeno 21 giorni, B0 fa 57.277 $ dal 2018 (+15%) ma 20.805 $ in OOS (−4%):
  nessun segno stabile, solo caso.
- **I costi non cambiano le conclusioni.** Con differenza denaro-lettera 0/3/6% per lato B0 fa 54.588/49.712/45.481 $ dal
  2018. L'ordine fra le strategie non cambia.
- **Spread a debito** (descrittivo): stesso rendimento di B0 in OOS (21.749 $, DD −9,2%), meno dal 2018 (36.872 $), perché taglia i
  movimenti grandi del 2020–21. Richiede di vendere una gamba.
- **F4** (W3.2 a metà senza stop, con put o call 10% fuori come protezione): 29.829 $ dal 2018 con DD −33,6% contro W3.2 a metà
  57.961 $ e −22,6%. La protezione costa più di quanto protegga.

## Cosa significa per l'operatività
Per chi vuole operare in opzioni su BTC, il segnale operativo resta uno solo: **B0, cioè le 7 regole**. A ogni segnale di
W3.2 si compra una call o una put alla pari a circa 30 giorni, con il 5% del conto, e la si vende quando W3.2 esce. Rende quanto
W3.2 a metà con perdita massima del 5% per operazione. Nessun segnale aggiuntivo ha mostrato un vantaggio: non conviene comprare
opzioni fra un segnale e l'altro. Unica nota pratica: quando il venerdì più vicino a 30 giorni è a meno di 3 settimane, il
risultato della singola operazione diventa molto più casuale. Non è dimostrato che convenga sceglierne uno più lontano.

## Limiti
- **Prezzi ricostruiti, non il book.** Superficie dalle 12:00 UTC con il prezzo Binance delle 12:00 come F (non il future);
  93,7% delle chiamate da scambi del giorno, 6,3% interpolate. Il regolamento è l'apertura oraria Binance delle 08:00, non
  l'indice Deribit; 8 giorni senza candela oraria sono interpolati.
- **Scadenze**: solo quelle presenti nel campione di scambi del giorno o dei 3 giorni prima, quindi poche nel 2018–19.
  **Griglia degli strike**: ricostruita dagli scambi visti fino al giorno (`op_griglia.py`).
- **Campione piccolo**: 22 operazioni chiuse per B0 (10 in OOS). Flusso perp vero solo dal 2020-04, funding dal 2020-01. Dati
  fino al 2026-11-21; l'operazione aperta del 16/11 è valutata a quella data ed esclusa dai conteggi.
- **Placebo di F3**: lunedì a caso con la stessa durata. Quando non si trovano date senza sovrapposizioni dopo 200 tentativi,
  alcune operazioni placebo si saltano.

## Deviazioni dal PREREG (dichiarate)
- **Holm per F1 e F2**: il PREREG non fissa il test. Usato un test appaiato a segni casuali sulle differenze per operazione
  rispetto a B0 (10.000 permutazioni), moltiplicato per 15 (F1) o 5 (F2). Per F3 si usa il p del placebo × 6.
- **Scelta su IS**: il capitale finale IS più alto fra le celle con DD IS non peggiore di B0 di oltre 3 punti. Il PREREG dice
  solo "scelta su IS".
- **Vicini**: F1 sono le celle adiacenti della griglia. F2 sono i parametri ±: 1,5/2,5×, 2,5/3,5×, 5/10 giorni; per U5, 21/45
  giorni. F3 sono le soglie adiacenti e le scadenze 21/45 giorni (per a anche 5% fuori). Per le celle con 2–3 vicini serve
  ≥ 75%.
- **"Utile", punto 2**: interpretato come "resta sopra 10.000 $ senza le 2 migliori", perché un segnale utile non deve battere B0.
- **Descrittivi aggiunti dopo i verdetti** (`op_extra.py`): B0 con scadenza ad almeno 21 giorni, e lo spread −20% con lo stesso vincolo.

## Ipotesi per un secondo ciclo (una sola, nata dalla diagnosi)
Le opzioni direzionali mensili (F3a, F3f, call sempre) perdono quasi solo quando entrano con IV alta. Ipotesi: "call o put alla pari
a 30 giorni solo se la IV a 30 giorni è sotto il terzile alto delle ultime 52 settimane, calcolato solo sul passato". Da provare
su F3a e su "call sempre", giudicandola contro "call sempre" e contro B0, con placebo nello stesso regime di IV. Esplorativa per
PREREG. Non riguarda B0, che è positivo anche con IV alta.

## Lezione proposta per RESEARCH.md
"Opzioni su BTC (ciclo 24–25/11, superficie Deribit 2018–26): comprare opzioni non crea un vantaggio proprio. B0 vale quanto
i segnali di W3.2 a metà dimensione, con perdita massima del 5% per operazione; struttura, uscite e segnali indipendenti non lo
battono in OOS. I segnali "in più" sono esposizione quasi continua alla deriva di BTC (placebo p ≥ 0,14). La scelta della scadenza
(18 contro 46 giorni) sposta il risultato del 15% senza segno stabile: è rumore, non una leva."
