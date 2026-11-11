# Scelta di modello ed effort

I nomi e le versioni dei modelli cambiano nel tempo. Questa guida ragiona per **fasce**: associa a ogni fascia il modello più recente che l'utente ha a disposizione. Se nell'ambiente vedi l'elenco dei modelli disponibili, usa quello.

## Fasce di modello

| Fascia | Famiglia tipica | Quando sceglierla |
|---|---|---|
| Veloce / economica | **Haiku** | Domande fattuali, riformulazioni, classificazioni, estrazioni semplici, piccole modifiche, risposte brevi. Ottima anche per i sottoagenti di sola lettura o ricerca. |
| Bilanciata | **Sonnet** | La maggior parte del lavoro quotidiano: codice di media complessità, documenti, analisi, ricerche mirate, compiti a più passaggi ben definiti. |
| Massima qualità | **Opus** | Ragionamento difficile, architetture, codice su molti moduli, scrittura dove conta molto la qualità, compiti lunghi e ambigui, revisione critica, coordinamento di più sottoagenti. |

Famiglia attuale (Claude 5): Haiku 5.5 (veloce), Sonnet 5.5 (bilanciata), Opus 5.5 (massima qualità), Fable 5.x (fascia più alta, per i compiti più lunghi e difficili). Verifica sempre quali sono disponibili all'utente.

Se l'utente ha accesso ad altri modelli (es. nuove famiglie o varianti), collocali nella fascia giusta in base a quello che sai di loro. Se non sei sicuro, dillo invece di inventare.

## Livelli di effort

L'effort decide quanto il modello ragiona prima di rispondere: più alto vuol dire più qualità e più consumo.

| Effort | Quando |
|---|---|
| **low** | Compiti semplici e chiari, risposte rapide. |
| **medium** | Default ragionevole per lavoro definito con qualche passaggio. |
| **high** | Problemi con insidie, debugging, analisi accurate, scrittura curata. |
| **xhigh** | Lavoro lungo e complesso dove un errore costa caro. |
| **max** | Solo per i problemi più difficili, quando il consumo non è un vincolo. |

Se nell'ambiente ci sono meno livelli, usa quelli disponibili.

## Regole pratiche

- Scegli il modello più economico che fa bene il lavoro: un compito semplice su Opus/max spreca limiti d'uso.
- Se il compito è lungo ma ripetitivo (es. 50 file da trasformare allo stesso modo), conviene la fascia bilanciata con effort medio, con un controllo finale più accurato.
- Per i compiti lunghi con sottoagenti: modello forte nella sessione principale (pianifica e verifica), modelli più economici nei sottoagenti di sola lettura o ricerca.
- Proponi sempre un'alternativa più economica per i prompt lunghi e dì cosa si perderebbe.
- Nel "perché" indica: complessità, durata stimata (breve / decine di minuti / ore), rapporto qualità/consumo.
