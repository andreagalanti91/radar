import sys, warnings, pickle
warnings.filterwarnings("ignore")
ROOT="/home/user/radar"; sys.path.insert(0,ROOT); sys.path.insert(0,ROOT+"/research/short_w2")
import numpy as np, pandas as pd
from radar.data import load_all
from radar.features import build_features
from radar import weekly as W
import short_lab
f=build_features(load_all()); f=f[f["close"].notna()]
fl=short_lab.load_long(f)
pickle.dump((f,fl),open("/tmp/claude-0/-home-user-radar/4f01d4b8-8442-5751-908f-fb8502af4b0c/scratchpad/disr/data.pkl","wb"))
def run(x,start,end=None,**kw):
    old={k:getattr(W,k) for k in kw}
    for k,v in kw.items(): setattr(W,k,v)
    xx=x if end is None else x[x.index<=end]
    r=W.simulate(xx,start=start); m=W.metrics(r)
    for k,v in old.items(): setattr(W,k,v)
    return r,m
for lab,x,s,e in [("2021",f,"2021-01-01",None),("1820",fl,"2018-01-01","2020-12-31")]:
    r,m=run(x,s,e)
    tt=r["trades"]+([dict(r["open"],pnl=r["open"]["pnl_close"])] if r["open"] else [])
    p=np.array([t["pnl"] for t in tt])
    print(lab,{k:m[k] for k in ("n","win_rate","total_pct","max_dd_pct","mar","worst_pct","years")})
    for t in tt: print("  ",t["entry"],t.get("exit"),t["side"],round(t["expo"],3),round(t["pnl"]*100,1))
    srt=np.sort(p)[::-1]; tot=np.prod(1+p)
    for k in (1,2,3): print(f"  senza top{k}: x{np.prod(1+srt[k:]):.2f} (tot x{tot:.2f})")
    print("  short:",[round(t['pnl']*100,1) for t in tt if t['side']=='short'])
