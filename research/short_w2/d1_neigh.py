"""D1 (esplorativa): parametri vicini, combinato con long W2, short 1x. MAR 2021-oggi | 2018-20 | rend 2021-oggi."""
import sys
sys.path.insert(0, '.')
from short_lab import *  # noqa
f = load_repo(); fl = load_long(f)
N = {"base": {}, "sma35": dict(sma=35), "sma45": dict(sma=45), "ema18": dict(ema_x=18), "ema24": dict(ema_x=24),
     "trail2": dict(trail=2.0, stop=2.0), "trail3": dict(trail=3.0, stop=3.0)}
for k, v in N.items():
    p = dict(P0, **v); out = []
    for ff, a, b in ((f, "2021-01-01", None), (fl, "2018-01-01", "2020-12-31")):
        w = weekly_bars(ff, p); s = (w["dn_w2"] & (w["close"] < w["ema21"])).fillna(False)
        out.append(metrics(simulate(ff, w, s, short_cfg("S1", p, "1x"), longs=True, start=a, end=b)))
    print(f"{k}: MAR {out[0]['mar']} | {out[1]['mar']} · rend21 {out[0]['ret']}% DD {out[0]['dd']}")
