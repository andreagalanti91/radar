"""W3.2 asset ciclo 2 · azioni · CONTEGGI per titolo (nessun rendimento riportato).

Motore: research/multi_asset/ma_lib.py (s1_weekly = segnali W3.2 "solo prezzo": regime SMA40/EMA20, ingresso EMA21, filtro MACD
nei trend >= 16 settimane, niente flusso perp, funding, distribuzione; s1_sim = esecuzione giornaliera, trailing 2,5 ATR,
uscita EMA21; rischio 25% come W3.2: il numero di ingressi non dipende dal rischio). Settimana W-FRI, decisione all'ultima
seduta della settimana, esecuzione all'apertura successiva. Taglio: venerdì 2026-11-20 (ultima settimana completa).
Varianti di flusso (candidati per Q3, NON scelti qui): long solo se flusso > 0, short solo se flusso < 0, flusso letto alla
seduta della decisione (dato disponibile alla chiusura). NaN = nessun ingresso.
Conta: (a) settimane con condizione d'ingresso vera ("segnali grezzi"), (b) ingressi effettivi della simulazione (in posizione
non si rientra), per anno e per lato, dal 2020-01-01 (o da un anno dopo il primo dato, per il riscaldamento).
Uscite: counts.csv (una riga per titolo × variante), counts_by_year.csv, counts.txt.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "multi_asset"))
sys.path.insert(0, str(HERE))
import ma_lib as M  # noqa: E402
import flow as FL  # noqa: E402

CUT = "2026-11-20"
START = "2020-01-01"
RISK = 0.25
VARIANTS = {"prezzo": None, "cmf20": "cmf20", "cmf_w4": "cmf_w4", "obv_slope20": "obv_slope20", "obv_chg20": "obv_chg20",
            "ad_slope20": "ad_slope20"}
D = HERE / "data"


def load(sym: str) -> pd.DataFrame:
    f = pd.read_csv(D / "px" / f"{sym}.csv.gz", index_col=0, parse_dates=True)
    return f[(f.index <= CUT) & f["close"].notna()]


def with_flow(wb: pd.DataFrame, fw: pd.DataFrame, col: str | None) -> pd.DataFrame:
    w = wb.copy()
    if col is None:
        return w
    x = fw[col].reindex(w.index)
    w["long"] = w["long"] & (x > 0).fillna(False)
    w["short"] = w["short"] & (x < 0).fillna(False)
    return w


def count_one(sym: str) -> tuple[list[dict], list[dict], pd.DataFrame]:
    f = load(sym)
    start = max(pd.Timestamp(START), f.index[0] + pd.DateOffset(years=1))
    years = (f.index[-1] - f.index[0]).days / 365.25
    fl = FL.daily(f)
    fw = FL.weekly(f, fl)
    wb = M.s1_weekly(f)
    rows, yrows = [], []
    for v, col in VARIANTS.items():
        w = with_flow(wb, fw, col)
        sel = w[(w["day"] >= start) & (w["day"] <= pd.Timestamp(CUT))]
        r = M.s1_sim(f, start, CUT, risk=RISK, wb=w)       # rendimenti calcolati dal motore ma NON usati né salvati
        ent = [(pd.Timestamp(t["entry"]), t["side"]) for t in r["trades"]]
        if r["open"]:
            ent.append((pd.Timestamp(r["open"]["entry"]), r["open"]["side"]))
        nl, ns = sum(s == "long" for _, s in ent), sum(s == "short" for _, s in ent)
        rows.append(dict(yahoo=sym, variant=v, first=str(f.index[0].date()), last=str(f.index[-1].date()), years=round(years, 2),
                         test_from=str(start.date()), weeks=len(sel), raw_long=int(sel["long"].sum()), raw_short=int(sel["short"].sum()),
                         entries=len(ent), entries_long=nl, entries_short=ns, open_now=(r["open"]["side"] if r["open"] else ""),
                         flow_nan_weeks=int(fw[col].reindex(sel.index).isna().sum()) if col else 0))
        for y in range(2020, int(CUT[:4]) + 1):
            yl = sum(1 for d, s in ent if d.year == y and s == "long")
            ys = sum(1 for d, s in ent if d.year == y and s == "short")
            sy = sel[pd.DatetimeIndex(sel["day"]).year == y]
            yrows.append(dict(yahoo=sym, variant=v, year=y, entries_long=yl, entries_short=ys,
                              raw_long=int(sy["long"].sum()), raw_short=int(sy["short"].sum())))
    fwd = fl.drop(columns=["volume"]).join(f[["close"]], how="left")
    return rows, yrows, (fwd, fw)


if __name__ == "__main__":
    uni = pd.read_csv(HERE / "universe.csv")
    meta = pd.read_csv(D / "meta.csv").set_index("yahoo")
    (D / "flow").mkdir(parents=True, exist_ok=True)
    rows, yrows, errs = [], [], []
    lines = [(s, "primaria") for s in uni["yahoo"].dropna().unique()] + \
            [(s, "USA") for s in uni["yahoo_us"].dropna().unique() if s and s not in set(uni["yahoo"])]
    for sym, line in lines:
        if not (D / "px" / f"{sym}.csv.gz").exists():
            errs.append((sym, "nessun file prezzi"))
            continue
        try:
            f = load(sym)
            if len(f) < 260:
                errs.append((sym, f"meno di un anno di dati ({len(f)} sedute)"))
                continue
            r, y, (fd, fw) = count_one(sym)
            for x in r:
                x["line"] = line
            rows += r
            yrows += y
            fd.drop(columns=["close"]).round(6).to_csv(D / "flow" / f"{sym}_d.csv.gz")
            fw.round({c: 6 for c in fw.columns if c != "day"}).to_csv(D / "flow" / f"{sym}_w.csv.gz")
        except Exception as e:  # noqa: BLE001
            errs.append((sym, f"errore {type(e).__name__}: {e}"))
    c = pd.DataFrame(rows)
    c.to_csv(HERE / "counts.csv", index=False)
    pd.DataFrame(yrows).to_csv(HERE / "counts_by_year.csv", index=False)
    pd.DataFrame(errs, columns=["yahoo", "motivo"]).to_csv(HERE / "counts_esclusi.csv", index=False)
    print(len(c[(c.variant == "prezzo") & (c.line == "primaria")]), "titoli (linea primaria) contati;", len(errs), "esclusi")
    for v in VARIANTS:
        s = c[(c.variant == v) & (c.line == "primaria")]
        print(f"{v:12s} ingressi tot {s.entries.sum():5d} (L {s.entries_long.sum()}, S {s.entries_short.sum()}) · mediana {s.entries.median():.0f}"
              f" · titoli >= 8 ingressi: {(s.entries >= 8).sum()}/{len(s)}")
