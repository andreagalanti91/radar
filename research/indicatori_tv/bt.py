import sys; sys.path.insert(0,sys.argv[1]); sys.path.insert(0,'/tmp/radar-work/ta-macd/scripts')
import numpy as np, pandas as pd
from ind import pmo, zeii, PX, weekly
P0=('2017-01-01','2020-12-31'); P1=('2021-01-01','2026-11-01')
def dd(e): return float((e/e.cummax()-1).min())
def latch(on,off,idx):
    s=[];p=0
    for a,b in zip(on.reindex(idx).fillna(False),off.reindex(idx).fillna(False)):
        if a: p=1
        elif b: p=0
        s.append(p)
    return pd.Series(s,idx)
def run(state,a,b,daily,short,fee=0.001,slip=0.001):
    f=PX[(PX.index>=pd.Timestamp(a))&(PX.index<=pd.Timestamp(b))]
    O=f.open.values;C=f.close.values;FU=f.funding.fillna(0).values if 'funding' in f else np.zeros(len(f))
    eq=1.;pos=0;ent=0;tr=[];E=[];tgt=None;cash=1.
    for i,d in enumerate(f.index):
        if tgt is not None and tgt!=pos:
            if pos: r=pos*(O[i]*(1-slip*pos)/ent-1); eq*=(1+r)*(1-fee); tr.append(r); pos=0
            if tgt: pos=tgt; ent=O[i]*(1+slip*pos); eq*=(1-fee)
            tgt=None
        mtm=eq*(1+pos*(C[i]/ent-1)) if pos else eq
        E.append(mtm)
        if d in state.index:
            v=state.loc[d]; v=0 if pd.isna(v) else int(v)
            if not short and v<0: v=0
            tgt=v
    if pos: tr.append(pos*(C[-1]/ent-1))
    e=pd.Series(E,f.index); t=np.array(tr) if tr else np.zeros(1)
    return dict(n=len(tr),rend=e.iloc[-1]-1,dd=dd(e),wr=(t>0).mean(),worst=t.min())
def bhs(a,b,dt):
    r=PX.close.loc[a:b].pct_change().fillna(0).values; lo,hi=0,3
    for _ in range(40):
        x=(lo+hi)/2;q=np.cumprod(1+x*r);d=(q/np.maximum.accumulate(q)-1).min()
        hi,lo=(x,lo) if d<dt else (hi,x)
    return np.cumprod(1+x*r)[-1]-1
W=weekly(); Dd=PX.copy()
rows=[]
for tf,df in (('giornaliero',Dd),('settimanale',W)):
    P=pmo(df); Z=zeii(df); idx=df.index
    S={}
    S['PMO trend (verde=long, rosso=short/fuori)']=P.trend
    S['Zeiierman bias (Z-Trend>−50 e Core verde)']=pd.Series(np.where((Z.tz>-50)&(Z.core==1),1,np.where((Z.tz<-50)&(Z.core==-1),-1,0)),idx)
    S['Zeiierman incrocio Pulse/Trend']=pd.Series(np.where(latch(Z.xup,Z.xdn,idx)==1,1,-1),idx)
    S['PMO verde + Zeiierman bias long']=pd.Series(np.where((P.trend==1)&(Z.tz>-50)&(Z.core==1),1,np.where((P.trend==-1)&(Z.tz<-50)&(Z.core==-1),-1,0)),idx)
    for nm,st in S.items():
        for short in (False,True):
            row=dict(tf=tf,regola=nm,lato='long+short' if short else 'solo long')
            for p,(a,b) in (('P0',P0),('P1',P1)):
                m=run(st,a,b,tf=='giornaliero',short)
                row.update({f'{p}_n':m['n'],f'{p}_rend':round(m['rend']*100),f'{p}_dd':round(m['dd']*100,1),f'{p}_wr':round(m['wr']*100),f'{p}_worst':round(m['worst']*100,1),f'{p}_bh':round(bhs(a,b,m['dd'])*100)})
            row['P1_10k']=round(10000*(1+row['P1_rend']/100)); row['regge']=row['P0_rend']>row['P0_bh'] and row['P1_rend']>row['P1_bh']
            rows.append(row)
    last=df.index[-1]; print(tf,'oggi',last.date(),'PMO change',round(P.change.iloc[-1],3),'trend',P.trend.iloc[-1],'| Z pz',round(Z.pz.iloc[-1],1),'tz',round(Z.tz.iloc[-1],1),'core',Z.core.iloc[-1],'est',Z.est.iloc[-1])
    c=df.close; u=Z.index[Z.ubk & (Z.index>='2017-01-01')]
    fw={k:((c.shift(-k)/c-1).loc[u]*100).round(1).tolist() for k in ((7,30) if tf=='giornaliero' else (2,8))}
    print(tf,'rilasci della pressione ALTA (segnale ribassista) dal 2017:',[d.date().isoformat() for d in u]); print('  rendimento dopo:',fw)
df=pd.DataFrame(rows); df.to_csv(sys.argv[1]+'/risultati.csv',index=False)
pd.set_option('display.width',260); pd.set_option('display.max_colwidth',50)
print(df[['tf','regola','lato','P1_n','P1_rend','P1_dd','P1_wr','P1_worst','P1_10k','P1_bh','P0_rend','P0_dd','P0_bh','regge']].sort_values('P1_10k',ascending=False).to_string(index=False))
