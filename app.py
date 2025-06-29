from flask import Flask, jsonify, render_template, request
from flask_apscheduler import APScheduler
from utils.fetch_rss import fetch_news_articles

import feedparser
import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from utils.fetch_rss import fetch_news_articles, RSS_FEEDS


import os

app = Flask(__name__)

DEFAULT_IMAGE = "/static/default.jpg"

# Set your API keys here or use environment variables
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "e5e201b4d81c43d6883ca45fd6602d10")
NEWSDATAAPI_KEY = os.getenv("NEWSDATAAPI_KEY", "pub_b510dfc52f0d4ae491fde45b3f300812")
BING_API_KEY = os.getenv("BING_API_KEY", "YOUR_BING_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "665aad188352edc541d8240238d430c5")
NYT_API_KEY = os.getenv("NYT_API_KEY", "YOUR_NYTIMES_API_KEY")

NEWS_SOURCES = [
    {
        "name": "BBC News",
        "type": "rss2json",
        "url": "https://api.rss2json.com/v1/api.json?rss_url=https://feeds.bbci.co.uk/news/rss.xml",
        "max_articles": 10,
        "max_age_days": 30
    },
    {
        "name": "CNN",
        "type": "rss",
        "url": "http://rss.cnn.com/rss/edition.rss",
        "max_articles": 5,
        "max_age_days": 30
    },
    {
        "name": "Reuters",
        "type": "rss",
        "url": "http://feeds.reuters.com/reuters/topNews",
        "max_articles": 10,
        "max_age_days": 7
    },
    {
        "name": "NewsAPI",
        "type": "api",
        "api_type": "newsapi",
        "url": f"https://newsapi.org/v2/top-headlines?language=en&pageSize=10&apiKey={NEWSAPI_KEY}",
        "max_articles": 10,
        "max_age_days": 7
    },
    {
        "name": "Bing News",
        "type": "api",
        "api_type": "bing",
        "url": "https://api.bing.microsoft.com/v7.0/news/search?q=top&count=10&mkt=en-US",
        "max_articles": 10,
        "max_age_days": 5
    },
    {
        "name": "GNews",
        "type": "api",
        "api_type": "gnews",
        "url": f"https://gnews.io/api/v4/top-headlines?lang=en&max=10&token={GNEWS_API_KEY}",
        "max_articles": 10,
        "max_age_days": 5
    },
    {
        "name": "NYTimes",
        "type": "api",
        "api_type": "nyt",
        "url": f"https://api.nytimes.com/svc/topstories/v2/home.json?api-key={NYT_API_KEY}",
        "max_articles": 10,
        "max_age_days": 7
    },

    {
        "name": "NewsData.io",
        "type": "api",
        "api_type": "newsdata",
        "url": f"https://newsdata.io/api/1/news?apikey={'pub_b510dfc52f0d4ae491fde45b3f300812'}&language=en&country=us",
        "max_articles": 10,
        "max_age_days": 7
    },

]
NEWSDATAAPI_KEY

def time_since(pub_date_str):
    try:
        pub_date = date_parser.parse(pub_date_str)
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - pub_date
        hours = int(delta.total_seconds()) // 3600
        if hours < 24:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        days = hours // 24
        return f"{days} day{'s' if days != 1 else ''} ago"
    except Exception:
        return ""

def is_recent(pub_date_str, max_days=30):
    try:
        pub_date = date_parser.parse(pub_date_str)
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - pub_date) <= timedelta(days=max_days)
    except Exception:
        return False

def fetch_rss2json(source):
    try:
        res = requests.get(source["url"], timeout=10).json()
        if res.get("status") != "ok":
            return []
        articles = []
        for item in res.get("items", []):
            pub = item.get("pubDate", "")
            if not is_recent(pub, source.get("max_age_days", 30)):
                continue
            if not item.get("thumbnail"):
                continue
            articles.append({
                "title": item.get("title"),
                "content": item.get("description", ""),
                "url": item.get("link"),
                "source": source["name"],
                "image_url": item.get("thumbnail", DEFAULT_IMAGE),
                "time": time_since(pub),
                "published": pub
            })
            if len(articles) >= source.get("max_articles", 10):
                break
        return articles
    except Exception:
        return []

def fetch_rss(source):
    try:
        feed = feedparser.parse(source["url"])
        articles = []
        for e in feed.entries:
            pub = e.get("published") or e.get("updated") or ""
            if not is_recent(pub, source.get("max_age_days", 30)):
                continue
            if len(articles) >= source.get("max_articles", 10):
                break
            img = DEFAULT_IMAGE
            if 'media_content' in e:
                img = e.media_content[0].get('url', DEFAULT_IMAGE)
            elif 'enclosures' in e:
                img = e.enclosures[0].get('href', DEFAULT_IMAGE)
            articles.append({
                "title": e.get("title"),
                "content": e.get("summary", ""),
                "url": e.get("link"),
                "source": source["name"],
                "image_url": img,
                "time": time_since(pub),
                "published": pub
            })
        return articles
    except Exception:
        return []

