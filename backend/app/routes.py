import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai_investigation import investigate_financial_question
from app.ai_service import generate_financial_insight
from app.alerts import generate_financial_alerts
from app.analytics import (
    calculate_advanced_kpis,
    calculate_anomaly_score,
    compare_payment_methods as analytics_compare_payment_methods,
    compare_periods,
    get_customer_concentration,
    get_daily_performance,
)
from app.audit import audit_event
from app.auth import get_current_user
from app.cashflow import calculate_cashflow_risk
from app.cfo_conversation_service import (
    get_conversation_history,
    get_owned_conversation,
    persist_cfo_exchange,
    prepare_cfo_exchange,
)
from app.chat_service import (
    route_question,
    stream_cfo_answer,
)
from app.config import settings
from app.database import get_db
from app.financial_actions import generate_financial_actions
from app.financial_health import calculate_financial_health
from app.forecasting import (
    forecast_revenue,
    get_daily_revenue,
)
from app.models import ChatMessage, Conversation
from app.models import Transaction, User
from app.production_hardening import (
    ai_limiter,
    enforce_rate_limit,
    request_rate_limit_key,
    user_rate_limit_key,
    webhook_limiter,
)
from app.reliability import CFOAIServiceError, public_ai_error_detail
from app.schemas import (
    CFOConversationResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services.analytics_service import (
    get_ai_insight_data,
    get_alert_analysis,
    get_anomaly_analysis,
    get_dashboard_analysis,
)
from app.services.revenue_service import get_revenue_history
from app.tools import (
    get_cashflow_analysis,
    get_failed_transactions,
    get_revenue_analysis,
)
from app.webhook_service import process_razorpay_event, verify_razorpay_signature
import logging

logger = logging.getLogger("cfox.routes")

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    dependencies=[Depends(get_current_user)],
)

SUPPORTED_PAYMENT_METHODS = {
    "upi",
    "card",
    "netbanking",
}


def normalize_payment_method(
        payment_method: str | None,
) -> str | None:
    if payment_method is None:
        return None

    normalized = payment_method.strip().lower()

    if normalized == "all":
        return None

    if normalized not in SUPPORTED_PAYMENT_METHODS:
        raise HTTPException(
            status_code=400,
            detail=(
                "payment_method must be one of: "
                "all, upi, card, netbanking"
            ),
        )

    return normalized


def display_payment_method(
        payment_method: str | None,
) -> str:
    return payment_method or "all"


def format_payment_method_analytics(
        analytics: dict,
) -> dict:
    payment_methods = []

    for payment_method in sorted(analytics):
        method_data = analytics[payment_method]
        changes = method_data.get("changes", {})

        payment_methods.append(
            {
                "payment_method": payment_method,
                "current_period": method_data.get("current_period", {}),
                "previous_period": method_data.get("previous_period", {}),
                "failure_rate_change": changes.get(
                    "failure_rate_change_percentage_points",
                    0.0,
                ),
                "failure_rate_multiplier": changes.get(
                    "failure_rate_multiplier",
                ),
                "revenue_change": changes.get("revenue_change", 0.0),
            }
        )

    worst_method = None

    if payment_methods:
        worst_method = max(
            payment_methods,
            key=lambda method: (
                method.get("current_period", {}).get("failure_rate", 0.0),
                method.get("failure_rate_change", 0.0),
            ),
        )["payment_method"]

    return {
        "payment_methods": payment_methods,
        "worst_performing_method": worst_method,
        "by_method": analytics,
    }


class CFOQuestion(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
        transaction: TransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    transaction_data = transaction.model_dump(
        exclude_none=True
    )

    db_transaction = Transaction(
        **transaction_data,
        user_id=current_user.id,
    )

    db.add(db_transaction)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        if "razorpay_payment_id" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A transaction with this razorpay_payment_id already exists.",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction could not be created because it conflicts with existing data.",
        ) from exc

    db.refresh(db_transaction)

    audit_event(
        "transaction.created",
        user_id=current_user.id,
        metadata={
            "transaction_id": db_transaction.id,
            "status": db_transaction.status,
            "payment_method": db_transaction.payment_method,
        },
    )

    return db_transaction


