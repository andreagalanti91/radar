"""Opzioni · fase 1 · motore: opzioni COMPRATE (call, put, straddle) con prezzatore inseribile. Nessun risultato qui.

Prezzatore (interfaccia di superficie.py; le date sono istanti alle 00:00 UTC di quel giorno):
    scadenze(data) -> list[date]                      scadenze quotate quel giorno
    iv(data, scadenza, strike, tipo) -> (vol, qualita)
    prezzo(data, scadenza, strike, tipo) -> (premio USD per 1 BTC, qualita)     tipo "C" / "P"; (None, q) = nessun prezzo
    spot(data) -> float
  facoltativi: strikes(data, scadenza) -> list[float] (griglia reale; altrimenti griglia_default),
               regolamento(scadenza) -> float (prezzo alle 08:00 UTC; altrimenti cache/btc_0800.csv).

Convenzioni (fissate prima dei risultati):
- ingresso all'apertura (00:00 UTC) del giorno indicato dal piano: premio = prezzo(data) × (1 + 3%) + commissione;
- commissione 0,03% del controvalore (spot × quantità) con tetto 12,5% del premio, per ogni acquisto e vendita;
- vendita prima della scadenza: prezzo(data) × (1 − 3%) − commissione; a scadenza (08:00 UTC del venerdì) valore intrinseco
  sul prezzo di regolamento meno esercizio 0,02% del controvalore (tetto 12,5% del valore);
- spesa = quota × capitale all'ingresso, commissioni incluse; il resto del conto resta in liquidità a rendimento zero;
- valutazione giornaliera alla chiusura (= prezzo delle 00:00 del giorno dopo) al valore di LIQUIDAZIONE (denaro e
  commissione inclusi): il DD giornaliero comprende la differenza denaro-lettera;
- uscite del piano "alla chiusura" (trailing/stop intraday di W3.2) al prezzo delle 00:00 del giorno dopo, "all'apertura"
  (uscite domenicali di W3.2, segnale contrario) al prezzo delle 00:00 del giorno stesso;
- U1/U2/U3: controllo alla chiusura giornaliera sul valore di liquidazione, vendita a quel prezzo; U4: vendita alle 00:00
  del giorno a 7 giorni dalla scadenza; U5: un solo rinnovo, comprato alle 00:00 del giorno dopo la scadenza;
- una posizione per volta: un ingresso con posizione aperta si ignora.
Con superficie.py (riferimento D alle 12:00 UTC) tutti gli istanti "00:00" qui sopra diventano "12:00" dello stesso giorno:
nessun anticipo (la decisione è della domenica, il prezzo del lunedì); le uscite "alla chiusura" (trailing intraday di
W3.2) restano sul giorno dopo, cioè dopo lo stop. Senza strikes() si usa griglia_default; senza regolamento() la cache 08:00.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SPREAD, FEE, FEE_CAP, EXER = 0.03, 0.0003, 0.125, 0.0002
DAY = pd.Timedelta(days=1)
EXP_H = pd.Timedelta(hours=8)


# ------------------------------------------------------------------ Black-76 e griglia
def ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black76(F: float, K: float, T: float, vol: float, tipo: str) -> float:
    """Prezzo Black-76 (tasso zero) in USD per 1 BTC. T in anni."""
    if T <= 0 or vol <= 0:
        return max(F - K, 0.0) if tipo == "C" else max(K - F, 0.0)
    s = vol * math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * s * s) / s
    d2 = d1 - s
    return F * ncdf(d1) - K * ncdf(d2) if tipo == "C" else K * ncdf(-d2) - F * ncdf(-d1)


def griglia_default(S: float) -> float:
    """Passo dei prezzi d'esercizio Deribit vicino al prezzo (approssimazione se il prezzatore non dà la griglia)."""
    return 250.0 if S < 10_000 else 500.0 if S < 30_000 else 1000.0 if S < 120_000 else 2000.0


def anni(data: pd.Timestamp, scadenza: pd.Timestamp) -> float:
    return ((pd.Timestamp(scadenza) + EXP_H) - pd.Timestamp(data)).total_seconds() / 86400 / 365


