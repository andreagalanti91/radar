"""Notizie crypto e macro da feed RSS pubblici, calendario economico e banche centrali, filtrati "per noi" (W3.2 su BTC ed ETH, TRX, SOL, TAO)."""
from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

FEEDS = {
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed",
    "The Block": "https://www.theblock.co/rss.xml",
    "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",
    "CryptoSlate": "https://cryptoslate.com/feed/",
    "Cryptonomist": "https://cryptonomist.ch/feed/",
    "Investing": "https://www.investing.com/rss/news_301.rss",
    "Bitcoin.com": "https://news.bitcoin.com/feed/",
    "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
}

ROOT = Path(__file__).resolve().parent.parent
NEWS_CACHE = ROOT / "data" / "news_cache.json"   # ultimo dato buono di notizie, calendario e banche centrali (fonte giù = si mostra questo)

# ---------------------------------------------------------------- rilevanza "per noi" (sezione Notizie della dashboard)
# Per noi = ciò che può toccare W3.2 su BTC ed ETH (decisione alla chiusura della domenica), TRX in osservazione e le preferite
# SOL e TAO. Regole dichiarate e testate (tests/test_news_rilevanza.py); il punteggio è una somma di voci leggibili (campo "why").
# Asset seguiti: etichetta → (regex a parole intere, punti se nel titolo). Solo nel riassunto vale 1 punto.
ASSETS = {
    "BTC": (r"\b(bitcoin|btc)\b", 3),
    "ETH": (r"\b(ether|ethereum|eth)\b", 3),
    "TRX": (r"\b(tron|trx)\b", 2),
    "SOL": (r"\b(solana|sol)\b", 2),
    "TAO": (r"\b(bittensor|tao)\b", 2),
}
# Temi, in ordine di priorità (il primo che compare nel titolo dà il gruppo; altrimenti il primo nel riassunto).
# Punti: peso se nel titolo, 1 se solo nel riassunto. Macro vale da solo (muove BTC anche senza nominarlo).
THEMES = {
    "sicurezza": (r"\b(hack(s|ed|ers?)?|exploit\w*|breach\w*|phishing|stolen|drained|outage|insolven\w*|bankrupt\w*|"
                  r"withdrawals? (paused|halted|suspended|frozen)|attacco|furto)\b", 2),
    "macro": (r"\b(fed|fomc|powell|federal reserve|inflation|cpi|pce|rate (cuts?|hikes?|increase|decision)|interest rates?|"
              r"treasur(y|ies) yields?|yields?|dollar index|dxy|recession|jobs report|payrolls?|nfp|unemployment|gdp|tariffs?|"
              r"ecb|boj|bank of japan|nasdaq|s&p 500|wall street|equities|stock market|tech (rout|selloff|stocks)|"
              r"inflazione|tassi|dazi|banca centrale)\b", 4),
    "etf": (r"\b(etfs?|etps?|blackrock|ibit|fidelity|grayscale|vaneck|inflows?|outflows?|institutional|microstrategy|strategy inc|"
            r"saylor|treasury compan\w*|corporate treasur\w*)\b", 2),
    "regole": (r"\b(sec|cftc|regulat\w*|lawsuits?|court|congress|senate|bills?|legislation|law|lawmakers|mica|esma|bans?|"
               r"tax(es)?|white house|executive order|strategic (bitcoin )?reserve|legge|normativa|regolament\w*|tasse)\b", 2),
    "mercato": (r"\b(prices?|liquidat\w*|futures|open interest|funding rates?|options?|leverage\w*|short squeeze|whales?|"
                r"on-?chain|exchange reserves?|miners?|hashrate|sell-?off|rally|crash\w*|plunge\w*|surge\w*|slump\w*|"
                r"tumble\w*|slides?|all-time high|bear(ish)? market|bull(ish)? market|bearish|bullish|prezzo|calo|rialzo)\b", 1),
}
THEME_LABELS = {"macro": "Macro e banche centrali", "etf": "ETF e flussi", "regole": "Regolamentazione",
                "sicurezza": "Exchange e sicurezza", "mercato": "Mercato"}
