"""ema_sma · GIUDIZIO 2024–26 e CONFERMA 2018–20 (una sola volta), dopo scelta.json. Scrive risultati.csv, giudizio.txt, *.csv."""
import json, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd
import es_lib as L, es_engine as EN, es_w32 as W32

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
G = L.grammar(); N = len(G); R = EN.rule_arrays(G)
SC = json.load(open(L.HERE / "scelta.json"))
R1, R2, U = 1785, 1962, SC["utente"]          # R1 = scelta del codice; R2 = gemella della famiglia a pari punteggio (deviazione D1)
assert SC["regola"] == R1
DISC = pd.read_csv(L.HERE / "scoperta.csv", index_col=0)
USER = G[(G.reg == "G1") & (G.ent == "E0") & (G.xtype == "C") & (G.xtf == "4h") & (G.xn == 2) & G.side.isin(["INV", "LS", "LO"])].index.tolist()
SUB = sorted(set([R1, R2, U] + USER))
P = L.PERIODS; JA, JB = P["giudizio 2024-26"]
name = lambda r: "{side} {reg} {ent} {xtf} {xkind}{xpar} N{xn}".format(**G.loc[r])  # noqa: E731


def sub_rules(ix):
    return {k: v[ix] for k, v in R.items()}


def perm_job(seed):
    a, Rs, st, isplit, base = perm_job.ctx
    ap = EN.permute(a, JA, JB, np.random.default_rng(seed)); S = EN.signals(ap)
    E, d, T, _ = EN.run(S, Rs, isplit, len(ap), st)
    m = EN.metrics(np.vstack([base, E]), pd.DatetimeIndex([pd.Timestamp(JA) - pd.Timedelta(days=1)]).append(d), T, ap.index, JA, JB, len(SUB))
    return m["S"].to_numpy()


