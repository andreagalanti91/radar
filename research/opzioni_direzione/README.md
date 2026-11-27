# Opzioni e direzione di BTC · skew, put/call, DVOL, massimo dolore, scelta put/call · 27/11/2026

PREREG `14cadc0` (committato da solo, prima dei risultati). Deviazioni dichiarate in `DEVIAZIONI.md`. W3.2 non è toccata.

## Verdetto
| Ipotesi | Esito |
|---|---|
| **H1** skew 25-delta → direzione a 7/30 g | **no**: nessuna correlazione OOS significativa; a 7 g il segno si inverte fra IS e OOS |
| **H2** rapporto put/call → direzione (contrarian o tendenza) | **no**: il segno IS (negativo) si inverte in OOS a 7 e 30 g |
| **H3** DVOL → direzione | **no** (ΔDVOL → 30 g: segno invertito in OOS) |
| **H3** DVOL → ampiezza | **strumento valido** (controllo positivo): ρ OOS 0,48, Holm 0,0008, ETH sì. Dice **quanto** si muoverà BTC, non **dove** |
| **H4** il prezzo converge al massimo dolore | **no**: il prezzo è andato verso il massimo dolore solo nel 31% (IS) e nel 44% (OOS) delle scadenze; placebo p 0,56–0,64 |
| **H5** put/call di B0r solo se l'opzione non è cara | **no** (descrittivo): in OOS non cambia nulla; in IS avrebbe tolto 3 operazioni vincenti |

**Nessun indicatore di opzioni dice la direzione di BTC.** La direzione per operare in opzioni resta quella del segnale di W3.2
(regola B0r). Il DVOL serve solo a stimare l'ampiezza del movimento atteso e il costo dell'opzione.

## Test (BTC, domeniche 2021–26; IS 2021–23, OOS 2024–26; Holm su 8)
ρ = correlazione di Spearman. Il p OOS è a una coda nel verso IS, con placebo a slittamento circolare (seme 20261127).

| V | Misura | n IS/OOS | ρ IS | ρ OOS | p OOS | Holm | Vicini stesso segno | ETH ρ OOS (p) |
|---|---|---|---|---|---|---|---|---|
| V1 | RR25 → r7 | 145/138 | +0,003 | −0,175 | 0,99 | 1 | 0/3 | −0,08 (0,89) |
| V2 | RR25 → r30 | 145/135 | −0,122 | −0,098 | 0,20 | 1 | 3/3 | −0,02 (0,43) |
| V3 | put/call → r7 | 157/149 | −0,099 | +0,074 | 0,80 | 1 | 0/2 | −0,03 (0,36) |
| V4 | put/call → r30 | 157/146 | −0,133 | +0,039 | 0,67 | 1 | 1/2 | +0,10 (0,71) |
| V5 | ΔDVOL 7 g → r30 | 144/146 | +0,090 | −0,057 | 0,77 | 1 | 0/2 | −0,01 (0,57) |
| V6 | DVOL → volatilità realizzata a 30 g | 145/146 | +0,607 | **+0,484** | 0,0001 | **0,0008** | 1/1 | +0,23 (0,036) |
| V7 | convergenza al massimo dolore − specchio | 36/34 scadenze | −0,78 pt | −0,16 pt | 0,56 | 1 | 1/2 | — |
| V8 | B0r saltando VRP > q75 IS | 4/6 operazioni | — | — | 1,00 | 1 | — | — |

V7 in dettaglio:
- Quota di scadenze in cui il prezzo è andato verso il massimo dolore: 31% in IS, 44% in OOS (soglia 55%).
- Placebo con uno strike a caso entro ±15%: p 0,64 in OOS, 0,70 su tutto il periodo.
- Distanza mediana fra massimo dolore e prezzo a E−7: 4,6%.

