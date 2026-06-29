"""Centralized settings, loaded from environment / .env via pydantic-settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from bot.prompts import SYSTEM_PROMPT as DEFAULT_SYSTEM_PROMPT
import os


class Settings(BaseSettings):
    """All runtime configuration. Values come from the environment or a local .env file."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (Groq, OpenAI-compatible)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    max_agent_iters: int = 5

    # Database local
    # database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"

    # Database for render.com
    # Obtener la URL inyectada por Render de manera dinámica
    raw_db_url = os.getenv("DATABASE_URL")

    if raw_db_url:
        # 1. Render usa postgres:// pero SQLAlchemy requiere postgresql://
        if raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

        # 2. Forzar explícitamente el driver moderno psycopg (Psycopg 3) si no está especificado
        if "postgresql://" in raw_db_url and "+psycopg" not in raw_db_url:
            raw_db_url = raw_db_url.replace(
                "postgresql://", "postgresql+psycopg://", 1)

        database_url = raw_db_url
    else:
        # Respaldo local si no hay variable de entorno
        database_url = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"

    # Streamlit client -> API base URL
    # api_url: str = "http://127.0.0.1:8000"

    # API for render.com
    api_url: str = os.getenv("API_URL", "http://127.0.0.1:8000")


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env is parsed once per process."""
    return Settings()
