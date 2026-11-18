import pickle, numpy as np, pandas as pd
from scipy.stats import norm, skew, kurtosis
D="/tmp/claude-0/-home-user-radar/4f01d4b8-8442-5751-908f-fb8502af4b0c/scratchpad/disr/"
eq18,eq21,p21,p18=pickle.load(open(D+"eq.pkl","rb"))
p21=np.array(p21); p18=np.array(p18)  # closed only
rng=np.random.default_rng(0)
def boot(p,yrs,n=20000):
    k=len(p); s=rng.choice(p,(n,k)); g=np.prod(1+s,1); c=g**(1/yrs)-1
    return np.percentile(c*100,[5,25,50,75,95]), (c<=0).mean()
print("closed 2021:",len(p21),"mean",p21.mean()*100, "18-20:",len(p18))
print("boot CAGR 2021 (12 chiusi, 5.6y):",boot(p21,5.6))
pall=np.concatenate([p18,p21]); print("boot CAGR 2018-26 (",len(pall),"chiusi, 8.6y):",boot(pall,8.6))
# geometric mean per trade CI
for nm,p in (("21",p21),("all",pall)):
    lg=np.log1p(p); m=lg.mean(); se=lg.std(ddof=1)/np.sqrt(len(lg)); print(nm,"log-ret/trade mean %.3f se %.3f t %.2f"%(m,se,m/se))
# rolling windows on combined weekly equity
e=pd.concat([eq18/eq18.iloc[0], (eq21/eq21.iloc[0])*(eq18.iloc[-1]/eq18.iloc[0])])
e=e[~e.index.duplicated()]
w=e.resample("W-SUN").last()
for yrs in (1,2,3):
    r=w.pct_change(52*yrs).dropna()
    print(f"finestre {yrs}a storiche 2018-26: P(<=0) {np.mean(r<=0):.2f} P(<+10%/anno) {np.mean((1+r)**(1/yrs)-1<0.10):.2f} min {r.min()*100:.0f}%")
# block bootstrap weekly returns, blocks of 26w, horizon 2/3y
wr=w.pct_change().dropna().to_numpy(); N=len(wr)
for H in (104,156):
    out=[]
    for _ in range(20000):
        idx=[]
        while len(idx)<H:
            s=rng.integers(0,N-26); idx+=list(range(s,s+26))
        out.append(np.prod(1+wr[idx[:H]])-1)
    out=np.array(out); print(f"block-boot {H//52}a: P(<=0) {np.mean(out<=0):.2f}, P(CAGR<10%) {np.mean((1+out)**(52/H)-1<0.1):.2f}, mediana CAGR {(np.median(1+out)**(52/H)-1)*100:.0f}%")
# Sharpe & DSR on weekly 2021+
w21=(eq21).resample("W-SUN").last().pct_change().dropna()
sr=w21.mean()/w21.std(); T=len(w21); g3=skew(w21); g4=kurtosis(w21,fisher=False)
print("SR ann 2021",sr*np.sqrt(52),"T",T,"skew",g3,"kurt",g4)
w18=eq18.resample("W-SUN").last().pct_change().dropna(); print("SR ann 18-20",w18.mean()/w18.std()*np.sqrt(52))
# variance of SR across trials: use 7 anchors from N1
g=pd.read_csv("/home/user/radar/research/notte_1511/n1/equity_giorni.csv",index_col=0,parse_dates=True)
srs=[]
for c in g.columns:
    x=g[c].resample("W-SUN").last().pct_change().dropna(); srs.append(x.mean()/x.std())
srs=np.array(srs); print("SR settimanali 7 giorni",np.round(srs*np.sqrt(52),2))
gam=0.5772
def dsr(sr,V,Nt):
    em=np.sqrt(V)*((1-gam)*norm.ppf(1-1/Nt)+gam*norm.ppf(1-1/(Nt*np.e)))
    z=(sr-em)*np.sqrt(T-1)/np.sqrt(1-g3*sr+(g4-1)/4*sr**2); return em*np.sqrt(52),norm.cdf(z)
for V in (srs.var(ddof=1), (0.5/np.sqrt(52))**2):
    for Nt in (31,100,300,1000):
        em,p=dsr(sr,V,Nt); print(f"V(SRann)={np.sqrt(V*52):.2f} N={Nt}: SR max atteso dal caso {em:.2f}, DSR {p:.3f}")
