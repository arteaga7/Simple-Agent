"""Conversation persistence: load/append messages from the Postgres `messages` table."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from bot.config import get_settings
from bot.db.models import Message


def load_messages(db: Session, session_id: str) -> list[dict]:
    """Return the full message history for a session in OpenAI/Groq format.
    On a brand-new session, returns just the system prompt (not yet persisted —
    it gets stored on the first `append_messages` call).
    """
    rows = db.scalars(
        select(Message).where(Message.session_id ==
                              session_id).order_by(Message.seq)
    ).all()
    if rows:
        return [row.payload for row in rows]
    return [{"role": "system", "content": get_settings().system_prompt}]


def append_messages(db: Session, session_id: str, messages: list[dict]) -> None:
    """Persist new messages, continuing the per-session sequence counter."""
    last_seq = db.scalar(
        select(func.max(Message.seq)).where(Message.session_id == session_id)
    )
    seq = (last_seq or 0) + 1
    for msg in messages:
        db.add(
            Message(
                session_id=session_id,
                seq=seq,
                role=str(msg.get("role", "")),
                payload=msg,
            )
        )
        seq += 1
    db.commit()
