import json
from datetime import datetime, timedelta

from app.config import settings
from app.webhook_service import process_razorpay_event, verify_razorpay_signature

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import Transaction, User
from app.analytics import (
    calculate_anomaly_score,
    compare_periods,
    compare_payment_methods as analytics_compare_payment_methods,
    calculate_advanced_kpis,
    get_daily_performance,
    get_customer_concentration,
)
from app.alerts import generate_financial_alerts
from app.cashflow import calculate_cashflow_risk
from app.chat_service import (
    route_question,
    stream_cfo_answer,
)
from app.forecasting import (
    get_daily_revenue,
    forecast_revenue,
)
from app.ai_service import generate_financial_insight
from app.tools import (
    get_revenue_analysis,
    get_cashflow_analysis,
    get_failed_transactions,
)
from app.services.analytics_service import (
    get_dashboard_analysis,
    get_alert_analysis,
    get_ai_insight_data,
    get_anomaly_analysis,
)
from app.services.revenue_service import get_revenue_history
from app.schemas import (
    TransactionCreate,
    TransactionResponse,
    AIInvestigationRequest,
    AIInvestigationResponse,
)

from app.ai_investigation import investigate_financial_question

from app.cfo_conversation_service import (
    generate_stateful_cfo_answer,
    get_conversation_history,
    get_owned_conversation,
    persist_cfo_exchange,
)


from app.models import Conversation
from app.schemas import (
    CFOConversationMessageRequest,
    CFOConversationMessageResponse,
)


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    dependencies=[Depends(get_current_user)],
)


# =========================================================
# REQUEST / VALIDATION HELPERS
# =========================================================

SUPPORTED_PAYMENT_METHODS = {
    "upi",
    "card",
    "netbanking",
}


def normalize_payment_method(
    payment_method: str | None,
) -> str | None:
    """
    Normalize the API payment-method selector.

    None and "all" both mean no payment-method filter.

    Supported concrete methods:
        - upi
        - card
        - netbanking

    Raises:
        HTTPException(400) for unsupported methods.
    """

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
    """
    Convert the internal representation back into
    the public API representation.
    """

    return payment_method or "all"


