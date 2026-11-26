import pandas as pd, numpy as np, sys
sys.path.insert(0, '.')
from dorito_lib import daily, resample, lele, VARIANTS
# triangoli letti dallo screenshot (calibrazione asse: 1/1/2025 x=146, 1/1/2026 x=454, 0,8438 px/giorno; precisione ~±3 giorni)
SHOT = [("R","2024-12-18"),("B","2025-03-11"),("R","2025-05-22"),("R","2025-08-14"),("B","2025-11-20"),
        ("B","2026-02-07"),("B","2026-06-30"),("B","2026-11-15")]
d = daily(include_partial=True)
win0, win1 = pd.Timestamp("2024-09-01"), pd.Timestamp("2026-11-26")
rows=[]
for tf, phases in [(1,[0]),(3,[0,1,2]),(7,[4])]:
  for ph in phases:
    b = resample(d, tf, ph)
    for vn, kw in VARIANTS.items():
      s = lele(b, **kw)
      ev = s[(s!=0)&(s.index>=win0)]
      evl = [("R" if v<0 else "B", t) for t,v in ev.items()]
      # coincidenza: ogni triangolo dello screenshot ha un segnale dello stesso lato con centro barra entro tol giorni
      tol = max(4, tf)  # 3D: mezza barra + errore di lettura
      hit=0; used=set()
      for side, ds in SHOT:
        t0=pd.Timestamp(ds)
        cands=[(abs((t+pd.Timedelta(days=(tf-1)/2)-t0).days),i) for i,(sd,t) in enumerate(evl) if sd==side and i not in used]
        cands=[c for c in cands if c[0]<=tol]
        if cands: hit+=1; used.add(min(cands)[1])
      extra=len(evl)-len(used)
      rows.append((tf,ph,vn,len(evl),hit,extra))
      print(f"TF {tf}D fase {ph} {vn}: segnali {len(evl)}, coincidenti {hit}/8, in piu {extra}")
      print("   ", " ".join(f"{sd}{t.date()}" for sd,t in evl))
from dorito_lib import resample_year
print("== 3D ricominciato ogni 1 gennaio")
b = resample_year(d, 3)
for vn, kw in VARIANTS.items():
  s = lele(b, **kw); ev=s[(s!=0)&(s.index>=win0)]
  print(vn, " ".join(f"{'R' if v<0 else 'B'}{t.date()}" for t,v in ev.items()))
