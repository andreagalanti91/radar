"""trend_multi · U2: azioni Dow 2000 con perpetuo oggi + 6 materie prime (ADDENDUM.md, commit 4b8f2fc). Uscite: risultati_u2.txt, u2_*.csv."""
import numpy as np
import pandas as pd
import tm_lib as T
import tm_study as S

OUT = T.D.parent; MA = OUT.parent / "multi_asset" / "data"
STOCKS = "BA CAT C GE HD HPQ IBM INTC JNJ JPM KO MCD MO MRK MSFT PG RTX T WMT XOM".split()
COMM = {"ORO": "GLD", "ARGENTO": "SLV", "PETROLIO": "USO", "GAS": "UNG", "RAME": "CPER", "PLATINO": "PPLT"}
FUT = {"ORO": "GC_F", "ARGENTO": "SI_F", "PETROLIO": "BZ_F", "GAS": "NG_F", "RAME": "HG_F", "PLATINO": "PL_F"}
extra = {s: (MA / "MSFT.csv.gz" if s == "MSFT" else MA / "dow2000" / f"{s}.csv.gz") for s in STOCKS}
extra.update({f"{k}_etf": (T.D / f"{v}.csv.gz" if v in ("GLD", "SLV", "USO") else T.D / "u2" / f"{v}.csv.gz") for k, v in COMM.items()})
extra.update({f"{k}_fut": T.D / "u2" / f"{v}.csv.gz" for k, v in FUT.items()})
pxa, rf, shy, first = T.load(extra)
zero = rf * 0
px = pxa[STOCKS + [f"{k}_etf" for k in COMM]].rename(columns={f"{k}_etf": k for k in COMM})
pxf = pxa[STOCKS + [f"{k}_fut" for k in COMM]].rename(columns={f"{k}_fut": k for k in COMM})
CLS = {**{s: "azioni" for s in STOCKS}, **{k: "materie" for k in COMM}}
log = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); log.append(s)

P("Avvio dati U2:", {k: str(first[k].date()) for k in list(extra)})
FUND = 0.05
base = dict(kind=(21, 63, 252), side="LF", freq="M", L=1.0, cash_ret=zero, fund_long=FUND)
VAR = {"U2-V1 LF 1/3/12": {}, "U2-V2 LS 1/3/12": dict(side="LS"), "U2-V3 LF 3/6/12": dict(kind=(63, 126, 252)),
       "U2-V4 LF 12m": dict(kind=(252,)), "U2-V5 LF SMA10": dict(kind=("sma", 210)), "U2-V6 LF settimanale": dict(freq="W"),
       "U2-V8 LS 3/6/12": dict(side="LS", kind=(63, 126, 252))}
R = {k: T.run(px, rf, **{**base, **v}) for k, v in VAR.items()}
spy = pxa[["SPY"]]
B = {"Equipesato U2 (funding 5%)": T.run(px, rf, fixed=T.fixed_ew, cash_ret=zero, fund_long=FUND),
     "Equipesato U2 (senza funding)": T.run(px, rf, fixed=T.fixed_ew, cash_ret=zero),
     "S&P 500 (SPY, senza funding)": T.run(spy, rf, fixed=lambda d, c, ok: np.ones(1), cash_ret=zero),
     "Liquidità (T-bill)": T.run(spy, rf, fixed=T.fixed_cash)}
allr = {**R, **B}
for per, (a, b) in S.PERIODS.items():
    a2 = max(a, "2008-03-31") if per.startswith("sviluppo") else a
    df = pd.DataFrame([S.row(k, r["eq"], rf, a2, b) for k, r in allr.items()])
    P(f"\n== {per} ({a2} → {b}) =="); P(S.fmt(df)); df.to_csv(OUT / f"u2_{per.split()[0].lower().replace('–', '-')}_{a[:4]}.csv", index=False)
P("\n== Crisi =="); P(pd.DataFrame({k: S.crisis(r["eq"]) for k, r in allr.items()}).T.map(lambda x: f"{x * 100:+.1f}%").to_string())
P("\n== Operazioni nel giudizio =="); P(pd.DataFrame({k: S.ops(r, T.J0, T.J1) for k, r in R.items()}).T.round(2).to_string())

P("\n== Criteri (giudizio) e bootstrap; soglia p < 0,0125 ==")
jm = {k: T.metrics(r["eq"], rf, T.J0, T.J1) for k, r in allr.items()}
EW, SP = "Equipesato U2 (funding 5%)", "S&P 500 (SPY, senza funding)"
for k in ("U2-V1 LF 1/3/12", "U2-V2 LS 1/3/12"):
    m = jm[k]; e = R[k]["eq"]
    h1 = T.metrics(e, rf, "2016-01-01", "2020-12-31")["tot"]; h2 = T.metrics(e, rf, "2021-01-01", T.J1)["tot"]
    x = S.excess(e, rf); _, p = T.boot(x)
    dew, pew = T.boot(x, S.excess(B[EW]["eq"], rf)); dsp, psp = T.boot(x, S.excess(B[SP]["eq"], rf))
    c1 = m["cdd"] > jm[EW]["cdd"] and m["cdd"] > jm[SP]["cdd"]; c2 = m["dd"] >= -0.25
    c3 = h1 > 0 and h2 > 0 and m["cagr"] > jm["Liquidità (T-bill)"]["cagr"]; c4 = p < 0.0125
    P(f"{k}: C1 CAGR/DD {m['cdd']:.2f} vs EW {jm[EW]['cdd']:.2f}, S&P {jm[SP]['cdd']:.2f} → {c1} | C2 DD {m['dd'] * 100:.1f}% → {c2} | "
      f"C3 metà {h1 * 100:+.1f}% / {h2 * 100:+.1f}%, CAGR {m['cagr'] * 100:.2f}% vs T-bill {jm['Liquidità (T-bill)']['cagr'] * 100:.2f}% → {c3} | "
      f"C4 eccesso annuo {x.mean() * 252 * 100:+.2f}% p={p:.4f} → {c4}")
    P(f"   differenza di Sharpe: vs equipesato {dew * np.sqrt(252):+.2f} p={pew:.3f}; vs S&P {dsp * np.sqrt(252):+.2f} p={psp:.3f}")

