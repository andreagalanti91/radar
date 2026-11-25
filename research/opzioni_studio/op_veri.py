"""Opzioni · secondo ciclo (ADDENDUM-2 C.2) · B0r con i prezzi degli scambi veri di Deribit.

Per ogni operazione di B0r (contratto scelto dal motore con la finestra 20–50 giorni, ingresso lunedì 12:00 UTC):
- ingresso: lo scambio vero del contratto più vicino alle 12:00 del lunedì entro ±6 ore (prezzo in BTC × indice = USD per 1 BTC);
- uscita prima della scadenza: lo scambio più vicino all'istante d'uscita di B0r (12:00) entro ±6 ore;
- a scadenza: valore intrinseco sul regolamento (Binance 08:00), come il motore;
- senza scambio entro ±6 ore: prezzo della superficie (dichiarato nella colonna "fonte").
Costi del PREREG (3% per lato, commissione 0,03% con tetto 12,5%, esercizio 0,02%). Conto composto 10.000 × Π(1 + 0,05 (m − 1)).
Fonte: API pubblica history.deribit.com (get_last_trades_by_instrument_and_time), cache in cache/deribit_trades/.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import op_engine as E  # noqa: E402
from op_prezzatore import PrezzatoreSuperficie  # noqa: E402

CACHE = HERE / "cache" / "deribit_trades"
URL = ("https://history.deribit.com/api/v2/public/get_last_trades_by_instrument_and_time?instrument_name={}"
       "&start_timestamp={}&end_timestamp={}&count=1000&sorting=asc")
MON = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
FIN = (20, 50)
PERIODI = {"dal 2018": ("2018-01-01", "2099"), "dal 2021": ("2021-01-01", "2099"), "IS 2018–21": ("2018-01-01", "2021-12-31"),
           "OOS 2022–26": ("2022-01-01", "2099")}


def nome(exp: pd.Timestamp, K: float, tipo: str) -> str:
    return f"BTC-{exp.day}{MON[exp.month - 1]}{exp.year % 100:02d}-{int(K)}-{tipo}"


def scambi(inst: str, t: pd.Timestamp, h: int = 6) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{inst}_{t:%Y%m%d%H}.json"
    if p.exists():
        return json.loads(p.read_text())
    a, b = int((t - pd.Timedelta(hours=h)).timestamp() * 1000), int((t + pd.Timedelta(hours=h)).timestamp() * 1000)
    req = urllib.request.Request(URL.format(inst, a, b), headers={"User-Agent": "research-client"})
    with urllib.request.urlopen(req, timeout=30) as r:
        tr = json.loads(r.read())["result"]["trades"]
    p.write_text(json.dumps(tr))
    time.sleep(0.3)
    return tr


def vicino(tr: list[dict], t: pd.Timestamp) -> dict | None:
    if not tr:
        return None
    ms = t.timestamp() * 1000
    return min(tr, key=lambda x: abs(x["timestamp"] - ms))


def main() -> list[str]:
    pz = PrezzatoreSuperficie()
    tr = pd.read_csv(HERE / "cache" / "op_w32_trades.csv")
    days = pd.date_range("2018-01-01", "2026-11-21")
    m = E.Motore(pz, E.Conf(finestra=FIN))
    r = m.simula(E.piano_w32(tr, days), days, "2018-01-01")
    rows = []
    for t in r["trades"]:
        g = t["legs"][0]
        inst = nome(g["exp"], g["K"], g["tipo"])
        t0 = t["entry"] + pd.Timedelta(hours=12)
        x0 = vicino(scambi(inst, t0), t0)
        if x0:
            S0, P0, f0 = x0["index_price"], x0["price"] * x0["index_price"], f"scambio {abs(x0['timestamp'] / 1000 - t0.timestamp()) / 3600:.1f} h"
        else:
            S0, P0, f0 = t["S0"], g["mid0"], "superficie"
        cost = P0 * 1.03 + min(0.0003 * S0, 0.125 * P0)
        if t["motivo"] == "scadenza":
            ST = pz.regolamento(g["exp"])
            iv = max(ST - g["K"], 0) if g["tipo"] == "C" else max(g["K"] - ST, 0)
            val, f1 = iv - min(0.0002 * ST, 0.125 * iv), "scadenza"
        else:
            t1 = t["exit"] + pd.Timedelta(hours=12)
            x1 = vicino(scambi(inst, t1), t1)
            if x1:
                S1, P1, f1 = x1["index_price"], x1["price"] * x1["index_price"], f"scambio {abs(x1['timestamp'] / 1000 - t1.timestamp()) / 3600:.1f} h"
            else:
                S1, P1, f1 = pz.spot(t["exit"]), g["last"], "superficie"
            val = P1 * 0.97 - min(0.0003 * S1, 0.125 * P1)
        rows.append(dict(entra=t["entry"].date(), esce=t["exit"].date(), motivo=t["motivo"], contratto=inst,
                         fonte_ingresso=f0, fonte_uscita=f1, mult_veri=round(max(val, 0) / cost, 4), mult_superficie=round(t["mult"], 4)))
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "b0r_prezzi_veri.csv", index=False)
    out = ["", "== B0r CON PREZZI VERI (scambi Deribit ±6 ore) contro B0r con la superficie · conto composto da 10.000 $, 5% per operazione",
           d.to_string(index=False)]
    ch = d[d["motivo"] != "aperta"]
    for k, (a, b) in PERIODI.items():
        x = ch[(pd.to_datetime(ch["entra"]) >= a) & (pd.to_datetime(ch["entra"]) <= b)]
        cv = 10_000 * float((1 + 0.05 * (x["mult_veri"] - 1)).prod())
        cs = 10_000 * float((1 + 0.05 * (x["mult_superficie"] - 1)).prod())
        out.append(f"{k}: {len(x)} operazioni chiuse · prezzi veri {cv:,.0f} $ · superficie {cs:,.0f} $ · differenza {cv / cs - 1:+.1%}")
    out.append(f"Ingressi da scambio vero: {(d['fonte_ingresso'] != 'superficie').sum()}/{len(d)} · uscite prima della scadenza da scambio "
               f"vero: {((d['fonte_uscita'].str.startswith('scambio'))).sum()}/{(~d['motivo'].isin(['scadenza'])).sum()}")
    print("\n".join(out))
    return out


if __name__ == "__main__":
    main()
