"""Pagina Scanner (solo informativa): TRX sulla carta con il cancello di BTC e scanner settimanale di W3.2 sulle altcoin.

Blocco 1 · TRX sulla carta (research/w32_asset2/OSSERVAZIONE-TRX.md, regole fissate il 25/11/2026, da non cambiare):
- motore radar.weekly invariato (W3.2, parametri di BTC, rischio 25%, trailing 2,5 ATRw) su TRX con spot e perp TRXUSDT, storia
  dal 2019-09-01 e test dal 2020-06-01 come Q4 di PREREG.md;
- cancello: TRX entra solo se alla stessa domenica W3.2 su BTC (dal 2020-06-01, dati di BTC del giro) è in posizione nello stesso
  verso o vi entra quel giorno; le uscite sono quelle di TRX;
- registro in avanti dal 25/11/2026 in data/trx_carta.json su 10.000 $ di carta. Nessun capitale, nessun ordine, nessun avviso.

Blocco 2 · Scanner settimanale: dopo la chiusura della domenica (UTC) lo stato di W3.2 con i parametri di BTC sulle prime 200 crypto
di CoinGecko (lista rifatta ogni settimana, build_universo_top200: esclusioni dello studio, operabilità Bitget/OKX; se CoinGecko non
risponde resta la lista precedente, in .scanner-cache/universo_top200.json, altrimenti radar/scanner_universo.json dello studio), con
la scheda di qualità dello studio dove c'è. Fonte dei dati: archivio Binance; senza perp Binance vivo, OKX (candele, volumi taker con
le pagine: ~1440 giorni, funding ~3 mesi); senza nessuno dei due "dati insufficienti" con il motivo. Risultato compatto in
data/scanner.json; si ricalcola solo a settimana nuova. Lezione 123: scegliere gli asset con un buon passato non funziona.

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
import re
import threading
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
OKX_CANDLES = "https://www.okx.com/api/v5/market/history-candles"
OKX_TAKER = "https://www.okx.com/api/v5/rubik/stat/taker-volume-contract"
OKX_INSTR = "https://www.okx.com/api/v5/public/instruments"
BITGET_CONTRACTS = "https://api.bitget.com/api/v2/mix/market/contracts"
CG_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"
BN_TICKER = "https://data-api.binance.vision/api/v3/ticker/price"
S3_LIST = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
# pausa minima fra due richieste allo stesso servizio (limiti pubblici: CoinGecko senza chiave ~10–30/min, OKX rubik 5 ogni 2 s,
# OKX candele 20 ogni 2 s, funding 10 ogni 2 s); con più thread le richieste si mettono in fila
PACE = {"https://api.coingecko.com/": 8.0, OKX_TAKER: 0.45, OKX_CANDLES: 0.12, OKX_FUND: 0.22, OKX_INSTR: 0.2}
WINDOW_DAYS = 1000          # ≈ 2,7 anni: SMA 40 settimane + z-score 180 giorni + un anno di simulazione (una sola richiesta spot)
THREADS = 12
MAX_ERR = 25                # oltre questi errori di rete il giro dello scanner si ferma e resta l'ultimo risultato
PROVV_FINO_GIORNI = 2       # risultato provvisorio (perp dell'archivio in ritardo): si riprova fino a 2 giorni dopo la domenica
COLS = ["open", "high", "low", "close", "volume", "tbv"]

AVVISO = "Solo informativa: mostra dove sarebbe W3.2 su ogni moneta, non è un segnale per mettere capitale."   # lezione 123

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
        self.per = {}                               # richieste per servizio (rapporto dei tempi)
        self._s = None
        self._lock, self._last = threading.Lock(), {}

    def _attendi(self, url: str):
        k = next((k for k in PACE if url.startswith(k)), None)
        if not k or not self.pausa:
            return
        with self._lock:
            w = self._last.get(k, 0) + PACE[k] - time.time()
            if w > 0:
                time.sleep(w)
            self._last[k] = time.time()

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
                self._attendi(url)
                self.n += 1
                k = re.sub(r"^https://([^/]+).*", r"\1", url)
                self.per[k] = self.per.get(k, 0) + 1
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


# ------------------------------------------------------------------ OKX (monete senza perp Binance)
def _ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


def _okx_pagine(net: Rete, url: str, params: dict, cur: str, da: date, ts=lambda r: r[0], pagine: int = 20) -> list:
    """Pagine OKX all'indietro (100 righe, cursore `after`/`end` = più vecchie di) fino a `da`; al massimo `pagine` pagine."""
    rows, c = [], None
    for _ in range(pagine):
        j = net.json(url, dict(params, **({cur: c} if c else {}))) or {}
        if str(j.get("code", "0")) != "0":
            raise RuntimeError(f"OKX {j.get('code')}: {str(j.get('msg'))[:60]}")
        d = j.get("data") or []
        if not d:
            break
        rows += d
        c = ts(d[-1])
        if int(c) < _ms(da) or len(d) < 100:
            break
    return rows


