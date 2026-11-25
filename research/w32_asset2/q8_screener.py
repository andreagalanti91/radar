"""Q8 · motore di ricerca settimanale, prova all'indietro senza sguardo al futuro (descrittivo).
Ogni 1° gennaio Y dal 2022: idonee = crypto con flusso perp (classi "valutabile" e "breve" di crypto/universe.csv: la classe finale
non si usa, perché dipende dal futuro) con versione completa iniziata prima di Y, serie viva al 1° gennaio e ≥ 2 anni di prezzi
(primo dato ≤ 1° gennaio Y−2). Scelte = idonee che sulla sola storia [completa_da, 31/12/Y−1] passano i criteri 1, 2, 3 e 5
(W3.2 con rischio e parametri di BTC). L'anno Y si opera con W3.2 da flat il 1° gennaio fino al 31/12 (o all'ultimo dato),
capitale uguale e separato; nessuna scelta = liquidità. Stessa ripartenza annuale per "BTC + ETH" e "tutte le idonee".
Uscite: risultati_q8.csv (asset × anno), out_q8.txt."""
from multiprocessing import Pool
import numpy as np, pandas as pd
import lib as L

YEARS = [2022, 2023, 2024, 2025, 2026]

def one(x):
    t, S0 = x["ticker"], x["completa_da"]; rows = []
    if not isinstance(S0, str): return rows
    f = L.cfeats(t); first = pd.Timestamp(x["dati_da"])
    for Y in YEARS:
        y0, yend = pd.Timestamp(f"{Y}-01-01"), pd.Timestamp(f"{Y}-12-31")
        if not (pd.Timestamp(S0) < y0 and f.index[-1] >= y0 and first <= pd.Timestamp(f"{Y - 2}-01-01")): continue
        he = str((y0 - pd.Timedelta(days=1)).date())
        m = L.omet(L.csim(f, S0, he)); b = L.bh(f, S0, he, 0.002)
        c = dict(c1=(m["cd"] if m["cd"] is not None else -9) > (b["cd"] if b["cd"] is not None else -9), c2=m["dd"] >= -35, c3=(m["wr"] or 0) >= 60, c5=m["n"] >= 8)
        E = str(min(yend, f.index[-1]).date()); oy = L.csim(f, str(y0.date()), E); my = L.omet(oy)
        rows.append(dict(ticker=t, anno=Y, st_fin=m["fin"], st_dd=m["dd"], st_wr=m["wr"], st_n=m["n"], st_cd=m["cd"], st_bh_cd=b["cd"], **c,
                         scelta=all(c.values()), anno_ret=my["ret"], anno_dd=my["dd"], anno_n=my["n"],
                         eq=oy["equity"].dropna().round(2).to_json(date_format="iso")))
    return rows

if __name__ == "__main__":
    u = L.CU[L.CU.classe.isin(["valutabile", "breve"])]
    rows = []
    with Pool(4) as pool:
        for rr in pool.imap_unordered(one, [r._asdict() for r in u.itertuples()]): rows += rr
    d = pd.DataFrame(rows).merge(L.CU[["ticker", "simbolo", "bitget_perp", "okx_perp"]], on="ticker")
    eqs = {(r.ticker, r.anno): pd.read_json(__import__("io").StringIO(r.eq), typ="series") for r in d.itertuples()}
    d.drop(columns=["eq"]).to_csv(L.HERE / "risultati_q8.csv", index=False)
    lines, acc = [], {"screener": [], "BTC + ETH": [], "tutte le idonee": [], "solo BTC": []}
    for Y in YEARS:
        x = d[d.anno == Y]; end = min(pd.Timestamp(f"{Y}-12-31"), pd.Timestamp(L.CEND))
        sets = {"screener": list(x[x.scelta].ticker), "BTC + ETH": ["BTC", "ETH"], "tutte le idonee": list(x.ticker), "solo BTC": ["BTC"]}
        res = {}
        for k, v in sets.items():
            if not v:
                tot = pd.Series(10000.0, index=pd.date_range(f"{Y}-01-01", end)); res[k] = dict(n=0, ret=0.0, dd=0.0)
            else:
                m, tot = L.port([eqs[(t, Y)] for t in v], f"{Y}-01-01", str(end.date())); res[k] = dict(n=len(v), ret=round((m["fin"] / 10000 - 1) * 100, 1), dd=m["dd"])
            acc[k].append(tot / 10000)
        sc = x[x.scelta]
        lines.append(f"{Y}: idonee {len(x)}, scelte {len(sc)}: " + (", ".join(f"{r.simbolo} ({r.anno_ret:+.0f}%)" for r in sc.itertuples()) or "nessuna")
                     + " | " + " · ".join(f"{k} {v['ret']:+.1f}% (DD {v['dd']})" for k, v in res.items()))
    lines.append("\nConto composto 2022-01-01 → " + L.CEND + " (ripartenza da flat ogni 1° gennaio):")
    for k, parts in acc.items():
        e = pd.concat([p * np.prod([q.iloc[-1] for q in parts[:i]]) for i, p in enumerate(parts)]) * 10000
        yrs = (e.index[-1] - e.index[0]).days / 365.25; dd = float((e / e.cummax() - 1).min()); cg = (e.iloc[-1] / 10000) ** (1 / yrs) - 1
        lines.append(f"  {k:16s} {e.iloc[-1]:>9.0f} $, CAGR {cg * 100:5.1f}%, DD {dd * 100:5.1f}%, CAGR/DD {cg / abs(dd):.2f}")
    (L.HERE / "out_q8.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