# ------------------------------------------------------------------ prezzatore provvisorio (solo test del motore)
class PrezzatoreB0Provvisorio:
    """Black-76 con la volatilità iv_vera e la base F/S di storico_prezzi_veri.csv, SOLO per le 23 operazioni (contratto
    fissato dal CSV: una scadenza e un prezzo d'esercizio per data d'ingresso). Spot: apertura del giorno dal frame
    (all'ingresso lo spot implicito del CSV, K / (1 + K_su_S)). Serve solo a provare il motore."""

    MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}

    def __init__(self, csv: Path, frame: pd.DataFrame, settle: pd.Series):
        self.c = pd.read_csv(csv)
        self.o, self.cl = frame["open"], frame["close"]
        self.settle = settle
        self.by_entry, self.by_exp = {}, {}
        for _, r in self.c.iterrows():
            _, e, K, t = r["contratto"].split("-")
            exp = pd.Timestamp(2000 + int(e[-2:]), self.MON[e[-5:-2]], int(e[:-5]))
            d0 = pd.Timestamp(r["entra"])
            S0 = float(K) / (1 + r["K_su_S"])
            self.by_entry[d0] = dict(exp=exp, K=float(K), tipo=t, S0=S0)
            self.by_exp[(exp, float(K), t)] = dict(iv=float(r["iv_vera"]), base=float(r["base"]), d0=d0, S0=S0)

    def scadenze(self, data):
        x = self.by_entry.get(pd.Timestamp(data))
        return [x["exp"]] if x else []

    def strikes(self, data, scadenza):
        x = self.by_entry.get(pd.Timestamp(data))
        return [x["K"]] if x else []

    def spot(self, data):
        d = pd.Timestamp(data)
        x = self.by_entry.get(d)
        if x:
            return x["S0"]
        if d in self.o.index:
            return float(self.o[d])
        return float(self.cl[self.cl.index < d].iloc[-1])

    def iv(self, data, scadenza, strike, tipo):
        x = self.by_exp.get((pd.Timestamp(scadenza), float(strike), tipo))
        return (x["iv"], "provvisoria") if x else (None, "assente")

    def prezzo(self, data, scadenza, strike, tipo):
        x = self.by_exp.get((pd.Timestamp(scadenza), float(strike), tipo))
        if not x:
            return None, "assente"
        S = self.spot(data)
        return black76(S * (1 + x["base"]), float(strike), anni(data, scadenza), x["iv"], tipo), "provvisoria"

    def regolamento(self, scadenza):
        return float(self.settle[pd.Timestamp(scadenza)])


# ------------------------------------------------------------------ configurazione e piano
@dataclass
class Conf:
    giorni: int = 30            # scadenza: venerdì quotato più vicino a N giorni
    mny: float = 0.0            # +0,05 = 5% fuori dal prezzo, −0,05 = 5% dentro
    quota: float = 0.05         # spesa in % del conto
    uscita: str = "U0"          # U0..U5
    straddle: bool = False
    spread_k: float = 0.0       # spread a debito: gamba venduta x più fuori dal prezzo (0 = nessuna)
    u_mult: float | None = None # moltiplicatore di U1/U2/U3 (vicini: 1,5 / 2,5 / 3,5)
    u4_giorni: int = 7          # U4: giorni prima della scadenza
    min_giorni: float = 0.0     # solo descrittivo: scadenze con almeno N giorni (se ce ne sono), come nello studio dell'utente
    spread: float = SPREAD
    fee: float = FEE
    fee_cap: float = FEE_CAP
    exer: float = EXER
    capitale: float = 10_000.0


@dataclass
class Piano:
    """mode "eventi" (W3.2): ingressi = {data: lato}, uscite = {data: "apertura"/"chiusura"}, in_pos = lato di W3.2 per giorno
    (serve a U5). mode "settimanale" (F3): segnali = {lunedì: +1 call / −1 put / 2 straddle / 0}; da flat si entra con
    segnale ≠ 0; in posizione direzionale un segnale opposto chiude all'apertura e (se la conf lo consente) riapre."""
    mode: str = "eventi"
    ingressi: dict = field(default_factory=dict)
    uscite: dict = field(default_factory=dict)
    segnali: dict = field(default_factory=dict)
    in_pos: pd.Series | None = None
    riapri_su_contrario: bool = True


