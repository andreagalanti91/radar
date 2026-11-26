"""Mercato power (pagina Oggi e Posizioni): sei semafori di contesto rispetto alla posizione aperta di W3.2, per BTC ed ETH.

Ogni semaforo dice se un dato di mercato è A FAVORE, NEUTRO o CONTRO la posizione aperta. Nessun punteggio unico: la pagina
mostra solo il conteggio "N a favore · N neutri · N contro". È contesto: decide W3.2 (le regole, i segnali, gli stop e il
capitale non leggono questo modulo). L'unico dei sei che W3.2 usa davvero è "Flusso e funding perp" (uscita per distribuzione).

Regole (proposta dell'anteprima "Cruscotto a tessere", 26/11/2026; le stesse frasi compaiono nel pannello "Dettagli ›"):

1. Ciclo on-chain (report.onchain, MVRV con le zone dello studio research/utxo_pl)
   zona capitolazione → a favore del long, contro lo short (vicino ai minimi di ciclo, rischio di rimbalzo);
   zona euforia → a favore dello short, contro il long; zona normale → neutro.
2. Dollaro (report.dollaro, DXY con EMA20/50 e divergenze come research/dxy_divergenza)
   dollaro forte → a favore dello short, contro il long; dollaro debole → a favore del long, contro lo short;
   in indebolimento (divergenza ancora da confermare) → neutro.
3. OPEX (report.opex, scadenze delle opzioni su BTC)
   solo se la scadenza principale è entro 7 giorni e il massimo dolore dista più del 3% dal prezzo: massimo dolore sopra il
   prezzo → a favore del long, contro lo short; sotto → a favore dello short, contro il long; altrimenti neutro.
4. VIX (report.macro, chiusura del VIX)
   sopra 30 (paura alta, mercati in fuga dal rischio) → a favore dello short, contro il long; sotto 15 (mercato tranquillo)
   → a favore del long, contro lo short; fra 15 e 30 → neutro.
5. Fed e calendario (report.banks, report.context)
   riunione FOMC entro 3 giorni → contro (rischio di un movimento brusco in qualsiasi verso, per long e short); altrimenti
   neutro: tassi e inflazione nei test non hanno anticipato la direzione di BTC (lezione 113).
6. Flusso e funding perp (report.weekly / weekly_eth: flusso CVD 14 g e funding 7 g, gli stessi dati dell'uscita per distribuzione)
   distribuzione attiva → contro; flusso nel verso della posizione (negativo per lo short, positivo per il long) → a favore;
   altrimenti neutro.

Senza posizione aperta su un asset i semafori sono neutri e la riga lo dice. Registro giornaliero: data/mercato_power.csv,
una riga al giorno per asset (la più recente del giorno sostituisce le precedenti), per verificare in futuro se i semafori
avevano ragione. Nessun avviso Telegram.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

NOTA = "Contesto: decide W3.2. Nessun punteggio unico; solo il flusso e funding dei perp entra nelle regole (uscita per distribuzione)."
LOG_FILE = "mercato_power.csv"
STATI = ("favore", "neutro", "contro")
OPEX_GIORNI = 7          # scadenza considerata solo entro 7 giorni
OPEX_DIST = 3.0          # massimo dolore oltre il 3% dal prezzo
VIX_ALTO = 30.0
VIX_BASSO = 15.0
FOMC_GIORNI = 3

# chiave, nome, regola (testo del pannello)
SEMAFORI = [
    ("onchain", "Ciclo on-chain", "Capitolazione: a favore del long, contro lo short. Euforia: a favore dello short, contro il long. Zona normale: neutro."),
    ("dollaro", "Dollaro", "Dollaro forte: a favore dello short, contro il long. Debole: a favore del long, contro lo short. In indebolimento (divergenza da confermare): neutro."),
    ("opex", "OPEX", f"Solo con la scadenza entro {OPEX_GIORNI} giorni e il massimo dolore a più del {OPEX_DIST:.0f}% dal prezzo: sopra il prezzo a favore del long e contro lo short, sotto il contrario. Altrimenti neutro."),
    ("vix", "VIX", f"Sopra {VIX_ALTO:.0f} (paura alta): a favore dello short, contro il long. Sotto {VIX_BASSO:.0f} (mercato tranquillo): a favore del long, contro lo short. Fra {VIX_BASSO:.0f} e {VIX_ALTO:.0f}: neutro."),
    ("fed", "Fed e calendario", f"Riunione FOMC entro {FOMC_GIORNI} giorni: contro (movimento brusco possibile in qualsiasi verso). Altrimenti neutro: tassi e inflazione non hanno anticipato la direzione (lezione 113)."),
    ("flusso", "Flusso e funding perp", "Distribuzione attiva: contro. Flusso dei perp nel verso della posizione (negativo per lo short, positivo per il long): a favore. Altrimenti neutro. È l'unico dei sei che W3.2 usa per decidere."),
]
NOMI = {k: n for k, n, _ in SEMAFORI}
REGOLE = {k: r for k, _, r in SEMAFORI}


def _n(x: float, d: int = 0) -> str:
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 and any(c in "123456789" for c in s) else "") + s


def _dm(s: str) -> str:
    return f"{s[8:10]}/{s[5:7]}"


def _pro(side: str | None, favore_long: bool | None) -> str:
    """favore_long True = il dato aiuta il long (quindi va contro lo short); False il contrario; None neutro."""
    if side not in ("long", "short") or favore_long is None:
        return "neutro"
    return "favore" if favore_long == (side == "long") else "contro"


def side_of(w: dict | None) -> str | None:
    if w and w.get("status") in ("aperto", "uscita") and w.get("side") in ("long", "short"):
        return w["side"]
    return None


# ------------------------------------------------------------------ i sei semafori
def s_onchain(oc: dict | None, side: str | None) -> dict | None:
    if not oc or oc.get("mvrv") is None:
        return None
    z = oc.get("zone")
    fl = True if z == "cap" else False if z == "eup" else None
    return {"stato": _pro(side, fl), "valore": f"MVRV {_n(oc['mvrv'], 2)}", "etichetta": str(oc.get("zone_name") or "normale").lower(),
            "perche": oc.get("breve") or ("Zona normale del ciclo" if z == "norm" else "")}


def s_dollaro(dx: dict | None, side: str | None) -> dict | None:
    if not dx or dx.get("close") is None:
        return None
    st = dx.get("state")
    fl = False if st == "forte" else True if st == "debole" else None
    lab = {"forte": "forte", "debole": "debole", "indeb": "divergenza da confermare"}.get(st, str(st or ""))
    nome = "Indice Fed" if dx.get("src") == "fred" else "DXY"
    return {"stato": _pro(side, fl), "valore": f"{nome} {_n(dx['close'], 2)}", "etichetta": lab, "perche": str(dx.get("frase") or "")}


def s_opex(ox: dict | None, side: str | None) -> dict | None:
    if not ox or ox.get("max_pain") is None or ox.get("dist_pct") is None:
        return None
    h, d = ox.get("hours"), ox["dist_pct"]
    vicino = h is not None and h <= OPEX_GIORNI * 24
    fl = (d > 0) if vicino and abs(d) > OPEX_DIST else None
    st = str(ox.get("status") or "")
    tag = st.replace("Scadenza ", "").replace("venerdì", "ven").replace("lunedì", "lun").replace("martedì", "mar") \
        .replace("mercoledì", "mer").replace("giovedì", "gio").replace("sabato", "sab").replace("domenica", "dom")
    return {"stato": _pro(side, fl), "valore": f"max pain {_n(ox['max_pain'] / 1000, 0)}k", "etichetta": tag,
            "perche": str(ox.get("frase") or "").replace(" — solo contesto", "")}


def s_vix(macro: dict | None, ctx: dict | None, side: str | None) -> dict | None:
    v = d20 = date = None
    for a in (macro or {}).get("assets") or []:
        if a.get("key") == "vix" and a.get("close") is not None:
            v, d20, date = a["close"], a.get("d20_pct"), a.get("date")
    if v is None:
        x = ((ctx or {}).get("fed") or {}).get("vix") or {}
        v, date = x.get("value"), x.get("date")
    if v is None:
        return None
    fl = False if v > VIX_ALTO else True if v < VIX_BASSO else None
    lab = f"paura alta (sopra {VIX_ALTO:.0f})" if v > VIX_ALTO else f"mercato tranquillo (sotto {VIX_BASSO:.0f})" if v < VIX_BASSO \
        else f"normale ({VIX_BASSO:.0f}–{VIX_ALTO:.0f})"
    pr = (f"Tensione {'in aumento' if d20 > 0 else 'in calo'} ({'+' if d20 > 0 else ''}{_n(d20, 1)}% in 20 g)" if d20 is not None else "Volatilità attesa sulle azioni USA")
    pr += ", sopra la soglia di paura" if v > VIX_ALTO else ", sotto la soglia di paura" if v >= VIX_BASSO else ", mercato tranquillo"
    return {"stato": _pro(side, fl), "valore": _n(v, 1), "etichetta": lab, "perche": pr, "data": date}


def s_fed(banks: list | None, ctx: dict | None, side: str | None, today) -> dict | None:
    fomc = sorted((b for b in (banks or []) if b.get("bank") == "Fed" and b.get("date") and b["date"] >= today.isoformat()),
                  key=lambda b: b["date"])
    nx = fomc[0]["date"] if fomc else ((ctx or {}).get("fed") or {}).get("next_fomc")
    if not nx:
        return None
    gg = (datetime.fromisoformat(nx).date() - today).days
    stato = "contro" if side in ("long", "short") and gg <= FOMC_GIORNI else "neutro"
    fed = (ctx or {}).get("fed") or {}
    r, c = (fed.get("rate") or {}).get("direction"), (fed.get("cpi") or {}).get("direction")
    pr = ("Tasso " + r if r else "") + (", inflazione " + c if c else "")
    pr = (pr[0].upper() + pr[1:] + ": " if pr else "") + ("riunione a ridosso, movimento brusco possibile" if gg <= FOMC_GIORNI else "evento atteso, nessuna direzione")
    return {"stato": stato, "valore": f"FOMC {_dm(nx)}", "etichetta": "oggi" if gg <= 0 else "domani" if gg == 1 else f"tra {gg} g", "perche": pr}


def s_flusso(w: dict | None, side: str | None) -> dict | None:
    if not w or w.get("flow") is None:
        return None
    f, U = w["flow"], (w.get("uscite") or {}).get("dist") or {}
    attiva = bool(U.get("attiva", w.get("dist_now")))
    if side not in ("long", "short"):
        stato = "neutro"
    elif attiva:
        stato = "contro"
    elif (f < 0) == (side == "short") and f != 0:
        stato = "favore"
    else:
        stato = "neutro"
    fund = U.get("fund7", w.get("fund7"))
    pr = f"flusso perp {_n(f, 2)}σ" + (f" · funding 7 g {_n(fund * 100, 3)}%" if fund is not None else "")
    pr += " · distribuzione attiva" if attiva else " · nessuna uscita per distribuzione"
    return {"stato": stato, "valore": f"{_n(f, 2)}σ", "etichetta": "in vendita" if f < 0 else "in acquisto", "perche": pr, "w3": True}


def conteggio(items: list) -> dict:
    return {s: sum(1 for i in items if i["stato"] == s) for s in STATI}


def riga(c: dict) -> str:
    return f"{c['favore']} a favore · {c['neutro']} {'neutro' if c['neutro'] == 1 else 'neutri'} · {c['contro']} contro"


def per_asset(report: dict, asset: str, today) -> dict | None:
    w = report.get("weekly" if asset == "BTC" else "weekly_eth")
    if not w:
        return None
    side = side_of(w)
    calc = {"onchain": lambda: s_onchain(report.get("onchain"), side), "dollaro": lambda: s_dollaro(report.get("dollaro"), side),
            "opex": lambda: s_opex(report.get("opex"), side), "vix": lambda: s_vix(report.get("macro"), report.get("context"), side),
            "fed": lambda: s_fed(report.get("banks"), report.get("context"), side, today), "flusso": lambda: s_flusso(w, side)}
    items = []
    for k, nome, regola in SEMAFORI:
        try:
            x = calc[k]()
        except Exception as e:  # noqa: BLE001  un dato malformato non toglie gli altri semafori
            print(f"[mercato] {k} non calcolato: {e!r}")
            x = None
        if x:
            items.append({"key": k, "nome": nome, "regola": regola, "w3": bool(x.pop("w3", False)), **x})
    c = conteggio(items)
    return {"asset": asset, "lato": side, "prezzo": w.get("price"), "items": items, "conteggio": c,
            "riga": riga(c) if side else "nessuna posizione aperta: semafori neutri"}


def build(report: dict, data_dir: Path | None = None, now: datetime | None = None) -> dict:
    """report["mercato"] = {"assets": {"BTC": {...}, "ETH": {...}}, "nota", "data"}; con data_dir aggiorna il registro."""
    now = now or datetime.now(timezone.utc)
    today = now.date()
    out = {"data": today.isoformat(), "nota": NOTA, "assets": {}}
    for a in ("BTC", "ETH"):
        x = per_asset(report, a, today)
        if x:
            out["assets"][a] = x
    if data_dir is not None and out["assets"]:
        log(Path(data_dir), out)
    return out


COLS = ["data", "asset", "lato", "prezzo"] + [k for k, _, _ in SEMAFORI] + ["favore", "neutri", "contro"]


def log(data_dir: Path, m: dict, prezzi: dict | None = None) -> Path:
    """Una riga al giorno per asset: la più recente del giorno sostituisce le precedenti."""
    p = data_dir / LOG_FILE
    rows = []
    if p.exists():
        with p.open(newline="") as f:
            rows = [r for r in csv.DictReader(f)]
    keep = {(m["data"], a) for a in m["assets"]}
    rows = [r for r in rows if (r.get("data"), r.get("asset")) not in keep]
    for a, x in m["assets"].items():
        st = {i["key"]: i["stato"] for i in x["items"]}
        rows.append({"data": m["data"], "asset": a, "lato": x["lato"] or "flat", "prezzo": (prezzi or {}).get(a, x.get("prezzo", "")),
                     **{k: st.get(k, "") for k, _, _ in SEMAFORI},
                     "favore": x["conteggio"]["favore"], "neutri": x["conteggio"]["neutro"], "contro": x["conteggio"]["contro"]})
    rows.sort(key=lambda r: (r["data"], r["asset"]))
    data_dir.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in COLS} for r in rows)
    return p
