"""Researcher agent: collects financial data, news, and price history."""

from __future__ import annotations

import logging

from src.agents.state import AgentState
from src.tools.financials import fetch_financials, fetch_price_history
from src.tools.news import fetch_news

logger = logging.getLogger(__name__)


async def researcher_node(state: AgentState) -> AgentState:
    """Gather raw data from external sources."""
    ticker = state["ticker"]
    logger.info("[Researcher] Collecting data for %s", ticker)

    try:
        financials = await fetch_financials(ticker)
    except Exception as exc:
        logger.error("[Researcher] Failed to fetch financials: %s", exc)
        return {**state, "error": f"Failed to fetch financials: {exc}"}

    news = await fetch_news(ticker, max_items=10)
    price_history = await fetch_price_history(ticker, period="1y")

    return {
        **state,
        "financials": financials,
        "news": news,
        "price_history": price_history,
    }
