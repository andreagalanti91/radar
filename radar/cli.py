"""Uso:
  python -m radar.cli daily        aggiorna dati, calcola segnale, invia alert, genera dashboard
  python -m radar.cli backtest     stampa le statistiche del backtest
  python -m radar.cli test-telegram  invia un messaggio di prova
"""
from __future__ import annotations

import os
import sys
import warnings

warnings.filterwarnings("ignore")

from . import telegram  # noqa: E402
from .backtest import run, summary  # noqa: E402
from .dashboard import render  # noqa: E402
from .data import ASSET_NEEDED, CRITICAL, STALE_HOURS, cache_name, is_critical, load_all, stale_sources, update_all, update_asset  # noqa: E402
from .features import build_features  # noqa: E402
from .live import BACKTEST_START, diff_events, evaluate, save_state  # noqa: E402
from .news import fetch_calendar, fetch_central_banks, fetch_news  # noqa: E402
from . import paper  # noqa: E402
from . import lab  # noqa: E402
from . import weekly  # noqa: E402
from . import journal  # noqa: E402
import pandas as pd  # noqa: E402
from .liquidations import collect as collect_liquidations  # noqa: E402
import json  # noqa: E402
from .live import STATE_FILE  # noqa: E402
from .strategy import Params  # noqa: E402


def _now() -> pd.Timestamp:
    return pd.Timestamp.utcnow().tz_localize(None)


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        print(f"[radar] state.json non leggibile ({e!r}): si riparte da uno stato vuoto")
        return {}


def _save_state(st: dict) -> None:
    STATE_FILE.write_text(json.dumps(st, indent=2, default=str))


def state_key(asset: str = "BTC") -> str:
    """Chiave dello stato degli avvisi W3.2 in data/state.json: "weekly" per BTC, "weekly_eth" per ETH."""
    return "weekly" if asset == "BTC" else f"weekly_{asset.lower()}"


def weekly_alerts(cur: dict, st: dict, send=None, h=None) -> list[dict]:
    """Eventi W3 + controllo orario dello stop dell'asset di `cur` (cur["asset"], BTC se assente). Ogni evento si marca in
    st["weekly"] (st["weekly_eth"] per ETH) SOLO se send() conferma (message_id o True); i falliti si ripropongono al giro
    dopo. Il controllo orario guarda il più protettivo tra lo stop del modello e l'ultimo comunicato. Restituisce gli eventi
    inviati. Asset aggiunti dopo BTC: il primo giro conta come primo avvio (posizione "in corso"), dal secondo uno stato
    mancante è uno stato perso (marker st["weekly_eth_since"])."""
    send = send or telegram.send
    a = weekly.asset_of(cur)
    k = state_key(a)
    lost = None if a == "BTC" else bool(st.get(f"{k}_since"))
    sent, st[k] = weekly.send_events(cur, st.get(k), send, lost=lost)
    if a != "BTC":
        st.setdefault(f"{k}_since", cur["date"])
    ik = f"{k}_intraday_keys"
    keys = st.get(ik, [])
    hev, new_keys = weekly.check_intraday(cur, keys, h, told=weekly.told_level(st[k], cur))
    if hev:
        if send(weekly.format_intraday(hev, cur)):
            st[ik] = new_keys
        else:
            print(f"[radar] allerta stop W3 {a} non confermata da Telegram: si riprova al prossimo giro")
    return sent


def asset_round(asset: str, d: dict, st: dict, now: pd.Timestamp, errors: dict, send=None, fetch=None) -> dict | None:
    """W3.2 di un asset diverso da BTC (oggi ETH), dopo il giro di BTC e isolato da esso: dati (stesse fonti di BTC, cache in
    data/), feature, valutazione e avvisi. Ritorna {"cur", "d", "stale"} o None se i dati mancano (errori in `errors` con il
    prefisso dell'asset: li segnala il messaggio di salute, cli.heartbeat). Un errore qui non ferma mai il giro di BTC."""
    fetch = fetch or update_asset
    da = fetch(asset, errors)
    if da is None:
        return None
    da = dict(da, fng=d.get("fng") if d.get("fng") is not None else pd.DataFrame(columns=["fng"]))
    f = build_features(da)
    cur = weekly.evaluate(f, asset=asset)
    stale = {cache_name(k, asset): v for k, v in stale_sources(da, now, names=ASSET_NEEDED).items()}
    try:
        sent = weekly_alerts(cur, st, send)
        print(f"[radar] W3 {asset} {cur['status']} · eventi inviati: {[e['type'] for e in sent]}")
    except Exception as e:  # noqa: BLE001
        print(f"[radar] eventi settimanali {asset} non inviati: {e!r}")
    return {"cur": cur, "d": da, "stale": stale}