def scarica_okx_candele(net: Rete, inst: str, da: date, oggi: date) -> pd.DataFrame:
    """Candele giornaliere UTC (1Dutc) chiuse di OKX: spot X-USDT (volume in moneta) o perp X-USDT-SWAP (volCcy in moneta).
    Senza taker buy (tbv vuoto): servono solo i prezzi."""
    rows = _okx_pagine(net, OKX_CANDLES, {"instId": inst, "bar": "1Dutc", "limit": 100}, "after", da)
    if not rows:
        return _klines([])
    x = pd.DataFrame([r[:9] for r in rows], columns=["t", "open", "high", "low", "close", "vol", "volCcy", "volQuote", "confirm"])
    x = x[x["confirm"] == "1"]
    idx = pd.DatetimeIndex(pd.to_datetime(pd.to_numeric(x["t"]), unit="ms").dt.normalize().values, name="date")
    out = pd.DataFrame({k: pd.to_numeric(x[k]).values for k in ("open", "high", "low", "close")}, index=idx)
    out["volume"] = pd.to_numeric(x["volCcy"] if inst.endswith("-SWAP") else x["vol"]).values
    out["tbv"] = np.nan
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out[(out.index.date >= da) & (out.index.date < oggi)]


def scarica_okx_taker(net: Rete, inst: str, da: date, oggi: date) -> pd.DataFrame:
    """Volumi taker del perp OKX per giorno UTC (rubik taker-volume-contract, period 1Dutc, unit 0 = moneta): volume = acquisti +
    vendite, tbv = acquisti, come le klines Binance (il flusso pf14z usa solo il rapporto). Storia ~1440 giorni con le pagine
    (controllo del 25/11/2026: dal 17/12/2022, senza buchi, anche per BTC)."""
    rows = _okx_pagine(net, OKX_TAKER, {"instId": inst, "period": "1Dutc", "unit": "0", "limit": 100}, "end", da)
    if not rows:
        return pd.DataFrame(columns=["volume", "tbv"], index=pd.DatetimeIndex([], name="date"))
    x = pd.DataFrame([r[:3] for r in rows], columns=["t", "sell", "buy"])
    idx = pd.DatetimeIndex(pd.to_datetime(pd.to_numeric(x["t"]), unit="ms").dt.normalize().values, name="date")
    s, b = pd.to_numeric(x["sell"]).values, pd.to_numeric(x["buy"]).values
    out = pd.DataFrame({"volume": s + b, "tbv": b}, index=idx)
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out[(out.index.date >= da) & (out.index.date < oggi)]


def scarica_okx_perp(net: Rete, inst: str, da: date, oggi: date) -> pd.DataFrame:
    """Perp OKX nello stesso formato del perp Binance: prezzi dalle candele, volume e taker buy dai volumi taker."""
    px = scarica_okx_candele(net, inst, da, oggi)[["open", "high", "low", "close"]]
    tk = scarica_okx_taker(net, inst, da, oggi)
    out = px.join(tk, how="outer")
    return out[out["close"].notna()][COLS]


def scarica_okx_funding(net: Rete, inst: str, da: date, oggi: date) -> pd.DataFrame:
    """Funding OKX giornaliero (somma dei realizzati): l'API dà solo ~3 mesi; la cache conserva quelli già scaricati."""
    rows = _okx_pagine(net, OKX_FUND, {"instId": inst, "limit": 100}, "after", da, ts=lambda r: r["fundingTime"], pagine=10)
    if not rows:
        return pd.DataFrame(columns=["funding", "source"], index=pd.DatetimeIndex([], name="date"))
    x = pd.DataFrame(rows)
    r = pd.to_numeric(x["realizedRate"].replace("", None), errors="coerce").fillna(pd.to_numeric(x["fundingRate"], errors="coerce"))
    d = pd.to_datetime(pd.to_numeric(x["fundingTime"]), unit="ms").dt.normalize()
    out = r.groupby(d.values).sum().to_frame("funding").assign(source="okx")
    out.index = pd.DatetimeIndex(out.index, name="date")
    return out[(out.index.date >= da) & (out.index.date < oggi)].sort_index()


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
        x = _rd(Path(cache) / _nome_cache(c, kind))
        x = _seed(c["ticker"], kind, None if c.get("fonte") == "okx" else seed_dir) if x is None else x
        out[kind] = None if x is None or (kind == "spot" and not (c.get("spot") or c.get("spot_okx"))) else x[x.index >= lim]
    return out | {"errore": None}


