"""trend_multi · funzioni comuni di analisi: tabella delle metriche, criteri, operazioni, crisi."""
import numpy as np
import pandas as pd
import tm_lib as T

PERIODS = {"sviluppo 2007–15": ("2007-01-31", "2015-12-31"), "GIUDIZIO 2016–26": (T.J0, T.J1),
           "2016–20": ("2016-01-01", "2020-12-31"), "2021–26": ("2021-01-01", T.J1)}
CRISES = {"2018 Q4": ("2018-09-28", "2018-12-31"), "19/02–23/03/2020": ("2020-02-19", "2020-03-23"),
          "marzo 2020": ("2020-02-28", "2020-03-31"), "2022": ("2021-12-31", "2022-12-30")}


def pct(x, d=1):
    return "n/d" if x is None or not np.isfinite(x) else f"{x * 100:+.{d}f}%"


def row(name, e, rf, a, b):
    m = T.metrics(e, rf, a, b)
    return dict(nome=name, CAGR=m["cagr"], vol=m["vol"], DD=m["dd"], CAGR_DD=m["cdd"], Sharpe=m["sharpe"],
                peggior_anno=m["worst"], anno=m["worst_y"], finale_10k=10000 * (1 + m["tot"]))


def fmt(df):
    d = df.copy()
    for c in ("CAGR", "vol", "DD", "peggior_anno"):
        d[c] = d[c].map(lambda x: f"{x * 100:.1f}")
    d["CAGR_DD"] = d["CAGR_DD"].map(lambda x: f"{x:.2f}"); d["Sharpe"] = d["Sharpe"].map(lambda x: f"{x:.2f}")
    d["finale_10k"] = d["finale_10k"].map(lambda x: f"{x:,.0f}".replace(",", "."))
    return d.to_string(index=False)


def ops(res, a, b):
    """Operazioni viste dall'utente nel periodo: cambi di stato (entra/esce/inverte), ordini ≥ 1% del capitale, rotazione."""
    yrs = (pd.Timestamp(b) - pd.Timestamp(a)).days / 365.25
    out = {}
    if len(res["sig"]):
        st = np.sign(res["sig"].loc[a:b]); out["cambi_stato_anno"] = float((st.diff().abs() > 0).sum().sum() / yrs)
        out["cambi_livello_anno"] = float((res["sig"].loc[a:b].diff().abs() > 1e-9).sum().sum() / yrs)
    out["ordini_1pct_anno"] = float(res["nord"].loc[a:b].sum() / yrs)
    out["rotazione_anno"] = float(res["to"].loc[a:b].sum() / yrs)
    g = res["gross"].loc[a:b]
    out["lordo_medio"] = float(g.mean()); out["giorni_investiti"] = float((g > 0.05).mean())
    out["posizioni_medie"] = float((res["w"].loc[a:b].abs() > 0.005).sum(axis=1).mean())
    return out


def crisis(e):
    return {k: float(e.loc[:b].iloc[-1] / e.loc[:a].iloc[-1] - 1) for k, (a, b) in CRISES.items()}


def excess(e, rf, a=T.J0, b=T.J1):
    r = e.loc[a:b].pct_change().dropna()
    return (r - rf.reindex(r.index)).to_numpy()
