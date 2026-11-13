"""Domanda 3 (PREREG.md): dopo un'ora di cascata il prezzo prosegue fino alla prossima fascia densa (R4) o rimbalza su una
confluenza fascia+supporto quando la cascata si esaurisce (R5)? Proxy OI (k 2/3/4) e liquidazioni reali Binance CM 2023-06→2024-10.
Uso: python research/liq_fasce/q3_cascate.py → risultati_q3.txt, q3_eventi.csv, q3_sintesi.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
from lf_data import WORK, hourly, map_at  # noqa: E402
from radar import levels, liqmap  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

FEE, THRU, HS, SIG = 0.0008, 0.0005, (4, 12, 24, 48), 0.30
f = build_features(load_all()); f = f[f["close"].notna()]
h = hourly()
h = h[h.index < "2026-11-12"]                                   # solo ore con OI e volume perp d'archivio
O, Hh, Ll, C = (h[k].to_numpy(float) for k in ("open", "high", "low", "close"))
T = h.index
fund = f["funding"].fillna(0).reindex(T.normalize()).to_numpy(float)   # funding giornaliero
lr = np.log(h["close"]).diff()
doi = np.log(h["oi_usd"]).diff()
sig = doi.rolling(720, min_periods=200).std()
rv = h["volume"] / h["volume"].rolling(720, min_periods=200).median()
_lv = {}


def lv(day):
    if day not in _lv:
        _lv[day] = levels.compute(f[f.index < day])
    return _lv[day]


def decl(ts, gap=24):
    out, last = [], None
    for t in ts:
        if last is None or (t - last) >= pd.Timedelta(hours=gap):
            out.append(t); last = t
    return out


def proxy_events(k, side):
    c = (doi <= -k * sig) & (rv >= 1.5) & ((lr < 0) if side == "long" else (lr > 0))
    return decl(T[c.fillna(False).to_numpy()])


def real_events(side):
    lq = pd.read_pickle("/tmp/radar-work/liq/work/liq.pkl")
    tot = lq.long_liq + lq.short_liq
    share = (lq.long_liq if side == "long" else lq.short_liq) / tot.replace(0, np.nan)
    c = (tot >= tot.quantile(0.995)) & (share >= 0.75)
    return decl(lq.index[c.to_numpy()])


MAPS = {}


def mp(t):
    if t not in MAPS:
        MAPS[t] = map_at(h, t)
    return MAPS[t]


def trade(i_in, sd, H, target=None):
    """Ingresso all'apertura della candela i_in, uscita al target (limit) o alla chiusura dopo H ore. Rendimento netto."""
    j_end = min(i_in + H - 1, len(T) - 1)
    px_in = O[i_in]
    for j in range(i_in, j_end + 1):
        if target is not None and ((sd < 0 and Ll[j] <= target * (1 - THRU)) or (sd > 0 and Hh[j] >= target * (1 + THRU))):
            px_out = min(O[j], target) if sd < 0 else max(O[j], target)
            if (sd < 0 and O[j] < target) or (sd > 0 and O[j] > target):
                px_out = O[j]
            return sd * (px_out / px_in - 1) - 2 * FEE - sd * fund[i_in] * (j - i_in + 1) / 24, True, j
    return sd * (C[j_end] / px_in - 1) - 2 * FEE - sd * fund[i_in] * (j_end - i_in + 1) / 24, False, j_end


def r4(events, side, H):
    """Continuazione: trade nel verso della cascata con obiettivo la prossima fascia densa (mappa fino all'ora di cascata)."""
    sd = -1 if side == "long" else 1
    rows = []
    for t in events:
        i = T.get_loc(t)
        if i + 1 >= len(T):
            continue
        m = mp(t + pd.Timedelta(hours=1))
        if m is None:
            continue
        p, w, dn, up = m
        cl = next((c for c in (dn if side == "long" else up) if c["rel"] >= SIG), None)
        if cl is None:
            continue
        r, hit, j = trade(i + 1, sd, H, cl["price"])
        mv = MOV[(sd, H)][i] if i < len(MOV[(sd, H)]) else np.nan        # escursione massima nelle H ore dopo la cascata
        rows.append(dict(t=t, side=side, dist=abs(cl["dist_pct"]) / 100, ret=r, hit=hit, i_in=i + 1, j_out=j, mov=mv))
    return pd.DataFrame(rows)