# Parole forti nel titolo (+2): storicamente muovono il prezzo. Un attacco conta solo se tocca un grande exchange, uno
# stablecoin principale o un asset seguito (EXCHANGES o ASSETS nel titolo).
STRONG = r"\b(fomc|rate decision|cpi|pce|payrolls?|nonfarm|etf (in|out)flows?|record( \w+)? (in|out)flows?|sec|cftc|executive order|strategic (bitcoin )?reserve)\b"
HACK = r"\b(hack(s|ed|ers?)?|exploit\w*|breach\w*|stolen|drained)\b"
EXCHANGES = r"\b(binance|coinbase|kraken|okx|bybit|bitfinex|bithumb|upbit|gemini|deribit|bitget|kucoin|tether|circle|usdt|usdc)\b"
# Fuori tema: titolo centrato su un altcoin minore senza nominare un asset seguito né un tema macro (resta fra "Altre notizie").
# Nomi a parole intere senza distinzione di maiuscole; sigle solo in maiuscolo (HYPE, NEAR, TON sono anche parole comuni).
MINOR = (r"\b(xrp|ripple|hyperliquid|aave|dogecoin|cardano|avalanche|polkadot|chainlink|aptos|toncoin|pepe|shiba inu|litecoin|"
         r"arbitrum|polygon|uniswap|ethena|pump\.?fun|memecoins?|meme coins?|nfts?|chainflip|monero|zcash|kaspa|"
         r"pi network|world liberty|bonk)\b")
MINOR_TICKERS = r"\b(XRP|HYPE|ADA|BNB|AVAX|SUI|TON|NEAR|LTC|XLM|ENA|DOGE|SHIB|PEPE|WLFI|BONK|LINK|DOT|UNI|ARB|OP|APT|ZEC|XMR)\b"
# Escluse del tutto: pubblicità e articoli promozionali.
PROMO = (r"\b(sponsored|press release|giveaway|airdrops?|presale|pre-sale|price predictions?|could (soar|explode)|"
         r"\d+x (gains|potential)|best crypto|top \d+ (coins|altcoins|cryptos?)|next 100x|comunicato stampa)\b")
# Escluse del tutto: nessuna parola crypto e nessun tema macro (articoli generici delle stesse testate).
CRYPTO = (r"\b(crypto\w*|cripto\w*|bitcoin|btc|ether(eum)?|eth|blockchain|tokens?|tokeni[sz]\w*|stablecoins?|defi|web3|coins?|"
          r"exchanges?|mining|miners?|wallets?|digital assets?|on-?chain|altcoins?|binance|coinbase|tether|usdt|usdc|satoshi|"
          r"tron|trx|solana|sol|bittensor|tao|etfs?)\b")
SOGLIA = 4           # punteggio minimo per "Notizie che toccano le posizioni"
DUP_MIN, DUP_OVERLAP = 3, 0.4   # doppioni: ≥ 3 radici in comune e ≥ 40% delle radici del titolo più corto, entro 72 ore
_STOP = set("the a an and or of to in on for with as at by from is are was be its it this that after amid over into new says "
            "said will can could may just than more most about your what how why who il lo la le gli di da del della dei "
            "per con su nel nella una uno che non".split())
_COMMON = {"cryp", "bitc", "btc", "toke", "mark", "coin", "pric"}   # troppo comuni nei titoli crypto per dire "stessa notizia"

