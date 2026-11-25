"""Pagina Scanner (solo informativa): TRX sulla carta con il cancello di BTC e scanner settimanale di W3.2 sulle altcoin.

Blocco 1 · TRX sulla carta (research/w32_asset2/OSSERVAZIONE-TRX.md, regole fissate il 25/11/2026, da non cambiare):
- motore radar.weekly invariato (W3.2, parametri di BTC, rischio 25%, trailing 2,5 ATRw) su TRX con spot e perp TRXUSDT, storia
  dal 2019-09-01 e test dal 2020-06-01 come Q4 di PREREG.md;
- cancello: TRX entra solo se alla stessa domenica W3.2 su BTC (dal 2020-06-01, dati di BTC del giro) è in posizione nello stesso
  verso o vi entra quel giorno; le uscite sono quelle di TRX;
- registro in avanti dal 25/11/2026 in data/trx_carta.json su 10.000 $ di carta. Nessun capitale, nessun ordine, nessun avviso.

Blocco 2 · Scanner settimanale: dopo la chiusura della domenica (UTC) lo stato di W3.2 con i parametri di BTC su ogni crypto dello
studio w32_asset2 con perp USDT-M Binance e perp operabile su Bitget o OKX (radar/scanner_universo.json, statico), più la scheda di
qualità dello studio. Risultato compatto in data/scanner.json; si ricalcola solo a settimana nuova. Lezione 123: scegliere gli asset
con un buon passato non funziona, la pagina non è un segnale.

Dati grezzi (mai in git): .scanner-cache/ (ignorata; nel workflow actions/cache). Fonti: data-api.binance.vision (spot giornaliero
con taker buy, 1 richiesta = 1000 giorni), data.binance.vision (perp USDT-M 1d con taker buy, funding mensile), OKX o Bitget per il
funding del mese non ancora archiviato. Finestra dello scanner: WINDOW_DAYS giorni (lo stato attuale è identico a quello calcolato
con la storia completa dello studio su 127 monete su 127, controllo del 25/11/2026 con finestre di 730, 1000 e 1200 giorni).
Se la cache manca si parte dai file dello studio (research/w32_asset2/crypto/data, già in git) e si scarica solo il resto.
Errori di rete: si tiene l'ultimo risultato con un avviso; il giro orario non si rompe (radar.cli._soft).
"""
from __future__ import annotations

import io
import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from . import weekly as W

ROOT = Path(__file__).resolve().parent.parent
UNIVERSO_FILE = Path(__file__).with_name("scanner_universo.json")
CACHE_DIR = ROOT / ".scanner-cache"
SEED_DIR = ROOT / "research" / "w32_asset2" / "crypto" / "data"
SPOT_API = "https://data-api.binance.vision/api/v3/klines"
ARCHIVE = "https://data.binance.vision/data/futures/um"
OKX_FUND = "https://www.okx.com/api/v5/public/funding-rate-history"
BITGET_FUND = "https://api.bitget.com/api/v2/mix/market/history-fund-rate"
WINDOW_DAYS = 1000          # ≈ 2,7 anni: SMA 40 settimane + z-score 180 giorni + un anno di simulazione (una sola richiesta spot)
THREADS = 12
MAX_ERR = 25                # oltre questi errori di rete il giro dello scanner si ferma e resta l'ultimo risultato
PROVV_FINO_GIORNI = 2       # risultato provvisorio (perp dell'archivio in ritardo): si riprova fino a 2 giorni dopo la domenica
COLS = ["open", "high", "low", "close", "volume", "tbv"]

AVVISO = ("Pagina informativa. Lo studio del 25/11/2026 (lezione 123) mostra che scegliere gli asset con un buon passato non "
          "funziona: non è un segnale per mettere capitale.")

# ---- TRX sulla carta (OSSERVAZIONE-TRX.md)
TRX = {"ticker": "TRX", "spot": "TRXUSDT", "perp": "TRXUSDT", "div": 1, "okx": "TRX-USDT-SWAP", "bitget": "TRXUSDT"}
TRX_SINCE = "2019-09-01"    # storia prezzi come lo studio (crypto/counts.py SINCE): stesse EMA iniziali
TRX_START = "2020-06-01"    # test dal 01/06/2020 (completa_da di TRX) e W3.2 di BTC dal 01/06/2020 (Q4)
TRX_LIVE_FROM = "2026-11-25"
TRX_CAPITALE = 10000.0
NOTA_TRX = "sulla carta: nessun capitale, nessun ordine"
TRX_RIF = {"fin": 87198, "dd": -22.5, "n": 12, "wr": 83, "senza_due_migliori": 17017, "dal": "2020-06-01",
           "nota": "backtest, non ripetibile: due operazioni fanno quasi tutto il risultato"}
TRX_VALUTAZIONI = [("2027-05-31", "6 mesi"), ("2027-11-30", "12 mesi")]
TRX_REGOLE = [
    "Motore W3.2 invariato (SMA 40 settimane, EMA 20/21, flusso perp di TRX, filtro MACD, trailing 2,5 ATR settimanali, uscita su "
    "EMA 21 e distribuzione, rischio 25%), su spot e perp TRXUSDT.",
    "Cancello: si entra solo se alla stessa domenica W3.2 su BTC è in posizione nello stesso verso (o vi entra quel giorno). Le "
    "uscite sono quelle di TRX.",
    "Capitale sulla carta 10.000 $, separato da BTC ed ETH. Regole fissate il 25/11/2026: non si cambiano durante l'osservazione.",
    "Con meno di 3 operazioni chiuse il registro non basta per giudicare. La decisione di passare a una quota reale spetta "
    "all'utente."]


MOTIVO_BREVE = {"trail": "trailing", "stop": "stop iniziale", "ema": "oltre la EMA 21", "dist": "distribuzione"}   # tabella dello scanner


class ReteNonDisponibile(RuntimeError):
    """Troppi errori di rete in un giro: si tiene l'ultimo risultato."""


