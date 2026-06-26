"""ASGI entrypoint. Run with: uvicorn main:app --reload"""
from bot.app_factory import create_app

app = create_app()
