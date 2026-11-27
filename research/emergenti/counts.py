"""emergenti · CONTEGGI DI STRUTTURA (nessun rendimento: niente P&L, equity, win rate o esiti dei trade).
Per ogni moneta dell'universo (data/universe.csv dopo il controllo di abbinamento): anni di dati, perp con taker buy, inizio
della versione completa W3.2 (SMA 40 settimane + flusso perp, w32_asset2/crypto/counts.py), ingressi W3.2 per anno e lato
(radar.weekly.simulate invariato, parametri di BTC: si leggono solo data, lato, prezzo d'ingresso e stop iniziale), verso di BTC
alla domenica del segnale (cancello di radar/scanner.py), rank alla classifica più recente prima del segnale, volume medio del perp
nei 90 giorni prima del segnale, età della moneta, distanza dello stop iniziale (2,5 ATRw) dall'ingresso e confronto con la
liquidazione a 2x e 5x (margine isolato; mantenimento 1% e, in sensibilità, 2,5%).
Scrive data/counts_moneta.csv, data/segnali.csv (un ingresso per riga, senza esiti), data/counts_anno.csv e stampa le tabelle."""
import importlib.util, json, sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; D = HERE / "data"; ROOT = HERE.parents[1]; W32 = HERE.parent / "w32_asset2" / "crypto"
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402
from radar import scanner as SC  # noqa: E402  (solo la funzione cancello, sola lettura)
spec = importlib.util.spec_from_file_location("w32_counts", W32 / "counts.py"); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
C.D = D / "coins"
LAST = pd.Timestamp("2026-11-24"); YEARS = list(range(2021, 2027))
LIQ = {2: (0.49, 0.475), 5: (0.19, 0.175)}          # distanza di liquidazione (mantenimento 1% / 2,5%)

def snap_table():
    s = pd.read_csv(D / "snapshots.csv"); s["giorno"] = pd.to_datetime(s.data.astype(str)); return s

def rank_at(u, snaps, day):
    """rank del ticker canonico nella classifica più recente con data <= day (None se fuori dalla top 200 o prima del 2020)."""
    past = [(g, y) for y, g in snaps.items() if g <= day]
    if not past: return None, None
    g, y = max(past); v = u.get(f"rank_{y}"); return (None if v != v else v), y

