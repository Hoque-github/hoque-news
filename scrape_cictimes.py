# scrape_cictimes.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_cictimes_articles():
    url = "https://www.cictimes.com/category/immigrate"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print("Error fetching CICTimes:", e)
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = []

    for post in soup.select('article'):
        title_tag = post.select_one('h2 a')
        date_tag = post.select_one('time')

        if not title_tag or not date_tag:
            continue

        title = title_tag.text.strip()
        link = title_tag['href']
        date_text = date_tag.text.strip()
        try:
            date = datetime.strptime(date_text, '%d %b, %Y | %I:%M %p').strftime('%b %d, %Y')
        except ValueError:
            date = date_text

        articles.append({'title': title, 'link': link, 'date': date})

    return articles