P("\n== Sensibilità e robustezza (giudizio) ==")
rows = []
for side in ("LF", "LS"):
    b0 = {**base, "side": side}
    chk = {"base (funding 5%, liquidità 0)": {}, "funding 0%": dict(fund_long=0.0), "funding 10%": dict(fund_long=0.10),
           "funding 0% + T-bill sul collaterale": dict(fund_long=0.0, cash_ret=rf), "funding 5% + T-bill sul collaterale": dict(cash_ret=rf),
           "costi doppi": dict(cost=0.002, borrow=0.02), "settimanale": dict(freq="W"), "banda 1%": dict(band=0.01),
           "segnale 3/6/12": dict(kind=(63, 126, 252)), "segnale 12m": dict(kind=(252,)), "segnale SMA10": dict(kind=("sma", 210)),
           "vol 40": dict(vol_n=40), "vol 90": dict(vol_n=90), "senza materie prime": dict(drop=tuple(COMM)), "senza azioni": dict(drop=tuple(STOCKS)),
           "rischio uguale per classe": dict(cls=CLS), "future al posto degli ETF-serie": dict(_px=pxf)}
    for n, kw in chk.items():
        kw = dict(kw); p_ = kw.pop("_px", px)
        r = T.run(p_, rf, **{**b0, **kw}); m = T.metrics(r["eq"], rf, T.J0, T.J1); o = S.ops(r, T.J0, T.J1)
        fl = {**b0, **kw}.get("fund_long", 0)
        ew = T.metrics(T.run(p_.drop(columns=list(kw.get("drop", ()))), rf, fixed=T.fixed_ew, cash_ret=zero, fund_long=fl)["eq"], rf, T.J0, T.J1)
        rows.append(dict(lato=side, controllo=n, CAGR=round(m["cagr"] * 100, 2), vol=round(m["vol"] * 100, 1), DD=round(m["dd"] * 100, 1),
                         CAGR_DD=round(m["cdd"], 2), Sharpe=round(m["sharpe"], 2), EW_CAGR=round(ew["cagr"] * 100, 1), EW_DD=round(ew["dd"] * 100, 1),
                         EW_CAGR_DD=round(ew["cdd"], 2), batte_EW=m["cdd"] > ew["cdd"], batte_SP=m["cdd"] > jm[SP]["cdd"],
                         ordini_anno=round(o["ordini_1pct_anno"]), lordo=round(o["lordo_medio"], 2)))
rb = pd.DataFrame(rows); P(rb.to_string(index=False)); rb.to_csv(OUT / "u2_robustezza.csv", index=False)

P("\n== Anni solari ==")
ks = ("U2-V1 LF 1/3/12", "U2-V2 LS 1/3/12", EW, "Equipesato U2 (senza funding)", SP)
P((pd.DataFrame({k: allr[k]["eq"].groupby(allr[k]["eq"].index.year).last().pct_change() for k in ks}) * 100).round(1).to_string())

P("\n== Contributo per classe a U2-V1 (somma dei rendimenti giornalieri peso×rendimento, giudizio, % annuo) ==")
r = R["U2-V1 LF 1/3/12"]; ret = px.pct_change(fill_method=None).fillna(0)
contrib = (r["w"].shift(1) * ret.reindex(r["w"].index)).loc[T.J0:T.J1].sum() / ((pd.Timestamp(T.J1) - pd.Timestamp(T.J0)).days / 365.25) * 100
P("azioni:", round(contrib[STOCKS].sum(), 2), "| materie prime:", round(contrib[list(COMM)].sum(), 2)); P(contrib.round(2).to_string())

for k in ("U2-V1 LF 1/3/12", "U2-V2 LS 1/3/12"):
    r = R[k]
    P(f"\n== Posizioni di {k} oggi: target se si decidesse il {r['tgt'].index[-1].date()}, pesi al {r['w'].index[-1].date()} ==")
    cur = pd.DataFrame({"segnale": r["sig"].iloc[-1], "peso_target": r["tgt"].iloc[-1], "peso_oggi": r["w"].iloc[-1]})
    cur["usd_su_60k"] = (cur["peso_oggi"] * 60000).round(0)
    P(cur.round(3).to_string()); P("lordo oggi:", round(r["w"].iloc[-1].abs().sum(), 3))
    cur.to_csv(OUT / f"u2_posizioni_oggi_{k[3:5]}.csv")
pd.DataFrame({k: v["eq"] for k, v in allr.items()}).round(5).to_csv(OUT / "u2_equity.csv.gz")
(OUT / "risultati_u2.txt").write_text("\n".join(log))
