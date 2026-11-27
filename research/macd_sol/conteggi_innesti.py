"""Fase 1 (nessun rendimento): quanti ingressi di W3.2 bloccherebbe W-F e quante settimane in posizione attiverebbero W-U."""
import sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import motore as M  # noqa: E402
L = M.L
out = []
for a, s in (("BTC", "2021-01-01"), ("ETH", "2021-01-11"), ("SOL", "2021-01-11")):
    f = L.cfeats(a); E = str(f.index[-1].date()); o = L.csim(f, s, E); w = o["weekly"]
    m, _ = M.macd(w["close"]); units = [("pct", 100 * m / w["close"], M.PCT)] + ([("abs", m, M.ABS)] if a == "SOL" else [])
    for u, x, th in units:
        tr = L.otrades(o); bl = bs = ul = us = 0
        for t in tr:
            sig = pd.Timestamp(t["signal"])
            if t["side"] == "long" and x.loc[sig] >= th["sell"]: bl += 1
            if t["side"] == "short" and x.loc[sig] < th["hi"]: bs += 1
            b = pd.Timestamp(t["exit"]) if t.get("exit") else w.index[-1] + pd.Timedelta(days=1)
            wk = x[(x.index >= pd.Timestamp(t["entry"])) & (x.index < b)]
            if t["side"] == "long" and (wk >= th["sell"]).any(): ul += 1
            if t["side"] == "short" and (wk <= th["lo"]).any(): us += 1
        nl = sum(t["side"] == "long" for t in tr); ns = len(tr) - nl
        out.append(f"{a} {u} dal {s}: trade W3.2 {nl} long + {ns} short · W-F blocca {bl} long e {bs} short (sui segnali dei trade base) · "
                   f"W-U toccherebbe {ul} long e {us} short (soglia raggiunta durante il trade)")
txt = "\n".join(out); print(txt); (HERE / "conteggi_innesti.txt").write_text(txt + "\n")
