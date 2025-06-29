# news_portal/utils/fetch_rss.py

import feedparser
from datetime import datetime, timedelta

# In-memory cache
#_cache = {}
#_CACHE_DURATION = timedelta(hours=1)

# Define country/category/language-based RSS feeds
RSS_FEEDS = {
    "us": {
        "general": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "technology": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "business": "https://www.forbes.com/business/feed/",
        "sports": "https://www.espn.com/espn/rss/news",
        "politics": "https://www.politico.com/rss/politics08.xml",
        "stock": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "fashion": "https://www.vogue.com/feed/rss",
        "travel": "https://www.lonelyplanet.com/news/rss.xml"
    },
    "gb": {
        "general": "https://www.theguardian.com/uk/rss",
        "technology": "https://www.techradar.com/rss",
        "business": "https://www.ft.com/?format=rss",
        "sports": "https://www.bbc.com/sport/rss.xml",
        "politics": "https://feeds.bbci.co.uk/news/politics/rss.xml",
        "travel": "https://www.cntraveller.com/rss/article"
    },
    "ca": {
        "general": "https://globalnews.ca/feed/",
        "technology": "https://mobilesyrup.com/feed/",
        "business": "https://financialpost.com/feed/",
        "sports": "https://www.tsn.ca/rss",
        "politics": "https://www.ctvnews.ca/rss/ctvnews-ca-politics-public-rss-1.822285"
    },
    "in": {
        "general": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "technology": "https://gadgets360.com/rss/news",
        "business": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
        "sports": "https://sports.ndtv.com/rss/all",
        "politics": "https://www.indiatoday.in/rss/1206550"
    },
}

def fetch_news_articles(country="us", category="general"):
    feed_url = RSS_FEEDS.get(country, {}).get(category)
    if not feed_url:
        return []

    feed = feedparser.parse(feed_url)
    articles = []

    for entry in feed.entries:
        article = {
            "title": entry.get("title", "No title"),
            "link": entry.get("link", "#"),
            "description": entry.get("summary", ""),
            "image_url": entry.get("media_content", [{}])[0].get("url") if entry.get("media_content") else None,
            "published": entry.get("published", "")
        }
        articles.append(article)

    return articles

#__all__ = ["fetch_news_articles", "RSS_FEEDS"]