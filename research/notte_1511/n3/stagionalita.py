"""Stagionalità solo DESCRITTIVA (PREREG: esclusa dai test decisivi): rendimento medio giornaliero per giorno della settimana
e per mese, IS 2021–23 contro OOS 2024–26, con t grezzo. Uso: python research/notte_1511/n3/stagionalita.py >> risultati.txt"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from radar.data import load_all  # noqa
px = load_all()["spot"]["close"].dropna()
r = (np.log(px).diff() * 100).loc["2021":]
print("\n" + "=" * 100)
print("Stagionalità descrittiva (rendimento log giornaliero medio, punti %; t = media/err.std.)")
names = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
for lab, key in (("giorno", r.index.dayofweek), ("mese", r.index.month)):
    g = pd.DataFrame({"r": r, "k": key, "oos": r.index >= "2024-01-01"})
    out = []
    for k, x in g.groupby("k"):
        a, b = x.loc[~x.oos, "r"], x.loc[x.oos, "r"]
        out.append(f"{names[k] if lab == 'giorno' else k}: IS {a.mean():+.2f} (t {a.mean()/a.std()*np.sqrt(len(a)):+.1f}) "
                   f"OOS {b.mean():+.2f} (t {b.mean()/b.std()*np.sqrt(len(b)):+.1f})")
    print(f"Per {lab}:\n  " + "\n  ".join(out))
