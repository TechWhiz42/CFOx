from datetime import datetime

from sqlalchemy.orm import Session

from app.chat_service import route_question, generate_cfo_answer
from app.models import ChatMessage, Conversation
from app.tools import (
    get_cashflow_analysis,
    get_failed_transactions,
    get_revenue_analysis,
    compare_payment_methods,
)
from app.cfo_reasoning import build_reasoning_question

def get_owned_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> Conversation | None:
    """Return a conversation only when it belongs to the authenticated user."""
    return (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        .first()
    )


def get_conversation_history(
    db: Session,
    conversation_id: int,
    limit: int = 20,
) -> list[ChatMessage]:
    """Return recent messages in chronological order."""
    limit = max(1, min(limit, 100))

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
        .all()
    )

    return list(reversed(messages))


def build_tool_result(db: Session, question: str):
    """Execute the same deterministic financial tool selection used by CFO chat."""
    tool_name = route_question(question)

    if tool_name == "compare_payment_methods":
        return tool_name, compare_payment_methods(db)

    if tool_name == "get_revenue_analysis":
        return tool_name, get_revenue_analysis(db)

    if tool_name == "get_cashflow_analysis":
        return tool_name, get_cashflow_analysis(db)

    if tool_name == "get_failed_transactions":
        return tool_name, get_failed_transactions(db, hours=24)

    return tool_name, None


def build_history_context(messages: list[ChatMessage]) -> str:
    """Build a compact conversation context for the CFO model."""
    if not messages:
        return ""

    lines = []
    for message in messages[-20:]:
        role = "User" if message.role == "user" else "CFOx"
        lines.append(f"{role}: {message.content}")

    return "\n".join(lines)


def generate_stateful_cfo_answer(
    db: Session,
    question: str,
    history: list[ChatMessage],
) -> tuple[str, str]:
    """Generate an answer using the existing verified-data CFO path.

    History is supplied as conversational context, while the current
    financial tool result remains the source of financial facts.
    """
    tool_name, tool_result = build_tool_result(db, question)

    history_context = build_history_context(history)

    if history_context:
        contextual_question = (
            "Previous conversation:\n"
            f"{history_context}\n\n"
            "Current question:\n"
            f"{question}"
        )
    else:
        contextual_question = question

    answer = generate_cfo_answer(
        contextual_question,
        tool_result,
    )

    return tool_name, answer


def persist_cfo_exchange(
    db: Session,
    conversation: Conversation,
    question: str,
    answer: str,
) -> tuple[ChatMessage, ChatMessage]:
    """Persist the user question and assistant answer atomically."""
    now = datetime.utcnow()

    user_message = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=question,
        created_at=now,
    )

    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        created_at=now,
    )

    db.add(user_message)
    db.add(assistant_message)

    conversation.updated_at = now
    db.add(conversation)

    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)

    return user_message, assistant_message

def generate_stateful_cfo_answer(
    db,
    question,
    history,
    user_id,
):
    reasoning_question = build_reasoning_question(
        question,
        history,
    )

    tool_name, tool_result = build_tool_result(
        db,
        reasoning_question,
        user_id,
    )

    answer = generate_cfo_answer(
        reasoning_question,
        tool_result,
    )

    return tool_name, answer
