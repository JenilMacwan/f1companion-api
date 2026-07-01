"""
News service.

Responsible for RSS feed retrieval, fallback handling, HTML cleanup,
image extraction, and article formatting.
"""

import re
import feedparser


# RSS Feed Sources
PRIMARY_RSS = "https://www.skysports.com/rss/12433"
FALLBACK_RSS = "https://www.autosport.com/rss/f1/news"


def get_f1_news():
    """
    Fetch the latest F1 news from RSS feeds.

    Tries Sky Sports F1 first, falls back to Autosport if no entries found.

    Returns:
        Dict with status and articles list (up to 10 articles).
    """
    feed = feedparser.parse(PRIMARY_RSS)
    source_name = "Sky Sports F1"

    if not feed.entries:
        feed = feedparser.parse(FALLBACK_RSS)
        source_name = "Autosport F1"

    news_list = []
    try:
        for entry in feed.entries[:10]:
            image_url = ""

            # Check for standard RSS enclosures (common for images)
            if 'enclosures' in entry and len(entry.enclosures) > 0:
                image_url = entry.enclosures[0].get('url', '')

            # Fallback: Check for media:content tags (common in Sky/BBC feeds)
            elif 'media_content' in entry:
                image_url = entry.media_content[0].get('url', '')

            # Second Fallback: Regex search in summary/description if image is embedded in HTML
            elif not image_url and 'summary' in entry:
                img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.summary)
                if img_match:
                    image_url = img_match.group(1)

            # Remove HTML tags from the summary
            clean_summary = re.sub(r'<[^>]+>', '', entry.get('summary', ''))
            news_list.append({
                "title": entry.get('title', 'No Title'),
                "description": clean_summary[:150] + "...",
                "link": entry.get('link', ''),
                "published": entry.get('published', ''),
                "image": image_url if image_url else "No Image Available",
                "source": source_name
            })

        return {
            "status": "ok",
            "articles": news_list
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
