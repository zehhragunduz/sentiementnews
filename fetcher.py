import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

import feedparser
import requests

logger = logging.getLogger(__name__)

RSS_SOURCES: Dict[str, str] = {
    "NTV":        "https://www.ntv.com.tr/son-dakika.rss",
    "Sabah":      "https://www.sabah.com.tr/rss/anasayfa.xml",
    "Hürriyet":   "https://www.hurriyet.com.tr/rss/anasayfa",
    "CNN Türk":   "https://www.cnnturk.com/feed/rss/all/news",
    "TRT Haber":  "https://www.trthaber.com/sondakika.rss",
    "Milliyet":   "https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml",
    "Habertürk":  "https://www.haberturk.com/rss",
    "AA":         "https://www.aa.com.tr/tr/rss/default?cat=guncel",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}
_HTML_RE = re.compile(r"<[^>]+>")


def _clean_html(text: str) -> str:
    return _HTML_RE.sub("", text).strip()


def _parse_date(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6]).isoformat()
            except Exception:
                pass
    return datetime.now().isoformat()


def fetch_feed(source_name: str, url: str, timeout: int = 10) -> List[Dict]:
    """Tek bir RSS kaynağından haberleri çeker."""
    articles: List[Dict] = []
    try:
        response = requests.get(url, timeout=timeout, headers=_HEADERS)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        for entry in feed.entries:
            title   = entry.get("title", "").strip()
            summary = _clean_html(entry.get("summary", entry.get("description", "")))
            link    = entry.get("link", "").strip()
            if not title:
                continue
            articles.append({
                "source":     source_name,
                "title":      title,
                "summary":    summary,
                "link":       link,
                "published":  _parse_date(entry),
                "fetched_at": datetime.now().isoformat(),
            })

        logger.info("%s: %d haber alındı.", source_name, len(articles))
    except requests.exceptions.Timeout:
        logger.warning("%s: bağlantı zaman aşımına uğradı.", source_name)
    except Exception as exc:
        logger.error("%s: RSS alınamadı — %s", source_name, exc)

    return articles


def fetch_all(
    sources: Optional[Dict[str, str]] = None,
    delay: float = 0.5,
) -> List[Dict]:
    """Tüm RSS kaynaklarından haberleri çekip tek liste döner."""
    if sources is None:
        sources = RSS_SOURCES

    all_articles: List[Dict] = []
    for name, url in sources.items():
        all_articles.extend(fetch_feed(name, url))
        time.sleep(delay)

    logger.info("Toplam %d haber alındı.", len(all_articles))
    return all_articles
