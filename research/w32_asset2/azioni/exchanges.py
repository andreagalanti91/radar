"""W3.2 asset ciclo 2 · azioni · operabilità su Bitget e OKX dalle liste PUBBLICHE degli strumenti (nessuna chiave).

Fonti (GET pubblici, User-Agent generico):
- Bitget  /api/v2/mix/market/contracts?productType=USDT-FUTURES|USDC-FUTURES|COIN-FUTURES  (campo isRwa = YES per azioni,
          ETF, indici, materie prime; openTime = data di apertura dichiarata, ms) e /api/v2/spot/public/symbols (token).
          Funding: /api/v2/mix/market/history-fund-rate (storico a pagine) e current-fund-rate (intervallo).
- OKX     /api/v5/public/instruments?instType=SWAP|FUTURES|SPOT (instCategory = 3 per le azioni; listTime, ms).
          Funding: /api/v5/public/funding-rate-history (solo gli ultimi ~3 mesi per limite dell'API).
Abbinamento al titolo: codice base dello strumento = ticker USA senza punteggiatura (BRK-B -> BRKB), o ticker + "STOCK" (Bitget,
quando il ticker coincide con una crypto), o alias esplicito (colonna exch_alias di universe.csv, es. TENCENT, SAMSUNG).
Nessuna deduzione: se l'abbinamento non è certo lo strumento non viene attribuito. ETF/indici/ETP esclusi per regola dell'utente.
Uscite: data/exchanges/*.json.gz (liste grezze con data), data/exchanges/stock_instruments.csv, data/exchanges/funding_*.csv.gz.
"""
from __future__ import annotations

import gzip
import json
import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
X = HERE / "data" / "exchanges"
UA = {"User-Agent": "research-client/1.0"}


def get(url: str, params: dict | None = None) -> dict:
    for k in range(3):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=60)
            r.raise_for_status()
            time.sleep(0.25)
            return r.json()
        except requests.RequestException:
            if k == 2:
                raise
            time.sleep(3 * (k + 1))
    return {}


def save(name: str, obj) -> None:
    with gzip.open(X / f"{name}.json.gz", "wt") as fh:
        json.dump(obj, fh)


def ms(x) -> str:
    try:
        v = int(x)
        return str(pd.Timestamp(v, unit="ms").date()) if v > 0 else ""
    except (TypeError, ValueError):
        return ""


def instruments() -> pd.DataFrame:
    rows = []
    for pt in ("USDT-FUTURES", "USDC-FUTURES", "COIN-FUTURES"):
        d = get("https://api.bitget.com/api/v2/mix/market/contracts", dict(productType=pt))
        save(f"bitget_{pt}", d)
        for x in d.get("data") or []:
            if x.get("isRwa") == "YES":
                rows.append(dict(exchange="bitget", kind=f"perp {pt}", inst=x["symbol"], base=x["baseCoin"], since=ms(x.get("openTime")),
                                 launch=ms(x.get("launchTime")), fund_h=x.get("fundInterval"), max_lev=x.get("maxLever"), status=x.get("symbolStatus")))
    d = get("https://api.bitget.com/api/v2/spot/public/symbols")
    save("bitget_spot", d)
    for t in ("SWAP", "FUTURES", "SPOT"):
        d = get("https://www.okx.com/api/v5/public/instruments", dict(instType=t))
        save(f"okx_{t}", d)
        for x in d.get("data") or []:
            if x.get("instCategory") == "3":
                base = x["instFamily"].split("-")[0] if x.get("instFamily") else x.get("baseCcy", "")
                if t == "SPOT":
                    base = x.get("baseCcy", "")
                rows.append(dict(exchange="okx", kind={"SWAP": "perp", "FUTURES": "futures XPERP", "SPOT": "token spot"}[t], inst=x["instId"],
                                 base=base, since=ms(x.get("listTime")), launch="", fund_h="", max_lev=x.get("lever"), status=x.get("state")))
    return pd.DataFrame(rows)