# impatto storico (vecchio indicatore, resta per compatibilità con i report già pubblicati)
IMPACT = [
    (r"\b(fomc|rate decision|rate cuts?|rate hikes?|powell|cpi|pce|nonfarm|payrolls?)\b", 3),
    (r"\b(hack(ed|ers?)?|exploit\w*|breach|stolen|drained)\b", 3),
    (r"\b(etf (in|out)flows?|record (in|out)flows?|spot bitcoin etf)\b", 3),
    (r"\b(sec|cftc|lawsuit|ban|executive order|strategic (bitcoin )?reserve)\b", 2),
    (r"\b(liquidat\w*|short squeeze|long squeeze|capitulat\w*)\b", 2),
    (r"\b(tariffs?|recession|treasury yields?|dollar index|dxy)\b", 2),
    (r"\b(all-time high|ath|crash\w*|plunge\w*|surge\w*|soar\w*|tumble\w*)\b", 1),
    (r"\b(blackrock|microstrategy|saylor|mt\.? ?gox|binance|coinbase)\b", 1),
]

def _text(el, *names):
    for n in names:
        x = el.find(n)
        if x is not None and (x.text or "").strip():
            return x.text.strip()
    return ""


def _clean(s: str, n: int = 220) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def _date(s: str) -> datetime | None:
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _fetch(source: str, url: str) -> list[dict]:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 RadarSignal/1.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:  # una fonte giù non deve bloccare le altre
        print(f"[news] {source}: {type(e).__name__}")
        return []
    atom = "{http://www.w3.org/2005/Atom}"
    items = root.findall(".//item") or root.findall(f".//{atom}entry")
    out = []
    for it in items[:25]:
        link = _text(it, "link")
        if not link:
            le = it.find(f"{atom}link")
            link = le.get("href") if le is not None else ""
        d = _date(_text(it, "pubDate", f"{atom}updated", f"{atom}published", "{http://purl.org/dc/elements/1.1/}date"))
        title = _clean(_text(it, "title", f"{atom}title"), 160)
        if not title or not link or not d:
            continue
        out.append({"source": source, "title": title, "link": link, "date": d.isoformat(),
                    "summary": _clean(_text(it, "description", f"{atom}summary", f"{atom}content"))})
    return out


def _now() -> datetime:
    return datetime.now(timezone.utc)


def classify(item: dict) -> dict:
    """Rilevanza "per noi" di una notizia: asset seguiti, tema, punteggio con le voci che lo compongono, gruppo.
    group = "noi" (tocca le posizioni), "altre" (resto), "via" (pubblicità o fuori tema generico: non si mostra)."""
    title = item.get("title") or ""
    tl, full = f" {title} ".lower(), f" {title} {item.get('summary') or ''} ".lower()
    why, score = [], 0
    in_title = [a for a, (rx, _) in ASSETS.items() if re.search(rx, tl)]
    in_body = [a for a, (rx, _) in ASSETS.items() if a not in in_title and re.search(rx, full)]
    if in_title:
        pts = max(ASSETS[a][1] for a in in_title) + len(in_title) - 1
        score += pts
        why.append(f"{'/'.join(in_title)} nel titolo +{pts}")
    elif in_body:
        score += 1
        why.append(f"{'/'.join(in_body)} nel testo +1")
    theme = next((k for k, (rx, _) in THEMES.items() if re.search(rx, tl)), None)
    if theme:
        score += THEMES[theme][1]
        why.append(f"{THEME_LABELS[theme]} +{THEMES[theme][1]}")
    else:
        theme = next((k for k, (rx, _) in THEMES.items() if re.search(rx, full)), None)
        if theme:
            score += 1
            why.append(f"{THEME_LABELS[theme]} nel testo +1")
    if item.get("source") == "Federal Reserve":
        theme = "macro"
        if not why or "Macro" not in why[-1]:
            score += THEMES["macro"][1]
            why.append("comunicato della Fed +4")
    strong = re.search(STRONG, tl) or (re.search(HACK, tl) and (re.search(EXCHANGES, tl) or in_title))
    if strong:
        score += 2
        why.append("parola forte nel titolo +2")
    group, reason = "altre", ""
    if re.search(PROMO, full):
        group, reason = "via", "promozionale"
    elif (not re.search(CRYPTO, full) and not re.search(MINOR, full) and not re.search(MINOR_TICKERS, f" {title} ")
          and theme != "macro" and not in_title):
        group, reason = "via", "fuori tema"
    elif not in_title and theme != "macro" and (re.search(MINOR, tl) or re.search(MINOR_TICKERS, f" {title} ")):
        reason = "altcoin minore"
    elif score >= SOGLIA and (in_title or theme in ("macro", "etf", "regole", "sicurezza")):
        group = "noi"
    item = dict(item, assets=in_title or in_body, theme=theme or "mercato", rel=score, why=why, group=group)
    if reason:
        item["reason"] = reason
    # compatibilità con la dashboard precedente: impatto e livello dal nuovo punteggio
    item["impact"], item["level"] = score, "alto" if score >= 8 else "medio" if score >= 5 else "basso"
    return item


