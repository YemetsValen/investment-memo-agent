"""Risk-assessment agent: evaluates financial metrics against thresholds."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.llm import get_llm
from src.agents.state import AgentState
from src.models.memo import RiskFlag, RiskLevel

logger = logging.getLogger(__name__)

# ── Rule-based risk checks (fast, no LLM needed) ───────────────

METRIC_RULES: list[dict] = [
    {
        "category": "Valuation",
        "field": "pe_ratio",
        "op": ">",
        "threshold": 40,
        "level": RiskLevel.HIGH,
        "desc": "P/E ratio significantly above market average",
    },
    {
        "category": "Debt",
        "field": "debt_to_equity",
        "op": ">",
        "threshold": 200,
        "level": RiskLevel.CRITICAL,
        "desc": "Debt-to-equity ratio dangerously high",
    },
    {
        "category": "Debt",
        "field": "debt_to_equity",
        "op": ">",
        "threshold": 100,
        "level": RiskLevel.HIGH,
        "desc": "Elevated debt-to-equity ratio",
    },
    {
        "category": "Profitability",
        "field": "profit_margin",
        "op": "<",
        "threshold": 0,
        "level": RiskLevel.HIGH,
        "desc": "Negative profit margin — company is losing money",
    },
    {
        "category": "Liquidity",
        "field": "current_ratio",
        "op": "<",
        "threshold": 1.0,
        "level": RiskLevel.HIGH,
        "desc": "Current ratio below 1 — potential liquidity risk",
    },
    {
        "category": "Volatility",
        "field": "beta",
        "op": ">",
        "threshold": 2.0,
        "level": RiskLevel.MEDIUM,
        "desc": "High beta — stock is significantly more volatile than market",
    },
    {
        "category": "Growth",
        "field": "revenue_growth",
        "op": "<",
        "threshold": -0.1,
        "level": RiskLevel.HIGH,
        "desc": "Revenue declining more than 10% — negative growth trend",
    },
    {
        "category": "Growth",
        "field": "earnings_growth",
        "op": "<",
        "threshold": -0.2,
        "level": RiskLevel.HIGH,
        "desc": "Earnings declining more than 20%",
    },
    {
        "category": "Valuation",
        "field": "price_to_book",
        "op": ">",
        "threshold": 10,
        "level": RiskLevel.MEDIUM,
        "desc": "Price-to-book ratio very high — may be overvalued",
    },
]


def _check_rules(financials_dict: dict) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    for rule in METRIC_RULES:
        val = financials_dict.get(rule["field"])
        if val is None:
            continue
        triggered = (
            (rule["op"] == ">" and val > rule["threshold"])
            or (rule["op"] == "<" and val < rule["threshold"])
        )
        if triggered:
            flags.append(
                RiskFlag(
                    category=rule["category"],
                    level=rule["level"],
                    description=rule["desc"],
                    metric=rule["field"],
                    value=str(round(val, 4)),
                    threshold=f"{rule['op']} {rule['threshold']}",
                )
            )
    return flags


# ── LLM-based qualitative risk assessment ──────────────────────

RISK_SYSTEM_PROMPT = """\
You are a risk analyst. Given the company data and news, identify qualitative \
risks NOT captured by simple metric thresholds. Focus on:
- Governance/regulatory risks
- Competitive threats
- Macro/sector risks
- News-driven concerns

Return ONLY a JSON array of risk objects:
[{"category": "...", "level": "LOW|MEDIUM|HIGH|CRITICAL", "description": "..."}]

Return an empty array [] if no additional qualitative risks are found."""


async def _llm_risk_check(state: AgentState) -> list[RiskFlag]:
    financials = state.get("financials")
    news = state.get("news", [])
    if not financials:
        return []

    news_text = "\n".join(f"- {n.title}" for n in news[:8])
    user_content = f"""Company: {financials.name} ({financials.ticker})
Sector: {financials.sector} | Industry: {financials.industry}

Recent News:
{news_text or '(none)'}"""

    llm = get_llm()
    response = await llm.ainvoke(
        [SystemMessage(content=RISK_SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )

    try:
        content = response.content
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""
        content = str(content).strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        items = json.loads(content)
    except (json.JSONDecodeError, IndexError):
        logger.warning("[Risk] Could not parse LLM risk response")
        return []

    flags: list[RiskFlag] = []
    for item in items:
        level_raw = item.get("level", "MEDIUM").upper()
        if level_raw not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            level_raw = "MEDIUM"
        flags.append(
            RiskFlag(
                category=item.get("category", "Other"),
                level=RiskLevel(level_raw),
                description=item.get("description", ""),
            )
        )
    return flags


# ── Main node ───────────────────────────────────────────────────


async def risk_node(state: AgentState) -> AgentState:
    """Evaluate risks using both rule-based and LLM-based checks."""
    if "error" in state and state["error"]:
        return state

    financials = state.get("financials")
    if not financials:
        return state

    # Rule-based flags
    rule_flags = _check_rules(financials.model_dump())

    # LLM-based qualitative flags
    llm_flags = await _llm_risk_check(state)

    all_flags = rule_flags + llm_flags
    logger.info(
        "[Risk] Found %d rule-based + %d LLM-based flags for %s",
        len(rule_flags),
        len(llm_flags),
        financials.ticker,
    )

    return {**state, "risk_flags": all_flags}
