"""Studio A1: dati provvisori OKX contro definitivi Binance nelle decisioni domenicali di W3.2 (BTC).

Ricostruisce, per ogni domenica, i valori che il tool avrebbe usato al primo giro del lunedì (00:03–01:07 UTC) con la stessa
logica di radar/data.py e radar/features.py, li confronta con i definitivi e conta le decisioni W3.2 cambiate.
Non modifica radar/ né data/: importa radar.features e radar.weekly in sola lettura.

Uso: python3 -I analysis.py RAW REPO   (RAW = uscita di collect.py e funding_rebuild.py; REPO = CSV del tool dal ramo dati)
Uscite (in questa cartella): flow_scenarios.csv, funding_sundays.csv, funding_daily.csv, decisions_*.csv, summary.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE))
from radar import features, weekly  # noqa: E402
import funding_rebuild as fr  # noqa: E402

FLOW_FROM = pd.Timestamp("2022-05-15")       # prima domenica con la taker share delle metrics continua (manca fino al 08/05/2022)
ARCH_END_FUND = pd.Timestamp("2026-10-31")   # ultimo giorno del funding nell'archivio mensile Binance
OUT = HERE
LOG: list[str] = []


def say(*a) -> None:
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


# ------------------------------------------------------------------ caricamento
def load(raw: Path, repo: Path) -> dict:
    rd = {n: pd.read_csv(repo / f"{n}.csv", index_col=0, parse_dates=True) for n in ["spot", "perp", "funding", "metrics", "fng"]}
    perp = rd["perp"]
    rd["perp"] = perp[perp["source"].fillna("binance") == "binance"].drop(columns=["source"])
    fund = rd["funding"]
    fb = fund[(fund["source"] == "binance") & (fund.index <= ARCH_END_FUND)]["funding"]
    reb8 = pd.read_csv(raw / "binance_funding_rebuilt_8h.csv", index_col=0, parse_dates=True)["rate"]
    reb = fr.daily(reb8)
    # funding "definitivo": archivio Binance fino al 31/10, poi ricostruito dall'indice di premio (stima, err p95 fund7 ~1e-5)
    fdef = pd.concat([fb, reb[reb.index > ARCH_END_FUND]])
    okx1d = pd.read_csv(raw / "okx_perp_1d.csv", index_col=0, parse_dates=True)
    okxf = pd.read_csv(raw / "okx_funding_8h.csv", parse_dates=["t"]).set_index("t")["realizedRate"]
    return dict(rd=rd, fdef=fdef, reb8=reb8, okx1d=okx1d, okxf8=okxf, okxf=okxf.groupby(okxf.index.normalize()).sum())


def frame(rd: dict, funding: pd.Series) -> pd.DataFrame:
    d = dict(rd)
    d["funding"] = funding.to_frame("funding")
    f = features.build_features(d)
    return f[f["close"].notna()]


def pf14z(vol: pd.Series, tb: pd.Series, idx: pd.DatetimeIndex) -> pd.Series:
    """Stessa costruzione di features.build_features (perp_flow14 → z su 180 giorni)."""
    vol, tb = vol.reindex(idx), tb.reindex(idx)
    delta = 2 * tb - vol
    fl = delta.rolling(14).sum() / vol.rolling(14).sum()
    return features._z(fl, 180)


# ------------------------------------------------------------------ flusso: scenari di ritardo e correzioni
def flow_scenarios(D: dict, f: pd.DataFrame) -> pd.DataFrame:
    perp, m, okx = D["rd"]["perp"], D["rd"]["metrics"], D["okx1d"]
    idx = f.index
    share = m["taker_buy_share"].reindex(idx)
    vol_b = perp["volume"].reindex(idx)
    tb_b = perp["taker_buy_volume"].reindex(idx)
    vol_o = okx["volCcy"].reindex(idx)
    act_share = tb_b / vol_b
    base = pf14z(vol_b, tb_b, idx)
    chk = (base - f["pf14z"]).abs().max()
    say(f"[controllo] pf14z ricostruito = build_features: scarto massimo {chk:.2e}")
    rows = []
    sundays = [s for s in idx if s.dayofweek == 6 and s >= FLOW_FROM]
    for S in sundays:
        i = idx.get_loc(S)
        win = idx[i - 3:i]                                # gio, ven, sab (live_flow)
        flow_def = float(base.loc[win].mean())
        for k in (1, 2, 3):
            okx_days = idx[i - k:i + 1]                   # ultimi k giorni prima della domenica + domenica
            ref = idx[max(0, i - k - 28):i - k]           # 28 giorni prima, con entrambe le fonti
            ratio = float((vol_b.loc[ref] / vol_o.loc[ref]).median())
            sbias = float((act_share.loc[ref] - share.loc[ref]).median())
            variants = {
                "P0_attuale": (vol_o, share),
                "P1_volume_scalato": (vol_o * ratio, share),
                "P2_scalato_taker_corretto": (vol_o * ratio, share + sbias),
            }
            rec = dict(date=S, k=k, flow_def=flow_def, ratio=ratio, share_bias=sbias)
            sl = slice(idx[max(0, i - 200)], S)            # basta la storia necessaria allo z a 180 giorni
            for name, (vo, sh) in variants.items():
                v, t = vol_b.loc[sl].copy(), tb_b.loc[sl].copy()
                v.loc[okx_days] = vo.loc[okx_days]
                t.loc[okx_days] = (vo * sh).loc[okx_days]
                z = pf14z(v, t, v.index)
                rec[name] = float(z.loc[win].mean())
            # P3: nessun dato OKX nel flusso: i pf14z con OKX nella finestra di 14 giorni restano vuoti
            v, t = vol_b.loc[sl].copy(), tb_b.loc[sl].copy()
            v.loc[okx_days], t.loc[okx_days] = np.nan, np.nan
            z = pf14z(v, t, v.index).loc[win]
            rec["P3_solo_definitivi"] = float(z.mean()) if z.notna().sum() >= 2 else np.nan
            rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "flow_scenarios.csv", index=False)
    return out


# ------------------------------------------------------------------ funding: provvisorio al giro del lunedì
def archived_until(T: pd.Timestamp) -> pd.Timestamp:
    """Ultimo giorno coperto dall'archivio mensile del funding al momento T (file del mese pubblicato il 1° alle ~08:30)."""
    first = T.normalize().replace(day=1)
    prev_end = first - pd.Timedelta(days=1)
    if T >= first + pd.Timedelta(hours=8, minutes=30):
        return prev_end
    return (prev_end.replace(day=1)) - pd.Timedelta(days=1)


