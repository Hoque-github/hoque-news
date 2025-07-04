from flask import Flask, jsonify, render_template, request
from flask_apscheduler import APScheduler
from utils.fetch_rss import fetch_news_articles
from cachetools import TTLCache
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from utils.fetch_rss import fetch_news_articles, RSS_FEEDS
from utils.fetch_rss import fetch_ai_news
from bs4 import BeautifulSoup
import os
from datetime import datetime
app = Flask(__name__)

# Global RSS cache: max 100 feeds, expire after 10 minutes
rss_cache = TTLCache(maxsize=100, ttl=600)

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
        "name": "CNN Top stories",
        "type": "rss",
        "url": "http://rss.cnn.com/rss/cnn_topstories.rss",
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

    {
        "name": "Guardians",
        "type": "rss",
        "url": "https://www.theguardian.com/world/rss",
        "max_articles": 10,
        "max_age_days": 7
    },

    {
        "name": "New York Times",
        "type": "rss",
        "url": "https://www.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "max_articles": 10,
        "max_age_days": 7
    },

    {
        "name": "AP News",
        "type": "rss",
        "url": "https://apnews.com/apf-topnews.rss",
        "max_articles": 10,
        "max_age_days": 7
    },
 
    {
        "name": "Al Jazeera",
        "type": "rss",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "max_articles": 10,
        "max_age_days": 7
    },

    {
        "name": "The Wall Street",
        "type": "rss",
        "url": "https://feeds.a.dj.com/rss/RHS.xml",
        "max_articles": 10,
        "max_age_days": 7
    },

    {
        "name": "Washington Post",
        "type": "rss",
        "url": "https://feeds.washingtonpost.com/rss/national",
        "max_articles": 10,
        "max_age_days": 7
    },

    {
        "name": "USA Today",
        "type": "rss",
        "url": "http://rssfeeds.usatoday.com/usatoday-NewsTopStories",
        "max_articles": 10,
        "max_age_days": 7
    },

        {
        "name": "Global News",
        "type": "rss",
        "url": "https://globalnews.ca/feed/",
        "max_articles": 10,
        "max_age_days": 7
    },
    {
        "name": "Toronto Star",
        "type": "rss",
        "url": "https://www.thestar.com/content/thestar/feed.RSSManagerServlet.articles.topstories.rss",
        "max_articles": 10,
        "max_age_days": 7
    },
        {
        "name": "National Post",
        "type": "rss",
        "url": "https://nationalpost.com/feed/",
        "max_articles": 10,
        "max_age_days": 7
    },
    {
        "name": "Financial Post",
        "type": "rss",
        "url": "https://business.financialpost.com/feed/",
        "max_articles": 10,
        "max_age_days": 7
    },
    {
        "name": "China Daily",
        "type": "rss",
        "url": "http://www.chinadaily.com.cn/rss/china_rss.xml",
        "max_articles": 10,
        "max_age_days": 7
    },
    {
        "name": "TODAY Online (Singapore)",
        "type": "rss",
        "url": "https://www.todayonline.com/rss",
        "max_articles": 10,
        "max_age_days": 7
    },

    {
        "name": "Dawn Pakistan",
        "type": "rss",
        "url": "https://www.dawn.com/feeds/home",
        "max_articles": 10,
        "max_age_days": 6
    },
    {
        "name": "The National UAE",
        "type": "rss",
        "url": "https://www.thenationalnews.com/rsse",
        "max_articles": 10,
        "max_age_days": 7
    },
    {
        "name": "TN",
        "type": "rss",
        "url": "https://www.thestar.com/authors.james_royson.html/.rss",
        "max_articles": 10,
        "max_age_days": 7
    },
    {
        "name": "Daily Star",
        "type": "rss",
        "url": "https://newsindex.fahadahammed.com/feed/get_feed_data/thedailystar/feed.xml",
        "max_articles": 10,
        "max_age_days": 7
    },

    {
        "name": "BX",
        "type": "rss",
        "url": "https://en.sunnews24x7.com/feeds",
        "max_articles": 10,
        "max_age_days": 7
    },


]