def _stems(title: str) -> set[str]:
    words = re.findall(r"[a-zà-ù0-9]+", title.lower())
    return {w[:4] for w in words if len(w) >= 3 and w not in _STOP} - _COMMON


def same_story(a: str, b: str) -> bool:
    """Due titoli raccontano la stessa notizia: radici (prime 4 lettere) in comune ≥ DUP_MIN e ≥ DUP_OVERLAP del più corto."""
    sa, sb = _stems(a), _stems(b)
    if not sa or not sb:
        return False
    common = len(sa & sb)
    return common >= DUP_MIN and common / min(len(sa), len(sb)) >= DUP_OVERLAP


def dedupe(items: list[dict], hours: int = 72) -> list[dict]:
    """Toglie i doppioni (stessa notizia da più testate): resta la più recente, con le altre fonti in "also" e il punteggio
    più alto del gruppo. Ingresso già classificato e in ordine di data decrescente."""
    out: list[dict] = []
    for it in items:
        d = datetime.fromisoformat(it["date"])
        for k in out:
            if (abs((datetime.fromisoformat(k["date"]) - d).total_seconds()) <= hours * 3600
                    and any(same_story(t, it["title"]) for t in k["_titles"])):
                k["_titles"].append(it["title"])
                if it["source"] != k["source"] and it["source"] not in k.setdefault("also", []):
                    k["also"].append(it["source"])
                if it.get("rel", 0) > k.get("rel", 0):
                    for f in ("rel", "why", "theme", "group", "impact", "level"):
                        if f in it:
                            k[f] = it[f]
                k["assets"] = sorted(set(k.get("assets", [])) | set(it.get("assets", [])), key=list(ASSETS).index)
                break
        else:
            out.append(dict(it, _titles=[it["title"]]))
    for k in out:
        del k["_titles"]
    return out


def select(items: list[dict], now: datetime | None = None, max_age_days: int = 4, max_items: int = 80) -> list[dict]:
    """Dalle notizie grezze dei feed a quelle mostrate: età massima, classificazione, via le escluse, doppioni uniti.
    Ordine: prima "noi" per punteggio e data, poi "altre" per data."""
    now = now or _now()
    fresh = [it for it in items if (now - datetime.fromisoformat(it["date"])).total_seconds() <= max_age_days * 86400]
    cl = [classify(it) for it in sorted(fresh, key=lambda x: x["date"], reverse=True)]
    kept = dedupe([it for it in cl if it["group"] != "via"])
    for it in kept:
        it.pop("summary", None)   # la pagina mostra solo titoli: il riassunto serve alla classificazione, non al report
    noi = sorted((x for x in kept if x["group"] == "noi"), key=lambda x: (x["rel"], x["date"]), reverse=True)
    altre = [x for x in kept if x["group"] != "noi"]
    return (noi + altre)[:max_items]


# ---------------------------------------------------------------- ultimo dato buono (fonte giù = si mostra questo con l'avviso)
_STATUS: dict = {}


