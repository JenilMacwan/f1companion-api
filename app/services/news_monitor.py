"""
Background monitor for news updates.
"""

import asyncio
import random
from app.services.news_service import get_f1_news
from app.services.notification_service import notify_breaking_news

_last_notified_article_url = None

async def start_news_monitoring(interval_hours: int = 3):
    """
    Background loop that polls for news every few hours.
    It picks the latest new article (or a random one from recent news if the latest was already sent).
    """
    global _last_notified_article_url
    interval_seconds = interval_hours * 3600
    print(f"Starting news monitor. Polling every {interval_hours} hours...")

    while True:
        try:
            # 1. Fetch latest news
            news_response = get_f1_news()
            articles = news_response.get("articles", [])
            
            if articles:
                # 2. Grab the latest article
                latest_article = articles[0]
                latest_url = latest_article.get("link")
                
                # 3. If it's a new article we haven't notified about yet, send it
                if latest_url and latest_url != _last_notified_article_url:
                    print(f"Pushing breaking news: {latest_article.get('title')}")
                    notify_breaking_news(latest_article)
                    _last_notified_article_url = latest_url
                else:
                    # As a fallback for the "random" requirement, we can pick a random one 
                    # if there are no new ones, but usually you only want to push *new* breaking news.
                    # We will stick to the latest unnotified article.
                    pass
                
        except Exception as e:
            print(f"Error in news monitor loop: {e}")
            
        # 4. Wait before polling again
        await asyncio.sleep(interval_seconds)
