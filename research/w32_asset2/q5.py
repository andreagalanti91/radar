"""Q5 · parametri per classe: trailing {2,0; 2,5; 3,0} ATRw × rischio {0,10; 0,15; 0,25}, una scelta per classe sul SOLO IS
(cella con la mediana di classe del CAGR/DD più alta fra quelle con mediana di classe del DD ≥ −35%; CAGR/DD non
arrotondato, perché arrotondato a 2 decimali dava mediane a pari merito), giudizio in OOS per asset.
Crypto: copia di radar/weekly.py (weekly_q5.py, generata qui) con la sola sostituzione delle due costanti (STOP_K = TRAIL_K; R_SHORT,
R_LONG); controllo (c): a 2,5/0,25 stessi trade di radar.weekly. Azioni: ma_lib.s1_sim (k e risk sono già parametri), solo prezzo
perché Q3 non passa su nessun titolo. Classe IS = valutabili con inizio ≤ 30/06/2022 (IS ≥ 6 mesi); OOS = 2023-01-01 → fine (o
dall'inizio se successivo). In OOS: criteri 1–5 sul solo OOS (4 = OOS positivo), conferma (senza il trade migliore; vicini = gli altri
due trailing allo stesso rischio), placebo e Holm sul numero di asset giudicati. Uscite: q5_griglia.csv, risultati_q5.csv, out_q5.txt."""
import importlib.util, re, types
from multiprocessing import Pool
import numpy as np, pandas as pd
import lib as L

KS, RS = (2.0, 2.5, 3.0), (0.10, 0.15, 0.25)
SRC = (L.ROOT / "radar" / "weekly.py").read_text()
COPY = L.HERE / "weekly_q5.py"

def engine_text(k, r):
    s = SRC.replace("STOP_K = TRAIL_K = 2.5\n", f"STOP_K = TRAIL_K = {k}\n", 1)
    s = re.sub(r"^R_SHORT = 0\.25", f"R_SHORT = {r}", s, count=1, flags=re.M)
    s = re.sub(r"^R_LONG = 0\.25", f"R_LONG = {r}", s, count=1, flags=re.M)
    return s

def engine(k, r):
    m = types.ModuleType(f"weekly_q5_{k}_{r}"); m.__file__ = str(COPY); exec(compile(engine_text(k, r), str(COPY), "exec"), m.__dict__); return m

ENG = None
def eng(k, r):
    global ENG
    if ENG is None: ENG = {(kk, rr): engine(kk, rr) for kk in KS for rr in RS}
    return ENG[(k, r)]

def csim(f, s, e, k, r):
    return eng(k, r).simulate(f[f.index <= pd.Timestamp(e)], start=s)

def check_c():
    out = []
    for t in ("BTC", "ETH", "SOL"):
        f = L.cfeats(t); a = L.W.simulate(f, start="2020-06-01"); b = csim(f, "2020-06-01", L.CEND, 2.5, 0.25)
        ka = [(x["entry"], x["side"], x.get("exit"), round(x["pnl"], 10)) for x in a["trades"]]
        kb = [(x["entry"], x["side"], x.get("exit"), round(x["pnl"], 10)) for x in b["trades"]]
        out.append(f"(c) {t}: copia 2,5/0,25 vs radar.weekly: trade {len(kb)}/{len(ka)} identici={ka == kb}, finale "
                   f"{float(b['equity'].iloc[-1]):.2f} vs {float(a['equity'].iloc[-1]):.2f}")
    return out

def oos_crit(m, b):
    return dict(c1=(m["cd"] if m["cd"] is not None else -9) > (b["cd"] if b["cd"] is not None else -9), c2=m["dd"] >= -35,
                c3=(m["wr"] or 0) >= 60, c4=m["ret"] > 0, c5=m["n"] >= 8)

def crypto_one(x):
    t, S = x["ticker"], x["completa_da"]; f = L.cfeats(t); E = str(f.index[-1].date()); rows = []
    for k in KS:
        for r in RS:
            row = dict(ticker=t, classe="altcoin", k=k, r=r)
            if S <= L.HALF_IF_AFTER:
                m = L.omet(csim(f, S, L.IS_END, k, r)); row.update(is_cd=m["cd"], is_cd_raw=m["cd_raw"], is_dd=m["dd"], is_ret=m["ret"])
            so = max(S, L.OOS_START); o = csim(f, so, E, k, r); m = L.omet(o); b = L.bh(f, so, E, 0.002)
            row.update(oos_inizio=so, **{f"oos_{a}": v for a, v in m.items()}, oos_bh_cd=b["cd"], oos_bh_fin=b["fin"], **oos_crit(m, b))
            pa, pm, p = L.placebo(f["close"], so, E, L.otrades(o)); row.update(oos_p=round(p, 4))
            rows.append(row)
    return rows

