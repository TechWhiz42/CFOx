from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app import ai_service
from app.analytics import (
    calculate_advanced_kpis,
    compare_payment_methods,
    get_customer_concentration,
    get_daily_performance,
)
from app.models import Transaction


INVESTIGATION_TYPES = (
    "revenue",
    "failure",
    "refund",
    "payment_method",
    "customer",
)


def classify_investigation(question: str) -> str:
    """Classify a CFO question into a supported investigation type."""
    text = question.lower().strip()

    if any(word in text for word in ("refund", "refunded", "chargeback")):
        return "refund"

    if any(
        word in text
        for word in (
            "fail",
            "failed",
            "failure",
            "declined",
            "decline",
        )
    ):
        return "failure"

    if any(
        word in text
        for word in (
            "customer",
            "customers",
            "client",
            "clients",
        )
    ):
        return "customer"

    if any(
        word in text
        for word in (
            "payment method",
            "payment methods",
            "upi",
            "card",
            "netbanking",
            "net banking",
        )
    ):
        return "payment_method"

    return "revenue"


def _percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _period_bounds(days: int) -> tuple[datetime, datetime]:
    days = max(1, min(days, 90))

    end = datetime.utcnow()
    start = end - timedelta(days=days)

    return start, end


def build_investigation_evidence(
    db: Session,
    question: str,
    user_id: int,
    days: int = 7,
) -> dict:
    """Collect verified, user-scoped database facts for an investigation."""
    investigation_type = classify_investigation(question)
    start, end = _period_bounds(days)

    base = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.created_at >= start,
        Transaction.created_at < end,
    )

    totals = base.with_entities(
        func.count(Transaction.id).label("total"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.status == "success", Transaction.amount),
                    else_=0,
                )
            ),
            0,
        ).label("revenue"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.status == "failed", Transaction.amount),
                    else_=0,
                )
            ),
            0,
        ).label("failed_amount"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.status == "refunded", Transaction.amount),
                    else_=0,
                )
            ),
            0,
        ).label("refunded_amount"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.status == "failed", 1),
                    else_=0,
                )
            ),
            0,
        ).label("failed"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.status == "refunded", 1),
                    else_=0,
                )
            ),
            0,
        ).label("refunded"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.status == "success", 1),
                    else_=0,
                )
            ),
            0,
        ).label("successful"),
    ).one()

    total = int(totals.total or 0)
    successful = int(totals.successful or 0)
    failed = int(totals.failed or 0)
    refunded = int(totals.refunded or 0)

    revenue = float(Decimal(str(totals.revenue or 0)))
    refunded_amount = float(
        Decimal(str(totals.refunded_amount or 0))
    )
    failed_amount = float(
        Decimal(str(totals.failed_amount or 0))
    )

    evidence = {
        "investigation_type": investigation_type,
        "period_days": days,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "total_transactions": total,
        "successful_transactions": successful,
        "failed_transactions": failed,
        "refunded_transactions": refunded,
        "revenue": round(revenue, 2),
        "refunded_amount": round(refunded_amount, 2),
        "failed_amount": round(failed_amount, 2),
        "failure_rate": _percent(failed, total),
        "refund_rate": _percent(refunded, total),
    }

    if investigation_type == "payment_method":
        evidence["payment_methods"] = compare_payment_methods(
            db,
            user_id=user_id,
        )

    if investigation_type == "customer":
        evidence["customer_concentration"] = get_customer_concentration(
            db,
            days,
            10,
            None,
            user_id,
        )

    if investigation_type == "revenue":
        evidence["daily_performance"] = get_daily_performance(
            db,
            min(days, 30),
            None,
            user_id,
        )

    if investigation_type in ("failure", "refund"):
        evidence["advanced_kpis"] = calculate_advanced_kpis(
            db,
            start,
            end,
            None,
            user_id,
        )

    return evidence


def investigate_financial_question(
    db: Session,
    question: str,
    user_id: int,
    days: int = 7,
) -> dict:
    """Investigate a financial question using verified DB evidence."""
    evidence = build_investigation_evidence(
        db,
        question=question,
        user_id=user_id,
        days=days,
    )

    insight = ai_service.generate_financial_insight(evidence)

    return {
        "question": question,
        "investigation_type": evidence["investigation_type"],
        "period_days": evidence["period_days"],
        "evidence_data": evidence,
        "summary": insight["summary"],
        "severity": insight["severity"],
        "evidence": insight.get("evidence", []),
        "impact": insight.get("impact", ""),
        "recommendations": insight.get("recommendations", []),
    }