"""Thin wrapper around the Groq client for tool-calling chat completions."""
from functools import lru_cache
from groq import Groq
from bot.config import get_settings


@lru_cache
def _client() -> Groq:
    return Groq(api_key=get_settings().groq_api_key)


def chat(messages: list[dict], tools: list[dict] | None = None):
    """Send a chat completion request and return the assistant message object.
    Tools are passed in Groq/OpenAI function-calling format; the returned message
    may contain ``tool_calls`` for the agent loop to execute.
    """
    settings = get_settings()
    kwargs: dict = {"model": settings.groq_model,
                    "messages": messages, "temperature": 0.1}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    response = _client().chat.completions.create(**kwargs)
    return response.choices[0].message
