"""The agent tool-calling loop: the heart that turns this from a chatbot into an agent."""
import json
import traceback

from sqlalchemy.orm import Session

from bot.agent import llm
from bot.agent.memory import append_messages, load_messages
from bot.config import get_settings
from bot.tools.registry import TOOL_SCHEMAS, dispatch

_GENERIC_ERROR = "Lo siento, ocurrió un problema al procesar tu mensaje. Inténtalo de nuevo."


def _run_tool(name: str, arguments, db: Session, session_id: str) -> dict:
    """Execute one tool call, converting any failure into a structured error."""
    try:
        return dispatch(name, arguments, db, session_id)
    except Exception as exc:  # keep the loop alive; surface the error to the model
        db.rollback()
        return {"error": f"Falló la herramienta '{name}': {exc}"}


def run_agent(db: Session, session_id: str, user_message: str) -> str:
    """Drive a full agent turn: reason, call tools as needed, return the final reply.
    The complete conversation (including assistant tool_calls and tool results) is
    loaded from and persisted back to Postgres so memory survives restarts.

    Any unexpected failure is contained: a generic reply is returned and only a
    consistent message history is persisted, so the session is never left in a
    state that would break subsequent turns.
    """
    settings = get_settings()
    history = load_messages(db, session_id)

    user_msg = {"role": "user", "content": user_message}
    history.append(user_msg)
    new_messages = [user_msg]

    final_reply = "Lo siento, no pude completar la solicitud."
    try:
        for _ in range(settings.max_agent_iters):
            assistant = llm.chat(history, tools=TOOL_SCHEMAS)
            history.append(assistant)
            new_messages.append(assistant)

            tool_calls = assistant.get("tool_calls")
            if not tool_calls:
                final_reply = assistant.get("content") or final_reply
                break

            for call in tool_calls:
                fn = call["function"]
                result = _run_tool(fn["name"], fn["arguments"], db, session_id)
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": fn["name"],
                    "content": json.dumps(result, ensure_ascii=False),
                }
                history.append(tool_msg)
                new_messages.append(tool_msg)
    except Exception:  # never let one turn crash the request
        db.rollback()
        traceback.print_exc()
        final_reply = _GENERIC_ERROR
        new_messages = _consistent_prefix(new_messages)

    try:
        append_messages(db, session_id, new_messages)
    except Exception:  # persistence failure must not break the reply
        db.rollback()
        traceback.print_exc()

    return final_reply


def _consistent_prefix(messages: list[dict]) -> list[dict]:
    """Drop a trailing assistant tool_calls turn that has no matching tool replies.

    The API requires every assistant ``tool_calls`` message to be followed by a
    ``tool`` reply for each id; persisting a dangling one would poison the session.
    """
    while messages and messages[-1].get("role") == "assistant" and messages[-1].get("tool_calls"):
        messages = messages[:-1]
    return messages
