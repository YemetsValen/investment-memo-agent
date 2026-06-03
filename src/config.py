from __future__ import annotations

from enum import StrEnum

from pydantic_settings import BaseSettings


class LLMProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class Settings(BaseSettings):
    # LLM
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"

    # Database
    database_url: str = "sqlite+aiosqlite:///./memos.db"

    # Confidence threshold: memos below this go to REVIEW queue
    confidence_threshold: float = 0.7

    # App
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
