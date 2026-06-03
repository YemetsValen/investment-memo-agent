"""Tests for Pydantic models."""

from src.models.memo import (
    AnalysisRequest,
    CompanyFinancials,
    InvestmentMemo,
    MemoStatus,
    Recommendation,
    ReviewQueueItem,
    RiskFlag,
    RiskLevel,
)


def test_company_financials_minimal():
    f = CompanyFinancials(ticker="AAPL")
    assert f.ticker == "AAPL"
    assert f.pe_ratio is None
    assert f.market_cap is None


def test_company_financials_full():
    f = CompanyFinancials(
        ticker="AAPL",
        name="Apple Inc.",
        market_cap=3e12,
        pe_ratio=28.5,
        debt_to_equity=150.0,
    )
    assert f.name == "Apple Inc."
    assert f.market_cap == 3e12


def test_risk_flag():
    flag = RiskFlag(
        category="Debt",
        level=RiskLevel.CRITICAL,
        description="D/E > 200",
        metric="debt_to_equity",
        value="250",
        threshold="> 200",
    )
    assert flag.level == RiskLevel.CRITICAL
    assert flag.metric == "debt_to_equity"


def test_investment_memo_defaults():
    memo = InvestmentMemo(ticker="TSLA")
    assert memo.status == MemoStatus.PENDING
    assert memo.recommendation == Recommendation.REVIEW
    assert memo.confidence == 0.0
    assert len(memo.id) == 12


def test_investment_memo_with_flags():
    flags = [
        RiskFlag(category="Valuation", level=RiskLevel.HIGH, description="P/E > 40"),
        RiskFlag(category="Debt", level=RiskLevel.CRITICAL, description="D/E > 200"),
    ]
    memo = InvestmentMemo(
        ticker="XYZ",
        risk_flags=flags,
        recommendation=Recommendation.AVOID,
        confidence=0.4,
    )
    assert len(memo.risk_flags) == 2
    assert memo.recommendation == Recommendation.AVOID


def test_analysis_request():
    req = AnalysisRequest(ticker="MSFT")
    assert req.ticker == "MSFT"


def test_review_queue_item():
    item = ReviewQueueItem(
        memo_id="abc123",
        ticker="BA",
        recommendation=Recommendation.REVIEW,
        confidence=0.35,
        risk_flags_count=5,
        critical_flags=2,
        reason="Low confidence; 2 CRITICAL flags",
    )
    assert item.critical_flags == 2
    assert item.reason.startswith("Low confidence")
