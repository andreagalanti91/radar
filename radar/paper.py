"""Modulo su carta: il campione di ricerca H2 (giro 12) simulato su un conto virtuale.

Regole H2 (v1), solo BTC, futures:
- segnali = setup attuali (compute_signals), decisione alla chiusura giornaliera UTC
- conferma: prima chiusura 4h oltre il massimo (short: sotto il minimo) delle 2 candele 4h precedenti,
  entro 72h (18 barre); ingresso a mercato all'apertura della barra successiva
- 2 livelli 40/60: 40% al prezzo di conferma, 60% limit a −0,5 ATR (valido 7 giorni)
- stop 1 ATR dall'ingresso (0,5 ATR oltre il secondo livello); TP unico a +1R dal medio effettivo,
  R = distanza stop–medio pianificato; tenuta massima 14 giorni
- size: rischio 3% del conto sullo stop, esposizione max 5x; slippage 0,1% su mercato/stop,
  commissioni 0,05%/lato, funding giornaliero
- ordine prudente dentro la barra: limit, stop, poi TP (nessun TP sulla barra che riempie un limit)
Stesso motore della ricerca (scratchpad giro 12, eng.py), riscritto senza le varianti non usate.
La liquidazione non si modella: con esposizione ≤ 5x e stop a ~1–2 ATR non è raggiungibile.

v2 (ricerca notte 01:47) = stessi trade di H2, cambia solo la size:
  rischio = 5,24% × (0,5 + 1,5·clip(segno·DT_mix, 0, 0,15)/0,15) × m
  m = 0,6 se long e ultima chiusura settimanale (W-SUN, settimana chiusa entro il giorno del segnale) < SMA 40 settimane, altrimenti 1
  DT = (2·taker_buy_base − volume)/volume sulla barra 4h UTC di conferma (chiusa prima dell'ingresso), DT_mix = media spot/perp
  leva = min(5, rischio/stop%)
Dal vivo (update): le candele 4h includono le ore chiuse del giorno in corso (candles_4h(live=True)), quindi la conferma
si vede entro ~1 ora; il rischio v2 di ogni trade dal vivo si congela all'ingresso in data/paper.json (v2.risk_frozen).
Regola dati in tempo reale: l'archivio perp arriva con ~1 giorno di ritardo; se manca il perp della barra di conferma
DT_mix = DT spot (nella ricerca lo spot da solo dà r_boot +206% contro +226% del mix: regola prudente). Se manca lo spot si
usa il perp; senza nessuno dei due DT = 0 (rischio minimo 0,5×).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .data import DATA_DIR, SYMBOL, _get
from .strategy import Params, compute_signals

FEE, SLIP = 0.0005, 0.001
NB, WIN = 2, 18                       # conferma: barre di riferimento, finestra in barre 4h (72h)
W, STEP, STOP = (0.4, 0.6), 0.5, 0.5  # pesi, distanza del limit (ATR), stop oltre l'ultimo livello (ATR)
TP_R, HOLD, LIM_DAYS = 1.0, 14, 7
CAP, COOLDOWN = 5.0, 1
LIVE_START = "2026-10-31"
REF_START = "2022-03-01"
PAPER_FILE = DATA_DIR / "paper.json"
V2_BASE, V2_K, V2_CLIP, V2_M, V2_SMA = 0.0524, 1.5, 0.15, 0.6, 40


OHLC = {"open": "first", "high": "max", "low": "min", "close": "last"}


def hours_after(t: pd.Timestamp) -> pd.DataFrame:
    """Ore spot CHIUSE dopo l'ora `t` (giorno in corso) da data-api.binance.vision, solo per il paper dal vivo.
    In caso di errore di rete restituisce un DataFrame vuoto (si ricade sui dati salvati)."""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = int((t + pd.Timedelta(hours=1)).tz_localize("UTC").timestamp() * 1000)
    try:
        rows = _get("https://data-api.binance.vision/api/v3/klines",
                    {"symbol": SYMBOL, "interval": "1h", "startTime": start, "limit": 1000}, retries=2).json()
    except Exception as e:  # noqa: BLE001
        print(f"[paper] ore di oggi non lette ({type(e).__name__}): solo dati salvati")
        return pd.DataFrame(columns=list(OHLC))
    rows = [r for r in rows if int(r[6]) < now_ms]   # close time passato: ora chiusa
    if not rows:
        return pd.DataFrame(columns=list(OHLC))
    d = pd.DataFrame([r[:5] for r in rows], columns=["t", *OHLC])
    d["t"] = pd.to_datetime(pd.to_numeric(d["t"]), unit="ms")
    return d.set_index("t").astype(float)


def candles_4h(live: bool = False) -> pd.DataFrame:
    """Candele 4h UTC aggregate da data/spot_1h.csv; l'ultimo giorno si scarta se incompleto.
    live=True (solo aggiornamento dal vivo): si accodano le ore chiuse del giorno in corso (hours_after);
    una barra 4h di oggi si usa solo se completa (4 ore chiuse). Storico e backtest restano sul solo spot_1h."""
    h = pd.read_csv(DATA_DIR / "spot_1h.csv", index_col=0, parse_dates=True)
    k = h.resample("4h").agg(OHLC).dropna()
    last = k.index[-1].normalize()
    k = k[k.index < last] if (k.index.normalize() == last).sum() < 6 else k
    if live:
        x = hours_after(h.index[-1])
        if len(x):
            n = x["open"].resample("4h").count()
            x = x.resample("4h").agg(OHLC)[n == 4].dropna()
            k = pd.concat([k, x[x.index > k.index[-1]]])
    return k


class _Bars:
    """Array delle candele 4h e indici giornalieri."""

    def __init__(self, h4: pd.DataFrame, f: pd.DataFrame):
        self.T = h4.index
        self.O, self.H, self.L, self.C = (h4[c].values for c in ("open", "high", "low", "close"))
        self.n = len(h4)
        day = self.T.normalize()
        self.days = pd.DatetimeIndex(sorted(set(day)))
        self.dob = np.searchsorted(self.days, day)
        self.last_of_day = np.r_[self.dob[1:] != self.dob[:-1], True]
        self.first = {d: i for i, d in reversed(list(enumerate(day)))}
        self.fund = f["funding"].reindex(self.days).fillna(0).values


def _confirm(b: _Bars, sg: int, t0: int):
    """(barra di ingresso, prezzo, stato). Stato: 'ok'; 'nofill' (finestra scaduta); a fine dati 'wait'
    (conferma non ancora arrivata) o 'next' (confermato sull'ultima chiusura: ingresso alla prossima apertura)."""
    for j in range(t0 - 1, t0 + WIN):
        ok = (sg == 1 and b.C[j] > b.H[j - NB:j].max()) or (sg == -1 and b.C[j] < b.L[j - NB:j].min())
        if j + 1 >= b.n:
            return None, None, "next" if ok else "wait"
        if ok:
            return j + 1, b.O[j + 1], "ok"
    return None, None, "nofill"


def _trade(b: _Bars, sg: int, a: float, te: int, p0: float) -> dict:
    """Simula un trade per nozionale pianificato = 1; path = [(giorno, pnl mark-to-market)]."""
    levels = np.array([p0, p0 - sg * STEP * a])
    w = np.array(W)
    stop = levels[-1] - sg * STOP * a
    pavg = 1.0 / np.sum(w / levels)
    rdist = abs(pavg - stop)
    stop_pct = rdist / pavg + 2 * FEE + SLIP
    filled = np.zeros(2, bool)
    qty = cost = pos = real = fees = fund = 0.0
    reason, path = "time", []
    end = min(b.n, te + HOLD * 6)
    j = te
    for j in range(te, end):
        filled_now = False
        for k in range(2):
            if filled[k] or (j - te >= LIM_DAYS * 6 and k > 0):
                continue
            lv = levels[k]
            if k == 0 and j == te:
                px = p0 * (1 + sg * SLIP)
            elif k > 0 and ((sg == 1 and b.L[j] <= lv) or (sg == -1 and b.H[j] >= lv)):
                px = min(lv, b.O[j]) if sg == 1 else max(lv, b.O[j])
                filled_now = True
            else:
                continue
            q = w[k] / px
            filled[k] = True; qty += q; pos += q; cost += q * px; fees += q * px * FEE
        avg = cost / qty
        if (sg == 1 and b.L[j] <= stop) or (sg == -1 and b.H[j] >= stop):
            px = (min(stop, b.O[j]) if sg == 1 else max(stop, b.O[j])) * (1 - sg * SLIP)
            real += sg * pos * (px - avg); fees += pos * px * FEE; pos = 0.0; reason = "stop"
        elif not filled_now:
            x = avg + sg * TP_R * rdist
            if (sg == 1 and b.H[j] >= x) or (sg == -1 and b.L[j] <= x):
                real += sg * pos * (x - avg); fees += pos * x * FEE; pos = 0.0; reason = "tp"
        if b.last_of_day[j] or j == end - 1:
            di = b.dob[j]
            if pos > 1e-12:
                fund -= sg * pos * b.C[j] * b.fund[di]
            path.append((di, real - fees + fund + (sg * pos * (b.C[j] - avg) if pos > 1e-12 else 0.0)))
        if pos <= 1e-12:
            break
    # ancora in posizione a fine dati prima dei 14 giorni: trade aperto (valutato all'ultima chiusura)
    is_open = pos > 1e-12 and end == b.n and te + HOLD * 6 > b.n
    if pos > 1e-12 and not is_open:
        px = b.C[j] * (1 - sg * SLIP)
        real += sg * pos * (px - avg); fees += pos * px * FEE; pos = 0.0
    pnl = real - fees + fund + (sg * pos * (b.C[j] - avg) if is_open else 0.0)
    di = b.dob[j]
    if path and path[-1][0] == di:
        path[-1] = (di, pnl)
    else:
        path.append((di, pnl))
    out = dict(sg=sg, entry_bar=te, entry=float(p0), avg=float(avg), stop=float(stop), tp=float(avg + sg * TP_R * rdist),
               levels=levels.tolist(), filled=filled.tolist(), fills=int(filled.sum()), pnl=float(pnl),
               reason="open" if is_open else reason, exit_bar=j, exit_day=int(di), path=path, stop_pct=float(stop_pct))
    if is_open:
        out["limit_expiry"] = str(b.T[te] + pd.Timedelta(days=LIM_DAYS)) if not filled[1] else None
        out["time_exit"] = str(b.T[te] + pd.Timedelta(days=HOLD))
    return out


def dt_4h(h4: pd.DataFrame) -> pd.DataFrame:
    """Delta taker (2·taker − volume)/volume per barra 4h (spot, perp, mix) da data/taker_1h.csv.
    Una barra vale solo con 4 ore presenti; perp mancante -> spot, spot mancante -> perp, nessuno -> 0."""
    t = pd.read_csv(DATA_DIR / "taker_1h.csv", index_col=0, parse_dates=True)
    out = {}
    for k in ("spot", "perp"):
        g = t[[f"{k}_vol", f"{k}_taker"]].dropna()
        n = g[f"{k}_vol"].resample("4h").count()
        g = g.resample("4h").sum()[n == 4]
        out[k] = (2 * g[f"{k}_taker"] - g[f"{k}_vol"]) / g[f"{k}_vol"]
    d = pd.DataFrame(out).reindex(h4.index)
    d["perp_ok"] = d.perp.notna()
    d["perp"] = d.perp.fillna(d.spot)
    d["spot"] = d.spot.fillna(d.perp)
    d[["spot", "perp"]] = d[["spot", "perp"]].fillna(0)
    d["mix"] = (d.spot + d.perp) / 2
    return d


def v2_risk(f: pd.DataFrame, h4: pd.DataFrame):
    """Funzione di rischio di v2: (segno, giorno del segnale, barra di conferma) -> (rischio, dettagli)."""
    dt = dt_4h(h4)
    wk = f["close"].resample("W-SUN").last()
    sma = wk.rolling(V2_SMA).mean()

    def fn(sg: int, d: pd.Timestamp, tc: pd.Timestamp):
        w = wk.index[wk.index <= d]
        below = bool(len(w) and not np.isnan(sma[w[-1]]) and wk[w[-1]] < sma[w[-1]])
        x = sg * float(dt.at[tc, "mix"]) if tc in dt.index else 0.0
        m = V2_M if (sg == 1 and below) else 1.0
        r = V2_BASE * (0.5 + V2_K * np.clip(x, 0, V2_CLIP) / V2_CLIP) * m
        perp = bool(dt.at[tc, "perp_ok"]) if tc in dt.index else False
        return float(r), dict(dt=round(x, 4), below_sma40w=below, perp=perp)
    return fn


def frozen_risk(fn, saved: dict):
    """Rischio v2 congelato all'ingresso: se il trade (giorno segnale + lato) è in `saved` si riusano rischio e DT
    salvati, altrimenti si calcola con `fn` e si aggiunge a `saved`. Così l'arrivo del perp non cambia a posteriori."""
    def g(sg: int, d: pd.Timestamp, tc: pd.Timestamp):
        key = f"{d.date()} {'long' if sg == 1 else 'short'}"
        if key not in saved:
            r, info = fn(sg, d, tc)
            saved[key] = dict(risk=r, **info, bar=str(tc))
        v = saved[key]
        return float(v["risk"]), dict(dt=v["dt"], below_sma40w=v["below_sma40w"], perp=v["perp"])
    return g


def simulate(f: pd.DataFrame, h4: pd.DataFrame, start=LIVE_START, capital: float = 10000.0, risk: float = 0.03,
             risk_fn=None) -> dict:
    """Conto dal giorno `start`: trade chiusi, eventuale trade aperto/conferma attesa, equity giornaliera, statistiche.
    Rischio fisso `risk` (H2) oppure `risk_fn(segno, giorno segnale, apertura barra 4h di conferma)` (v2)."""
    b = _Bars(h4, f)
    s = compute_signals(f, Params())
    s = s[(s.index >= pd.Timestamp(start)) & (s.index <= b.days[-1]) & (s.long_sig | s.short_sig)]
    d0 = int(np.searchsorted(b.days, pd.Timestamp(start)))
    E, nxt, trades, eq_by_day, open_pos = 1.0, -1, [], {}, None
    for d, r in s.iterrows():
        sd = int(np.searchsorted(b.days, d))
        if sd < nxt:
            continue
        sg, a = (1 if r.long_sig else -1), float(r.atr)
        nd = d + pd.Timedelta(days=1)
        if nd not in b.first and nd <= b.days[-1]:
            continue          # giorno successivo mancante nei dati (come nella ricerca)
        t0 = b.first.get(nd, b.n)
        te, p0, st = _confirm(b, sg, t0)
        if st in ("wait", "next"):   # segnale in corso: conferma attesa o ingresso alla prossima apertura
            j = b.n - 1
            lvl = b.H[j - NB + 1:j + 1].max() if sg == 1 else b.L[j - NB + 1:j + 1].min()
            open_pos = dict(status="conferma" if st == "wait" else "ingresso", side="long" if sg == 1 else "short",
                            signal_date=str(d.date()), setup=r.get("setup", ""), atr=round(a, 2), trigger=round(float(lvl), 2),
                            deadline=str(nd + pd.Timedelta(hours=4 * WIN)))
            if st == "next" and risk_fn:   # confermato sull'ultima barra: il rischio di v2 è già noto
                rk, info = risk_fn(sg, d, b.T[j])
                open_pos.update(risk=round(rk, 4), **info)
            break
        if st == "nofill":
            nxt = int(b.dob[min(t0 + WIN, b.n - 1)]) + COOLDOWN
            continue
        t = _trade(b, sg, a, te, p0)
        rk, info = risk_fn(sg, d, b.T[te - 1]) if risk_fn else (risk, {})
        N = min(CAP, rk / t["stop_pct"])
        for di, v in t["path"]:
            eq_by_day[di] = E * (1 + N * v)
        Es, E = E, E * (1 + N * t["pnl"])
        row = dict(date=str(d.date()), setup=r.get("setup", ""), side="long" if sg == 1 else "short",
                   entry_time=str(b.T[te]), entry=round(t["entry"], 2), avg=round(t["avg"], 2), stop=round(t["stop"], 2),
                   tp=round(t["tp"], 2), fills=t["fills"], exit=t["reason"], exit_date=str(b.days[t["exit_day"]].date()),
                   N=round(N, 3), pnl_pct=round(N * t["pnl"] * 100, 2), pnl_usd=round(Es * N * t["pnl"] * capital, 2),
                   risk=round(rk, 4), **info, pnl_unit=t["pnl"])
        if t["reason"] == "open":
            open_pos = dict(row, status="aperto", levels=[round(x, 2) for x in t["levels"]], filled=t["filled"],
                            limit_expiry=t["limit_expiry"], time_exit=t["time_exit"],
                            size_usd=round(Es * N * capital, 2))
            break
        trades.append(row)
        nxt = t["exit_day"] + COOLDOWN
    eq = pd.Series(np.nan, index=range(d0, len(b.days)))
    if len(eq):
        eq.iloc[0] = 1.0
        e = pd.Series(eq_by_day)
        eq.loc[e.index[e.index >= d0]] = e[e.index >= d0]
        eq = eq.ffill()
    eq.index = b.days[d0:]
    return dict(trades=trades, open=open_pos, equity=eq * capital, stats=stats(trades, eq), capital=capital, risk=risk)


def stats(trades: list, eq: pd.Series) -> dict:
    """WR (pnl netto > 0 sul trade), rendimento e drawdown sull'equity giornaliera mark-to-market."""
    if not len(eq):
        return dict(n=0, wr=None, ret=0.0, dd=0.0)
    pn = np.array([t["pnl_unit"] for t in trades])
    return dict(n=len(trades), wr=round(float((pn > 0).mean()) * 100, 1) if len(pn) else None,
                ret=round(float(eq.iloc[-1] / eq.iloc[0] - 1) * 100, 1), dd=round(float((eq / eq.cummax() - 1).min()) * 100, 1))


def _account(r: dict, version: str, start: str, ref: dict) -> dict:
    eq = r["equity"]
    return dict(
        version=version, start=start, capital0=r["capital"], risk=r["risk"] if r.get("risk_fn") is None else "v2",
        capital=round(float(eq.iloc[-1]), 2) if len(eq) else r["capital"], stats=r["stats"], open=r["open"],
        trades=[{k: v for k, v in t.items() if k != "pnl_unit"} for t in r["trades"]],
        equity=[[str(d.date()), round(float(v), 2)] for d, v in eq.items()],
        reference=dict(start=REF_START, **ref["stats"]),
    )


def update(f: pd.DataFrame) -> dict:
    """Ricalcola i conti su carta H2 e v2 dal LIVE_START e i riferimenti storici; salva data/paper.json.
    Le chiavi di primo livello restano quelle di H2 (compatibilità), i due conti sono in "h2" e "v2"."""
    h4 = candles_4h(live=True)
    h2 = _account(simulate(f, h4, LIVE_START), "H2 v1", LIVE_START, simulate(f, h4, REF_START))
    out = dict(h2, updated=str(h4.index[-1] + pd.Timedelta(hours=4)), h2=h2)
    if (DATA_DIR / "taker_1h.csv").exists():
        fn = v2_risk(f, h4)
        ref = simulate(f, h4, REF_START, risk_fn=fn)   # storico di riferimento: sempre ricalcolato
        try:
            saved = json.loads(PAPER_FILE.read_text()).get("v2", {}).get("risk_frozen", {})
        except (OSError, ValueError):
            saved = {}
        live = simulate(f, h4, LIVE_START, risk_fn=frozen_risk(fn, saved))
        v2 = _account(dict(live, risk_fn=fn), "v2", LIVE_START, ref)
        v2["risk_frozen"] = saved   # "AAAA-MM-GG lato" -> rischio, DT, sotto SMA40w, perp, barra di conferma
        v2["risk"] = dict(base=V2_BASE, k=V2_K, clip=V2_CLIP, m_long_sotto_sma40w=V2_M, cap=CAP)
        v2["reference"]["trades"] = [dict(date=t["date"], side=t["side"], risk=t["risk"], dt=t["dt"], perp=t["perp"],
                                          N=t["N"], pnl_pct=t["pnl_pct"]) for t in ref["trades"]]
        out["v2"] = v2
    PAPER_FILE.write_text(json.dumps(out, indent=1, default=str))
    return out
