"""Opzioni · fase 1 · SOLO conteggi dei segnali F3 (nessun P&L). Uso: python3 research/opzioni_studio/op_count.py → conteggi.txt

Per ogni segnale e soglia candidata: settimane attive e operazioni (una posizione per volta, ingresso il lunedì dopo la
domenica del segnale, tenuta fino al venerdì più vicino a 30 giorni o al segnale contrario; dopo la scadenza si rientra al
lunedì successivo se il segnale vale ancora), per anno, per lato, IS 2018–21 / OOS 2022–26; sovrapposizione con W3.2;
quota del tempo in posizione. Le scadenze sono teoriche (ogni venerdì): nel 2018–19 Deribit quotava meno scadenze.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import op_engine as E  # noqa: E402
import op_segnali as S  # noqa: E402

C = HERE / "cache"
OUT = []


def say(s: str = "") -> None:
    print(s)
    OUT.append(s)


def load():
    w = pd.read_csv(C / "op_settimanale.csv", index_col=0, parse_dates=True)
    w = w[w.index >= "2018-01-01"]
    t = pd.read_csv(C / "op_w32_trades.csv")
    k = pd.read_csv(C / "op_cono.csv", index_col=0, parse_dates=True).reindex(w.index)
    return w, t, k


def scad_30(monday: pd.Timestamp) -> pd.Timestamp:
    """Venerdì più vicino a 30 giorni (scadenza alle 08:00): dal lunedì è sempre il venerdì a +32 giorni."""
    fr = [monday + pd.Timedelta(days=4 + 7 * j) for j in range(2, 8)]
    return min(fr, key=lambda e: (abs(E.anni(monday, e) * 365 - 30), -e.value))


def occupa(sig: pd.Series, last_day: pd.Timestamp) -> list[dict]:
    """Operazioni (solo date) dalla serie settimanale: +1, −1, 2 (straddle), 0."""
    ops, pos = [], None
    for sun, v in sig.items():
        mon = sun + E.DAY
        if mon > last_day:
            break
        if pos is not None and mon > pos["exp"]:
            pos = None
        if pos is not None and pos["lato"] in (1, -1) and v == -pos["lato"]:
            pos["fine"], pos["motivo"] = mon, "contrario"
            pos = None
        if pos is None and v:
            exp = scad_30(mon)
            pos = dict(entra=mon, lato=int(v), exp=exp, fine=exp, motivo="scadenza")
            ops.append(pos)
    return ops


def cono_vs_premio(w: pd.DataFrame, k: pd.DataFrame) -> pd.DataFrame:
    """F3.f · rapporto valore atteso a 30 giorni secondo il cono / premio pagato (alla pari, IV proxy, costi d'acquisto)."""
    q = k[[c for c in k.columns if c.startswith("q")]].to_numpy()
    rel = np.exp(q)                                  # S_T / S_0 sui 100 quantili equiprobabili
    out = pd.DataFrame(index=w.index)
    T = 30 / 365
    for tipo, pay in (("C", np.maximum(rel - 1, 0)), ("P", np.maximum(1 - rel, 0))):
        ev = pay.mean(axis=1) - E.EXER * pay.astype(bool).mean(axis=1)
        prem = np.array([E.black76(1.0, 1.0, T, v, tipo) if v == v else np.nan for v in w["iv30"]])
        cost = prem * 1.03 + np.minimum(0.0003, 0.125 * prem)
        out[f"r{tipo}"] = ev / cost
    return out


def segnali(w: pd.DataFrame, k: pd.DataFrame) -> dict[str, dict[str, pd.Series]]:
    z = lambda b: b.astype(int)  # noqa: E731
    iv_ok = w["iv30"].notna()
    sig = {"a · tendenza di solo prezzo": {"a1 EMA20 in salita/discesa": w["a_pend"], "a2 EMA20 sopra/sotto SMA40": w["a_pos"]},
           "b · condizioni d'ingresso di W3.2 ogni settimana": {f"b flusso oltre ±{x}σ": w[f"b_{x}"] for x in ("0", "0.5", "1")},
           "c · volatilità a buon mercato → straddle": {
               "c1 IV < RV30": 2 * z(iv_ok & (w["iv_rv"] < 1.0)),
               "c2 IV < 0,9·RV30": 2 * z(iv_ok & (w["iv_rv"] < 0.9)),
               "c3 IV nel quintile basso a 52 sett.": 2 * z(w["iv_pct52"] <= 0.2),
               "c4 IV nel decile basso a 52 sett.": 2 * z(w["iv_pct52"] <= 0.1),
               "c5 c1 oppure c3 (testo del PREREG)": 2 * z((iv_ok & (w["iv_rv"] < 1.0)) | (w["iv_pct52"] <= 0.2))},
           "d · compressione delle bande → straddle": {
               "d1 Bollinger 20s, quintile basso a 52 sett.": 2 * z(w["bbw_pct52"] <= 0.2),
               "d2 decile basso a 52 sett.": 2 * z(w["bbw_pct52"] <= 0.1),
               "d3 quintile basso a 104 sett.": 2 * z(w["bbw_pct104"] <= 0.2),
               "d4 quintile basso su tutta la storia": 2 * z(w["bbw_pctall"] <= 0.2)},
           "e · dopo una cascata → call": {
               "e1 chiusura −10% o peggio": z(w["min_ret_cc"] <= -0.10),
               "e2 chiusura −8% o peggio": z(w["min_ret_cc"] <= -0.08),
               "e3 chiusura −12% o peggio": z(w["min_ret_cc"] <= -0.12),
               "e4 minimo −10% sotto la chiusura precedente": z(w["min_ret_low"] <= -0.10)}}
    r = cono_vs_premio(w, k)
    fsig = {}
    for x in (0.0, 0.2, 0.4, 0.5, 0.6):
        c_ok, p_ok = r["rC"] >= 1 + x, r["rP"] >= 1 + x
        s = np.where(c_ok & p_ok, np.where(r["rC"] >= r["rP"], 1, -1), np.where(c_ok, 1, np.where(p_ok, -1, 0)))
        fsig[f"f valore atteso del cono ≥ premio × {1 + x:.1f}"] = pd.Series(s, w.index)
    sig["f · cono contro premio (IV proxy, provvisorio)"] = fsig
    return sig, r


def stats(ops: list[dict], sig: pd.Series, w32: pd.Series, days: pd.DatetimeIndex) -> dict:
    o = pd.DataFrame(ops)
    if o.empty:
        return {"n": 0}
    o["anno"] = o["entra"].dt.year
    o["meta"] = np.where(o["entra"] <= pd.Timestamp(S.IS_END), "IS", "OOS")
    held = pd.Series(0, index=days)
    for _, x in o.iterrows():
        held[(held.index >= x["entra"]) & (held.index <= x["fine"])] = 1
    ov_entry = [int(w32.get(x["entra"], 0) != 0) for _, x in o.iterrows()]
    same = [int(w32.get(x["entra"], 0) == x["lato"]) for _, x in o.iterrows()]
    both = ((held == 1) & (w32.reindex(days).fillna(0) != 0)).sum()
    return {"n": len(o), "IS": int((o["meta"] == "IS").sum()), "OOS": int((o["meta"] == "OOS").sum()),
            "long": int((o["lato"] == 1).sum()), "short": int((o["lato"] == -1).sum()), "straddle": int((o["lato"] == 2).sum()),
            "IS_lati": o[o["meta"] == "IS"]["lato"].value_counts().to_dict(),
            "OOS_lati": o[o["meta"] == "OOS"]["lato"].value_counts().to_dict(),
            "per_anno": o["anno"].value_counts().sort_index().to_dict(),
            "sett_attive": int((sig != 0).sum()),
            "con_w32_in_pos": round(float(np.mean(ov_entry)), 2), "stesso_lato_w32": round(float(np.mean(same)), 2),
            "tempo_in_pos": round(float(held.mean()), 2),
            "giorni_sovrapposti_su_giorni_op": round(float(both / max(held.sum(), 1)), 2),
            "contrari": int((o["motivo"] == "contrario").sum())}


def main() -> None:
    w, t, k = load()
    last = pd.Timestamp(S.frame().index[-1])
    days = pd.date_range("2018-01-01", last)
    w32 = S.w32_in_pos(t, days, last)
    sig, r = segnali(w, k)
    say("CONTEGGI DEI SEGNALI F3 (fase 1: nessun P&L). Decisione alla domenica, ingresso lunedì, opzione ≈30 giorni.")
    say(f"Settimane di decisione: {w.index[0].date()} → {w.index[-1].date()} ({len(w)}); dati giornalieri fino al {last.date()}.")
    say("IS = ingressi 2018-01 → 2021-12, OOS = 2022-01 → 2026-11. Lati: 1 call, −1 put, 2 straddle.")
    say("con_w32 = quota delle operazioni aperte mentre W3.2 è in posizione; stesso_lato = W3.2 in posizione dallo stesso lato;")
    say("sovrapp. = giorni in opzione con W3.2 in posizione / giorni in opzione; tempo = quota dei giorni 2018→oggi in posizione.")
    say(f"Riferimento W3.2: {len(t)} operazioni dal 2018 (IS {int((pd.to_datetime(t['entry']) <= S.IS_END).sum())}, "
        f"OOS {int((pd.to_datetime(t['entry']) > S.IS_END).sum())}); tempo in posizione {float((w32 != 0).mean()):.2f}.")
    say("Copertura dei dati: flusso perp vero dal 2020-04-12 (prima proxy CVD spot), funding dal 2020-01-01, IV proxy dal "
        f"{w['iv30'].first_valid_index().date()} (DVOL dal 2021-03-24), quintile IV a 52 sett. dal "
        f"{w['iv_pct52'].first_valid_index().date()}; liquidazioni solo dal 2026-10-30 (non usabili).")
    rows = []
    for fam, d in sig.items():
        say("")
        say(f"== {fam}")
        say(f"{'candidata':<48}{'op':>4}{'IS':>4}{'OOS':>5}{'call':>5}{'put':>5}{'str':>5}{'sett':>6}{'con_w32':>8}{'st.lato':>8}"
            f"{'sovrapp':>8}{'tempo':>7}{'contr':>6}  per anno")
        for name, s in d.items():
            st = stats(occupa(s, last), s, w32, days)
            if st["n"] == 0:
                say(f"{name:<48}   0")
                continue
            say(f"{name:<48}{st['n']:>4}{st['IS']:>4}{st['OOS']:>5}{st['long']:>5}{st['short']:>5}{st['straddle']:>5}"
                f"{st['sett_attive']:>6}{st['con_w32_in_pos']:>8.2f}{st['stesso_lato_w32']:>8.2f}"
                f"{st['giorni_sovrapposti_su_giorni_op']:>8.2f}{st['tempo_in_pos']:>7.2f}{st['contrari']:>6}  "
                + " ".join(f"{y % 100:02d}:{n}" for y, n in st["per_anno"].items()))
            say(f"{'':<48}IS per lato {st['IS_lati']} · OOS per lato {st['OOS_lati']}")
            rows.append(dict(famiglia=fam[0], candidata=name, **{k_: v for k_, v in st.items() if not isinstance(v, dict)}))
    pd.DataFrame(rows).to_csv(C / "op_conteggi.csv", index=False)
    say("")
    say("== F3.f · distribuzione del rapporto valore atteso del cono / premio (alla pari, 30 g, IV proxy)")
    for tipo in ("C", "P"):
        x = r[f"r{tipo}"].dropna()
        say(f"{'call' if tipo == 'C' else 'put '}: n {len(x)} · quantili 10/25/50/75/90% "
            + " / ".join(f"{v:.2f}" for v in x.quantile([.1, .25, .5, .75, .9])) + f" · quota ≥ 1: {(x >= 1).mean():.2f}")
    say("Nota: la deriva storica del cono (media dei rendimenti giornalieri dal 2014, ~+0,10–0,15%/giorno, ~+3–5% a 30 giorni) rende "
        "le call sistematicamente 'convenienti' e le put 'care': F3.f è in gran parte una call permanente.")
    say("")
    say("Come si confronteranno cono e premio in fase 2 (nessun rendimento calcolato qui): alla domenica, per il contratto che")
    say("si comprerebbe lunedì (scadenza reale scelta dal motore, T giorni; prezzo d'esercizio sulla griglia reale), il cono di")
    say("radar/cone.py è ricalcolato con la sola storia fino alla domenica e con orizzonte T (cone.simulate(horizon=T)); il valore")
    say("atteso è la media del valore intrinseco a scadenza sui cammini, meno l'esercizio 0,02%; il costo è il premio della")
    say("superficie del lunedì × 1,03 + commissione. Segnale se valore atteso / costo ≥ soglia (call o put; se entrambe, la")
    say("maggiore). La qualità del confronto dipende dalla IV della superficie: qui è usata la IV proxy (DVOL / alla pari della")
    say("domenica) solo per contare. Il risultato realizzato si misura poi con lo stesso motore delle altre famiglie.")
    (HERE / "conteggi.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
