
"""
Helper Functions
"""
import re
import feedparser
from app.core.config import IMAGE_BASE_URL, STATS_BASE_URL
from app.core.constants import TRACK_LAYOUT

""" CIRCUIT LAYOUT """
def get_track_layout(location: str) -> str:
    filename = TRACK_LAYOUT.get(location)

    if filename is None:
        return ""

    return f"{IMAGE_BASE_URL}/{filename}"

""" DRIVER IMAGE """
def get_driver_image(driver_id: str) -> str:
    return f"{IMAGE_BASE_URL}/drivers/{driver_id}.webp"


""" CONSTRUCTOR IMAGE """
def get_constructor_logo(constructor_id: str) -> str:
    return f"{IMAGE_BASE_URL}/constructors/{constructor_id}.webp"

""" STATS """
def stats(path: str) -> str:
    return f"{STATS_BASE_URL}/{path}"

""" NEWS IMAGE """
def extract_image(entry) -> str:
    if "enclosures" in entry and entry.enclosures:
        return entry.enclosures[0].get("url", "")

    if "media_content" in entry:
        return entry.media_content[0].get("url", "")

    if "summary" in entry:
        img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.summary)
        if img_match:
            return img_match.group(1)

    return ""

def clean_description(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)

    if len(text) > 150:
        return text[:150] + "..."

    return text

def parse_feed(url: str, source: str) -> list:
    try:
        feed = feedparser.parse(url)

    except Exception:
        return []

    articles = []

    for entry in feed.entries:

        articles.append({
            "title": entry.get("title", "No Title"),
            "description": clean_description(
                entry.get("summary", "")
            ),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "published_parsed": entry.get("published_parsed"),
            "image": extract_image(entry),
            "source": source
        })

    return articles

def remove_duplicates(articles):

    seen = set()

    unique = []

    for article in articles:

        key = ( 
            article["title"].strip().lower(),
            article["source"]
        )
        if key in seen:
            continue

        seen.add(key)

        unique.append(article)

    return unique