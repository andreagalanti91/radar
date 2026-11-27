"""Registro sulla carta di V3 dello studio research/emergenti: solo gli short di W3.2 sulle monete emergenti
(research/emergenti/PREREG-AVANTI-V3.md, approvato il 27/11/2026, registro dal 30/11/2026). Nessun capitale, nessun ordine,
nessun avviso: il modulo scrive solo dati (data/emergenti_carta.json, report["emergenti_carta"]).

Regole (PREREG-AVANTI-V3.md, non si cambiano durante il registro):
- segnali: V3 come nello studio (scelta del 27/11/2026: prevale il PREREG). Motore research/emergenti/engine.py con i
  parametri di W3.2 (= radar.weekly.simulate senza l'arrotondamento dei prezzi a 0,01), long spenti, short ammessi solo nelle
  domeniche in cui la moneta è nella lista (rank 101–200) dell'anno del lunedì d'ingresso, come run.py (maschera "short").
  Differenza nota rispetto allo scanner: con i long spenti circa il 4% degli short parte una o più settimane prima, quando W3.2
  sarebbe ancora long (controllo su 20 monete: 18 short diversi su 229); il registro segue lo studio, non lo scanner. La lista
  2025 serve solo per il percorso prima del 2026 (posizioni aperte dal 2025 che occupano la moneta). Uscite di W3.2 (trailing,
  stop, EMA 21, distribuzione);
- budget di carta 10.000 $, massimo 5 posizioni, margine = min(valore del budget / 5, cassa) all'ingresso, nozionale = size di
  W3.2 nella quota (esposizione ≤ 1x), liquidazione a margine isolato (mantenimento 1%), costi 0,2% per lato più il funding reale
  (research/emergenti/engine.py outcome e portfolio, come lo studio); segnali dello stesso giorno in ordine di volume medio a
  90 giorni del perp; i segnali in eccesso si registrano come esclusi;
- solo gli ingressi dal 30/11/2026: le posizioni aperte dello studio al 24/11 non contano;
- valutazione non prima di 20 operazioni chiuse (stato "rivalutare"), con le soglie del PREREG (SOGLIE).

Liste annuali: 2026 = istantanea CoinMarketCap del 16/11/2025 (la più recente prima del 1/1/2026, Common Crawl;
research/emergenti/data/snapshots.csv, esclusioni e simboli di research/emergenti/data/universe.csv e sources.csv), salvata in
radar/emergenti_liste.json (`python -m radar.emergenti_carta lista` la riscrive). Dal 2027: classifica CoinGecko del giorno
(prime 200 con le esclusioni dello scanner, radar.scanner.build_universo_top200) presa al primo giro dell'anno nuovo, entro il
7 gennaio; se CoinGecko non risponde vale la lista settimanale dello scanner più recente prima del 1° gennaio, salvata nel
registro durante dicembre (campo "lista_candidata"). La lista congelata si salva nel registro ("liste") e non si riscrive.

Aggiornamento: a settimana nuova (domenica chiusa), dati dalla cache dello scanner (.scanner-cache/, scaricati solo i giorni
mancanti; fonti data-api.binance.vision, data.binance.vision, OKX: raggiungibili dai runner USA). Errori: resta l'ultimo stato
con l'avviso; il giro orario non si rompe (radar.cli._soft).
"""
from __future__ import annotations

import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import scanner as SC
from . import weekly as W

ROOT = Path(__file__).resolve().parent.parent
LISTE_FILE = Path(__file__).with_name("emergenti_liste.json")
FILE = "emergenti_carta.json"
INIZIO = "2026-11-30"
BUDGET = 10000.0
SLOTS = 5
FEE = 0.002                    # per lato (0,1% di slittamento nel prezzo del motore + 0,1% di commissione), come lo studio
MMR = 0.01
RANK = (101, 200)
FERMA_GIORNI = 7
NOTA = "sulla carta: nessun capitale, nessun ordine, nessun avviso"
SOGLIE = {"min_chiuse": 20, "wr_min": 50, "rendimento_min": 0, "dd_min": -25, "fase_btc_long_giorni": 182,
          "fase_btc_long_perdita_max": -10,
          "testo": "Non prima di 20 operazioni chiuse. Quota reale da riconsiderare solo se valgono tutte: WR ≥ 50%, rendimento del "
                   "budget positivo, DD giornaliero del budget ≥ −25%, almeno un semestre di fase non ribassista per le alt (BTC "
                   "W3.2 long) senza perdita maggiore di −10%. Altrimenti il registro si chiude. La decisione spetta all'utente."}
