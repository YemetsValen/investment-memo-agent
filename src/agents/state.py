"""Shared agent state definition for LangGraph."""

from __future__ import annotations

from typing import TypedDict

from src.models.memo import CompanyFinancials, Recommendation, RiskFlag
from src.tools.news import NewsItem


class AgentState(TypedDict, total=False):
    """State passed between agents in the LangGraph pipeline."""

    # Input
    ticker: str

    # Researcher output
    financials: CompanyFinancials
    news: list[NewsItem]
    price_history: list[dict]

    # Analyst output
    summary: str
    thesis: str
    recommendation: Recommendation
    confidence: float

    # Risk output
    risk_flags: list[RiskFlag]

    # Writer output
    report_md: str

    # Error tracking
    error: str