def piano_w32(trades: pd.DataFrame, days: pd.DatetimeIndex) -> Piano:
    ing, usc = {}, {}
    for _, t in trades.iterrows():
        ing[pd.Timestamp(t["entry"])] = 1 if t["side"] == "long" else -1
        if isinstance(t["exit"], str) and t["exit"]:
            usc[pd.Timestamp(t["exit"])] = "apertura" if t["reason"] in ("ema", "dist") else "chiusura"
    s = pd.Series(0, index=days)
    for _, t in trades.iterrows():
        a = pd.Timestamp(t["entry"])
        b = pd.Timestamp(t["exit"]) if isinstance(t["exit"], str) and t["exit"] else days[-1] + DAY
        s[(s.index >= a) & (s.index < b)] = 1 if t["side"] == "long" else -1
    return Piano("eventi", ing, usc, in_pos=s)


def piano_settimanale(serie: pd.Series) -> Piano:
    """serie indicizzata per domenica (decisione) → segnali al lunedì successivo."""
    return Piano("settimanale", segnali={pd.Timestamp(d) + DAY: int(v) for d, v in serie.items() if v == v})


# ------------------------------------------------------------------ simulazione
def _settle_cache() -> pd.Series:
    p = HERE / "cache" / "btc_0800.csv"
    return pd.read_csv(p, index_col=0, parse_dates=True)["open_0800"] if p.exists() else pd.Series(dtype=float)


