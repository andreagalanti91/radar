"""Effetto calendario delle scadenze mensili delle opzioni Deribit su BTC · controllo descrittivo veloce (26/11/2026).

Non preregistrato: risponde alla domanda dell'utente "check dell'OPEX (scadenze delle opzioni, up o down)".
Scadenza mensile Deribit = ultimo venerdì del mese, 08:00 UTC; trimestrali = marzo, giugno, settembre, dicembre.
Controllo = tutti gli altri venerdì (ogni venerdì ha comunque la scadenza settimanale: il confronto misura l'effetto della
scadenza GRANDE contro quella piccola, a parità di giorno della settimana).

Dati: data/spot.csv (BTC giornaliero dal 2019-09, candele UTC) e data/spot_1h.csv (orario dal 2022-02) per le 24 ore attorno
alle 08:00. Il "massimo dolore" storico non è ricostruibile (servirebbe l'open interest per strike del passato): qui si misura
solo l'effetto calendario. `python3 check.py` → risultati.txt
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("risultati.txt")
RNG = np.random.default_rng(7)


def last_friday(y: int, m: int) -> pd.Timestamp:
    d = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0)
    return d - pd.Timedelta(days=(d.weekday() - 4) % 7)


def load():
    d = pd.read_csv(ROOT / "data" / "spot.csv", parse_dates=["date"]).set_index("date").sort_index()
    h = pd.read_csv(ROOT / "data" / "spot_1h.csv", parse_dates=["t"]).set_index("t").sort_index()
    return d, h


def daily_rows(d: pd.DataFrame) -> pd.DataFrame:
    """Per ogni venerdì: rendimento e ampiezza 7 giorni prima (sab–gio), il venerdì, 7 giorni dopo (sab–ven)."""
    C, H, L = d["close"], d["high"], d["low"]
    idx = d.index
    pos = {t: i for i, t in enumerate(idx)}
    rows = []
    for t in idx[idx.weekday == 4]:
        i = pos[t]
        if i < 8 or i + 7 >= len(idx) or (idx[i + 7] - t).days != 7 or (t - idx[i - 8]).days != 8:
            continue
        mf = last_friday(t.year, t.month) == t
        rows.append({
            "date": t, "monthly": mf, "quarterly": mf and t.month in (3, 6, 9, 12),
            "r_pre": C.iloc[i - 1] / C.iloc[i - 8] - 1, "rg_pre": H.iloc[i - 7:i].max() / L.iloc[i - 7:i].min() - 1,
            "r_day": C.iloc[i] / C.iloc[i - 1] - 1, "rg_day": H.iloc[i] / L.iloc[i] - 1,
            "r_post": C.iloc[i + 7] / C.iloc[i] - 1, "rg_post": H.iloc[i + 1:i + 8].max() / L.iloc[i + 1:i + 8].min() - 1,
            "r_post1": C.iloc[i + 1] / C.iloc[i] - 1,
        })
    return pd.DataFrame(rows).set_index("date")


def hourly_rows(h: pd.DataFrame) -> pd.DataFrame:
    """Per ogni venerdì dal 2022: 24 ore prima e 24 ore dopo le 08:00 UTC (rendimento e ampiezza)."""
    rows = []
    for t in pd.date_range(h.index[0].normalize(), h.index[-1].normalize(), freq="W-FRI"):
        t8 = t + pd.Timedelta(hours=8)
        a, b = h.loc[t8 - pd.Timedelta(hours=24):t8 - pd.Timedelta(hours=1)], h.loc[t8:t8 + pd.Timedelta(hours=23)]
        if len(a) < 23 or len(b) < 23:
            continue
        mf = last_friday(t.year, t.month) == t
        p0, p8, p1 = a["open"].iloc[0], b["open"].iloc[0], b["close"].iloc[-1]
        rows.append({"date": t, "monthly": mf, "quarterly": mf and t.month in (3, 6, 9, 12),
                     "r_24pre": p8 / p0 - 1, "rg_24pre": a["high"].max() / a["low"].min() - 1,
                     "r_24post": p1 / p8 - 1, "rg_24post": b["high"].max() / b["low"].min() - 1})
    return pd.DataFrame(rows).set_index("date")


def perm_p(x: np.ndarray, y: np.ndarray, n: int = 20000) -> float:
    """p a due code della differenza delle mediane (permutazione)."""
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    obs = abs(np.median(x) - np.median(y))
    z = np.concatenate([x, y])
    k = len(x)
    cnt = 0
    for _ in range(n):
        RNG.shuffle(z)
        cnt += abs(np.median(z[:k]) - np.median(z[k:])) >= obs
    return (cnt + 1) / (n + 1)


def pct(v: float, d: int = 2) -> str:
    return f"{v * 100:+.{d}f}%"


def block(df: pd.DataFrame, mask: pd.Series, ctrl: pd.Series, cols: list[tuple[str, str, bool]], name: str) -> list[str]:
    ev, co = df[mask], df[ctrl]
    out = [f"\n## {name}: {len(ev)} scadenze contro {len(co)} altri venerdì"]
    out.append(f"{'misura':<34}{'scadenze':>12}{'altri ven.':>12}{'p (mediane)':>13}")
    for c, lab, absval in cols:
        x, y = ev[c].to_numpy(), co[c].to_numpy()
        if absval:
            x, y = np.abs(x), np.abs(y)
        out.append(f"{lab:<34}{pct(np.median(x)):>12}{pct(np.median(y)):>12}{perm_p(x, y):>13.3f}")
    return out


def main() -> None:
    d, h = load()
    D = daily_rows(d)
    Hh = hourly_rows(h)
    other = ~D["monthly"]
    cols = [("r_pre", "rendimento 7 g prima (mediana)", False), ("r_pre", "|rendimento| 7 g prima", True),
            ("rg_pre", "range 7 g prima", False),
            ("r_day", "rendimento del venerdì", False), ("r_day", "|rendimento| del venerdì", True),
            ("rg_day", "range del venerdì", False),
            ("r_post", "rendimento 7 g dopo (mediana)", False), ("r_post", "|rendimento| 7 g dopo", True),
            ("rg_post", "range 7 g dopo", False), ("r_post1", "rendimento del sabato", False)]
    L = [f"Scadenze mensili Deribit su BTC · {D.index[0]:%Y-%m-%d} → {D.index[-1]:%Y-%m-%d} (giornaliero, data/spot.csv)"]
    L += block(D, D["monthly"], other, cols, "Tutte le mensili")
    L += block(D, D["quarterly"], other, cols, "Solo trimestrali")
    L += block(D, D["monthly"] & ~D["quarterly"], other, cols, "Mensili non trimestrali")

    L.append("\n## Direzione")
    for k, m in (("mensili", D["monthly"]), ("trimestrali", D["quarterly"]), ("altri venerdì", other)):
        s = D[m]
        L.append(f"{k:<14} n={len(s):3d}  7 g dopo su {100 * (s.r_post > 0).mean():4.0f}%  (media {pct(s.r_post.mean())})  "
                 f"7 g prima su {100 * (s.r_pre > 0).mean():4.0f}%  venerdì su {100 * (s.r_day > 0).mean():4.0f}%")
    L.append("\n## Inversione dopo la scadenza (il movimento dei 7 giorni prima si gira nei 7 dopo?)")
    for k, m in (("mensili", D["monthly"]), ("altri venerdì", other)):
        s = D[m]
        rev = (np.sign(s.r_pre) != np.sign(s.r_post)).mean()
        L.append(f"{k:<14} segno opposto {100 * rev:4.0f}%  correlazione prima/dopo {s.r_pre.corr(s.r_post):+.2f}")

    L.append(f"\n## 24 ore attorno alle 08:00 UTC · {Hh.index[0]:%Y-%m-%d} → {Hh.index[-1]:%Y-%m-%d} (orario, data/spot_1h.csv)")
    hc = [("r_24pre", "|rendimento| 24 h prima", True), ("rg_24pre", "range 24 h prima", False),
          ("r_24post", "|rendimento| 24 h dopo", True), ("rg_24post", "range 24 h dopo", False),
          ("r_24post", "rendimento 24 h dopo (mediana)", False)]
    L += block(Hh, Hh["monthly"], ~Hh["monthly"], hc, "Mensili (orario)")
    L += block(Hh, Hh["quarterly"], ~Hh["monthly"], hc, "Trimestrali (orario)")

    # per gli anni: stabilità del segno dei 7 giorni dopo
    L.append("\n## Per anno · mensili: mediana 7 g dopo e % su")
    for y, s in D[D["monthly"]].groupby(D[D["monthly"]].index.year):
        L.append(f"{y}  n={len(s):2d}  {pct(s.r_post.median())}  su {100 * (s.r_post > 0).mean():3.0f}%")
    txt = "\n".join(L) + "\n"
    OUT.write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
