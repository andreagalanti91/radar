"""Fase 1 (nessun rendimento): MACD settimanale 12/26/9 su SOL, conteggi di settimane e segnali per variante.
Uso: python -I research/macd_sol/conteggi.py  (dalla radice del repo)."""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "research/w32_asset2/crypto/data/SOL_spot.csv.gz"
P_IS = 32.11          # mediana close settimanali 12/04/2020–25/12/2022 (PREREG §2)
WARM = 35             # prima candela utilizzabile (26 + 9)
LO, HI, SELL = -50.0, -3.0, 10.0


def md(df, index=True):
    """Tabella markdown senza dipendenze (tabulate non è installato)."""
    df = df.reset_index() if index else df
    fmt = lambda x: (f"{x:g}" if isinstance(x, float) else str(x.date()) if hasattr(x, "date") else str(x))
    rows = [" | ".join(map(str, df.columns))] + [" | ".join("---" for _ in df.columns)]
    rows += [" | ".join(fmt(x) for x in r) for r in df.itertuples(index=False)]
    return "\n".join("| " + r + " |" for r in rows)


def bars():
    f = pd.read_csv(SRC, parse_dates=["date"], index_col="date")
    w = f[["open", "high", "low", "close"]].resample("W-SUN").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"})
    w = w[w.index <= f.index[-1]].copy()
    c = w["close"]
    w["line"] = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    w["sig"] = w["line"].ewm(span=9, adjust=False).mean()
    w["hist"] = w["line"] - w["sig"]
    w["line_n"] = w["line"] * P_IS / c
    w["pct"] = 100 * w["line"] / c
    w["ok"] = False
    w.iloc[WARM - 1:, w.columns.get_loc("ok")] = True
    return f, w


def run(w, buy, sell):
    """Sequenza di ingressi/uscite (date di decisione domenicale) senza prezzi d'esecuzione né rendimenti."""
    pos, ev = False, []
    for d, r in w[w["ok"]].iterrows():
        if not pos and buy.loc[d]:
            pos = True; ev.append((d, "entrata"))
        elif pos and sell.loc[d]:
            pos = False; ev.append((d, "uscita"))
    return ev


def main():
    f, w = bars()
    v = w[w["ok"]]
    band = lambda s: (s >= LO) & (s <= HI)
    cross = (w["line"] > w["sig"]) & (w["line"].shift() <= w["sig"].shift())
    var = {
        "R1 letterale": (band(w["line"]), w["line"] >= SELL),
        "R2 ripartenza": (cross & band(w["line"]), w["line"] >= SELL),
        "R3 istogramma": (band(w["hist"]), w["hist"] >= SELL),
        "R4 normalizzata": (band(w["line_n"]), w["line_n"] >= SELL),
        "Rif. flip solo long (lez. 79)": (cross, (w["line"] < w["sig"]) & (w["line"].shift() >= w["sig"].shift())),
    }
    out = []
    p = out.append
    p(f"Dati: {f.index[0].date()} → {f.index[-1].date()}; candele W-SUN {w.index[0].date()} → {w.index[-1].date()} ({len(w)});"
      f" utilizzabili dal {v.index[0].date()} ({len(v)} settimane)")
    yr = v.index.year
    t = pd.DataFrame({
        "settimane": v.groupby(yr).size(),
        "close min": v.groupby(yr)["close"].min().round(2),
        "close mediana": v.groupby(yr)["close"].median().round(2),
        "close max": v.groupby(yr)["close"].max().round(2),
        "linea in [-50,-3]": band(v["line"]).groupby(yr).sum(),
        "linea >= +10": (v["line"] >= SELL).groupby(yr).sum(),
        "linea < -50": (v["line"] < LO).groupby(yr).sum(),
        "ist in [-50,-3]": band(v["hist"]).groupby(yr).sum(),
        "ist >= +10": (v["hist"] >= SELL).groupby(yr).sum(),
        "lin_n in banda": band(v["line_n"]).groupby(yr).sum(),
        "lin_n >= +10": (v["line_n"] >= SELL).groupby(yr).sum(),
        "incroci rialzo in banda": (cross & band(w["line"]))[v.index].groupby(yr).sum(),
    })
    t.loc["Totale"] = t.sum(numeric_only=True)
    for col in ["close min", "close mediana", "close max"]:
        t.loc["Totale", col] = {"close min": v["close"].min(), "close mediana": v["close"].median(),
                                "close max": v["close"].max()}[col]
    p("\n## Settimane per anno (dalla prima utilizzabile)\n" + md(t))

    q = [0, .05, .25, .5, .75, .95, 1]
    d = pd.DataFrame({k: v[k].quantile(q).round(2) for k in ["line", "hist", "pct"]})
    d.index = ["min", "p5", "p25", "mediana", "p75", "p95", "max"]
    d.columns = ["linea MACD $", "istogramma $", "linea % del prezzo"]
    p("\n## Distribuzione (settimane utilizzabili)\n" + md(d))
    g = v.groupby(yr).agg(lin_min=("line", "min"), lin_max=("line", "max"), pct_min=("pct", "min"),
                          pct_max=("pct", "max"), ist_min=("hist", "min"), ist_max=("hist", "max")).round(2)
    p("\n## Estremi per anno (linea $, linea % prezzo, istogramma $)\n" + md(g))
    # peso relativo delle soglie assolute a prezzi diversi
    rows = [{"prezzo $": px, "-3 $ in % prezzo": round(-300 / px, 2), "-50 $ in %": round(-5000 / px, 1),
             "+10 $ in %": round(1000 / px, 2)} for px in [2, 20, 32.11, 100, 200]]
    p("\n## Peso delle soglie assolute a prezzi diversi\n" + md(pd.DataFrame(rows), index=False))
    p(f"\nR4: P_IS = {P_IS} $ → compra con linea/close in [{-5000/P_IS:.1f}%, {-300/P_IS:.2f}%], vende con linea/close ≥ {1000/P_IS:.1f}%")

    p("\n## Ingressi/uscite per variante (date di decisione, solo conteggi)")
    tab = {}
    for name, (b, s) in var.items():
        ev = run(w, b, s)
        e = pd.Series([x[0].year for x in ev if x[1] == "entrata"]).value_counts()
        u = pd.Series([x[0].year for x in ev if x[1] == "uscita"]).value_counts()
        tab[name + " · entrate"] = e
        tab[name + " · uscite"] = u
        aperto = "sì" if ev and ev[-1][1] == "entrata" else "no"
        if not name.startswith("Rif"):
            p(f"- {name}: {sum(1 for x in ev if x[1]=='entrata')} entrate, {sum(1 for x in ev if x[1]=='uscita')} uscite,"
              f" posizione aperta a fine dati: {aperto}; sequenza: " + ", ".join(f"{x[1][0].upper()} {x[0].date()}" for x in ev))
        else:
            p(f"- {name}: {sum(1 for x in ev if x[1]=='entrata')} entrate, aperta a fine dati: {aperto}")
    tt = pd.DataFrame(tab).fillna(0).astype(int).sort_index()
    tt.loc["Totale"] = tt.sum()
    p("\n" + md(tt.T))
    txt = "\n".join(out)
    (ROOT / "research/macd_sol/conteggi_output.txt").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
