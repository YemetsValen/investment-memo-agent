from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Recommendation(StrEnum):
    BUY = "BUY"
    HOLD = "HOLD"
    AVOID = "AVOID"
    REVIEW = "REVIEW"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MemoStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REVIEW = "REVIEW"
    FAILED = "FAILED"


# ── Financial data ──────────────────────────────────────────────


class CompanyFinancials(BaseModel):
    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float | None = None
    pe_ratio: float | None = None
    forward_pe: float | None = None
    price_to_book: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    profit_margin: float | None = None
    roe: float | None = None
    current_ratio: float | None = None
    dividend_yield: float | None = None
    beta: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    current_price: float | None = None
    free_cash_flow: float | None = None
    earnings_growth: float | None = None


# ── Risk assessment ─────────────────────────────────────────────


class RiskFlag(BaseModel):
    category: str = Field(description="Risk category, e.g. 'Valuation', 'Debt', 'Governance'")
    level: RiskLevel
    description: str = Field(description="Concise explanation of the risk")
    metric: str | None = Field(default=None, description="Metric that triggered this flag")
    value: str | None = Field(default=None, description="Actual metric value")
    threshold: str | None = Field(default=None, description="Threshold that was exceeded")


# ── Investment memo ─────────────────────────────────────────────


class InvestmentMemo(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    ticker: str
    company_name: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: MemoStatus = MemoStatus.PENDING

    # Analysis outputs
    financials: CompanyFinancials | None = None
    summary: str = ""
    thesis: str = ""
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    recommendation: Recommendation = Recommendation.REVIEW
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Markdown report
    report_md: str = ""


# ── REVIEW queue ────────────────────────────────────────────────


class ReviewQueueItem(BaseModel):
    memo_id: str
    ticker: str
    recommendation: Recommendation
    confidence: float
    risk_flags_count: int
    critical_flags: int
    reason: str = Field(description="Why this memo was sent to REVIEW")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── API schemas ─────────────────────────────────────────────────


class AnalysisRequest(BaseModel):
    ticker: str = Field(description="Stock ticker symbol, e.g. 'AAPL'")


class AnalysisResponse(BaseModel):
    memo_id: str
    status: MemoStatus
    message: str = ""
