"""
News router.

Endpoint: /news
"""

from fastapi import APIRouter

from app.services.news_service import get_f1_news

router = APIRouter()


@router.get("/news")
def news():
    return get_f1_news()