def _src(k: str) -> str:
    """Nome di una fonte per l'utente: "eth_funding" -> "ETH funding"."""
    return "ETH " + k[4:] if k.startswith("eth_") else k


def source_lines(errors: dict, stale: dict) -> list[str]:
    """Problemi delle fonti per il messaggio di salute: fonti non scaricate (si usa l'ultima cache) e dati fermi."""
    return ([f"fonte {_src(k)} non disponibile ({str(v)[:60]})" for k, v in (errors or {}).items()]
            + [f"dati {_src(k)} vecchi (ultimo giorno {telegram.dm(v)})" for k, v in (stale or {}).items()])


def brief_enabled() -> bool:
    return os.environ.get("RADAR_DAILY_BRIEF", "1") == "1"


def heartbeat_due(st: dict, now: pd.Timestamp) -> bool:
    """Un controllo di salute al giorno (UTC), al primo giro dopo le 07:00 UTC."""
    return os.environ.get("RADAR_HEARTBEAT", "1") == "1" and now.hour >= 7 and st.get("heartbeat") != str(now.date())


def heartbeat(cur: dict | None, st: dict, now: pd.Timestamp, data_until: str, problems: list[str], send=None,
              others: dict | None = None, errors: dict | None = None, stale: dict | None = None) -> bool:
    """Messaggio di salute. Tutto ok: nessun messaggio (la riga «✅ Sistema ok» è nel riepilogo "Oggi"; il messaggio «tutto ok»
    parte solo con il riepilogo spento, RADAR_DAILY_BRIEF=0). Con problemi: al primo giro dopo le 07:00 UTC (marker
    st["heartbeat"]) e, come gli avvisi sulle fonti di prima, al primo giro del giorno con una fonte di W3.2 non scaricata
    (st["source_alert"]) o con dati fermi da oltre STALE_HOURS ore (st["stale_alert"]): gli avvisi sulle fonti stanno solo qui.
    Ogni marker si scrive solo se Telegram conferma."""
    send = send or telegram.send
    today = str(now.date())
    errors, stale = errors or {}, stale or {}
    crit = {k: v for k, v in errors.items() if is_critical(k)}
    due = heartbeat_due(st, now)
    src_due = bool(crit and st.get("source_alert") != today) or bool(stale and st.get("stale_alert") != today)
    allp = source_lines(errors, stale) + list(problems or [])
    if not allp:
        if not due:
            return False
        if brief_enabled():   # tutto ok: già detto dal riepilogo "Oggi"
            st["heartbeat"] = today
            return False
    elif not (due or src_due):
        return False
    note = (f"Segnali calcolati sui dati fino al {telegram.dm(data_until)}: decisioni possibili in ritardo."
            if (crit or stale) and data_until else None)
    if not send(weekly.format_heartbeat(cur, data_until, now.strftime("%d/%m %H:%M UTC"), allp, today, others, note)):
        return False
    if due:
        st["heartbeat"] = today
    if crit:
        st["source_alert"] = today
    if stale:
        st["stale_alert"] = today
    return True


def health(data_until: str | None, problems: list[str], now: pd.Timestamp, errors: dict | None = None,
           stale: dict | None = None) -> str:
    """Riga di salute del riepilogo "Oggi"."""
    return telegram.health_line(data_until, source_lines(errors or {}, stale or {}) + list(problems or []),
                                weekly.next_decision(str(now.date())))


BRIEF_WAIT_H = 6   # se alle 06:00 UTC i dati non arrivano ancora a ieri, il riepilogo parte comunque (con la data dei dati)


def brief_due(st: dict, now: pd.Timestamp, data_until: str | None) -> bool:
    """Riepilogo giornaliero "Oggi": una volta al giorno (UTC), al primo giro dopo le 00:00 che ha i dati fino a ieri (candela
    giornaliera chiusa), oppure dalle BRIEF_WAIT_H UTC anche senza. Dipende dallo stato (st["daily_brief"]) e non dal cron:
    il cron delle 00:30 di daily.yml non partiva mai. RADAR_DAILY_BRIEF=0 lo spegne."""
    if not brief_enabled() or st.get("daily_brief") == str(now.date()):
        return False
    yesterday = str((now - pd.Timedelta(days=1)).date())
    return bool(data_until and data_until >= yesterday) or now.hour >= BRIEF_WAIT_H


