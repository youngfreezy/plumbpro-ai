"""LLM client factory for PlumbPro AI.

Provides pre-configured LangChain chat model instances for the different
tiers (default, premium, light) used throughout the orchestrator.
Includes a retry wrapper for transient API failures.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage

from backend.shared.config import get_settings

logger = logging.getLogger(__name__)

# Retry configuration
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 1.5  # seconds


def _build_anthropic(model: str, **kwargs: Any) -> ChatAnthropic:
    """Construct a ChatAnthropic instance with shared defaults."""
    settings = get_settings()
    return ChatAnthropic(
        model=model,
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=4096,
        temperature=0,
        **kwargs,
    )


def get_default_model(**kwargs: Any) -> ChatAnthropic:
    """Return the default-tier model (Sonnet class)."""
    settings = get_settings()
    return _build_anthropic(settings.ANTHROPIC_DEFAULT_MODEL, **kwargs)


def get_premium_model(**kwargs: Any) -> ChatAnthropic:
    """Return the premium-tier model (Opus class)."""
    settings = get_settings()
    return _build_anthropic(settings.ANTHROPIC_PREMIUM_MODEL, **kwargs)


def get_light_model(**kwargs: Any) -> ChatAnthropic:
    """Return the light-tier model (Haiku class) for fast classification."""
    settings = get_settings()
    return _build_anthropic(settings.ANTHROPIC_LIGHT_MODEL, **kwargs)


async def invoke_with_retry(
    llm: ChatAnthropic,
    messages: list[BaseMessage],
    *,
    max_retries: int = _MAX_RETRIES,
    backoff_base: float = _RETRY_BACKOFF_BASE,
) -> BaseMessage:
    """Invoke the LLM with exponential-backoff retry on transient errors.

    Parameters
    ----------
    llm:
        A LangChain chat model (with or without bound tools).
    messages:
        The message list to send.
    max_retries:
        Maximum number of retry attempts after the first failure.
    backoff_base:
        Base seconds for exponential backoff.

    Returns
    -------
    BaseMessage
        The AIMessage response from the model.
    """
    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            response = await llm.ainvoke(messages)
            return response
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                wait = backoff_base * (2 ** attempt)
                logger.warning(
                    "LLM call failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries + 1,
                    wait,
                    exc,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "LLM call failed after %d attempts: %s",
                    max_retries + 1,
                    exc,
                )
    raise last_error  # type: ignore[misc]
