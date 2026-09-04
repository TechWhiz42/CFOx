from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Transaction


def get_daily_revenue(
        db: Session,
        days: int = 30,
        user_id: int | None = None,
) -> list[dict]:
    """
    Return daily successful revenue for the requested number of days.

    When user_id is supplied, only that user's transactions are included.
    """

    if days <= 0:
        return []

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = (
        db.query(
            func.date(Transaction.created_at).label("date"),
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            ).label("revenue"),
        )
        .filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == "success",
        )
    )

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    rows = (
        query
        .group_by(func.date(Transaction.created_at))
        .order_by(func.date(Transaction.created_at))
        .all()
    )

    revenue_by_date = {
        row.date: Decimal(str(row.revenue or 0))
        for row in rows
    }

    result = []

    for i in range(days + 1):
        current_date = (
                start_date + timedelta(days=i)
        ).date()

        revenue = revenue_by_date.get(
            current_date,
            Decimal("0"),
        )

        result.append(
            {
                "date": current_date.isoformat(),
                "revenue": float(
                    revenue.quantize(Decimal("0.01"))
                ),
            }
        )

    return result


def forecast_revenue(
        db: Session,
        history_days: int = 30,
        forecast_days: int = 7,
        user_id: int | None = None,
) -> dict:
    """
    Generate a simple weighted revenue forecast.

    The forecast uses the most recent seven days of non-zero
    revenue history, with more recent days receiving greater weight.
    """

    if history_days <= 0:
        return {
            "error": "history_days must be greater than zero."
        }

    if forecast_days <= 0:
        return {
            "error": "forecast_days must be greater than zero."
        }

    history = get_daily_revenue(
        db,
        history_days,
        user_id,
    )

    revenues = [
        item["revenue"]
        for item in history
        if item["revenue"] > 0
    ]

    if len(revenues) < 3:
        return {
            "error": "Not enough revenue history for forecasting."
        }

    recent = revenues[-7:]

    weights = list(
        range(
            1,
            len(recent) + 1,
        )
    )

    weighted_total = sum(
        Decimal(str(revenue)) * Decimal(str(weight))
        for revenue, weight in zip(recent, weights)
    )

    weight_total = Decimal(
        str(sum(weights))
    )

    weighted_average = (
            weighted_total / weight_total
    )

    last_date = datetime.utcnow().date()

    forecast = []

    for i in range(1, forecast_days + 1):
        forecast_date = (
                last_date + timedelta(days=i)
        )

        forecast.append(
            {
                "date": forecast_date.isoformat(),
                "predicted_revenue": float(
                    weighted_average.quantize(
                        Decimal("0.01")
                    )
                ),
            }
        )

    return {
        "history_days": history_days,
        "forecast_days": forecast_days,
        "recent_average": float(
            weighted_average.quantize(
                Decimal("0.01")
            )
        ),
        "forecast": forecast,
    }