def status() -> dict:
    """Esito dell'ultimo giro per fonte: {nome: {"ok": bool, "n": voci, "at": ISO}} (per la riga "Fonti" della dashboard)."""
    return dict(_STATUS)


def _cache_load(path: Path | None) -> dict:
    try:
        return json.loads(path.read_text()) if path and path.exists() else {}
    except (OSError, ValueError):
        return {}


def _cache_put(path: Path | None, key: str, items: list[dict], at: str) -> None:
    """Salva l'ultimo dato buono di una fonte; riscrive il file solo se il contenuto cambia (il giro committa data/ ogni ora)."""
    if not path:
        return
    c = _cache_load(path)
    if (c.get(key) or {}).get("items") == items:
        return
    c[key] = {"at": at, "items": items}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(c, ensure_ascii=False, separators=(",", ":")))
    except OSError as e:
        print(f"[news] cache non salvata: {type(e).__name__}")


def _with_fallback(key: str, items: list[dict], cache: Path | None, at: str, minimum: int = 1, keep: int = 40) -> list[dict]:
    """Dato nuovo → si salva (le prime `keep` voci) e ogni voce porta "fetched"; dato assente o troppo scarso → ultimo dato
    buono, con "stale" (la pagina mostra l'avviso)."""
    if len(items) >= minimum:
        _cache_put(cache, key, items[:keep], at)
        return [dict(x, fetched=at) for x in items]
    old = _cache_load(cache).get(key) or {}
    if old.get("items"):
        print(f"[news] {key}: fonte non disponibile, uso l'ultimo dato del {old.get('at')}")
        return [dict(x, fetched=old.get("at"), stale=True) for x in old["items"]]
    return []


def fetch_news(max_items: int = 80, max_age_days: int = 4, cache: Path | None = NEWS_CACHE) -> list[dict]:
    with ThreadPoolExecutor(8) as ex:
        per = list(ex.map(lambda kv: (kv[0], _fetch(*kv)), FEEDS.items()))
    at = _now().isoformat(timespec="seconds")
    for name, lst in per:
        _STATUS[name] = {"ok": bool(lst), "n": len(lst), "at": at}
    out = select([x for _, lst in per for x in lst], max_age_days=max_age_days, max_items=max_items)
    # meno di 10 notizie = quasi tutte le fonti giù: meglio l'ultimo elenco buono, con l'avviso in pagina
    return _with_fallback("news", out, cache, at, minimum=10)

