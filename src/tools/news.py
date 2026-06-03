"""Fetch recent news headlines for a company via yfinance."""

from __future__ import annotations

import contextlib
import logging
from datetime import datetime

import yfinance as yf
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class NewsItem(BaseModel):
    title: str
    publisher: str = ""
    link: str = ""
    published: datetime | None = None


async def fetch_news(ticker: str, max_items: int = 10) -> list[NewsItem]:
    """Return recent news headlines for the given ticker."""
    logger.info("Fetching news for %s", ticker)
    stock = yf.Ticker(ticker)
    raw_news = stock.news or []

    items: list[NewsItem] = []
    for entry in raw_news[:max_items]:
        published = None
        ts = entry.get("providerPublishTime")
        if ts:
            with contextlib.suppress(TypeError, ValueError, OSError):
                published = datetime.utcfromtimestamp(int(ts))

        items.append(
            NewsItem(
                title=entry.get("title", ""),
                publisher=entry.get("publisher", ""),
                link=entry.get("link", ""),
                published=published,
            )
        )
    return items
