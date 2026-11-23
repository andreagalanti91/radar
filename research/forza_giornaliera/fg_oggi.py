"""Caso 21–23/11/2026 e stato di oggi (BTC, ETH). Descrittivo. Non scrive in data/: i file scaricati restano in dati/.
Fonti: data/*.csv del tool (fino al 21/11), Binance spot (data-api.binance.vision), archivio Binance USDT-M 1h (data.binance.vision,
22/11), OKX rubik taker-volume (contratti, 23/11: provvisorio, altra borsa). Uso: python3 fg_oggi.py [--fetch] → oggi.txt"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D = HERE / "dati"
sys.path.insert(0, str(HERE))
import fg_lib as G  # noqa: E402
from radar import weekly as W  # noqa: E402
from radar.data import load_all, load_asset  # noqa: E402
from radar.features import build_features  # noqa: E402

SYM = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
KC = ["t", "open", "high", "low", "close", "volume", "ct", "quote_volume", "count", "taker_buy_volume", "tbq", "ign"]
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def fetch():
    import requests
    for a, s in SYM.items():
        for iv, lim in (("1d", 10), ("1h", 120)):
            r = requests.get("https://data-api.binance.vision/api/v3/klines", params={"symbol": s, "interval": iv, "limit": lim}, timeout=30)
            (D / f"{a}_spot_{iv}.json").write_text(r.text)
        r = requests.get("https://www.okx.com/api/v5/rubik/stat/taker-volume", params={"ccy": a, "instType": "CONTRACTS", "period": "1H"}, timeout=30)
        (D / f"{a}_okx_contratti_1h.json").write_text(r.text)
        r = requests.get("https://www.okx.com/api/v5/rubik/stat/taker-volume", params={"ccy": a, "instType": "SPOT", "period": "1H"}, timeout=30)
        (D / f"{a}_okx_spot_1h.json").write_text(r.text)


def kl(path) -> pd.DataFrame:
    x = pd.DataFrame(json.loads(Path(path).read_text()), columns=KC).astype(float)
    x.index = pd.to_datetime(x["t"], unit="ms")
    return x


def perp_1h(asset: str) -> pd.DataFrame:
    out = []
    for p in sorted(D.glob(f"{SYM[asset]}-1h-*.zip")):
        z = zipfile.ZipFile(p)
        x = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
        x.columns = KC[:len(x.columns)]
        x.index = pd.to_datetime(x["t"], unit="ms")
        out.append(x)
    return pd.concat(out).sort_index()


def okx(asset: str, kind: str) -> pd.DataFrame:
    j = json.loads((D / f"{asset}_okx_{kind}_1h.json").read_text())["data"]
    x = pd.DataFrame(j, columns=["t", "sell", "buy"]).astype(float)
    x.index = pd.to_datetime(x["t"], unit="ms")
    return x.sort_index()


def main():
    if "--fetch" in sys.argv:
        fetch()
    for a in ("BTC", "ETH"):
        d = load_all() if a == "BTC" else load_asset(a)
        sd, sh, ph = kl(D / f"{a}_spot_1d.json"), kl(D / f"{a}_spot_1h.json"), perp_1h(a)
        last_h = sh.index[-1]
        say(f"\n===== {a} · dati orari spot fino a {last_h} UTC (ultima ora in corso) · perp Binance orario fino a {ph.index[-1]}")
        # --- giorno 22/11 aggiunto ai dati del tool (spot: API; perp: archivio orario)
        day = pd.Timestamp("2026-11-22")
        sp, pp = d["spot"].copy(), d["perp"].copy()
        cols = ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_volume"]
        if day not in sp.index:
            sp.loc[day, cols] = sd.loc[day, cols].to_numpy()
        ph22 = ph[ph.index.normalize() == day]
        if day not in pp.index and len(ph22) == 24:
            pp.loc[day, cols] = [ph22["open"].iloc[0], ph22["high"].max(), ph22["low"].min(), ph22["close"].iloc[-1],
                                 ph22["volume"].sum(), ph22["quote_volume"].sum(), ph22["taker_buy_volume"].sum()]
            pp.loc[day, "source"] = "binance"
        d2 = dict(d, spot=sp, perp=pp)
        f0 = build_features(d2)
        f0 = f0[f0["close"].notna()]
        f = G.add_flows(f0)
        f["cl_buy"] = G.klass(f, 3, 1, 0.5)
        f["cl_sell"] = G.klass(f, 3, -1, 0.5)
        f["cl_buy_usd"] = G.klass_trader(f, 3, 1)
        f["spot_usd"] = f["spot_delta"] * f["close"] / 1e6
        f["perp_usd"] = f["perp_delta"] * f["close"] / 1e6
        f["vr"] = f["perp_vol"] / f["spot_vol"]
        t = f.loc["2026-11-14":, ["close", "low", "high", "spot_usd", "perp_usd", "vr", "up3", "dn3", "pz3", "sz3", "cl_buy", "cl_sell",
                                  "cl_buy_usd", "hi20", "lo20", "pf14z", "sf14z"]].copy()
        say("Giornaliero Binance (delta netto taker in M$; vr = volume perp/spot; up3/dn3 = dal minimo/massimo di 3 giorni):")
        say(t.round(2).to_string())
        say(f"rapporto mediano dei volumi perp/spot a 180 giorni: {f['vratio'].iloc[-1]:.1f}")
        # --- orario dal minimo del 21/11
        h = pd.read_csv(G.ROOT / "data" / "taker_1h.csv", index_col=0, parse_dates=True) if a == "BTC" else None
        x = pd.DataFrame({"close": sh["close"], "spot_d": (2 * sh["taker_buy_volume"] - sh["volume"]) * sh["close"] / 1e6,
                          "spot_v": sh["quote_volume"] / 1e6})
        x["perp_d"] = ((2 * ph["taker_buy_volume"] - ph["volume"]) * ph["close"] / 1e6).reindex(x.index)
        x["perp_v"] = (ph["quote_volume"] / 1e6).reindex(x.index)
        oc, osp = okx(a, "contratti"), okx(a, "spot")
        x["okx_perp_d"] = ((oc["buy"] - oc["sell"]) / 1e6).reindex(x.index)
        x["okx_spot_d"] = ((osp["buy"] - osp["sell"])).reindex(x.index)
        x21 = x[x.index >= "2026-11-21"]
        tlow = sh.loc["2026-11-21":"2026-11-21 23:00", "low"].idxmin()
        say(f"minimo del 21/11: {sh.loc[tlow, 'low']:.0f} nell'ora {tlow} UTC")
        wins = {"dal minimo del 21/11 a fine 21/11": (tlow, "2026-11-21 23:00"), "22/11 (giorno intero)": ("2026-11-22", "2026-11-22 23:00"),
                "dal minimo a fine 22/11": (tlow, "2026-11-22 23:00"), "23/11 fino all'ultima ora chiusa": ("2026-11-23", last_h - pd.Timedelta(hours=1)),
                "22/11 + 23/11": ("2026-11-22", last_h - pd.Timedelta(hours=1))}
        for nm, (s, e) in wins.items():
            y = x.loc[s:e]
            pb = y["perp_d"].sum(min_count=1)
            row = f"{nm}: prezzo {y['close'].iloc[0]:.0f} → {y['close'].iloc[-1]:.0f} · spot Binance {y['spot_d'].sum():+.0f} M$ (vol {y['spot_v'].sum():.0f})"
            row += f" · perp Binance {pb:+.0f} M$ su {int(y['perp_d'].notna().sum())}/{len(y)} ore (vol {y['perp_v'].sum():.0f})" if np.isfinite(pb) else " · perp Binance n.d."
            row += f" · contratti OKX {y['okx_perp_d'].sum():+.0f} M$ (provvisorio, {int(y['okx_perp_d'].notna().sum())} ore)"
            if np.isfinite(pb) and y["perp_d"].notna().all() and abs(y["spot_d"].sum()) > 0:
                row += f" · rapporto perp/spot dei netti {pb / y['spot_d'].sum():+.1f}:1 · rapporto dei volumi {y['perp_v'].sum() / y['spot_v'].sum():.1f}"
            say(row)
        # massimo orario dopo il minimo e livello 62,5k
        y = sh.loc[tlow:]
        say(f"massimo dopo il minimo: {y['high'].max():.0f} ({y['high'].idxmax()}) · ultimo prezzo {sh['close'].iloc[-1]:.0f}")
        # --- stato W3.2 e regole
        r = W.simulate(f0)
        o = r["open"]
        say(f"W3.2 al {f0.index[-1].date()}: " + (f"{o['side']} dal {o['entry']} a {o['entry_px']} · trailing {o['trail']:.0f} · P/L {100 * o['pnl']:+.1f}%" if o else "flat")
            + f" · decisione in sospeso: {r['pending']}")
        last = f.iloc[-1]
        say(f"Regole (chiusura {f.index[-1].date()}): up3 {100 * last['up3']:+.1f}% · pz3 {last['pz3']:+.2f} · sz3 {last['sz3']:+.2f} → classe acquisti '{last['cl_buy']}' "
            f"(versione in dollari: '{last['cl_buy_usd']}') · chiusura {last['close']:.0f} · massimo 20 g {last['hi20']:.0f} · minimo 20 g {last['lo20']:.0f}")
        if o:
            sdv = 1 if o["side"] == "long" else -1
            A_spot = (last["close"] > last["hi20"]) if sdv < 0 else (last["close"] < last["lo20"])
            say(f"E-out (non adottata): rottura contraria a 20 g = {bool(A_spot)}; guidata dallo spot = {(last['cl_buy'] if sdv < 0 else last['cl_sell']) == 'spot'}")
        f.loc["2026-11-01":].to_csv(D / f"{a}_stato.csv")
    (HERE / "oggi.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
