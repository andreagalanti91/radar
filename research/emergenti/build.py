"""emergenti · compone i file per moneta (data/coins/<T>_spot|perp|funding.csv.gz, formato di w32_asset2: date,open,high,low,
close,volume,tbv / date,funding) dalle serie grezze Binance (data/raw/bn di questo studio + quelle già scaricate da w32_asset2),
con catene di ticker, riscalature e tagli di w32_asset2/crypto/build.py (funzioni importate, nessuna copia della logica).
Monete senza perp Binance ma con perp OKX vivo: candele e volumi taker OKX (funzioni di radar/scanner.py, sola lettura, pause
pubbliche; taker solo da ~12/2022, funding solo ~3 mesi). Nessun dato inventato: i buchi restano buchi.
Controllo dell'abbinamento per prezzo: prezzo CoinGecko di oggi contro l'ultima chiusura (24/11), prezzo CMC di ogni istantanea
contro la chiusura dello stesso giorno; rapporto fuori da [0,5; 2] = abbinamento sbagliato (ticker riusato o moneta diversa):
la moneta resta nell'universo ma senza dati per quella classifica. Scrive data/coins/, data/sources.csv, data/match.csv."""
import importlib.util, json, os, sys
from datetime import date
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; D = HERE / "data"; ROOT = HERE.parents[1]; W32 = HERE.parent / "w32_asset2" / "crypto"
COINS = D / "coins"; COINS.mkdir(parents=True, exist_ok=True)
ALL = D / "raw" / "bn_all"; ALL.mkdir(parents=True, exist_ok=True)
OKXD = D / "raw" / "okx"; OKXD.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(W32))
spec = importlib.util.spec_from_file_location("w32_build", W32 / "build.py"); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
LAST = pd.Timestamp("2026-11-24")

def link_all():
    """una sola cartella (collegamenti) con le serie grezze dei due studi; prevalgono quelle scaricate qui."""
    for src in (W32 / "data" / "raw" / "bn", D / "raw" / "bn"):
        for p in src.glob("*.csv.gz"):
            q = ALL / p.name
            if q.is_symlink() or q.exists(): q.unlink()
            os.symlink(p.resolve(), q)

def okx_series(inst):
    """perp OKX nel formato Binance (volumi taker = tbv) con cache in data/raw/okx/."""
    p = OKXD / f"{inst}_perp.csv.gz"
    if p.exists(): return pd.read_csv(p, index_col=0, parse_dates=True)
    sys.path.insert(0, str(ROOT))
    from radar import scanner as SC
    import requests
    s = requests.Session(); s.headers["User-Agent"] = "radar-research-script/1.0 (python-requests; academic backtest)"
    def get(url, params=None):
        r = s.get(url, params=params, timeout=30)
        if r.status_code == 404: return None
        r.raise_for_status(); return r.content
    net = SC.Rete(get=get)
    x = SC.scarica_okx_perp(net, inst, date(2019, 1, 1), (LAST + pd.Timedelta(days=1)).date())
    fu = SC.scarica_okx_funding(net, inst, date(2026, 8, 1), (LAST + pd.Timedelta(days=1)).date())
    x.index.name = "date"; x.to_csv(p, compression="gzip")
    if len(fu): fu[["funding"]].to_csv(OKXD / f"{inst}_funding.csv.gz", compression="gzip")
    return x

def okx_funding(inst):
    p = OKXD / f"{inst}_funding.csv.gz"
    if p.exists(): return pd.read_csv(p, index_col=0, parse_dates=True)
    sys.path.insert(0, str(ROOT))
    from radar import scanner as SC
    import requests
    s = requests.Session(); s.headers["User-Agent"] = "radar-research-script/1.0 (python-requests; academic backtest)"
    def get(url, params=None):
        r = s.get(url, params=params, timeout=30)
        if r.status_code == 404: return None
        r.raise_for_status(); return r.content
    fu = SC.scarica_okx_funding(SC.Rete(get=get), inst, date(2026, 10, 25), (LAST + pd.Timedelta(days=1)).date())
    fu[["funding"]].to_csv(p, compression="gzip"); return fu[["funding"]]

SALTI = []
def salti(t, sp, pp):
    """Controllo automatico dei salti giornalieri > 3x (chiusura/chiusura precedente) su spot e perp. Cambio di denominazione =
    apertura del giorno del salto pari alla chiusura precedente divisa (o moltiplicata) per 10, 100 o 1000 (±3%): i dati della
    moneta si tagliano dal giorno prima del salto (resta la storia vecchia, come un delisting). Gli altri salti si segnalano
    (data/salti.csv): su un buco di dati (> 3 giorni) o movimento reale (apertura continua: crolli come LUNA, FTT, OM, DEXE, H)."""
    cut = None
    for k, x in (("spot", sp), ("perp", pp)):
        if x is None or len(x) < 2: continue
        c = x["close"]; pc = c.shift(); r = c / pc
        for d in r.index[(r > 3) | (r < 1 / 3)]:
            i = x.index.get_loc(d); prev, o = float(c.iloc[i - 1]), float(x["open"].iloc[i]); gap = (d - x.index[i - 1]).days
            red = any(0.97 <= o * f / prev <= 1.03 for f in (10, 100, 1000, 0.1, 0.01, 0.001))
            tipo = "cambio di denominazione: dati tagliati" if red else ("salto su un buco di dati" if gap > 3 else "movimento reale (apertura continua)")
            SALTI.append(dict(ticker=t, serie=k, data=str(d.date()), chiusura_prec=prev, apertura=o, chiusura=float(c.iloc[i]),
                              giorni_dal_prec=gap, tipo=tipo))
            if red: cut = d if cut is None else min(cut, d)
    return cut