def bitget_funding(sym: str) -> pd.DataFrame:
    out = []
    for pg in range(1, 30):
        d = get("https://api.bitget.com/api/v2/mix/market/history-fund-rate",
                dict(symbol=sym, productType="usdt-futures", pageSize=100, pageNo=pg)).get("data") or []
        out += d
        if len(d) < 100:
            break
    df = pd.DataFrame(out)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["fundingTime"].astype("int64"), unit="ms")
    return df[["time", "fundingRate"]].astype({"fundingRate": float}).sort_values("time")


def okx_funding(inst: str) -> pd.DataFrame:
    out, after = [], None
    for _ in range(10):
        p = dict(instId=inst, limit=400)
        if after:
            p["after"] = after
        d = get("https://www.okx.com/api/v5/public/funding-rate-history", p).get("data") or []
        if not d:
            break
        out += d
        after = d[-1]["fundingTime"]
        if len(d) < 100:
            break
    df = pd.DataFrame(out)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["fundingTime"].astype("int64"), unit="ms")
    df["fundingRate"] = df["realizedRate"].replace("", None).fillna(df["fundingRate"]).astype(float)
    return df[["time", "fundingRate"]].drop_duplicates("time").sort_values("time")


def codes(row: pd.Series) -> list[str]:
    c = []
    us = row.get("us_ticker")
    if isinstance(us, str) and us:
        b = us.replace("-", "").replace(".", "")
        c += [b, b + "STOCK"]
    al = row.get("exch_alias")
    if isinstance(al, str) and al:
        c += al.split("|")
    return c


def match(uni: pd.DataFrame, ins: pd.DataFrame) -> pd.DataFrame:
    perps = ins[ins["kind"].str.startswith("perp")]
    toks = ins[ins["kind"] == "token spot"]
    res = []
    for _, r in uni.iterrows():
        cs = codes(r)
        out = dict(yahoo=r["yahoo"])
        for ex in ("bitget", "okx"):
            p = perps[(perps.exchange == ex) & perps.base.isin(cs)]
            out[f"{ex}_perp"] = "|".join(p.inst)
            out[f"{ex}_since"] = min(p.since) if len(p) else ""
        t = toks[toks.base.isin(["X" + x for x in cs])]   # OKX: token azionari "X<ticker>" (xStocks)
        out["okx_token"] = "|".join(t.inst)
        out["okx_token_since"] = min(t.since) if len(t) else ""
        res.append(out)
    return pd.DataFrame(res)


if __name__ == "__main__":
    X.mkdir(parents=True, exist_ok=True)
    ins = instruments()
    ins["downloaded"] = pd.Timestamp.now("UTC").strftime("%Y-%m-%d")
    ins.to_csv(X / "stock_instruments.csv", index=False)
    print(ins.groupby(["exchange", "kind"]).size())
    uni = pd.read_csv(HERE / "universe.csv")
    m = match(uni, ins)
    m.to_csv(X / "match.csv", index=False)
    fund = []
    for _, r in m.iterrows():
        for sym in filter(None, r["bitget_perp"].split("|")):
            df = bitget_funding(sym)
            if len(df):
                df.to_csv(X / f"funding_bitget_{sym}.csv.gz", index=False)
                fund.append(dict(yahoo=r["yahoo"], exchange="bitget", inst=sym, n=len(df), first=str(df.time.min()), last=str(df.time.max()),
                                 mean_rate=df.fundingRate.mean(), per_day=len(df) / max(1, (df.time.max() - df.time.min()).days)))
        for inst in filter(None, r["okx_perp"].split("|")):
            df = okx_funding(inst)
            if len(df):
                df.to_csv(X / f"funding_okx_{inst}.csv.gz", index=False)
                fund.append(dict(yahoo=r["yahoo"], exchange="okx", inst=inst, n=len(df), first=str(df.time.min()), last=str(df.time.max()),
                                 mean_rate=df.fundingRate.mean(), per_day=len(df) / max(1, (df.time.max() - df.time.min()).days)))
    fd = pd.DataFrame(fund)
    if len(fd):
        fd["annual_pct"] = fd["mean_rate"] * fd["per_day"] * 365 * 100
    fd.to_csv(X / "funding_summary.csv", index=False)
    print(fd.to_string() if len(fd) else "nessun funding")
