# news_portal/utils/fetch_rss.py

import feedparser
from datetime import datetime, timedelta
import requests


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



# FOR AI 
# # AI

def fetch_ai_news(source):
    try:
        if source["type"] == "rss2json":
            response = requests.get(source["url"])
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
        elif source["type"] == "rss":
            feed = feedparser.parse(source["url"])
            items = feed.entries
        else:
            print(f"[WARN] Unknown source type: {source['type']}")
            return []

        articles = []
        max_age = timedelta(days=source.get("max_age_days", 60))
        now = datetime.now()

        for item in items[:source.get("max_articles", 10)]:
            # Handle pubDate for both formats
            pub_date_raw = item.get("published", "") or item.get("pubDate", "")
            try:
                pub_date = datetime(*item.published_parsed[:6])
            except Exception:
                pub_date = now

            if now - pub_date > max_age:
                continue

            time_str = pub_date.strftime("%b %d, %Y")

            articles.append({
                "title": item.get("title", "No title"),
                "link": item.get("link", "#"),
                "summary": item.get("description", "") or item.get("summary", ""),
                "time": time_str,
                "image": extract_image(item)
            })

        return articles

    except Exception as e:
        print(f"[ERROR] Failed to fetch AI news: {e}")
        return []

def extract_image(item):
    # Try common RSS image tags
    if "media_content" in item and item["media_content"]:
        return item["media_content"][0].get("url", "")
    elif "media_thumbnail" in item and item["media_thumbnail"]:
        return item["media_thumbnail"][0].get("url", "")
    elif "image" in item:
        return item["image"]
    return ""





#__all__ = ["fetch_news_articles", "RSS_FEEDS"]