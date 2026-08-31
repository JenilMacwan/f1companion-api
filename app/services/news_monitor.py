"""
Background monitor for news updates.
"""

import asyncio
import random
import datetime
from app.services.news_service import get_f1_news
from app.services.notification_service import notify_breaking_news

_sent_urls_today = set()
_current_day = None

async def start_news_monitoring():
    """
    Background loop that polls for news and pushes 5 times a day.
    It picks a random article that hasn't been sent yet today.
    """
    global _sent_urls_today, _current_day
    
    # 5 times a day = 24 hours / 5 = 4.8 hours
    interval_seconds = int((24 / 5) * 3600)
    print("Starting news monitor. Pushing 5 times a day...")

    while True:
        try:
            today = datetime.datetime.now().date()
            # Reset the list of sent articles at the start of a new day
            if today != _current_day:
                _current_day = today
                _sent_urls_today.clear()
            
            # 1. Fetch latest news
            news_response = get_f1_news()
            articles = news_response.get("articles", [])
            
            # 2. Filter out articles we've already sent today
            available_articles = [a for a in articles if a.get("link") not in _sent_urls_today]
            
            if available_articles:
                # 3. Pick a random article from the remaining ones
                article_to_send = random.choice(available_articles)
                url = article_to_send.get("link")
                
                print(f"Pushing breaking news: {article_to_send.get('title')}")
                notify_breaking_news(article_to_send)
                
                # Mark it as sent today
                if url:
                    _sent_urls_today.add(url)
                
        except Exception as e:
            print(f"Error in news monitor loop: {e}")
            
        # Wait before the next push
        await asyncio.sleep(interval_seconds)
