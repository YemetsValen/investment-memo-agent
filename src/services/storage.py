"""In-memory storage for memos and review queue.

Production-ready upgrade: swap for aiosqlite / Postgres.
Keeping it simple so the demo runs with zero external deps.
"""

from __future__ import annotations

from src.models.memo import InvestmentMemo, ReviewQueueItem


class MemoStore:
    """Thread-safe in-memory store for investment memos."""

    def __init__(self) -> None:
        self._memos: dict[str, InvestmentMemo] = {}
        self._review_queue: dict[str, ReviewQueueItem] = {}

    # ── Memos ───────────────────────────────────────────────────

    def save(self, memo: InvestmentMemo) -> None:
        self._memos[memo.id] = memo

    def get(self, memo_id: str) -> InvestmentMemo | None:
        return self._memos.get(memo_id)

    def list_all(self) -> list[InvestmentMemo]:
        return list(self._memos.values())

    # ── Review queue ────────────────────────────────────────────

    def add_to_review(self, item: ReviewQueueItem) -> None:
        self._review_queue[item.memo_id] = item

    def get_review_queue(self) -> list[ReviewQueueItem]:
        return list(self._review_queue.values())

    def approve_review(self, memo_id: str) -> InvestmentMemo | None:
        self._review_queue.pop(memo_id, None)
        memo = self._memos.get(memo_id)
        if memo:
            memo.status = "COMPLETED"  # type: ignore[assignment]
        return memo

    def reject_review(self, memo_id: str) -> InvestmentMemo | None:
        self._review_queue.pop(memo_id, None)
        memo = self._memos.get(memo_id)
        if memo:
            memo.status = "FAILED"  # type: ignore[assignment]
        return memo


store = MemoStore()
