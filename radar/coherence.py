"""Controlli di coerenza orari sui dati e sullo storico di W3.1 (solo avviso: non cambiano dati, segnali né posizione).

A ogni giro (radar.cli.daily, dopo la valutazione di W3.1 e prima del messaggio di salute):
- buchi: giorni mancanti negli ultimi GAP_DAYS giorni delle fonti giornaliere di W3.1 (data.CRITICAL). L'avviso "dati vecchi"
  guarda solo l'ultimo giorno; un buco in mezzo falsa medie e flusso senza che nessuno lo veda;
- storico riscritto: un trade della simulazione W3.1 già visto in un giro precedente (per data del segnale) che sparisce, cambia
  lato o ingresso, oppure, se era chiuso, cambia uscita o motivo. Succede quando i dati provvisori (OKX) vengono sostituiti da
  quelli definitivi (archivio Binance) e una decisione passata non è più la stessa;
- decisione cambiata: riga del registro domenicale provvisori/definitivi (radar/provlog.py) con "changed" vero.
Un solo messaggio Telegram per evento: marker in data/state.json (chiave "coherence"), scritti solo se Telegram conferma.
I problemi in corso entrano anche nel messaggio di salute quotidiano. Le soglie d'allarme sull'equity sono in radar/guard.py.
"""
from __future__ import annotations

import pandas as pd

from .data import CRITICAL

GAP_DAYS = 60
TEXT = "Controllo di coerenza: verificare prima della prossima decisione. Nessuna azione automatica."


def gaps(d: dict, names=CRITICAL, days: int = GAP_DAYS) -> dict[str, list[str]]:
    """{fonte: [giorni mancanti]} negli ultimi `days` giorni fino all'ultimo giorno presente. Fonte assente o vuota: niente
    (la segnalano gli avvisi "fonte non disponibile" e "dati vecchi")."""
    out = {}
    for k in names:
        df = (d or {}).get(k)
        if df is None or not len(df):
            continue
        ix = pd.DatetimeIndex(df.index).normalize()
        last = ix.max()
        want = pd.date_range(max(ix.min(), last - pd.Timedelta(days=days)), last, freq="D")
        miss = want.difference(ix)
        if len(miss):
            out[k] = [str(x.date()) for x in miss]
    return out


def trades_sig(wcur: dict | None) -> dict[str, list]:
    """Firma dei trade della simulazione: {segnale: [lato, ingresso, uscita, motivo]} (uscita e motivo None se aperto)."""
    out = {}
    for t in ((wcur or {}).get("history") or {}).get("trades", []):
        is_open = t.get("reason") == "open" or not t.get("exit")
        out[str(t.get("signal"))] = [t.get("side"), t.get("entry"), None if is_open else t.get("exit"),
                                     None if is_open else t.get("reason")]
    return out


def history_changes(prev: dict, cur: dict) -> list[str]:
    """Trade già visti che non sono più uguali. Un trade aperto che si chiude e un trade nuovo sono normali."""
    out = []
    for sig, p in sorted((prev or {}).items()):
        c = cur.get(sig)
        if c is None:
            out.append(f"trade con segnale del {sig} ({p[0]}) non più presente nello storico")
        elif list(c[:2]) != list(p[:2]):
            out.append(f"trade con segnale del {sig}: era {p[0]} con ingresso {p[1]}, ora {c[0]} con ingresso {c[1]}")
        elif p[2] is not None and list(c[2:]) != list(p[2:]):
            out.append(f"trade con segnale del {sig}: uscita {p[2]} ({p[3]}) diventata {c[2] or 'aperto'}"
                       + (f" ({c[3]})" if c[3] else ""))
    return out


def prov_changes(prov: dict | None) -> list[dict]:
    return [r for r in (prov or {}).get("last") or [] if r.get("changed") in (True, "True")]


def format_alert(lines: list[str]) -> str:
    return "<b>RADAR SIGNAL BTC · Controllo di coerenza</b>\n" + "\n".join(lines) + "\n" + TEXT


def update(d: dict, wcur: dict | None, prov: dict | None, st: dict, send=None) -> dict:
    """Esegue i controlli, avvisa una volta per evento e ritorna {"problems": [...], "gaps": {...}, "history": [...]}."""
    cs = st.setdefault("coherence", {})
    sent = list(cs.get("sent", []))
    events: list[tuple[str | None, str]] = []          # (marker o None, riga del messaggio)
    g = gaps(d)
    for k, miss in g.items():
        events.append((f"gap:{k}:{miss[0]}", f"dati {k}: {len(miss)} giorni mancanti negli ultimi {GAP_DAYS} "
                       f"({', '.join(miss[:5])}{'…' if len(miss) > 5 else ''})"))
    sig = trades_sig(wcur)
    hist = history_changes(cs.get("trades") or {}, sig) if wcur else []
    events += [(None, "storico W3.1 riscritto · " + x) for x in hist]
    for r in prov_changes(prov):
        events.append((f"prov:{r.get('date')}", f"decisione del {r.get('date')}: con i dati provvisori "
                       f"«{r.get('decision_p')}», con i definitivi «{r.get('decision_d')}»"))
    new = [(m, line) for m, line in events if m is None or m not in sent]
    confirmed = True
    if new:
        if send is None:
            from .telegram import send
        confirmed = bool(send(format_alert([line for _, line in new])))
        if confirmed:
            cs["sent"] = (sent + [m for m, _ in new if m])[-40:]
            print(f"[coherence] avviso inviato: {len(new)} eventi")
        else:
            print("[coherence] avviso non confermato da Telegram: si riprova al prossimo giro")
    if wcur and (confirmed or not hist):                # storico di riferimento: si aggiorna solo dopo aver avvisato
        cs["trades"] = sig
    problems = [line for _, line in events]
    print(f"[coherence] buchi {sum(len(v) for v in g.values())}, storico riscritto {len(hist)}, "
          f"decisioni cambiate {len(prov_changes(prov))}")
    return {"problems": problems, "gaps": g, "history": hist}
