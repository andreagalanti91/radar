# Scadenze delle opzioni (OPEX) su BTC · controllo descrittivo veloce · 26/11/2026

**Verdetto: utile solo come contesto, non come segnale.** Attorno alle scadenze mensili Deribit BTC non si muove in modo più
ampio né più stretto dei venerdì normali; c'è una leggera tendenza al rialzo nei 7 giorni dopo la scadenza (mediana +1,7%
contro −0,1%, su nel 62% dei casi contro 48%, p ≈ 0,02), ma è una sola misura su circa trenta, concentrata nel 2020–21
(+5,0% e +2,6%) e debole dal 2022 (+0,5/+1,3%): non regge come vantaggio. Nessuna modifica a W3.2.

Non preregistrato: risponde alla domanda dell'utente "check dell'OPEX (scadenze delle opzioni, up o down)".
`python3 check.py` → `risultati.txt` (circa 30 secondi).

- **Scadenza** = ultimo venerdì del mese alle 08:00 UTC (Deribit); trimestrali = marzo, giugno, settembre, dicembre.
- **Controllo** = tutti gli altri venerdì. Ogni venerdì ha comunque una scadenza settimanale: il confronto misura la scadenza
  grande contro quella piccola, a parità di giorno.
- **Dati**: `data/spot.csv` (giornaliero, 86 mensili dal 09/2019, di cui 29 trimestrali, contro 289 altri venerdì) e
  `data/spot_1h.csv` (24 ore prima e dopo le 08:00, 57 mensili dal 02/2022). p = permutazione sulla differenza delle mediane.

| misura (mediana) | mensili | trimestrali | altri venerdì |
|---|---|---|---|
| \|rendimento\| 7 g prima | 3,7% | 3,5% | 4,3% |
| range 7 g prima | 10,2% | 10,3% | 10,7% |
| range del venerdì | 4,2% | 4,2% | 4,1% |
| rendimento 7 g dopo | **+1,7%** (p 0,02) | +0,9% (p 0,40) | −0,1% |
| 7 g dopo in rialzo | 62% | 62% | 48% |
| range 7 g dopo | 10,6% | 9,3% | 11,1% |
| \|rendimento\| 24 h dopo le 08:00 | 0,85% (p 0,10) | 0,77% | 1,26% |

- **Ampiezza**: nessuna differenza dimostrabile prima, il giorno e dopo (p da 0,1 a 0,9). Nelle 24 ore dopo le 08:00 il prezzo
  si muove un po' meno (0,85% contro 1,26%, p 0,10): non significativo.
- **Direzione**: il venerdì di scadenza tende a chiudere un po' in calo (−0,4%, p 0,06), la settimana dopo un po' in rialzo.
  Il movimento della settimana prima non si inverte dopo (correlazione +0,07).
- **Trimestrali**: stesse indicazioni, più deboli (29 casi, nessuna misura significativa).
- **Massimo dolore** (lo strike dove le opzioni in scadenza valgono meno per chi le ha comprate): **non ricostruibile** nel
  passato, serve l'open interest per strike di ogni scadenza, che le API pubbliche non danno all'indietro. Da oggi
  `radar/opex.py` salva uno snapshot giornaliero in `data/opex/snap.jsonl` (massimo dolore, muri, put/call, prezzo): la verifica
  della "calamita" (il prezzo si avvicina al massimo dolore nell'ultima settimana?) si potrà fare solo dopo almeno 12–18
  scadenze mensili, cioè fra un anno o più.

Uso nel tool: scheda "OPEX · solo contesto" in Posizioni (radar/opex.py), descrittiva; nessun avviso, W3.2 non cambia.
