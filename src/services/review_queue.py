"""Decide whether a memo needs human review based on confidence + risk flags.

Mirrors the strict-moderator pattern:
  confidence < threshold  →  REVIEW
  critical risk flags     →  REVIEW
  otherwise               →  auto-publish
"""

from __future__ import annotations

from src.config import settings
from src.models.memo import (
    InvestmentMemo,
    MemoStatus,
    Recommendation,
    ReviewQueueItem,
    RiskLevel,
)
from src.services.storage import store


def evaluate_memo(memo: InvestmentMemo) -> InvestmentMemo:
    """Apply confidence-threshold + risk-flag rules.

    Returns the memo with updated status and recommendation.
    """
    critical_count = sum(
        1 for f in memo.risk_flags if f.level == RiskLevel.CRITICAL
    )
    high_count = sum(
        1 for f in memo.risk_flags if f.level == RiskLevel.HIGH
    )

    needs_review = False
    reasons: list[str] = []

    # Rule 1: low confidence
    if memo.confidence < settings.confidence_threshold:
        needs_review = True
        reasons.append(
            f"Confidence {memo.confidence:.2f} < threshold {settings.confidence_threshold}"
        )

    # Rule 2: critical risk flags
    if critical_count > 0:
        needs_review = True
        reasons.append(f"{critical_count} CRITICAL risk flag(s)")

    # Rule 3: many high-risk flags
    if high_count >= 3:
        needs_review = True
        reasons.append(f"{high_count} HIGH risk flags (>=3)")

    if needs_review:
        memo.status = MemoStatus.REVIEW
        memo.recommendation = Recommendation.REVIEW
        store.add_to_review(
            ReviewQueueItem(
                memo_id=memo.id,
                ticker=memo.ticker,
                recommendation=memo.recommendation,
                confidence=memo.confidence,
                risk_flags_count=len(memo.risk_flags),
                critical_flags=critical_count,
                reason="; ".join(reasons),
            )
        )
    else:
        memo.status = MemoStatus.COMPLETED

    store.save(memo)
    return memo
