import pandas as pd, numpy as np
R='/home/user/radar/'
p=pd.read_csv(R+'data/perp.csv',index_col='date',parse_dates=True); s=pd.read_csv(R+'data/spot.csv',index_col='date',parse_dates=True)
d=pd.DataFrame({'c':s.close,'ps':p.taker_buy_volume/p.volume,'ss':s.taker_buy_volume/s.volume,'pq':p.quote_volume,
 'pd':2*p.taker_buy_volume-p.volume,'pv':p.volume,'sd':2*s.taker_buy_volume-s.volume,'sv':s.volume}).dropna(subset=['c'])
z=lambda x:(x-x.rolling(180).mean())/x.rolling(180).std()
for N in (3,5,7):
    d[f'pz{N}']=z(d.pd.rolling(N).sum()/d.pv.rolling(N).sum()); d[f'sz{N}']=z(d.sd.rolling(N).sum()/d.sv.rolling(N).sum())
print('ULTIMI 10 GIORNI'); t=d.tail(10); print(pd.DataFrame({'perp_buy%':t.ps*100,'perp_$B':t.pq/1e9,'perp_delta_BTC':t.pd,'spot_buy%':t.ss*100,'spot_delta_BTC':t.sd,'pz5':t.pz5,'sz5':t.sz5}).round(2))
for h in (1,3,7,14): d[f'r{h}']=d.c.shift(-h)/d.c-1
d=d[d.index>='2021-01-01']
V={'V1':(5,-1,'b'),'V2':(3,-1,'b'),'V3':(7,-1,'b'),'V4':(5,-.75,'b'),'V5':(5,-1.25,'b'),'V6':(5,-1,'s'),'V7':(3,-1,'s'),'V8':(7,-1,'s')}
def ev(N,ZA,k):
    A=((d[f'pz{N}']<ZA)&(d[f'sz{N}']>=0)).astype(int)
    rec=A.shift(1).rolling(5).max()==1
    cond=(d.ps.between(.495,.505)|(d[f'pz{N}']>-.25)) if k=='b' else d.ps>.505
    e=rec&cond&(A==0); out=[];last=None
    for t in d.index[e]:
        if last is None or (t-last).days>=7: out.append(t); last=t
    return pd.DatetimeIndex(out)
w3=pd.to_datetime(pd.read_csv(R+'research/weekly_w3_trades.csv').ingresso)
rng=np.random.default_rng(1); rows=[]
for k,(N,ZA,kind) in V.items():
    E=ev(N,ZA,kind); r={'v':k,'n':len(E)}
    for h in (1,3,7,14): r[f'ex{h}']=(d.loc[E,f'r{h}'].mean()-d[f'r{h}'].mean())*100
    pool=d.r7.dropna().values; m=d.loc[E,'r7'].dropna().mean()
    r['p7']=np.mean([rng.choice(pool,len(E)).mean()>=m for _ in range(2000)])
    for a,b,l in (('2021','2023','e21'),('2024','2027','e24')):
        x=d.loc[a:b]; Ex=[t for t in E if a<=str(t.year)<=b]
        r[l]=(x.loc[Ex,'r7'].mean()-x.r7.mean())*100; r['n'+l]=len(Ex)
    cap=1e4
    for t in E:
        v=d.r7.get(t)
        if pd.notna(v): cap*=(1+v)*(1-.001)
    r['cap']=cap; r['top-1']=cap/(1+d.loc[E,'r7'].max())
    r['wr']=(d.loc[E,'r7']>0).mean()*100
    r['w3_14g']=sum(any(0<=(t-e).days<=14 for e in E) for t in w3)
    r['w3_att']=round(len(w3)*(1-(1-15/len(d))**len(E)),1)
    rows.append(r)
print(pd.DataFrame(rows).round(2).to_string())
print('BH',d.c.iloc[-1]/d.c.iloc[0]*1e4, 'base r7%',d.r7.mean()*100)
print('eventi V1 ultimi:',ev(5,-1,'b')[-5:].date, 'V6:',ev(5,-1,'s')[-5:].date)
