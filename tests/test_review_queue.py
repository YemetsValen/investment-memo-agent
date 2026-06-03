"""Tests for the REVIEW queue confidence-threshold logic."""

from src.models.memo import (
    InvestmentMemo,
    MemoStatus,
    Recommendation,
    RiskFlag,
    RiskLevel,
)
from src.services.review_queue import evaluate_memo
from src.services.storage import store as global_store


def _reset_store():
    """Clear global store between tests."""
    global_store._memos.clear()
    global_store._review_queue.clear()


def test_high_confidence_passes():
    _reset_store()
    memo = InvestmentMemo(
        ticker="AAPL",
        recommendation=Recommendation.BUY,
        confidence=0.85,
        risk_flags=[],
    )
    result = evaluate_memo(memo)
    assert result.status == MemoStatus.COMPLETED
    assert result.recommendation == Recommendation.BUY


def test_low_confidence_goes_to_review():
    _reset_store()
    memo = InvestmentMemo(
        ticker="XYZ",
        recommendation=Recommendation.BUY,
        confidence=0.4,
        risk_flags=[],
    )
    result = evaluate_memo(memo)
    assert result.status == MemoStatus.REVIEW
    assert result.recommendation == Recommendation.REVIEW


def test_critical_flag_forces_review():
    _reset_store()
    memo = InvestmentMemo(
        ticker="BA",
        recommendation=Recommendation.AVOID,
        confidence=0.9,
        risk_flags=[
            RiskFlag(
                category="Debt",
                level=RiskLevel.CRITICAL,
                description="D/E > 200",
            ),
        ],
    )
    result = evaluate_memo(memo)
    assert result.status == MemoStatus.REVIEW


def test_many_high_flags_force_review():
    _reset_store()
    flags = [
        RiskFlag(category="A", level=RiskLevel.HIGH, description="flag1"),
        RiskFlag(category="B", level=RiskLevel.HIGH, description="flag2"),
        RiskFlag(category="C", level=RiskLevel.HIGH, description="flag3"),
    ]
    memo = InvestmentMemo(
        ticker="RISK",
        recommendation=Recommendation.HOLD,
        confidence=0.8,
        risk_flags=flags,
    )
    result = evaluate_memo(memo)
    assert result.status == MemoStatus.REVIEW


def test_review_queue_populated():
    _reset_store()
    memo = InvestmentMemo(
        ticker="LOW",
        recommendation=Recommendation.BUY,
        confidence=0.3,
        risk_flags=[],
    )
    evaluate_memo(memo)
    queue = global_store.get_review_queue()
    assert len(queue) == 1
    assert queue[0].memo_id == memo.id
