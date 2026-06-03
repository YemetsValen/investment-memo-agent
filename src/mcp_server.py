"""MCP server — exposes investment analysis tools for Claude / Cursor / etc."""

from __future__ import annotations

import asyncio
import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.agents.graph import compile_graph
from src.models.memo import InvestmentMemo, MemoStatus
from src.services.review_queue import evaluate_memo
from src.services.storage import store
from src.tools.financials import fetch_financials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("investment-memo-agent")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_financials",
            description="Fetch key financial metrics for a stock ticker (via Yahoo Finance).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. 'AAPL'",
                    }
                },
                "required": ["ticker"],
            },
        ),
        Tool(
            name="generate_memo",
            description=(
                "Run the full multi-agent investment analysis pipeline "
                "(Researcher → Analyst → Risk → Writer) and return the "
                "structured investment memo with recommendation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. 'AAPL'",
                    }
                },
                "required": ["ticker"],
            },
        ),
        Tool(
            name="screen_company",
            description=(
                "Quick screen: fetch financials + run rule-based risk checks. "
                "Faster than generate_memo (no LLM calls)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. 'AAPL'",
                    }
                },
                "required": ["ticker"],
            },
        ),
        Tool(
            name="list_review_queue",
            description="List all memos currently in the human REVIEW queue.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_financials":
        ticker = arguments["ticker"].upper()
        financials = await fetch_financials(ticker)
        return [TextContent(type="text", text=financials.model_dump_json(indent=2))]

    if name == "generate_memo":
        ticker = arguments["ticker"].upper()
        graph = compile_graph()
        result = await graph.ainvoke({"ticker": ticker})

        memo = InvestmentMemo(
            ticker=ticker,
            status=MemoStatus.PROCESSING,
            company_name=result.get("financials", {}).name
            if result.get("financials")
            else ticker,
            financials=result.get("financials"),
            summary=result.get("summary", ""),
            thesis=result.get("thesis", ""),
            risk_flags=result.get("risk_flags", []),
            recommendation=result.get("recommendation", "REVIEW"),
            confidence=result.get("confidence", 0.0),
            report_md=result.get("report_md", ""),
        )
        memo = evaluate_memo(memo)
        return [TextContent(type="text", text=memo.report_md)]

    if name == "screen_company":
        from src.agents.risk import _check_rules

        ticker = arguments["ticker"].upper()
        financials = await fetch_financials(ticker)
        flags = _check_rules(financials.model_dump())
        result = {
            "ticker": ticker,
            "company": financials.name,
            "financials": financials.model_dump(),
            "risk_flags": [f.model_dump() for f in flags],
            "risk_flag_count": len(flags),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    if name == "list_review_queue":
        queue = store.get_review_queue()
        items = [item.model_dump() for item in queue]
        return [TextContent(type="text", text=json.dumps(items, indent=2, default=str))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


def main() -> None:
    logger.info("Starting Investment Memo Agent MCP server")
    asyncio.run(_run())


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
