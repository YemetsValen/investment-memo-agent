"""FastAPI routes for the Investment Memo Agent."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.agents.graph import compile_graph
from src.models.memo import (
    AnalysisRequest,
    AnalysisResponse,
    InvestmentMemo,
    MemoStatus,
    ReviewQueueItem,
)
from src.services.review_queue import evaluate_memo
from src.services.storage import store

logger = logging.getLogger(__name__)
router = APIRouter()

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_company(request: AnalysisRequest):
    """Run the full multi-agent analysis pipeline for a ticker."""
    ticker = request.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")

    memo = InvestmentMemo(ticker=ticker, status=MemoStatus.PROCESSING)
    store.save(memo)

    logger.info("Starting analysis for %s (memo_id=%s)", ticker, memo.id)

    try:
        graph = compile_graph()
        result = await graph.ainvoke({"ticker": ticker})
    except Exception as exc:
        logger.error("Pipeline failed for %s: %s", ticker, exc)
        memo.status = MemoStatus.FAILED
        store.save(memo)
        return AnalysisResponse(
            memo_id=memo.id,
            status=MemoStatus.FAILED,
            message=str(exc),
        )

    # Update memo with results
    memo.financials = result.get("financials")
    memo.company_name = memo.financials.name if memo.financials else ticker
    memo.summary = result.get("summary", "")
    memo.thesis = result.get("thesis", "")
    memo.risk_flags = result.get("risk_flags", [])
    memo.recommendation = result.get("recommendation", "REVIEW")
    memo.confidence = result.get("confidence", 0.0)
    memo.report_md = result.get("report_md", "")

    # Apply confidence-threshold + risk-flag REVIEW logic
    memo = evaluate_memo(memo)

    # Save report to disk
    report_path = REPORTS_DIR / f"{ticker}_{memo.id}.md"
    report_path.write_text(memo.report_md, encoding="utf-8")
    logger.info("Report saved to %s", report_path)

    return AnalysisResponse(
        memo_id=memo.id,
        status=memo.status,
        message=f"Analysis complete. Recommendation: {memo.recommendation}",
    )


@router.get("/memo/{memo_id}", response_model=InvestmentMemo)
async def get_memo(memo_id: str):
    """Retrieve a completed investment memo by ID."""
    memo = store.get(memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")
    return memo


@router.get("/memos", response_model=list[InvestmentMemo])
async def list_memos():
    """List all investment memos."""
    return store.list_all()


@router.get("/review-queue", response_model=list[ReviewQueueItem])
async def get_review_queue():
    """Get all memos pending human review."""
    return store.get_review_queue()


@router.post("/review-queue/{memo_id}/approve", response_model=InvestmentMemo)
async def approve_memo(memo_id: str):
    """Approve a memo from the review queue."""
    memo = store.approve_review(memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found in review queue")
    return memo


@router.post("/review-queue/{memo_id}/reject", response_model=InvestmentMemo)
async def reject_memo(memo_id: str):
    """Reject a memo from the review queue."""
    memo = store.reject_review(memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found in review queue")
    return memo


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "investment-memo-agent"}