class Motore:
    """Ordine degli eventi di un giorno d: scadenza alle 08:00 e azioni all'istante del prezzatore (ora = 0 o 12 UTC):
    uscite (di d all'apertura, "alla chiusura" di d−1, contrario, U4), rinnovo U5, ingressi, poi valutazione (U1–U3)."""

    def __init__(self, prezzatore, conf: Conf, settle: pd.Series | None = None):
        self.p, self.c = prezzatore, conf
        self.settle = _settle_cache() if settle is None else settle
        self.ora = float(getattr(prezzatore, "ora", 0.0))

    def t(self, d) -> pd.Timestamp:
        return pd.Timestamp(d) + pd.Timedelta(hours=self.ora)

    def giorni(self, d, exp) -> float:
        return ((pd.Timestamp(exp) + EXP_H) - self.t(d)).total_seconds() / 86400

    # costi
    def _fee(self, S: float, prem: float, qty: float) -> float:
        return min(self.c.fee * S * qty, self.c.fee_cap * prem * qty)

    def _regola(self, exp: pd.Timestamp) -> float:
        if hasattr(self.p, "regolamento"):
            try:
                v = self.p.regolamento(exp)
                if v is not None:
                    return float(v)
            except Exception:  # noqa: BLE001
                pass
        return float(self.settle[pd.Timestamp(exp)])

    # scelta del contratto
    def scegli(self, d: pd.Timestamp, tipo: str, mny: float | None = None, giorni: int | None = None) -> tuple | None:
        exps = [pd.Timestamp(e) for e in self.p.scadenze(d) if self.giorni(d, e) >= 1.0]
        if not exps:
            return None
        g = self.c.giorni if giorni is None else giorni
        if self.c.min_giorni and any(self.giorni(d, e) >= self.c.min_giorni for e in exps):
            exps = [e for e in exps if self.giorni(d, e) >= self.c.min_giorni]
        exp = min(exps, key=lambda e: (abs(self.giorni(d, e) - g), -e.value))
        S = self.p.spot(d)
        x = (self.c.mny if mny is None else mny) * (1 if tipo == "C" else -1)
        target = S * (1 + x)
        ks = list(self.p.strikes(d, exp)) if hasattr(self.p, "strikes") else []
        if ks:
            K = min(ks, key=lambda k: (abs(k - target), k))
        else:
            step = griglia_default(S)
            K = round(target / step) * step
        return exp, float(K), S

    def _mid(self, d, leg) -> float | None:
        v, q = self.p.prezzo(d, leg["exp"], leg["K"], leg["tipo"])
        leg.setdefault("qual", []).append(q)
        return None if v is None or not np.isfinite(v) else float(v)

    def _liq(self, d, legs, S) -> float:
        """Valore di liquidazione delle gambe aperte all'istante di d (gambe vendute: si ricomprano alla lettera)."""
        tot = 0.0
        for g in legs:
            m = self._mid(d, g)
            m = g["last"] if m is None else m
            g["last"] = m
            sg = g.get("segno", 1)
            tot += sg * g["qty"] * m * (1 - sg * self.c.spread) - self._fee(S, m, g["qty"])
        return tot

    def _sell(self, d, legs, S) -> float:
        v = self._liq(d, legs, S)
        for g in legs:
            g["open"] = False
        return v

    def _open(self, d: pd.Timestamp, lato: int, cash: float, quota: float | None = None, mny: float | None = None,
              giorni: int | None = None, qty_btc: float | None = None) -> dict | None:
        c = self.c
        tipi = ["C", "P"] if lato == 2 else ["C" if lato > 0 else "P"]
        legs, S = [], None
        for t in tipi:
            ch = self.scegli(d, "C" if lato == 2 else t, 0.0 if lato == 2 else mny, giorni)  # straddle: stesso K alla pari
            if ch is None:
                return None
            exp, K, S = ch
            g = dict(exp=exp, K=K, tipo=t, segno=1, open=True)
            m = self._mid(d, g)
            if m is None or m <= 0:
                return None
            g.update(mid0=m, last=m)
            legs.append(g)
            if c.spread_k and lato != 2:            # spread a debito: si vende la stessa scadenza più fuori dal prezzo
                x = c.spread_k * (1 if t == "C" else -1)
                ks = list(self.p.strikes(d, exp)) if hasattr(self.p, "strikes") else []
                tg = S * (1 + (c.mny if mny is None else mny) * (1 if t == "C" else -1) + x)
                K2 = min(ks, key=lambda k: (abs(k - tg), k)) if ks else round(tg / griglia_default(S)) * griglia_default(S)
                g2 = dict(exp=exp, K=float(K2), tipo=t, segno=-1, open=True)
                m2 = self._mid(d, g2)
                if m2 is None or K2 == K:
                    return None
                g2.update(mid0=m2, last=m2)
                legs.append(g2)
        unit = sum(g["segno"] * g["mid0"] * (1 + g["segno"] * c.spread) + min(c.fee * S, c.fee_cap * g["mid0"]) for g in legs)
        if unit <= 0:
            return None
        if qty_btc is None:
            spend = (c.quota if quota is None else quota) * cash
            q = spend / unit
        else:
            q, spend = qty_btc, qty_btc * unit
        for g in legs:
            g["qty"] = q
        return dict(entry=d, lato=lato, legs=legs, spend=spend, eq0=cash, S0=S, proceeds=0.0, renewed=False,
                    exp=min(g["exp"] for g in legs), K=legs[0]["K"], half_done=False,
                    giorni_scad=round(self.giorni(d, legs[0]["exp"]), 1))

    def _settle(self, pos, d) -> float:
        ST = self._regola(d)
        val = 0.0
        for g in pos["legs"]:
            if g["open"] and g["exp"] == d:
                iv = max(ST - g["K"], 0.0) if g["tipo"] == "C" else max(g["K"] - ST, 0.0)
                val += g.get("segno", 1) * g["qty"] * iv - min(self.c.exer * ST * g["qty"], self.c.fee_cap * iv * g["qty"])
                g["open"] = False
        return val

    def simula(self, piano: Piano, days: pd.DatetimeIndex, start: str = "2018-01-01", end: str | None = None) -> dict:
        days = days[(days >= pd.Timestamp(start)) & ((days <= pd.Timestamp(end)) if end else True)]
        c = self.c
        cash, pos, trades = c.capitale, None, []
        eq = np.full(len(days), np.nan)
        pend_open = None

        def chiudi(d, motivo, valore):
            nonlocal cash, pos
            pos["proceeds"] += valore
            cash += valore
            pos.update(exit=d, motivo=motivo, mult=pos["proceeds"] / pos["spend"],
                       ret=(pos["proceeds"] - pos["spend"]) / pos["eq0"])
            trades.append(pos)
            pos = None

        def scadenza(d):
            nonlocal cash, pos, pend_open
            if pos is None or not any(g["open"] and g["exp"] == d for g in pos["legs"]):
                return
            val = self._settle(pos, d)
            if not any(g["open"] for g in pos["legs"]):
                was_gain = pos["proceeds"] + val > pos["spend"]
                lato_r, renewed = pos["lato"], pos["renewed"]
                chiudi(d, "scadenza", val)
                if c.uscita == "U5" and not renewed and was_gain and piano.in_pos is not None:
                    pend_open = (lato_r, d)
            else:
                pos["proceeds"] += val
                cash += val

        for i, d in enumerate(days):
            if self.ora >= 8:
                scadenza(d)
            # istante del giorno: uscite
            if pos is not None:
                ex = None
                if piano.mode == "eventi" and (piano.uscite.get(d) == "apertura" or piano.uscite.get(d - DAY) == "chiusura") \
                        and pos["entry"] < d:
                    ex = "segnale"
                if piano.mode == "settimanale" and pos["lato"] in (1, -1) and piano.segnali.get(d, 0) == -pos["lato"]:
                    ex = "contrario"
                if c.uscita == "U4" and d >= pos["exp"] - c.u4_giorni * DAY:
                    ex = "U4"
                if ex:
                    chiudi(d, ex, self._sell(d, [g for g in pos["legs"] if g["open"]], self.p.spot(d)))
            # ingressi
            if pos is None:
                lato, kw = None, {}
                if pend_open is not None:
                    lr, dexp = pend_open
                    if piano.in_pos.get(d, 0) == lr and (piano.uscite.get(d) != "apertura"):
                        lato, kw = lr, dict(rinnovo=True, renewed=True)
                    pend_open = None
                if lato is None and piano.mode == "eventi" and d in piano.ingressi:
                    lato = piano.ingressi[d]
                elif lato is None and piano.mode == "settimanale" and piano.segnali.get(d, 0):
                    lato = piano.segnali[d]
                if lato:
                    x = self._open(d, lato, cash)
                    if x is None:
                        trades.append(dict(entry=d, lato=lato, saltata="nessun prezzo", spend=0.0, proceeds=0.0, ret=0.0,
                                           mult=np.nan))
                    else:
                        x.update(kw)
                        cash -= x["spend"]
                        pos = x
            # valutazione all'istante; U1–U3
            mark = 0.0
            if pos is not None:
                legs = [g for g in pos["legs"] if g["open"]]
                S = self.p.spot(d)
                v = self._liq(d, legs, S)
                tgt = {"U1": c.u_mult or 2.0, "U2": c.u_mult or 3.0, "U3": c.u_mult or 2.0}.get(c.uscita)
                if tgt and pos["entry"] < d and v >= tgt * pos["spend"] * (0.5 if pos["half_done"] else 1.0) and v > 0:
                    if c.uscita == "U3" and not pos["half_done"]:
                        for g in legs:
                            g["qty"] /= 2
                        half = v / 2
                        pos["proceeds"] += half
                        cash += half
                        pos["half_done"] = True
                        v = v / 2
                    elif c.uscita != "U3":
                        for g in legs:
                            g["open"] = False
                        chiudi(d, c.uscita, v)
                        v = 0.0
                mark = v if pos is not None else 0.0
            if self.ora < 8:
                scadenza(d)
                if pos is None:
                    mark = 0.0
            eq[i] = cash + mark
        if pos is not None:   # posizione aperta all'ultimo giorno: valutata al valore di liquidazione, esclusa dai conteggi
            v = self._liq(days[-1], [g for g in pos["legs"] if g["open"]], self.p.spot(days[-1]))
            chiudi(days[-1], "aperta", v)
        return {"trades": [t for t in trades if "saltata" not in t], "saltate": [t for t in trades if "saltata" in t],
                "equity": pd.Series(eq, days), "conf": c}


