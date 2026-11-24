"""trend_multi · studio ETF (PREREG.md, commit 3ca3620). Uscite: risultati_etf.txt, etf_*.csv."""
import sys
import numpy as np
import pandas as pd
import tm_lib as T
import tm_study as S

OUT = T.D.parent
px, rf, shy, first = T.load()
px = px[T.UNIVERSE]
zero = rf * 0
log = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); log.append(s)

P("Avvio dati:", {k: str(v.date()) for k, v in first.items()}, "| ultimo:", px.index[-1].date())
base = dict(kind=(21, 63, 252), side="LF", freq="M", L=1.0)
VAR = {"V1 LF 1/3/12 mens.": {}, "V2 LS 1/3/12 mens.": dict(side="LS"), "V3 LF 3/6/12": dict(kind=(63, 126, 252)),
       "V4 LF 12m": dict(kind=(252,)), "V5 LF SMA 10 mesi": dict(kind=("sma", 210)), "V6 LF settimanale": dict(freq="W"),
       "V7 LF leva 2x (descr.)": dict(L=2.0), "V8 LS 3/6/12": dict(side="LS", kind=(63, 126, 252))}
R = {k: T.run(px, rf, **{**base, **v}) for k, v in VAR.items()}
B = {"60/40 SPY/IEF": T.run(px, rf, fixed=T.fixed_6040), "Equipesato universo": T.run(px, rf, fixed=T.fixed_ew),
     "Liquidità (T-bill)": T.run(px, rf, fixed=T.fixed_cash)}
allr = {**R, **B}
for per, (a, b) in S.PERIODS.items():
    df = pd.DataFrame([S.row(k, r["eq"], rf, a, b) for k, r in allr.items()])
    P(f"\n== {per} ({a} → {b}) =="); P(S.fmt(df)); df.to_csv(OUT / f"etf_{per.split()[0].lower().replace('–', '-')}_{a[:4]}.csv", index=False)

P("\n== Crisi (rendimento nel periodo) ==")
P(pd.DataFrame({k: S.crisis(r["eq"]) for k, r in allr.items()}).T.map(lambda x: f"{x * 100:+.1f}%").to_string())
P("\n== Operazioni nel giudizio ==")
P(pd.DataFrame({k: S.ops(r, T.J0, T.J1) for k, r in R.items()}).T.round(2).to_string())

P("\n== Criteri (giudizio) e bootstrap ==")
jm = {k: T.metrics(r["eq"], rf, T.J0, T.J1) for k, r in allr.items()}
x60, xew = S.excess(B["60/40 SPY/IEF"]["eq"], rf), S.excess(B["Equipesato universo"]["eq"], rf)
verd = {}
for k in ("V1 LF 1/3/12 mens.", "V2 LS 1/3/12 mens."):
    m = jm[k]; e = R[k]["eq"]
    h1 = T.metrics(e, rf, "2016-01-01", "2020-12-31")["tot"]; h2 = T.metrics(e, rf, "2021-01-01", T.J1)["tot"]
    x = S.excess(e, rf)
    _, p = T.boot(x); d60, p60 = T.boot(x, x60); dew, pew = T.boot(x, xew)
    c1 = m["cdd"] > jm["60/40 SPY/IEF"]["cdd"] and m["cdd"] > jm["Equipesato universo"]["cdd"]
    c2 = m["dd"] >= -0.25; c3 = h1 > 0 and h2 > 0 and m["cagr"] > jm["Liquidità (T-bill)"]["cagr"]; c4 = p < 0.025
    verd[k] = (c1, c2, c3, c4)
    P(f"{k}: C1 CAGR/DD {m['cdd']:.2f} vs 60/40 {jm['60/40 SPY/IEF']['cdd']:.2f}, EW {jm['Equipesato universo']['cdd']:.2f} → {c1} | "
      f"C2 DD {m['dd'] * 100:.1f}% → {c2} | C3 metà {h1 * 100:+.1f}% / {h2 * 100:+.1f}%, CAGR {m['cagr'] * 100:.2f}% vs T-bill "
      f"{jm['Liquidità (T-bill)']['cagr'] * 100:.2f}% → {c3} | C4 eccesso annuo {x.mean() * 252 * 100:+.2f}% p={p:.4f} → {c4}")
    P(f"   differenza di Sharpe (giornaliero×√252): vs 60/40 {d60 * np.sqrt(252):+.2f} p={p60:.3f}; vs equipesato {dew * np.sqrt(252):+.2f} p={pew:.3f}")