REGOLE = [
    "Short di W3.2 (parametri di BTC) solo sulle monete con rank 101–200 nella lista d'inizio anno; nessun long.",
    "Budget di carta 10.000 $, massimo 5 posizioni, margine 1/5 del budget (o la cassa se minore), size di W3.2 nella quota "
    "(esposizione ≤ 1x); i segnali con le quote piene si registrano come esclusi.",
    "Uscite di W3.2; costi 0,2% per lato più il funding reale; liquidazione a margine isolato.",
    "Solo ingressi dal 30/11/2026: le posizioni aperte dello studio al 24/11 non contano."]

_E = None


def engine():
    """research/emergenti/engine.py (copia di radar.weekly.simulate con indici, stop giornalieri, outcome e portfolio)."""
    global _E
    if _E is None:
        spec = importlib.util.spec_from_file_location("emergenti_engine", ROOT / "research" / "emergenti" / "engine.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _E = m
    return _E


# ------------------------------------------------------------------ liste annuali
def build_lista_studio(anno: int = 2026, d: Path = ROOT / "research" / "emergenti" / "data") -> dict:
    """Lista dell'anno dai file dello studio: rank 101–200 dell'istantanea CMC più recente prima del 1/1, senza esclusi, con la
    versione completa di W3.2 e una fonte dati viva (perp Binance attivo nell'archivio a novembre 2026, altrimenti perp OKX).
    Le monete già nello scanner (radar/scanner_universo.json) tengono i simboli e la cache dello scanner."""
    import re
    u = pd.read_csv(d / "universe.csv")
    cm = pd.read_csv(d / "counts_moneta.csv").set_index("ticker")
    src = pd.read_csv(d / "sources.csv").set_index("ticker")
    snap = pd.read_csv(d / "snapshots.csv", usecols=["anno", "data"])
    data_snap = str(int(snap.loc[snap["anno"] == anno, "data"].iloc[0]))
    static = {m["ticker"]: m for m in SC.carica_universo()}
    sel = u[(u[f"rank_{anno}"] > RANK[0] - 1) & (u[f"rank_{anno}"] <= RANK[1]) & u["escluso"].isna()]
    monete, senza = [], []

    def seg(txt, kind):
        out = [re.match(rf"binance {kind} (\S+) (\d{{4}}-\d\d-\d\d)\.\.(\d{{4}}-\d\d-\d\d)", p.strip()) for p in str(txt).split("|")]
        return [m.groups() for m in out if m and m.group(3) >= "2026-11-01"]
    for r in sel.itertuples():
        t, rk = r.ticker, int(getattr(r, f"rank_{anno}"))
        if t not in cm.index or pd.isna(cm.loc[t, "completa_da"]):
            senza.append({"t": t, "rk": rk, "motivo": "senza dati o senza versione completa di W3.2 nello studio"})
            continue
        okx = None if pd.isna(r.okx_perp_simbolo) else r.okx_perp_simbolo
        bitget = None if pd.isna(r.bitget_perp_simbolo) else r.bitget_perp_simbolo
        c = {"ticker": t, "nome": r.nome, "rank": rk}
        if t in static:
            s = static[t]
            c.update(spot=s["spot"], perp=s["perp"], div=s["div"], fonte="binance", okx=s.get("okx"), bitget=s.get("bitget"),
                     da=s.get("da"), spot_okx=None)
        else:
            pp = seg(src.loc[t, "perp"], "perp") if t in src.index else []
            sp = seg(src.loc[t, "spot"], "spot") if t in src.index else []
            if pp:
                perp = pp[-1][0]
                c.update(spot=sp[-1][0] if sp else None, perp=perp, fonte="binance", okx=okx, bitget=bitget, da=None, spot_okx=None,
                         div=1000000 if perp.startswith(("1M", "1000000")) else 1000 if perp.startswith("1000") else 1)
            elif okx and "okx swap" in str(src.loc[t, "perp"] if t in src.index else ""):
                c.update(spot=sp[-1][0] if sp else None, perp=okx, fonte="okx", okx=okx, bitget=bitget, da=None, div=1,
                         spot_okx=None if sp else f"{t}-USDT")
            else:
                senza.append({"t": t, "rk": rk, "motivo": "nessun perp vivo (Binance o OKX) a novembre 2026"})
                continue
        monete.append(c)
    monete.sort(key=lambda m: m["rank"])
    return {"anno": anno, "data": f"{data_snap[:4]}-{data_snap[4:6]}-{data_snap[6:]}",
            "fonte": f"CoinMarketCap {data_snap[6:]}/{data_snap[4:6]}/{data_snap[:4]} (Common Crawl), research/emergenti/data/snapshots.csv",
            "n_lista": len(sel), "n": len(monete), "monete": monete, "senza_dati": senza}


def lista_da_universo(u: dict, anno: int, fonte: str) -> dict:
    """Lista dell'anno dalla lista settimanale dello scanner (CoinGecko, esclusioni già applicate): rank 101–200 con una fonte dati."""
    sel = [m for m in u.get("monete", []) if m.get("rank_oggi") and RANK[0] <= m["rank_oggi"] <= RANK[1]]
    monete = [dict({k: m.get(k) for k in ("ticker", "nome", "spot", "spot_okx", "perp", "div", "fonte", "okx", "bitget", "da")},
                   rank=m["rank_oggi"]) for m in sel if m.get("perp")]
    return {"anno": anno, "data": u.get("aggiornato"), "fonte": fonte, "n_lista": len(sel), "n": len(monete), "monete": monete,
            "senza_dati": [{"t": m["ticker"], "rk": m["rank_oggi"], "motivo": m.get("nd") or "nessuna fonte dati"} for m in sel if not m.get("perp")]}


def liste_statiche(path: Path = LISTE_FILE) -> dict:
    try:
        return {str(k): v for k, v in json.loads(Path(path).read_text()).items()}
    except Exception:  # noqa: BLE001
        return {}


def aggiorna_liste(reg: dict, oggi: date, net: SC.Rete | None, cache: Path, static: dict | None = None) -> list[str]:
    """Liste annuali: quelle statiche (2026) più quelle congelate nel registro. Di dicembre si salva come candidata la lista
    settimanale dello scanner; dal 1° gennaio (entro il 7) si prova la classifica CoinGecko del giorno, altrimenti la candidata.
    Ritorna gli avvisi."""
    avvisi = []
    liste = reg.setdefault("liste", {})
    static = liste_statiche() if static is None else static
    y = oggi.year
    if oggi.month == 12:
        try:
            u = SC.universo_precedente(cache)
            if (u.get("aggiornato") or "") >= f"{y}-12-01":
                reg["lista_candidata"] = lista_da_universo(u, y + 1, f"CoinGecko, lista settimanale dello scanner del {u['aggiornato']}")
        except Exception as e:  # noqa: BLE001
            avvisi.append(f"lista candidata per il {y + 1} non salvata ({type(e).__name__})")
    if str(y) not in static and str(y) not in liste:
        lista = None
        if oggi <= date(y, 1, 7) and net is not None:
            try:
                prev = SC.universo_precedente(cache)
                u = SC.build_universo_top200(net, oggi, prev)
                lista = lista_da_universo(u, y, f"CoinGecko /coins/markets del {oggi} (prime 200, esclusioni dello scanner)")
            except Exception as e:  # noqa: BLE001
                avvisi.append(f"classifica CoinGecko del {oggi} non disponibile ({type(e).__name__})")
        cand = reg.get("lista_candidata")
        if lista is None and cand and cand.get("anno") == y:
            lista = cand
        if lista is not None:
            liste[str(y)] = lista
            reg.pop("lista_candidata", None)
        else:
            avvisi.append(f"lista {y} non disponibile: nessun ingresso nuovo finché non c'è")
    return avvisi


def tutte_le_liste(reg: dict, static: dict | None = None) -> dict:
    return (liste_statiche() if static is None else static) | dict(reg.get("liste") or {})


def membri(liste: dict) -> dict[int, set]:
    return {int(a): {m["ticker"] for m in l["monete"]} for a, l in liste.items()}


# ------------------------------------------------------------------ segnali e candidati
def inizio_sim(f: pd.DataFrame) -> str | None:
    """Lunedì dopo la prima domenica con SMA 40 settimane e flusso perp calcolabili (come radar.scanner.stato_moneta)."""
    w = W.weekly_bars(f)
    ok = w[w["sma"].notna() & w["flow"].notna()]
    return None if ok.empty else str((ok.index[0] + pd.Timedelta(days=1)).date())


def segnali(t: str, f: pd.DataFrame, memb: dict[int, set], inizio: str = INIZIO) -> tuple[list[dict], dict | None]:
    """Short di V3 come nello studio (research/emergenti/run.py, maschera "short"): motore con i parametri di W3.2, long spenti,
    short ammessi solo nelle domeniche in cui la moneta è nella lista dell'anno del lunedì d'ingresso; si tengono gli ingressi dal
    `inizio`. Più l'eventuale ingresso short in sospeso (segnale dell'ultima domenica)."""
    E = engine()
    f = f[f["close"].notna()]
    s0 = inizio_sim(f)
    if s0 is None:
        return [], None
    w = E.weekly_bars(f)
    sun = w.index
    al = pd.Series(False, index=sun)
    as_ = pd.Series([t in memb.get((s + pd.Timedelta(days=1)).year, set()) for s in sun], index=sun)
    with np.errstate(divide="ignore", invalid="ignore"):
        o = E.simulate(f, start=s0, allow_long=al, allow_short=as_, all_perp=True)
    out = [tr for tr in E.all_trades(o) if tr["side"] == "short" and tr["entry"] >= inizio]
    pend = None
    dom = f.index[-1]
    if dom.dayofweek == 6 and o["open"] is None and dom in w.index and pd.Timestamp(s0) <= dom:
        wk = w.loc[dom]
        ing = str((dom + pd.Timedelta(days=1)).date())
        if bool(wk["short"]) and bool(as_.get(dom, False)) and ing >= inizio:
            pend = {"t": t, "sig": str(dom.date()), "ing": ing}
    return out, pend


def vol90(perp: pd.DataFrame | None) -> pd.Series:
    if perp is None or not len(perp) or not {"close", "volume"} <= set(perp.columns):
        return pd.Series(dtype=float)
    return (perp["close"] * perp["volume"]).rolling(90, min_periods=30).mean()


def _trail(tr: dict) -> float:
    """Stop valido dal giorno dopo (come il campo trail di radar.weekly.simulate e dello scanner): a cricchetto sul trailing
    dalla miglior chiusura con l'ATR settimanale corrente."""
    sd = 1 if tr["side"] == "long" else -1
    tl = tr["best"] - sd * W.TRAIL_K * tr["curatr"]
    return float(max(tr["stop"], tl) if sd > 0 else min(tr["stop"], tl))


def candidati(t: str, trades: list[dict], f: pd.DataFrame, G: pd.DatetimeIndex, v90: pd.Series | None = None) -> list[dict]:
    """Esito giornaliero per 1 $ di margine (engine.outcome, nozionale = size di W3.2) sulla griglia comune G. Una posizione aperta
    su una moneta con i dati fermi resta aperta fino alla fine della griglia all'ultimo valore."""
    E = engine()
    f = f[f["close"].notna()]
    A = {k: f[c].to_numpy(float) for k, c in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}
    A["FU"] = f["funding"].fillna(0).to_numpy(float)
    out = []
    for tr in trades:
        r0, r1, v, liq = E.outcome(tr, A, tr["expo"], fee=FEE, mmr=MMR)
        d = f.index[r0:r1 + 1]
        if d[0] > G[-1]:
            continue
        g0 = int(G.searchsorted(d[0]))
        aperta = tr["reason"] == "open" and not liq
        g1 = len(G) - 1 if aperta else int(G.searchsorted(min(d[-1], G[-1])))
        vg = pd.Series(v, index=d).reindex(G[g0:g1 + 1]).ffill().to_numpy()
        intra = liq or (tr["reason"] in ("stop", "trail") and r1 == tr["i_exit"])
        s = pd.Timestamp(tr["signal"])
        pri = float(v90.get(s, np.nan)) if v90 is not None and s in v90.index else np.nan
        px_out = None
        if liq:
            px_out = tr["entry_px"] * (1 + (1 / tr["expo"] - MMR))
        elif not aperta:
            px_out = tr["exit_px"]
        out.append({"t": t, "sig": tr["signal"], "ing": tr["entry"], "usc": None if aperta else str(d[-1].date()),
                    "px_in": tr["entry_px"], "px_out": px_out, "ult": float(f["close"].iloc[r1]),
                    "trail": _trail(tr), "k": tr["expo"],
                    "motivo": "liquidazione" if liq else W.REASONS.get(tr["reason"], tr["reason"]), "liq": liq, "aperta": aperta,
                    "i0": g0, "i1": g1, "v": vg, "intra": intra, "pri": pri if pri == pri else 0.0,
                    "dati_fino": str(f.index[-1].date())})
    return out


# ------------------------------------------------------------------ portafoglio e metriche
def portafoglio(cands: list[dict], G: pd.DatetimeIndex, budget: float = BUDGET, slots: int = SLOTS) -> dict:
    """engine.portfolio (come lo studio): massimo `slots` posizioni, margine min(valore/slots, cassa). Ritorna valore giornaliero,
    posizioni aperte, chiuse ed esclusi (segnali con le quote piene)."""
    if not len(G):
        return {"eq": np.array([budget]), "aperte": [], "chiuse": [], "esclusi": []}
    E = engine()
    eq, taken = E.portfolio([dict(c) for c in cands], len(G), slots=slots, budget=budget, start_i=0)
    presi = {(p["t"], p["i0"]) for p in taken}
    aperte, chiuse = [], []
    for p in sorted(taken, key=lambda p: (p["i0"], p["t"])):
        pnl = float(p["v"][-1] - 1)
        r = {"t": p["t"], "ing": p["ing"], "px_in": SC._r(p["px_in"], 8), "quota": round(float(p["m"]), 2),
             "pnl": round(pnl * 100, 2), "pnl_usd": round(float(p["m"]) * pnl, 2)}
        if p["aperta"]:
            aperte.append(dict(r, ult=SC._r(p["ult"], 8), mv=round(float(1 - p["ult"] / p["px_in"]) * 100, 1),
                               trail=SC._r(p["trail"], 8), sig=p["sig"], dati_fino=p["dati_fino"]))
        else:
            chiuse.append(dict(r, usc=p["usc"], px_out=SC._r(p["px_out"], 8), motivo=p["motivo"]))
    esclusi = [{"t": c["t"], "sig": c["sig"], "ing": c["ing"], "motivo": f"quote piene ({slots} posizioni) o cassa esaurita"}
               for c in sorted(cands, key=lambda c: (c["i0"], -c["pri"])) if (c["t"], c["i0"]) not in presi]
    return {"eq": np.asarray(eq, float), "aperte": aperte, "chiuse": chiuse, "esclusi": esclusi}


def metriche(eq: np.ndarray, chiuse: list[dict], G: pd.DatetimeIndex, fase_btc: pd.Series | None = None,
             budget: float = BUDGET) -> dict:
    """Valore, rendimento, DD giornaliero, WR delle chiuse; verifica delle soglie del PREREG e stato."""
    eq = np.asarray(eq, float)
    valore = float(eq[-1]) if len(eq) else budget
    x = pd.Series(np.r_[budget, eq])
    dd = float((x / x.cummax() - 1).min() * 100)
    n = len(chiuse)
    wr = round(sum(c["pnl"] > 0 for c in chiuse) / n * 100, 1) if n else None
    rend = round((valore / budget - 1) * 100, 2)
    giorni = rend_fase = None
    if fase_btc is not None and len(G) and len(eq):
        g = fase_btc.reindex(G).fillna(0).to_numpy()
        r = np.r_[eq[0] / budget, eq[1:] / eq[:-1]] - 1
        giorni = int((g > 0).sum())
        rend_fase = round(float(np.prod(1 + r[g > 0]) - 1) * 100, 2) if giorni else None
    S = SOGLIE
    ver = {"chiuse": {"valore": n, "ok": n >= S["min_chiuse"]},
           "wr": {"valore": wr, "ok": wr is not None and wr >= S["wr_min"]},
           "rendimento": {"valore": rend, "ok": rend > S["rendimento_min"]},
           "dd": {"valore": round(dd, 2), "ok": dd >= S["dd_min"]},
           "fase_btc_long": {"giorni": giorni, "valore": rend_fase,
                             "ok": bool(giorni is not None and giorni >= S["fase_btc_long_giorni"] and rend_fase is not None
                                        and rend_fase >= S["fase_btc_long_perdita_max"])}}
    stato = "rivalutare" if n >= S["min_chiuse"] else "in raccolta"
    esito = None
    if stato == "rivalutare":
        esito = ("tutte le condizioni valgono: quota reale da riconsiderare (decide l'utente)" if all(v["ok"] for v in ver.values())
                 else "condizioni non tutte vere: il registro si chiude (decide l'utente)")
    return {"valore": round(valore, 2), "rendimento": rend, "dd": round(dd, 2), "n_chiuse": n, "wr": wr, "verifica": ver,
            "stato": stato, "esito": esito}


def fase_btc(f_btc: pd.DataFrame | None) -> pd.Series | None:
    """+1 nei giorni in cui W3.2 su BTC è long (cancello della domenica precedente, valido per la settimana dopo)."""
    if f_btc is None or not len(f_btc):
        return None
    g = SC.cancello(f_btc)
    s = g.copy()
    s.index = s.index + pd.Timedelta(days=1)
    return s.reindex(pd.date_range(s.index[0], f_btc.index[-1] + pd.Timedelta(days=1))).ffill()


def calcola(dati: dict[str, dict], liste: dict, oggi: date, f_btc: pd.DataFrame | None = None, inizio: str = INIZIO,
            budget: float = BUDGET) -> dict:
    """Registro dal `inizio` a partire dalle feature delle monete (`dati[t] = {"f": feature, "perp": perp grezzo}`), solo giorni
    chiusi prima di `oggi`. Puro (senza rete)."""
    memb = membri(liste)
    tutti, attesa, fino = {}, [], []
    for t, x in dati.items():
        f = x.get("f")
        if f is None or not len(f):
            continue
        f = f[f.index.date < oggi]
        if not len(f):
            continue
        fino.append(f.index[-1])
        trs, pend = segnali(t, f, memb, inizio)
        tutti[t] = (f, trs, vol90(x.get("perp")))
        if pend:
            attesa.append(pend)
    fine = max(fino) if fino else None
    G = pd.date_range(inizio, fine) if fine is not None and fine >= pd.Timestamp(inizio) else pd.DatetimeIndex([])
    cands = []
    if len(G):
        for t, (f, trs, v90) in tutti.items():
            cands += candidati(t, trs, f, G, v90)
    pf = portafoglio(cands, G, budget)
    m = metriche(pf["eq"], pf["chiuse"], G, fase_btc(f_btc), budget)
    ferme = sorted(t for t, (f, _, _) in tutti.items() if fine is not None and (fine - f.index[-1]).days > FERMA_GIORNI)
    return {"posizioni": pf["aperte"], "chiuse": pf["chiuse"], "esclusi": pf["esclusi"], "in_attesa": attesa, **m,
            "dati_fino": str(fine.date()) if fine is not None else None, "n_monete": len(tutti), "ferme": ferme,
            "serie": {"date": [str(d.date()) for d in G], "valore": [round(float(v), 2) for v in pf["eq"]]} if len(G) else None}


# ------------------------------------------------------------------ registro e giro
def _vuoto() -> dict:
    return {"inizio": INIZIO, "budget": BUDGET, "settimana": None, "aggiornato": None, "posizioni": [], "chiuse": [], "esclusi": [],
            "in_attesa": [], "valore": BUDGET, "rendimento": 0.0, "dd": 0.0, "n_chiuse": 0, "wr": None, "stato": "in raccolta",
            "liste": {}}


def _lista_meta(liste: dict, anno: int) -> dict:
    l = liste.get(str(anno))
    if not l:
        return {"anno": anno, "fonte": None, "n": 0, "nota": "lista non ancora disponibile"}
    return {"anno": anno, "fonte": l.get("fonte"), "data": l.get("data"), "n": l.get("n"), "n_lista": l.get("n_lista"),
            "tickers": [m["ticker"] for m in l.get("monete", [])]}


def unisci_chiuse(vecchie: list[dict], nuove: list[dict]) -> list[dict]:
    """Una chiusa già registrata non si riscrive; quelle nuove si aggiungono."""
    k = lambda r: f"{r['t']}|{r['ing']}"  # noqa: E731
    have = {k(r) for r in vecchie}
    return list(vecchie) + [r for r in nuove if k(r) not in have]


def build(reg: dict, now: datetime, dati: dict | None = None, static: dict | None = None) -> dict:
    oggi = pd.Timestamp(now).date()
    liste = tutte_le_liste(reg, static)
    anno = max(oggi.year, int(INIZIO[:4]))
    out = {k: reg.get(k) for k in ("inizio", "budget", "aggiornato", "settimana", "dati_fino", "posizioni", "chiuse", "esclusi",
                                    "in_attesa", "valore", "rendimento", "dd", "n_chiuse", "wr", "stato", "esito", "verifica",
                                    "serie", "ferme")}
    out.update(soglie=SOGLIE, lista=_lista_meta(liste, anno), regole=REGOLE, nota=NOTA,
               dati=dati or reg.get("dati") or {"ritardo": False, "nota": None})
    return out


def _coin_dicts(liste: dict, cache: Path) -> list[dict]:
    """Monete di tutte le liste (più recente per prima), con i simboli della lista settimanale dello scanner se c'è la moneta."""
    try:
        sett = {m["ticker"]: m for m in SC.universo_precedente(cache)["monete"] if m.get("perp")}
    except Exception:  # noqa: BLE001
        sett = {}
    out = {}
    for a in sorted((a for a in liste if int(a) >= int(INIZIO[:4])), reverse=True):   # 2025: solo percorso, nessun ingresso
        for m in liste[a]["monete"]:
            if m["ticker"] not in out:
                s = sett.get(m["ticker"])
                out[m["ticker"]] = {k: (s or m).get(k) for k in ("ticker", "spot", "spot_okx", "perp", "div", "fonte", "da", "okx", "bitget")}
    return [c for c in out.values() if c.get("perp")]


def scarica(coins: list[dict], net: SC.Rete, oggi: date, cache: Path, seed_dir: Path | None, threads: int = SC.THREADS) -> tuple[dict, list]:
    da = oggi - timedelta(days=SC.WINDOW_DAYS)

    def uno(c):
        try:
            s = SC.aggiorna_moneta(net, c, cache, oggi, da, seed_dir)
        except SC.ReteNonDisponibile as e:
            s = dict(SC.cache_moneta(c, cache, da, seed_dir), errore=f"rete: {str(e)[:60]}")
        return c["ticker"], s
    with ThreadPoolExecutor(threads) as ex:
        res = list(ex.map(uno, coins))
    dati, errori = {}, []
    for t, s in res:
        if s["errore"]:
            errori.append(t)
        dati[t] = {"f": SC.feats(s["spot"], s["perp"], s["funding"]), "perp": s.get("perp")}
    return dati, errori


def giro(f_btc: pd.DataFrame | None, data_dir: Path, now: datetime | None = None, net: SC.Rete | None = None,
         cache: Path = SC.CACHE_DIR, seed_dir: Path | None = SC.SEED_DIR, static: dict | None = None,
         dati: dict | None = None) -> dict:
    """Un giro orario: a settimana nuova (domenica chiusa) ricalcola il registro e salva data/emergenti_carta.json; altrimenti
    restituisce quello salvato. Prima della prima domenica di segnale (29/11/2026) nessuna richiesta. Errori: ultimo stato con
    l'avviso. `dati` (feature per moneta) solo per i test."""
    now = now or datetime.now(timezone.utc)
    data_dir = Path(data_dir)
    path = data_dir / FILE
    reg = SC._load(path) or _vuoto()
    oggi = pd.Timestamp(now).date()
    dom = SC.ultima_domenica(now)
    primo = date.fromisoformat(INIZIO) - timedelta(days=1)
    if reg.get("settimana") == str(dom) and path.exists():
        return build(reg, now, static=static)
    try:
        avvisi = []
        if dom >= primo:
            net = net or SC.Rete()
            avvisi += aggiorna_liste(reg, oggi, net if dati is None else None, cache, static)
            liste = tutte_le_liste(reg, static)
            errori = []
            if dati is None:
                coins = _coin_dicts(liste, cache)
                dati, errori = scarica(coins, net, oggi, cache, seed_dir)
                if len(errori) > len(coins) / 2:
                    raise SC.ReteNonDisponibile(f"dati non aggiornati per {len(errori)} monete su {len(coins)}")
            out = calcola(dati, liste, oggi, f_btc)
            out["chiuse"] = unisci_chiuse(reg.get("chiuse") or [], out["chiuse"])
            reg.update(out)
            if errori:
                avvisi.append(f"dati non aggiornati per {', '.join(errori)}: valori sull'ultima cache")
            if out["ferme"]:
                avvisi.append(f"dati fermi da oltre {FERMA_GIORNI} giorni: {', '.join(out['ferme'])}")
        reg["settimana"] = str(dom)
        reg["aggiornato"] = pd.Timestamp(now).isoformat(timespec="minutes")
        reg["dati"] = {"ritardo": bool(avvisi), "nota": "; ".join(avvisi) or None}
    except Exception as e:  # noqa: BLE001
        print(f"[radar] emergenti sulla carta: aggiornamento non riuscito ({e!r}): resta l'ultimo stato")
        return build(reg, now, {"ritardo": True, "nota": f"Registro non aggiornato ({type(e).__name__}): ultimo stato salvato.",
                                "errore": f"{type(e).__name__}: {str(e)[:120]}"}, static)
    data_dir.mkdir(parents=True, exist_ok=True)
    out = build(reg, now, static=static)
    path.write_text(json.dumps(dict(out, liste=reg.get("liste") or {}, lista_candidata=reg.get("lista_candidata")),
                               ensure_ascii=False, separators=(",", ":"), default=str))
    print(f"[radar] emergenti sulla carta (V3): {len(out['posizioni'] or [])} aperte, {out['n_chiuse']} chiuse, valore {out['valore']} $"
          f", stato {out['stato']}" + (f" · {reg['dati']['nota']}" if reg["dati"]["nota"] else ""))
    return out


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["lista"]:
        l, l25 = build_lista_studio(2026), build_lista_studio(2025)
        LISTE_FILE.write_text(json.dumps({"2025": l25, "2026": l}, ensure_ascii=False, indent=0, default=str))
        print(f"{LISTE_FILE}: {l['n']} monete su {l['n_lista']} della lista 2026")
    else:
        print("uso: python -m radar.emergenti_carta lista")