AI_NEWS_SOURCE = [
    {
        "name": "VentureBeat AI",
        "type": "rss",
        "url": "https://venturebeat.com/category/ai/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "MIT Technology Review – AI",
        "type": "rss",
        "url": "https://www.technologyreview.com/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "AI News",
        "type": "rss",
        "url": "https://www.artificialintelligence-news.com/feed/rss/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "AI Business",
        "type": "rss",
        "url": "https://aibusiness.com/rss.xml",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Towards Data Science – AI",
        "type": "rss",
        "url": "https://towardsdatascience.com/tagged/artificial-intelligence/rss",
        "max_articles": 10,
        "max_age_days": 600
    },


    {
        "name": "The Guardian – AI",
        "type": "rss",
        "url": "https://www.theguardian.com/technology/artificialintelligenceai/rss",
        "max_articles": 10,
        "max_age_days": 600
    },

    {
        "name": "OpenAI Blog",
        "type": "rss",
        "url": "https://openai.com/blog/rss/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Google AI Blog",
        "type": "rss",
        "url": "https://ai.googleblog.com/feeds/posts/default",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Meta AI Blog",
        "type": "rss",
        "url": "https://ai.meta.com/blog/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "DeepMind Blog",
        "type": "rss",
        "url": "https://www.deepmind.com/blog/rss",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "MIT AI",
        "type": "rss",
        "url": "https://www.technologyreview.com/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    
    {
        "name": "AI News",
        "type": "rss",
        "url": "https://www.artificialintelligence-news.com/feed/rss/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "AI Accelerator",
        "type": "rss",
        "url": "https://aiacceleratorinstitute.com/rss/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "AI Trends",
        "type": "rss",
        "url": "https://www.aitrends.com/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "The Gradient",
        "type": "rss",
        "url": "https://thegradient.pub/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },

    {
        "name": "AI Weekly",
        "type": "rss",
        "url": "https://aiweekly.co/rss",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Unite AI",
        "type": "rss",
        "url": "https://unite.ai/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Daily AI",
        "type": "rss",
        "url": "https://dailyai.com/feed",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Daily AI",
        "type": "rss",
        "url": "https://dailyai.com/feed",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Mark Tech",
        "type": "rss",
        "url": "https://www.marktechpost.com/feed",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "The Verge",
        "type": "rss",
        "url": "https://www.theverge.com/rss/index.xml",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Ars Technica",
        "type": "rss",
        "url": "https://feeds.arstechnica.com/arstechnica/index ",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "WIRED AI",
        "type": "rss",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "max_articles": 10,
        "max_age_days": 600
    },

    {
        "name": "Venture Beat",
        "type": "rss",
        "url": "https://venturebeat.com/category/ai/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Tech Crunch",
        "type": "rss",
        "url": "https://techcrunch.com/tag/ai/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "ZDNet AI",
        "type": "rss",
        "url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Tech republic",
        "type": "rss",
        "url": "https://www.techrepublic.com/rssfeeds/topic/artificial-intelligence/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Microsoft AI Blog",
        "type": "rss",
        "url": "https://blogs.microsoft.com/ai/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Google Cloud Blog",
        "type": "rss",
        "url": "https://cloud.google.com/blog/topics/ai-ml/rss.xml",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "IBM Blog AI",
        "type": "rss",
        "url": "https://www.ibm.com/blogs/research/category/artificial-intelligence/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "NVIDIA AI Blog",
        "type": "rss",
        "url": "https://blogs.nvidia.com/blog/category/ai/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "ScienceDaily AI News",
        "type": "rss",
        "url": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "MIT AI News",
        "type": "rss",
        "url": "https://news.mit.edu/rss/topic/artificial-intelligence",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Forbes AI & Blockchain",
        "type": "rss",
        "url": "https://www.forbes.com/ai/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Forbes AI & Blockchain",
        "type": "rss",
        "url": "https://www.forbes.com/ai/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Business Insider AI",
        "type": "rss",
        "url": "https://www.businessinsider.com/rss?IR=T",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Financial Times AI",
        "type": "rss",
        "url": "https://www.ft.com/artificial-intelligence?format=rss",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "The Register AI",
        "type": "rss",
        "url": "https://www.theregister.com/tag/ai/headlines.atom",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "ArXiv.org cs AI",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "ArXiv.org cs ML",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.LG",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "ArXiv.org St ML",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/stat.ML",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Barkeley AI Blog",
        "type": "rss",
        "url": "https://bair.berkeley.edu/blog/feed.xml",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Distll Pub AI Reserch",
        "type": "rss",
        "url": "https://distill.pub/rss.xml",
        "max_articles": 10,
        "max_age_days": 600
    },
     {
        "name": "Machine Learning Mastery",
        "type": "rss",
        "url": "https://machinelearningmastery.com/blog/feed/",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Kaggle Blog",
        "type": "rss",
        "url": "https://medium.com/feed/kaggle-blog",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "AI Now Institute",
        "type": "rss",
        "url": "https://ainowinstitute.org/category/news/feed",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Hacker News",
        "type": "rss",
        "url": "https://news.ycombinator.com/rss",
        "max_articles": 10,
        "max_age_days": 600
    },
    {
        "name": "Reddit AI",
        "type": "rss",
        "url": "https://rss.app/feeds/A1B2C3D4E5F6G7H8.xml",
        "max_articles": 10,
        "max_age_days": 600
    },

]





CRYPTO_NEWS_SOURCE = [
    {
        "name": "Coin desk",
        "type": "rss",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "max_articles": 90,
        "max_age_days": 30
    },

    {
        "name": "Coin Telegraph",
        "type": "rss",
        "url": "https://cointelegraph.com/rss/",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Bitcoin.com",
        "type": "rss",
        "url": "https://news.bitcoin.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Be In Crypto",
        "type": "rss",
        "url": "https://beincrypto.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Crypto Slate",
        "type": "rss",
        "url": "https://cryptoslate.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Bitcoin Megazine",
        "type": "rss",
        "url": "https://bitcoinmagazine.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "CryptoNews.com",
        "type": "rss",
        "url": "https://cryptonews.com/news/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Daily Hodl",
        "type": "rss",
        "url": "https://dailyhodl.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Reuters Crypto",
        "type": "rss",
        "url": "https://www.reuters.com/arc/outboundfeeds/tag/cryptocurrencies/?outputType=rss/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Bloomberg Crypto",
        "type": "rss",
        "url": "https://www.bloomberg.com/feeds/bpol/news.xml",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Forbes Crypto",
        "type": "rss",
        "url": "https://www.forbes.com/crypto-blockchain/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Coindesk All News",
        "type": "rss",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Coin Journal",
        "type": "rss",
        "url": "https://coinjournal.net/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "FXStreet",
        "type": "rss",
        "url": "https://www.fxstreet.com/rss/news/cryptocurrencies",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Alpha Bitcoin",
        "type": "rss",
        "url": "https://seekingalpha.com/tag/bitcoin/feed",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Zero Hedge",
        "type": "rss",
        "url": "https://www.zerohedge.com/rss.xml",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Yahoo Finance",
        "type": "rss",
        "url": "https://finance.yahoo.com/news/rssindex",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Business Insider",
        "type": "rss",
        "url": "https://www.businessinsider.com/feed/?alpha_token=BI",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Messari Crypto News",
        "type": "rss",
        "url": "https://messari.io/feed/news",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Crypto Quant",
        "type": "rss",
        "url": "https://cryptoquant.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Glassnode",
        "type": "rss",
        "url": "https://insights.glassnode.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Blockonmi",
        "type": "rss",
        "url": "https://blockonomi.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Inside Bitcoins",
        "type": "rss",
        "url": "https://insidebitcoins.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Crypto Globe",
        "type": "rss",
        "url": "https://www.cryptoglobe.com/feed",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Token Post",
        "type": "rss",
        "url": "https://tokenpost.com/rss",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Blockchain.com",
        "type": "rss",
        "url": "https://www.blockchain.com/blog/rss.xml",
        "max_articles": 10,
        "max_age_days": 90
    },

    {
        "name": "Blockchain.com",
        "type": "rss",
        "url": "https://rss.app/feeds/e3U9TqPzVd0F0QWd.xml",
        "max_articles": 10,
        "max_age_days": 90
    },

]

CRICKET_NEWS_SOURCE = [
    {
        "name": "ESPNcricinfo – Australia",
        "type": "rss",
        "url": "https://www.espncricinfo.com/rss/content/story/feeds/6.xml",
        "max_articles": 10,
        "max_age_days": 90
    },
    
    {"name": "ESPNcricinfo – Global", "type": "rss", "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "max_articles": 10, "max_age_days": 90},
    {"name": "ESPNcricinfo – Pakistan", "type": "rss", "url": "https://www.espncricinfo.com/rss/content/story/feeds/7.xml", "max_articles": 10, "max_age_days": 90},
    {"name": "ESPNcricinfo – Bangladesh", "type": "rss", "url": "https://www.espncricinfo.com/rss/content/story/feeds/3.xml", "max_articles": 10, "max_age_days": 90},
    {"name": "ESPNcricinfo – Sri Lanka", "type": "rss", "url": "https://www.espncricinfo.com/rss/content/story/feeds/17.xml", "max_articles": 10, "max_age_days": 90},
    {"name": "ESPNcricinfo – England", "type": "rss", "url": "https://www.espncricinfo.com/rss/content/story/feeds/4.xml", "max_articles": 10, "max_age_days": 90},
    {"name": "Feedspot – Cricket Times", "type": "rss", "url": "https://crickettimes.com/feed", "max_articles": 10, "max_age_days": 90},
    {"name": "Feedspot – Cricket Addictor", "type": "rss", "url": "https://cricketaddictor.com/feed", "max_articles": 10, "max_age_days": 90},
    {"name": "Feedspot – CricBuzz", "type": "rss", "url": "https://www.cricbuzz.com/rss/news", "max_articles": 10, "max_age_days": 90},
    {"name": "Island Cricket (Sri Lanka)", "type": "rss", "url": "https://islandcricket.lk/feed", "max_articles": 10, "max_age_days": 90},
    {"name": "Bangla Cricket (Bangladesh)", "type": "rss", "url": "https://feed.podbean.com/banglacricket/feed.xml", "max_articles": 10, "max_age_days": 90},
    {"name": "Cricbuzz – All News)", "type": "rss", "url": "https://feeds.cricbuzz.com/cricbuzz-feed", "max_articles": 10, "max_age_days": 90},
    {"name": "Cricwaves", "type": "rss", "url": "https://cricwaves.com/feed/", "max_articles": 10, "max_age_days": 90},
    {"name": "Cricket Web", "type": "rss", "url": "https://cricketweb.net/feed/", "max_articles": 10, "max_age_days": 90},
    {"name": "CricTracker", "type": "rss", "url": "https://www.crictracker.com/feed/", "max_articles": 10, "max_age_days": 90},
    {"name": "Cricket Country", "type": "rss", "url": "https://www.cricketcountry.com/rss", "max_articles": 10, "max_age_days": 90},
    {"name": "ICC Official News)", "type": "rss", "url": "https://www.icc-cricket.com/rss", "max_articles": 10, "max_age_days": 90},

]

FOOTBALL_NEWS_SOURCE = [
    {
        "name": "101 Great Goals",
        "type": "rss",
        "url": "https://www.101greatgoals.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "90min",
        "type": "rss",
        "url": "https://www.90min.com/rss",
        "max_articles": 10,
        "max_age_days": 90
    },
     {
        "name": "Soccer News",
        "type": "rss",
        "url": "https://www.soccernews.com/rss",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Caught Offside",
        "type": "rss",
        "url": "https://www.caughtoffside.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "FootballFan Cast",
        "type": "rss",
        "url": "https://www.footballfancast.com/feed/",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Football Italia",
        "type": "rss",
        "url": "https://www.football-italia.net/rss",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "MARCA La Liga Focus",
        "type": "rss",
        "url": "https://e00-marca.uecdn.es/rss/feed/portada.xml",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "MLSsoccer.com",
        "type": "rss",
        "url": "https://www.mlssoccer.com/rss/rss.xml",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Goal.com",
        "type": "rss",
        "url": "https://www.goal.com/en-us/feeds/news/google.xml",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Arseblog (Arsenal Fans)",
        "type": "rss",
        "url": "https://arseblog.com/feed/ ",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Exp Tribune Pakistan – Football",
        "type": "rss",
        "url": "https://tribune.com.pk/feeds/football",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "Qaumi Awaz (Pakistan)",
        "type": "rss",
        "url": "https://www.qaumiawaz.com/section/football.rss",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "News Int'l(Pakistan) Sports ",
        "type": "rss",
        "url": "https://www.thenews.com.pk/rss/category/Football.xml ",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "UNI India Football",
        "type": "rss",
        "url": "https://www.uniindia.com/rss/feedSports.xml",
        "max_articles": 10,
        "max_age_days": 90
    },
    {
        "name": "NDTV Sports – Football",
        "type": "rss",
        "url": "https://sports.ndtv.com/football/rss",
        "max_articles": 10,
        "max_age_days": 90
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
    

import re

def generate_summary(text, max_sentences=10):
    """Extract the first few sentences from the description as a summary."""
    # Basic sentence splitting (could be improved with NLP later)
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    summary = ' '.join(sentences[:max_sentences])
    return summary



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

    for article in all_articles:
        desc = article.get("description", "") or article.get("content", "")
        if desc:
            soup = BeautifulSoup(desc, "html.parser")
            clean_desc = soup.get_text(separator=" ", strip=True)
            article["description"] = clean_desc
        else:
            article["description"] = "No description available."

        content = article.get("content", "")
        if content:
            soup = BeautifulSoup(content, "html.parser")
            clean_content = soup.get_text(separator=" ", strip=True)
            article["content"] = clean_content
        else:
            article["content"] = article["description"]

#    return render_template("index.html")
    return render_template("index.html", articles=all_articles, page_title="🌍 Today's Top World News Headlines")


@app.route("/trending")
def trending():
    response = requests.get(f'https://newsdata.io/api/1/news?apikey={NEWSDATAAPI_KEY}&category=top&language=en')
    data = response.json()
    return jsonify(data["results"])



@app.route("/ainews")
def ainews():
    all_articles = []
    for source in AI_NEWS_SOURCE:
        if source["type"] == "rss2json":
            all_articles.extend(fetch_rss2json(source))
        elif source["type"] == "rss":
            all_articles.extend(fetch_rss(source))
        elif source["type"] == "api":
            all_articles.extend(fetch_api_articles(source))

    all_articles = sorted(all_articles, key=get_pub_time, reverse=True)

    for article in all_articles:
        desc = article.get("description", "") or article.get("content", "")
        if desc:
            soup = BeautifulSoup(desc, "html.parser")
            clean_desc = soup.get_text(separator=" ", strip=True)
            article["description"] = clean_desc
        else:
            article["description"] = "No description available."

        content = article.get("content", "")
        if content:
            soup = BeautifulSoup(content, "html.parser")
            clean_content = soup.get_text(separator=" ", strip=True)
            article["content"] = clean_content
        else:
            article["content"] = article["description"]

    return render_template("ainews.html", articles=all_articles, page_title="🤖 Breaking AI News & Trends")

    #return render_template("index.html", articles=all_articles)




@app.route("/crypto")
def crypto():
    all_articles = []
    for source in CRYPTO_NEWS_SOURCE:
        if source["type"] == "rss2json":
            all_articles.extend(fetch_rss2json(source))
        elif source["type"] == "rss":
            all_articles.extend(fetch_rss(source))
        elif source["type"] == "api":
            all_articles.extend(fetch_api_articles(source))

    all_articles = sorted(all_articles, key=get_pub_time, reverse=True)

    for article in all_articles:
        desc = article.get("description", "") or article.get("content", "")
        if desc:
            soup = BeautifulSoup(desc, "html.parser")
            clean_desc = soup.get_text(separator=" ", strip=True)
            article["description"] = clean_desc
        else:
            article["description"] = "No description available."

        content = article.get("content", "")
        if content:
            soup = BeautifulSoup(content, "html.parser")
            clean_content = soup.get_text(separator=" ", strip=True)
            article["content"] = clean_content
        else:
            article["content"] = article["description"]

    return render_template("crypto.html", articles=all_articles, page_title="🪙 Crypto & Blockchain: Market Moves and News")

#CRICKET
@app.route("/cricket")
def cricket():
    all_articles = []
    for source in CRICKET_NEWS_SOURCE:
        if source["type"] == "rss2json":
            all_articles.extend(fetch_rss2json(source))
        elif source["type"] == "rss":
            all_articles.extend(fetch_rss(source))
        elif source["type"] == "api":
            all_articles.extend(fetch_api_articles(source))

    all_articles = sorted(all_articles, key=get_pub_time, reverse=True)

    for article in all_articles:
        desc = article.get("description", "") or article.get("content", "")
        if desc:
            soup = BeautifulSoup(desc, "html.parser")
            clean_desc = soup.get_text(separator=" ", strip=True)
            article["description"] = clean_desc
        else:
            article["description"] = "No description available."

        content = article.get("content", "")
        if content:
            soup = BeautifulSoup(content, "html.parser")
            clean_content = soup.get_text(separator=" ", strip=True)
            article["content"] = clean_content
        else:
            article["content"] = article["description"]

    return render_template("cricket.html", articles=all_articles, page_title="🏏 World Cricket Today",
            page_subtitle="Latest cricket scores, match analyses, expert insights, and team news from Test, ODI, T20, IPL, PSL & beyond.")


#FOOTBALL
@app.route("/football")
def football():
    all_articles = []
    for source in FOOTBALL_NEWS_SOURCE:
        if source["type"] == "rss2json":
            all_articles.extend(fetch_rss2json(source))
        elif source["type"] == "rss":
            all_articles.extend(fetch_rss(source))
        elif source["type"] == "api":
            all_articles.extend(fetch_api_articles(source))

    all_articles = sorted(all_articles, key=get_pub_time, reverse=True)

    for article in all_articles:
        desc = article.get("description", "") or article.get("content", "")
        if desc:
            soup = BeautifulSoup(desc, "html.parser")
            clean_desc = soup.get_text(separator=" ", strip=True)
            article["description"] = clean_desc
        else:
            article["description"] = "No description available."

        content = article.get("content", "")
        if content:
            soup = BeautifulSoup(content, "html.parser")
            clean_content = soup.get_text(separator=" ", strip=True)
            article["content"] = clean_content
        else:
            article["content"] = article["description"]

    return render_template("football.html", articles=all_articles, page_title="⚽ Global Football Highlights",
            page_subtitle="Breaking news, match updates, player stories, and everything football – from the Premier League to the World Cup.")


#CANADA IMMIGRATION




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

# AI NEWS

# app.py
@app.route("/ai-news")
def ai_news():
    all_ai_articles = []
    for source in AI_NEWS_SOURCE:
        articles = fetch_ai_news(source)
        all_ai_articles.extend(articles)

    # Sort with images first
    all_ai_articles.sort(key=lambda x: x.get("image") is None)

    # Trending = top 5 articles with title + url
    trending = [
        {"title": a['title'], "url": a['url']}
        for a in all_ai_articles
        if a.get('title') and a.get('url')
    ][:5]

    return render_template("ai_news.html", articles=all_ai_articles, trending=trending)




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
    app.run(host='0.0.0.0', port = 5000, debug=True)
