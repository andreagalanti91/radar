import sys, warnings, pickle
warnings.filterwarnings("ignore")
ROOT="/home/user/radar"; sys.path.insert(0,ROOT)
import numpy as np, pandas as pd
from radar import weekly as W
D="/tmp/claude-0/-home-user-radar/4f01d4b8-8442-5751-908f-fb8502af4b0c/scratchpad/disr/"
f,fl=pickle.load(open(D+"data.pkl","rb"))
def run(x,start,end=None,**kw):
    old={k:getattr(W,k) for k in kw}
    for k,v in kw.items(): setattr(W,k,v)
    xx=x if end is None else x[x.index<=end]
    r=W.simulate(xx,start=start); m=W.metrics(r)
    for k,v in old.items(): setattr(W,k,v)
    return r,m
print("== sizing (rischio allo stop iniziale)")
for rk in (0.02,0.03,0.05,0.10,0.15,0.25):
    a,ma=run(f,"2021-01-01",R_LONG=rk,R_SHORT=rk); b,mb=run(fl,"2018-01-01","2020-12-31",R_LONG=rk,R_SHORT=rk)
    ex=np.mean([t["expo"] for t in a["trades"]])
    print(f"r={rk:.2f} 2021: fin {10000*(1+ma['total_pct']/100):,.0f} DD {ma['max_dd_pct']} MAR {ma['mar']} cagr {((1+ma['total_pct']/100)**(1/5.87)-1)*100:.1f}% expo media {ex:.2f} | 18-20: fin {10000*(1+mb['total_pct']/100):,.0f} DD {mb['max_dd_pct']} peggiore {mb['worst_pct']}")
print("== slippage/fee stress")
for sl in (0.001,0.003,0.005,0.01):
    a,ma=run(f,"2021-01-01",SLIP=sl); b,mb=run(fl,"2018-01-01","2020-12-31",SLIP=sl)
    print(f"slip {sl}: 2021 fin {10000*(1+ma['total_pct']/100):,.0f} DD {ma['max_dd_pct']} | 18-20 fin {10000*(1+mb['total_pct']/100):,.0f}")
# funding x3
f3=f.copy(); f3["funding"]=f3["funding"]*3
a,ma=run(f3,"2021-01-01"); print("funding x3 (anche dist cambia):",10000*(1+ma['total_pct']/100),ma['max_dd_pct'])
# rischio effettivo allo stop di ogni trade = expo*2.5atr/close
r,m=run(f,"2021-01-01")
print("rischio iniziale per trade 2021+:",[round(t["expo"]*2.5*t["atr"]/t["sig_close"]*100,1) for t in r["trades"]+[r["open"]]])
r2,m2=run(fl,"2018-01-01","2020-12-31")
print("rischio iniziale 18-20:",[round(t["expo"]*2.5*t["atr"]/t["sig_close"]*100,1) for t in r2["trades"]+[r2["open"]]])
print("open:",{k:r["open"][k] for k in ("entry","entry_px","stop0","trail","expo","last")})
# equity series for bootstrap
eq21=r["equity"]; eq18=r2["equity"]
pickle.dump((eq18,eq21,[t["pnl"] for t in r["trades"]],[t["pnl"] for t in r2["trades"]]),open(D+"eq.pkl","wb"))