def close_at(sp, pp, day):
    for x in (sp, pp):
        if x is not None and len(x):
            y = x[(x.index <= day) & (x.index >= day - pd.Timedelta(days=3))]
            if len(y): return float(y["close"].iloc[-1])
    return None

if __name__ == "__main__":
    link_all(); B.BN = ALL
    u = pd.read_csv(D / "universe_raw.csv"); u = u[u.escluso.isna()]
    s = pd.read_csv(D / "snapshots.csv"); snaps = s.groupby("anno").data.first().to_dict()
    cmcpx = {(a, sl): p for a, sl, p in zip(s.anno, s.slug, s.prezzo)}
    srcs, match = [], []
    for r in u.itertuples():
        t = r.ticker; ch = json.loads(r.chain)
        has_bn = any(c.get("spot") or c.get("perp") for c in ch)
        if has_bn:
            sp, pp, fu, ssp, spp, sfu = B.series(t, ch)
            # mese non ancora archiviato da Binance (novembre 2026): funding OKX dello stesso asset (come w32_asset2/build.py)
            if fu is not None and pp is not None and pp.index[-1] >= LAST - pd.Timedelta(days=3) and fu.index[-1] < LAST:
                o = None
                for q in (W32 / "data" / "raw" / "okx" / f"{t}-USDT-SWAP_funding.csv.gz",
                          OKXD / f"{r.okx_perp_simbolo}_funding.csv.gz" if isinstance(r.okx_perp_simbolo, str) else None):
                    if q is not None and q.exists(): o = pd.read_csv(q, index_col=0, parse_dates=True); break
                if o is None and bool(r.okx_perp) and isinstance(r.okx_perp_simbolo, str) and r.okx_perp_simbolo:
                    try: o = okx_funding(r.okx_perp_simbolo)
                    except Exception as e: print("OKX funding", t, repr(e)[:100]); o = None
                if o is not None and len(o):
                    o = o[(o.index > fu.index[-1]) & (o.index <= LAST)][["funding"]]
                    if len(o): fu = pd.concat([fu, o]); sfu.append(B.seg(o, "okx funding (mese non archiviato da Binance)"))
        elif bool(r.okx_perp) and isinstance(r.okx_perp_simbolo, str) and r.okx_perp_simbolo:
            try: pp = okx_series(r.okx_perp_simbolo)
            except Exception as e: print("OKX", t, repr(e)[:120]); pp = None
            sp, fu = None, None
            fp = OKXD / f"{r.okx_perp_simbolo}_funding.csv.gz"
            if fp.exists(): fu = pd.read_csv(fp, index_col=0, parse_dates=True)
            ssp, spp, sfu = [], ([B.seg(pp, "okx swap (taker da rubik)")] if pp is not None and len(pp) else []), ([B.seg(fu, "okx funding ~3 mesi")] if fu is not None else [])
        else:
            sp = pp = fu = None; ssp = spp = sfu = []
        cut = salti(t, sp, pp)
        if cut is not None:
            sp, pp, fu = (None if x is None else x[x.index < cut] for x in (sp, pp, fu))
        # controllo dell'abbinamento per prezzo
        m = dict(ticker=t)
        if r.prezzo_oggi == r.prezzo_oggi and r.prezzo_oggi:
            c = close_at(sp, pp, LAST); m["oggi_rapporto"] = None if c is None else round(c / r.prezzo_oggi, 3)
        for y, day in snaps.items():
            sl = getattr(r, f"slug_{y}", None)
            if isinstance(sl, str):
                c = close_at(sp, pp, pd.Timestamp(str(day))); pc = cmcpx.get((y, sl))
                m[f"r_{y}"] = None if c is None or not pc else round(c / pc, 3)
        match.append(m)
        for k, x in (("spot", sp), ("perp", pp), ("funding", fu)):
            p = COINS / f"{t}_{k}.csv.gz"
            if x is not None and len(x):
                x = x[x.index <= LAST]; x.index.name = "date"; x.to_csv(p, compression="gzip")
            elif p.exists(): p.unlink()
        srcs.append(dict(ticker=t, spot=" | ".join(filter(None, ssp)), perp=" | ".join(filter(None, spp)), funding=" | ".join(filter(None, sfu))))
    pd.DataFrame(srcs).to_csv(D / "sources.csv", index=False); pd.DataFrame(match).to_csv(D / "match_raw.csv", index=False)
    pd.DataFrame(SALTI).to_csv(D / "salti.csv", index=False); print(pd.DataFrame(SALTI).groupby("tipo").ticker.apply(lambda x: sorted(set(x))).to_string())
    print("monete con file:", len({p.name.split("_")[0] for p in COINS.glob("*.csv.gz")}))