def daily_brief(report: dict, st: dict, now: pd.Timestamp, data_until: str | None, send=None,
                health: str | None = None) -> bool:
    """Invia il riepilogo "Oggi" (W3 + contesto della pre-analisi, telegram.today_brief, con la riga di salute `health`) se
    dovuto; il marker del giorno si scrive solo se Telegram conferma (si riprova al giro dopo)."""
    send = send or telegram.send
    if not brief_due(st, now, data_until):
        return False
    if send(telegram.today_brief(report, str(now.date()), health)):
        st["daily_brief"] = str(now.date())
        return True
    print("[radar] riepilogo giornaliero non confermato da Telegram: si riprova al prossimo giro")
    return False


def wallets_enabled() -> bool:
    """Sezione Wallet (scout balene, sentinella, comandi Telegram): in pausa dal 22/11/2026, RADAR_WALLETS=1 la riaccende."""
    return os.environ.get("RADAR_WALLETS", "0") == "1"


def _soft(label: str, fn, *a, **k):
    """Fonte o modulo non essenziale per W3: un errore si registra e non ferma il giro."""
    try:
        return fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] {label} non disponibile: {e!r}")
        return None


def daily() -> None:
    try:   # registro dei trade reali: comandi Telegram arrivati dall'ultimo giro (risposta entro un'ora)
        n = journal.poll()
        if n:
            print(f"[radar] registro reale: {n} comandi Telegram eseguiti")
    except Exception as e:  # noqa: BLE001
        print(f"[radar] registro reale non letto: {e!r}")
    errors: dict = {}
    try:
        d = update_all(errors=errors)
    except Exception as e:  # noqa: BLE001   fonte W3 senza dati né cache: niente da valutare
        telegram.send(telegram.format_run_stopped(type(e).__name__))
        raise
    f = build_features(d)
    now = _now()
    stale = stale_sources(d, now)
    data_until = min(str(d[k].index.max().date()) for k in CRITICAL)
    problems: list[str] = []   # problemi del giro diversi dalle fonti (le fonti: errors e stale, cli.source_lines)
    # ---- W3 per primo: valutazione e alert prima di tutto il resto (fonti accessorie, v2, dashboard)
    st = _load_state()
    wcur = None
    try:
        wcur = weekly.evaluate(f)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] settimanale W3 non calcolato: {e!r}")
        problems.append("W3.2 non calcolato")
        if st.get("w3_error_alert") != str(now.date()) and telegram.send(
                telegram.format_w3_error(f"{type(e).__name__}: {str(e)[:200]}")):
            st["w3_error_alert"] = str(now.date())
    if wcur:
        try:
            sent = weekly_alerts(wcur, st)
            print(f"[radar] W3 {wcur['status']} · eventi inviati: {[e['type'] for e in sent]}")
        except Exception as e:  # noqa: BLE001
            print(f"[radar] eventi settimanali non inviati: {e!r}")
    # ---- W3.2 ETH (dal 22/11/2026, capitale separato RADAR_ETH_CAPITAL): dopo BTC e isolato, dati ETH mancanti non bloccano nulla
    eth = None
    try:
        eth = asset_round("ETH", d, st, now, errors)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] W3.2 ETH non calcolato: {e!r}")
        problems.append("W3.2 ETH non calcolato")
    ecur = (eth or {}).get("cur")
    if eth:
        stale.update(eth["stale"])
    elif "W3.2 ETH non calcolato" not in problems:
        problems.append("W3.2 ETH non calcolato")
    # registro "provvisori vs definitivi" della decisione domenicale e soglie d'allarme: solo registro e avviso, W3 non cambia
    from importlib import import_module as _im   # import isolato: un modulo rotto non ferma il giro
    from .data import DATA_DIR as _ddir
    provlog_out = _soft("registro provvisori/definitivi", lambda: _im(".provlog", __package__).update(f, d, wcur, _ddir))
    guard_out = _soft("soglie d'allarme", lambda: _im(".guard", __package__).update(wcur, st, journal.load()))
    guard_eth = _soft("soglie d'allarme ETH", lambda: _im(".guard", __package__).update(ecur, st, None, asset="ETH")) if ecur else None
    # allarme "fuori dal backtest" (radar/limiti.py): calo, perdite di fila o singola operazione oltre i limiti storici, sul
    # conto del modello e sulle operazioni vere del diario; un avviso per evento, marcatore st["limiti"] solo a invio riuscito
    limiti_out = _soft("limiti del backtest", lambda: _im(".limiti", __package__).update({"BTC": wcur, "ETH": ecur}, st, journal.load()))
    # avviso VIX (condizione di mercato, non W3.2): controllo ogni 4 ore, avviso solo all'attraversamento di 30/15 con riarmo
    _soft("avviso VIX", lambda: _im(".vix", __package__).update(st, now))
    # controlli di coerenza orari (buchi nei dati, storico riscritto, decisione cambiata con i definitivi): solo avviso
    coh = _soft("controlli di coerenza", lambda: _im(".coherence", __package__).update(d, wcur, provlog_out, st))
    problems += [x.split(" (")[0] for x in (coh or {}).get("problems", [])]
    if eth:
        coh_eth = _soft("controlli di coerenza ETH", lambda: _im(".coherence", __package__).update(eth["d"], ecur, None, st, asset="ETH"))
        problems += ["ETH " + x.split(" (")[0] for x in (coh_eth or {}).get("problems", [])]
    # salute: messaggio separato solo con problemi (fonti incluse); tutto ok = riga in fondo al riepilogo "Oggi"
    _soft("heartbeat", heartbeat, wcur, st, now, data_until, problems, others={"ETH": ecur}, errors=errors, stale=stale)
    hl = _soft("riga di salute", health, data_until, problems, now, errors, stale)
    _save_state(st)
    # ---- v2, moduli accessori e dashboard: ognuno isolato
    _soft("liquidazioni", collect_liquidations)
    try:
        report = evaluate(f)
    except Exception as e:  # noqa: BLE001
        print(f"[radar] v2 non calcolato, dashboard non generata: {e!r}")
        st = _load_state()
        if wcur:   # il riepilogo "Oggi" non dipende da v2: parte con W3 e la pre-analisi
            from .preview import build as _pv
            from .data import DATA_DIR as _dd

            def _mb():   # import isolato: un errore del modulo non ferma il riepilogo
                from .macro import build
                return build(_dd, weekly=wcur)
            _soft("riepilogo giornaliero", daily_brief, {"weekly": wcur, "weekly_eth": ecur, "preview": _soft("pre-analisi W3", _pv, f),
                                                         "macro": _soft("chiusura multi-asset", _mb)},
                  st, _now(), data_until, health=hl)
        st["last_run"] = _now().isoformat(timespec="seconds")
        _save_state(st)
        return
    if wcur:
        report["weekly"] = wcur          # BTC: chiave storica, invariata per compatibilità
    if ecur:
        report["weekly_eth"] = ecur      # ETH: stessa struttura (asset = "ETH")
    for k, v in (("provlog", provlog_out), ("guard", guard_out), ("guard_eth", guard_eth), ("limiti", limiti_out)):
        if v is not None:
            report[k] = v
    from importlib import import_module
    from .data import DATA_DIR

    def mod(name: str):   # import isolato: un modulo accessorio rotto non ferma il giro
        return import_module(f".{name}", __package__)
    report["levels"] = _soft("supporti e resistenze", lambda: mod("levels").compute(f))
    _soft("modulo su carta", paper.update, f)
    # mappa delle liquidazioni vicine e balene Hyperliquid (radar/liqmap.py)
    report["liqmap"] = _soft("mappa delle liquidazioni", lambda: mod("liqmap").update(report.get("levels"), DATA_DIR))
    # card "Fra 30 giorni": cono di probabilità dalla volatilità, non dalla direzione; solo lettura, nessun effetto su W3.2 (radar/cone.py)
    report["cone"] = _soft("cono a 30 giorni", lambda: mod("cone").build(f, report, DATA_DIR))
    # mappa unica dei livelli (supporti, resistenze, medie, Fibonacci, liquidazioni, zone) con probabilità di tocco dal cono:
    # contesto, non segnale; nessun effetto su W3.2 (radar/livelli.py, card "Livelli e probabilità a 30 giorni")
    report["livelli"] = _soft("mappa dei livelli", lambda: mod("livelli").compute(f, report, DATA_DIR))
    # pre-analisi della prossima decisione W3 (chiusura della domenica) con i dati di oggi: solo lettura (radar/preview.py)
    report["preview"] = _soft("pre-analisi W3", lambda: mod("preview").build(f, report)) if wcur else None
    _soft("trader seguito (esiti)", lambda: mod("xinbox").evaluate_all())
    report["liqsources"] = _soft("liquidazioni multi-exchange", lambda: mod("liqsources").summary())
    # ultima cascata di liquidazioni (24 ore) e prossime fasce dense: solo contesto (radar/liqcascade.py, lezione 92)
    report["cascade"] = _soft("cascata di liquidazioni", lambda: mod("liqcascade").update(report, DATA_DIR))
    # scout balene Hyperliquid: una volta al giorno (≥ 20 ore dall'ultimo giro) (radar/scout.py).
    # In pausa dal 22/11/2026 (richiesta dell'utente): gira solo con RADAR_WALLETS=1 (radar/wallets.enabled)
    if wallets_enabled():
        try:   # come prima: None = scout non rifatto oggi; assente = errore (la dashboard legge l'ultimo file)
            report["scout"] = mod("scout").daily(DATA_DIR)
        except Exception as e:  # noqa: BLE001
            print(f"[radar] scout balene non disponibile: {e!r}")
    else:
        print("[radar] scout balene e wallet in pausa (RADAR_WALLETS=0)")
    # motore del book: foto, controlli, previsione 1h/4h (radar/orderbook.py)
    report["orderbook"] = _soft("book", lambda: mod("orderbook").update(DATA_DIR))
    report["news"] = _soft("notizie", fetch_news) or []
    report["calendar"] = _soft("calendario", fetch_calendar) or []
    report["banks"] = _soft("banche centrali", fetch_central_banks) or []   # prossime riunioni Fed (FOMC) e BCE
    # esito per fonte dell'ultimo giro delle notizie (riga "Fonti" della pagina Notizie)
    report["news_fonti"] = _soft("stato delle fonti delle notizie", lambda: _im(".news", __package__).status())
    # riquadro "Contesto" (regime di mercato, Fed, CPI, VIX, FOMC): descrizione senza probabilità, nessun effetto su W3.2 (radar/context.py)
    report["context"] = _soft("contesto di mercato e politica economica", lambda: mod("context").build(DATA_DIR, banks=report.get("banks")))
    # chiusura multi-asset (S&P, Nasdaq, oro, argento, dollaro, VIX, Treasury 10 anni): solo contesto (radar/macro.py)
    report["macro"] = _soft("chiusura multi-asset", lambda: mod("macro").build(DATA_DIR, weekly=report.get("weekly")))
    # scheda "Ciclo on-chain" nella posizione di BTC (radar/onchain.py): MVRV di CoinMetrics una volta al giorno (data/mvrv.csv),
    # zone dello studio research/utxo_pl; solo contesto (lezione 125), nessun avviso e nessun effetto su W3.2; rete giù = ultimo dato
    report["onchain"] = _soft("ciclo on-chain (MVRV)", lambda: mod("onchain").build(DATA_DIR, side=mod("onchain").side_of(wcur)))
    # scheda "Dollaro" nella posizione di BTC (radar/dollaro.py): DXY giornaliero da Yahoo una volta al giorno (data/dollaro.csv),
    # ripiego FRED DTWEXBGS e ultimo file; divergenza come research/dxy_divergenza. Solo contesto: nessun avviso, W3.2 non cambia
    report["dollaro"] = _soft("dollaro (DXY)", lambda: mod("dollaro").build(DATA_DIR, side=mod("dollaro").side_of(wcur)))
    # scheda "OPEX" nella posizione di BTC (radar/opex.py): scadenze delle opzioni da Deribit (ripiego OKX, poi ultimo file
    # data/opex/ultimo.json) una volta al giorno e ogni 4 ore nelle ultime 48 ore; snapshot in data/opex/snap.jsonl per verificare
    # in futuro la "calamita" del massimo dolore. Solo contesto (studio research/opex): nessun avviso, W3.2 non cambia
    report["opex"] = _soft("scadenze delle opzioni (OPEX)", lambda: mod("opex").build(DATA_DIR, side=mod("opex").side_of(wcur)))
    # "Mercato power" in Oggi e Posizioni (radar/mercato.py): sei semafori di contesto (on-chain, dollaro, OPEX, VIX, Fed, flusso e
    # funding perp) a favore/neutro/contro la posizione aperta di BTC ed ETH, registro data/mercato_power.csv. Nessun punteggio unico,
    # nessun avviso: non entra in W3.2 (decide W3.2)
    report["mercato"] = _soft("mercato power", lambda: mod("mercato").build(report, DATA_DIR))
    # opzioni su BTC "sulla carta" con i segnali di W3.2 (radar/opzioni.py, pagina Opzioni): catena OKX, registro
    # data/opzioni_carta.json, archivio data/opzioni/. Legge solo W3.2, non invia ordini; OKX giù = ultimo dato, giro intatto
    report["opzioni"] = _soft("opzioni su carta", lambda: mod("opzioni").giro(wcur, DATA_DIR)) if wcur else None
    # pagina Scanner, solo informativa (radar/scanner.py): TRX sulla carta con il cancello di BTC (registro data/trx_carta.json dal
    # 25/11/2026, ricalcolo a giorno nuovo) e stato settimanale di W3.2 sulle crypto dello studio w32_asset2 (data/scanner.json,
    # ricalcolo solo a settimana nuova; dati grezzi in .scanner-cache/, fuori da git). Nessun ordine né avviso, nessun effetto su
    # W3.2 di BTC ed ETH; rete giù = ultimo risultato con l'avviso
    report["trx_carta"] = _soft("TRX sulla carta", lambda: mod("scanner").trx_giro(f, DATA_DIR))
    report["scanner"] = (_soft("scanner settimanale", lambda: mod("scanner").giro(f, DATA_DIR))
                         or _soft("scanner (ultimo salvato)", lambda: mod("scanner").ultimo(DATA_DIR)))
    # registro "scommesse" sulla carta (radar/scommesse.py, research/w32_asset2/REGISTRO-SCOMMESSE.md): ingressi nuovi dello
    # scanner nel verso di BTC dal 29/11/2026, 100 $ fissi; aperte rivalutate una volta al giorno. Nessun ordine né avviso
    report["scommesse"] = _soft("scommesse sulla carta", lambda: mod("scommesse").giro(report.get("scanner"), DATA_DIR))
    # registro V3 sulla carta (radar/emergenti_carta.py, research/emergenti/PREREG-AVANTI-V3.md): solo short di W3.2 sulle monete
    # 101–200 della lista d'inizio anno, dal 30/11/2026, budget di carta 10.000 $, ricalcolo a settimana nuova. Nessun ordine né avviso
    report["emergenti_carta"] = _soft("emergenti sulla carta (V3)", lambda: mod("emergenti_carta").giro(f, DATA_DIR))
    for k in ("levels", "liqmap", "orderbook", "preview", "cone", "livelli", "opzioni", "trx_carta", "scanner", "scommesse", "emergenti_carta", "mercato", "opex", "onchain", "dollaro"):
        if report.get(k) is None:
            report.pop(k, None)
    # v2: solo stato e storico per la dashboard (messaggi Telegram di v2 eliminati il 25/11/2026; spenti dal 12/11/2026)
    events = diff_events(report)
    save_state(report)
    st = _load_state()
    # riepilogo giornaliero "Oggi" (W3 + contesto + riga di salute), interruttore RADAR_DAILY_BRIEF
    _soft("riepilogo giornaliero", daily_brief, report, st, _now(), data_until, health=hl)
    # fine del giro pesante: lo legge il controllo del workflow (daily.yml) per saltare un secondo giro entro 25 minuti
    st["last_run"] = _now().isoformat(timespec="seconds")
    _save_state(st)
    _soft("registro reale (collegamento al segnale)", journal.link, report)   # prezzi e orari di v2 e W3
    _soft("laboratorio", lab.build, report)
    out = render(report)
    print(f"[radar] {report['date']} score {report['score']:+.2f} · eventi v2: {[e['type'] for e in events]} · dashboard: {out}")


def backtest() -> None:
    f = build_features(load_all())
    p = Params()
    for mk in ("futures", "spot"):
        t = run(f, p, mk, BACKTEST_START)
        print(f"\n== {mk}\n{summary(t)}")
        print(t.drop(columns=[c for c in ("pending_entries", "next_tps", "mtm") if c in t]).to_string())


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if cmd == "daily":
        daily()
    elif cmd == "backtest":
        backtest()
    elif cmd == "test":
        import unittest
        r = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover("tests"))
        sys.exit(0 if r.wasSuccessful() else 1)
    elif cmd == "test-telegram":
        ok = telegram.send(telegram.format_test())
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