# ------------------------------------------------------------------ metriche
def _streak(r: np.ndarray) -> float:
    """Serie peggiore: perdita composta più grande su operazioni perdenti consecutive (in % del conto)."""
    worst, cur = 0.0, 1.0
    for x in r:
        cur = cur * (1 + x) if x < 0 else 1.0
        worst = min(worst, cur - 1)
    return worst


def metriche(ris: dict, da: str | None = None, a: str | None = None, capitale: float = 10_000.0) -> dict:
    """Metriche nel periodo [da, a] (equity ribasata a `capitale`; operazioni per data d'ingresso)."""
    full = ris["equity"].dropna()
    e = full[(full.index >= pd.Timestamp(da)) if da else full.index == full.index]
    if a:
        e = e[e.index <= pd.Timestamp(a)]
    tr = [t for t in ris["trades"] if (not da or t["entry"] >= pd.Timestamp(da)) and (not a or t["entry"] <= pd.Timestamp(a))
          and t.get("motivo") != "aperta"]
    if e.empty:
        return {}
    prev = full[full.index < e.index[0]]
    base = float(prev.iloc[-1]) if len(prev) else float(ris["conf"].capitale)
    e = pd.concat([pd.Series([base], [e.index[0] - DAY]), e]) / base * capitale
    r = np.array([t["ret"] for t in tr])
    yrs = max((e.index[-1] - e.index[0]).days / 365.25, 1e-9)
    fin = float(e.iloc[-1])
    gains, loss = r[r > 0].sum(), -r[r < 0].sum()
    best2 = np.sort(r)[-2:] if len(r) >= 2 else r
    rest = np.sort(r)[:-2] if len(r) >= 2 else np.zeros(0)
    return {"finale": round(fin, 0), "cagr": round((fin / capitale) ** (1 / yrs) - 1, 4),
            "dd": round(float((e / e.cummax() - 1).min()), 4), "n": len(r),
            "quota_guadagno": round(float((r > 0).mean()), 3) if len(r) else None,
            "pf": round(float(gains / loss), 2) if loss > 0 else None,
            "peggiore": round(float(r.min()), 4) if len(r) else None,
            "serie_peggiore": round(_streak(r), 4),
            "senza_2_migliori": round(capitale * float(np.prod(1 + rest)), 0),
            "migliori_2": [round(float(x), 4) for x in best2]}


