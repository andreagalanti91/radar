"""Superficie giornaliera di volatilità implicita delle opzioni BTC (Deribit), ricostruita da un campione di scambi veri.

Dati: dati/superficie.csv.gz (costruito da dati/scarica.py + dati/costruisci.py; colonne descritte in costruisci.py).

Convenzioni
-----------
* Giorno D = giorno UTC. Tempo di riferimento della superficie: D alle 12:00 UTC. Le opzioni scadono alle 08:00 UTC
  della data di scadenza, quindi T = (scadenza 08:00 - D 12:00) / 365 giorni. Una scadenza uguale a D è già scaduta.
* Forward F ≈ prezzo indice mediano del campione di D (spot(D)). Moneyness m = ln(K / F).
* Nessun anticipo del futuro: il valore di D usa solo scambi di D; se D non ha dati utili si usa il giorno precedente
  più vicino entro 3 giorni (qualità "estesa"), mai un giorno successivo.

Qualità restituita da iv() / prezzo()
-------------------------------------
* "scambi"      la scadenza richiesta è stata scambiata in D, nello stesso tipo (call/put), e una fascia con scambi ha
                moneyness media entro 0,05 da m; il valore è interpolato linearmente in m fra le mediane delle fasce
                (piatto oltre il bordo).
* "interpolata" dati di D ma non direttamente: scadenza non scambiata (interpolazione lineare della varianza totale
                σ²T fra le scadenze vicine, alla stessa m, escluse quelle a meno di 2 giorni; oltre la prima/ultima
                scadenza volatilità costante), oppure m fuori
                dall'intervallo osservato (volatilità piatta oltre il bordo), oppure presa dall'altro tipo.
* "estesa"      D senza dati utili: stesso calcolo sul giorno precedente più vicino entro 3 giorni (T ricalcolato da D,
                m rispetto all'indice di quel giorno).
* "mancante"    niente entro 3 giorni: iv = nan (non si inventa).

Esempio
-------
    import superficie as S
    sc = S.scadenza_vicina("2021-05-10", 30)           # venerdì scambiato più vicino a 30 giorni
    F = S.spot("2021-05-10")
    vol, q = S.iv("2021-05-10", sc, round(F, -3), "C")  # (0.759, "scambi"), sc = 2021-05-28
    usd, q = S.prezzo("2021-05-10", sc, round(F, -3), "C")
"""
import datetime as _dt
import math
import os

import numpy as np
import pandas as pd

_QUI = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(_QUI, "dati", "superficie.csv.gz")
GIORNI_ESTENSIONE = 3
_TOLL_M = 0.05  # distanza massima in ln(K/F) dal punto osservato più vicino per la qualità "scambi"

_dati = None  # {data: {"F": float, "sc": {scadenza: {"T": float, "C": (m, iv, n), "P": (m, iv, n)}}}}


def _d(x):
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    return _dt.date.fromisoformat(str(x)[:10])


def _carica():
    global _dati
    if _dati is not None:
        return _dati
    df = pd.read_csv(FILE)
    df = df[df["iv"] > 0]
    _dati = {}
    for (d, sc), g in df.groupby(["data", "scadenza"], sort=True):
        gd = _dati.setdefault(_d(d), {"F": float(g["indice"].iloc[0]), "sc": {}})
        voce = {"T": float(g["gg"].iloc[0]) / 365.0}
        for tipo in ("C", "P"):
            h = g[g["tipo"] == tipo].sort_values("m")
            if len(h):
                voce[tipo] = (h["m"].to_numpy(float), h["iv"].to_numpy(float), h["n"].to_numpy(int))
        gd["sc"][_d(sc)] = voce
    return _dati


def _T(data, scadenza, ora=12.0):
    rif = _dt.datetime.combine(_d(data), _dt.time(0)) + _dt.timedelta(hours=ora)
    return (_dt.datetime.combine(_d(scadenza), _dt.time(8)) - rif).total_seconds() / 86400 / 365.0


def _giorno_utile(data):
    """(giorno con dati, giorni indietro) per D o il precedente più vicino entro GIORNI_ESTENSIONE; (None, None) se nessuno."""
    dati, d = _carica(), _d(data)
    for k in range(GIORNI_ESTENSIONE + 1):
        g = d - _dt.timedelta(days=k)
        if g in dati and dati[g]["sc"]:
            return g, k
    return None, None


def spot(data):
    """Prezzo indice (USD) del giorno D: mediana dell'indice Deribit negli scambi campionati di D.
    Se D manca, il giorno precedente più vicino entro 3 giorni; altrimenti nan."""
    g, _ = _giorno_utile(data)
    return _carica()[g]["F"] if g else float("nan")


def scadenze(data, giorni_indietro=GIORNI_ESTENSIONE):
    """Scadenze (date) ancora vive dopo D e scambiate in D o nei `giorni_indietro` giorni precedenti (solo passato)."""
    dati, d = _carica(), _d(data)
    out = set()
    for k in range(giorni_indietro + 1):
        g = dati.get(d - _dt.timedelta(days=k))
        if g:
            out.update(s for s in g["sc"] if s > d)
    return sorted(out)


