"""Parte 2 · fase 1: scarica i dati pubblici e gratuiti per le famiglie F1 (opzioni) e F3 (rotazione crypto).

Fonti (API pubbliche documentate, nessuna chiave, nessuno scraping):
- Deribit `public/get_volatility_index_data` (www.deribit.com): DVOL BTC giornaliero (esiste dal 24/03/2021).
- Deribit `public/get_last_trades_by_currency_and_time` (history.deribit.com, archivio ufficiale): opzioni BTC scambiate
  nelle 24 ore della DOMENICA UTC (giorno della decisione W3), aggregate in put/call e skew; dal 2019 (dati sottili prima).
- Binance `data-api.binance.vision` /api/v3/klines: ETHBTC spot giornaliero (dal 14/07/2017).
- Binance `data.binance.vision` archivio futures USDT-M: BTCDOMUSDT giornaliero (indice di dominanza Binance, dal 2021).
Uso: python3 -I fetch.py [dvol|ethbtc|btcdom|opt|all]   (output in ./data/, relativo a questo file)
"""
from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

D = Path(__file__).resolve().parent / "data"
D.mkdir(exist_ok=True)
UA = {"User-Agent": "radar-research/1.0"}
END = datetime(2026, 11, 17, tzinfo=timezone.utc)   # ultimo giorno chiuso usato nella ricerca (dati congelati)


def get(url: str, retries: int = 5):
    for k in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if getattr(e, "code", None) == 404:
                return None
            time.sleep(2 + 3 * k)
    raise RuntimeError(f"fallito: {url}")


def ms(d: datetime) -> int:
    return int(d.timestamp() * 1000)


