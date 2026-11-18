import pickle, numpy as np, pandas as pd
D="/tmp/claude-0/-home-user-radar/4f01d4b8-8442-5751-908f-fb8502af4b0c/scratchpad/disr/"
f,fl=pickle.load(open(D+"data.pkl","rb")); eq18,eq21,_,_=pickle.load(open(D+"eq.pkl","rb"))
c=f["close"]
for s in ("2023-07-01","2024-01-01","2024-03-11","2025-01-01","2024-11-18"):
    e=eq21[eq21.index>=s]; b=c[c.index>=s]
    print(s,"W3 x%.2f DD %.1f%% | B&H x%.2f DD %.1f%%"%(e.iloc[-1]/e.iloc[0],(e/e.cummax()-1).min()*100,b.iloc[-1]/b.iloc[0],(b/b.cummax()-1).min()*100))
pk=eq21.cummax(); print("ultimo massimo equity",eq21.idxmax().date(), "giorni sotto massimo oggi",(eq21.index[-1]-eq21.idxmax()).days)
# longest flat stretch: max days between new highs
nh=eq21[eq21>=pk-1e-9].index; gaps=np.diff(nh).astype('timedelta64[D]').astype(int); print("max giorni senza nuovo massimo 2021+",gaps.max(), nh[np.argmax(gaps)].date())
pk8=eq18.cummax(); nh8=eq18[eq18>=pk8-1e-9].index; g8=np.diff(nh8).astype('timedelta64[D]').astype(int); print("18-20 max giorni senza nuovo massimo",g8.max(), nh8[np.argmax(g8)].date())
# 2019-06 -> 2020-10 flat? 2022 H2
for a,b_ in (("2019-07-01","2020-09-30"),("2022-04-01","2022-12-31"),("2024-03-12","2024-09-22"),("2025-02-27","2026-11-17")):
    e=pd.concat([eq18,eq21]); e=e[~e.index.duplicated()]; x=e[(e.index>=a)&(e.index<=b_)]
    bb=fl["close"] if a<"2021" else c; y=bb[(bb.index>=a)&(bb.index<=b_)]
    print(a,b_,"W3 %+.1f%%  B&H %+.1f%%"%((x.iloc[-1]/x.iloc[0]-1)*100,(y.iloc[-1]/y.iloc[0]-1)*100))
