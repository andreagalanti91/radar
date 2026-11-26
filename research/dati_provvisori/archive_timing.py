"""Ora di pubblicazione dei file giornalieri di data.binance.vision (perp USDT-M BTCUSDT).

Legge l'elenco pubblico del bucket (stesso elenco della pagina https://data.binance.vision) e per ogni file giornaliero
calcola il ritardo = LastModified − fine del giorno UTC. Salva timing.csv e stampa il riepilogo per giorno della settimana.
I file molto vecchi sono stati ricaricati in blocco (es. 21/03/2022): si usano solo i giorni dal 2024-06-01.
Uso: python3 archive_timing.py [cartella_output]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import requests

LIST = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
PREFIXES = {"klines_1d": "data/futures/um/daily/klines/BTCUSDT/1d/",
            "metrics": "data/futures/um/daily/metrics/BTCUSDT/",
            "premium_8h": "data/futures/um/daily/premiumIndexKlines/BTCUSDT/8h/",
            "premium_1m": "data/futures/um/daily/premiumIndexKlines/BTCUSDT/1m/",
            "spot_klines_1d": "data/spot/daily/klines/BTCUSDT/1d/"}
FROM = pd.Timestamp("2024-06-01")


def listing(prefix: str, marker: str) -> list[tuple[str, str]]:
    out = []
    while True:
        r = requests.get(LIST, params={"delimiter": "/", "prefix": prefix, "marker": marker}, timeout=60)
        r.raise_for_status()
        t = r.text
        out += re.findall(r"<Key>([^<]+\.zip)</Key><LastModified>([^<]+)</LastModified>", t)
        if "<IsTruncated>true</IsTruncated>" not in t:
            return out
        marker = re.findall(r"<NextMarker>([^<]+)</NextMarker>", t)[0]


def main(outdir: Path) -> pd.DataFrame:
    rows = []
    for name, pre in PREFIXES.items():
        # parti dal 2024-06 per non scaricare l'elenco intero
        sample = "BTCUSDT-1d-" if "klines" in name else ("BTCUSDT-metrics-" if name == "metrics" else
                                                          "BTCUSDT-8h-" if name == "premium_8h" else "BTCUSDT-1m-")
        for key, lm in listing(pre, pre + sample + "2024-05-31.zip"):
            m = re.search(r"(\d{4}-\d{2}-\d{2})\.zip$", key)
            if not m:
                continue
            day = pd.Timestamp(m.group(1))
            if day < FROM:
                continue
            lmt = pd.Timestamp(lm).tz_localize(None)
            rows.append({"file": name, "day": day, "dow": day.day_name(), "last_modified": lmt,
                         "lag_h": (lmt - (day + pd.Timedelta(days=1))).total_seconds() / 3600})
    df = pd.DataFrame(rows)
    df.to_csv(outdir / "timing.csv", index=False)
    return df


def summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["file", "dow"])["lag_h"]
    s = pd.DataFrame({"n": g.size(), "mediana_h": g.median().round(1), "p90_h": g.quantile(0.9).round(1),
                      "p95_h": g.quantile(0.95).round(1), "max_h": g.max().round(1)})
    return s


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    df = main(out)
    s = summary(df)
    s.to_csv(out / "timing_summary.csv")
    print(s.to_string())
    # quota dei sabati / domeniche disponibili entro le ore del lunedì (ore dalla fine della DOMENICA)
    for f in ("klines_1d", "metrics", "premium_8h"):
        d = df[df.file == f]
        for dow, shift in (("Saturday", 24), ("Sunday", 0)):
            x = d[d.dow == dow]["lag_h"] - shift   # ore dopo la mezzanotte domenica→lunedì
            print(f, dow, "pronto entro lun 00:07:", round((x <= 7 / 60).mean() * 100, 1), "%",
                  "· entro 01:07:", round((x <= 67 / 60).mean() * 100, 1), "%",
                  "· entro 06:00:", round((x <= 6).mean() * 100, 1), "%",
                  "· entro 12:00:", round((x <= 12).mean() * 100, 1), "%", "n", len(x))
