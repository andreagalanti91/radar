"""Previsionale 2 · parte DESCRITTIVA (PREREG §7): come si è comportato BTC nelle fasi di politica economica e nei regimi di
mercato dal 2015. Descrizione, non previsione. Uso: python3 research/previsionale2/p2_descr.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from p2_data import build  # noqa: E402

START = "2015-01-01"
# Fasi storiche: date dei cambi di tasso lette da DFF (giorno dopo la decisione) — definite a posteriori, solo descrittive.
FASI = [("Tasso a zero, prima dei rialzi", "2015-01-01", "2015-12-16"),
        ("Rialzi 2015–18 (QT da 10/2017)", "2015-12-17", "2018-12-19"),
        ("Pausa 2019 (QT fino a 08/2019)", "2018-12-20", "2019-07-31"),
        ("Tagli 2019 (bilancio risale da 09/2019)", "2019-08-01", "2020-03-03"),
        ("Emergenza: tasso zero + QE 2020–22", "2020-03-04", "2022-03-16"),
        ("Rialzi 2022–23 (QT da 06/2022)", "2022-03-17", "2023-07-26"),
        ("Plateau 5,3% + QT 2023–24", "2023-07-27", "2024-09-18"),
        ("Tagli 2024–25", "2024-09-19", "2025-12-10"),
        ("Fermo ~3,6%, bilancio stabile 2026", "2025-12-11", "2026-09-16"),
        ("Rialzo 09/2026 → oggi", "2026-09-17", "2026-11-15")]
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def runs(mask: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    m = mask.to_numpy()
    idx, out, i = mask.index, [], 0
    while i < len(m):
        if m[i]:
            j = i
            while j + 1 < len(m) and m[j + 1]:
                j += 1
            out.append((idx[i], idx[j]))
            i = j + 1
        else:
            i += 1
    return out


def row(d: pd.DataFrame, mask: pd.Series, name: str) -> dict:
    c = d["close"]
    rr = runs(mask)
    long = [r for r in rr if (r[1] - r[0]).days + 1 >= 30]
    dd = min(((c[a:b] / c[a:b].cummax() - 1).min() for a, b in rr), default=np.nan)
    q = d[mask]
    nind = sum(((b - a).days + 1) // 30 for a, b in rr)
    return dict(stato=name, giorni=int(mask.sum()), episodi=len(rr), episodi_30g=len(long), finestre_30g=int(nind),
                r30_media=q["f30"].mean() * 100, r30_mediana=q["f30"].median() * 100, su30=q["f30"].gt(0).where(q["f30"].notna()).mean() * 100,
                su7=q["f7"].gt(0).where(q["f7"].notna()).mean() * 100, dd_max=dd * 100)


def table(d, groups: dict, title: str) -> pd.DataFrame:
    t = pd.DataFrame([row(d, m, k) for k, m in groups.items()])
    say("\n" + title)
    say(t.round(1).to_string(index=False))
    return t.assign(tabella=title)


def main() -> None:
    d = build()
    d["f30"] = d["close"].shift(-30) / d["close"] - 1
    d["f7"] = d["close"].shift(-7) / d["close"] - 1
    d = d[d.index >= START]
    al = pd.Series(True, index=d.index)
    say(f"BTC {START} → {d.index[-1].date()}: tutti i giorni")
    T = [table(d, {"Tutti i giorni": al}, "0. Riferimento")]
    # fasi storiche (una riga = UN episodio)
    rows = []
    for name, a, b in FASI:
        m = pd.Series((d.index >= a) & (d.index <= b), index=d.index)
        r = row(d, m, f"{name} [{a[:7]} → {b[:7]}]")
        c = d.loc[m, "close"]
        r["btc_fase"] = (c.iloc[-1] / c.iloc[0] - 1) * 100
        r["dff"] = f"{d.loc[m, 'dff'].iloc[0]:.2f}→{d.loc[m, 'dff'].iloc[-1]:.2f}"
        r["bilancio_mld"] = f"{d.loc[m, 'walcl'].iloc[0] / 1e6:.2f}→{d.loc[m, 'walcl'].iloc[-1] / 1e6:.2f}"
        rows.append(r)
    t = pd.DataFrame(rows)
    say("\n1. Fasi storiche della Fed (definite a posteriori; ogni riga è UN solo episodio)")
    say(t.round(1).to_string(index=False))
    T.append(t.assign(tabella="1. Fasi storiche"))
    tasso = pd.Series(np.where(d["pol"] > 0.125, "RIALZO", np.where(d["pol"] < -0.125, "TAGLIO", "FERMO")), index=d.index)
    bil = pd.Series(np.where(d["walcl13"] > 1, "QE", np.where(d["walcl13"] < -1, "QT", "STABILE")), index=d.index)
    T.append(table(d, {k: tasso == k for k in ("RIALZO", "FERMO", "TAGLIO")}, "2. Direzione del tasso (meccanica, nota in tempo reale: DFF contro 126 giorni prima, ±0,125)"))
    T.append(table(d, {k: bil == k for k in ("QE", "STABILE", "QT")}, "3. Bilancio Fed (meccanica: WALCL a 91 giorni, ±1%)"))
    T.append(table(d, {f"{a} + {b}": (tasso == a) & (bil == b) for a in ("RIALZO", "FERMO", "TAGLIO") for b in ("QE", "STABILE", "QT")
                       if ((tasso == a) & (bil == b)).sum() >= 60}, "4. Tasso × bilancio (celle con ≥ 60 giorni)"))
    T.append(table(d, {"liquidità netta in aumento (nl13 > 0)": d["nl13"] > 0, "liquidità netta in calo": d["nl13"] <= 0,
                       "restrittiva: tasso su + liquidità giù": (d["pol"] > 0) & (d["nl13"] < 0),
                       "rendimento reale in salita (dry > 0)": d["dry"] > 0, "rendimento reale in discesa": d["dry"] <= 0,
                       "dollaro in salita (usd > 0)": d["usd"] > 0, "dollaro in discesa": d["usd"] <= 0,
                       "curva invertita (10a − 2a < 0)": d["curva"] < 0, "curva positiva": d["curva"] >= 0,
                       "VIX > 25": d["vixlvl"] > 25, "VIX ≤ 25": d["vixlvl"] <= 25,
                       "CPI annuo in salita": d["cpi"] > 0, "CPI annuo in discesa": d["cpi"] < 0,
                       "FOMC entro 7 giorni": d["fomc"] > 0, "nessun FOMC entro 7 giorni": d["fomc"] == 0},
                   "5. Altre condizioni di politica economica (meccaniche, con i ritardi di pubblicazione)"))
    T.append(table(d, {"T=U rialzo (sopra SMA200 in salita)": d["T"] == "U", "T=M misto": d["T"] == "M", "T=D ribasso": d["T"] == "D",
                       "V=A volatilità alta": d["V"] == "A", "V=B volatilità bassa": d["V"] == "B",
                       **{f"T={a} · V={b}": (d["T"] == a) & (d["V"] == b) for a in "UMD" for b in "AB"}},
                   "6. Regimi di mercato (meccanici)"))
    # stabilità nel tempo delle condizioni principali: rendimento medio a 30 g per sotto-periodo (ON − OFF)
    say("\n7. Stabilità: differenza del rendimento medio a 30 giorni (condizione vera − falsa), punti %, per sotto-periodo")
    conds = {"tasso in RIALZO": tasso == "RIALZO", "tasso in TAGLIO": tasso == "TAGLIO", "bilancio QE": bil == "QE", "bilancio QT": bil == "QT",
             "liquidità netta in aumento": d["nl13"] > 0, "rend. reale in salita": d["dry"] > 0, "dollaro in salita": d["usd"] > 0,
             "curva invertita": d["curva"] < 0, "VIX > 25": d["vixlvl"] > 25, "CPI in salita": d["cpi"] > 0,
             "T=U": d["T"] == "U", "T=D": d["T"] == "D", "V=A": d["V"] == "A"}
    per = {"2015–17": ("2015", "2017"), "2018–20": ("2018", "2020"), "2021–23": ("2021", "2023"), "2024–26": ("2024", "2026")}
    st = []
    for k, m in conds.items():
        r = {"condizione": k}
        for pn, (a, b) in per.items():
            q, mm = d.loc[a:b], m.loc[a:b]
            r[pn] = (q.loc[mm, "f30"].mean() - q.loc[~mm, "f30"].mean()) * 100 if mm.sum() >= 30 and (~mm).sum() >= 30 else np.nan
            r[f"g_{pn}"] = int(mm.sum())
        v = [r[p] for p in per if np.isfinite(r[p])]
        r["stesso_segno"] = f"{max(sum(x > 0 for x in v), sum(x < 0 for x in v))}/{len(v)}"
        st.append(r)
    st = pd.DataFrame(st)
    say(st.round(1).to_string(index=False))
    pd.concat(T).to_csv(HERE / "descrittiva.csv", index=False, float_format="%.2f")
    st.to_csv(HERE / "descrittiva_stabilita.csv", index=False, float_format="%.2f")
    (HERE / "risultati_descrittiva.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
