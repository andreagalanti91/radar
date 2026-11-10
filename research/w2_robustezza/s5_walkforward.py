"""Punto 5: walk-forward a finestra espansa. 54 config; al 1 gennaio di ogni anno 2021..2026 scelgo il MAR piu' alto sulla finestra
2018-01-01 -> 31/12 dell'anno prima (flusso proxy fino al 2020-04) e uso quella config per l'anno. Equity cucita con i rendimenti
giornalieri della simulazione continua della config scelta (eredita la sua posizione aperta: approssimazione dichiarata)."""
from lib import *
import itertools
repo, long = load()
G = [dict(sma=s, ema_t=e_, ema_x=e_ + 1, trail=k, stop=k, f1=f) for s, e_, k, f in itertools.product((30, 40, 50), (15, 20, 26), (2.0, 2.5, 3.0), (True, False))]
lab = lambda g: f"SMA{g['sma']}/EMA{g['ema_t']}/tr{g['trail']}/{'F1' if g['f1'] else 'noF1'}"
EQ = {lab(g): run(long, start="2018-01-01", **g)["equity"] for g in G}
R = pd.DataFrame({k: v.pct_change().fillna(0) for k, v in EQ.items()})
FIX = "SMA40/EMA20/tr2.5/F1"
def mar(r):
    c = (1 + r).cumprod(); dd = (c / c.cummax() - 1).min(); return (c.iloc[-1] - 1) / abs(dd) if dd < 0 else 0
rows, parts = [], []
for y in range(2021, 2027):
    tr = R[R.index < f"{y}-01-01"]; m = tr.apply(mar); best = m.idxmax(); te = R[(R.index >= f"{y}-01-01") & (R.index <= f"{y}-12-31")]
    parts.append(te[best])
    rows.append(dict(anno=y, scelta=best, mar_train=round(m[best], 2), rango_fissa_train=int((m > m[FIX]).sum() + 1),
                     oos_scelta=round(((1 + te[best]).prod() - 1) * 100, 1), oos_fissa=round(((1 + te[FIX]).prod() - 1) * 100, 1),
                     oos_mediana_54=round(((1 + te).prod() - 1).median() * 100, 1), rango_fissa_oos=int(((1 + te).prod() > (1 + te[FIX]).prod()).sum() + 1)))
df = pd.DataFrame(rows); df.to_csv(HERE / "s5_walkforward.csv", index=False); print(df.to_string(index=False))
wf = (1 + pd.concat(parts)).cumprod(); fx = (1 + R[FIX][R.index >= "2021-01-01"]).cumprod()
allc = (1 + R[R.index >= "2021-01-01"]).cumprod()
print("WF cucita ", stats(wf)); print("fissa     ", stats(fx))
fin = allc.iloc[-1] * 1e4; dds = (allc / allc.cummax() - 1).min() * 100
print(f"54 config 2021-oggi: finale mediana {fin.median():.0f}, min {fin.min():.0f}, max {fin.max():.0f}; rango della fissa {(fin > fin[FIX]).sum()+1}/54; DD mediana {dds.median():.1f}")
print("solo F1:", fin[[k for k in fin.index if k.endswith('/F1')]].median().round(), "solo noF1:", fin[[k for k in fin.index if k.endswith('noF1')]].median().round())
print(f"log-rendimento WF / fissa = {np.log(wf.iloc[-1]) / np.log(fx.iloc[-1]):.2f}")
pd.DataFrame({"wf": wf, "fissa": fx}).to_csv(HERE / "s5_equity.csv")
