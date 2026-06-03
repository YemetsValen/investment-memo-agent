"""LLM factory — picks Anthropic or OpenAI based on config."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from src.config import LLMProvider, settings


def get_llm() -> BaseChatModel:
    if settings.llm_provider == LLMProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,  # type: ignore[arg-type]
            max_tokens=2048,
            temperature=0.2,
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,  # type: ignore[arg-type]
        max_tokens=2048,
        temperature=0.2,
    )
