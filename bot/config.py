"""Centralized settings, loaded from environment / .env via pydantic-settings."""
from functools import lru_cache
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.prompts import SYSTEM_PROMPT as DEFAULT_SYSTEM_PROMPT


class Settings(BaseSettings):
    """All runtime configuration. Values come from the environment or a local .env file."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (Google Gemini via its OpenAI-compatible endpoint)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    max_agent_iters: int = 5

    # Database — read from the DATABASE_URL env var (Render/Docker set it);
    # falls back to a local Postgres for bare `uvicorn` runs.
    # database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"

    # Database for render.com
    database_url: str = os.getenv("DATABASE_URL")

    # Streamlit client -> API base URL (the UI reads API_URL from the env in app.py).
    api_url: str = "http://localhost:8000"

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, value: str) -> str:
        """Rewrite the legacy ``postgres://`` scheme (which SQLAlchemy 2.x rejects)
        that some providers still hand out to the canonical ``postgresql://``."""
        if value and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env is parsed once per process."""
    return Settings()
