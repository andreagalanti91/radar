"""Q1/Q2 · W3.2 completa (parametri di BTC) su tutte le crypto valutabili e brevi; solo prezzo descrittivo. PREREG f40f7a6.
Uscite: risultati_crypto.csv (una riga per moneta), trades_crypto.csv, eq_crypto.csv.gz (equity W3.2 e B&H, 10.000 $)."""
import sys
from multiprocessing import Pool
import numpy as np, pandas as pd
import lib as L

def one(x):
    t, cl, S = x["ticker"], x["classe"], x["completa_da"]
    try:
        if cl in ("valutabile", "breve"):
            f = L.cfeats(t)
            if cl == "breve" and (not isinstance(S, str) or pd.Timestamp(S) > f.index[-1] - pd.Timedelta(days=180)):
                return dict(ticker=t, versione="completa", nota="< 180 g di test"), None, None
            row, o, f = L.eval_crypto(t, S, f=f, plac=(cl == "valutabile"))
            tr = pd.DataFrame(L.otrades(o)); tr["ticker"] = t
            eq = pd.DataFrame({f"{t}|w": o["equity"], f"{t}|bh": L.bh_curve(f, S, row["fine"], 0.002)})
            op = o["open"]; row.update(versione="completa", posizione_aperta=(op["side"] if op else ""), pending=str(o["pending"] or ""))
            return dict(ticker=t, **row), tr, eq
        if cl == "solo prezzo":
            f = L.cfeats(t)[["open", "high", "low", "close"]]
            S = str(max(pd.Timestamp("2020-06-01"), f.index[0] + pd.Timedelta(days=300)).date()); E = str(f.index[-1].date())
            if pd.Timestamp(S) > f.index[-1] - pd.Timedelta(days=180): return dict(ticker=t, versione="solo prezzo", nota="< 180 g"), None, None
            def po(a, e): return L.M.s1_sim(f, a, e, risk=0.25, fee=0.002, short_cost=0.10, wb=L.M.s1_weekly(f[f.index <= pd.Timestamp(e)], "W-SUN"))
            o = po(S, E); m = L.ametrics(o); b = L.bh(f, S, E, 0.002); ps, kind = L.periods(S, E); hs = [L.ametrics(po(a, e))["ret"] for a, e in ps]
            c = L.crit(m, b, hs)
            return dict(ticker=t, versione="solo prezzo", inizio=S, fine=E, **m, bh_fin=b["fin"], bh_dd=b["dd"], bh_cd=b["cd"], bh_cagr=b["cagr"],
                        is_ret=hs[0], oos_ret=hs[1], split=kind, **c, passa15=all(c.values()), falliti=L.failed(c)), None, None
    except Exception as e:  # noqa: BLE001
        return dict(ticker=t, errore=f"{type(e).__name__}: {e}"), None, None
    return dict(ticker=t), None, None

if __name__ == "__main__":
    u = L.CU[L.CU.classe.isin(["valutabile", "breve", "solo prezzo"])]
    jobs = [r._asdict() for r in u.itertuples()]
    rows, trs, eqs = [], [], []
    with Pool(4) as pool:
        for i, (row, tr, eq) in enumerate(pool.imap_unordered(one, jobs)):
            rows.append(row); print(i, row.get("ticker"), row.get("versione"), row.get("fin"), row.get("dd"), row.get("p"), row.get("errore", ""), flush=True)
            if tr is not None and len(tr): trs.append(tr)
            if eq is not None: eqs.append(eq)
    d = pd.DataFrame(rows).merge(L.CU[["ticker", "simbolo", "nome", "rank_oggi", "rank_2020", "classe", "bitget_perp", "okx_perp"]], on="ticker", how="left")
    d["operabile"] = d.bitget_perp.astype(str).eq("True") | d.okx_perp.astype(str).eq("True")
    v = d[d.classe == "valutabile"]
    for q, sel in (("q1", v), ("q2", v[v.rank_2020.notna()])):
        hk = L.holm(dict(zip(sel.ticker, sel.p)))
        d[f"holm_{q}"] = d.ticker.map(hk)
        d[f"passa_davvero_{q}"] = d.ticker.isin(sel.ticker) & d.passa15.fillna(False).astype(bool) & d.conferma.fillna(False).astype(bool) & d[f"holm_{q}"].fillna(False).astype(bool)
    d.to_csv(L.HERE / "risultati_crypto.csv", index=False)
    pd.concat(trs).to_csv(L.HERE / "trades_crypto.csv", index=False)
    pd.concat(eqs, axis=1).round(2).to_csv(L.HERE / "eq_crypto.csv.gz")
    print("valutabili", len(v), "passa 1-5", int(v.passa15.sum()), "Q1 davvero", int(d.passa_davvero_q1.sum()), "Q2 davvero", int(d.passa_davvero_q2.sum()))
