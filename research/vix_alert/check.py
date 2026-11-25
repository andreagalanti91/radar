"""Controllo descrittivo veloce (non preregistrato) della regola dell'utente: VIX chiude sopra 30 → 'buy', sotto 15 → 'sell'.
Eventi = primo giorno di chiusura oltre la soglia dopo essere tornati dall'altra parte del riarmo (30→ riarmo sotto 25; 15→ riarmo sopra 17).
Rendimenti successivi di S&P 500 e BTC a 30/90/180 giorni di calendario, contro la media di tutti i giorni."""
import pandas as pd, numpy as np, os
H=os.path.dirname(os.path.abspath(__file__)); R=os.path.join(H,'..','..')
def load(p):
    d=pd.read_csv(p); d.columns=[c.lower() for c in d.columns]
    dc=[c for c in d.columns if 'date' in c][0]; cc='close' if 'close' in d.columns else d.columns[-1]
    s=pd.Series(d[cc].values,index=pd.to_datetime(d[dc]).dt.tz_localize(None).dt.normalize()); return s[~s.index.duplicated()].sort_index().astype(float)
vix=load(os.path.join(R,'research/multi_asset/data/VIX.csv.gz')); spx=load(os.path.join(R,'research/multi_asset/data/SPX.csv.gz'))
b=pd.read_csv(os.path.join(R,'data/spot.csv')); bc=[c for c in b.columns if 'time' in c.lower() or 'date' in c.lower()][0]
ix=pd.to_datetime(b[bc],unit='ms') if pd.api.types.is_numeric_dtype(b[bc]) else pd.to_datetime(b[bc])
ix=ix.dt.tz_localize(None) if ix.dt.tz is not None else ix
btc=pd.Series(b['close'].values,index=ix.dt.normalize()).sort_index(); btc=btc[~btc.index.duplicated()]
def events(v, soglia, riarmo, sopra):
    out=[]; armed=True
    for d,x in v.items():
        if armed and ((x>soglia) if sopra else (x<soglia)): out.append(d); armed=False
        elif not armed and ((x<riarmo) if sopra else (x>riarmo)): armed=True
    return out
def fwd(s,d,h):
    if d < s.index[0] or d+pd.Timedelta(days=h) > s.index[-1]: return np.nan
    a=s[s.index>=d]; t=s[s.index>=d+pd.Timedelta(days=h)]
    return np.nan if len(a)==0 or len(t)==0 else t.iloc[0]/a.iloc[0]-1
def base(s,h,start):
    s=s[s.index>=start]; r=[fwd(s,d,h) for d in s.index[::5]]; return np.nanmedian(r)*100, np.nanmean(np.array(r)>0)*100
for nome,s,start in [('S&P 500 dal 1990',spx,'1990-01-01'),('S&P 500 dal 2018',spx,'2018-01-01'),('BTC dal 2018',btc,'2018-01-01')]:
    v=vix[vix.index>=start]
    print(f'\n== {nome}')
    for lab,ev in [('VIX >30 (buy)',events(v,30,25,True)),('VIX <15 (sell)',events(v,15,17,False))]:
        row=[f'{lab}: {len(ev)} eventi']
        for h in (30,90,180):
            r=np.array([fwd(s,d,h) for d in ev]); r=r[~np.isnan(r)]
            if len(r): row.append(f'{h}g med {np.median(r)*100:+.1f}% su {np.mean(r>0)*100:.0f}%')
        print(' · '.join(row))
    print('riferimento (tutti i giorni): '+' · '.join(f'{h}g med {base(s,h,start)[0]:+.1f}% su {base(s,h,start)[1]:.0f}%' for h in (30,90,180)))
    if nome.startswith('BTC') or nome.endswith('2018'):
        print('date >30:', [d.strftime('%Y-%m-%d') for d in events(v,30,25,True)])
        print('date <15:', [d.strftime('%Y-%m-%d') for d in events(v,15,17,False)])