## Regole operative (10.000 $, 1x, costi 0,10%/lato, funding; terzili IS)
| Regola | IS 2021–23 | DD | OOS 2024–26 | DD | MAR OOS | Dal 2021 | DD | Op. | WR | Placebo OOS | OOS senza le 2 migliori |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **W3.2 com'è** | 33.465 | −19,3 | 25.250 | −21,1 | 7,22 | **84.330** | −21,1 | 14 | 93% | — | 13.575 |
| Buy & hold | 14.619 | −76,6 | 14.241 | −53,0 | 0,80 | 20.819 | −76,6 | — | — | — | — |
| V1 skew, 7 g | 6.759 | −57,7 | 2.948 | −72,3 | −0,98 | 1.993 | −81,6 | 63 | 46% | 1,00 | 2.452 |
| V2 skew, 30 g | 7.574 | −67,0 | 24.961 | −19,3 | 7,76 | 18.906 | −67,0 | 63 | 48% | 0,0001* | 10.851 |
| V3 = V4 put/call | 35.649 | −45,1 | 5.256 | −66,6 | −0,71 | 18.718 | −66,6 | 101 | 42% | 0,65 | 3.317 |
| V5 ΔDVOL | 11.916 | −54,1 | 5.088 | −64,3 | −0,76 | 6.069 | −64,3 | 128 | 45% | 0,74 | 3.744 |
| V7 verso il massimo dolore | 4.873 | −65,5 | 6.541 | −43,1 | −0,80 | 3.187 | −79,1 | 70 | 37% | 0,95 | 5.621 |
| **B0r** (opzioni, regola in uso) | 18.432 | −8,7 | 16.198 | −9,8 | 6,31 | 29.856 | −9,8 | 13 | 85% | — | 10.175 |
| V8 B0r con filtro VRP q75 | 15.443 | −8,7 | 16.198 | −9,8 | 6,31 | 25.014 | −9,8 | 10 | 90% | — | 10.175 |

\* p minimo raggiungibile circa 1/130 (DEVIAZIONI 3).

Quartili, quintili, ETH e tutti i periodi sono in `regole.csv`.

- **V2 (skew a 30 g, long quando le call sono care, short quando le put sono care) è l'unico caso da guardare con attenzione,
  ma non passa.** In OOS fa quanto W3.2 (24.961 $, DD −19%, placebo basso, sopra 10.000 $ senza le 2 migliori), ma nell'IS
  2021–23, dove sono stati stimati verso e soglie, perde il 24% con DD −67%. La correlazione OOS è −0,098, sotto la soglia di
  0,10 e con p 0,20. Su ETH, con gli stessi parametri, fa +13% con DD −57%. È un buon periodo, non un vantaggio stabile.
- **V3 = V4** (put/call contrarian nel verso IS) è il caso opposto: +256% in IS, −47% in OOS. È il segno tipico di una
  relazione che non esiste.
- **Opzioni care in media**: il DVOL supera la volatilità realizzata nei 30 giorni successivi nel 72% delle settimane (mediana
  1,21; IS 1,22, OOS 1,20; ETH 1,12). Chi compra opzioni senza un segnale paga in media il 20% in più di quanto BTC si muova.

## Scadenza del 27/11/2026 (descrittiva, fuori dal test)
- **Istantanea Deribit delle 07:38**: massimo dolore 70.000 $ con l'indice a 61.527 $ (13,8% sopra).
- **Regolamento Deribit alle 08:00**: 61.600 $.
- **Proxy a E−7**: 74.000 $ con BTC a 61.859 $.

Il prezzo non si è avvicinato al massimo dolore: è rimasto lì dov'era.

## Quando comprare put o call (dai dati, nessun consiglio personale)
- **Direzione**: call se W3.2 è long, put se è short (regola B0r, `research/opzioni_studio`). Skew, put/call, DVOL e massimo
  dolore non aiutano a scegliere fra put e call: nessuno predice la direzione in OOS.
- **Scadenza**: il venerdì più vicino a 30 giorni fra 20 e 50 giorni. Sotto i 20 giorni il risultato diventa molto più casuale
  (studio opzioni).
