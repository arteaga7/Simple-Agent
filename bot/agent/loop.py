"""The agent tool-calling loop: the heart that turns this from a chatbot into an agent."""
import json
from sqlalchemy.orm import Session
from bot.agent import llm
from bot.agent.memory import append_messages, load_messages
from bot.config import get_settings
from bot.tools.registry import TOOL_SCHEMAS, dispatch


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
    """
    settings = get_settings()
    history = load_messages(db, session_id)

    user_msg = {"role": "user", "content": user_message}
    history.append(user_msg)
    new_messages = [user_msg]

    final_reply = "Lo siento, no pude completar la solicitud."
    for _ in range(settings.max_agent_iters):
        assistant = llm.chat(history, tools=TOOL_SCHEMAS)
        assistant_dict = assistant.model_dump(exclude_none=True)
        history.append(assistant_dict)
        new_messages.append(assistant_dict)

        if not assistant.tool_calls:
            final_reply = assistant.content or ""
            break

        for call in assistant.tool_calls:
            result = _run_tool(call.function.name,
                               call.function.arguments, db, session_id)
            tool_msg = {
                "role": "tool",
                "tool_call_id": call.id,
                "name": call.function.name,
                "content": json.dumps(result, ensure_ascii=False),
            }
            history.append(tool_msg)
            new_messages.append(tool_msg)

    append_messages(db, session_id, new_messages)
    return final_reply