class CFOQuestion(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


# =========================================================
# TRANSACTION INGESTION
# =========================================================

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
    """Create a transaction owned by the authenticated user.

    The request cannot supply user_id; ownership is derived exclusively
    from the verified JWT. Razorpay payment IDs are globally unique and
    therefore protect against accidental duplicate ingestion.
    """

    db_transaction = Transaction(
        razorpay_payment_id=transaction.razorpay_payment_id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        payment_method=transaction.payment_method,
        customer_id=transaction.customer_id,
        created_at=transaction.created_at,
        user_id=current_user.id,
    )

    db.add(db_transaction)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # The unique payment ID is the intended duplicate guard. Avoid
        # exposing raw database errors to API clients.
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
    """List only the authenticated user's transactions."""

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be non-negative")

    return (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


# =========================================================
# DAILY REVENUE
# =========================================================

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


# =========================================================
# REVENUE FORECAST
# =========================================================

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


# =========================================================
# CASH-FLOW RISK
# =========================================================

@router.get("/analytics/cashflow-risk")
def cashflow_risk(
    payment_method: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(
        payment_method
    )

    return calculate_cashflow_risk(
        db,
        normalized_method,
        user_id=current_user.id,
    )


# =========================================================
# AI FINANCIAL INSIGHT
# =========================================================

@router.get("/analytics/ai-insight")
def ai_insight(
    payment_method: str = "upi",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(
        payment_method
    )

    financial_data = get_ai_insight_data(
        db,
        payment_method=normalized_method,
        user_id=current_user.id,
    )

    return generate_financial_insight(
        financial_data,
    )

# =========================================================
# PAYMENT METHOD ANALYTICS
# =========================================================

@router.get("/analytics/payment-methods")
def payment_method_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analytics_compare_payment_methods(
        db,
        user_id=current_user.id,
    )


# =========================================================
# DETERMINISTIC ANOMALY ANALYSIS
# =========================================================

@router.get("/analytics/anomaly")
def anomaly_analysis(
    payment_method: str = "upi",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(
        payment_method
    )

    return get_anomaly_analysis(
        db,
        payment_method=normalized_method,
        user_id=current_user.id,
    )
# =========================================================
# UNIFIED DASHBOARD
# =========================================================

@router.get("/dashboard")
def dashboard(
    payment_method: str = "upi",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(
        payment_method
    )

    return get_dashboard_analysis(
        db,
        payment_method=normalized_method,
        user_id=current_user.id,
    )


# =========================================================
# AI CFO CHAT
# =========================================================

@router.post("/cfo/chat")
def cfo_chat(
    request: CFOQuestion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # -----------------------------------------------------
    # 1. FAST LOCAL ROUTING
    # -----------------------------------------------------

    tool_name = route_question(
        question,
    )

    # -----------------------------------------------------
    # 2. RUN ONLY THE REQUIRED ANALYTICS
    # -----------------------------------------------------

    tool_result = None

    if tool_name == "compare_payment_methods":
        tool_result = (
            analytics_compare_payment_methods(
                db,
                user_id=current_user.id,
            )
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
        # Preserve the existing chat behavior:
        # anomaly questions currently analyze UPI.

        comparison = compare_periods(
            db,
            "upi",
            user_id=current_user.id,
        )

        anomaly = calculate_anomaly_score(
            comparison,
        )

        tool_result = {
            "payment_method": "upi",
            "comparison": comparison,
            "anomaly": anomaly,
        }

    # -----------------------------------------------------
    # 3. STREAM RESPONSE
    # -----------------------------------------------------

    def generate():
        yield json.dumps(
            {
                "type": "metadata",
                "tool_used": tool_name,
            }
        ) + "\n"

        for token in stream_cfo_answer(
            question,
            tool_result,
        ):
            yield json.dumps(
                {
                    "type": "token",
                    "content": token,
                }
            ) + "\n"

        yield json.dumps(
            {
                "type": "done",
            }
        ) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )


# =========================================================
# FINANCIAL ALERTS
# =========================================================

@router.get("/alerts")
def financial_alerts(
    payment_method: str = "upi",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_method = normalize_payment_method(
        payment_method
    )

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
        "payment_method": display_payment_method(
            normalized_method
        ),
        **alert_data,
    }


# =========================================================
# REVENUE HISTORY
# =========================================================

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

    normalized_method = normalize_payment_method(
        payment_method
    )

    return get_revenue_history(
        db,
        days=days,
        payment_method=normalized_method,
        user_id=current_user.id,
    )

# =========================================================
# PHASE 9 — ADVANCED FINANCIAL ANALYTICS
# =========================================================

@router.get("/analytics/advanced-kpis")
def advanced_kpis(
    days: int = 30,
    payment_method: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return calculate_advanced_kpis(
        db, start_date, end_date, normalize_payment_method(payment_method), current_user.id
    )


@router.get("/analytics/daily-performance")
def daily_performance(
    days: int = 30,
    payment_method: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")

    return {
        "days": days,
        "payment_method": display_payment_method(normalize_payment_method(payment_method)),
        "data": get_daily_performance(db, days, payment_method, current_user.id),
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
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")
    if top_n < 1 or top_n > 100:
        raise HTTPException(status_code=400, detail="top_n must be between 1 and 100")

    return get_customer_concentration(
        db, days, top_n, payment_method, current_user.id
    )


# =========================================================
# RAZORPAY WEBHOOK
# =========================================================

webhook_router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@webhook_router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Receive Razorpay payment events without JWT authentication.

    Authentication is replaced here by Razorpay HMAC-SHA256 signature
    verification over the exact raw request body.
    """
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Razorpay webhook secret is not configured.",
        )

    if settings.RAZORPAY_WEBHOOK_USER_ID < 1:
        raise HTTPException(
            status_code=503,
            detail="Razorpay webhook owner is not configured.",
        )

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    event_id = request.headers.get("x-razorpay-event-id", "")

    if not event_id:
        raise HTTPException(
            status_code=400,
            detail="Missing x-razorpay-event-id header.",
        )

    if not verify_razorpay_signature(
        body,
        signature,
        settings.RAZORPAY_WEBHOOK_SECRET,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature.",
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Webhook body must contain valid JSON.",
        ) from exc

    event_name = payload.get("event")
    if not isinstance(event_name, str) or not event_name:
        raise HTTPException(
            status_code=400,
            detail="Webhook event is missing.",
        )

    result = process_razorpay_event(
        db,
        event_id=event_id,
        event_name=event_name,
        payload=payload,
        owner_user_id=settings.RAZORPAY_WEBHOOK_USER_ID,
    )

    return {"status": "ok", "result": result}

@router.post(
    "/ai/investigate",
    response_model=AIInvestigationResponse,
)
def ai_investigate(
    request: AIInvestigationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    return investigate_financial_question(
        db,
        question=question,
        user_id=current_user.id,
        days=request.days,
    )


@router.post(
    "/cfo/conversations/{conversation_id}/messages",
    response_model=CFOConversationMessageResponse,
)
def send_cfo_conversation_message(
    conversation_id: int,
    request: CFOConversationMessageRequest,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    question = request.content.strip()

    history = get_conversation_history(
        db,
        conversation_id,
    )

    try:
        tool_name, answer = generate_stateful_cfo_answer(
            db,
            question,
            history,
        )

        user_message, assistant_message = persist_cfo_exchange(
            db,
            conversation,
            question,
            answer,
        )
    except Exception:
        db.rollback()
        raise

    return {
        "conversation_id": conversation.id,
        "tool_used": tool_name,
        "user_message": user_message,
        "assistant_message": assistant_message,
    }