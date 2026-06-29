"""Centralized settings, loaded from environment / .env via pydantic-settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from bot.prompts import SYSTEM_PROMPT as DEFAULT_SYSTEM_PROMPT


class Settings(BaseSettings):
    """All runtime configuration. Values come from the environment or a local .env file."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (Groq, OpenAI-compatible)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    max_agent_iters: int = 5

    # Database
    # database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"

    # Database render.com
    database_url: str = "postgresql://chatbot:jlVPBXLMKOekTgXpHCbkZB5iCD1ml6CD@dpg-d90ub4e8bjmc739hjm00-a.oregon-postgres.render.com/chatbot_jmfh"

    # Streamlit client -> API base URL
    api_url: str = "http://127.0.0.1:8000"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env is parsed once per process."""
    return Settings()