# ---------------------------------------------------------------- calendario economico
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
# perché ogni dato conta per BTC (spiegazione breve mostrata in dashboard)
EVENT_NOTES = [
    (r"gdp price", "Deflatore del PIL: misura d'inflazione dentro il dato sulla crescita; effetto di solito limitato."),
    (r"cpi|inflation", "Inflazione USA: se sopra le attese allontana i tagli dei tassi e pesa sugli asset a rischio come BTC; sotto le attese è di solito positiva."),
    (r"pce", "Indicatore di inflazione preferito dalla Fed: stessa logica del CPI, con effetto spesso più contenuto."),
    (r"non-?farm|employment change|payroll", "Occupazione USA: un mercato del lavoro troppo forte rafforza dollaro e rendimenti, uno debole aumenta le attese di tagli."),
    (r"unemployment", "Disoccupazione: un aumento fa salire le attese di tagli dei tassi, spesso favorevoli a BTC nel medio periodo."),
    (r"federal funds|fomc|rate statement|press conference", "Decisione e messaggio della Fed: il principale motore macro. Il tono (più o meno restrittivo) conta quanto la decisione."),
    (r"gdp", "Crescita economica: sorprese forti al ribasso aumentano l'avversione al rischio nel breve."),
    (r"retail sales", "Consumi USA: misura la forza della domanda; sorprese ampie muovono dollaro e rendimenti."),
    (r"pmi|ism", "Fiducia delle imprese: anticipa il ciclo economico; sotto 50 indica contrazione."),
    (r"jolts|job openings", "Posti vacanti: segnale sulla tenuta del mercato del lavoro guardato dalla Fed."),
    (r"jobless claims", "Richieste di sussidio settimanali: aumenti persistenti indicano rallentamento del lavoro."),
    (r"consumer (confidence|sentiment)", "Fiducia dei consumatori: dato secondario, include le aspettative di inflazione."),
    (r"ecb|main refinancing|boj|policy rate", "Banca centrale non USA: muove il dollaro e la liquidità globale."),
    (r"ppi", "Prezzi alla produzione: anticipano l'inflazione al consumo; sorprese al rialzo allontanano i tagli dei tassi."),
    (r"adp", "Occupazione privata ADP: anticipa il dato ufficiale sul lavoro; da sola muove poco."),
    (r"durable goods", "Ordini di beni durevoli: domanda delle imprese, effetto di solito limitato."),
    (r"powell|fed chair", "Parla il presidente della Fed: una frase sui tassi può muovere BTC più di un dato."),
    (r"minutes", "Verbali della Fed: dicono quanto i membri sono propensi a tagliare o alzare i tassi."),
]
# nome breve in italiano del dato (regex sul titolo inglese della fonte; vince il primo che corrisponde)
EVENT_IT = [
    (r"core pce", "Inflazione PCE core"), (r"pce", "Inflazione PCE"), (r"core cpi", "Inflazione CPI core"), (r"cpi", "Inflazione CPI"),
    (r"core ppi", "Prezzi alla produzione core"), (r"ppi", "Prezzi alla produzione"),
    (r"non-?farm", "Occupazione USA (non agricola)"), (r"adp", "Occupazione privata ADP"),
    (r"unemployment rate", "Tasso di disoccupazione"), (r"unemployment claims|jobless claims", "Richieste di sussidio"),
    (r"jolts|job openings", "Posti di lavoro vacanti"), (r"average hourly earnings", "Salari orari"),
    (r"federal funds rate", "Fed · decisione sui tassi"), (r"fomc statement", "Fed · comunicato"),
    (r"fomc press conference", "Fed · conferenza stampa"), (r"fomc meeting minutes", "Fed · verbali"),
    (r"powell", "Discorso di Powell"), (r"gdp price", "PIL · deflatore"), (r"gdp", "PIL"),
    (r"core retail sales", "Vendite al dettaglio core"), (r"retail sales", "Vendite al dettaglio"),
    (r"ism manufacturing", "ISM manifatturiero"), (r"ism services", "ISM servizi"),
    (r"manufacturing pmi", "PMI manifatturiero"), (r"services pmi", "PMI servizi"),
    (r"cb consumer confidence", "Fiducia dei consumatori (Conference Board)"),
    (r"uom consumer sentiment", "Fiducia dei consumatori (Michigan)"), (r"inflation expectations", "Aspettative di inflazione"),
    (r"durable goods", "Ordini di beni durevoli"), (r"main refinancing rate|monetary policy statement", "BCE · decisione sui tassi"),
    (r"boj policy rate", "BoJ · decisione sui tassi"),
]
_PERIOD = {"m/m": "mese", "q/q": "trimestre", "y/y": "anno"}


def event_name(title: str) -> str:
    """Nome italiano breve del dato macro ("Core PCE Price Index m/m" → "Inflazione PCE core · mese"); se non noto, il titolo."""
    t = title.lower()
    name = next((n for rx, n in EVENT_IT if re.search(rx, t)), None)
    if not name:
        return title
    per = next((v for k, v in _PERIOD.items() if k in t), "")
    return f"{name} · {per}" if per else name


