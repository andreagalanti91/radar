"""Notizie crypto e macro da feed RSS pubblici, classificate per scheda."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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

# schede tematiche: parole intere (regex), una notizia può stare in più schede
TABS = {
    "macro": r"\b(fed|fomc|powell|inflation|cpi|pce|rate cuts?|rate hikes?|interest rates?|treasur(y|ies)|yields?|dollar index|dxy|strong dollar|weak dollar|recession|jobs report|payrolls?|nfp|gdp|tariffs?|economy|federal reserve|ecb|boj|unemployment)\b",
    "regolamentazione": r"\b(sec|regulat\w*|lawsuits?|court|congress|senate|bills?|legislation|stablecoin act|genius act|clarity act|mica|esma|cftc|bans?|taxe?s?|licen[cs]e\w*|compliance|atkins|white house|trump administration)\b",
    "etf": r"\b(etfs?|blackrock|ibit|fidelity|grayscale|inflows?|outflows?|institutional|microstrategy|saylor|treasury compan\w*|corporate treasur\w*)\b",
    "derivati": r"\b(liquidat\w*|futures|open interest|funding rates?|options?|leverage\w*|short squeeze|whales?|on-?chain|exchange reserves?|miners?|hashrate|deribit|cme)\b",
}
BTC_RE = r"\b(bitcoin|btc)\b"
# impatto sul prezzo di BTC: parole che storicamente muovono il mercato
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


def classify(item: dict) -> tuple[list[str], int]:
    t = f" {item['title']} {item['summary']} ".lower()
    tabs = [k for k, rx in TABS.items() if re.search(rx, t)]
    if item["source"] == "Federal Reserve" and "macro" not in tabs:
        tabs.append("macro")
    btc = bool(re.search(BTC_RE, t))
    if btc:
        tabs.append("bitcoin")
    title = item["title"].lower()
    score = sum(w * (2 if re.search(rx, title) else 1) for rx, w in IMPACT if re.search(rx, t))
    score += 1 if btc else 0
    return tabs, score


def fetch_news(max_items: int = 80, max_age_days: int = 4) -> list[dict]:
    with ThreadPoolExecutor(8) as ex:
        items = [x for lst in ex.map(lambda kv: _fetch(*kv), FEEDS.items()) for x in lst]
    now = datetime.now(timezone.utc)
    seen, out = set(), []
    for it in sorted(items, key=lambda x: x["date"], reverse=True):
        key = re.sub(r"\W+", "", it["title"].lower())[:60]
        if key in seen or (now - datetime.fromisoformat(it["date"])).days > max_age_days:
            continue
        seen.add(key)
        it["tabs"], it["impact"] = classify(it)
        it["level"] = "alto" if it["impact"] >= 8 else "medio" if it["impact"] >= 4 else "basso"
        out.append(it)
    return out[:max_items]


# ---------------------------------------------------------------- calendario economico
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
# perché ogni dato conta per BTC (spiegazione breve mostrata in dashboard)
EVENT_NOTES = [
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
]


def fetch_calendar() -> list[dict]:
    try:
        r = requests.get(CALENDAR_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0 RadarSignal/1.0"})
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        print(f"[news] calendario: {type(e).__name__}")
        return []
    out = []
    for x in rows:
        if not ((x.get("country") == "USD" and x.get("impact") in ("High", "Medium"))
                or (x.get("country") in ("EUR", "CNY", "JPY") and x.get("impact") == "High")):
            continue
        note = next((n for rx, n in EVENT_NOTES if re.search(rx, x["title"].lower())), "")
        out.append({"title": x["title"], "country": x["country"], "date": x["date"],
                    "impact": {"High": "alto", "Medium": "medio"}.get(x["impact"], "basso"),
                    "forecast": x.get("forecast") or "", "previous": x.get("previous") or "", "note": note})
    return sorted(out, key=lambda e: e["date"])