def main():
    u = pd.read_csv(D / "universe.csv")
    st = snap_table(); snaps = st.groupby("anno").giorno.first().to_dict()
    fb = C.feats("BTC"); sb = C.full_start(fb); gate = SC.cancello(fb, start=str(sb.date()))
    rows, sig = [], []
    for r in u.itertuples():
        base = r._asdict()
        f = C.feats(r.ticker) if (C.D / f"{r.ticker}_spot.csv.gz").exists() or (C.D / f"{r.ticker}_perp.csv.gz").exists() else None
        row = dict(ticker=r.ticker, rank_oggi=r.rank_oggi, emergente_oggi=r.emergente_oggi, emergente_storico=r.emergente_storico,
                   bitget_perp=r.bitget_perp, okx_perp=r.okx_perp)
        if f is None or not len(f): rows.append(dict(row, classe="senza dati")); continue
        pp = pd.read_csv(C.D / f"{r.ticker}_perp.csv.gz", index_col=0, parse_dates=True) if (C.D / f"{r.ticker}_perp.csv.gz").exists() else None
        row.update(dati_da=str(f.index[0].date()), dati_a=str(f.index[-1].date()), anni_prezzi=round(len(f) / 365.25, 2),
                   anni_perp_tbv=round(pp["tbv"].notna().sum() / 365.25, 2) if pp is not None else 0.0,
                   perp_da=str(pp.index[0].date()) if pp is not None else "")
        fs = C.full_start(f) if f["pf14z"].notna().any() else None
        if fs is None or fs > f.index[-1]:
            rows.append(dict(row, classe="solo prezzo" if f["pf14z"].notna().sum() == 0 else "breve (nessun segnale calcolabile)")); continue
        row["completa_da"] = str(fs.date()); row["anni_completa"] = round((f.index[-1] - fs).days / 365.25, 2)
        o = W.simulate(f, start=str(fs.date()))
        w = o["weekly"]; ok = w[(w.index >= fs) & w["sma"].notna() & w["flow"].notna()]
        row["sett_cond_long"] = int(ok["long"].sum()); row["sett_cond_short"] = int(ok["short"].sum()); row["sett_valide"] = len(ok)
        qv = (pp["close"] * pp["volume"]) if pp is not None else None
        first = f.index[0]
        for t in o["trades"] + ([o["open"]] if o["open"] else []):
            sd = 1 if t["side"] == "long" else -1; e = pd.Timestamp(t["entry"]); s0 = pd.Timestamp(t["signal"])
            px = float(f.loc[e, "open"]) * (1 + W.SLIP * sd); dist = abs(px - t["stop0"]) / px
            rk, ry = rank_at(base, snaps, s0)
            v90 = float(qv[(qv.index <= s0) & (qv.index > s0 - pd.Timedelta(days=90))].mean()) if qv is not None else np.nan
            g = int(gate.get(s0, 0)) if s0 in gate.index else 0
            sig.append(dict(ticker=r.ticker, segnale=str(s0.date()), ingresso=t["entry"], anno=e.year, lato=t["side"],
                            dist_stop=round(dist, 4), esposizione_1x=t["expo"], btc=("flat" if g == 0 else "con" if g == sd else "contro"),
                            rank_al_segnale=rk, classifica=ry, emergente_pit=(rk is not None and 100 < rk <= 200),
                            emergente_oggi=r.emergente_oggi, sett_storia=int((s0 - first).days // 7),
                            vol90_mn=round(v90 / 1e6, 2) if v90 == v90 else None,
                            bitget_listato=(isinstance(r.bitget_perp_da, str) and r.bitget_perp_da <= str(s0.date())),
                            okx_listato=(isinstance(r.okx_perp_da, str) and r.okx_perp_da <= str(s0.date())),
                            aperta=not t.get("exit")))
        mine = [x for x in sig if x["ticker"] == r.ticker]
        ds = np.array([x["dist_stop"] for x in mine]) if mine else np.array([])
        row.update(classe="con segnali W3.2" if mine else "completa, nessun ingresso", n_ingressi=len(mine),
                   n_long=sum(x["lato"] == "long" for x in mine), n_short=sum(x["lato"] == "short" for x in mine),
                   dist_stop_mediana=round(float(np.median(ds)), 4) if len(ds) else None,
                   oltre_liq_2x=int((ds > LIQ[2][0]).sum()), oltre_liq_5x=int((ds > LIQ[5][0]).sum()))
        rows.append(row)
    cm = pd.DataFrame(rows); sg = pd.DataFrame(sig)
    cm.to_csv(D / "counts_moneta.csv", index=False); sg.to_csv(D / "segnali.csv", index=False)
    return u, cm, sg, snaps

def yearly(u, cm, sg):
    out = []
    for Y in YEARS:
        y0 = pd.Timestamp(f"{Y}-01-01")
        live = cm[cm.dati_da.notna() & (pd.to_datetime(cm.dati_da) <= y0 + pd.Timedelta(days=364)) & (pd.to_datetime(cm.dati_a) >= y0)]
        full = cm[cm.completa_da.notna() & (pd.to_datetime(cm.completa_da) <= y0) & (pd.to_datetime(cm.dati_a) >= y0)]
        for grp, sel in (("tutte", lambda x: x.ticker == x.ticker), ("emergenti storiche", lambda x: x.emergente_storico == True),
                         ("emergenti oggi (101-500)", lambda x: x.emergente_oggi == True)):
            ss = sg[sg.anno == Y]
            if grp == "emergenti storiche": ss = ss[ss.emergente_pit]
            elif grp == "emergenti oggi (101-500)": ss = ss[ss.emergente_oggi == True]
            out.append(dict(anno=Y, gruppo=grp, con_dati=int(sel(live).sum()), completa_al_1gen=int(sel(full).sum()),
                            ingressi=len(ss), long=int((ss.lato == "long").sum()), short=int((ss.lato == "short").sum()),
                            long_con_btc=int(((ss.lato == "long") & (ss.btc == "con")).sum()),
                            long_contro_btc=int(((ss.lato == "long") & (ss.btc == "contro")).sum()),
                            short_con_btc=int(((ss.lato == "short") & (ss.btc == "con")).sum()),
                            short_contro_btc=int(((ss.lato == "short") & (ss.btc == "contro")).sum()),
                            dist_mediana=round(float(ss.dist_stop.median()), 3) if len(ss) else None,
                            oltre_2x=int((ss.dist_stop > LIQ[2][0]).sum()), oltre_5x=int((ss.dist_stop > LIQ[5][0]).sum())))
    t = pd.DataFrame(out); t.to_csv(D / "counts_anno.csv", index=False); return t

if __name__ == "__main__":
    u, cm, sg, snaps = main(); t = yearly(u, cm, sg)
    pd.set_option("display.width", 250); print(t.to_string(index=False))
    print(cm.classe.value_counts().to_string())
