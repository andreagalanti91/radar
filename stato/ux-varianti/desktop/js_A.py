# Variante A: la barra delle uscite misura la propria colonna (BTC ed ETH affiancate), non tutta la scheda
OLD = 'const W = Math.max(240, ($("qExitB").clientWidth || 320) - 4);'
NEW = ('const qb = $("qExitB"), qc = getComputedStyle(qb).gridTemplateColumns.split(" ").length || 1;   // colonne della scheda (A: BTC | ETH su desktop)\n'
       '    const W = Math.max(240, ((qb.clientWidth || 320) - 28 * (qc - 1)) / qc - 4);')