def dvol() -> None:
    rows, s = {}, datetime(2021, 3, 1, tzinfo=timezone.utc)
    while s < END + timedelta(days=1):
        e = min(s + timedelta(days=600), END + timedelta(days=1))
        url = ("https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC"
               f"&start_timestamp={ms(s)}&end_timestamp={ms(e)}&resolution=1D")
        for t, o, h, l, c in json.loads(get(url))["result"]["data"]:
            rows[t] = (o, h, l, c)
        s = e
    with open(D / "dvol_btc_1d.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "open", "high", "low", "close"])
        for t in sorted(rows):
            day = datetime.fromtimestamp(t / 1000, timezone.utc).date()
            if day <= END.date():
                w.writerow([day.isoformat(), *rows[t]])
    print("dvol", len(rows))


def ethbtc() -> None:
    rows, s = [], ms(datetime(2017, 7, 1, tzinfo=timezone.utc))
    while True:
        url = f"https://data-api.binance.vision/api/v3/klines?symbol=ETHBTC&interval=1d&startTime={s}&limit=1000"
        k = json.loads(get(url))
        if not k:
            break
        rows += k
        s = k[-1][0] + 86400000
        if len(k) < 1000:
            break
    with open(D / "ethbtc_1d.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "open", "high", "low", "close", "volume_eth"])
        for r in rows:
            day = datetime.fromtimestamp(r[0] / 1000, timezone.utc).date()
            if day <= END.date():
                w.writerow([day.isoformat(), r[1], r[2], r[3], r[4], r[5]])
    print("ethbtc", len(rows))


def _zip_rows(blob: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        txt = z.read(z.namelist()[0]).decode()
    return [r for r in csv.reader(io.StringIO(txt)) if r and r[0].isdigit()]


def btcdom() -> None:
    base = "https://data.binance.vision/data/futures/um"
    rows: dict[int, list[str]] = {}
    m = date(2020, 6, 1)
    while m <= END.date():
        blob = get(f"{base}/monthly/klines/BTCDOMUSDT/1d/BTCDOMUSDT-1d-{m:%Y-%m}.zip")
        if blob:
            for r in _zip_rows(blob):
                rows[int(r[0])] = r
        elif m.year == END.year and m.month == END.month:      # mese in corso: archivi giornalieri
            d = m
            while d <= END.date():
                b = get(f"{base}/daily/klines/BTCDOMUSDT/1d/BTCDOMUSDT-1d-{d:%Y-%m-%d}.zip")
                for r in (_zip_rows(b) if b else []):
                    rows[int(r[0])] = r
                d += timedelta(days=1)
        m = (m.replace(day=28) + timedelta(days=4)).replace(day=1)
    with open(D / "btcdom_1d.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "open", "high", "low", "close"])
        for t in sorted(rows):
            r = rows[t]
            w.writerow([datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat(), r[1], r[2], r[3], r[4]])
    print("btcdom", len(rows))


MON = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}


def _expiry(code: str) -> datetime:
    dd, mm, yy = int(code[:-5]), MON[code[-5:-2]], 2000 + int(code[-2:])
    return datetime(yy, mm, dd, 8, tzinfo=timezone.utc)                 # scadenze Deribit alle 08:00 UTC


def opt_day(day: date) -> dict:
    """Aggrega le opzioni BTC scambiate nella domenica UTC `day` (00:00–24:00)."""
    s0 = ms(datetime(day.year, day.month, day.day, tzinfo=timezone.utc))
    e0, s, seen = s0 + 86400000, s0, {}
    while True:
        url = ("https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time?currency=BTC&kind=option"
               f"&start_timestamp={s}&end_timestamp={e0}&count=10000&sorting=asc")
        res = json.loads(get(url))["result"]
        tr = res["trades"]
        new = 0
        for t in tr:
            if t["trade_id"] not in seen:
                seen[t["trade_id"]] = t
                new += 1
        if not res.get("has_more") or not tr or new == 0:
            break
        s = tr[-1]["timestamp"]                                           # inclusivo + dedupe per trade_id
    agg = dict(date=day.isoformat(), n=0, call_btc=0.0, put_btc=0.0, call_buy_btc=0.0, put_buy_btc=0.0,
               pw_iv=0.0, pw_w=0.0, cw_iv=0.0, cw_w=0.0, atm_iv=0.0, atm_w=0.0)
    for t in seen.values():
        _, exp, k, cp = t["instrument_name"].split("-")
        a, S = float(t["amount"]), float(t["index_price"])
        agg["n"] += 1
        side = "call" if cp == "C" else "put"
        agg[f"{side}_btc"] += a
        if t["direction"] == "buy":
            agg[f"{side}_buy_btc"] += a
        iv = t.get("iv")
        if not iv or iv <= 0:
            continue
        days = (_expiry(exp) - datetime.fromtimestamp(t["timestamp"] / 1000, timezone.utc)).total_seconds() / 86400
        if not 7 <= days <= 45:
            continue
        mny = float(k) / S
        if cp == "P" and 0.80 <= mny <= 0.95:
            agg["pw_iv"] += iv * a; agg["pw_w"] += a
        elif cp == "C" and 1.05 <= mny <= 1.20:
            agg["cw_iv"] += iv * a; agg["cw_w"] += a
        elif 0.97 <= mny <= 1.03:
            agg["atm_iv"] += iv * a; agg["atm_w"] += a
    out = dict(date=agg["date"], n_trades=agg["n"], call_btc=round(agg["call_btc"], 3), put_btc=round(agg["put_btc"], 3),
               call_buy_btc=round(agg["call_buy_btc"], 3), put_buy_btc=round(agg["put_buy_btc"], 3))
    for p in ("pw", "cw", "atm"):
        out[f"{p}_iv"] = round(agg[f"{p}_iv"] / agg[f"{p}_w"], 3) if agg[f"{p}_w"] > 0 else ""
        out[f"{p}_btc"] = round(agg[f"{p}_w"], 3)
    return out


def opt(first: date = date(2019, 1, 6), last: date | None = None, path: Path | None = None) -> None:
    """Domeniche da `first` (prima domenica del 2019) a `last`; riprende da dove si era fermato (date già presenti)."""
    path = path or D / "deribit_opt_sunday.csv"
    last = last or END.date()
    done = set()
    for pp in [path, D / "deribit_opt_sunday.csv"]:
        if pp.exists():
            with open(pp) as fh:
                done |= {r["date"] for r in csv.DictReader(fh)}
    d = first
    fields = None
    while d <= last:
        if d.isoformat() not in done:
            row = opt_day(d)
            new_file = not path.exists()
            with open(path, "a", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(row))
                if new_file:
                    w.writeheader()
                w.writerow(row)
            fields = fields or list(row)
        d += timedelta(days=7)
    print("opt ok")


def merge_parts() -> None:
    """Unisce data/opt_part_*.csv nel file principale, ordinato per data, senza doppioni; cancella le parti."""
    path = D / "deribit_opt_sunday.csv"
    rows = {}
    for pp in [path, *sorted(D.glob("opt_part_*.csv"))]:
        if pp.exists():
            with open(pp) as fh:
                for r in csv.DictReader(fh):
                    rows[r["date"]] = r
    keys = sorted(rows)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[keys[0]]))
        w.writeheader()
        for k in keys:
            w.writerow(rows[k])
    for pp in D.glob("opt_part_*.csv"):
        pp.unlink()
    print("opt", len(keys), keys[0], keys[-1])


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "optpart":          # python3 -I fetch.py optpart AAAA-MM-GG AAAA-MM-GG n  (domeniche, intervallo chiuso)
        a, b = (date.fromisoformat(x) for x in sys.argv[2:4])
        opt(a, b, D / f"opt_part_{sys.argv[4]}.csv")
        sys.exit(0)
    if what == "merge":
        merge_parts()
        sys.exit(0)
    for name, fn in (("dvol", dvol), ("ethbtc", ethbtc), ("btcdom", btcdom), ("opt", opt)):
        if what in (name, "all"):
            fn()