def r5(events, side, H, rand=None, conf_req=True):
    """Rimbalzo: il minimo (massimo) dell'ora di cascata entra in una fascia densa PRE-cascata in confluenza con S (R);
    l'ora dopo chiude contro la cascata senza nuovo estremo; trade contrario all'apertura dell'ora successiva."""
    sd = 1 if side == "long" else -1
    rows = []
    for t in events:
        i = T.get_loc(t)
        if i + 2 >= len(T):
            continue
        exhausted = (C[i + 1] > O[i + 1] and Ll[i + 1] >= Ll[i]) if side == "long" else (C[i + 1] < O[i + 1] and Hh[i + 1] <= Hh[i])
        if not exhausted:
            continue
        m = mp(t)
        if m is None:
            continue
        p, w, dn, up = m
        if rand is not None:
            cands = [dict(price=p * (1 - x) if side == "long" else p * (1 + x)) for x in rand()]
        else:
            cands = [c for c in (dn if side == "long" else up) if c["rel"] >= SIG]
        touched = [c for c in cands if (Ll[i] <= c["price"] < p) if side == "long"] if side == "long" else [c for c in cands if p < c["price"] <= Hh[i]]
        L_ = lv(t.normalize())
        ok = [c for c in touched if (liqmap.confluence(c, L_) or "").startswith("S" if side == "long" else "R")]
        sel = ok if conf_req else touched
        r, _, j = trade(i + 2, sd, H)
        rows.append(dict(t=t, side=side, touched=bool(touched), conf=bool(ok), sel=bool(sel), ret=r, i_in=i + 2, j_out=j))
    return pd.DataFrame(rows)


def rand_hours_ret(n, sd, H, dists=None, draws=1000, seed=3, lo="2021-02-01", hi="2026-11-10"):
    """Media del rendimento di n ore a caso con la stessa regola (obiettivo alla stessa distanza se dato)."""
    rng = np.random.default_rng(seed)
    pool = np.flatnonzero((T >= lo) & (T < hi))
    out = []
    for _ in range(draws):
        ii = rng.choice(pool, n, replace=False)
        rs = []
        for a, i in enumerate(ii):
            tgt = (C[i - 1] * (1 + sd * dists[a % len(dists)])) if dists is not None else None
            rs.append(trade(i, sd, H, tgt)[0])
        out.append(np.mean(rs))
    return np.array(out)


def base_hit(d, sd, H):
    """Probabilità di toccare la stessa distanza entro H ore partendo da un'ora qualsiasi (controllo 'calamita')."""
    return float((MOV[(sd, H)] >= d).mean())


MOV = {}
for H in HS:
    lo_f = pd.Series(Ll[::-1]).rolling(H, min_periods=1).min().to_numpy()[::-1]
    hi_f = pd.Series(Hh[::-1]).rolling(H, min_periods=1).max().to_numpy()[::-1]
    prev = np.r_[np.nan, C[:-1]]
    MOV[(-1, H)] = (1 - lo_f / prev)[1:-H]
    MOV[(1, H)] = (hi_f / prev - 1)[1:-H]


def equity(R, sd_of):
    """10k a 1x, trade non sovrapposti in ordine di tempo, mark-to-market orario; DD sul giornaliero."""
    R = R.sort_values("i_in")
    eq, cap, last_out, marks = [], 1.0, -1, {}
    for _, r in R.iterrows():
        if r.i_in <= last_out:
            continue
        sd = sd_of(r)
        path = C[r.i_in:r.j_out + 1] / O[r.i_in]
        for j, x in zip(range(r.i_in, r.j_out + 1), path):
            marks[T[j]] = cap * (1 + sd * (x - 1))
        cap *= 1 + r.ret
        marks[T[r.j_out]] = cap
        last_out = r.j_out
    s = pd.Series(marks).sort_index()
    full = s.reindex(T[T >= "2021-02-01"]).ffill().fillna(1.0)
    d = full.resample("D").last()
    dd = float((d / d.cummax() - 1).min())
    n = int((R.i_in > -1).sum())
    return round(cap * 10000), round(dd * 100, 1), round((cap - 1) / abs(dd), 2) if dd < 0 else None


