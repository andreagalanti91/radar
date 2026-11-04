"""Monitoraggio su carta della strategia dell'utente su materie prime (argento XAG, petrolio Brent): short sul ritest di un
supporto rotto ("flip") sotto medie ribassiste e long di rimbalzo su una zona di domanda forte. NON è una strategia validata:
dal 2021 lo short flip ha perso (argento −0,54R medio, Brent −0,20R; RESEARCH.md lezioni 75–76). Gli alert servono a seguirla
dal vivo come richiesto dall'utente, con stop e target dichiarati, e a misurarne l'esito reale.

Dati: Sina Finance (futures globali, giornaliero, senza chiave): XAG = argento spot Londra, OIL = Brent. Si usano solo le
giornate chiuse per i segnali; l'ultima barra (in corso) serve solo per l'allerta "prezzo nella zona di ritest".
Regole (come la ricerca, /tmp/radar-work/silver/scripts/bt.py): zone da frattali giornalieri (5 barre, 3 anni) e settimanali
(3 barre, 6 anni, peso 2) raggruppati entro 1,5 ATR, forza ≥ 2; rottura = chiusura sotto il fondo zona; ritest entro 20 giorni =
massimo dentro la zona e chiusura sotto il tetto, con EMA20 < EMA50 e prezzo sotto la SMA200; ingresso all'apertura dopo,
stop = tetto zona + 0,5 ATR, target = zona sotto (o 1,5R se più vicina di 1R); invalidazione = chiusura sopra il tetto.
Rimbalzo long: minimo nella zona forte (forza ≥ 3), candela verde, arrivo dall'alto; stop = fondo zona − 0,5 ATR.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests

ASSETS = {"XAG": "Argento (XAG/USD)", "OIL": "Petrolio Brent"}
URL = "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20x=/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol={}"
WINDOW, K_STOP = 20, 0.5


def fetch(sym: str) -> pd.DataFrame:
    s = requests.get(URL.format(sym), timeout=30).text
    rows = json.loads(s[s.index("(") + 1:s.rindex(")")])
    d = pd.DataFrame(rows)
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")[["open", "high", "low", "close"]].astype(float)


def _prep(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    c, pc = d["close"], d["close"].shift()
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    d["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    d["e20"], d["e50"] = c.ewm(span=20, adjust=False).mean(), c.ewm(span=50, adjust=False).mean()
    d["s200"] = c.rolling(200).mean()
    d["bear"] = (d.e20 < d.e50) & (c < d.s200)
    return d


def zones(d: pd.DataFrame, i: int) -> list[tuple[float, float, float, int]]:
    """Zone (basso, alto, forza, tocchi) note alla chiusura della barra i (solo frattali già confermati)."""
    H, L, A, idx = d.high.to_numpy(), d.low.to_numpy(), d.atr.to_numpy(), d.index
    pts = []
    for j in range(max(5, i - 800), i - 4):          # frattale giornaliero confermato 5 barre dopo
        if H[j] == H[j - 5:j + 6].max():
            pts.append((idx[j], H[j], 1.0))
        if L[j] == L[j - 5:j + 6].min():
            pts.append((idx[j], L[j], 1.0))
    w = d.iloc[:i + 1][["high", "low"]].resample("W-FRI").agg({"high": "max", "low": "min"}).dropna()
    wh, wl = w.high.to_numpy(), w.low.to_numpy()
    for j in range(3, len(w) - 3):
        if wh[j] == wh[j - 3:j + 4].max():
            pts.append((w.index[j], wh[j], 2.0))
        if wl[j] == wl[j - 3:j + 4].min():
            pts.append((w.index[j], wl[j], 2.0))
    now = idx[i]
    pts = sorted([p for p in pts if (now - p[0]).days <= (1095 if p[2] == 1 else 2190)], key=lambda x: x[1])
    tol, zs = 1.5 * A[i], []
    for _, p, wgt in pts:
        if zs and p - zs[-1][0] <= tol:
            lo, hi, f, t = zs[-1]
            zs[-1] = (lo, max(hi, p), f + wgt, t + 1)
        else:
            zs.append((p, p, wgt, 1))
    return [z for z in zs if z[2] >= 2]


def evaluate(sym: str, d: pd.DataFrame | None = None) -> dict:
    raw = fetch(sym) if d is None else d
    today = datetime.now(timezone.utc).date()
    live = raw.iloc[-1]
    d = _prep(raw[raw.index.date < today])                    # solo giornate chiuse per i segnali
    n, i = len(d), len(d) - 1
    C, H, L, O, A = (d[k].to_numpy() for k in ("close", "high", "low", "open", "atr"))
    zs_now = zones(d, i)
    # rotture di supporto negli ultimi WINDOW giorni ancora "vive" (nessuna chiusura sopra il tetto da allora)
    breaks = []
    for j in range(max(1, n - WINDOW - 1), n):
        for lo, hi, f, t in zones(d, j - 1):
            if C[j] < lo <= C[j - 1]:
                after = C[j + 1:]
                if (after > hi).any():
                    status = "invalidata"
                elif j < i and ((H[j + 1:] >= lo) & (C[j + 1:] < hi)).any():
                    k = j + 1 + int(np.argmax((H[j + 1:] >= lo) & (C[j + 1:] < hi)))
                    status = "ritest" if d.bear.iat[k] else "ritest senza medie ribassiste"
                else:
                    status = "in attesa di ritest"
                breaks.append({"date": str(d.index[j].date()), "lo": round(float(lo), 3), "hi": round(float(hi), 3), "force": float(f),
                               "status": status, "expires": str((d.index[j] + pd.Timedelta(days=28)).date())})
    # segnale sulla barra chiusa più recente
    signal = None
    for b in breaks:
        if b["status"] == "ritest" and H[i] >= b["lo"] and C[i] < b["hi"] and d.bear.iat[i]:
            stop = b["hi"] + K_STOP * A[i]
            below = [z for z in zs_now if z[1] < b["lo"] and z[1] < C[i]]
            tgt = below[-1][1] if below else None
            risk = stop - C[i]
            if tgt is None or (C[i] - tgt) < risk:
                tgt = C[i] - 1.5 * risk
            signal = {"side": "short", "date": str(d.index[i].date()), "zone": [b["lo"], b["hi"]], "entry": round(float(C[i]), 3),
                      "stop": round(float(stop), 3), "target": round(float(tgt), 3), "rr": round(float((C[i] - tgt) / risk), 2)}
            break
    if signal is None and i > 5:
        for lo, hi, f, t in zs_now:
            if f >= 3 and L[i] <= hi and C[i] >= lo and C[i] > O[i] and C[i - 5] > hi and hi < C[i] * 1.05:
                stop = lo - K_STOP * A[i]
                above = [z for z in zs_now if z[0] > hi and z[0] > C[i]]
                risk = C[i] - stop
                tgt = above[0][0] if above and above[0][0] - C[i] >= risk else C[i] + 1.5 * risk
                signal = {"side": "long", "date": str(d.index[i].date()), "zone": [round(float(lo), 3), round(float(hi), 3)],
                          "entry": round(float(C[i]), 3), "stop": round(float(stop), 3), "target": round(float(tgt), 3),
                          "rr": round(float((tgt - C[i]) / risk), 2)}
                break
    sup = sorted([z for z in zs_now if z[1] < C[i]], key=lambda z: -z[1])[:3]
    res = sorted([z for z in zs_now if z[0] > C[i]], key=lambda z: z[0])[:3]
    fz = lambda z: {"lo": round(float(z[0]), 3), "hi": round(float(z[1]), 3), "force": float(z[2])}
    r3 = lambda x: round(float(x), 3)
    return {"sym": sym, "name": ASSETS.get(sym, sym), "date": str(d.index[i].date()), "close": r3(C[i]),
            "live": r3(live["close"]), "atr": r3(A[i]), "ema20": r3(d.e20.iat[i]),
            "ema50": r3(d.e50.iat[i]), "sma200": r3(d.s200.iat[i]), "bear": bool(d.bear.iat[i]),
            "breaks": breaks, "signal": signal, "supports": [fz(z) for z in sup], "resistances": [fz(z) for z in res],
            "bars_after": [(str(x.date()), float(h), float(l), float(c)) for x, h, l, c in
                           zip(d.index[-40:], H[-40:], L[-40:], C[-40:])]}


def _p(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def diff_events(cur: dict, st: dict) -> tuple[list[str], dict]:
    """Alert con dedupe: rottura (setup attivo), prezzo nella zona di ritest (in tempo reale), segnale, invalidazione,
    esito del trade su carta (stop o target)."""
    sym, msgs = cur["sym"], []
    seen = set(st.get("seen", []))
    head = f"<b>RADAR · {cur['name']}</b> · strategia su carta (non validata)"
    for b in cur["breaks"]:
        k = f"{sym}:brk:{b['date']}:{b['lo']}"
        if k not in seen and b["status"] == "in attesa di ritest":
            msgs.append(f"{head}\nSupporto rotto il {b['date']}: zona {_p(b['lo'])}–{_p(b['hi'])} ora resistenza. "
                        f"Setup short se il prezzo torna nella zona entro il {b['expires']} con medie ribassiste. "
                        f"Invalidazione: chiusura sopra {_p(b['hi'])}.")
            seen.add(k)
        kz = f"{sym}:zone:{b['date']}:{b['lo']}"
        if kz not in seen and b["status"] == "in attesa di ritest" and b["lo"] <= cur["live"] <= b["hi"]:
            msgs.append(f"{head}\nPrezzo {_p(cur['live'])} DENTRO la zona di ritest {_p(b['lo'])}–{_p(b['hi'])}. "
                        f"Il segnale si conferma solo con la chiusura giornaliera sotto {_p(b['hi'])}.")
            seen.add(kz)
        ki = f"{sym}:inv:{b['date']}:{b['lo']}"
        if ki not in seen and b["status"] == "invalidata" and f"{sym}:brk:{b['date']}:{b['lo']}" in seen:
            msgs.append(f"{head}\nScenario short INVALIDATO: chiusura sopra {_p(b['hi'])} (zona {_p(b['lo'])}–{_p(b['hi'])}).")
            seen.add(ki)
    s = cur["signal"]
    if s:
        ks = f"{sym}:sig:{s['date']}:{s['side']}"
        if ks not in seen:
            msgs.append(f"{head}\n<b>SEGNALE {s['side'].upper()}</b> alla chiusura del {s['date']} ({_p(s['entry'])}): ingresso "
                        f"all'apertura successiva. Stop {_p(s['stop'])} · target {_p(s['target'])} · R/R {str(s['rr']).replace('.', ',')}. "
                        f"Zona {_p(s['zone'][0])}–{_p(s['zone'][1])}.")
            seen.add(ks)
            st.setdefault("open", []).append(s)
    still = []
    for t in st.get("open", []):                               # esito su carta del segnale aperto
        bars = [b for b in cur["bars_after"] if b[0] > t["date"]]
        hit = None
        for day, h, l, c in bars:
            if t["side"] == "short":
                if h >= t["stop"]:
                    hit = ("stop", day, t["stop"]); break
                if l <= t["target"]:
                    hit = ("target", day, t["target"]); break
            else:
                if l <= t["stop"]:
                    hit = ("stop", day, t["stop"]); break
                if h >= t["target"]:
                    hit = ("target", day, t["target"]); break
        if hit:
            r = (t["entry"] - hit[2]) if t["side"] == "short" else (hit[2] - t["entry"])
            msgs.append(f"{head}\nTrade su carta {t['side']} del {t['date']} chiuso a {hit[0]} il {hit[1]} a {_p(hit[2])} "
                        f"({'+' if r >= 0 else '−'}{_p(abs(r) / t['entry'] * 100)}%).")
            st.setdefault("closed", []).append(dict(t, exit=hit[1], exit_px=hit[2], why=hit[0]))
        else:
            still.append(t)
    st["open"], st["seen"] = still, sorted(seen)[-200:]
    return msgs, st
