"""Controllo di fedeltà: valori recenti e riepilogo settimanale dal 2024 (barra 12/11 parziale da data-api.binance.vision)."""
import sys; sys.path.insert(0,'/home/user/radar/research/zeiierman')
from ztp import *
df=load_daily()
df.loc[pd.Timestamp('2026-11-12')]=[74015.20,74217.49,71255.02,71561.98]  # barra parziale 12/11 (data-api.binance.vision)
z=ztp(df); z['close']=df.close
z['tzblue']=z.tz<=-70; z['tzred']=z.tz>=-30
print(z.loc['2026-11-08':,['close','pz','tz','cz','core','est']].round(1))
w=z.loc['2024-01-01':].resample('W').agg({'close':'last','pz':'mean','tz':'mean','cz':'mean','core':lambda s:round(s.mean(),1),'red':'sum','blue':'sum','tzred':'sum','tzblue':'sum','est':lambda s:s.abs().max()})
pd.set_option('display.max_rows',500); print(w.round(0).to_string())
print('est events', z[z.us|z.ls|z.ubk|z.lbk][['us','ls','ubk','lbk']].astype(int).to_string())