def fetch_api_articles(source):
    try:
        res = requests.get(source["url"], headers={
            "Ocp-Apim-Subscription-Key": BING_API_KEY
        } if source.get("api_type") == "bing" else {}, timeout=10).json()
        articles = []

        if source["api_type"] == "newsapi":
            items = res.get("articles", [])
            for item in items:
                pub = item.get("publishedAt", "")
                if not is_recent(pub, source.get("max_age_days", 7)):
                    continue
                articles.append({
                    "title": item.get("title"),
                    "content": item.get("description", ""),
                    "url": item.get("url"),
                    "source": source["name"],
                    "image_url": item.get("urlToImage", DEFAULT_IMAGE),
                    "time": time_since(pub),
                    "published": pub
                })

        elif source["api_type"] == "bing":
            for item in res.get("value", []):
                pub = item.get("datePublished", "")
                if not is_recent(pub, source.get("max_age_days", 7)):
                    continue
                img = item.get("image", {}).get("thumbnail", {}).get("contentUrl", DEFAULT_IMAGE)
                articles.append({
                    "title": item.get("name"),
                    "content": item.get("description", ""),
                    "url": item.get("url"),
                    "source": source["name"],
                    "image_url": img,
                    "time": time_since(pub),
                    "published": pub
                })

        elif source["api_type"] == "gnews":
            for item in res.get("articles", []):
                pub = item.get("publishedAt", "")
                if not is_recent(pub, source.get("max_age_days", 7)):
                    continue
                articles.append({
                    "title": item.get("title"),
                    "content": item.get("description", ""),
                    "url": item.get("url"),
                    "source": source["name"],
                    "image_url": item.get("image", DEFAULT_IMAGE),
                    "time": time_since(pub),
                    "published": pub
                })

        elif source["api_type"] == "nyt":
            for item in res.get("results", []):
                pub = item.get("published_date", "")
                if not is_recent(pub, source.get("max_age_days", 7)):
                    continue
                img = DEFAULT_IMAGE
                if item.get("multimedia"):
                    img = item["multimedia"][0].get("url", DEFAULT_IMAGE)
                articles.append({
                    "title": item.get("title"),
                    "content": item.get("abstract", ""),
                    "url": item.get("url"),
                    "source": source["name"],
                    "image_url": img,
                    "time": time_since(pub),
                    "published": pub
                })

        return articles[:source.get("max_articles", 10)]

    except Exception:
        return []

def get_pub_time(article):
    try:
        pub = article.get("published", "")
        dt = date_parser.parse(pub)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


@app.route("/")
def index():
    all_articles = []
    for source in NEWS_SOURCES:
        if source["type"] == "rss2json":
            all_articles.extend(fetch_rss2json(source))
        elif source["type"] == "rss":
            all_articles.extend(fetch_rss(source))
        elif source["type"] == "api":
            all_articles.extend(fetch_api_articles(source))
    all_articles = sorted(all_articles, key=get_pub_time, reverse=True)
    return render_template("index.html", articles=all_articles)


@app.route("/trending")
def trending():
    response = requests.get(f'https://newsdata.io/api/1/news?apikey={NEWSDATAAPI_KEY}&category=top&language=en')
    data = response.json()
    return jsonify(data["results"])


@app.route("/load_more")
def load_more():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 20))

    all_articles = []
    for source in NEWS_SOURCES:
        if source["type"] == "rss2json":
            all_articles.extend(fetch_rss2json(source))
        elif source["type"] == "rss":
            all_articles.extend(fetch_rss(source))
        elif source["type"] == "api":
            all_articles.extend(fetch_api_articles(source))

    all_articles = sorted(all_articles, key=get_pub_time, reverse=True)
    sliced = all_articles[offset:offset + limit]
    return jsonify(sliced)

@app.route('/news')
def get_news():
    country = request.args.get('country', '').lower()
    category = request.args.get('category', '').lower()

    articles = []

    if country and category:
        # Case 1: Specific country + category
        articles = fetch_news_articles(country=country, category=category)
    elif country:
        # Case 2: All categories for a given country
        categories = RSS_FEEDS.get(country, {}).keys()
        for cat in categories:
            articles += fetch_news_articles(country=country, category=cat)
    elif category:
        # Case 3: Specific category across all countries
        for ctry in RSS_FEEDS:
            if category in RSS_FEEDS[ctry]:
                articles += fetch_news_articles(country=ctry, category=category)
    else:
        # Case 4: Default – general category from all countries
        for ctry in RSS_FEEDS:
            if 'general' in RSS_FEEDS[ctry]:
                articles += fetch_news_articles(country=ctry, category='general')

    return jsonify({"articles": articles[:30]})  # limit to 30 total results

    # Use these params in your news fetching logic (API calls or filters)

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

scheduler = APScheduler()

def scheduled_fetch():
    # You can customize which countries/categories to pre-fetch
    print("Running scheduled news fetch...")
    fetch_news_articles("us", "general")  # example; expand this if needed
    print(f"[{datetime.now()}] Scheduled job running...")
    fetch_news_articles()

    with open("log.txt", "a") as log:
        log.write(f"[{datetime.now()}] Scheduled job ran.\n")
    fetch_news_articles()

scheduler.init_app(app)
scheduler.start()

scheduler.add_job(id='Scheduled Task', func=scheduled_fetch, trigger='interval', hours=1)


if __name__ == "__main__":
    app.run(debug=True)