@router.get(
    "",
    response_model=list[TransactionResponse],
)
def list_transactions(
        limit: int = 50,
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100",
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="offset must be non-negative",
        )

    return (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/analytics/daily-revenue")
def daily_revenue(
        days: int = 30,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 365",
        )

    return {
        "days": days,
        "data": get_daily_revenue(
            db,
            days,
            user_id=current_user.id,
        ),
    }


@router.get("/analytics/revenue-forecast")
def revenue_forecast(
        history_days: int = 30,
        forecast_days: int = 7,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if history_days < 3:
        raise HTTPException(
            status_code=400,
            detail="history_days must be at least 3",
        )

    if forecast_days < 1 or forecast_days > 30:
        raise HTTPException(
            status_code=400,
            detail="forecast_days must be between 1 and 30",
        )

    return forecast_revenue(
        db,
        history_days,
        forecast_days,
        user_id=current_user.id,
    )


@router.get("/analytics/cashflow-risk")
def cashflow_risk(
        payment_method: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(payment_method)

    return calculate_cashflow_risk(
        db,
        normalized_method,
        user_id=current_user.id,
    )


@router.get("/analytics/ai-insight")
def ai_insight(
        payment_method: str = "upi",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(payment_method)

    financial_data = get_ai_insight_data(
        db,
        payment_method=normalized_method,
        user_id=current_user.id,
    )

    return generate_financial_insight(financial_data)


@router.get("/analytics/payment-methods")
def payment_method_analytics(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    analytics = analytics_compare_payment_methods(
        db,
        user_id=current_user.id,
    )

    return format_payment_method_analytics(analytics)


@router.get("/analytics/anomaly")
def anomaly_analysis(
        payment_method: str = "upi",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(payment_method)

    return get_anomaly_analysis(
        db,
        payment_method=normalized_method,
        user_id=current_user.id,
    )


@router.get("/dashboard")
def dashboard(
        payment_method: str = "upi",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(payment_method)

    return get_dashboard_analysis(
        db,
        payment_method=normalized_method,
        user_id=current_user.id,
    )


@router.post("/cfo/chat")
def cfo_chat(
        request: CFOQuestion,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    enforce_rate_limit(
        ai_limiter,
        user_rate_limit_key(current_user.id, "ai:cfo_chat"),
    )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    tool_name = route_question(question)
    tool_result = None

    if tool_name == "compare_payment_methods":
        tool_result = analytics_compare_payment_methods(
            db,
            user_id=current_user.id,
        )

    elif tool_name == "get_revenue_analysis":
        tool_result = get_revenue_analysis(
            db,
            user_id=current_user.id,
        )

    elif tool_name == "get_cashflow_analysis":
        tool_result = get_cashflow_analysis(
            db,
            user_id=current_user.id,
        )

    elif tool_name == "get_failed_transactions":
        tool_result = get_failed_transactions(
            db,
            hours=24,
            user_id=current_user.id,
        )

    elif tool_name == "get_anomaly_analysis":
        comparison = compare_periods(
            db,
            "upi",
            user_id=current_user.id,
        )

        anomaly = calculate_anomaly_score(comparison)

        tool_result = {
            "payment_method": "upi",
            "comparison": comparison,
            "anomaly": anomaly,
        }

    def generate():
        try:
            yield json.dumps({
                "type": "metadata",
                "tool_used": tool_name,
            }) + "\n"

            for token in stream_cfo_answer(question, tool_result):
                yield json.dumps({
                    "type": "token",
                    "content": token,
                }) + "\n"

            yield json.dumps({"type": "done"}) + "\n"

        except CFOAIServiceError:
            yield json.dumps({
                "type": "error",
                "detail": public_ai_error_detail(),
            }) + "\n"

        except Exception:
            yield json.dumps({
                "type": "error",
                "detail": "An unexpected error occurred.",
            }) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )


@router.get("/alerts")
def financial_alerts(
        payment_method: str = "upi",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(payment_method)

    alert_analysis = get_alert_analysis(
        db,
        payment_method=normalized_method,
        user_id=current_user.id,
    )

    alert_data = generate_financial_alerts(
        analysis=alert_analysis["analysis"],
        cashflow=alert_analysis["cashflow"],
        anomaly=alert_analysis["anomaly"],
    )

    return {
        "payment_method": display_payment_method(normalized_method),
        **alert_data,
    }


@router.get("/analytics/revenue-history")
def revenue_history(
        days: int = 30,
        payment_method: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if days < 1 or days > 90:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 90",
        )

    normalized_method = normalize_payment_method(payment_method)

    return get_revenue_history(
        db,
        days=days,
        payment_method=normalized_method,
        user_id=current_user.id,
    )


@router.get("/analytics/advanced-kpis")
def advanced_kpis(
        days: int = 30,
        payment_method: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 365",
        )

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return calculate_advanced_kpis(
        db,
        start_date,
        end_date,
        normalize_payment_method(payment_method),
        current_user.id,
    )


@router.get("/analytics/daily-performance")
def daily_performance(
        days: int = 30,
        payment_method: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 365",
        )

    normalized_method = normalize_payment_method(payment_method)

    return {
        "days": days,
        "payment_method": display_payment_method(normalized_method),
        "data": get_daily_performance(
            db,
            days,
            normalized_method,
            current_user.id,
        ),
    }


@router.get("/analytics/customer-concentration")
def customer_concentration(
        days: int = 30,
        top_n: int = 10,
        payment_method: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 365",
        )

    if top_n < 1 or top_n > 100:
        raise HTTPException(
            status_code=400,
            detail="top_n must be between 1 and 100",
        )

    normalized_method = normalize_payment_method(payment_method)

    return get_customer_concentration(
        db,
        days,
        top_n,
        normalized_method,
        current_user.id,
    )


class CFOInvestigationRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    days: int = Field(default=7, ge=1, le=90)


@router.post("/ai/investigate")
def investigate_cfo_question(
        request: CFOInvestigationRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    enforce_rate_limit(
        ai_limiter,
        user_rate_limit_key(current_user.id, "ai:investigate"),
    )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    return investigate_financial_question(
        db,
        question=question,
        user_id=current_user.id,
        days=request.days,
    )


@router.get("/analytics/financial-health")
def financial_health(
        payment_method: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(payment_method)

    comparison = compare_periods(
        db,
        normalized_method,
        current_user.id,
    )

    forecast = forecast_revenue(
        db,
        history_days=30,
        forecast_days=7,
        user_id=current_user.id,
    )

    cashflow = calculate_cashflow_risk(
        db,
        payment_method=normalized_method,
        comparison=comparison,
        forecast=forecast,
        user_id=current_user.id,
    )

    anomaly = calculate_anomaly_score(comparison)

    health = calculate_financial_health(
        comparison=comparison,
        anomaly=anomaly,
        cashflow=cashflow,
        forecast=forecast,
    )

    return {
        "payment_method": display_payment_method(normalized_method),
        "health": health,
        "supporting_data": {
            "comparison": comparison,
            "anomaly": anomaly,
            "cashflow": cashflow,
            "forecast": forecast,
        },
    }


@router.get("/analytics/financial-actions")
def financial_actions(
        payment_method: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(payment_method)

    comparison = compare_periods(
        db,
        normalized_method,
        current_user.id,
    )

    forecast = forecast_revenue(
        db,
        history_days=30,
        forecast_days=7,
        user_id=current_user.id,
    )

    cashflow = calculate_cashflow_risk(
        db,
        payment_method=normalized_method,
        comparison=comparison,
        forecast=forecast,
        user_id=current_user.id,
    )

    anomaly = calculate_anomaly_score(comparison)

    health = calculate_financial_health(
        comparison=comparison,
        anomaly=anomaly,
        cashflow=cashflow,
        forecast=forecast,
    )

    actions = generate_financial_actions(
        health,
        {
            "comparison": comparison,
            "anomaly": anomaly,
            "cashflow": cashflow,
            "forecast": forecast,
        },
    )

    return {
        "payment_method": display_payment_method(normalized_method),
        "health": health,
        "actions": actions,
        "supporting_data": {
            "comparison": comparison,
            "anomaly": anomaly,
            "cashflow": cashflow,
            "forecast": forecast,
        },
    }


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


def _conversation_payload(conversation: Conversation) -> dict:
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


def _conversation_with_messages(
        conversation: Conversation,
        messages: list[ChatMessage],
) -> dict:
    payload = _conversation_payload(conversation)

    payload["messages"] = [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        }
        for message in messages
    ]

    return payload


@router.post(
    "/cfo/conversations",
    response_model=CFOConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cfo_conversation(
        request: ConversationCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    title = request.title.strip() if request.title else None

    conversation = Conversation(
        user_id=current_user.id,
        title=title or "New conversation",
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return _conversation_payload(conversation)


@router.get("/cfo/conversations")
def list_cfo_conversations(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .all()
    )

    return [
        _conversation_payload(conversation)
        for conversation in conversations
    ]


@router.get("/cfo/conversations/{conversation_id}")
def get_cfo_conversation(
        conversation_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    conversation = get_owned_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    messages = get_conversation_history(
        db,
        conversation_id,
        limit=100,
    )

    return _conversation_with_messages(conversation, messages)


@router.delete("/cfo/conversations/{conversation_id}")
def delete_cfo_conversation(
        conversation_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    conversation = get_owned_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    db.delete(conversation)
    db.commit()

    audit_event(
        "conversation.deleted",
        user_id=current_user.id,
        metadata={
            "conversation_id": conversation_id,
        },
    )

    return {
        "status": "deleted",
        "id": conversation_id,
    }


@router.post("/cfo/conversations/{conversation_id}/messages")
def create_cfo_message(
        conversation_id: int,
        request: ConversationMessageRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    enforce_rate_limit(
        ai_limiter,
        user_rate_limit_key(current_user.id, "ai:conversation"),
    )

    question = request.content.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    try:
        conversation, contextual_question, tool_name, tool_result = prepare_cfo_exchange(
            db,
            conversation_id,
            question,
            current_user.id,
        )
    except ValueError as exc:
        if str(exc) == "Conversation not found.":
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            ) from exc

        raise

    try:
        answer = "".join(
            stream_cfo_answer(contextual_question, tool_result)
        )
    except CFOAIServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail=public_ai_error_detail(),
        ) from exc

    user_message, assistant_message = persist_cfo_exchange(
        db,
        conversation,
        question,
        answer,
    )

    return {
        "tool_used": tool_name,
        "user_message": {
            "id": user_message.id,
            "role": user_message.role,
            "content": user_message.content,
            "created_at": user_message.created_at.isoformat(),
        },
        "assistant_message": {
            "id": assistant_message.id,
            "role": assistant_message.role,
            "content": assistant_message.content,
            "created_at": assistant_message.created_at.isoformat(),
        },
    }


@router.post("/cfo/conversations/{conversation_id}/messages/stream")
def stream_cfo_conversation_message(
        conversation_id: int,
        request: ConversationMessageRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    enforce_rate_limit(
        ai_limiter,
        user_rate_limit_key(current_user.id, "ai:conversation_stream"),
    )

    question = request.content.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    try:
        conversation, contextual_question, tool_name, tool_result = prepare_cfo_exchange(
            db,
            conversation_id,
            question,
            current_user.id,
        )
    except ValueError as exc:
        if str(exc) == "Conversation not found.":
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            ) from exc

        raise

    def generate():
        answer_parts: list[str] = []

        try:
            yield json.dumps({
                "type": "metadata",
                "tool_used": tool_name,
            }) + "\n"

            for token in stream_cfo_answer(contextual_question, tool_result):
                answer_parts.append(token)

                yield json.dumps({
                    "type": "token",
                    "content": token,
                }) + "\n"

            answer = "".join(answer_parts)

            user_message, assistant_message = persist_cfo_exchange(
                db,
                conversation,
                question,
                answer,
            )

            yield json.dumps({
                "type": "done",
                "user_message_id": user_message.id,
                "assistant_message_id": assistant_message.id,
            }) + "\n"

        except CFOAIServiceError:
            db.rollback()

            yield json.dumps({
                "type": "error",
                "detail": public_ai_error_detail(),
            }) + "\n"

        except Exception:
            db.rollback()

            yield json.dumps({
                "type": "error",
                "detail": "An unexpected error occurred.",
            }) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )


webhook_router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@webhook_router.post("/razorpay")
@webhook_router.post("/razorpay")
async def razorpay_webhook(
        request: Request,
        db: Session = Depends(get_db),
):
    enforce_rate_limit(
        webhook_limiter,
        request_rate_limit_key(request, "webhook:razorpay"),
    )

    if not settings.RAZORPAY_WEBHOOK_SECRET:
        logger.warning(
            "webhook_razorpay_secret_not_configured"
        )

        raise HTTPException(
            status_code=503,
            detail="Razorpay webhook secret is not configured.",
        )

    if settings.RAZORPAY_WEBHOOK_USER_ID < 1:
        logger.warning(
            "webhook_razorpay_owner_not_configured"
        )

        raise HTTPException(
            status_code=503,
            detail="Razorpay webhook owner is not configured.",
        )

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    event_id = request.headers.get("x-razorpay-event-id", "")

    if not event_id:
        logger.warning(
            "webhook_razorpay_missing_event_id"
        )

        raise HTTPException(
            status_code=400,
            detail="Missing x-razorpay-event-id header.",
        )

    if len(event_id) > 255:
        logger.warning(
            "webhook_razorpay_event_id_too_long"
        )

        raise HTTPException(
            status_code=400,
            detail="x-razorpay-event-id is too long.",
        )

    if not verify_razorpay_signature(
            body,
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET,
    ):
        logger.warning(
            "webhook_razorpay_invalid_signature event_id=%s",
            event_id,
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature.",
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        logger.warning(
            "webhook_razorpay_invalid_json event_id=%s",
            event_id,
        )

        raise HTTPException(
            status_code=400,
            detail="Webhook body must contain valid JSON.",
        ) from exc

    if not isinstance(payload, dict):
        logger.warning(
            "webhook_razorpay_non_object_body event_id=%s",
            event_id,
        )

        raise HTTPException(
            status_code=400,
            detail="Webhook body must contain a JSON object.",
        )

    event_name = payload.get("event")

    if not isinstance(event_name, str) or not event_name:
        logger.warning(
            "webhook_razorpay_missing_event_name event_id=%s",
            event_id,
        )

        raise HTTPException(
            status_code=400,
            detail="Webhook event is missing.",
        )

    try:
        result = process_razorpay_event(
            db,
            event_id=event_id,
            event_name=event_name,
            payload=payload,
            owner_user_id=settings.RAZORPAY_WEBHOOK_USER_ID,
        )
    except ValueError as exc:
        logger.warning(
            "webhook_razorpay_rejected event_id=%s reason=%s",
            event_id,
            str(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    audit_event(
        "webhook.razorpay_processed",
        user_id=settings.RAZORPAY_WEBHOOK_USER_ID,
        request_id=getattr(request.state, "request_id", None),
        metadata={
            "event_id": event_id,
            "event_name": event_name,
            "result": result,
        },
    )

    return {
        "status": "ok",
        "result": result,
    }