for k in ("60/40 SPY/IEF", "Equipesato universo"):
    x = S.excess(B[k]["eq"], rf); P(f"   {k}: eccesso annuo {x.mean() * 252 * 100:+.2f}% p={T.boot(x)[1]:.4f}")

P("\n== Robustezza (giudizio; CAGR/DD del 60/40 =", round(jm["60/40 SPY/IEF"]["cdd"], 2), ") ==")
rows = []
for side in ("LF", "LS"):
    b0 = {**base, "side": side}
    chk = {"base": {}, "costi doppi": dict(cost=0.002, borrow=0.02), "liquidità 0": dict(cash_ret=zero), "liquidità SHY": dict(cash_ret=shy),
           "vol 40": dict(vol_n=40), "vol 90": dict(vol_n=90), "banda 1%": dict(band=0.01), "settimanale": dict(freq="W"),
           "segnale 3/6/12": dict(kind=(63, 126, 252)), "segnale 12m": dict(kind=(252,)), "segnale SMA10": dict(kind=("sma", 210))}
    chk.update({f"senza {c}": dict(drop=tuple(v)) for c, v in T.CLASSES.items()})
    for n, kw in chk.items():
        r = T.run(px, rf, **{**b0, **kw}); m = T.metrics(r["eq"], rf, T.J0, T.J1); o = S.ops(r, T.J0, T.J1)
        b60 = jm["60/40 SPY/IEF"]["cdd"]
        if n.startswith("senza") and ("azioni" in n or "obbligazioni" in n):
            pass
        rows.append(dict(lato=side, controllo=n, CAGR=round(m["cagr"] * 100, 2), vol=round(m["vol"] * 100, 1), DD=round(m["dd"] * 100, 1),
                         CAGR_DD=round(m["cdd"], 2), Sharpe=round(m["sharpe"], 2), batte_6040=m["cdd"] > b60,
                         ordini_anno=round(o["ordini_1pct_anno"]), rotazione=round(o["rotazione_anno"], 1)))
rb = pd.DataFrame(rows); P(rb.to_string(index=False)); rb.to_csv(OUT / "etf_robustezza.csv", index=False)

P("\n== Anni solari (V1, V2, 60/40, equipesato) ==")
yr = pd.DataFrame({k: allr[k]["eq"].groupby(allr[k]["eq"].index.year).last().pct_change() for k in
                   ("V1 LF 1/3/12 mens.", "V2 LS 1/3/12 mens.", "60/40 SPY/IEF", "Equipesato universo", "Liquidità (T-bill)")})
P((yr * 100).round(1).to_string())

P("\n== Posizioni di V1 oggi ==")
r = R["V1 LF 1/3/12 mens."]
last = r["tgt"].index[-1]
P("pesi target se si decidesse il", last.date(), "| pesi correnti al", r["w"].index[-1].date())
cur = pd.DataFrame({"segnale": r["sig"].iloc[-1], "peso_target": r["tgt"].iloc[-1], "peso_oggi": r["w"].iloc[-1]})
cur["usd_su_60k"] = (cur["peso_oggi"] * 60000).round(0)
P(cur.round(3).to_string()); P("lordo oggi:", round(r["w"].iloc[-1].abs().sum(), 3))
cur.to_csv(OUT / "etf_posizioni_oggi.csv")
pd.DataFrame({k: v["eq"] for k, v in allr.items()}).round(5).to_csv(OUT / "etf_equity.csv.gz")
(OUT / "risultati_etf.txt").write_text("\n".join(log))