def funding_sundays(D: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    fdef, okxf, okxf8, reb8 = D["fdef"], D["okxf"], D["okxf8"], D["reb8"]
    first_okx = okxf.index.min() + pd.Timedelta(days=1)    # primo giorno OKX completo
    rows = []
    for S in pd.date_range("2026-08-30", fdef.index.max(), freq="W-SUN"):
        T = S + pd.Timedelta(days=1, minutes=7)            # primo giro utile del lunedì
        au = archived_until(T)
        days = pd.date_range(S - pd.Timedelta(days=6), S)
        if days[0] < first_okx:
            continue
        defn = fdef.reindex(days)
        f0 = pd.Series([fdef[d] if d <= au else okxf.get(d, np.nan) for d in days], index=days)
        # F1: ricostruzione Binance dall'indice di premio giornaliero (file del giorno d pubblicato il giorno dopo ~08:40:
        # al lunedì 00:07 mancano i pagamenti delle 08:00 e 16:00 della domenica → per quelli il tasso OKX dello stesso pagamento)
        pays = pd.date_range(days[0], S + pd.Timedelta(hours=16), freq="8h")
        r = []
        for p in pays:
            prem_day = (p - pd.Timedelta(minutes=1)).normalize()   # giorno dei premi del periodo
            ok = prem_day < S                                       # file del sabato sì, della domenica no
            r.append(reb8.get(p, np.nan) if ok else okxf8.get(p, np.nan))
        r = pd.Series(r, index=pays)
        f1 = pd.Series([fdef[d] if d <= au else r[r.index.normalize() == d].sum() for d in days], index=days)
        # F1b: come F1 ma si attende il file della domenica (giro del lunedì dopo le ~11:00 UTC)
        f1b = pd.Series([fdef[d] if d <= au else reb8[reb8.index.normalize() == d].sum() for d in days], index=days)
        # F2: OKX + scarto medio Binance−OKX dei 28 giorni precedenti già definitivi (archivio o ricostruzione)
        ref = pd.date_range(S - pd.Timedelta(days=34), S - pd.Timedelta(days=7))
        bias = float((fdef.reindex(ref) - okxf.reindex(ref)).median())
        f2 = pd.Series([fdef[d] if d <= au else okxf.get(d, np.nan) + bias for d in days], index=days)
        rows.append(dict(date=S, okx_days=int((days > au).sum()), fund7_def=defn.mean(), F0_attuale=f0.mean(),
                         F1_premio_binance=f1.mean(), F1b_premio_attesa=f1b.mean(), F2_okx_piu_scarto=f2.mean(),
                         bias=bias))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "funding_sundays.csv", index=False)
    j = pd.concat([fdef.rename("def"), okxf.rename("okx"), fr.daily(reb8).rename("rebuilt")], axis=1, sort=True).dropna()
    j = j[j.index >= first_okx]
    j.to_csv(OUT / "funding_daily.csv")
    return out, j


