"""HTTP routes: the chat endpoint and a health check."""
import traceback

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from bot.agent.loop import run_agent
from bot.api.schemas import ChatRequest, ChatResponse
from bot.db.database import get_db

router = APIRouter()

_FALLBACK_REPLY = "Lo siento, ocurrió un problema al procesar tu mensaje. Inténtalo de nuevo."


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Liveness + DB connectivity check."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Run one agent turn for the given session.

    Final safety net: any error becomes a graceful 200 reply (logged to stderr)
    rather than a 500, so the chat UI never breaks on a single bad turn.
    """
    try:
        reply = run_agent(db, request.session_id, request.message)
    except Exception:
        db.rollback()
        traceback.print_exc()
        reply = _FALLBACK_REPLY
    return ChatResponse(reply=reply, session_id=request.session_id)
