# main.py
"""FastAPI application factory: wires routes and bootstraps the database on startup.
Run with: uvicorn main:app --reload"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from bot.api.routes import router
from bot.db.database import Base, SessionLocal, engine
from bot.db import models
from bot.db.seed import seed_products


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed the catalog before serving requests."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_products(db)
    yield


app = FastAPI(title="Chatbot de Pedidos (Agente)", lifespan=lifespan)
app.include_router(router)
