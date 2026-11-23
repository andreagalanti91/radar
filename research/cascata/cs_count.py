"""Conteggio degli eventi PRIMA del PREREG: solo numero di giorni e grandezze del giorno, nessun rendimento successivo."""
import warnings; warnings.filterwarnings("ignore")
import pandas as pd
import cs_lib as L

OUT = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.append(s)

GRID = {"rA2 vr2": dict(rA=2, vr=2), "rA1.5 vr2": dict(rA=1.5, vr=2), "rA2 vr1.5": dict(rA=2, vr=1.5), "rA1.5 vr1.5": dict(rA=1.5, vr=1.5),
        "rP7 vr2": dict(rP=0.07, vr=2), "rP7 vr1.5": dict(rP=0.07, vr=1.5), "rP5 vr1.5": dict(rP=0.05, vr=1.5),
        "eA2 vr2 tail1/3": dict(eA=2, vr=2, tail=1/3), "eA2 vr1.5 tail1/3": dict(eA=2, vr=1.5, tail=1/3),
        "eA1.5 vr1.5 tail1/3": dict(eA=1.5, vr=1.5, tail=1/3), "eA1.5 vr1.5 tail1/2": dict(eA=1.5, vr=1.5, tail=0.5),
        "eA2 vr1.5": dict(eA=2, vr=1.5), "eA2.5 vr2": dict(eA=2.5, vr=2), "eA2 (limite)": dict(eA=2), "eA1.5 (limite)": dict(eA=1.5),
        "eA2.5 (limite)": dict(eA=2.5), "eA1.25 vr1.5 tail1/2": dict(eA=1.25, vr=1.5, tail=0.5), "eA1 vr1.5 tail1/2": dict(eA=1.0, vr=1.5, tail=0.5),
        "eA1.25 vr2 tail1/2": dict(eA=1.25, vr=2, tail=0.5), "eA1.5 vr2 tail1/3": dict(eA=1.5, vr=2, tail=1/3), "eA1.25 (limite)": dict(eA=1.25)}
SETS = {"BTC 2021+": (L.btc(), "2021-01-01", None), "BTC 2018-20": (L.btc_long(), "2018-01-01", "2020-12-31"),
        "ETH 2021+": (L.eth(), "2021-01-01", None)}
for nm, (f, s, e) in SETS.items():
    x = L.feats(f)
    pos, tl = L.w32_days(f, s, e)
    x = x.loc[s:e] if e else x.loc[s:]
    pos = pos.reindex(x.index)
    say(f"\n== {nm}: giorni {len(x)}, trade W3.2 {len(tl)}, giorni in posizione long {(pos.side>0).sum()} short {(pos.side<0).sum()}")
    say(f"{'definizione':24s} giù(tutti) su(tutti) | a favore nei trade: giorni  trade toccati  (IS/OOS giorni)")
    for k, d in GRID.items():
        dn, up = L.trig(x, d, "S"), L.trig(x, d, "L")
        fav = (dn & (pos.side < 0)) | (up & (pos.side > 0))
        nt = pos.sig[fav].nunique()
        say(f"{k:24s} {int(dn.sum()):9d} {int(up.sum()):9d} | {int(fav.sum()):6d} {nt:6d}   ({int(fav[:'2023-12-31'].sum())}/{int(fav['2024-01-01':].sum())})")

say("\n== Grandezze dei giorni 13–21/11/2026 (dati del tool; lato short) — nessun rendimento successivo")
fl = L.btc_live(); x = L.feats(fl)
say(pd.concat([fl[["open", "high", "low", "close"]], x[["atr1", "vr", "rA_S", "rP_S", "eA_S", "eP_S", "tail_S"]]], axis=1).loc["2026-11-13":].round(3).to_string())
(L.HERE / "conteggi.txt").write_text("\n".join(OUT) + "\n")
