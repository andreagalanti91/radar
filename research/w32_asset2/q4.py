"""Q4 · BTC come cancello: un'altcoin entra solo se alla stessa domenica W3.2 su BTC è in posizione nello stesso verso (o vi entra
quel giorno: segnale di BTC della stessa domenica); uscite proprie. BTC = W3.2 dal 2020-06-01 (parametri invariati, anche nei vicini).
"In posizione" alla domenica d = entrata ≤ d < uscita (un'uscita di BTC decisa quella domenica conta ancora come in posizione).
Holm sulle altcoin valutabili (78). Uscite: risultati_q4.csv, out_q4.txt."""
from multiprocessing import Pool
import pandas as pd
import lib as L

fb = L.cfeats("BTC"); ob = L.csim(fb, "2020-06-01")
sun = fb.index[fb.index.dayofweek == 6]; GATE = pd.Series(0, index=sun)
for t in L.otrades(ob):
    a, sd = pd.Timestamp(t["entry"]), (1 if t["side"] == "long" else -1)
    b = pd.Timestamp(t["exit"]) if t.get("exit") else sun[-1] + pd.Timedelta(days=1)
    GATE[(GATE.index >= a) & (GATE.index < b)] = sd; GATE[pd.Timestamp(t["signal"])] = sd

def wpos(trs, idx):
    s = pd.Series(0, index=idx)
    for t in trs:
        a = pd.Timestamp(t["entry"]); b = pd.Timestamp(t["exit"]) if t.get("exit") else idx[-1] + pd.Timedelta(days=1)
        s[(s.index >= a) & (s.index < b)] = 1 if t["side"] == "long" else -1
    return s

def one(x):
    t, S = x["ticker"], x["completa_da"]
    row, o, f = L.eval_crypto(t, S, gate=GATE)
    q1 = pd.read_csv(L.HERE / "trades_crypto.csv"); q1 = q1[q1.ticker == t]
    g = GATE.reindex(pd.to_datetime(q1.signal)).fillna(0).to_numpy(); sd = q1.side.map({"long": 1, "short": -1}).to_numpy()
    pw = wpos(L.otrades(o), sun); inpos = pw[(pw != 0) & (pw.index >= S)]; bt = GATE.reindex(inpos.index)
    return dict(ticker=t, **row, q1_trade=len(q1), q1_trade_stesso_verso_btc=int((g == sd).sum()),
                q4_sett_in_pos=len(inpos), q4_sett_stesso_verso_pct=round(100 * float((bt == inpos).mean()), 1) if len(inpos) else None)

if __name__ == "__main__":
    u = L.CU[(L.CU.classe == "valutabile") & (L.CU.ticker != "BTC")]
    with Pool(4) as pool: rows = list(pool.imap_unordered(one, [r._asdict() for r in u.itertuples()]))
    d = pd.DataFrame(rows).merge(L.CU[["ticker", "simbolo", "rank_oggi", "rank_2020", "bitget_perp", "okx_perp"]], on="ticker")
    hk = L.holm(dict(zip(d.ticker, d.p))); d["holm"] = d.ticker.map(hk)
    d["passa_davvero"] = d.passa15 & d.conferma & d.holm
    d.to_csv(L.HERE / "risultati_q4.csv", index=False)
    q1 = pd.read_csv(L.HERE / "risultati_crypto.csv").set_index("ticker")
    lines = [f"BTC (cancello) dal 2020-06-01: {len(L.otrades(ob))} operazioni; domeniche con cancello long/short/flat: "
             f"{(GATE > 0).sum()}/{(GATE < 0).sum()}/{(GATE == 0).sum()}",
             f"altcoin valutabili {len(d)} · passano 1-5 {int(d.passa15.sum())} · conferma {int((d.passa15 & d.conferma).sum())} · davvero {int(d.passa_davvero.sum())}",
             f"mediane Q4: finale {d.fin.median():.0f}, DD {d.dd.median():.1f}, WR {d.wr.median():.0f}, trade {d.n.median():.0f}, CAGR/DD {d.cd.median():.2f}",
             f"mediane Q1 stesse monete: finale {q1.loc[d.ticker].fin.median():.0f}, DD {q1.loc[d.ticker].dd.median():.1f}, WR {q1.loc[d.ticker].wr.median():.0f}, "
             f"trade {q1.loc[d.ticker].n.median():.0f}, CAGR/DD {q1.loc[d.ticker].cd.median():.2f}",
             f"operazioni Q1 delle altcoin con BTC nello stesso verso alla domenica del segnale: {d.q1_trade_stesso_verso_btc.sum()}/{d.q1_trade.sum()} "
             f"({100 * d.q1_trade_stesso_verso_btc.sum() / d.q1_trade.sum():.0f}%)",
             f"Q4: settimane in posizione con BTC nello stesso verso (mediana per moneta) {d.q4_sett_stesso_verso_pct.median():.0f}%"]
    (L.HERE / "out_q4.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