# ------------------------------------------------------------------ decisioni
def inject(w: pd.DataFrame, vals: dict) -> pd.DataFrame:
    """Sostituisce flow/fund7 delle domeniche in `vals` e ricalcola i segnali con le stesse regole di weekly.weekly_bars."""
    w = w.copy()
    for S, v in vals.items():
        if S in w.index:
            for k, x in v.items():
                w.at[S, k] = x
    c = w["close"]
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    w["long"] = (up & (c > w["ema21"]) & (w["flow"] > 0) & w["f1_ok"]).fillna(False)
    w["short"] = (dn & (c < w["ema21"]) & (w["flow"] < 0)).fillna(False)
    w["dist_long"] = ((w["fund7"] > weekly.FUND_HOT) & (w["flow"] < 0)).fillna(False)
    w["dist_short"] = ((w["fund7"] < weekly.FUND_COLD) & (w["flow"] > 0)).fillna(False)
    return w


def simulate_with(f: pd.DataFrame, vals: dict) -> dict:
    orig = weekly.weekly_bars
    weekly.weekly_bars = lambda ff: inject(orig(ff), vals)
    try:
        return weekly.simulate(f)
    finally:
        weekly.weekly_bars = orig


def side_series(trades: list[dict], sundays) -> dict:
    out = {}
    for S in sundays:
        s = str(S.date())
        out[S] = 0
        for t in trades:
            if t["entry"] <= s and (not t.get("exit") or t["exit"] > s):
                out[S] = 1 if t["side"] == "long" else -1
    return out


def decision_text(wk: pd.Series, side: int) -> str:
    d = weekly._decide(wk, side)
    if not d:
        return "nessuna"
    return f"ingresso {'long' if d[1] > 0 else 'short'}" if d[0] == "enter" else f"uscita {d[1]}"


def compare(f: pd.DataFrame, base: dict, vals: dict, label: str) -> dict:
    """Decisioni puntuali (stessa posizione del definitivo) e simulazione completa con i provvisori."""
    w0 = base["weekly"]
    w1 = inject(w0, vals)
    sides = side_series(base["trades"] + ([base["open"]] if base["open"] else []), list(vals))
    ch = []
    for S in vals:
        if S not in w0.index:
            continue
        a, b = decision_text(w0.loc[S], sides[S]), decision_text(w1.loc[S], sides[S])
        if a != b:
            ch.append(dict(scenario=label, date=str(S.date()), side=sides[S], decision_def=a, decision_prov=b,
                           flow_def=w0.at[S, "flow"], flow_prov=w1.at[S, "flow"], fund7_def=w0.at[S, "fund7"],
                           fund7_prov=w1.at[S, "fund7"]))
    r = simulate_with(f, vals)
    m0, m1 = weekly.metrics(base), weekly.metrics(r)
    t0 = {(t["entry"], t["side"], t.get("exit")) for t in base["trades"]}
    t1 = {(t["entry"], t["side"], t.get("exit")) for t in r["trades"]}
    return dict(changed=ch, trades_diff=len(t0 ^ t1), ret_def=m0.get("total_pct"), ret_prov=m1.get("total_pct"),
                dd_def=m0.get("max_dd_pct"), dd_prov=m1.get("max_dd_pct"), m0=m0, m1=m1)


