"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
)

app = FastAPI(
    title="Investment Memo Agent",
    description=(
        "AI-powered investment due-diligence assistant. "
        "Multi-agent LangGraph pipeline: Researcher → Analyst → Risk → Writer. "
        "Low-confidence memos go to a human REVIEW queue."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


def run() -> None:
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    run()
