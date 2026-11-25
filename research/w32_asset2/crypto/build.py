"""w32_asset2/crypto: compone i file per moneta nel formato di w32_top100 (data/<T>_spot.csv.gz, _perp.csv.gz, _funding.csv.gz:
date,open,high,low,close,volume,tbv / date,funding) dalle serie grezze (fetch.py, okx.py), con catene di ticker e riscalature
di universe.py; scrive data/sources.csv (da dove viene ogni tratto) e data/qc.csv (controlli di qualità). Nessun dato inventato:
i buchi restano buchi, tbv mancante resta vuoto (fonti senza taker buy)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import universe as U
HERE = Path(__file__).resolve().parent; D = HERE / "data"; RAW = D / "raw"; BN = RAW / "bn"; OK = RAW / "okx"; BG = RAW / "bitget"
LAST = pd.Timestamp("2026-11-24")
PX = ["open", "high", "low", "close"]

def rd(p):
    return pd.read_csv(p, index_col=0, parse_dates=True) if p.exists() else None

DROPPED = {}
def traded(x, key):
    """giorni a volume zero = mercato fermo/delistato (l'archivio continua con il prezzo congelato, es. TON, RAYUSDT): si tolgono."""
    if x is None: return None
    z = x["volume"] <= 0
    if z.any(): DROPPED[key] = DROPPED.get(key, 0) + int(z.sum())
    return x[~z]

def scale(x, div):
    x = x.copy(); x[PX] = x[PX] / div
    if "volume" in x: x[["volume", "tbv"]] = x[["volume", "tbv"]] * div
    return x

def perp_div(sym):
    return 1e6 if sym.startswith(("1M", "1000000")) else 1000 if sym.startswith("1000") else 1

def stitch(parts):
    """parts: [(df, etichetta)] in ordine; il tratto successivo prevale dal suo primo giorno."""
    out, src = None, []
    for x, lab in parts:
        if x is None or not len(x): continue
        if out is None: out = x
        else: out = pd.concat([out[out.index < x.index[0]], x])
        src.append(lab)
    if out is None: return None, []
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out, src

def seg(x, lab):
    return f"{lab} {x.index[0].date()}..{x.index[-1].date()}" if x is not None and len(x) else None

def series(t, ch):
    sp_parts, pp_parts, fu_parts = [], [], []
    for c in ch:
        cut = (lambda x: x if x is None or c["until"] is None else x[x.index < c["until"]])
        if c["spot"]:
            x = traded(cut(rd(BN / f"{c['spot']}_spot.csv.gz")), (t, "spot"))
            if x is not None: x = scale(x, c["fac"]); sp_parts.append((x, seg(x, f"binance spot {c['spot']}")))
        if c["perp"]:
            x = traded(cut(rd(BN / f"{c['perp']}_perp.csv.gz")), (t, "perp"))
            if x is not None: x = scale(x, c["fac"] * perp_div(c["perp"])); pp_parts.append((x, seg(x, f"binance perp {c['perp']}")))
            y = cut(rd(BN / f"{c['perp']}_funding.csv.gz"))
            if y is not None and x is not None and len(x): y = y[y.index <= x.index[-1]]   # funding del contratto congelato: no
            if y is not None: fu_parts.append((y, seg(y, f"binance funding {c['perp']}")))
    # estensioni all'indietro dichiarate (punto 4: SOL e TAO il più lunghi possibile)
    if t == "SOL":
        x = rd(BN / "SOLBUSD_spot.csv.gz")
        if x is not None: sp_parts.insert(0, (x, seg(x, "binance spot SOLBUSD (BUSD~USD)")))
    if t == "TAO":
        x = rd(BG / "TAOUSDT_spot.csv.gz")
        if x is not None and sp_parts:
            x = x[x.index < sp_parts[0][0].index[0]]; sp_parts.insert(0, (x, seg(x, "bitget spot TAOUSDT (senza tbv)")))
    sp, ssp = stitch(sp_parts); pp, spp = stitch(pp_parts); fu, sfu = stitch(fu_parts)
    if t in U.CUT_FROM:
        sp, pp, fu = (None if x is None else x[x.index >= U.CUT_FROM[t]] for x in (sp, pp, fu))
    return sp, pp, fu, ssp, spp, sfu

def okx_fallback(t):
    sp = rd(OK / f"{t}-USDT_candles.csv.gz"); pp = rd(OK / f"{t}-USDT-SWAP_candles.csv.gz"); fu = rd(OK / f"{t}-USDT-SWAP_funding.csv.gz")
    return sp, pp, fu, [seg(sp, "okx spot (senza tbv)")] if sp is not None else [], [seg(pp, "okx swap (senza tbv)")] if pp is not None else [], \
        [seg(fu, "okx funding (solo ~3 mesi)")] if fu is not None else []

ARCH_FUND_END = pd.Timestamp("2026-10-31")   # ultimo mese dell'archivio mensile funding Binance al 25/11/2026

def qc(t, k, x, sp=None, ref_end=LAST):
    if x is None or not len(x): return dict(ticker=t, serie=k, righe=0, nota="vuota")
    r = dict(ticker=t, serie=k, righe=len(x), giorni_vol0_tolti=DROPPED.get((t, k), 0), da=str(x.index[0].date()), a=str(x.index[-1].date()),
             buchi_giorni=int(len(pd.date_range(x.index[0], x.index[-1])) - len(x)), ferma=bool(x.index[-1] < ref_end - pd.Timedelta(days=3)))
    if k == "funding":
        r["funding_abs_gt_1pct"] = int((x["funding"].abs() > 0.01).sum()); return r
    c = x["close"]; lr = np.log(c / c.shift()).abs()
    r.update(nan_o_zero=int((c.isna() | (c <= 0)).sum()), salti_x3=int((lr > np.log(3)).sum()),
             ohlc_incoerenti=int(((x["high"] < x[["open", "close"]].max(axis=1) * 0.999) | (x["low"] > x[["open", "close"]].min(axis=1) * 1.001)).sum()),
             tbv_mancante=int(x["tbv"].isna().sum()), tbv_gt_vol=int((x["tbv"] > x["volume"] * 1.0001).sum()))
    if sp is not None and k == "perp":
        j = pd.concat([sp["close"], c], axis=1, keys=["s", "p"], sort=True).dropna()
        if len(j): r["spot_perp_diff_mediana_pct"] = round(float((j.p / j.s - 1).abs().median() * 100), 3); r["spot_perp_giorni_gt5pct"] = int(((j.p / j.s - 1).abs() > 0.05).sum())
    return r

if __name__ == "__main__":
    u = pd.read_csv(D / "universe_raw.csv"); u = u[u.escluso.isna()]
    srcs, qcs = [], []
    for r in u.itertuples():
        t = r.ticker; has_bn = isinstance(r.chain, str) and (r.bn_spot == True or isinstance(r.bn_perp, str))
        sp, pp, fu, ssp, spp, sfu = series(t, json.loads(r.chain)) if has_bn else okx_fallback(t)
        if has_bn and fu is not None and pp is not None and pp.index[-1] >= LAST - pd.Timedelta(days=3):
            o = rd(OK / f"{t}-USDT-SWAP_funding.csv.gz")       # mese non ancora archiviato da Binance: funding OKX (stesso asset)
            if o is not None:
                o = o[(o.index > fu.index[-1]) & (o.index <= LAST)]
                if len(o): fu = pd.concat([fu, o]); sfu.append(seg(o, "okx funding (mese non archiviato da Binance)"))
        for k, x in (("spot", sp), ("perp", pp), ("funding", fu)):
            p = D / f"{t}_{k}.csv.gz"
            if x is not None and len(x):
                x = x[x.index <= LAST]; x.index.name = "date"; x.to_csv(p, compression="gzip")
            elif p.exists(): p.unlink()
        srcs.append(dict(ticker=t, spot=" | ".join(filter(None, ssp)), perp=" | ".join(filter(None, spp)), funding=" | ".join(filter(None, sfu))))
        fend = LAST if fu is not None and fu.index[-1] > ARCH_FUND_END else ARCH_FUND_END     # senza OKX il funding si ferma a fine ottobre
        if pp is not None and len(pp): fend = min(fend, pp.index[-1])
        qcs += [qc(t, "spot", sp), qc(t, "perp", pp, sp), qc(t, "funding", fu, ref_end=fend)]
    pd.DataFrame(srcs).to_csv(D / "sources.csv", index=False); q = pd.DataFrame(qcs); q.to_csv(D / "qc.csv", index=False)
    q = q[q.righe > 0]
    print("serie non vuote", len(q), "| ferme", int(q.ferma.sum()), "| con salti x3", int((q.salti_x3 > 0).sum()),
          "| OHLC incoerenti", int((q.ohlc_incoerenti > 0).sum()), "| spot/perp > 5% (giorni>5)", int((q.get("spot_perp_giorni_gt5pct", 0) > 5).sum()))
