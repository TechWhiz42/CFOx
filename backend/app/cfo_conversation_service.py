from datetime import datetime

from sqlalchemy.orm import Session

from app.analytics import (
    calculate_anomaly_score,
    compare_periods,
    compare_payment_methods as analytics_compare_payment_methods,
)
from app.chat_service import route_question, generate_cfo_answer
from app.cfo_reasoning import build_reasoning_question
from app.models import ChatMessage, Conversation
from app.tools import (
    get_cashflow_analysis,
    get_failed_transactions,
    get_revenue_analysis,
)


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


def build_tool_result(
    db: Session,
    question: str,
    user_id: int,
) -> tuple[str, dict | None]:
    """Execute CFO tools against only the authenticated user's transactions."""
    tool_name = route_question(question)

    if tool_name == "compare_payment_methods":
        return (
            tool_name,
            analytics_compare_payment_methods(
                db,
                user_id=user_id,
            ),
        )

    if tool_name == "get_revenue_analysis":
        return (
            tool_name,
            get_revenue_analysis(
                db,
                user_id=user_id,
            ),
        )

    if tool_name == "get_cashflow_analysis":
        return (
            tool_name,
            get_cashflow_analysis(
                db,
                user_id=user_id,
            ),
        )

    if tool_name == "get_failed_transactions":
        return (
            tool_name,
            get_failed_transactions(
                db,
                hours=24,
                user_id=user_id,
            ),
        )

    if tool_name == "get_anomaly_analysis":
        # Preserve the existing CFO chat behavior:
        # anomaly questions currently analyze UPI.
        comparison = compare_periods(
            db,
            "upi",
            user_id=user_id,
        )
        anomaly = calculate_anomaly_score(
            comparison,
        )

        return (
            tool_name,
            {
                "payment_method": "upi",
                "comparison": comparison,
                "anomaly": anomaly,
            },
        )

    return tool_name, None


def build_history_context(
    messages: list[ChatMessage],
) -> str:
    """Build a compact conversation context for the CFO model."""
    if not messages:
        return ""

    lines = []

    for message in messages[-20:]:
        role = "User" if message.role == "user" else "CFOx"
        lines.append(
            f"{role}: {message.content}"
        )

    return "\n".join(lines)


def generate_stateful_cfo_answer(
    db: Session,
    question: str,
    history: list[ChatMessage],
    user_id: int,
) -> tuple[str, str]:
    """Generate an answer using verified, user-scoped financial data."""
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