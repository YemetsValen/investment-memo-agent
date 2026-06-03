"""Fetch company financial data via yfinance (free, no API key required)."""

from __future__ import annotations

import logging

import yfinance as yf

from src.models.memo import CompanyFinancials

logger = logging.getLogger(__name__)


def _safe(info: dict, key: str) -> float | None:
    val = info.get(key)
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


async def fetch_financials(ticker: str) -> CompanyFinancials:
    """Fetch key financial metrics for a ticker from Yahoo Finance."""
    logger.info("Fetching financials for %s", ticker)
    stock = yf.Ticker(ticker)
    info = stock.info

    if not info or info.get("quoteType") is None:
        msg = f"Ticker '{ticker}' not found on Yahoo Finance"
        raise ValueError(msg)

    return CompanyFinancials(
        ticker=ticker.upper(),
        name=info.get("longName", info.get("shortName", "")),
        sector=info.get("sector", ""),
        industry=info.get("industry", ""),
        market_cap=_safe(info, "marketCap"),
        pe_ratio=_safe(info, "trailingPE"),
        forward_pe=_safe(info, "forwardPE"),
        price_to_book=_safe(info, "priceToBook"),
        debt_to_equity=_safe(info, "debtToEquity"),
        revenue_growth=_safe(info, "revenueGrowth"),
        profit_margin=_safe(info, "profitMargins"),
        roe=_safe(info, "returnOnEquity"),
        current_ratio=_safe(info, "currentRatio"),
        dividend_yield=_safe(info, "dividendYield"),
        beta=_safe(info, "beta"),
        fifty_two_week_high=_safe(info, "fiftyTwoWeekHigh"),
        fifty_two_week_low=_safe(info, "fiftyTwoWeekLow"),
        current_price=_safe(info, "currentPrice") or _safe(info, "regularMarketPrice"),
        free_cash_flow=_safe(info, "freeCashflow"),
        earnings_growth=_safe(info, "earningsGrowth"),
    )


async def fetch_price_history(ticker: str, period: str = "1y") -> list[dict]:
    """Fetch historical price data for charting / trend analysis."""
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    if hist.empty:
        return []
    records: list[dict] = []
    for date, row in hist.iterrows():
        records.append(
            {
                "date": str(date.date()),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            }
        )
    return records