def stock_one(sym):
    f = L.aload(sym); wb, fw = L.abars(f); S, E = L.astart(f), str(f.index[-1].date()); rows = []
    for k in KS:
        for r in RS:
            row = dict(ticker=sym, classe="azioni", k=k, r=r)
            if S <= L.HALF_IF_AFTER:
                m = L.ametrics(L.asim(f, wb, fw, None, S, L.IS_END, r, k)); row.update(is_cd=m["cd"], is_cd_raw=m["cd_raw"], is_dd=m["dd"], is_ret=m["ret"])
            so = max(S, L.OOS_START); o = L.asim(f, wb, fw, None, so, E, r, k); m = L.ametrics(o); b = L.bh(f, so, E, L.M.FEE)
            row.update(oos_inizio=so, **{f"oos_{a}": v for a, v in m.items()}, oos_bh_cd=b["cd"], oos_bh_fin=b["fin"], **oos_crit(m, b))
            pa, pm, p = L.placebo(f["close"], so, E, o["trades"] + ([o["open"]] if o["open"] else [])); row.update(oos_p=round(p, 4))
            rows.append(row)
    return rows

if __name__ == "__main__":
    COPY.write_text('"""COPIA di radar/weekly.py per Q5 (research/w32_asset2/q5.py): unica differenza ammessa = le due costanti\n'
                    'STOP_K = TRAIL_K e R_SHORT/R_LONG, sostituite da q5.py per ogni cella della griglia. Qui i valori di W3.2 (2,5/0,25)."""\n'
                    + engine_text(2.5, 0.25))
    lines = check_c(); print("\n".join(lines), flush=True)
    cu = L.CU[(L.CU.classe == "valutabile") & (L.CU.ticker != "BTC")]
    c = pd.read_csv(L.HERE / "azioni" / "counts.csv"); syms = list(c[(c.line == "primaria") & (c.variant == "prezzo")].yahoo)
    rows = []
    with Pool(4) as pool:
        for i, rr in enumerate(pool.imap_unordered(crypto_one, [r._asdict() for r in cu.itertuples()])): rows += rr; print("c", i, rr[0]["ticker"], flush=True)
        for i, rr in enumerate(pool.imap_unordered(stock_one, syms)): rows += rr; print("a", i, rr[0]["ticker"], flush=True)
    g = pd.DataFrame(rows); g.to_csv(L.HERE / "q5_griglia.csv", index=False)
    res = []
    for cl in ("altcoin", "azioni"):
        x = g[g.classe == cl]
        cell = x.groupby(["k", "r"]).agg(n_is=("is_cd", "count"), is_cd_med=("is_cd_raw", "median"), is_dd_med=("is_dd", "median"),
                                         oos_cd_med=("oos_cd", "median"), oos_dd_med=("oos_dd", "median"),
                                         oos_15=("c1", lambda s: int((x.loc[s.index, ["c1", "c2", "c3", "c4", "c5"]].all(axis=1)).sum()))).reset_index()
        ok = cell[cell.is_dd_med >= -35]
        ch = ok.sort_values("is_cd_med", ascending=False).iloc[0] if len(ok) else None
        lines.append(f"\n[{cl}] griglia (mediane di classe; IS su {int(cell.n_is.max())} asset, OOS su {x.ticker.nunique()}):\n" + cell.round(2).to_string(index=False))
        base = cell[(cell.k == 2.5) & (cell.r == 0.25)].iloc[0]
        post = cell.sort_values("oos_cd_med", ascending=False).iloc[0]
        if ch is None:
            lines.append(f"[{cl}] nessuna cella con mediana DD IS ≥ −35%: nessuna scelta; si resta ai parametri di BTC"); continue
        k, r = ch.k, ch.r
        sel = x[(x.k == k) & (x.r == r)].copy()
        for t in sel.ticker:
            nb = x[(x.ticker == t) & (x.r == r) & (x.k != k)]
            bc = sel.loc[sel.ticker == t, "oos_bh_cd"].iloc[0]; bc = -9 if pd.isna(bc) else bc
            sel.loc[sel.ticker == t, "conferma"] = (sel.loc[sel.ticker == t, "oos_wo"].iloc[0] > 10000) and (nb.oos_cd.fillna(-9) > bc).sum() >= len(nb) / 2
        sel["passa15"] = sel[["c1", "c2", "c3", "c4", "c5"]].all(axis=1)
        hk = L.holm(dict(zip(sel.ticker, sel.oos_p))); sel["holm"] = sel.ticker.map(hk)
        sel["passa_davvero"] = sel.passa15 & sel.conferma.astype(bool) & sel.holm
        res.append(sel)
        migliora = (ch.oos_cd_med > base.oos_cd_med) and (ch.oos_15 > base.oos_15)
        lines.append(f"[{cl}] SCELTA IS: trailing {k} ATRw, rischio {r} (mediana IS CAGR/DD {ch.is_cd_med:.2f}, DD {ch.is_dd_med:.1f}) · "
                     f"OOS: mediana CAGR/DD {ch.oos_cd_med:.2f} contro {base.oos_cd_med:.2f} dei parametri di BTC; passano 1–5 in OOS "
                     f"{int(ch.oos_15)} contro {int(base.oos_15)} → {'MIGLIORA' if migliora else 'NON migliora'} · passano davvero in OOS "
                     f"{int(sel.passa_davvero.sum())}: {list(sel[sel.passa_davvero].ticker)} · passano 1–5 OOS: {list(sel[sel.passa15].ticker)}")
        lines.append(f"[{cl}] a posteriori (NON utilizzabile): cella OOS migliore {post.k}/{post.r}, mediana CAGR/DD {post.oos_cd_med:.2f}")
    pd.concat(res).to_csv(L.HERE / "risultati_q5.csv", index=False)
    (L.HERE / "out_q5.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
