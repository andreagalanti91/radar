"""Statistiche operazione per operazione di W3.2 (Radar) e v1, per periodo d'ingresso. Risultato = sul capitale."""
import pandas as pd, numpy as np
w = pd.read_csv('w32_radar_trades.csv', parse_dates=['entra','esce']).rename(columns={'sul_capitale':'r'})
v = pd.read_csv('import/v1_operazioni_2018_2026.csv', parse_dates=['entra','esce']).rename(columns={'risultato':'r'})
w = w[w.esce.notna() & (w.esce.astype(str)!='NaT')]
def stats(d):
    d = d.dropna(subset=['r']); r = d.r; win, los = r[r>0], r[r<=0]
    seq = (r<=0).astype(int).tolist(); mx=c=0
    for x in seq: c = c+1 if x else 0; mx = max(mx,c)
    dur = (d.esce-d.entra).dt.days
    pf = win.sum()/abs(los.sum()) if len(los) and los.sum()!=0 else np.inf
    return {'operazioni':len(r),'long/short':f"{(d.verso=='long').sum()}/{(d.verso=='short').sum()}",'win rate':f"{len(win)/len(r)*100:.0f}%",
            'guadagno medio':f"{win.mean()*100:+.1f}%" if len(win) else '—','perdita media':f"{los.mean()*100:+.1f}%" if len(los) else '—',
            'rapporto guadagno/perdita':f"{win.mean()/abs(los.mean()):.1f}" if len(win) and len(los) and los.mean()!=0 else '—',
            'profit factor':f"{pf:.1f}" if np.isfinite(pf) else '∞','attesa per operazione':f"{r.mean()*100:+.1f}%",
            'migliore':f"{r.max()*100:+.1f}%",'peggiore':f"{r.min()*100:+.1f}%",'perdite di fila (max)':mx,
            'durata media (giorni)':f"{dur.mean():.0f}",'win rate long':f"{(d[d.verso=='long'].r>0).mean()*100:.0f}%" if (d.verso=='long').any() else '—',
            'win rate short':f"{(d[d.verso=='short'].r>0).mean()*100:.0f}%" if (d.verso=='short').any() else '—'}
rows=[]
for nome,a,b in [('Dal 2018','2018-01-01','2100'),('2018–2021','2018-01-01','2022-01-01'),('2022–2026','2022-01-01','2100'),('Dal 2021','2021-01-01','2100')]:
    for s,d in [('W3.2',w),('v1',v)]:
        x=d[(d.entra>=a)&(d.entra<b)]; rows.append({'periodo':nome,'strategia':s,**stats(x)})
t=pd.DataFrame(rows); t.to_csv('tab_operazioni.csv',index=False); print(t.T.to_string())