PERIODI = {"dal 2018": ("2018-01-01", None), "dal 2021": ("2021-01-01", None),
           "IS 2018–21": ("2018-01-01", "2021-12-31"), "OOS 2022–26": ("2022-01-01", None)}


def tutte_le_metriche(ris: dict) -> dict:
    return {k: metriche(ris, *v) for k, v in PERIODI.items()}


# ------------------------------------------------------------------ placebo
def placebo(motore: Motore, ris: dict, days: pd.DatetimeIndex, n: int = 1000, seed: int = 7,
            da: str = "2018-01-01", a: str | None = None) -> dict:
    """Date d'ingresso a caso (lunedì), stesso numero e stessa sequenza di lati delle operazioni reali nel periodo; ogni
    operazione placebo dura quanto la reale corrispondente (al massimo fino alla scadenza). p = quota dei placebo con
    capitale finale ≥ reale."""
    rng = np.random.default_rng(seed)
    tr = [t for t in ris["trades"] if t["entry"] >= pd.Timestamp(da) and (a is None or t["entry"] <= pd.Timestamp(a))]
    if not tr:
        return {"p": None, "finali": []}
    lati = [t["lato"] for t in tr]
    durate = [max(int((t["exit"] - t["entry"]).days), 1) for t in tr]
    mondays = days[(days.dayofweek == 0) & (days >= pd.Timestamp(da)) & ((days <= pd.Timestamp(a)) if a else True)]
    real = metriche(ris, da, a)["finale"]
    fin = []
    for _ in range(n):
        for _try in range(200):
            idx = np.sort(rng.choice(len(mondays), size=len(tr), replace=False))
            ds = mondays[idx]
            if all((ds[j + 1] - ds[j]).days > durate[j] for j in range(len(ds) - 1)):
                break
        pi = Piano("eventi", {d: l for d, l in zip(ds, lati)},
                   {d + pd.Timedelta(days=k): "apertura" for d, k in zip(ds, durate)})
        r = motore.simula(pi, days, da, a)
        fin.append(metriche(r, da, a)["finale"])
    fin = np.array(fin)
    return {"p": float((fin >= real).mean()), "finali": fin, "reale": real}


def con(conf: Conf, **kw) -> Conf:
    return replace(conf, **kw)