def err_stats(x: pd.Series) -> str:
    a = x.abs().dropna()
    if not len(a):
        return "n 0"
    return f"n {len(a)} · mediana {a.median():.3g} · p95 {a.quantile(.95):.3g} · max {a.max():.3g}"


def main(raw: Path, repo: Path) -> None:
    D = load(raw, repo)
    f = frame(D["rd"], D["fdef"])
    say(f"Dati definitivi: {f.index.min().date()} → {f.index.max().date()} · funding definitivo archivio fino a "
        f"{ARCH_END_FUND.date()}, poi ricostruito dal premio fino a {D['fdef'].index.max().date()}")
    base = weekly.simulate(f)
    mb = weekly.metrics(base)
    say(f"W3.2 definitivo: {mb}")

    # --- rapporti OKX/Binance
    okx, perp, m = D["okx1d"], D["rd"]["perp"], D["rd"]["metrics"]
    rat = (okx["volCcy"] / perp["volume"]).dropna()
    say("Volume OKX / Binance per anno (mediana):", rat.groupby(rat.index.year).median().round(3).to_dict())
    sh_err = (m["taker_buy_share"] - perp["taker_buy_volume"] / perp["volume"]).dropna()
    say("Taker share metrics (non pesata) − share vera (pesata) giornaliera:", err_stats(sh_err),
        f"· media {sh_err.mean():+.4f}")
    pd.DataFrame({"okx_over_binance_vol": rat, "share_err": sh_err}).to_csv(OUT / "ratios_daily.csv")

    # --- flusso
    fs = flow_scenarios(D, f)
    res, allch = [], []
    for k in (1, 2, 3):
        x = fs[fs.k == k]
        for c in ("P0_attuale", "P1_volume_scalato", "P2_scalato_taker_corretto", "P3_solo_definitivi"):
            e = x[c] - x["flow_def"]
            sign = int(((np.sign(x[c]) != np.sign(x["flow_def"])) & x[c].notna()).sum())
            vals = {pd.Timestamp(r["date"]): {"flow": r[c]} for _, r in x.iterrows()}
            cmp_ = compare(f, base, vals, f"flow k={k} {c}")
            allch += cmp_["changed"]
            res.append(dict(k=k, variante=c, n=len(x), err_mediana=e.abs().median(), err_p95=e.abs().quantile(.95),
                            err_max=e.abs().max(), bias=e.mean(), segno_diverso=sign, vuoti=int(x[c].isna().sum()),
                            decisioni_cambiate=len(cmp_["changed"]), trade_diversi=cmp_["trades_diff"],
                            rend_def=cmp_["ret_def"], rend_prov=cmp_["ret_prov"], dd_def=cmp_["dd_def"],
                            dd_prov=cmp_["dd_prov"]))
    rf = pd.DataFrame(res)
    rf.to_csv(OUT / "flow_results.csv", index=False)
    say("\nFLUSSO (domeniche dal 2022-05-15; k = giorni finali gio/ven/sab ancora OKX al lunedì):")
    say(rf.round(4).to_string(index=False))

    # --- funding
    fu, fd = funding_sundays(D)
    say("\nFUNDING giornaliero OKX − definitivo:", err_stats(fd["okx"] - fd["def"]),
        f"· media {(fd['okx'] - fd['def']).mean():+.2e}")
    say("FUNDING giornaliero ricostruito − archivio (fino al 31/10):",
        err_stats((fd["rebuilt"] - fd["def"])[fd.index <= ARCH_END_FUND]))
    resf = []
    for c in ("F0_attuale", "F1_premio_binance", "F1b_premio_attesa", "F2_okx_piu_scarto"):
        e = fu[c] - fu["fund7_def"]
        vals = {pd.Timestamp(r["date"]): {"fund7": r[c]} for _, r in fu.iterrows()}
        cmp_ = compare(f, base, vals, f"funding {c}")
        allch += cmp_["changed"]
        resf.append(dict(variante=c, n=len(fu), err_mediana=e.abs().median(), err_p95=e.abs().quantile(.95),
                         err_max=e.abs().max(), bias=e.mean(), decisioni_cambiate=len(cmp_["changed"]),
                         trade_diversi=cmp_["trades_diff"]))
    rfu = pd.DataFrame(resf)
    rfu.to_csv(OUT / "funding_results.csv", index=False)
    say("\nFUNDING 7g alle domeniche (dal 30/08/2026, finestra OKX disponibile):")
    say(fu.round(8).to_string(index=False))
    say(rfu.to_string(index=False))

    # --- funding: sensibilità sullo storico 2021–2026 (OKX non disponibile prima di fine agosto 2026)
    w = base["weekly"]
    sides = side_series(base["trades"] + ([base["open"]] if base["open"] else []), list(w.index[w.index >= weekly.START]))
    e0 = (fu["F0_attuale"] - fu["fund7_def"])
    lo, hi = float(e0.min()), float(e0.max())
    sens = []
    for S, sd in sides.items():
        wk = w.loc[S]
        if pd.isna(wk["fund7"]):
            continue
        for shift in (lo, hi, -2 * max(abs(lo), abs(hi)), 2 * max(abs(lo), abs(hi))):
            w1 = inject(w, {S: {"fund7": wk["fund7"] + shift}})
            a, b = decision_text(wk, sd), decision_text(w1.loc[S], sd)
            if a != b:
                sens.append(dict(date=str(S.date()), side=sd, shift=shift, fund7_def=wk["fund7"], flow=wk["flow"],
                                 decision_def=a, decision_shift=b))
    sens = pd.DataFrame(sens)
    sens.to_csv(OUT / "funding_sensitivity.csv", index=False)
    # percorso completo con uno scarto costante su tutte le domeniche (caso peggiore: errore sempre dello stesso segno)
    path = []
    e1 = (fu["F1_premio_binance"] - fu["fund7_def"])
    for lab, sh in (("F0 min", lo), ("F0 max", hi), ("F0 2×min", 2 * lo), ("F0 2×max", 2 * hi),
                    ("F1 min", float(e1.min())), ("F1 max", float(e1.max()))):
        vals = {S: {"fund7": w.at[S, "fund7"] + sh} for S in sides}
        c_ = compare(f, base, vals, f"funding storico {lab}")
        path.append(dict(scarto=lab, valore=sh, decisioni_cambiate=len(c_["changed"]), trade_diversi=c_["trades_diff"],
                         rend_def=c_["ret_def"], rend_prov=c_["ret_prov"], dd_def=c_["dd_def"], dd_prov=c_["dd_prov"],
                         date=" ".join(f"{x['date']}:{x['decision_def']}→{x['decision_prov']}" for x in c_["changed"])))
    path = pd.DataFrame(path)
    path.to_csv(OUT / "funding_history_path.csv", index=False)
    say("\nFunding sullo storico 2021–2026 con scarto costante a ogni domenica (simulazione completa):")
    say(path.to_string(index=False))
    near = []
    for S, sd in sides.items():
        wk = w.loc[S]
        if sd > 0 and wk["flow"] < 0:
            near.append(wk["fund7"] - weekly.FUND_HOT)
        if sd < 0 and wk["flow"] > 0:
            near.append(weekly.FUND_COLD - wk["fund7"])
    near = pd.Series(near)
    say(f"\nSensibilità funding sullo storico ({len(sides)} domeniche dal 2021): errore OKX osservato da {lo:+.2e} a {hi:+.2e};"
        f" domeniche con il flusso contrario alla posizione (dove il funding decide): {len(near)}; distanza dalla soglia"
        f" (negativa = sotto, nessuna uscita) mediana {near.median():+.2e}, massima {near.max():+.2e}")
    say("Decisioni che cambierebbero spostando fund7 dell'errore osservato (o del doppio):",
        "nessuna" if not len(sens) else "\n" + sens.to_string(index=False))

    pd.DataFrame(allch).to_csv(OUT / "decisions_changed.csv", index=False)
    if allch:
        say("\nDECISIONI CAMBIATE (tutte le varianti):")
        say(pd.DataFrame(allch).to_string(index=False))
    (OUT / "summary.txt").write_text("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
