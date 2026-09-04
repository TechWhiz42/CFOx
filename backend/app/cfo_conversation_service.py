from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.analytics import (
    calculate_anomaly_score,
    compare_periods,
    compare_payment_methods as analytics_compare_payment_methods,
)
from app.cfo_reasoning import (
    build_reasoning_question,
    serialize_reasoning_context,
)
from app.chat_service import route_question, generate_cfo_answer
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
    limit = max(1, min(limit, 100))

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.conversation_id == conversation_id
        )
        .order_by(
            ChatMessage.created_at.desc(),
            ChatMessage.id.desc(),
        )
        .limit(limit)
        .all()
    )

    return list(reversed(messages))


def _add_cross_metric_evidence(
        db: Session,
        user_id: int,
        result: dict,
) -> dict:
    """
    Add deterministic cross-metric evidence without changing the primary
    tool's identity.

    This is intentionally limited to analytics functions whose user-scoped
    interfaces already exist in CFOx.
    """
    if not isinstance(result, dict):
        return result

    try:
        comparison = compare_periods(
            db,
            None,
            user_id=user_id,
        )
        result["comparison"] = comparison
        result["anomaly"] = calculate_anomaly_score(comparison)
    except TypeError:
        # Compatibility with an older analytics signature. The primary tool
        # result is still valid, so do not make reasoning enrichment fatal.
        pass

    try:
        result["cashflow"] = get_cashflow_analysis(
            db,
            user_id=user_id,
        )
    except (TypeError, KeyError):
        pass

    return result


def build_tool_result(
        db: Session,
        question: str,
        user_id: int,
) -> tuple[str, dict | None]:
    """Execute deterministic CFO tools against the authenticated user's data."""

    tool_name = route_question(question)

    if tool_name == "compare_payment_methods":
        return (
            tool_name,
            {
                "payment_methods": analytics_compare_payment_methods(
                    db,
                    user_id=user_id,
                )
            },
        )

    if tool_name == "get_revenue_analysis":
        result = get_revenue_analysis(
            db,
            user_id=user_id,
        )
        return (
            tool_name,
            _add_cross_metric_evidence(
                db,
                user_id,
                result,
            ),
        )

    if tool_name == "get_cashflow_analysis":
        result = get_cashflow_analysis(
            db,
            user_id=user_id,
        )
        return (
            tool_name,
            _add_cross_metric_evidence(
                db,
                user_id,
                result,
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
        comparison = compare_periods(
            db,
            "upi",
            user_id=user_id,
        )
        return (
            tool_name,
            {
                "payment_method": "upi",
                "comparison": comparison,
                "anomaly": calculate_anomaly_score(comparison),
            },
        )

    return tool_name, None


def build_history_context(
        messages: list[ChatMessage],
) -> str:
    """Compatibility helper for callers that need readable history."""

    if not messages:
        return ""

    return "\n".join(
        (
            "User" if message.role == "user" else "CFOx"
        )
        + f": {message.content}"
        for message in messages[-20:]
    )


def _build_contextual_question(
        question: str,
        history: list[ChatMessage],
        tool_name: str,
        tool_result,
) -> str:
    reasoning_question = build_reasoning_question(
        question,
        history,
    )

    reasoning_context = serialize_reasoning_context(
        tool_name,
        tool_result,
    )

    return (
        f"{reasoning_question}\n\n"
        "Verified reasoning evidence:\n"
        f"{reasoning_context}"
    )


def generate_stateful_cfo_answer(
        db: Session,
        question: str,
        history: list[ChatMessage],
        user_id: int,
) -> tuple[str, str]:
    """Generate a context-aware answer using verified user-scoped data."""

    reasoning_question = build_reasoning_question(
        question,
        history,
    )

    tool_name, tool_result = build_tool_result(
        db,
        reasoning_question,
        user_id,
    )

    contextual_question = _build_contextual_question(
        question,
        history,
        tool_name,
        tool_result,
    )

    answer = generate_cfo_answer(
        contextual_question,
        tool_result,
    )

    return tool_name, answer


def prepare_cfo_exchange(
        db: Session,
        conversation_id: int,
        question: str,
        user_id: int,
):
    """
    Prepare a persistent streaming exchange.

    Nothing is persisted here; persistence happens only after successful
    streaming so an interrupted generation does not create a fake assistant
    message.
    """
    conversation = get_owned_conversation(
        db,
        conversation_id,
        user_id,
    )

    if conversation is None:
        raise ValueError("Conversation not found.")

    history = get_conversation_history(
        db,
        conversation_id,
    )

    reasoning_question = build_reasoning_question(
        question,
        history,
    )

    tool_name, tool_result = build_tool_result(
        db,
        reasoning_question,
        user_id,
    )

    contextual_question = _build_contextual_question(
        question,
        history,
        tool_name,
        tool_result,
    )

    return (
        conversation,
        contextual_question,
        tool_name,
        tool_result,
    )


def persist_cfo_exchange(
        db: Session,
        conversation: Conversation,
        question: str,
        answer: str,
) -> tuple[ChatMessage, ChatMessage]:
    now = datetime.now(timezone.utc)

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

    conversation.updated_at = now

    db.add(user_message)
    db.add(assistant_message)
    db.add(conversation)

    db.commit()

    db.refresh(user_message)
    db.refresh(assistant_message)
    db.refresh(conversation)

    return user_message, assistant_message