if __name__ == "__main__":
    t0 = time.time(); out = open(L.HERE / "giudizio.txt", "w")
    def pr(*x):
        s = " ".join(str(v) for v in x); print(s); out.write(s + "\n")
    a = L.load_4h(); S = EN.signals(a); i0 = a.index.searchsorted(pd.Timestamp(EN.START))
    E, days, T, _ = EN.run(S, R, i0, len(a))
    M = {p: EN.metrics(E, days, T, a.index, x, y, N) for p, (x, y) in P.items()}
    BH = {p: EN.bh(S, x, y) for p, (x, y) in P.items()}
    full = EN.metrics(E, days, T, a.index, "2021-01-01", L.CUT, N); BHf = EN.bh(S, "2021-01-01", L.CUT)
    res = G.copy()
    for p, m in list(M.items()) + [("intero 2021-26", full)]:
        k = p.split()[0][:4]
        for c in ("fin", "cagr", "dd", "S", "n", "wr", "fin_no2"): res[f"{k}_{c}"] = m[c].to_numpy()
    res["valid_sc"] = DISC["valid"].to_numpy(); res["sp_sc"] = DISC["sp"].to_numpy()
    res.to_csv(L.HERE / "risultati.csv", index_label="rule")
    assert np.allclose(res["scop_fin"], DISC["fin"], rtol=1e-4), "la scoperta ricalcolata non coincide"
    pr("B&H", {p: {k: round(float(v), 3) for k, v in b.items()} for p, b in BH.items()}, "intero", {k: round(float(v), 3) for k, v in BHf.items()})

    # --- regole giudicate
    def row(r, m, cap=None):
        x = (cap if cap is not None else m).loc[r]
        return dict(fin=round(x.fin), cagr=round(x.cagr * 100, 1), dd=round(x.dd * 100, 1), S=round(x.S, 2), n=int(x.n), wr=round(x.wr * 100) if x.n else None, fin_no2=round(x.fin_no2))
    w32 = W32.table({})
    rows = []
    for lab, r in (("R1 scelta", R1), ("R2 gemella", R2), ("U esempio utente", U)):
        for p, m in list(M.items()) + [("intero 2021-26", full)]:
            rows.append(dict(regola=lab, descr=name(r), periodo=p, **row(r, m)))
    for p, b in list(BH.items()) + [("intero 2021-26", BHf)]:
        rows.append(dict(regola="buy & hold", descr="", periodo=p, fin=round(b["fin"]), cagr=round(b["cagr"] * 100, 1), dd=round(b["dd"] * 100, 1), S=round(b["S"], 2), n=1))
    for _, x in w32.iterrows():
        rows.append(dict(regola="W3.2", descr="radar/weekly.py", periodo=x.periodo, fin=round(x.fin), cagr=round(x.cagr * 100, 1), dd=round(x.dd * 100, 1), S=round(x.S, 2), n=int(x.n), wr=round(x.wr * 100)))
    tab = pd.DataFrame(rows); tab.to_csv(L.HERE / "giudicate.csv", index=False); pr(tab.to_string())

    # --- versione con tetto di rischio 25% (solo regole giudicate ed esempi)
    Rs = sub_rules(np.array(SUB))
    Ec, dc, Tc, _ = EN.run(S, Rs, i0, len(a), cap=True)
    rows = []
    for lab, r in (("R1", R1), ("R2", R2), ("U", U)):
        j = SUB.index(r)
        for p, (x, y) in list(P.items()) + [("intero 2021-26", ("2021-01-01", L.CUT))]:
            m = EN.metrics(Ec, dc, Tc, a.index, x, y, len(SUB)); rows.append(dict(regola=lab + " tetto 25%", periodo=p, **row(j, m)))
    capt = pd.DataFrame(rows); capt.to_csv(L.HERE / "tetto25.csv", index=False); pr(capt.to_string())

    # --- esempio dell'utente: 24 regole
    ut = res.loc[USER, ["side", "xkind", "xpar", "conf_fin", "conf_dd", "conf_S", "scop_fin", "scop_dd", "scop_S", "scop_n", "giud_fin", "giud_dd", "giud_S", "giud_n", "giud_wr", "inte_fin", "inte_dd", "inte_n", "inte_wr"]]
    ut.to_csv(L.HERE / "esempio_utente.csv"); pr(ut.round(3).to_string())
    pr("mediana per lato:\n", ut.groupby("side")[["conf_fin", "scop_fin", "giud_fin", "inte_fin", "inte_dd", "conf_S", "scop_S", "giud_S"]].median().round(3).to_string())

    # --- permutazioni del giudizio (500) per le regole giudicate
    isplit = a.index.searchsorted(pd.Timestamp(JA))
    E1, d1, T1, st = EN.run(S, Rs, i0, isplit)
    perm_job.ctx = (a, Rs, st, isplit, E1[-1][None, :])
    with Pool(4) as pool:
        ps = np.vstack(pool.map(perm_job, range(5000, 5500), chunksize=10))
    realS = res.loc[SUB, "giud_S"].to_numpy()
    pv = pd.DataFrame(dict(rule=SUB, descr=[name(r) for r in SUB], S=realS, p=(ps >= realS).mean(0), perm_med=np.median(ps, 0), perm_p95=np.quantile(ps, 0.95, 0)))
    pv.to_csv(L.HERE / "p_giudizio.csv", index=False); pr(pv.round(3).to_string())

    # --- criteri
    for lab, r in (("R1", R1), ("R2", R2), ("U", U)):
        c = {}
        for p in ("giudizio 2024-26", "conferma 2018-20"):
            m = M[p].loc[r]
            c[p] = dict(cagr_pos=bool(m.cagr > 0), batte_bh=bool(m.S > BH[p]["S"]), dd_ok=bool(m.dd >= -0.35), senza2=bool(m.fin_no2 > 10000))
        c["p_giudizio"] = float(pv.loc[pv.rule == r, "p"].iloc[0])
        c["VALIDA"] = all(all(v.values()) for k, v in c.items() if isinstance(v, dict)) and c["p_giudizio"] <= 0.025
        pr("CRITERI", lab, name(r), json.dumps(c))

    # --- le regole buone restano buone?
    from numpy import argsort
    rk = lambda x: pd.Series(x).rank().to_numpy()  # noqa: E731
    sp = lambda x, y: float(np.corrcoef(rk(x), rk(y))[0, 1])  # noqa: E731
    v = res["valid_sc"].to_numpy()
    pr("Spearman S scoperta-giudizio: tutte %.3f | valide in scoperta %.3f | scoperta-conferma %.3f | giudizio-conferma %.3f" % (
        sp(res.scop_S, res.giud_S), sp(res.scop_S[v], res.giud_S[v]), sp(res.scop_S, res.conf_S), sp(res.giud_S, res.conf_S)))
    for k, p in (("scop", "scoperta 2021-23"), ("giud", "giudizio 2024-26"), ("conf", "conferma 2018-20")):
        ok = (res[f"{k}_cagr"] > 0) & (res[f"{k}_S"] > BH[p]["S"]) & (res[f"{k}_dd"] >= -0.35)
        pr(p, "CAGR>0 %.3f | S>B&H %.3f | CAGR>0, S>B&H e DD>=-35%% %.3f | mediana S %.3f | mediana fin %.0f | B&H S %.3f" % (
            (res[f"{k}_cagr"] > 0).mean(), (res[f"{k}_S"] > BH[p]["S"]).mean(), ok.mean(), res[f"{k}_S"].median(), res[f"{k}_fin"].median(), BH[p]["S"]))
        res[f"{k}_ok"] = ok
    pr("regole OK (CAGR>0, S>B&H, DD>=-35%%) in tutti e tre i periodi: %d su %d; in giudizio e conferma: %d" % (
        (res.scop_ok & res.giud_ok & res.conf_ok).sum(), N, (res.giud_ok & res.conf_ok).sum()))
    allok = res[res.scop_ok & res.giud_ok & res.conf_ok]
    pr("  di cui per lato", allok.groupby("side").size().to_dict(), "per classe", allok.groupby("xclass").size().to_dict(), "per regime", allok.groupby("reg").size().to_dict())
    allok.to_csv(L.HERE / "ok_tre_periodi.csv")
    top = res[res.valid_sc].sort_values("scop_S", ascending=False).head(20)
    pr("prime 20 della scoperta in giudizio e conferma:\n", top[["side", "reg", "ent", "xtf", "xtype", "xkind", "xpar", "xn", "scop_fin", "scop_S", "giud_fin", "giud_dd", "giud_S", "conf_fin", "conf_dd", "conf_S"]].round(2).to_string())
    pr("  mediane prime 20: giud_fin %.0f giud_S %.2f conf_fin %.0f conf_S %.2f; quota OK in giudizio %.2f" % (top.giud_fin.median(), top.giud_S.median(), top.conf_fin.median(), top.conf_S.median(), top.giud_ok.mean()))
    fam = res.groupby("fam").agg(side=("side", "first"), reg=("reg", "first"), xclass=("xclass", "first"), n=("side", "size"), scop_S=("scop_S", "median"), giud_S=("giud_S", "median"), conf_S=("conf_S", "median"),
                                 scop_fin=("scop_fin", "median"), giud_fin=("giud_fin", "median"), conf_fin=("conf_fin", "median"), giud_dd=("giud_dd", "median"), scop_dd=("scop_dd", "median"), conf_dd=("conf_dd", "median"),
                                 scop_ok=("scop_ok", "mean"), giud_ok=("giud_ok", "mean"), conf_ok=("conf_ok", "mean"), trade_anno=("inte_n", lambda x: x.median() / 5.87))
    fam.to_csv(L.HERE / "mappa_famiglie.csv"); pr("famiglie (mediane), ordinate per S in scoperta:\n", fam.sort_values("scop_S", ascending=False).round(2).to_string())
    pr("Spearman fra famiglie (mediana S): scoperta-giudizio %.3f, scoperta-conferma %.3f, giudizio-conferma %.3f" % (sp(fam.scop_S, fam.giud_S), sp(fam.scop_S, fam.conf_S), sp(fam.giud_S, fam.conf_S)))
    res["ma"] = np.where(res.xtype == "A", "ATR", res.xkind)
    for key in ("side", "reg", "ent", "xclass", "ma", "xn", "xpar"):
        sel = res if key not in ("xn", "xpar") else res[res.xtype == "C"]
        gcols = [key] if key not in ("xn", "xpar") else ["xtf", key]
        t = sel.groupby(gcols).agg(n=("side", "size"), conf_S=("conf_S", "median"), scop_S=("scop_S", "median"), giud_S=("giud_S", "median"), conf_fin=("conf_fin", "median"), scop_fin=("scop_fin", "median"),
                                   giud_fin=("giud_fin", "median"), inte_dd=("inte_dd", "median"), conf_ok=("conf_ok", "mean"), scop_ok=("scop_ok", "mean"), giud_ok=("giud_ok", "mean"), trade_anno=("inte_n", lambda x: x.median() / 5.87), wr=("inte_wr", "median"))
        t.to_csv(L.HERE / f"mappa_{key}.csv"); pr(f"per {key}:\n", t.round(3).to_string())
    # EMA contro SMA a parità di tutto il resto (coppie)
    c = res[res.xtype != "A"]; key = ["side", "reg", "ent", "xtype", "xtf", "xpar", "xn"]
    pe = c[c.xkind == "EMA"].set_index(key); ps_ = c[c.xkind == "SMA"].set_index(key)
    for k in ("conf", "scop", "giud"):
        dS = pe[f"{k}_S"] - ps_[f"{k}_S"].reindex(pe.index)
        pr(f"EMA − SMA in coppia ({k}): mediana ΔS %.3f, quota EMA migliore %.3f (n %d)" % (dS.median(), (dS > 0).mean(), len(dS)))
    c4 = res[res.xclass == "C4h"].set_index(["side", "reg", "ent", "xkind", "xpar", "xn"]); c1 = res[res.xclass == "C1D"].set_index(["side", "reg", "ent", "xkind", "xpar", "xn"])
    for k in ("conf", "scop", "giud"):
        dS = c4[f"{k}_S"] - c1[f"{k}_S"].reindex(c4.index)
        pr(f"uscita 4h − 1D in coppia ({k}): mediana ΔS %.3f, quota 4h migliore %.3f" % (dS.median(), (dS > 0).mean()))

    # --- uso complementare dentro W3.2
    d = S["daily"]; c4h = a["close"]
    st1 = L.hyst(c4h, L.ma(c4h, "SMA", 200), 1).resample("1D").last()
    st3 = L.hyst(c4h, L.ma(c4h, "EMA", 50), 2).resample("1D").last()
    kt = W32.table({"K1 uscita+filtro 4h SMA200": (st1, True, True), "K2 solo filtro 4h SMA200": (st1, True, False), "K3 uscita+filtro 4h EMA50 N2": (st3, True, True)})
    kt.to_csv(L.HERE / "w32_k.csv", index=False); pr(kt.round(3).to_string())
    pr("tempo", round(time.time() - t0), "s")
