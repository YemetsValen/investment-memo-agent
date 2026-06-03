"""Analyst agent: produces investment thesis + recommendation via LLM."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.llm import get_llm
from src.agents.state import AgentState
from src.models.memo import Recommendation

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior equity analyst. Given a company's financial data and recent \
news, produce a structured investment analysis.

Return ONLY valid JSON with these fields:
{
  "summary": "2-3 sentence company overview",
  "thesis": "Investment thesis explaining the core argument for/against",
  "recommendation": "BUY | HOLD | AVOID",
  "confidence": 0.0-1.0
}

Be data-driven. Reference specific metrics. If data is insufficient, lower \
your confidence score accordingly."""


async def analyst_node(state: AgentState) -> AgentState:
    """Analyze financial data and produce investment thesis."""
    if "error" in state and state["error"]:
        return state

    financials = state.get("financials")
    if not financials:
        return {**state, "error": "No financial data available for analysis"}

    news = state.get("news", [])
    news_text = "\n".join(f"- {n.title} ({n.publisher})" for n in news[:8])

    user_content = f"""Company: {financials.name} ({financials.ticker})
Sector: {financials.sector} | Industry: {financials.industry}

Key Metrics:
- Market Cap: {financials.market_cap}
- P/E Ratio: {financials.pe_ratio}
- Forward P/E: {financials.forward_pe}
- Price/Book: {financials.price_to_book}
- Debt/Equity: {financials.debt_to_equity}
- Revenue Growth: {financials.revenue_growth}
- Profit Margin: {financials.profit_margin}
- ROE: {financials.roe}
- Current Ratio: {financials.current_ratio}
- Beta: {financials.beta}
- Free Cash Flow: {financials.free_cash_flow}
- Earnings Growth: {financials.earnings_growth}
- 52-wk High: {financials.fifty_two_week_high}
- 52-wk Low: {financials.fifty_two_week_low}
- Current Price: {financials.current_price}

Recent News:
{news_text or '(no recent news)'}"""

    llm = get_llm()
    response = await llm.ainvoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )

    try:
        content = response.content
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""
        content = str(content).strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(content)
    except (json.JSONDecodeError, IndexError, KeyError) as exc:
        logger.warning("[Analyst] Failed to parse LLM response: %s", exc)
        return {
            **state,
            "summary": str(response.content)[:500],
            "thesis": "Analysis could not be structured",
            "recommendation": Recommendation.REVIEW,
            "confidence": 0.3,
        }

    rec_raw = result.get("recommendation", "HOLD").upper()
    if rec_raw not in {"BUY", "HOLD", "AVOID"}:
        rec_raw = "HOLD"

    return {
        **state,
        "summary": result.get("summary", ""),
        "thesis": result.get("thesis", ""),
        "recommendation": Recommendation(rec_raw),
        "confidence": min(max(float(result.get("confidence", 0.5)), 0.0), 1.0),
    }
