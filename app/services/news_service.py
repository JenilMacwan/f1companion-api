from app.core.config import PRIMARY_RSS_URL, SECONDARY_RSS_URL, FALLBACK_RSS_URL
from app.utils.helpers import parse_feed, remove_duplicates


def get_f1_news():

    """ Fetch the latest F1 news from RSS feeds."""

    formula_articles = parse_feed(
    PRIMARY_RSS_URL,
    "Formula 1"
    )

    sky_articles = parse_feed(
        SECONDARY_RSS_URL,              
        "Sky Sports"
    )

    autosport_articles = parse_feed(
        FALLBACK_RSS_URL,
        "Autosport"
    )

    all_articles = (
        formula_articles +
        sky_articles +
        autosport_articles
    )

    all_articles = remove_duplicates(all_articles)

    all_articles.sort(
        key=lambda x: x["published_parsed"] or (),
        reverse=True
    )   

    for article in all_articles:
        article.pop("published_parsed", None)

    return {
        "status": "ok",
        "articles": all_articles[:10]
    }