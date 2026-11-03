"""Pure Momentum Oscillator (MisinkoMaster) e Zeiierman Trend Pressure, tradotti dal Pine v6 fornito dall'utente."""
import sys; sys.path.insert(0,'/tmp/radar-work/ta-macd/scripts')
import numpy as np, pandas as pd
from common import PX, weekly

def ema(s,n):   # ta.ema: alpha 2/(n+1), seme SMA
    s=pd.Series(s,dtype=float); out=np.full(len(s),np.nan); a=2/(n+1); v=s.values; prev=np.nan; buf=[]
    for i,x in enumerate(v):
        if np.isnan(x): out[i]=prev; continue
        if np.isnan(prev):
            buf.append(x)
            if len(buf)==n: prev=np.mean(buf); out[i]=prev
        else: prev=a*x+(1-a)*prev; out[i]=prev
    return pd.Series(out,s.index)
def wma(s,n):
    w=np.arange(1,n+1); return s.rolling(n).apply(lambda x:(x*w).sum()/w.sum(),raw=True)
def rma(s,n):
    out=np.full(len(s),np.nan); v=s.values; prev=np.nan; buf=[]
    for i,x in enumerate(v):
        if np.isnan(x): continue
        if np.isnan(prev):
            buf.append(x)
            if len(buf)==n: prev=np.mean(buf); out[i]=prev
        else: prev=(prev*(n-1)+x)/n; out[i]=prev
    return pd.Series(out,s.index)
def atr(df,n):
    tr=pd.concat([df.high-df.low,(df.high-df.close.shift()).abs(),(df.low-df.close.shift()).abs()],axis=1).max(axis=1)
    tr.iloc[0]=df.high.iloc[0]-df.low.iloc[0]; return rma(tr,n)

def pmo(df,ln=45,l=0.05,s=-0.05):
    cd=wma(df.close*2-ema(df.close,ln),ln); ch=(cd-cd.shift())/atr(df,ln)
    tr=[];t=0
    for x in ch.values:
        if x>l: t=1
        if x<s: t=-1
        tr.append(t)
    return pd.DataFrame({'change':ch,'trend':tr},df.index)

def zeii(df,fl=21,pl=9,ps=7,sl=55,ml=120,ts=5,db=9.0,zn=20,sn=7,rm=16,gw=0.65):
    clp=lambda v,lo,hi: np.minimum(hi,np.maximum(lo,v))
    mt=0.01
    def wr(k):
        hh=df.high.rolling(k).max(); ll=df.low.rolling(k).min(); return 100*(df.close-hh)/np.maximum(hh-ll,mt)
    def sm(v,k): return ema(v,k) if k>1 else v
    def stk(x,k):
        hi=x.rolling(k).max(); lo=x.rolling(k).min(); return -100+100*(x-lo)/np.maximum(hi-lo,1e-10)
    rF,rS,rM=wr(fl),wr(sl),wr(ml)
    pr=clp(rF*0.72+stk(rF,pl)*0.28,-100,0); pz=sm(pr,ps)
    sw,mw,th=0.18,0.72,0.92; fw=max(0,1-sw-mw)
    cn=clp((rF*fw+rS*sw+rM*mw)/(fw+sw+mw),-100,0)
    dsum=(rF-rS).abs()+(rS-rM).abs()+(rF-rM).abs(); ag=1-clp(dsum/300,0,1)
    p=(df.close-df.close.shift()).abs().rolling(sl).mean()*sl; nmv=(df.close-df.close.shift(sl)).abs()
    ef=clp(nmv/np.maximum(p,mt),0,1).fillna(0)
    ud=np.zeros(len(df)); dd=np.zeros(len(df)); cnv=cn.values
    for i in range(len(df)):
        pu=ud[i-1] if i else 0; pd_=dd[i-1] if i else 0
        c=cnv[i]
        ud[i]=min(1,pu*0.93+0.07) if (not np.isnan(c) and c>-30) else pu*0.94
        dd[i]=min(1,pd_*0.93+0.07) if (not np.isnan(c) and c<-70) else pd_*0.94
    tg0=clp(cn+db*(ud-dd),-100,0); tg=sm(tg0,2)
    ba=2/(ts+1); tz=np.full(len(df),np.nan); tgv,mv,agv,efv=tg.values,rM.values,ag.values,ef.values
    for i in range(len(df)):
        prev=tz[i-1] if i else np.nan
        if np.isnan(tgv[i]): tz[i]=prev; continue
        if np.isnan(prev): tz[i]=tgv[i]; continue
        side=1 if mv[i]>-50 else -1 if mv[i]<-50 else 0
        pull=(side==1 and tgv[i]<prev) or (side==-1 and tgv[i]>prev)
        lk=clp(0.15+agv[i]*efv[i]*th,0,0.97)
        a=max(0.015,ba*(1-lk)) if pull else max(ba*0.75,0.03)
        tz[i]=clp(prev+a*(tgv[i]-prev),-100,0)
    tz=pd.Series(tz,df.index)
    def prs(k):
        hh=df.high.rolling(k).max(); ll=df.low.rolling(k).min(); rg=np.maximum(hh-ll,mt); cr=np.maximum(df.high-df.low,mt)
        bh=np.maximum(df.open,df.close); bl=np.minimum(df.open,df.close); uw=df.high-bh; lw=bl-df.low
        cl=(df.close-ll)/rg; mn=((df.high+df.low+df.close)/3-ll)/rg; bd=((df.close-df.open)/cr+1)*0.5; wk=((lw-uw)/cr+1)*0.5
        p5=df.close.shift(5).fillna(df.close); im=((df.close-p5)/rg+1)*0.5
        return clp((cl*0.42+mn*0.23+bd*0.13+wk*0.12+im*0.10)*100,0,100)
    cp=ema(prs(21),rm); cg=ema(prs(112),3); c0=cg*gw+cp*(1-gw)
    core=np.where((c0>50)&(cg>50),1,np.where((c0<50)&(cg<50),-1,0))
    d=sn-5; ez=clp(zn-d*4,8,42); rb=clp(8+d*1.75,1,18); cf=1 if sn<=5 else 2 if sn<=7 else 3 if sn<=9 else 4; fast=sn<=2
    up=-ez; dn=-100+ez; ur=up-rb; lr=dn+rb
    est=np.zeros(len(df),int); ucn=lcn=0; e=0; pzv,tzv=pz.values,tz.values
    for i in range(len(df)):
        uc=pzv[i]>=up and tzv[i]>=up; lc=pzv[i]<=dn and tzv[i]<=dn
        ucn=ucn+1 if uc else 0; lcn=lcn+1 if lc else 0
        ux=(pzv[i]<ur or tzv[i]<ur) if fast else (pzv[i]<ur and tzv[i]<ur)
        lx=(pzv[i]>lr or tzv[i]>lr) if fast else (pzv[i]>lr and tzv[i]>lr)
        if e==0:
            if ucn>=cf: e=1
            elif lcn>=cf: e=-1
        elif e==1 and ux: e=0
        elif e==-1 and lx: e=0
        est[i]=e
    est=pd.Series(est,df.index); pe=est.shift().fillna(0)
    return pd.DataFrame({'pz':pz,'tz':tz,'cz':c0-100,'c0':c0,'cg':cg,'core':core,'est':est,
        'ubk':(est==0)&(pe==1),'lbk':(est==0)&(pe==-1),'xup':(pz>tz)&(pz.shift()<=tz.shift()),'xdn':(pz<tz)&(pz.shift()>=tz.shift())},df.index)