def parse_calendar(rows: list[dict]) -> list[dict]:
    """Dati del calendario che contano per BTC: USA ad alto e medio impatto, euro/Cina/Giappone solo ad alto impatto."""
    out = []
    for x in rows:
        if not ((x.get("country") == "USD" and x.get("impact") in ("High", "Medium"))
                or (x.get("country") in ("EUR", "CNY", "JPY") and x.get("impact") == "High")):
            continue
        note = next((n for rx, n in EVENT_NOTES if re.search(rx, x["title"].lower())), "")
        out.append({"title": x["title"], "name": event_name(x["title"]), "country": x["country"], "date": x["date"],
                    "impact": {"High": "alto", "Medium": "medio"}.get(x["impact"], "basso"),
                    "forecast": x.get("forecast") or "", "previous": x.get("previous") or "", "note": note})
    return sorted(out, key=lambda e: _date(e["date"]) or _now())


def fetch_calendar(cache: Path | None = NEWS_CACHE) -> list[dict]:
    at = _now().isoformat(timespec="seconds")
    try:
        r = requests.get(CALENDAR_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0 RadarSignal/1.0"})
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        print(f"[news] calendario: {type(e).__name__}")
        rows = []
    out = parse_calendar(rows)
    _STATUS["calendario"] = {"ok": bool(out), "n": len(out), "at": at}
    return _with_fallback("calendar", out, cache, at)


FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
ECB_URL = "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html"
_MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September",
                                       "October", "November", "December"], 1)}


def fomc_time_rome(d) -> str:
    """Ora italiana della decisione FOMC (14:00 a New York) per la data d: 20:00 di norma, 19:00 nelle settimane in cui
    l'ora legale è sfasata tra USA ed Europa (metà marzo, fine ottobre/inizio novembre)."""
    import datetime as dt
    from zoneinfo import ZoneInfo
    t = dt.datetime(d.year, d.month, d.day, 14, 0, tzinfo=ZoneInfo("America/New_York"))
    return t.astimezone(ZoneInfo("Europe/Rome")).strftime("%H:%M")


def bank_at(b: dict) -> str:
    """Istante della decisione di una banca centrale (data + ora italiana) in ISO con il fuso giusto, ora legale compresa."""
    from zoneinfo import ZoneInfo
    d = datetime.fromisoformat(f"{b['date']}T{b.get('time') or '12:00'}:00").replace(tzinfo=ZoneInfo("Europe/Rome"))
    return d.isoformat()


