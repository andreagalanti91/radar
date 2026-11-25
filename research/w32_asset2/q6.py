"""Q6 · portafoglio: BTC + ETH (capitali uguali e separati) contro BTC + ETH + ogni asset che passa davvero in Q1–Q5 ed è operabile
su Bitget o OKX (capitale uguale e separato). Candidati: risultati_crypto.csv (Q1/Q2), risultati_q4.csv, risultati_azioni.csv (Q3),
risultati_q5.csv. Periodi: dal 2020-06-01 (inizio della versione completa) e dal 2021-01-01 (riferimento), ogni asset riparte da
10.000 $ e da flat; liquidità prima dell'inizio dell'asset. Uscite: risultati_q6.csv, out_q6.txt."""
import pandas as pd
import lib as L
import q4

def cands():
    out = []
    q1 = pd.read_csv(L.HERE / "risultati_crypto.csv")
    for q in ("q1", "q2"):
        out += [(t, q) for t in q1[q1[f"passa_davvero_{q}"] & q1.operabile].ticker]
    d4 = pd.read_csv(L.HERE / "risultati_q4.csv"); d4 = d4[d4.passa_davvero & (d4.bitget_perp | d4.okx_perp)]; out += [(t, "q4") for t in d4.ticker]
    da = pd.read_csv(L.HERE / "risultati_azioni.csv"); out += [(t, "q3") for t in da[da.passa_davvero & da.operabile].yahoo]
    d5 = pd.read_csv(L.HERE / "risultati_q5.csv"); out += [(t, "q5") for t in d5[d5.passa_davvero].ticker]
    return [(t, q) for t, q in out if t not in ("BTC", "ETH")]

def curve(t, q, S):
    x = L.CU[L.CU.ticker == t].iloc[0]; s = max(S, x.completa_da); f = L.cfeats(t)
    o = L.csim(f, s, gate=q4.GATE if q == "q4" else None); return o

def wk(o, idx):
    return q4.wpos(L.otrades(o), idx)

if __name__ == "__main__":
    C = cands(); lines = [f"candidati che passano davvero in Q1–Q5 e operabili: {C}"]; rows = []
    sun = q4.sun
    for S in ("2020-06-01", "2021-01-01"):
        O = {t: curve(t, "q1", S) for t in ("BTC", "ETH")}
        for t, q in C: O[f"{t}({q})"] = curve(t, q, S)
        sets = {"BTC solo": ["BTC"], "BTC + ETH": ["BTC", "ETH"], "BTC + ETH + candidati": ["BTC", "ETH"] + [f"{t}({q})" for t, q in C]}
        for k, v in sets.items():
            m, tot = L.port([O[a]["equity"] for a in v], S)
            yrs = (pd.Timestamp(L.CEND) - pd.Timestamp(S)).days / 365.25
            ntr = sum(len(L.otrades(O[a])) for a in v)
            rows.append(dict(da=S, portafoglio=k, asset="+".join(v), **m, trade=ntr, trade_anno=round(ntr / yrs, 1)))
        for t, q in C:
            a = f"{t}({q})"; p = wk(O[a], sun); b = wk(O["BTC"], sun); inpos = p[(p != 0) & (p.index >= S)]
            yrs = (pd.Timestamp(L.CEND) - pd.Timestamp(S)).days / 365.25
            lines.append(f"[{S}] {a}: {len(L.otrades(O[a]))} operazioni ({len(L.otrades(O[a])) / yrs:.1f} l'anno); settimane in posizione {len(inpos)}, "
                         f"BTC nello stesso verso {100 * (b.reindex(inpos.index) == inpos).mean():.0f}%, opposto "
                         f"{100 * ((b.reindex(inpos.index) != 0) & (b.reindex(inpos.index) != inpos)).mean():.0f}%, BTC flat {100 * (b.reindex(inpos.index) == 0).mean():.0f}%")
    d = pd.DataFrame(rows); d.to_csv(L.HERE / "risultati_q6.csv", index=False); lines.append(d.to_string(index=False))
    for S in ("2020-06-01", "2021-01-01"):
        a = d[(d.da == S) & (d.portafoglio == "BTC + ETH")].iloc[0]; b = d[(d.da == S) & (d.portafoglio == "BTC + ETH + candidati")].iloc[0]
        ok = (b.cd > a.cd) and (b.dd >= a.dd - 3)
        lines.append(f"[{S}] BTC+ETH+candidati contro BTC+ETH: CAGR/DD {b.cd} vs {a.cd}, DD {b.dd} vs {a.dd} → {'MIGLIORA' if ok else 'NON migliora'}")
    (L.HERE / "out_q6.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