if __name__ == "__main__":
    out = []
    P = lambda s="": out.append(str(s)) or print(s)
    SPLIT = pd.Timestamp("2024-01-01")
    EV = {(src, side): (proxy_events(int(src[-1]), side) if src.startswith("proxy") else real_events(side))
          for src in ("proxy k3", "proxy k2", "proxy k4", "reali CM") for side in ("long", "short")}
    EV = {k: [t for t in v if pd.Timestamp("2021-02-01") <= t < pd.Timestamp("2026-11-10")] for k, v in EV.items()}
    P("Eventi (accorpati a 24 h): " + ", ".join(f"{a} {b} {len(v)}" for (a, b), v in EV.items()))
    rows, allev = [], []
    for (src, side), ev in EV.items():
        for H in HS:
            A = r4(ev, side, H)
            sd = -1 if side == "long" else 1
            if len(A):
                ctrl_hit = np.mean([base_hit(d, sd, H) for d in A.dist])
                mvv, dv = A["mov"].to_numpy(), A["dist"].to_numpy()       # controllo a pari volatilità: stessa distanza dopo ALTRE cascate
                ctrl_casc = np.nanmean([(np.delete(mvv, a) >= dv[a]).mean() for a in range(len(A))])
                a, b = A[A.t < SPLIT], A[A.t >= SPLIT]
                row = dict(regola="R4 continuazione", fonte=src, cascata=side, H=H, n=len(A), n_IS=len(a), n_OOS=len(b),
                           ret_pct=A.ret.mean() * 100, ret_IS=a.ret.mean() * 100 if len(a) else np.nan, ret_OOS=b.ret.mean() * 100 if len(b) else np.nan,
                           wr=(A.ret > 0).mean() * 100, tocco=A.hit.mean() * 100, tocco_ctrl=ctrl_hit * 100,
                           tocco_ctrl_cascate=ctrl_casc * 100)
                if H == 24 and src in ("proxy k3", "reali CM"):
                    rr = rand_hours_ret(len(A), sd, H, A.dist.to_numpy(), draws=300)
                    row.update(ctrl_ore_caso=rr.mean() * 100, p_vs_caso=float((rr >= A.ret.mean()).mean()))
                    row.update(dict(zip(("cap_10k", "dd", "mar"), equity(A, lambda r, s=sd: s))))
                rows.append(row)
                if H == 24:
                    allev.append(A.assign(regola="R4", fonte=src, H=H))
            B = r5(ev, side, H)
            if len(B):
                S = B[B.sel]; N_ = B[~B.conf]
                a, b = S[S.t < SPLIT], S[S.t >= SPLIT]
                row = dict(regola="R5 rimbalzo su confluenza", fonte=src, cascata=side, H=H, n=len(S), n_IS=len(a), n_OOS=len(b),
                           ret_pct=S.ret.mean() * 100 if len(S) else np.nan, ret_IS=a.ret.mean() * 100 if len(a) else np.nan,
                           ret_OOS=b.ret.mean() * 100 if len(b) else np.nan, wr=(S.ret > 0).mean() * 100 if len(S) else np.nan,
                           esauriti_senza_conf=N_.ret.mean() * 100 if len(N_) else np.nan, n_senza=len(N_))
                if H == 24 and src in ("proxy k3", "reali CM") and len(S):
                    sd5 = 1 if side == "long" else -1
                    rr = rand_hours_ret(len(S), sd5, H, None, draws=300)
                    row.update(ctrl_ore_caso=rr.mean() * 100, p_vs_caso=float((rr >= S.ret.mean()).mean()))
                    # livelli casuali con la stessa distribuzione di distanze delle fasce
                    dists = np.array([abs(c["dist_pct"]) / 100 for t in EV[(src, side)] if mp(t) for c in (mp(t)[2] if side == "long" else mp(t)[3]) if c["rel"] >= SIG])
                    pl = []
                    for j in range(100):
                        g = np.random.default_rng(900 + j)
                        Br = r5(ev, side, H, rand=lambda g=g: g.choice(dists, 6))
                        Sr = Br[Br.sel]
                        pl.append(Sr.ret.mean() if len(Sr) else np.nan)
                    pl = np.array(pl)
                    row.update(ctrl_livelli_caso=np.nanmean(pl) * 100, p_vs_livelli=float(np.nanmean(pl >= S.ret.mean())))
                    row.update(dict(zip(("cap_10k", "dd", "mar"), equity(S, lambda r, s=sd5: s))))
                rows.append(row)
                if H == 24:
                    allev.append(B.assign(regola="R5", fonte=src, H=H))
    R = pd.DataFrame(rows)
    R.round(3).to_csv(HERE / "q3_sintesi.csv", index=False)
    pd.concat(allev).to_csv(HERE / "q3_eventi.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    P(R.round(2).to_string(index=False))
    # buy & hold dal 2021-02
    c = h["close"]["2021-02-01":]
    P(f"\nBuy & hold 2021-02 → 2026-11-11: 10k → {10000 * c.iloc[-1] / c.iloc[0]:,.0f}, DD {(c / c.cummax() - 1).min() * 100:.1f}%")
    (HERE / "risultati_q3.txt").write_text("\n".join(out) + "\n")
