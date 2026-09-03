from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.analytics import (
    compare_payment_methods as analytics_compare_payment_methods,
)
from app.cashflow import calculate_cashflow_risk
from app.forecasting import forecast_revenue
from app.models import Transaction


PAYMENT_METHODS = (
    "upi",
    "card",
    "netbanking",
)


def compare_payment_methods(db: Session, user_id: int | None = None) -> dict:
    """
    Compare all supported payment methods.

    Uses the optimized single-query analytics implementation.
    """
    return analytics_compare_payment_methods(db, user_id=user_id)


def get_revenue_analysis(db: Session, user_id: int | None = None) -> dict:
    """
    Return payment-method performance and revenue forecast.

    Payment-method comparison and forecasting are each calculated
    once and then returned together.
    """

    payment_methods = analytics_compare_payment_methods(db, user_id=user_id)

    forecast = forecast_revenue(
        db,
        history_days=30,
        forecast_days=7,
        user_id=user_id,
    )

    return {
        "payment_methods": payment_methods,
        "forecast": forecast,
    }


def get_cashflow_analysis(db: Session, user_id: int | None = None) -> dict:
    """
    Return cash-flow risk for every supported payment method.

    Reuses the already-aggregated payment-method comparisons and
    calculates the forecast only once.
    """

    payment_methods = analytics_compare_payment_methods(db, user_id=user_id)

    forecast = forecast_revenue(
        db,
        history_days=30,
        forecast_days=7,
        user_id=user_id,
    )

    results = {}

    for method in PAYMENT_METHODS:
        comparison = payment_methods[method]

        results[method] = calculate_cashflow_risk(
            db,
            method,
            comparison=comparison,
            forecast=forecast,
            user_id=user_id,
        )

    return results


def get_failed_transactions(
    db: Session,
    hours: int = 24,
    payment_method: str | None = None,
    user_id: int | None = None,
) -> dict:
    """
    Return recent failed transactions.

    Results are limited to the latest 100 transactions.
    """

    hours = max(1, min(hours, 168))

    start_time = datetime.utcnow() - timedelta(hours=hours)

    query = db.query(Transaction).filter(
        Transaction.status == "failed",
        Transaction.created_at >= start_time,
    )

    if payment_method:
        query = query.filter(
            Transaction.payment_method == payment_method
        )

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    transactions = (
        query
        .order_by(Transaction.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "hours": hours,
        "payment_method": payment_method or "all",
        "count": len(transactions),
        "transactions": [
            {
                "id": transaction.id,
                "payment_id": transaction.razorpay_payment_id,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "payment_method": transaction.payment_method,
                "customer_id": transaction.customer_id,
                "status": transaction.status,
                "created_at": (
                    transaction.created_at.isoformat()
                    if transaction.created_at
                    else None
                ),
            }
            for transaction in transactions
        ],
    }