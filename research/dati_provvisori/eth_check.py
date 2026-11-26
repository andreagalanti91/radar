"""Controllo ETH (secondo asset di W3.2): funding OKX contro Binance e ricostruzione dall'indice di premio, ultime 12 domeniche.

Uso: python3 -I eth_check.py RAW REPO   (REPO deve contenere eth_funding.csv del ramo dati)
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import collect  # noqa: E402
import funding_rebuild as fr  # noqa: E402
from analysis import archived_until  # noqa: E402


def main(raw: Path, repo: Path) -> None:
    today = date.today()
    this = date(today.year, today.month, 1)
    urls = [f"{collect.ARCH}/monthly/premiumIndexKlines/ETHUSDT/1m/ETHUSDT-1m-{m}.zip" for m in ("2026-07", "2026-08", "2026-09", "2026-10")]
    urls += [f"{collect.ARCH}/daily/premiumIndexKlines/ETHUSDT/1m/ETHUSDT-1m-{this + timedelta(days=i):%Y-%m-%d}.zip"
             for i in range((today - this).days)]
    frames = [x for x in map(collect._zip, urls) if x is not None]
    df = pd.concat(frames)
    ot = pd.to_numeric(df["open_time"], errors="coerce").dropna().astype("int64")
    prem = pd.Series(pd.to_numeric(df["close"]).values[: len(ot)], index=pd.to_datetime(ot.values, unit="ms")).sort_index()
    prem = prem[~prem.index.duplicated()]
    reb8 = fr.funding_8h(prem)
    rows = collect.okx_pages(f"{collect.OKX}/public/funding-rate-history", {"instId": "ETH-USDT-SWAP", "limit": 100})
    o = pd.DataFrame(rows)
    o8 = pd.Series(pd.to_numeric(o["realizedRate"]).values, index=pd.to_datetime(pd.to_numeric(o["fundingTime"]), unit="ms")).sort_index()
    okx = o8.groupby(o8.index.normalize()).sum()
    act = pd.read_csv(repo / "eth_funding.csv", index_col=0, parse_dates=True)
    end = pd.Timestamp("2026-10-31")
    fb = act[(act["source"] == "binance") & (act.index <= end)]["funding"]
    reb = fr.daily(reb8)
    chk = pd.concat([fb.rename("b"), reb.rename("r")], axis=1, sort=True).dropna()
    e = (chk["r"].rolling(7).mean() - chk["b"].rolling(7).mean()).abs().dropna()
    print(f"ETH ricostruzione fund7 vs archivio: n {len(e)} p95 {e.quantile(.95):.2e} max {e.max():.2e}")
    fdef = pd.concat([fb, reb[reb.index > end]])
    out = []
    for S in pd.date_range("2026-08-30", fdef.index.max(), freq="W-SUN"):
        days = pd.date_range(S - pd.Timedelta(days=6), S)
        if days[0] <= okx.index.min():
            continue
        au = archived_until(S + pd.Timedelta(days=1, minutes=7))
        f0 = [fdef[d] if d <= au else okx.get(d) for d in days]
        f1 = []
        for d in days:
            if d <= au:
                f1.append(fdef[d])
                continue
            pays = [d + pd.Timedelta(hours=h) for h in (0, 8, 16)]
            f1.append(sum(reb8.get(p) if (p - pd.Timedelta(minutes=1)).normalize() < S else o8.get(p) for p in pays))
        out.append(dict(date=S.date(), fund7_def=fdef.reindex(days).mean(), F0_attuale=sum(f0) / 7, F1_premio_binance=sum(f1) / 7))
    out = pd.DataFrame(out)
    out["err_F0"] = out["F0_attuale"] - out["fund7_def"]
    out["err_F1"] = out["F1_premio_binance"] - out["fund7_def"]
    out.to_csv(HERE / "eth_funding_sundays.csv", index=False)
    print(out.to_string(index=False))
    for c in ("err_F0", "err_F1"):
        a = out[c].abs()
        print(c, f"mediana {a.median():.2e} p95 {a.quantile(.95):.2e} max {a.max():.2e}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