def _nome_cache(c: dict, kind: str) -> str:
    """File di cache per moneta e fonte: le serie OKX hanno un nome a parte (scala e simboli diversi da Binance)."""
    return f"{c['ticker']}_{'okx_' if c.get('fonte') == 'okx' else ''}{kind}.csv.gz"


def _scarica(net: Rete, c: dict, kind: str, a: date, oggi: date) -> pd.DataFrame | None:
    okx = c.get("fonte") == "okx"
    if kind == "spot":
        if c.get("spot"):
            return scarica_spot(net, c["spot"], a, oggi)
        return scarica_okx_candele(net, c["spot_okx"], a, oggi) if c.get("spot_okx") else None
    if kind == "perp":
        if okx:
            return scarica_okx_perp(net, c["perp"], a, oggi)
        new = scarica_perp(net, c["perp"], a, oggi)
        if new is not None and len(new) and c.get("div", 1) != 1:   # come lo studio (crypto/build.py scale): stessa scala dei file seme
            new[["open", "high", "low", "close"]] = new[["open", "high", "low", "close"]] / c["div"]
            new[["volume", "tbv"]] = new[["volume", "tbv"]] * c["div"]
        return new
    return scarica_okx_funding(net, c["perp"], a, oggi) if okx else scarica_funding(net, c, a, oggi)


