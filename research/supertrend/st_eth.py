"""supertrend · conferma esterna su ETH (PREREG §6): S1–S3 su 1D e 1W, S4a; K1–K3 su W3.2 ETH. Stessi parametri, niente 4h."""
from __future__ import annotations
import importlib.util, sys, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import st_lib as L, st_engine as E, st_run as R, st_w32 as K

CEND = "2026-11-10"          # fine dei dati W3.2 ETH (research/w32_multi)

if __name__ == "__main__":
    d = pd.read_csv(L.ROOT / "research" / "w32_multi" / "data" / "ETH_spot_long.csv.gz", index_col=0, parse_dates=True)
    d = d[d.index <= L.CUT][["open", "high", "low", "close"]]
    fu = pd.read_csv(L.ROOT / "data" / "eth_funding.csv", index_col=0, parse_dates=True)["funding"]
    B = E.base_daily(d, fu); T = E.targets(E.directions(B))
    names = [s for s in E.STRATS if s in T] + ["S4a_long", "S4a_short"]
    bhs = {p: E.bh(B, a, b) for p, (a, b) in E.PER_ALL.items()}
    t = pd.concat([R.table(B, T, names=names), R.table(B, T, cap=True, names=names)])
    t.to_csv(L.HERE / "eth_risultati.csv", index=False)
    j = R.judge(t[~t["cap"] & t["strat"].isin(E.STRATS)], bhs)
    # W3.2 ETH e K1–K3
    spec = importlib.util.spec_from_file_location("t10", L.ROOT / "research" / "top10_w3" / "run.py"); T10 = importlib.util.module_from_spec(spec); spec.loader.exec_module(T10)
    f, st = T10.feats("ETH"); f = f[f.index <= CEND]
    X = K.st_inputs(d)
    rows = []
    for v in (None, "K1", "K2", "K3"):
        for p, (a, b) in {"2021-23": ("2021-01-01", "2023-12-31"), "2024-26": ("2024-01-01", CEND), "2021-26": ("2021-01-01", CEND)}.items():
            rows.append(dict(var=v or "W3.2 ETH", periodo=p, **K.simulate(f, a, b, v, X)))
    KE = pd.DataFrame(rows); KE.to_csv(L.HERE / "eth_w32_k.csv", index=False)
    pd.set_option("display.width", 250)
    with open(L.HERE / "eth.txt", "w") as fh:
        def P(*a):
            print(*a); print(*a, file=fh)
        P("ETH BUY & HOLD"); P(pd.DataFrame(bhs).T.round(3).to_string())
        for cap in (False, True):
            P("\nETH 10/3" + (" tetto" if cap else " 1x"))
            x = t[t["cap"] == cap]
            for col, fr in (("fin", 0), ("dd", 3), ("S", 2), ("n", 0), ("wr", 2)):
                P(col); P(x.pivot(index="strat", columns="periodo", values=col).loc[names].round(fr).to_string())
        P("\nCRITERI ETH (1x)"); P(j[["strat", "periodi_ok", "tutti"]].to_string())
        P("\nW3.2 ETH E K"); P(KE.round(3).to_string())
