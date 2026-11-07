"""Controlli dopo T2 a 1 giorno (non preregistrati, dichiarati come tali): placebo sul segno, soglie vicine,
e confronto con un riferimento banale (inversione del movimento delle ultime 24 ore)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import magnet as M  # noqa: E402

h = M.hourly(); Z = M.maps(h)
hi, lo, t, cl = h["high"].to_numpy(), h["low"].to_numpy(), h.index, h["close"].to_numpy()
out = []
def run(n, thr, rule, label):
    rows = []
    rng = np.random.default_rng(3)
    for d, r in Z.iterrows():
        if not (r["up"] and r["dn"]):
            continue
        i = t.searchsorted(d)
        A, B = r["up"][0]["price"], r["dn"][0]["price"]
        sh, sl = hi[i:i + n] >= A, lo[i:i + n] <= B
        ha, hb = (np.argmax(sh) if sh.any() else 10**9), (np.argmax(sl) if sl.any() else 10**9)
        if ha == hb:
            continue
        ret24 = cl[i - 1] / cl[i - 25] - 1 if i >= 25 else 0
        if rule == "imb":
            if abs(r["imb"]) < thr: continue
            side_up = r["imb"] > 0
        elif rule == "placebo":
            if abs(r["imb"]) < thr: continue
            side_up = rng.random() < 0.5
        elif rule == "rev24":
            side_up = ret24 < 0
        elif rule == "imb_vs_mom":   # solo giorni in cui squilibrio e momentum delle 24h indicano lati OPPOSTI
            if abs(r["imb"]) < thr or (r["imb"] > 0) == (ret24 > 0): continue
            side_up = r["imb"] > 0
        da, db = A / r["price"] - 1, 1 - B / r["price"]
        e = db / (da + db)
        rows.append((float((ha < hb) == side_up), e if side_up else 1 - e))
    R = np.array(rows)
    eff = (R[:, 0].mean() - R[:, 1].mean()) * 100
    p = binomtest(int(R[:, 0].sum()), len(R), R[:, 1].mean()).pvalue
    s = f"{label}: n {len(R)}, effetto {eff:+.1f} pt (p {p:.3f})"
    print(s); out.append(s)
for thr in (10, 20, 30, 40):
    run(24, thr, "imb", f"squilibrio ≥ {thr}% · 1g")
run(24, 20, "placebo", "placebo (lato a caso) · 1g")
run(24, 0, "rev24", "riferimento banale: inversione delle ultime 24h · 1g (negativo = il momentum vince)")
run(24, 20, "imb_vs_mom", "squilibrio ≥ 20% quando è OPPOSTO al momentum delle 24h · 1g")
run(72, 20, "imb_vs_mom", "squilibrio ≥ 20% quando è OPPOSTO al momentum delle 24h · 3g")
run(12, 20, "imb", "squilibrio ≥ 20% · 12h")
corr = np.corrcoef([r["imb"] for _, r in Z.iterrows()], [h["close"].asof(d - pd.Timedelta(hours=1)) / h["close"].asof(d - pd.Timedelta(hours=25)) - 1 for d in Z.index])[0, 1]
s = f"correlazione squilibrio ↔ rendimento delle 24h precedenti: {corr:+.2f}"; print(s); out.append(s)
Path(__file__).with_name("risultati_t2.txt").write_text("\n".join(out) + "\n")
