"""w32_asset2/crypto: scarica dall'archivio pubblico data.binance.vision (non da fapi/api, bloccate dal runner USA) per ogni
simbolo Binance della catena di universe_raw.csv:
  spot 1d (dal 2018-06: serve la SMA 40 settimane al 01/01/2020), perp USDT-M 1d con taker buy (dal 2019-09), funding mensile.
Archivio grezzo per simbolo in data/raw/bn/<SIMBOLO>_<spot|perp|funding>.csv.gz (prezzi non riscalati), riprendibile:
scarica solo i mesi/giorni mancanti (mesi dal listing S3, giorni del mese in corso dai file giornalieri). I file di
research/w32_top100/data (57 monete, fino al 10/11/2026) fanno da seme per i simboli a catena semplice.
Uso: python3 fetch.py [TICKER ...]   (in background: nohup python3 fetch.py > data/raw/fetch.log 2>&1 &)"""
import io, json, sys, time, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
import pandas as pd, requests
import bv_list
HERE = Path(__file__).resolve().parent; RAW = HERE / "data" / "raw"; BN = RAW / "bn"; BN.mkdir(parents=True, exist_ok=True)
SEED = HERE.parents[1] / "w32_top100" / "data"
ARC = "https://data.binance.vision/data"
S = requests.Session(); S.headers["User-Agent"] = "radar-research-script/1.0 (python-requests; academic backtest)"
COLS = ["t", "open", "high", "low", "close", "volume", "ct", "qv", "n", "tbv", "tbqv", "ig"]
LAST = date(2026, 11, 24)                    # ultimo giorno pubblicato nell'archivio giornaliero al 25/11/2026
START = {"spot": "2018-06", "perp": "2019-09", "funding": "2019-09"}
MKT = {"spot": "spot", "perp": "um", "funding": "umfund"}

def get(url):
    for a in range(5):
        try:
            r = S.get(url, timeout=60)
            if r.status_code in (200, 404, 400, 403): return r
        except requests.RequestException: pass
        time.sleep(2 + 4 * a)
    return None

def zcsv(url):
    r = get(url); time.sleep(0.03)
    if r is None or r.status_code != 200: return None
    z = zipfile.ZipFile(io.BytesIO(r.content)); raw = z.read(z.namelist()[0]).decode()
    if not raw.strip(): return None
    hdr = not raw.split("\n", 1)[0][:1].isdigit()
    return pd.read_csv(io.StringIO(raw), header=0 if hdr else None)

def kl(df):
    df = df.iloc[:, :12].copy(); df.columns = COLS
    t = pd.to_numeric(df["t"]); t = t.where(t < 1e14, t // 1000)        # spot dal 2025: microsecondi
    df["date"] = pd.to_datetime(t, unit="ms").dt.normalize()
    return df.set_index("date")[["open", "high", "low", "close", "volume", "tbv"]].astype(float)

def fund(df):
    df = df.copy(); df["date"] = pd.to_datetime(pd.to_numeric(df["calc_time"]), unit="ms").dt.normalize()
    return df.groupby("date")["last_funding_rate"].sum().rename("funding").to_frame()

def url(kind, sym, m=None, d=None):
    if kind == "funding": return f"{ARC}/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{m}.zip"
    root = f"{ARC}/spot" if kind == "spot" else f"{ARC}/futures/um"
    return f"{root}/monthly/klines/{sym}/1d/{sym}-1d-{m}.zip" if m else f"{root}/daily/klines/{sym}/1d/{sym}-1d-{d}.zip"

def rd(p):
    return pd.read_csv(p, index_col=0, parse_dates=True) if p.exists() else None

def seed(sym, kind, seeds):
    """seme dai file w32_top100 (stessa fonte), riportato ai prezzi grezzi del simbolo."""
    t = seeds.get(sym)
    if not t: return None
    x = rd(SEED / f"{t}_{kind}.csv.gz")
    if x is None: return None
    if kind == "perp" and sym.startswith("1000"): x[["open", "high", "low", "close"]] *= 1000
    if kind == "perp" and sym.startswith("1M"): x[["open", "high", "low", "close"]] *= 1e6
    return x

def update(sym, kind, seeds):
    p = BN / f"{sym}_{kind}.csv.gz"; old = rd(p)
    if old is None: old = seed(sym, kind, seeds)
    ms = [m for m in bv_list.months(MKT[kind], sym) if m >= START[kind]]
    have = set() if old is None else set(old.index.to_period("M").astype(str))
    cur = f"{LAST:%Y-%m}"
    if old is not None and len(old):                  # l'ultimo mese del seme può essere parziale: si riscarica
        have.discard(str(old.index[-1].to_period("M")))
    todo = [m for m in ms if m not in have and m < cur]
    fr = [] if old is None else [old]
    parse = fund if kind == "funding" else kl
    for m in todo:
        x = zcsv(url(kind, sym, m))
        if x is not None and len(x): fr.append(parse(x))
    live = bool(ms) and ms[-1] >= f"{(LAST.replace(day=1) - timedelta(1)):%Y-%m}"
    if kind != "funding" and live:                     # mese in corso dai file giornalieri
        got = set() if old is None else set(old.index[old.index >= pd.Timestamp(LAST.replace(day=1))].strftime("%Y-%m-%d"))
        for d in (LAST.replace(day=1) + timedelta(i) for i in range(LAST.day)):
            if f"{d}" in got: continue
            x = zcsv(url(kind, sym, d=d))
            if x is not None and len(x): fr.append(kl(x))
    if not fr: return sym, kind, 0, None
    x = pd.concat(fr).sort_index(); x = x[~x.index.duplicated(keep="last")]
    tmp = p.with_suffix(".tmp"); x.to_csv(tmp, compression="gzip"); tmp.replace(p)
    return sym, kind, len(x), str(x.index[-1].date())

def safe(j, seeds):
    try: return update(j[0], j[1], seeds)
    except Exception as e: return j[0], j[1], "ERRORE", repr(e)[:200]     # una serie rotta non ferma il giro

def jobs(u):
    seeds, out = {}, []
    for r in u.itertuples():
        ch = json.loads(r.chain)
        if len(ch) == 1:                                # seme solo per catene semplici (stesso simbolo di w32_top100)
            c = ch[0]
            if c["spot"]: seeds[c["spot"]] = r.ticker
            if c["perp"]: seeds.setdefault(c["perp"], r.ticker)
        for c in ch:
            if c["spot"]: out.append((c["spot"], "spot"))
            if c["perp"]: out += [(c["perp"], "perp"), (c["perp"], "funding")]
    seen, uniq = set(), []
    for j in out:
        if j not in seen: seen.add(j); uniq.append(j)
    # il seme va per simbolo: spot e perp hanno simboli uguali (es. BTCUSDT); il file giusto lo sceglie `kind`
    return uniq, seeds

if __name__ == "__main__":
    u = pd.read_csv(HERE / "data" / "universe_raw.csv"); u = u[u.escluso.isna() & u.chain.notna()]
    if sys.argv[1:]: u = u[u.ticker.isin(sys.argv[1:])]
    js, seeds = jobs(u); print(len(js), "serie", flush=True)
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(safe, js, [seeds] * len(js)):
            print(*r, flush=True)