- **Prezzo d'esercizio**: alla pari. Vendita all'uscita di W3.2, mai rinnovi, niente prese di profitto a 2×/3×.
- **Quando non comprare**:
  - fra un segnale e l'altro: le opzioni costano in media più del movimento che pagano (DVOL/realizzata 1,21);
  - con scadenza sotto 20 giorni;
  - per "giocare" la scadenza o il massimo dolore.
- **Opzioni care**: saltare la call/put di B0r quando il VRP è alto non ha aiutato. Nel 2021–23 avrebbe tolto 3 operazioni
  vincenti (18.432 → 15.443 $); nel 2024–26 non avrebbe cambiato nulla. Il segnale conta più del prezzo pagato. Il costo
  alto si gestisce con la dimensione, non saltando il segnale.
- **Dimensione**: 5% del conto o una cifra fissa per operazione. La perdita massima è il premio. Dal 2021 B0r fa 29.856 $ con
  DD −9,8% (W3.2 a 1x: 84.330 $, DD −21%).
- **Ampiezza**: il DVOL indica bene quanto si muoverà BTC nel mese (ρ 0,48 in OOS). È utile per leggere il movimento atteso,
  non per scegliere il lato.

## Limiti
- **Skew**: per fasce di delta (0,15–0,35), con F = indice. Mancano 23 domeniche su 308 (nessuna scadenza fra 20 e 50 giorni).
- **Massimo dolore**: è un proxy dal volume campionato degli ultimi 28 giorni, non open interest. Errore mediano 3,25 punti % su
  8 scadenze di oggi, sempre dal lato giusto rispetto al prezzo. H4 è un test del proxy; l'open interest vero si raccoglie
  solo dal 26/11/2026 (`data/opex/snap.jsonl`).
- **Put/call**: volumi della sola domenica (il vicino lun–dom dal campione dà lo stesso esito).
- **Campione**: circa 140 domeniche per periodo, 34–36 scadenze per periodo, 13 operazioni B0r dal 2021. V8 è descrittivo.

## File
- `PREREG.md`
- `DEVIAZIONI.md`
- `scarica.py`, `costruisci.py`, `conteggi.py` (fase 1)
- `fase2.py`: produce `risultati.txt`, `test.csv`, `vicini.csv`, `regole.csv`, `maxpain_osservazioni.csv` e `b0r_filtro.csv`, circa 1 minuto

## Lezione proposta (128)
"**Lezione 128**: opzioni come bussola della direzione di BTC (research/opzioni_direzione, PREREG 14cadc0, 8 varianti, Holm).
- **Direzione**: skew 25-delta, put/call e variazione del DVOL non predicono la direzione a 7/30 giorni. In OOS il segno si
  inverte o la correlazione resta sotto 0,10; su ETH nemmeno.
- **Massimo dolore**: è un proxy dal volume, validato sull'open interest di oggi (errore mediano 3%). Il prezzo non converge
  verso il massimo dolore nell'ultima settimana: ci va nel 31–44% delle scadenze, placebo p 0,56–0,64. Il 27/11/2026 il
  massimo dolore era a 70.000 $ e il regolamento a 61.600 $.
- **Ampiezza**: solo il livello del DVOL predice l'ampiezza dei movimenti a 30 giorni (ρ OOS 0,48, Holm 0,0008).
- **Costo**: il DVOL supera la volatilità poi realizzata nel 72% delle settimane, quindi comprare opzioni senza segnale costa.
  Saltare le call/put di B0r quando sono care toglie vincenti.
- **Regola**: per put o call resta B0r (lato di W3.2, 20–50 giorni, alla pari, 5%).
- **Metodo**: una regola che va bene solo in OOS (skew a 30 g: +150% OOS, −24% IS) non è un vantaggio. Va giudicata con il
  periodo in cui sono state scelte le soglie e con la correlazione, non con il solo capitale finale."
