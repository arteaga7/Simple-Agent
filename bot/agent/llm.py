"""Thin wrapper around the LLM for tool-calling chat completions.

We talk to Google Gemini through its OpenAI-compatible endpoint, so the standard
OpenAI ``chat.completions`` interface (with ``tools`` / ``tool_choice``) works
unchanged — the agent loop and tool schemas don't need to know the provider.
"""
import time
from functools import lru_cache

from openai import APIConnectionError, InternalServerError, OpenAI

from bot.config import get_settings

_MAX_RETRIES = 2  # retry only on transient connection / 5xx errors


@lru_cache
def _client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.gemini_api_key, base_url=settings.gemini_base_url)


def _normalize(message) -> dict:
    """Convert an OpenAI/Gemini message object into a plain history dict."""
    out: dict = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        out["tool_calls"] = [
            {
                "id": c.id,
                "type": "function",
                "function": {"name": c.function.name, "arguments": c.function.arguments},
            }
            for c in message.tool_calls
        ]
        # Tool-call turns carry no user-visible text; keep content null per the API.
        out["content"] = message.content or None
    return out


def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Send a chat completion and return a normalized assistant message dict.

    The returned dict is in OpenAI history format and may carry ``tool_calls`` for
    the agent loop to execute. Transient failures (network, 5xx) are retried; other
    errors propagate to the loop, which degrades gracefully instead of 500-ing.
    """
    settings = get_settings()
    kwargs: dict = {"model": settings.gemini_model, "messages": messages, "temperature": 0.1}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = _client().chat.completions.create(**kwargs)
            return _normalize(response.choices[0].message)
        except (APIConnectionError, InternalServerError) as exc:
            last_exc = exc
            time.sleep(0.5 * (attempt + 1))  # brief backoff, then retry
    raise last_exc  # type: ignore[misc]