def fetch_central_banks(n: int = 6, cache: Path | None = NEWS_CACHE) -> list[dict]:
    """Prossime riunioni di politica monetaria di Fed (FOMC) ed BCE, dai calendari ufficiali. Data = giorno della decisione;
    "at" = istante della decisione con il fuso (per la finestra "prima della chiusura di domenica")."""
    import datetime as dt
    today, out = dt.date.today(), []
    at = _now().isoformat(timespec="seconds")
    try:   # Fed: sezioni "2026 FOMC Meetings", mese + "17-18*" (asterisco = proiezioni economiche e conferenza più seguita)
        h = requests.get(FOMC_URL, timeout=15, headers={"User-Agent": "RadarSignal/1.0"}).text
        for y in re.finditer(r"(\d{4}) FOMC Meetings", h):
            seg = h[y.end():y.end() + 20000].split("FOMC Meetings")[0]
            for mon, days in re.findall(r"fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>.*?fomc-meeting__date[^>]*>([^<]+)<", seg, re.S):
                mon = mon.split("/")[-1].strip()
                d_end = re.findall(r"\d+", days)
                if mon not in _MONTHS or not d_end:
                    continue
                d = dt.date(int(y.group(1)), _MONTHS[mon], int(d_end[-1]))
                if d >= today:
                    out.append({"bank": "Fed", "title": "FOMC · decisione sui tassi" + (" e proiezioni" if "*" in days else ""),
                                "date": d.isoformat(), "time": fomc_time_rome(d), "impact": "alto",
                                "note": "Tassi USA e conferenza stampa di Powell: l'evento macro che muove di più BTC."})
    except Exception as e:  # noqa: BLE001
        print(f"[news] FOMC: {type(e).__name__}")
    try:   # BCE: solo le riunioni di politica monetaria seguite da conferenza stampa (giorno della decisione)
        h = requests.get(ECB_URL, timeout=15, headers={"User-Agent": "RadarSignal/1.0"}).text
        for d, t in re.findall(r"<dt[^>]*>\s*(\d{2}/\d{2}/\d{4})\s*</dt>\s*<dd[^>]*>(.*?)</dd>", h, re.S):
            t = re.sub(r"<[^>]+>", "", t).lower()
            if "monetary policy meeting" in t and "non-monetary" not in t and "press conference" in t:
                dd = dt.datetime.strptime(d, "%d/%m/%Y").date()
                if dd >= today:
                    out.append({"bank": "BCE", "title": "BCE · decisione sui tassi", "date": dd.isoformat(), "time": "14:15",
                                "impact": "medio", "note": "Tassi dell'area euro: effetto su BTC soprattutto attraverso il dollaro."})
    except Exception as e:  # noqa: BLE001
        print(f"[news] BCE: {type(e).__name__}")
    out = [dict(b, at=bank_at(b)) for b in sorted(out, key=lambda e: e["date"])[:n]]
    _STATUS["banche centrali"] = {"ok": bool(out), "n": len(out), "at": at}
    res = _with_fallback("banks", out, cache, at)
    return [b for b in res if b["date"] >= today.isoformat()] if res and res[0].get("stale") else res


# ---------------------------------------------------------------- "Prima della decisione di domenica"
def next_close(now: datetime) -> datetime:
    """Prossima chiusura settimanale di W3.2: domenica 24:00 UTC (= lunedì 00:00 UTC), strettamente dopo `now`."""
    from datetime import timedelta
    now = now.astimezone(timezone.utc)
    monday = (now + timedelta(days=7 - now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday


def agenda(calendar: list[dict], banks: list[dict], now: datetime | None = None) -> dict:
    """Eventi in calendario da inizio giornata (ora italiana) fino alla prossima chiusura settimanale, in ordine di tempo:
    dati macro della fonte calendario + riunioni di banca centrale. Ogni voce: kind ("dato"/"banca"), name, at (ISO UTC),
    impact, note, past. Riferimento di agendaW() nella dashboard (stessa regola, verificata con node nei test)."""
    from zoneinfo import ZoneInfo
    now = (now or _now()).astimezone(timezone.utc)
    close = next_close(now)
    day0 = now.astimezone(ZoneInfo("Europe/Rome")).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    ev = []
    for e in calendar or []:
        d = _date(e.get("date") or "")
        if d:
            ev.append({"kind": "dato", "name": e.get("name") or event_name(e["title"]), "country": e.get("country", ""),
                       "at": d.astimezone(timezone.utc), "impact": e.get("impact", "medio"), "note": e.get("note", ""),
                       "forecast": e.get("forecast", ""), "previous": e.get("previous", "")})
    for b in banks or []:
        d = datetime.fromisoformat(b.get("at") or bank_at(b))
        ev.append({"kind": "banca", "name": b["title"], "country": b.get("bank", ""), "at": d.astimezone(timezone.utc),
                   "impact": b.get("impact", "alto"), "note": b.get("note", ""), "forecast": "", "previous": ""})
    ev.sort(key=lambda x: (x["at"], x["impact"] != "alto"))
    inside = [dict(x, at=x["at"].isoformat(), past=x["at"] < now) for x in ev if day0 <= x["at"] < close]
    after = next((dict(x, at=x["at"].isoformat(), past=False) for x in ev if x["at"] >= close and x["impact"] == "alto"), None)
    return {"close": close.isoformat(), "events": inside, "next_after": after}