def aggiorna_moneta(net: Rete, c: dict, cache: Path, oggi: date, da: date, seed_dir: Path | None = SEED_DIR) -> dict:
    """Serie spot, perp e funding di una moneta dalla cache, scaricando solo i giorni mancanti. Fonte Binance (prezzi perp divisi
    per c["div"] e volumi moltiplicati: 1000PEPEUSDT -> unità di PEPE, come i file dello studio) oppure OKX (c["fonte"] == "okx":
    candele, volumi taker e funding OKX; spot Binance se c'è). Ritorna {"spot", "perp", "funding", "errore"}: con un errore si
    usa la cache. Moneta senza perp (c["perp"] vuoto): niente da scaricare."""
    cache.mkdir(parents=True, exist_ok=True)
    t, out, err = c["ticker"], {}, None
    okx = c.get("fonte") == "okx"
    seed_dir = None if okx else seed_dir          # i file dello studio per le monete OKX non hanno il taker buy
    lim = pd.Timestamp(max(da, date.fromisoformat(c["da"])) if c.get("da") else da)
    for kind in ("spot", "perp", "funding"):
        p = cache / _nome_cache(c, kind)
        old = _rd(p)
        if old is None:
            old = _seed(t, kind, seed_dir)
        if old is not None:
            old = old[old.index >= lim]
        has = bool(c.get("spot") or c.get("spot_okx")) if kind == "spot" else bool(c.get("perp"))
        if not has:
            out[kind] = None
            continue
        try:
            if kind == "spot":
                a = (old.index.max().date() - timedelta(days=2)) if old is not None and len(old) else lim.date()
            elif kind == "perp":
                back = 3 if okx else 10
                a = (old.index.max().date() - timedelta(days=back)) if old is not None and len(old) else lim.date()
            elif okx:
                a = (old.index.max().date() - timedelta(days=3)) if old is not None and len(old) else lim.date()
            else:
                ob = old[old["source"] == "binance"] if old is not None and "source" in old else old
                a = (ob.index.max().date() - timedelta(days=45)) if ob is not None and len(ob) else lim.date()
            a = max(a, lim.date())
            new = _scarica(net, c, kind, a, oggi) if (kind == "funding" or a < oggi - timedelta(days=1)) else None
            if kind == "funding" and not okx and old is not None and "source" in old and new is not None and len(new):
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
        if w["sma"].notna().sum() == 0:
            return {"lato": None, "nd": f"storia breve: {len(w)} settimane di prezzi, ne servono 40 (SMA 40 settimane)"}
        n_fl = int(f["pf14z"].notna().sum()) if "pf14z" in f else 0
        return {"lato": None, "nd": f"flusso perp non calcolabile: {n_fl} giorni validi di taker buy (servono 14 + 90 giorni)"}
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
        last = float(f["close"].iloc[-1])
        out.update(lato=op["side"], ing=op["entry"], sig=op["signal"], sett=_sett(op["entry"], dom), px_in=_r(px0, 6),
                   trail=_r(op["trail"], 6), mv=round((last / px0 - 1) * sg * 100, 1),
                   du=round((last - float(op["trail"])) / last * sg * 100, 1) if op.get("trail") and last else None)
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
        if not c.get("perp"):                      # nessun perp con taker buy: niente da scaricare
            return c, {"spot": None, "perp": None, "funding": None, "errore": None}, None
        s = aggiorna_moneta(net, c, cache, oggi, da, seed_dir)
        return c, s, feats(s["spot"], s["perp"], s["funding"])
    with ThreadPoolExecutor(threads) as ex:
        res = list(ex.map(uno, universo))
    t_dl = time.time() - t0
    rows, errori, perp_ok, f_btc = [], [], 0, None
    for c, s, f in res:
        st = stato_moneta(f, dom) if c.get("perp") else {"lato": None, "nd": c.get("nd") or "nessuna fonte dati"}
        if c["ticker"] == "BTC":
            f_btc = f
        if s["errore"]:
            errori.append(c["ticker"])
        pp = s.get("perp")
        if pp is not None and len(pp) and pp.index[-1] >= pd.Timestamp(dom) - pd.Timedelta(days=1):
            perp_ok += 1
        extra = {}
        if c.get("fonte") == "okx":
            fu = s.get("funding")
            extra["fo"] = "okx"
            extra["fq"] = str(fu.index[0].date()) if fu is not None and len(fu) else None   # funding OKX solo da questa data
        rows.append({"t": c["ticker"], "n": c.get("nome"), "cl": c.get("classe"), "rk": c.get("rank_oggi"),
                     "bg": bool(c.get("bitget")), "ok": bool(c.get("okx")), "q": c.get("scheda"), **st, **extra,
                     **({"err": s["errore"]} if s["errore"] else {})})
    if len(errori) > len(rows) / 2:   # rete in gran parte giù: meglio l'ultimo risultato completo che uno fatto di cache vecchie
        raise ReteNonDisponibile(f"dati non aggiornati per {len(errori)} monete su {len(rows)}")
    btc = next((r["lato"] for r in rows if r["t"] == "BTC"), None)
    # cancello di Q4 (W3.2 su BTC in posizione alla domenica o vi entra quel giorno): concordanza della settimana e, per ogni
    # posizione, al segnale (registro delle scommesse)
    gate = pd.Series(dtype=int)
    if f_btc is not None and len(f_btc):
        try:
            w = W.weekly_bars(f_btc[f_btc.index <= pd.Timestamp(dom)])
            okw = w[w["sma"].notna() & w["flow"].notna()]
            gate = cancello(f_btc[f_btc.index <= pd.Timestamp(dom)], start=str((okw.index[0] + pd.Timedelta(days=1)).date()))
        except Exception:  # noqa: BLE001
            gate = pd.Series(dtype=int)
    gdir = lambda d: {1: "long", -1: "short", 0: "flat"}.get(int(gate.get(pd.Timestamp(d), 0))) if len(gate) else None  # noqa: E731
    g_dom = gdir(dom) or btc
    for r in rows:
        r["btc"] = _verso_btc(r["lato"], g_dom) if r["t"] != "BTC" else None
        if r.get("sig") and r["lato"] in ("long", "short"):
            r["g"] = gdir(r["sig"])
    n_ok = sum(r["lato"] is not None for r in rows)
    cnt = {k: sum(r["lato"] == k for r in rows) for k in ("long", "short", "flat")} | {"nd": len(rows) - n_ok}
    provv = perp_ok < 0.9 * max(n_ok, 1)
    return {"settimana": str(dom), "calcolato": pd.Timestamp(now).isoformat(timespec="minutes"), "n": len(rows), "conteggi": cnt,
            "nuovi": [r["t"] for r in rows if r.get("evento") == "ingresso"],
            "uscite": [r["t"] for r in rows if r.get("evento") == "uscita"], "btc": btc, "btc_cancello": g_dom, "provvisorio": provv,
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
    net = net or Rete()
    try:
        meta = None
        if universo is None:
            u = aggiorna_universo(net, now, cache)
            universo, meta = u["monete"], u["meta"]
        out = calcola_scanner(universo, net, now, cache, seed_dir)
        if meta:
            out["universo"] = meta
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


def aggiorna_universo(net: Rete, now: datetime, cache: Path = CACHE_DIR, static: Path = UNIVERSO_FILE) -> dict:
    """Lista della settimana: si rifà una volta per settimana (domenica chiusa più recente dell'ultima lista) dalle prime 200 di
    CoinGecko; se CoinGecko non risponde resta la lista precedente (cache, altrimenti quella statica dello studio)."""
    dom = ultima_domenica(now)
    prev = universo_precedente(cache, static)
    nota = None
    if (prev.get("aggiornato") or "") > str(dom):
        u = prev
    else:
        try:
            u = build_universo_top200(net, pd.Timestamp(now).date(), prev, static)
            Path(cache).mkdir(parents=True, exist_ok=True)
            (Path(cache) / UNIV_CACHE).write_text(json.dumps(u, ensure_ascii=False, separators=(",", ":")))
        except ReteNonDisponibile:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[radar] scanner: universo top 200 non aggiornato ({e!r}): resta la lista precedente")
            u, nota = prev, f"Classifica CoinGecko non disponibile ({type(e).__name__}): resta la lista precedente."
    m = u["monete"]
    cnt = {"binance": sum(x.get("fonte") == "binance" for x in m), "okx": sum(x.get("fonte") == "okx" for x in m),
           "senza": sum(not x.get("fonte") for x in m), "operabili": sum(bool(x.get("bitget") or x.get("okx")) for x in m)}
    ex = {}
    for x in u.get("esclusi", []):
        ex.setdefault(x["motivo"], []).append(x["t"])
    meta = {"aggiornato": u.get("aggiornato"), "fonte": u.get("fonte"), "n": len(m), "fonti": cnt, "esclusi": ex,
            "avvisi": list(u.get("avvisi") or []) + ([nota] if nota else []), "richieste": u.get("richieste"), "secondi": u.get("secondi")}
    return {"monete": m, "meta": meta}


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


# ------------------------------------------------------------------ universo top 200 (settimanale)
# Regole di esclusione = research/w32_asset2/crypto/universe.py (copiate: il modulo dello studio legge file locali non in git;
# tests/test_scanner.py controlla che restino uguali)
EXCL_CAT = {"stablecoins": "stablecoin", "yield-bearing-stablecoins": "stablecoin", "wrapped-tokens": "wrapped",
            "bridged-tokens": "bridged", "liquid-staking-tokens": "staked", "liquid-restaking-tokens": "staked",
            "tokenized-btc": "wrapped", "tokenized-gold": "oro/materie prime", "tokenized-silver": "oro/materie prime",
            "tokenized-commodities": "oro/materie prime", "tokenized-treasuries": "rwa/fondo", "tokenized-money-market-fund-mmfs": "rwa/fondo",
            "tokenized-private-credit": "rwa/fondo", "tokenized-credit": "rwa/fondo", "tokenized-stock": "rwa/azione tokenizzata",
            "tokenized-exchange-traded-funds-etfs": "rwa/fondo", "tokenized-products": "rwa/fondo"}
NOT_EXCL = {"spx6900"}
EXCL_MANUAL = {"midas-fasanara-global-open": "rwa/fondo"}
TICK = {"GRAM": "TON", "BTT": "BTTC"}
TICK_ID = {"beam-2": "BEAMX"}
CUT_FROM = {"LIT": "2025-12-23", "SUN": "2021-06-18", "PUMP": "2025-07-10"}
TOP_N = 200
UNIV_CACHE = "universo_top200.json"      # in .scanner-cache/: lista della settimana (fuori da git)
# regola di riserva, solo se una categoria CoinGecko non ha risposto: nomi e prezzi tipici delle classi escluse
RISERVA = [(re.compile(r"\b(wrapped|bridged)\b", re.I), "wrapped"), (re.compile(r"\b(staked|restaked|liquid staking)\b", re.I), "staked"),
           (re.compile(r"\b(gold|silver|xaut|paxg)\b", re.I), "oro/materie prime"), (re.compile(r"\b(tokenized|treasury|fund)\b", re.I), "rwa/fondo")]


def _riserva(x: dict) -> str:
    nome = f"{x.get('name', '')} {x.get('symbol', '')}"
    px = x.get("current_price")
    if px and abs(float(px) - 1) < 0.02 and ("usd" in nome.lower() or "eur" in nome.lower()):
        return "stablecoin"
    return next((lab for rx, lab in RISERVA if rx.search(nome)), "")


CAT_NOMI = {"Stablecoins": "stablecoins", "Yield-Bearing Stablecoin": "yield-bearing-stablecoins", "Wrapped-Tokens": "wrapped-tokens",
            "Bridged-Tokens": "bridged-tokens", "Liquid Staking Tokens": "liquid-staking-tokens", "Liquid Restaking Tokens": "liquid-restaking-tokens",
            "Tokenized BTC": "tokenized-btc", "Tokenized Gold": "tokenized-gold", "Tokenized Silver": "tokenized-silver",
            "Tokenized Commodities": "tokenized-commodities", "Tokenized Treasuries": "tokenized-treasuries",
            "Tokenized Money Market Fund (MMFs)": "tokenized-money-market-fund-mmfs", "Tokenized Private Credit": "tokenized-private-credit",
            "Tokenized Credit": "tokenized-credit", "Tokenized Stocks": "tokenized-stock",
            "Tokenized Exchange-Traded Funds (ETFs)": "tokenized-exchange-traded-funds-etfs", "Tokenized Assets": "tokenized-products"}
CG_COIN = "https://api.coingecko.com/api/v3/coins/"


def categorie_moneta(net: Rete, cg_id: str) -> set[str]:
    """Motivi d'esclusione di una moneta dalle sue categorie CoinGecko (nomi delle categorie di EXCL_CAT, come /coins/categories/list)."""
    j = None
    for k in range(3):                           # 429 frequenti senza chiave: nuovi tentativi distanziati
        try:
            j = net.json(CG_COIN + cg_id, {"localization": "false", "tickers": "false", "market_data": "false", "community_data": "false",
                                           "developer_data": "false", "sparkline": "false"})
            break
        except ReteNonDisponibile:
            raise
        except Exception:  # noqa: BLE001
            if k == 2:
                raise
            time.sleep(20 if net.pausa else 0)
    if not isinstance(j, dict) or "categories" not in j:
        raise ValueError("categorie assenti")
    return {EXCL_CAT[CAT_NOMI[c]] for c in (j.get("categories") or []) if c in CAT_NOMI}


def _classi_studio(path: Path = ROOT / "research" / "w32_asset2" / "crypto" / "data" / "universe_raw.csv") -> dict:
    """Classificazione dello studio (id CoinGecko -> motivo d'esclusione, "" = inclusa)."""
    try:
        u = pd.read_csv(path, usecols=["id_cg", "escluso"]).dropna(subset=["id_cg"])
        return {i: ("" if pd.isna(x) else str(x)) for i, x in zip(u["id_cg"], u["escluso"])}
    except Exception:  # noqa: BLE001
        return {}


def _da_statico(m: dict) -> dict:
    return dict(m, fonte="binance", spot_okx=None, id=None)


def universo_precedente(cache: Path = CACHE_DIR, static: Path = UNIVERSO_FILE) -> dict:
    """Lista della settimana precedente (cache), altrimenti quella dello studio (radar/scanner_universo.json, 25/11/2026)."""
    u = _load(Path(cache) / UNIV_CACHE)
    if u and u.get("monete"):
        return u
    s = json.loads(Path(static).read_text())
    return {"aggiornato": None, "fonte": "studio w32_asset2 (25/11/2026), lista statica", "monete": [_da_statico(m) for m in s["monete"]],
            "esclusi": [], "avvisi": []}


def _s3_simboli(net: Rete, prefix: str = "data/futures/um/daily/klines/") -> set[str]:
    out, marker = set(), ""
    for _ in range(10):
        b = net.get(S3_LIST, {"prefix": prefix, "delimiter": "/", "marker": marker})
        t = (b or b"").decode("utf-8", "replace")
        keys = re.findall(r"<Prefix>([^<]+)</Prefix>", t)[1:]
        out |= {k[len(prefix):].strip("/") for k in keys}
        if "<IsTruncated>true</IsTruncated>" not in t or not keys:
            break
        nm = re.findall(r"<NextMarker>([^<]+)</NextMarker>", t)
        marker = nm[0] if nm else keys[-1]
    return out


def _perp_attivo(net: Rete, sym: str, oggi: date) -> bool:
    """Perp USDT-M ancora vivo nell'archivio: file giornaliero di 2 o 3 giorni fa presente e con volume (un perp delistato può
    continuare ad avere file a volume zero e prezzo fermo: TONUSDT dal 07/2026)."""
    for k in (2, 3):
        d = oggi - timedelta(days=k)
        df = net.zip_csv(f"{ARCHIVE}/daily/klines/{sym}/1d/{sym}-1d-{d:%Y-%m-%d}.zip")
        if df is not None:
            x = _klines(df)
            return bool(len(x) and float(x["volume"].iloc[-1]) > 0)
    return False


def build_universo_top200(net: Rete, oggi: date, prev: dict, static: Path = UNIVERSO_FILE, threads: int = THREADS) -> dict:
    """Prime 200 di CoinGecko (/coins/markets) senza stablecoin, wrapped/bridged, staked, oro/argento, RWA/fondi/azioni
    tokenizzate (regole dello studio); operabilità dalle liste pubbliche Bitget (perp USDT) e OKX (SWAP); fonte dei dati: perp
    USDT-M Binance vivo nell'archivio, altrimenti perp OKX (candele, volumi taker, funding), altrimenti nessuna ("dati
    insufficienti"). Le monete dello studio tengono simboli, date e scheda di qualità di radar/scanner_universo.json.
    Eccezione se la classifica CoinGecko non arriva: il chiamante tiene la lista precedente."""
    t0, n0 = time.time(), net.n
    avvisi = []
    top = None
    for k in range(3):                         # CoinGecko senza chiave risponde spesso 429: due nuovi tentativi distanziati
        try:
            top = net.json(CG_MARKETS, {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1})
            break
        except ReteNonDisponibile:
            raise
        except Exception as e:  # noqa: BLE001
            if k == 2:
                raise RuntimeError(f"classifica CoinGecko non disponibile ({type(e).__name__})") from e
            time.sleep(30 * (k + 1) if net.pausa else 0)
    if not isinstance(top, list) or len(top) < TOP_N:
        raise RuntimeError("classifica CoinGecko incompleta")
    top = sorted([x for x in top if x.get("market_cap_rank")], key=lambda x: x["market_cap_rank"])[:TOP_N]
    # classificazione: già nota (studio del 25/11/2026 e settimane precedenti) oppure, per gli id nuovi, categorie della singola
    # moneta (/coins/{id}) confrontate con i nomi delle categorie escluse. CoinGecko senza chiave limita molto (429): così bastano
    # poche richieste a settimana invece di 17 elenchi di categoria
    note = _classi_studio() | {m["id"]: "" for m in prev.get("monete", []) if m.get("id")} | \
        {x["id"]: x["motivo"] for x in prev.get("esclusi", []) if x.get("id")}
    nuovi = [x for x in top if x["id"] not in note and x["id"] not in EXCL_MANUAL and x["id"] not in NOT_EXCL]
    cat, mancanti = {}, []
    for x in nuovi:
        try:
            cat[x["id"]] = categorie_moneta(net, x["id"])
        except ReteNonDisponibile:
            raise
        except Exception:  # noqa: BLE001
            mancanti.append(x["id"])
    if mancanti:
        avvisi.append(f"categorie CoinGecko non disponibili per {', '.join(mancanti)}: regola di riserva sui nomi")
    # liste di operabilità e dei simboli Binance (se una lista non arriva: valori della settimana precedente)
    prev_m = {m["ticker"]: m for m in prev.get("monete", [])}

    def lista(nome, f):
        try:
            return f()
        except ReteNonDisponibile:
            raise
        except Exception as e:  # noqa: BLE001
            avvisi.append(f"lista {nome} non disponibile ({type(e).__name__}): valori della settimana precedente")
            return None
    bg = lista("Bitget", lambda: {x["baseCoin"]: x["symbol"] for x in (net.json(BITGET_CONTRACTS, {"productType": "USDT-FUTURES"}) or {})["data"]
                                  if x.get("quoteCoin") == "USDT" and x.get("symbolType", "perpetual") == "perpetual" and x.get("symbolStatus", "normal") == "normal"})
    ok_sw = lista("OKX SWAP", lambda: {x["instId"][:-10]: x["instId"] for x in (net.json(OKX_INSTR, {"instType": "SWAP"}) or {})["data"]
                                     if x["instId"].endswith("-USDT-SWAP") and x.get("state", "live") == "live"})
    ok_sp = lista("OKX SPOT", lambda: {x["instId"][:-5]: x["instId"] for x in (net.json(OKX_INSTR, {"instType": "SPOT"}) or {})["data"]
                                     if x["instId"].endswith("-USDT") and x.get("state", "live") == "live"})
    bn_sp = lista("Binance spot", lambda: {x["symbol"] for x in net.json(BN_TICKER) or []})
    bn_um = lista("archivio perp Binance", lambda: _s3_simboli(net))
    static_m = {m["ticker"]: m for m in json.loads(Path(static).read_text())["monete"]}
    try:   # classe dello studio (valutabile, breve, solo prezzo, senza dati) per le monete fuori dalla lista statica
        cl_studio = dict(pd.read_csv(ROOT / "research" / "w32_asset2" / "crypto" / "universe.csv", usecols=["ticker", "classe"]).values)
    except Exception:  # noqa: BLE001
        cl_studio = {}
    righe, esclusi = [], []
    for x in top:
        sym = str(x["symbol"]).upper()
        t = TICK_ID.get(x["id"], TICK.get(sym, sym))
        if x["id"] in EXCL_MANUAL or x["id"] in NOT_EXCL:
            ex = EXCL_MANUAL.get(x["id"], "")
        elif x["id"] in cat:
            ex = ",".join(sorted(cat[x["id"]]))
        elif x["id"] in note:
            ex = note[x["id"]]
        else:
            ex = _riserva(x)
        if ex:
            esclusi.append({"id": x["id"], "t": t, "n": x.get("name"), "rk": x["market_cap_rank"], "motivo": ex})
            continue
        righe.append((t, x))
    viste = set()
    cand = {}
    for t, x in righe:
        if t in viste:
            continue
        viste.add(t)
        s = static_m.get(t)
        pv = prev_m.get(t, {})
        c = {"ticker": t, "nome": x.get("name"), "id": x["id"], "rank_oggi": int(x["market_cap_rank"]),
             "classe": s["classe"] if s else ("nuova" if t not in cl_studio or cl_studio[t] == "esclusa" else cl_studio[t]), "da": (s or {}).get("da") or CUT_FROM.get(t), "scheda": (s or {}).get("scheda"),
             "bitget": (bg.get(t) if bg is not None else pv.get("bitget")), "okx": (ok_sw.get(t) if ok_sw is not None else pv.get("okx"))}
        if s:
            pp = [s["perp"]]
            c["spot"] = s["spot"]
        else:
            pp = [p for p in (f"{t}USDT", f"1000{t}USDT", f"1M{t}USDT", f"1000000{t}USDT") if bn_um is None or p in bn_um]
            c["spot"] = f"{t}USDT" if (bn_sp is not None and f"{t}USDT" in bn_sp) else (pv.get("spot") if bn_sp is None else None)
        cand[t] = (c, pp, pv)

    def attivo(item):
        c, pp, pv = item
        if bn_um is None:                                  # archivio non elencato: scelta della settimana precedente
            return next((p for p in pp if pv.get("fonte") == "binance" and pv.get("perp") == p), None)
        return next((p for p in pp if _perp_attivo(net, p, oggi)), None)
    with ThreadPoolExecutor(threads) as ex_:
        vivi = list(ex_.map(attivo, cand.values()))
    monete = []
    for (c, pp, pv), perp in zip(cand.values(), vivi):
        swap = ok_sw.get(c["ticker"]) if ok_sw is not None else pv.get("okx") or (pv.get("perp") if pv.get("fonte") == "okx" else None)
        if perp:
            c.update(fonte="binance", perp=perp, spot_okx=None,
                     div=1000000 if perp.startswith(("1M", "1000000")) else 1000 if perp.startswith("1000") else 1)
        elif swap:
            c.update(fonte="okx", perp=swap, div=1,
                     spot_okx=None if c.get("spot") else (ok_sp.get(c["ticker"]) if ok_sp is not None else pv.get("spot_okx")))
        else:
            c.update(fonte=None, perp=None, div=1, spot_okx=None,
                     nd=("perp solo su Bitget, senza volumi taker storici pubblici: flusso perp non calcolabile" if c.get("bitget") else
                         "nessun perp su Binance, OKX o Bitget: flusso perp non calcolabile"))
        monete.append(c)
    monete.sort(key=lambda m: m["rank_oggi"])
    return {"aggiornato": str(oggi), "fonte": "CoinGecko /coins/markets (prime 200), liste Bitget e OKX, archivio data.binance.vision",
            "n_top": TOP_N, "n": len(monete), "monete": monete, "esclusi": esclusi, "avvisi": avvisi,
            "richieste": net.n - n0, "secondi": round(time.time() - t0, 1)}


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
