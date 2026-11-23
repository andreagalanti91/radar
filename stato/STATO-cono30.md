# STATO · cono di probabilità a 30 giorni (card "Fra 30 giorni")
**Stato: COMPLETATO in locale (23/11/2026) · da committare, pubblicare e verificare sul sito a cura della regia**

- Studio: research/cono30 (PREREG 17b9a49, ADDENDUM 3049ee9 esplorativo). Passa solo (b) bootstrap + deriva storica:
  copertura 80% 78,7/78,4/77,5 (totale 78,2%), 50% 50,6/51,5/54,7, errore di calibrazione del tocco 4,6 punti, Brier 0,1761
  (rif. 0,1799). (a) e (c) falliscono di 0,3–0,7 punti sul 50% del 2024–26. Variante con deriva dal flusso perp: NON adottata.
- Tool: radar/cone.py + radar/cone_seed.csv, report["cone"] in radar/cli.py, card cnCard in radar/dashboard_template.html,
  tests/test_cone.py, README (Dashboard), memoria/03-tool/MODULI.md. Registro data/cone_log.csv (nasce al primo giro).
- Render: scratchpad/cono/ (render_cono.py, shot_cono.js; 400/1280, chiaro/scuro).
- Prossima azione: commit dei file (non il PREREG, già committato), deploy, verifica sul sito; lezione da numerare in RESEARCH.md.
