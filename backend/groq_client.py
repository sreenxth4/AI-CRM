"""
Shared Groq client helpers for the CRM agent.

Keeps model configuration, token caps, and rate-limit handling consistent
across the LangGraph agent and tool-level LLM calls.
"""

import os
import re
import time

from langchain_groq import ChatGroq


DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_RETRY_AFTER_SECONDS = 25.0
MAX_LOCAL_RETRY_WAIT_SECONDS = float(
    os.getenv("GROQ_MAX_LOCAL_RETRY_WAIT_SECONDS", "45")
)
RATE_LIMIT_MARKERS = (
    "rate_limit_exceeded",
    "Rate limit reached",
    "Error code: 429",
)


class GroqRateLimitError(Exception):
    """Raised when Groq is still rate-limited after local retry handling."""

    def __init__(self, retry_after_seconds: float, message: str | None = None):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            message
            or (
                "Groq rate limit reached. Please wait a few seconds and try "
                "again."
            )
        )


def get_groq_llm(*, max_tokens: int, temperature: float = 0.3):
    """Create a Groq chat model with conservative output limits."""
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        temperature=temperature,
        max_retries=0,
        max_tokens=max_tokens,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def invoke_groq_with_retry(llm, messages, *, attempts: int = 2):
    """Invoke Groq, waiting once when the provider returns a 429 retry hint."""
    for attempt in range(attempts):
        try:
            return llm.invoke(messages)
        except Exception as exc:
            retry_after = get_retry_after_seconds(exc)
            if retry_after is None:
                raise

            if (
                attempt < attempts - 1
                and retry_after <= MAX_LOCAL_RETRY_WAIT_SECONDS
            ):
                time.sleep(retry_after)
                continue

            raise GroqRateLimitError(retry_after) from exc

    raise GroqRateLimitError(DEFAULT_RETRY_AFTER_SECONDS)


def get_retry_after_seconds(exc: Exception) -> float | None:
    """Return Groq retry delay when an exception looks like a rate limit."""
    error_text = str(exc)
    if not any(marker in error_text for marker in RATE_LIMIT_MARKERS):
        return None

    match = re.search(r"try again in ([0-9.]+)s", error_text, re.IGNORECASE)
    if match:
        return max(1.0, float(match.group(1)) + 1.0)

    return DEFAULT_RETRY_AFTER_SECONDS