# ------------------------------------------------------------------ rete
class Rete:
    """Richieste HTTP con pochi tentativi e un tetto di errori per giro (niente attese lunghe se la rete è giù).
    `get(url, params)` restituisce i byte della risposta, None per 404, eccezione per gli altri errori (iniettabile nei test)."""

    def __init__(self, get=None, max_err: int = MAX_ERR, pausa: float = 0.5):
        self._get = get or self._http
        self.max_err, self.pausa = max_err, pausa
        self.err = self.n = self.byte = 0
        self._s = None

    def _http(self, url: str, params: dict | None = None) -> bytes | None:
        if self._s is None:
            self._s = requests.Session()
            self._s.headers["User-Agent"] = "RadarSignal/1.0"
        r = self._s.get(url, params=params, timeout=15)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content

    def get(self, url: str, params: dict | None = None) -> bytes | None:
        last = None
        for i in range(2):
            if self.err >= self.max_err:
                raise ReteNonDisponibile(f"{self.err} errori di rete: giro interrotto" + (f" ({last!r})" if last else ""))
            try:
                self.n += 1
                out = self._get(url, params)
                self.byte += len(out or b"")
                return out
            except Exception as e:  # noqa: BLE001
                last = e
                if i == 0 and self.pausa:
                    time.sleep(self.pausa)
        self.err += 1
        raise last

    def json(self, url: str, params: dict | None = None):
        b = self.get(url, params)
        return None if b is None else json.loads(b)

    def zip_csv(self, url: str) -> pd.DataFrame | None:
        b = self.get(url)
        if b is None:
            return None
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            raw = z.read(z.namelist()[0]).decode()
        head = raw.split("\n", 1)[0]
        return pd.read_csv(io.StringIO(raw), header=0 if any(ch.isalpha() for ch in head) else None)


# ------------------------------------------------------------------ date
def _months(a: date, b: date):
    d = date(a.year, a.month, 1)
    while d <= b:
        yield d
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def _days(a: date, b: date):
    while a <= b:
        yield a
        a += timedelta(days=1)


def _month_end(m: date) -> date:
    return date(m.year + (m.month == 12), m.month % 12 + 1, 1) - timedelta(days=1)


def ultima_domenica(now: datetime | pd.Timestamp) -> date:
    """Ultima domenica la cui candela giornaliera è chiusa (UTC): di lunedì alle 00:30 è la domenica appena finita."""
    ts = pd.Timestamp(now)
    ts = ts.tz_convert("UTC").tz_localize(None) if ts.tzinfo else ts
    y = ts.date() - timedelta(days=1)
    return y - timedelta(days=(y.weekday() - 6) % 7)


