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
        elif bool(r.okx_perp) and isinstance(r.okx_perp_simbolo, str) and r.okx_perp_simbolo:
            try: pp = okx_series(r.okx_perp_simbolo)
            except Exception as e: print("OKX", t, repr(e)[:120]); pp = None
            sp, fu = None, None
            fp = OKXD / f"{r.okx_perp_simbolo}_funding.csv.gz"
            if fp.exists(): fu = pd.read_csv(fp, index_col=0, parse_dates=True)
            ssp, spp, sfu = [], ([B.seg(pp, "okx swap (taker da rubik)")] if pp is not None and len(pp) else []), ([B.seg(fu, "okx funding ~3 mesi")] if fu is not None else [])
        else:
            sp = pp = fu = None; ssp = spp = sfu = []
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
    print("monete con file:", len({p.name.split("_")[0] for p in COINS.glob("*.csv.gz")}))
