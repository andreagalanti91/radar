"""dati_nuovi · FASE 1 · analisi degli errori di W3.2 (descrittiva, nessuna variante).

- BTC dal 01/01/2018: radar.weekly.simulate sul frame lungo ufficiale (research/w32_ufficiale/f_lungo.csv.gz, serie continua,
  riferimento 242.755 $). Controllo anche dal 2021 sul frame del tool (84.820 $).
- ETH dal 11/01/2021: frame di research/w32_asset2 (riferimento 39.572 $).
- Per ogni operazione: MAE/MFE sul prezzo (minimi/massimi giornalieri dall'entrata all'uscita), restituzione del guadagno massimo,
  motivo d'ingresso (età del trend, F1, flusso) e d'uscita, contesto dei dati già raccolti ALLA DATA DEL SEGNALE (valori del giorno
  prima della domenica, come il flusso) con il percentile sugli ultimi 365 giorni.
- Movimenti > 30% mancati: zigzag 30% sulle chiusure giornaliere; per ogni gamba la quota del movimento presa nello stesso verso
  e cosa bloccava l'ingresso nelle domeniche della gamba.
Uscite: errori/*.csv, errori/errori_output.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "w32_asset2"))
from radar import weekly as W  # noqa: E402
import lib as L  # noqa: E402

OUT = HERE / "errori"; OUT.mkdir(exist_ok=True)
DN = HERE / "data"
END = "2026-11-24"
LOG = []


def p(*a):
    s = " ".join(str(x) for x in a); print(s); LOG.append(s)


# ------------------------------------------------------------------ frame e simulazioni
def frames():
    fl = pd.read_csv(ROOT / "research/w32_ufficiale/f_lungo.csv.gz", index_col=0, parse_dates=True)
    ft = pd.read_csv(ROOT / "research/w32_ufficiale/f_tool.csv.gz", index_col=0, parse_dates=True)
    fe = L.cfeats("ETH")
    return fl[fl.index <= END], ft[ft.index <= END], fe[fe.index <= END]


# ------------------------------------------------------------------ contesto (dati già raccolti)
def _ser(path, col, date="date", **kw):
    d = pd.read_csv(path, **kw)
    d[date] = pd.to_datetime(d[date].astype(str).str[:10])
    return d.set_index(date)[col].astype(float).sort_index()


def context(asset):
    """Serie giornaliere disponibili alla data indicata (ritardo di pubblicazione già applicato)."""
    c = {}
    m = ROOT / "data" / ("metrics.csv" if asset == "BTC" else "eth_metrics.csv")
    met = pd.read_csv(m, parse_dates=["date"]).set_index("date").sort_index()
    c["oi_usd_chg28"] = (met["oi_usd"] / met["oi_usd"].shift(28) - 1) * 100
    c["top_ls"] = met["top_ls_pos"]
    c["global_ls"] = met["global_ls"]
    if asset == "BTC":
        c["mvrv"] = _ser(ROOT / "research/utxo_pl/mvrv.csv", "mvrv")
        c["dvol"] = _ser(ROOT / "research/opzioni_studio/dati/dvol.csv", "close")
    else:
        c["mvrv"] = _ser(DN / "mvrv/eth_mvrv.csv", "mvrv") if (DN / "mvrv/eth_mvrv.csv").exists() else pd.Series(dtype=float)
        c["dvol"] = _ser(ROOT / "research/opzioni_direzione/dati/dvol_ETH_1D.csv", "close", date="t")
    dx = _ser(ROOT / "research/dxy_divergenza/dollaro_fred.csv", "DTWEXBGS", date="observation_date")
    c["dxy_chg28"] = (dx / dx.asfreq("D").ffill().shift(28).reindex(dx.index) - 1) * 100
    vx = pd.read_csv(ROOT / "research/censimento/data/VIXCLS.csv")
    vx["observation_date"] = pd.to_datetime(vx["observation_date"])
    c["vix"] = pd.to_numeric(vx.set_index("observation_date")["VIXCLS"], errors="coerce").dropna()
    idx = pd.date_range("2014-01-01", END)
    df = pd.DataFrame({k: v.reindex(idx.union(v.index)).ffill(limit=10).reindex(idx) for k, v in c.items()})
    # ritardi: derivati/MVRV/DVOL/VIX 1 giorno (dato di sabato alla decisione della domenica, come il flusso);
    # dollaro FRED (H.10 settimanale, pubblicato il lunedì successivo): 7 giorni
    lag = {k: 1 for k in df}; lag["dxy_chg28"] = 7
    return pd.DataFrame({k: df[k].shift(lag[k]) for k in df})


def pct_rank(s, day, n=365):
    x = s.loc[:day].dropna().iloc[-n:]
    if len(x) < 60 or pd.isna(s.get(day)):
        return np.nan
    return round(100 * (x < s[day]).mean())


# ------------------------------------------------------------------ schede
def card(f, w, ctx, t, asset):
    e, x = pd.Timestamp(t["entry"]), pd.Timestamp(t.get("exit") or f.index[-1])
    g = f.loc[e:x]; sd = 1 if t["side"] == "long" else -1; px0 = t["entry_px"]
    if sd > 0:
        mfe, mae = g["high"].max() / px0 - 1, g["low"].min() / px0 - 1
    else:
        mfe, mae = 1 - g["low"].min() / px0, 1 - g["high"].max() / px0
    move = t["move"] if t.get("exit") else (f["close"].iloc[-1] / px0 - 1) * sd
    give = (mfe - move) / mfe if mfe > 0 else np.nan
    sig = pd.Timestamp(t["signal"]); wk = w.loc[sig]
    why = (f"trend {int(wk['trend_age'])} sett. sopra SMA40, F1 {'attivo' if wk['trend_age'] >= W.OLD_TREND else 'non attivo'}"
           if sd > 0 else f"SMA40 in calo, chiusura {100 * (wk['close'] / wk['sma'] - 1):+.0f}% dalla SMA40")
    row = dict(asset=asset, verso=t["side"], segnale=t["signal"], entrata=t["entry"], uscita=t.get("exit") or "aperta",
               prezzo_in=round(px0), prezzo_out=round(t["exit_px"]) if t.get("exit_px") else round(f["close"].iloc[-1]),
               esposizione=t["expo"], sul_capitale=round(100 * (t["pnl"] if t.get("exit") else t["pnl_close"]), 1),
               movimento=round(100 * move, 1), mfe=round(100 * mfe, 1), mae=round(100 * mae, 1),
               restituito=round(100 * give) if give == give else None, giorni=(x - e).days,
               motivo_uscita=W.REASONS.get(t.get("reason", "open"), t.get("reason")), ingresso=why,
               flusso=round(float(wk["flow"]), 2), fund7=round(float(wk["fund7"]) * 1e4, 2),
               atr_pct=round(100 * float(wk["atr"] / wk["close"]), 1),
               dist_ema21_atr=round(float((wk["close"] - wk["ema21"]) / wk["atr"]), 2),
               sett_prec_atr=round(float((wk["close"] - w["close"].shift(1)[sig]) / wk["atr"]), 2))
    for k in ctx:
        v = ctx[k].get(sig - pd.Timedelta(days=0))
        row[k] = None if pd.isna(v) else round(float(v), 3 if k in ("mvrv", "top_ls", "global_ls") else 1)
        row[k + "_pct1y"] = pct_rank(ctx[k], sig)
    return row


def run_trades(f, start, asset, ctx):
    o = W.simulate(f, start=start)
    w = o["weekly"]
    tr = o["trades"] + ([dict(o["open"], exit=None, exit_px=None, reason="open")] if o["open"] else [])
    return o, pd.DataFrame([card(f, w, ctx, t, asset) for t in tr])


# ------------------------------------------------------------------ movimenti > 30% mancati
def zigzag(c, th=0.30):
    """Zigzag classico sulle chiusure: un nuovo estremo si conferma quando il prezzo torna indietro di th."""
    piv, tr = [], 0
    hi = lo = float(c.iloc[0]); hi_i = lo_i = c.index[0]
    for t, v in c.items():
        if tr == 0:
            if v > hi: hi, hi_i = v, t
            if v < lo: lo, lo_i = v, t
            if v >= lo * (1 + th): tr = 1; piv.append((lo_i, lo)); hi, hi_i = v, t
            elif v <= hi * (1 - th): tr = -1; piv.append((hi_i, hi)); lo, lo_i = v, t
        elif tr == 1:
            if v > hi: hi, hi_i = v, t
            elif v <= hi * (1 - th): piv.append((hi_i, hi)); tr = -1; lo, lo_i = v, t
        else:
            if v < lo: lo, lo_i = v, t
            elif v >= lo * (1 + th): piv.append((lo_i, lo)); tr = 1; hi, hi_i = v, t
    piv.append((hi_i, hi) if tr == 1 else (lo_i, lo))      # ultima gamba (può essere ancora in corso)
    return [(a, b, va, vb) for (a, va), (b, vb) in zip(piv[:-1], piv[1:]) if a != b]


def missed(f, o, start, asset):
    c = f.loc[start:END, "close"]
    pos = pd.Series(0, index=c.index)
    for t in o["trades"] + ([o["open"]] if o["open"] else []):
        a = pd.Timestamp(t["entry"]); b = pd.Timestamp(t["exit"]) if t.get("exit") else c.index[-1] + pd.Timedelta(days=1)
        pos[(pos.index >= a) & (pos.index < b)] = 1 if t["side"] == "long" else -1
    r = np.log(c).diff().fillna(0)
    w = o["weekly"]
    rows = []
    for a, b, va, vb in zigzag(c):
        mv = vb / va - 1
        if abs(mv) < 0.30:
            continue
        sd = 1 if mv > 0 else -1
        seg = slice(a + pd.Timedelta(days=1), b)
        lr = r[seg]; ps = pos[seg]
        tot = float(lr.sum()); got = float((lr * (ps == sd)).sum())
        share = got / tot if tot else np.nan
        same = float((ps == sd).mean()); opp = float((ps == -sd).mean())
        # cosa bloccava l'ingresso nelle domeniche della gamba in cui W3.2 era flat
        sun = w.loc[(w.index >= a) & (w.index < b)]
        blk = {}
        for d, wk in sun.iterrows():
            if pos.get(d + pd.Timedelta(days=1), 0) != 0:
                continue
            if sd > 0:
                cond = {"regime": bool((wk["close"] > wk["sma"]) and (wk["ema20"] > w["ema20"].shift(1)[d])),
                        "ema21": bool(wk["close"] > wk["ema21"]), "flusso": bool(wk["flow"] > 0), "F1": bool(wk["f1_ok"])}
            else:
                cond = {"regime": bool((wk["close"] < wk["sma"]) and (wk["sma"] < w["sma"].shift(4)[d]) and (wk["ema20"] < w["ema20"].shift(1)[d])),
                        "ema21": bool(wk["close"] < wk["ema21"]), "flusso": bool(wk["flow"] < 0)}
            for k, v in cond.items():
                if not v:
                    blk[k] = blk.get(k, 0) + 1
        nflat = int(sum(pos.get(d + pd.Timedelta(days=1), 0) == 0 for d in sun.index))
        rows.append(dict(asset=asset, verso="rialzo" if sd > 0 else "ribasso", da=str(a.date()), a=str(b.date()), giorni=(b - a).days,
                         movimento=round(100 * mv, 1), quota_presa=round(100 * share) if share == share else None,
                         giorni_stesso_verso=round(100 * same), giorni_verso_opposto=round(100 * opp), domeniche_flat=nflat,
                         blocchi=" ".join(f"{k}:{v}" for k, v in sorted(blk.items(), key=lambda z: -z[1])),
                         mancato=bool(share == share and share < 1 / 3)))
    return pd.DataFrame(rows)


def main():
    fl, ft, fe = frames()
    cb, ce = context("BTC"), context("ETH")
    ob, tb = run_trades(fl, "2018-01-01", "BTC", cb)
    o21 = W.simulate(ft, start="2021-01-01")
    oe, te = run_trades(fe, "2021-01-11", "ETH", ce)
    p(f"Controllo motore: BTC dal 2018 {ob['equity'].iloc[-1]:,.0f} $ (rif. 242.755) · BTC dal 2021 {o21['equity'].iloc[-1]:,.0f} $"
      f" (rif. 84.820) · ETH dal 11/01/2021 {oe['equity'].iloc[-1]:,.0f} $ (rif. 39.572)")
    allt = pd.concat([tb, te], ignore_index=True)
    allt.to_csv(OUT / "operazioni.csv", index=False)
    loss = allt[allt["sul_capitale"] <= 0]
    late = allt[(allt["sul_capitale"] > 0) & (allt["restituito"] > 50)]
    loss.to_csv(OUT / "perdite.csv", index=False); late.to_csv(OUT / "uscite_tardive.csv", index=False)
    cols = ["asset", "verso", "segnale", "uscita", "prezzo_in", "prezzo_out", "sul_capitale", "movimento", "mfe", "mae",
            "restituito", "giorni", "motivo_uscita"]
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    p("\nTUTTE LE OPERAZIONI (BTC dal 2018, ETH dal 2021)"); p(allt[cols].to_string())
    p("\nPERDITE (sul capitale ≤ 0)"); p(loss[cols + ["ingresso"]].to_string())
    ctxc = ["flusso", "fund7", "atr_pct", "dist_ema21_atr", "sett_prec_atr", "oi_usd_chg28", "top_ls", "top_ls_pct1y",
            "global_ls", "mvrv", "mvrv_pct1y", "dxy_chg28", "vix", "vix_pct1y", "dvol", "dvol_pct1y"]
    p("\nCONTESTO ALLA DATA DEL SEGNALE · PERDITE"); p(loss[["asset", "verso", "segnale"] + ctxc].to_string())
    p("\nCONTESTO ALLA DATA DEL SEGNALE · VINCENTI (confronto, mediane per verso)")
    win = allt[allt["sul_capitale"] > 0]
    for nm, g in (("perdite", loss), ("vincenti", win)):
        for sd in ("long", "short"):
            x = g[g["verso"] == sd]
            if len(x):
                p(f"  {nm:9s} {sd:5s} n={len(x):2d} " + " ".join(f"{k}={x[k].median():.2f}" for k in ctxc if x[k].notna().any()))
    p("\nUSCITE TARDIVE (in guadagno, restituito > 50% del MFE)"); p(late[cols].to_string())
    mb, me = missed(fl, ob, "2018-01-01", "BTC"), missed(fe, oe, "2021-01-11", "ETH")
    mm = pd.concat([mb, me], ignore_index=True); mm.to_csv(OUT / "movimenti_30.csv", index=False)
    p("\nMOVIMENTI > 30% (zigzag 30% sulle chiusure) e quota presa nello stesso verso"); p(mm.to_string())
    p(f"\nMancati (quota < 1/3): BTC {int(mb['mancato'].sum())}/{len(mb)} · ETH {int(me['mancato'].sum())}/{len(me)}")
    (OUT / "errori_output.txt").write_text("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
