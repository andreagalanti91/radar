"""tradera_test · confronto in avanti: ogni nuovo grafico di TraderA → output del rilevatore alla stessa data → confronto.csv.

Procedura (a ogni nuovo screenshot dell'utente):
1. leggere dal grafico: asset, data, timeframe, lato, ingresso, stop, obiettivo, punti della linea, zone;
2. aggiornare i dati (python3 fetch.py; per un'azione nuova: fetch.yahoo_raw("TICKER") salvato in data/<TICKER>_raw.csv.gz);
3. python3 -c "import confronto as K; K.aggiungi(K.confronta(K.dati('LMT'), '2026-11-13', dict(lato='long', ingresso=567.93,
   stop=539.57, obiettivo=688.69, fonte='invio 2, #4')))";
4. quando il piano si chiude, compilare a mano la colonna esito_trader / esito_rilevatore (obiettivo, stop, non eseguito).
confronta() è pura (nessun I/O, nessun dato dopo `data`); aggiungi() scrive una riga.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tt_detect as T  # noqa: E402

CSV = HERE / "confronto.csv"
COLS = ["data", "asset", "timeframe", "fonte", "tr_lato", "tr_ingresso", "tr_stop", "tr_obiettivo", "tr_note",
        "ril_stato", "ril_lato", "ril_data_segnale", "ril_ingresso", "ril_stop", "ril_obiettivo", "ril_rr", "ril_confluenza",
        "ril_linea", "ril_zona_prezzo", "diff_ingresso_pct", "diff_stop_pct", "diff_obiettivo_pct", "esito_trader",
        "esito_rilevatore"]


def dati(asset: str) -> pd.DataFrame:
    import fetch
    if asset in ("BTC", "ETH"):
        return fetch.crypto(asset + "USDT")
    return fetch.stock(asset, raw=True)


def _pct(a, b):
    try:
        return round(100 * (float(a) / float(b) - 1), 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return ""


def confronta(df: pd.DataFrame, data: str, trader: dict, asset: str = "", timeframe: str = "1D", recente: int = 15) -> dict:
    """Riga di confronto: stato del rilevatore alla chiusura di `data` (solo barre ≤ data)."""
    d = df[df.index <= pd.Timestamp(data)]
    r = T.detect(d)
    ix = d.index
    lato = trader.get("lato", "")
    want = 1 if lato == "long" else -1 if lato == "short" else None
    ev = [x for x in r["signals"] + r["flips"] if len(d) - 1 - x["t"] <= recente and (want is None or x["side"] == want)]
    row = {k: "" for k in COLS}
    row.update(data=data, asset=asset, timeframe=timeframe, fonte=trader.get("fonte", ""), tr_lato=lato,
               tr_ingresso=trader.get("ingresso", ""), tr_stop=trader.get("stop", ""), tr_obiettivo=trader.get("obiettivo", ""),
               tr_note=trader.get("note", ""))
    if ev:
        x = ev[-1]
        t = x["t"]
        ent = float(d["open"].iloc[t + 1]) if t + 1 < len(d) else float(x["close"])
        row.update(ril_stato="segnale" if x in r["signals"] else "piano speculare", ril_lato="long" if x["side"] > 0 else "short",
                   ril_data_segnale=str(ix[t].date()), ril_ingresso=round(ent, 2), ril_stop=round(float(x["stop"]), 2),
                   ril_obiettivo=round(float(x["tgt"]), 2), ril_rr=round(float(x.get("rr", float("nan"))), 2),
                   ril_confluenza=x.get("conf", ""),
                   ril_linea=(f"{ix[x['iA']].date()} {x['pA']:.2f} → {ix[x['iB']].date()} {x['pB']:.2f}" if "iA" in x else ""))
    else:
        pend = [q for q in r["pending"] if want is None or q["side"] == want]
        opp = [x for x in r["signals"] if want is not None and x["side"] == -want and len(d) - 1 - x["t"] <= 40]
        if opp:   # piano speculare del segnale opposto recente: scatta con chiusura oltre linea ∓ INV·ATR
            x, t = opp[-1], len(d) - 1
            s = x["side"]
            m = (x["pB"] - x["pA"]) / (x["iB"] - x["iA"])
            lv = x["pA"] + m * (t - x["iA"])
            ext = d["high"].iloc[t - T.P["BASE"] + 1:t + 1].max() if s > 0 else d["low"].iloc[t - T.P["BASE"] + 1:t + 1].min()
            base = d["low"].iloc[x["iB"]:x["ib"] + 1].min() if s > 0 else d["high"].iloc[x["iB"]:x["ib"] + 1].max()
            row.update(ril_stato="speculare in attesa (scatta con chiusura oltre il prezzo indicato)",
                       ril_lato="short" if s > 0 else "long", ril_ingresso=round(float(lv - s * T.P["INV"] * r["atr"][t]), 2),
                       ril_stop=round(float(ext * (1 + s * T.P["MARG"])), 2), ril_obiettivo=round(float(base), 2),
                       ril_linea=f"{ix[x['iA']].date()} {x['pA']:.2f} → {ix[x['iB']].date()} {x['pB']:.2f}")
        elif pend:
            q = pend[0]
            row.update(ril_stato=q["kind"], ril_lato="long" if q["side"] > 0 else "short", ril_ingresso=round(float(q["lv_next"]), 2),
                       ril_stop=round(float(q["stop"]), 2) if "stop" in q else "", ril_obiettivo=round(float(q["tgt"]), 2) if "tgt" in q else "",
                       ril_linea=f"{ix[q['iA']].date()} {q['pA']:.2f} → {ix[q['iB']].date()} {q['pB']:.2f}")
        else:
            row.update(ril_stato="nessun setup")
    c = float(d["close"].iloc[-1])
    z = [x for x in T.zones(d) if x["lo"] * 0.98 <= c <= x["hi"] * 1.02]
    row["ril_zona_prezzo"] = "; ".join(f"{x['lo']:.2f}–{x['hi']:.2f}" for x in z) or "nessuna"
    row.update(diff_ingresso_pct=_pct(row["ril_ingresso"], row["tr_ingresso"]), diff_stop_pct=_pct(row["ril_stop"], row["tr_stop"]),
               diff_obiettivo_pct=_pct(row["ril_obiettivo"], row["tr_obiettivo"]))
    return row


def aggiungi(row: dict, path: Path = CSV) -> None:
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in COLS})


if __name__ == "__main__":
    # registro iniziale: i quattro piani noti al 23/11/2026
    if CSV.exists():
        CSV.unlink()
    aggiungi(confronta(dati("LMT"), "2026-11-13", dict(lato="long", ingresso=567.93, stop=539.57, obiettivo=688.69,
                                                       fonte="invio 2 #4", note="linea mar→ago, ritest a limite"), "LMT"))
    aggiungi(confronta(dati("LMT"), "2026-11-13", dict(lato="short", ingresso=567.65, stop=585.13, obiettivo=499.69,
                                                       fonte="invio 2 #4", note="piano speculare se la linea cede"), "LMT"))
    aggiungi(confronta(dati("NVDA"), "2026-11-19", dict(lato="", fonte="invio 1 #3",
                                                        note="zone 140–150, 88–95, 44–50, 29–33; prezzo 145,98"), "NVDA"))
    aggiungi(confronta(dati("BTC"), "2026-11-21", dict(lato="long", ingresso=55777.53, fonte="invio 1 #1",
                                                       note="acquisto eseguito 7 BTC; stop e obiettivo non noti"), "BTC"))
    print(pd.read_csv(CSV).T.to_string())
