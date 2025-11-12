from flask import Flask, render_template, request, redirect, url_for
import feedparser
from bs4 import BeautifulSoup
import webbrowser
import threading
import requests  # added for reliable feed fetching

app = Flask(__name__)

RSS_FEEDS = {
    'technology': 'https://timesofindia.indiatimes.com/rssfeeds/66949542.cms',
    'sports': 'https://timesofindia.indiatimes.com/rssfeeds/4719148.cms',
    'india': 'https://feeds.feedburner.com/ndtvnews-india-news',
    'entertainment': 'https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms',
    'world': 'https://feeds.feedburner.com/ndtvnews-world-news',
    'business': 'https://timesofindia.indiatimes.com/rssfeeds/1898055.cms',
}

@app.route('/')
def home():
    return render_template(
        'index.html',
        categories=RSS_FEEDS.keys(),
        articles=None,
        error=None,
        selected_category=None
    )

@app.route('/news', methods=['GET', 'POST'])
def news():
    if request.method == 'POST':
        category = request.form.get('category')
        if category not in RSS_FEEDS:
            return render_template(
                'index.html',
                error="Invalid category selected.",
                categories=RSS_FEEDS.keys(),
                articles=None,
                selected_category=None
            )
        return redirect(url_for('news', category=category))
    
    category = request.args.get('category')
    if category not in RSS_FEEDS:
        return render_template(
            'index.html',
            error="Please select a valid category.",
            categories=RSS_FEEDS.keys(),
            articles=None,
            selected_category=None
        )

    # Use requests with browser-like headers to avoid blocking
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(RSS_FEEDS[category], headers=headers, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as e:
        return render_template(
            'index.html',
            error=f"Failed to fetch RSS feed: {str(e)}",
            categories=RSS_FEEDS.keys(),
            articles=None,
            selected_category=category
        )

    if feed.bozo:
        return render_template(
            'index.html',
            error="Failed to parse RSS feed.",
            categories=RSS_FEEDS.keys(),
            articles=None,
            selected_category=category
        )

    articles = []
    for entry in feed.entries[:8]:
        title = entry.get('title', 'No title')
        link = entry.get('link', 'No link')

        image = None
        if 'media_content' in entry:
            image = entry.media_content[0]['url']
        elif 'description' in entry:
            soup = BeautifulSoup(entry.description, 'html.parser')
            img = soup.find('img')
            if img:
                image = img.get('src')

        summary_html = entry.get('summary') or entry.get('description') or ''
        soup = BeautifulSoup(summary_html, 'html.parser')
        summary_text = soup.get_text()
        if len(summary_text) > 150:
            summary_text = summary_text[:147] + "..."

        articles.append({
            'title': title,
            'link': link,
            'image': image,
            'summary': summary_text,
        })

    return render_template(
        'index.html',
        articles=articles,
        selected_category=category,
        categories=RSS_FEEDS.keys(),
        error=None
    )

def open_browser():
    webbrowser.get('open -a "Google Chrome" %s').open("http://127.0.0.1:5050")

if __name__ == '__main__':
    threading.Timer(1.25, open_browser).start()
    app.run(debug=True, port=5050)