# ------------------------------------------------------------------ download per moneta
def _klines(rows) -> pd.DataFrame:
    """Klines (lista dell'API o tabella dell'archivio) -> giornaliero date, open, high, low, close, volume, tbv."""
    df = pd.DataFrame(rows).iloc[:, :12]
    if df.empty:
        return pd.DataFrame(columns=COLS, index=pd.DatetimeIndex([], name="date"))
    df.columns = range(df.shape[1])
    df = df[pd.to_numeric(df[0], errors="coerce").notna()]
    ot = pd.to_numeric(df[0]).astype("int64")
    ot = ot.where(ot < 10**14, ot // 1000)   # file recenti in microsecondi
    out = pd.DataFrame({"open": pd.to_numeric(df[1]).values, "high": pd.to_numeric(df[2]).values,
                        "low": pd.to_numeric(df[3]).values, "close": pd.to_numeric(df[4]).values,
                        "volume": pd.to_numeric(df[5]).values, "tbv": pd.to_numeric(df[9]).values},
                       index=pd.DatetimeIndex(pd.to_datetime(ot.values, unit="ms").normalize(), name="date"))
    return out[~out.index.duplicated(keep="last")].sort_index()


def scarica_spot(net: Rete, sym: str, da: date, oggi: date) -> pd.DataFrame:
    """Spot giornaliero con taker buy dall'API pubblica data-api.binance.vision (1000 giorni a richiesta), solo giorni chiusi."""
    rows, ms = [], int(datetime(da.year, da.month, da.day, tzinfo=timezone.utc).timestamp() * 1000)
    for _ in range(10):   # al massimo 10 pagine (27 anni): nessun ciclo infinito se l'API risponde male
        b = net.json(SPOT_API, {"symbol": sym, "interval": "1d", "startTime": ms, "limit": 1000})
        if not b:
            break
        rows += b
        nxt = int(b[-1][0]) + 86_400_000
        if len(b) < 1000 or nxt <= ms:
            break
        ms = nxt
    out = _klines(rows)
    return out[out.index.date < oggi]


def scarica_perp(net: Rete, sym: str, da: date, oggi: date) -> pd.DataFrame:
    """Perp USDT-M giornaliero con taker buy dall'archivio: mesi chiusi dal file mensile (il mese appena chiuso, se non ancora
    pubblicato, dai file giornalieri), mese in corso dai file giornalieri fino a ieri (quelli non ancora pubblicati mancano)."""
    mese = date(oggi.year, oggi.month, 1)
    prev = date(mese.year - (mese.month == 1), (mese.month - 2) % 12 + 1, 1)
    frames, giorni = [], list(_days(max(da, mese), oggi - timedelta(days=1)))
    for m in [m for m in _months(da, oggi) if m < mese]:
        df = net.zip_csv(f"{ARCHIVE}/monthly/klines/{sym}/1d/{sym}-1d-{m:%Y-%m}.zip")
        if df is not None:
            frames.append(_klines(df))
        elif m >= prev:   # mese appena chiuso non ancora archiviato
            giorni += list(_days(max(m, da), _month_end(m)))
    for d in giorni:
        df = net.zip_csv(f"{ARCHIVE}/daily/klines/{sym}/1d/{sym}-1d-{d:%Y-%m-%d}.zip")
        if df is not None:
            frames.append(_klines(df))
    out = pd.concat(frames) if frames else _klines([])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out[(out.index.date >= da) & (out.index.date < oggi)]


def scarica_funding(net: Rete, c: dict, da: date, oggi: date) -> pd.DataFrame:
    """Funding giornaliero (somma): archivio mensile Binance per i mesi chiusi; i giorni dopo l'ultimo mese archiviato da OKX
    (o da Bitget se la moneta non ha il perp OKX). Colonna source = binance / okx / bitget."""
    sym, mese, frames = c["perp"], date(oggi.year, oggi.month, 1), []
    for m in [m for m in _months(da, oggi) if m < mese]:
        df = net.zip_csv(f"{ARCHIVE}/monthly/fundingRate/{sym}/{sym}-fundingRate-{m:%Y-%m}.zip")
        if df is None or not len(df):
            continue
        if "calc_time" not in df:
            df = df.set_axis(["calc_time", "interval_h", "last_funding_rate"][: df.shape[1]], axis=1)
        d = pd.to_datetime(pd.to_numeric(df["calc_time"]), unit="ms").dt.normalize()
        frames.append(pd.to_numeric(df["last_funding_rate"]).groupby(d.values).sum().to_frame("funding").assign(source="binance"))
    out = pd.concat(frames) if frames else pd.DataFrame(columns=["funding", "source"])
    last = out.index.max() if len(out) else pd.Timestamp(da) - pd.Timedelta(days=1)
    rec = None
    if c.get("okx"):
        j = net.json(OKX_FUND, {"instId": c["okx"], "limit": 100}) or {}
        x = pd.DataFrame(j.get("data") or [])
        if len(x):
            d = pd.to_datetime(pd.to_numeric(x["fundingTime"]), unit="ms").dt.normalize()
            rec = pd.to_numeric(x["realizedRate"]).groupby(d.values).sum().to_frame("funding").assign(source="okx")
    elif c.get("bitget"):
        j = net.json(BITGET_FUND, {"symbol": c["bitget"], "productType": "usdt-futures", "pageSize": 100}) or {}
        x = pd.DataFrame(j.get("data") or [])
        if len(x):
            d = pd.to_datetime(pd.to_numeric(x["fundingTime"]), unit="ms").dt.normalize()
            rec = pd.to_numeric(x["fundingRate"]).groupby(d.values).sum().to_frame("funding").assign(source="bitget")
    if rec is not None:
        rec = rec[(rec.index > last) & (rec.index.date < oggi)]
        out = pd.concat([out, rec]) if len(out) else rec
    out.index = pd.DatetimeIndex(out.index, name="date")
    return out.sort_index()


# ------------------------------------------------------------------ cache
def _rd(p: Path) -> pd.DataFrame | None:
    try:
        return pd.read_csv(p, index_col=0, parse_dates=True) if p.exists() else None
    except Exception:  # noqa: BLE001   cache illeggibile = assente
        return None


def _merge(old: pd.DataFrame | None, new: pd.DataFrame | None) -> pd.DataFrame | None:
    if old is None or not len(old):
        return new
    if new is None or not len(new):
        return old
    out = pd.concat([old, new])
    return out[~out.index.duplicated(keep="last")].sort_index()


def _seed(t: str, kind: str, seed_dir: Path | None) -> pd.DataFrame | None:
    """File dello studio (già in git, stesso formato e stessa scala dei prezzi): punto di partenza se la cache manca."""
    if seed_dir is None:
        return None
    x = _rd(Path(seed_dir) / f"{t}_{kind}.csv.gz")
    if x is not None and kind == "funding" and "source" not in x:
        x = x.assign(source="binance")
        x.loc[x.index >= pd.Timestamp("2026-11-01"), "source"] = "okx"   # novembre 2026 nello studio = OKX
    return x


def cache_moneta(c: dict, cache: Path, da: date, seed_dir: Path | None = SEED_DIR) -> dict:
    """Solo la cache su disco (o i file dello studio), senza rete."""
    lim = pd.Timestamp(max(da, date.fromisoformat(c["da"])) if c.get("da") else da)
    out = {}
    for kind in ("spot", "perp", "funding"):
        x = _rd(Path(cache) / f"{c['ticker']}_{kind}.csv.gz")
        x = _seed(c["ticker"], kind, seed_dir) if x is None else x
        out[kind] = None if x is None or (kind == "spot" and not c.get("spot")) else x[x.index >= lim]
    return out | {"errore": None}


def aggiorna_moneta(net: Rete, c: dict, cache: Path, oggi: date, da: date, seed_dir: Path | None = SEED_DIR) -> dict:
    """Serie spot, perp e funding di una moneta dalla cache, scaricando solo i giorni mancanti. Prezzi perp divisi per c["div"]
    e volumi moltiplicati
    (1000PEPEUSDT -> unità di PEPE), come i file dello studio. Ritorna {"spot", "perp", "funding", "errore"}: con un errore si usa la cache."""
    cache.mkdir(parents=True, exist_ok=True)
    t, out, err = c["ticker"], {}, None
    lim = pd.Timestamp(max(da, date.fromisoformat(c["da"])) if c.get("da") else da)
    for kind in ("spot", "perp", "funding"):
        p = cache / f"{t}_{kind}.csv.gz"
        old = _rd(p)
        if old is None:
            old = _seed(t, kind, seed_dir)
        if old is not None:
            old = old[old.index >= lim]
        sym = c.get("spot") if kind == "spot" else c["perp"]
        if not sym:
            out[kind] = None
            continue
        try:
            if kind == "spot":
                a = (old.index.max().date() - timedelta(days=2)) if old is not None and len(old) else lim.date()
                new = scarica_spot(net, sym, max(a, lim.date()), oggi) if a < oggi - timedelta(days=1) else None
            elif kind == "perp":
                a = (old.index.max().date() - timedelta(days=10)) if old is not None and len(old) else lim.date()
                new = scarica_perp(net, sym, max(a, lim.date()), oggi) if a < oggi - timedelta(days=1) else None
                if new is not None and len(new) and c.get("div", 1) != 1:   # come lo studio (crypto/build.py scale): stessa scala dei file seme
                    new[["open", "high", "low", "close"]] = new[["open", "high", "low", "close"]] / c["div"]
                    new[["volume", "tbv"]] = new[["volume", "tbv"]] * c["div"]
            else:
                ob = old[old["source"] == "binance"] if old is not None and "source" in old else old
                a = (ob.index.max().date() - timedelta(days=45)) if ob is not None and len(ob) else lim.date()
                new = scarica_funding(net, c, max(a, lim.date()), oggi)
                if old is not None and "source" in old and new is not None and len(new):
                    old = old[(old["source"] == "binance") | (old.index < new.index.min())]   # provvisori sostituiti
        except ReteNonDisponibile:
            raise
        except Exception as e:  # noqa: BLE001
            err = f"{kind}: {type(e).__name__}: {str(e)[:80]}"
            new = None
        x = _merge(old, new)
        if x is not None and len(x):
            x = x[x.index >= lim]
            if new is not None and len(new):
                x.round(10).to_csv(p, compression={"method": "gzip", "mtime": 0})   # mtime fisso: stessa impronta se i dati non cambiano
        out[kind] = x
    out["errore"] = err
    return out


# ------------------------------------------------------------------ feature (= research/w32_asset2/crypto/counts.py feats)
def _z(s: pd.Series, n: int) -> pd.Series:
    return (s - s.rolling(n, min_periods=n // 2).mean()) / s.rolling(n, min_periods=n // 2).std()


def feats(spot: pd.DataFrame | None, perp: pd.DataFrame | None, fund: pd.DataFrame | None, fine: date | None = None) -> pd.DataFrame | None:
    """Giornaliero per radar.weekly: prezzi dallo spot (dal perp dove manca), pf14z dal perp con taker buy, funding (ffill 3 giorni).
    Come lo studio; in più dal vivo la fine è l'ultimo giorno dei prezzi (il perp dell'archivio arriva un giorno dopo: il flusso
    usato dalla domenica arriva fino al sabato). Un perp fermo da oltre 7 giorni (delistato) chiude la serie come nello studio.
    Giorni a volume zero tolti (prezzi congelati dopo un delisting)."""
    sp = None if spot is None or not len(spot) else spot[spot["volume"] > 0]
    pp = None if perp is None or not len(perp) else perp[perp["volume"] > 0]
    if sp is None and pp is None:
        return None
    end = max(x.index[-1] for x in (sp, pp) if x is not None)
    if pp is not None and end - pp.index[-1] > pd.Timedelta(days=7):
        end = pp.index[-1]
    if fine is not None:
        end = min(end, pd.Timestamp(fine))
    idx = pd.date_range(min(x.index[0] for x in (sp, pp) if x is not None), end)
    px = pd.DataFrame(index=idx, columns=["open", "high", "low", "close"], dtype=float)
    if pp is not None:
        px = pp[["open", "high", "low", "close"]].reindex(idx)
    if sp is not None:
        px = sp[["open", "high", "low", "close"]].reindex(idx).combine_first(px)
    f = px.copy()
    if pp is not None:
        q = pp.reindex(idx)
        d = 2 * q["tbv"] - q["volume"]
        f["pf14z"] = _z(d.rolling(14).sum() / q["volume"].rolling(14).sum(), 180)
    else:
        f["pf14z"] = np.nan
    fu = fund["funding"] if fund is not None and len(fund) else pd.Series(dtype=float)
    f["funding"] = pd.to_numeric(fu, errors="coerce").reindex(idx).ffill(limit=3)
    return f[f["close"].notna()]


# ------------------------------------------------------------------ W3.2: stato, cancello
def _trades(o: dict) -> list[dict]:
    return o["trades"] + ([dict(o["open"])] if o["open"] else [])


def cancello(f_btc: pd.DataFrame, start: str = TRX_START) -> pd.Series:
    """Cancello di Q4 alle domeniche: +1/-1 se W3.2 su BTC (dal `start`) è in posizione (entrata ≤ domenica < uscita: un'uscita
    decisa quella domenica conta ancora) o vi entra quel giorno (segnale della domenica); 0 altrimenti."""
    f = f_btc[f_btc["close"].notna()]
    o = W.simulate(f, start=start)
    sun = f.index[f.index.dayofweek == 6]
    g = pd.Series(0, index=sun)
    for t in _trades(o):
        a, sd = pd.Timestamp(t["entry"]), (1 if t["side"] == "long" else -1)
        b = pd.Timestamp(t["exit"]) if t.get("exit") else sun[-1] + pd.Timedelta(days=1)
        g[(g.index >= a) & (g.index < b)] = sd
        if pd.Timestamp(t["signal"]) in g.index:
            g[pd.Timestamp(t["signal"])] = sd
    if o["pending"] and o["pending"]["kind"] == "enter":
        g[pd.Timestamp(o["pending"]["date"])] = int(o["pending"]["arg"])
    return g


def simula_con_cancello(f: pd.DataFrame, gate: pd.Series, start: str = TRX_START) -> dict:
    """radar.weekly.simulate invariato con gli ingressi filtrati dal cancello (come research/w32_asset2/lib.py csim): le candele
    settimanali sono quelle di weekly_bars, con long/short veri solo se il cancello è nello stesso verso. weekly.py non cambia: la
    funzione weekly_bars del modulo si sostituisce solo per la durata della chiamata."""
    orig = W.weekly_bars

    def wb(ff):
        w = orig(ff)
        g = gate.reindex(w.index).fillna(0)
        w["long"] = w["long"] & (g > 0)
        w["short"] = w["short"] & (g < 0)
        return w
    W.weekly_bars = wb
    try:
        return W.simulate(f, start=start)
    finally:
        W.weekly_bars = orig


def condizioni(w: pd.DataFrame) -> dict:
    """Condizioni di W3.2 all'ultima candela settimanale chiusa (stesse formule di weekly_bars/evaluate)."""
    wk = w.iloc[-1]
    e20_up = bool(wk["ema20"] > w["ema20"].iloc[-2]) if len(w) > 1 else None
    sma_dn = bool(wk["sma"] < w["sma"].iloc[-5]) if len(w) > 4 else None
    up = bool(wk["close"] > wk["sma"]) and bool(e20_up)
    dn = bool(wk["close"] < wk["sma"]) and bool(sma_dn) and e20_up is False
    fl = None if pd.isna(wk["flow"]) else round(float(wk["flow"]), 2)
    return {"px_sma": 1 if wk["close"] > wk["sma"] else -1, "ema20": 1 if e20_up else -1, "sma_dn": sma_dn,
            "ema21": 1 if wk["close"] > wk["ema21"] else -1, "flow": fl, "f1": bool(wk["f1_ok"]),
            "macd": bool(wk["macd"] > wk["macd_sig"] and wk["macd"] > 0), "eta": int(wk["trend_age"]),
            "regime": "long" if up else "short" if dn else "neutro", "c_long": bool(wk["long"]), "c_short": bool(wk["short"]),
            "close": float(wk["close"]), "sma": float(wk["sma"]), "ema21_v": float(wk["ema21"])}


def _exit_px(f: pd.DataFrame, t: dict) -> float | None:
    """Prezzo d'uscita come in simulate, senza l'arrotondamento a 0,01 (inutile sotto 1 $): apertura del giorno per EMA 21 e
    distribuzione, livello dello stop (o apertura se peggiore) per stop e trailing; slittamento 0,1% incluso."""
    if not t.get("exit"):
        return None
    sg, o = (1 if t["side"] == "long" else -1), float(f.loc[pd.Timestamp(t["exit"]), "open"])
    if t.get("reason") in ("stop", "trail"):
        o = min(o, t["stop"]) if sg > 0 else max(o, t["stop"])
    return o * (1 - W.SLIP * sg)


def _entry_px(f: pd.DataFrame, t: dict) -> float:
    sg = 1 if t["side"] == "long" else -1
    return float(f.loc[pd.Timestamp(t["entry"]), "open"]) * (1 + W.SLIP * sg)


def _r(x, n=5):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def _sett(entry: str, dom: date) -> int:
    """Chiusure settimanali dall'ingresso (lunedì) alla domenica `dom` compresa."""
    return max(0, ((dom - date.fromisoformat(entry)).days + 1) // 7)


# ------------------------------------------------------------------ scanner: una moneta
def stato_moneta(f: pd.DataFrame | None, dom: date) -> dict:
    """Stato W3.2 (parametri di BTC) alla chiusura della domenica `dom`, con le decisioni di quella domenica già applicate:
    lato = posizione dal lunedì; evento = ingresso (segnale della domenica), uscita (decisa la domenica o trailing in settimana)."""
    if f is None or not len(f):
        return {"lato": None, "nd": "dati non disponibili"}
    f = f[f.index <= pd.Timestamp(dom)]
    if not len(f) or f.index[-1] < pd.Timestamp(dom):
        return {"lato": None, "nd": f"dati fermi al {f.index[-1].date() if len(f) else '–'}"}
    w = W.weekly_bars(f)
    ok = w[w["sma"].notna() & w["flow"].notna()]
    if ok.empty or ok.index[0] >= pd.Timestamp(dom):
        return {"lato": None, "nd": "storia breve: servono 40 settimane e il flusso perp"}
    with np.errstate(divide="ignore", invalid="ignore"):   # prezzi sotto 0,005 $: entry_px di simulate arrotondato a 0 (campo move, non usato)
        o = W.simulate(f, start=str((ok.index[0] + pd.Timedelta(days=1)).date()))
    c = condizioni(w)
    c["dsma"] = round((c.pop("close") / c.pop("sma") - 1) * 100, 1)
    c.pop("ema21_v")
    out = {"lato": "flat", "evento": None, "cond": c, "ult": _r(float(f["close"].iloc[-1]), 6)}
    op, pe = o["open"], o["pending"]
    if op:
        sg = 1 if op["side"] == "long" else -1
        px0 = _entry_px(f, op)
        out.update(lato=op["side"], ing=op["entry"], sig=op["signal"], sett=_sett(op["entry"], dom), px_in=_r(px0, 6),
                   trail=_r(op["trail"], 6), mv=round((float(f["close"].iloc[-1]) / px0 - 1) * sg * 100, 1))
        if pe and pe["kind"] == "exit":
            out.update(lato="flat", evento="uscita", motivo=MOTIVO_BREVE.get(pe["arg"], pe["arg"]), da=op["side"])
    elif pe and pe["kind"] == "enter":
        out.update(lato="long" if pe["arg"] > 0 else "short", evento="ingresso", sig=pe["date"], sett=0)
    last = o["trades"][-1] if o["trades"] else None
    if out["evento"] is None and last and last["reason"] in ("trail", "stop") and pd.Timestamp(last["exit"]) > pd.Timestamp(dom) - pd.Timedelta(days=7):
        out.update(evento="uscita", motivo=MOTIVO_BREVE.get(last["reason"], last["reason"]), da=last["side"], uscita=last["exit"])
    return out


def _verso_btc(lato: str | None, btc: str | None) -> str | None:
    if lato in (None, "flat") or btc is None:
        return None
    return "BTC flat" if btc == "flat" else "stesso" if lato == btc else "opposto"


# ------------------------------------------------------------------ scanner: giro settimanale
def carica_universo(path: Path = UNIVERSO_FILE) -> list[dict]:
    return json.loads(Path(path).read_text())["monete"]


def _load(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except Exception:  # noqa: BLE001
        return None


def calcola_scanner(universo: list[dict], net: Rete, now: datetime, cache: Path = CACHE_DIR, seed_dir: Path | None = SEED_DIR,
                    threads: int = THREADS) -> dict:
    """Scarica (solo i giorni mancanti) e calcola lo stato di tutte le monete alla domenica appena chiusa."""
    t0 = time.time()
    oggi = pd.Timestamp(now).date()
    dom = ultima_domenica(now)
    da = oggi - timedelta(days=WINDOW_DAYS)

    def uno(c):
        s = aggiorna_moneta(net, c, cache, oggi, da, seed_dir)
        return c, s, feats(s["spot"], s["perp"], s["funding"])
    with ThreadPoolExecutor(threads) as ex:
        res = list(ex.map(uno, universo))
    t_dl = time.time() - t0
    rows, errori, perp_ok = [], [], 0
    for c, s, f in res:
        st = stato_moneta(f, dom)
        if s["errore"]:
            errori.append(c["ticker"])
        pp = s.get("perp")
        if pp is not None and len(pp) and pp.index[-1] >= pd.Timestamp(dom) - pd.Timedelta(days=1):
            perp_ok += 1
        rows.append({"t": c["ticker"], "n": c.get("nome"), "cl": c.get("classe"), "rk": c.get("rank_oggi"),
                     "bg": bool(c.get("bitget")), "ok": bool(c.get("okx")), "q": c.get("scheda"), **st,
                     **({"err": s["errore"]} if s["errore"] else {})})
    if len(errori) > len(rows) / 2:   # rete in gran parte giù: meglio l'ultimo risultato completo che uno fatto di cache vecchie
        raise ReteNonDisponibile(f"dati non aggiornati per {len(errori)} monete su {len(rows)}")
    btc = next((r["lato"] for r in rows if r["t"] == "BTC"), None)
    for r in rows:
        r["btc"] = _verso_btc(r["lato"], btc) if r["t"] != "BTC" else None
    n_ok = sum(r["lato"] is not None for r in rows)
    cnt = {k: sum(r["lato"] == k for r in rows) for k in ("long", "short", "flat")} | {"nd": len(rows) - n_ok}
    provv = perp_ok < 0.9 * max(n_ok, 1)
    return {"settimana": str(dom), "calcolato": pd.Timestamp(now).isoformat(timespec="minutes"), "n": len(rows), "conteggi": cnt,
            "nuovi": [r["t"] for r in rows if r.get("evento") == "ingresso"],
            "uscite": [r["t"] for r in rows if r.get("evento") == "uscita"], "btc": btc, "provvisorio": provv,
            "finestra_giorni": WINDOW_DAYS, "righe": rows, "avviso": AVVISO,
            "dati": {"ritardo": False, "nota": ("Flusso perp dell'archivio non ancora completo per tutte le monete: risultato "
                                                "provvisorio, si ricalcola al prossimo giro.") if provv else None,
                     "errori": errori, "richieste": net.n, "mb": round(net.byte / 1e6, 2),
                     "secondi_download": round(t_dl, 1), "secondi": round(time.time() - t0, 1)}}


def giro(f_btc: pd.DataFrame | None, data_dir: Path, now: datetime | None = None, net: Rete | None = None,
         cache: Path = CACHE_DIR, universo: list[dict] | None = None, seed_dir: Path | None = SEED_DIR) -> dict:
    """Un giro orario: se c'è una settimana nuova completa (o l'ultimo risultato era provvisorio, entro 2 giorni dalla domenica)
    ricalcola e salva data/scanner.json; altrimenti restituisce il risultato salvato. Errori di rete: ultimo risultato + avviso.
    f_btc non serve allo scanner (BTC è una riga come le altre): resta per simmetria con trx_giro."""
    now = now or datetime.now(timezone.utc)
    data_dir = Path(data_dir)
    path = data_dir / "scanner.json"
    prev = _load(path)
    dom = ultima_domenica(now)
    if prev and prev.get("settimana") == str(dom) and (not prev.get("provvisorio")
                                                        or pd.Timestamp(now).date() > dom + timedelta(days=PROVV_FINO_GIORNI)):
        return prev
    if prev and (prev.get("settimana") or "") > str(dom):
        return prev
    try:
        out = calcola_scanner(universo if universo is not None else carica_universo(), net or Rete(), now, cache, seed_dir)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] scanner: aggiornamento non riuscito ({e!r}): resta l'ultimo risultato")
        base = prev or {"settimana": None, "righe": [], "conteggi": {}, "nuovi": [], "uscite": [], "avviso": AVVISO}
        nota = (f"Aggiornamento della settimana del {dom:%d/%m/%Y} non riuscito ({type(e).__name__}): "
                + (f"risultato della settimana del {date.fromisoformat(prev['settimana']):%d/%m/%Y}." if prev and prev.get("settimana")
                   else "nessun risultato salvato."))
        return dict(base, dati=dict(base.get("dati") or {}, ritardo=True, nota=nota, errore=f"{type(e).__name__}: {str(e)[:120]}"))
    data_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"), default=str))
    d = out["dati"]
    print(f"[radar] scanner {out['settimana']}: {out['conteggi']} · nuovi {out['nuovi']} · {d['richieste']} richieste, "
          f"{d['mb']} MB, download {d['secondi_download']} s, totale {d['secondi']} s" + (" · PROVVISORIO" if out["provvisorio"] else ""))
    return out


def ultimo(data_dir: Path) -> dict | None:
    """Ultimo risultato salvato (se il giro dello scanner si è rotto): con l'avviso di dati non aggiornati."""
    prev = _load(Path(data_dir) / "scanner.json")
    if prev:
        prev["dati"] = dict(prev.get("dati") or {}, ritardo=True, nota="Scanner non calcolato in questo giro: ultimo risultato salvato.")
    return prev


# ------------------------------------------------------------------ TRX sulla carta
def _reg_vuoto() -> dict:
    return {"inizio": TRX_LIVE_FROM, "capitale": TRX_CAPITALE, "operazioni": [], "stato": None, "dati_fino": None, "aggiornato": None}


def aggiorna_registro(reg: dict, o: dict, f: pd.DataFrame, gate: pd.Series, now: datetime) -> dict:
    """Registro in avanti: le operazioni simulate con ingresso dal 25/11/2026 entrano una volta; una chiusa non si riscrive più,
    una aperta si aggiorna (trailing, ultimo prezzo, risultato) finché si chiude. Il passato prima del 25/11 non entra."""
    reg = json.loads(json.dumps(reg)) if reg else _reg_vuoto()
    ops = reg.setdefault("operazioni", [])
    viste = set()
    for t in _trades(o):
        if t["entry"] < reg["inizio"]:
            continue
        k = f"{t['side']}|{t['entry']}"
        viste.add(k)
        r = next((x for x in ops if x["chiave"] == k), None)
        if r and r["stato"] == "chiusa":
            continue
        if r is None:
            r = {"chiave": k, "verso": t["side"], "segnale": t["signal"], "ingresso": t["entry"], "prezzo_in": _r(_entry_px(f, t)),
                 "esposizione": t["expo"], "mercato": t["market"], "btc_al_segnale": int(gate.get(pd.Timestamp(t["signal"]), 0))}
            ops.append(r)
        if t.get("exit"):
            r.update(stato="chiusa", uscita=t["exit"], prezzo_out=_r(_exit_px(f, t)), motivo=W.REASONS.get(t["reason"], t["reason"]),
                     pnl_pct=round(t["pnl"] * 100, 2))
            r.pop("trailing", None)
            r.pop("ultimo", None)
        else:
            op = o["open"]
            r.update(stato="aperta", trailing=_r(op["trail"]), ultimo=_r(op["last"]), pnl_pct=round(op["pnl"] * 100, 2),
                     motivo="posizione aperta")
    for r in ops:   # un'operazione aperta che il calcolo non vede più (dati riscritti): resta, con la nota
        if r["stato"] == "aperta" and r["chiave"] not in viste:
            r["nota"] = f"non più presente nel calcolo del {pd.Timestamp(now).date()} (dati riscritti): da controllare"
    cap = reg.get("capitale", TRX_CAPITALE)
    for r in ops:
        r["capitale_prima"] = round(cap, 2)
        cap_dopo = cap * (1 + r["pnl_pct"] / 100)
        r["esito_usd"] = round(cap_dopo - cap, 2)
        if r["stato"] == "chiusa":
            cap = cap_dopo
    aperta = next((r for r in ops if r["stato"] == "aperta"), None)
    reg["capitale_ora"] = round(cap + (aperta["esito_usd"] if aperta else 0.0), 2)
    reg["capitale_chiuse"] = round(cap, 2)
    return reg


def stato_trx(o: dict, f: pd.DataFrame, gate: pd.Series) -> dict:
    """Stato attuale di TRX alla data dei dati: posizione, condizioni proprie (senza cancello) all'ultima domenica, cancello di BTC."""
    w = W.weekly_bars(f)
    c = condizioni(w)
    dom = w.index[-1]
    g = int(gate.get(dom, 0))
    btc = "long" if g > 0 else "short" if g < 0 else "flat"
    s = {"data": str(f.index[-1].date()), "domenica": str(dom.date()), "prezzo": _r(float(f["close"].iloc[-1])), "cond": c,
         "btc": btc, "lato": "flat", "pending": None}
    if o["open"]:
        op = o["open"]
        s.update(lato=op["side"], ingresso=op["entry"], prezzo_in=_r(_entry_px(f, op)), trailing=_r(op["trail"]),
                 pnl_pct=round(op["pnl"] * 100, 2))
    if o["pending"]:
        pe = o["pending"]
        s["pending"] = {"tipo": pe["kind"], "verso": ("long" if pe["arg"] > 0 else "short") if pe["kind"] == "enter" else None,
                        "motivo": W.REASONS.get(pe["arg"]) if pe["kind"] == "exit" else None, "segnale": pe["date"]}
    if s["lato"] == "flat" and not s["pending"]:
        if c["c_long"] or c["c_short"]:
            v = "long" if c["c_long"] else "short"
            s["perche"] = f"condizione {v} di TRX vera, ma W3.2 su BTC è {btc}: cancello chiuso"
        else:
            s["perche"] = f"nessuna condizione d'ingresso di TRX (regime {c['regime']})"
    return s


def build_trx(reg: dict, now: datetime, dati: dict | None = None) -> dict:
    oggi = pd.Timestamp(now).date()
    chiuse = [r for r in reg.get("operazioni", []) if r["stato"] == "chiusa"]
    cap0 = reg.get("capitale", TRX_CAPITALE)
    capn = reg.get("capitale_ora", cap0)
    return {"nota": NOTA_TRX, "inizio": reg.get("inizio", TRX_LIVE_FROM), "capitale": cap0, "capitale_ora": capn,
            "risultato_usd": round(capn - cap0, 2), "risultato_pct": round((capn / cap0 - 1) * 100, 2),
            "operazioni": reg.get("operazioni", []), "chiuse": len(chiuse), "stato": reg.get("stato"),
            "dati_fino": reg.get("dati_fino"), "aggiornato": reg.get("aggiornato"), "rif": TRX_RIF, "regole": TRX_REGOLE,
            "valutazioni": [{"data": d, "cosa": k, "giorni": (date.fromisoformat(d) - oggi).days} for d, k in TRX_VALUTAZIONI],
            "dati": dati or {"ritardo": False, "nota": None}}


def trx_giro(f_btc: pd.DataFrame | None, data_dir: Path, now: datetime | None = None, net: Rete | None = None,
             cache: Path = CACHE_DIR, seed_dir: Path | None = SEED_DIR) -> dict:
    """Un giro orario di TRX sulla carta: ricalcolo solo quando c'è un giorno chiuso nuovo (dati TRX e BTC), altrimenti il
    registro salvato. Errore di rete: cache su disco se c'è, altrimenti l'ultimo registro con l'avviso. Mai ordini né avvisi."""
    now = now or datetime.now(timezone.utc)
    data_dir = Path(data_dir)
    path = data_dir / "trx_carta.json"
    reg = _load(path) or _reg_vuoto()
    oggi = pd.Timestamp(now).date()
    ieri = oggi - timedelta(days=1)
    btc_last = f_btc.index[-1].date() if f_btc is not None and len(f_btc) else None
    if f_btc is None or btc_last is None:
        return build_trx(reg, now, {"ritardo": True, "nota": "Dati di BTC non disponibili in questo giro: registro non aggiornato."})
    if reg.get("dati_fino") and reg["dati_fino"] >= str(min(ieri, btc_last)) and reg.get("stato"):
        return build_trx(reg, now)
    net = net or Rete()
    dati = {"ritardo": False, "nota": None}
    try:
        s = aggiorna_moneta(net, TRX, cache, oggi, date.fromisoformat(TRX_SINCE), seed_dir)
    except ReteNonDisponibile as e:   # rete giù: si calcola sulla cache (o sui file dello studio), il registro resta coerente
        s = dict(cache_moneta(TRX, cache, date.fromisoformat(TRX_SINCE), seed_dir), errore=f"rete: {str(e)[:80]}")
    if s["errore"]:
        dati = {"ritardo": True, "nota": f"Dati di TRX non aggiornati ({s['errore']}): calcolo sull'ultima cache."}
    f = feats(s["spot"], s["perp"], s["funding"], fine=btc_last)
    if f is None or not len(f):
        return build_trx(reg, now, {"ritardo": True, "nota": "Dati di TRX non disponibili: registro non aggiornato."})
    gate = cancello(f_btc)
    o = simula_con_cancello(f, gate)
    reg = aggiorna_registro(reg, o, f, gate, now)
    reg["stato"] = stato_trx(o, f, gate)
    reg["dati_fino"] = str(f.index[-1].date())
    reg["aggiornato"] = pd.Timestamp(now).isoformat(timespec="minutes")
    data_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg, ensure_ascii=False, indent=1, default=str))
    st = reg["stato"]
    print(f"[radar] TRX sulla carta: {st['lato']} al {reg['dati_fino']} · BTC {st['btc']} · capitale {reg['capitale_ora']} $"
          + (f" · in sospeso {st['pending']}" if st["pending"] else ""))
    return build_trx(reg, now, dati)


# ------------------------------------------------------------------ universo (file statico, si rifà solo a mano)
def build_universo(research: Path = ROOT / "research" / "w32_asset2") -> dict:
    """radar/scanner_universo.json dai file dello studio: monete valutabili e brevi con perp USDT-M Binance attivo e perp su Bitget
    o OKX (universe.csv, ops.csv), simboli Binance correnti (sources.csv), scheda di qualità (risultati_crypto.csv = Q1, W3.2 da
    sola; risultati_q4.csv = con il cancello di BTC). `python -m radar.scanner universo` lo riscrive."""
    import re
    cr = research / "crypto"
    u = pd.read_csv(cr / "universe.csv")
    src = pd.read_csv(cr / "data" / "sources.csv").set_index("ticker")
    ops = pd.read_csv(cr / "data" / "ops.csv").set_index("ticker")
    q1 = pd.read_csv(research / "risultati_crypto.csv").set_index("ticker")
    q4 = pd.read_csv(research / "risultati_q4.csv").set_index("ticker")
    cut = {"LIT": "2025-12-23", "SUN": "2021-06-18", "PUMP": "2025-07-10"}   # = crypto/universe.py CUT_FROM

    def seg(txt, kind):
        out = [re.match(rf"binance {kind} (\S+) (\d{{4}}-\d\d-\d\d)\.\.(\d{{4}}-\d\d-\d\d)", p.strip()) for p in str(txt).split("|")]
        return [m.groups() for m in out if m and m.group(3) >= "2026-11-01"]   # segmento ancora attivo al 25/11/2026

    def num(x, n=1):
        return None if pd.isna(x) else round(float(x), n)

    def scheda(d, t):
        if t not in d.index:
            return None
        r = d.loc[t]
        if pd.isna(r["fin"]) or pd.isna(r["n"]):
            return None
        c = [bool(r[k]) for k in ("c1", "c2", "c3", "c4", "c5")]
        return {"c": sum(c), "f": "" if all(c) else ",".join(str(i + 1) for i, v in enumerate(c) if not v), "fin": num(r["fin"], 0),
                "dd": num(r["dd"]), "wr": num(r["wr"], 0), "n": None if pd.isna(r["n"]) else int(r["n"]), "cd": num(r["cd"], 2),
                "bh": num(r["bh_cd"], 2), "p": num(r["p"], 4), "da": r["inizio"]}
    rows = []
    sel = u[((u.bitget_perp == True) | (u.okx_perp == True)) & u.classe.isin(["valutabile", "breve"])]  # noqa: E712
    for r in sel.itertuples():
        pp, sp = seg(src.loc[r.ticker, "perp"], "perp"), seg(src.loc[r.ticker, "spot"], "spot")
        if not pp:
            continue
        perp = pp[-1][0]
        o = ops.loc[r.ticker] if r.ticker in ops.index else None
        s1, s4 = scheda(q1, r.ticker), scheda(q4, r.ticker)
        if s4 is not None:
            s4["ok"] = bool(q4.loc[r.ticker, "passa_davvero"])
        rows.append({"ticker": r.ticker, "nome": r.nome, "rank_oggi": None if pd.isna(r.rank_oggi) else int(r.rank_oggi),
                     "classe": r.classe, "spot": sp[-1][0] if sp else None, "perp": perp,
                     "div": 1000000 if perp.startswith(("1M", "1000000")) else 1000 if perp.startswith("1000") else 1,
                     "okx": (o["okx_perp_simbolo"] if o is not None and bool(o["okx_perp"]) else None),
                     "bitget": (o["bitget_perp_simbolo"] if o is not None and bool(o["bitget_perp"]) else None),
                     "da": cut.get(r.ticker), "scheda": {"q1": s1, "q4": s4}})
    rows.sort(key=lambda x: (x["rank_oggi"] is None, x["rank_oggi"] or 0, x["ticker"]))
    return {"fonte": "research/w32_asset2 (25/11/2026): universe.csv, data/sources.csv, data/ops.csv, risultati_crypto.csv, risultati_q4.csv",
            "criteri": {"1": "CAGR/DD > buy & hold", "2": "DD ≥ −35%", "3": "WR ≥ 60%", "4": "IS e OOS positivi", "5": "≥ 8 trade"},
            "n": len(rows), "monete": rows}


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["universo"]:
        u = build_universo()
        UNIVERSO_FILE.write_text(json.dumps(u, ensure_ascii=False, indent=0, default=str))
        print(f"{UNIVERSO_FILE}: {u['n']} monete")
    else:
        print("uso: python -m radar.scanner universo")