def scadenza_vicina(data, giorni, solo_venerdi=True):
    """Scadenza di scadenze(data) più vicina a D + `giorni` (di default solo i venerdì); None se non ce ne sono."""
    d = _d(data)
    cand = [s for s in scadenze(d) if not solo_venerdi or s.weekday() == 4]
    if not cand:
        return None
    obiettivo = d + _dt.timedelta(days=giorni)
    return min(cand, key=lambda s: (abs((s - obiettivo).days), s))


def _sorriso(voce, m, tipo):
    """IV alla moneyness m per una scadenza di un giorno. -> (iv, diretta: bool) o (None, False)."""
    altro = "P" if tipo == "C" else "C"
    for t, diretto in ((tipo, True), (altro, False)):
        if t not in voce:
            continue
        mm, vv, _ = voce[t]
        v = float(np.interp(m, mm, vv))  # piatta oltre i bordi
        vicino = float(np.min(np.abs(mm - m))) <= _TOLL_M  # uno scambio osservato a moneyness vicina
        return v, diretto and vicino
    return None, False


def iv(data, scadenza, strike, tipo, F=None, ora=12.0):
    """Volatilità implicita annua (frazione) per D, scadenza, strike (USD), tipo 'C'/'P'. -> (iv, qualita).

    qualita in {"scambi", "interpolata", "estesa", "mancante"} (vedi docstring del modulo).
    F: forward/prezzo di riferimento per la moneyness ln(K/F) (default spot(D), mediana del giorno). Passare il prezzo
       del momento d'ingresso (es. l'apertura del giorno) quando lo si conosce: la superficie è in moneyness, quindi
       la volatilità segue il prezzo del momento, non quello medio del giorno.
    ora: ora UTC di valutazione in D per il tempo a scadenza (default 12)."""
    tipo = tipo.upper()[0]
    d, scad = _d(data), _d(scadenza)
    T = _T(d, scad, ora)
    if T <= 0:
        return float("nan"), "mancante"
    g, k = _giorno_utile(d)
    if g is None:
        return float("nan"), "mancante"
    giorno = _carica()[g]
    m = math.log(float(strike) / (float(F) if F else giorno["F"]))
    v, diretta = _valuta(giorno, d, scad, T, m, tipo, ora)
    if v is None or not np.isfinite(v):
        return float("nan"), "mancante"
    if k > 0:
        return v, "estesa"
    return v, "scambi" if diretta else "interpolata"


def _valuta(giorno, d, scad, T, m, tipo, ora=12.0):
    """Calcolo su un giorno di dati: sorriso diretto se la scadenza c'è, altrimenti varianza totale fra scadenze."""
    voce = giorno["sc"].get(scad)
    if voce is not None:
        v, diretta = _sorriso(voce, m, tipo)
        if v is not None:
            return v, diretta
    punti = []  # (T da D, iv alla m)
    for s, vs in giorno["sc"].items():
        Ts = _T(d, s, ora)
        if Ts < 2 / 365:  # scadenze a meno di 2 giorni: IV rumorose, non usate per interpolare altre scadenze
            continue
        v, _ = _sorriso(vs, m, tipo)
        if v is not None:
            punti.append((Ts, v))
    if not punti:
        return None, False
    punti.sort()
    Ts = np.array([p[0] for p in punti])
    vs = np.array([p[1] for p in punti])
    if T <= Ts[0]:
        return float(vs[0]), False
    if T >= Ts[-1]:
        return float(vs[-1]), False
    i = int(np.searchsorted(Ts, T))
    T1, T2, v1, v2 = Ts[i - 1], Ts[i], vs[i - 1], vs[i]
    w = v1 * v1 * T1 + (v2 * v2 * T2 - v1 * v1 * T1) * (T - T1) / (T2 - T1)
    return float(math.sqrt(max(w, 1e-12) / T)), False


def _N(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black76(F, K, T, sigma, tipo):
    """Premio Black-76 senza sconto (tassi ≈ 0), in USD per 1 BTC di sottostante."""
    if T <= 0 or sigma <= 0:
        return max(F - K, 0.0) if tipo == "C" else max(K - F, 0.0)
    s = sigma * math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * s * s) / s
    d2 = d1 - s
    if tipo == "C":
        return F * _N(d1) - K * _N(d2)
    return K * _N(-d2) - F * _N(-d1)


def prezzo(data, scadenza, strike, tipo, F=None, ora=12.0):
    """Premio teorico Black-76 (USD per 1 BTC) con forward F (default spot(D)) e la volatilità di iv(). -> (premio, qualita).
    Il premio in BTC (come quotato su Deribit) è premio / F. Per F e ora vedi iv()."""
    tipo = tipo.upper()[0]
    v, q = iv(data, scadenza, strike, tipo, F=F, ora=ora)
    if q == "mancante":
        return float("nan"), q
    F = float(F) if F else spot(data)
    return black76(F, float(strike), _T(data, scadenza, ora), v, tipo), q
