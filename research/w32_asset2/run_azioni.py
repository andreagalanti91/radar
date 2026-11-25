"""Q3 · azioni: W3.2 solo prezzo contro W3.2 con flusso cmf20 (ma_lib.s1_sim, W-FRI, 0,05%/lato, short 3% annuo). PREREG f40f7a6.
Universo: le 124 linee primarie contate in azioni/counts.csv. Holm sul numero di titoli valutati (124) per ciascuna variante.
Uscite: risultati_azioni.csv, trades_azioni.csv, eq_azioni.csv.gz."""
from multiprocessing import Pool
import pandas as pd
import lib as L

def one(sym):
    f = L.aload(sym); bars = L.abars(f); rows, trs, eqs = [], [], {}
    for v, col in (("prezzo", None), ("cmf20", "cmf20")):
        row, o, _ = L.eval_stock(sym, col, f=f, bars=bars)
        rows.append(dict(yahoo=sym, variante=v, posizione_aperta=(o["open"]["side"] if o["open"] else ""), **row))
        tr = pd.DataFrame(o["trades"] + ([o["open"]] if o["open"] else []))
        if len(tr): tr["yahoo"], tr["variante"] = sym, v; trs.append(tr)
        eqs[f"{sym}|{v}"] = o["equity"]
    eqs[f"{sym}|bh"] = L.bh_curve(f, rows[0]["inizio"], rows[0]["fine"], L.M.FEE)
    return rows, trs, pd.DataFrame(eqs)

if __name__ == "__main__":
    c = pd.read_csv(L.HERE / "azioni" / "counts.csv"); syms = list(c[(c.line == "primaria") & (c.variant == "prezzo")].yahoo)
    R, T, E = [], [], []
    with Pool(4) as pool:
        for i, (rows, trs, eq) in enumerate(pool.imap_unordered(one, syms)):
            R += rows; T += trs; E.append(eq)
            print(i, [(r["yahoo"], r["variante"], r["fin"], r["dd"], r["wr"], r["falliti"], r["p"]) for r in rows], flush=True)
    d = pd.DataFrame(R).merge(L.AU[["yahoo", "name", "country", "currency", "rank_today", "rank_2020", "bitget", "okx", "perp_since"]], on="yahoo", how="left")
    d["operabile"] = d.bitget.eq("si") | d.okx.eq("si")
    for v in ("prezzo", "cmf20"):
        s = d[d.variante == v]; hk = L.holm(dict(zip(s.yahoo, s.p)))
        m = d.variante == v; d.loc[m, "holm"] = d.loc[m, "yahoo"].map(hk)
    d["passa_davvero"] = d.passa15.astype(bool) & d.conferma.astype(bool) & d.holm.fillna(False).astype(bool)
    d.to_csv(L.HERE / "risultati_azioni.csv", index=False); pd.concat(T).to_csv(L.HERE / "trades_azioni.csv", index=False)
    pd.concat(E, axis=1).round(2).to_csv(L.HERE / "eq_azioni.csv.gz")
    for v in ("prezzo", "cmf20"):
        s = d[d.variante == v]; print(v, "passa 1-5", int(s.passa15.sum()), "conferma", int((s.passa15 & s.conferma).sum()), "davvero", int(s.passa_davvero.sum()))
