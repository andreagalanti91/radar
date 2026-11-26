"""Conteggi dei segnali (nessun rendimento). Output: eventi.csv, conteggi.txt"""
import sys; sys.path.insert(0, '.')
import pandas as pd
from dorito_lib import daily, resample_year, lele, VARIANTS
d = daily(include_partial=False)  # ultimo giorno chiuso: 25/11/2026
ev = []
for tf in (1, 3):
    b = resample_year(d, tf)
    for vn, kw in VARIANTS.items():
        s = lele(b, **kw)
        for t, v in s[s != 0].items():
            end = b.index[b.index.get_loc(t)] + pd.Timedelta(days=int(b.loc[t, 'n']) - 1) if tf > 1 else t
            ev.append(dict(tf=f"{tf}D", variante=vn, apertura_barra=t.date(), chiusura_barra=end.date(),
                           lato="nero_long" if v > 0 else "rosso_short", close=round(b.loc[t, 'close'], 2)))
E = pd.DataFrame(ev)
E.to_csv('eventi.csv', index=False)
E['anno'] = pd.to_datetime(E.chiusura_barra).dt.year
with open('conteggi.txt', 'w') as f:
    for (tf, vn), g in E.groupby(['tf', 'variante']):
        g = g[g.anno >= 2018]
        t = g.pivot_table(index='anno', columns='lato', values='close', aggfunc='count', fill_value=0)
        t['totale'] = t.sum(axis=1)
        f.write(f"\n{tf} {vn} (dal 2018; ultimo giorno chiuso 25/11/2026)\n{t.to_string()}\n"
                f"totale dal 2018: {len(g)}  dal 2021: {(g.anno >= 2021).sum()}\n")
print(open('conteggi.txt').read())
print(E[(E.tf == '3D') & (E.variante == 'IS_40_10') & (E.anno >= 2018)].to_string(index=False))
