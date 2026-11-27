# Deviazioni dal PREREG (commit f558fb4)

Nessuna deviazione dalle regole, dai parametri o dai criteri. Precisazioni di implementazione (fase2.py), decise prima di
leggere i risultati:
- **Criterio 7 (non concentrato):** si riporta a R 0,25 una operazione toccata alla volta (BTC e ETH, finestra dell'insieme) e si
  prende il ripristino che abbassa di più il CAGR/DD insieme; quel valore deve restare sopra W3.2.
- **Placebo:** gli insiemi di operazioni candidate comprendono la posizione aperta (come nei conteggi); estrazione senza
  ripetizione dentro la prova, prove indipendenti fra loro (quindi con ripetizione fra prove, come dichiarato per D3 e D4).
- **Controllo:** l'insieme calcolato con le date ridotte coincide al dollaro con quello calcolato con la regola (assert nel codice).
- **MAR** = rendimento totale / |DD| (definizione di RESEARCH.md); è informativo.

- Procedura: conteggi committati in 010ee98, contemporaneo a f558fb4 e prima di fase2.py (il PREREG li voleva nello stesso commit). Un solo generatore con seme 20261127 consumato in ordine D1→D4: i p di D2–D4 dipendono dall'ordine (riproducibile). Il controllo "operazioni identiche" è stato fatto fuori da fase2.py (revisione).
